import json
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import unittest
from unittest.mock import patch

# Test discovery puts this directory on sys.path.
from test_card_api import api


def preset_files():
    # The project may live on exFAT, where macOS leaves binary "._name" metadata copies beside real files.
    return sorted(p for p in (api.ROOT/'runner/providers').glob('*.json') if not p.name.startswith('.'))


class ClaudeHandler(BaseHTTPRequestHandler):
    records=[]
    repeat_cursor=False
    def log_message(self,*args):pass
    def reply(self,data):
        payload=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        type(self).records.append((self.path,dict(self.headers),None))
        if 'after_id' in self.path and not self.repeat_cursor:
            self.reply({'data':[{'id':'claude-fixture-b'}],'has_more':False,'last_id':'claude-fixture-b'})
        else:
            self.reply({'data':[{'id':'claude-fixture-a'}],'has_more':True,'last_id':'claude-fixture-a'})
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).records.append((self.path,dict(self.headers),data))
        self.reply({'model':'claude-fixture-snapshot','stop_reason':'max_tokens','content':[{'type':'thinking','thinking':'HIDDEN-FIXTURE'},{'type':'text','text':'Visible answer'}], 'usage':{'input_tokens':11,'output_tokens':22}})


class ProviderTests(unittest.TestCase):
    def test_all_presets_validate(self):
        names={'claude','openai','gemini','glm','zai','kimi','kimi-intl','deepseek','grok'}
        self.assertEqual(set(api.provider_catalog()),names)
        for name in names:
            config=api.validate_config({'provider':name})
            self.assertTrue(config['base_url'].startswith('https://'))
            self.assertTrue(config['api_key_env'].endswith('_API_KEY'))
            self.assertNotIn('api_key',config)

    def test_generous_defaults_and_explicit_override(self):
        for name in api.provider_catalog():
            config=api.validate_config({'provider':name})
            self.assertEqual(config['max_output_tokens'],65536)
            self.assertEqual(config['timeout_seconds'],900)
        for path in [api.ROOT/'runner/config.example.json',*preset_files()]:
            config=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(config['max_output_tokens'],65536)
            self.assertEqual(config['timeout_seconds'],900)
        config=api.validate_config({'provider':'gemini','max_output_tokens':4096,'timeout_seconds':60})
        self.assertEqual(config['max_output_tokens'],4096)
        self.assertEqual(config['timeout_seconds'],60)

    def test_selection_config_uses_chosen_provider(self):
        template=json.loads((api.ROOT/'runner/config.example.json').read_text())
        self.assertEqual(template['provider'],'select')
        config=api.validate_config(api.prepare_runtime_config(template,choose=lambda:'gemini'))
        self.assertEqual(config['provider'],'gemini')
        self.assertEqual(config['api_key_env'],'GEMINI_API_KEY')
        self.assertNotIn('.example',config['base_url'])

    def test_old_placeholder_migrates_and_keeps_run_preferences(self):
        old={'base_url':'https://YOUR-PROVIDER.example/v1','api_key_env':'LLM_API_KEY','token_parameter':'max_tokens','runs':1,'language':'en'}
        config=api.validate_config(api.prepare_runtime_config(old,choose=lambda:'openai'))
        self.assertEqual(config['api_key_env'],'OPENAI_API_KEY')
        self.assertEqual(config['token_parameter'],'max_completion_tokens')
        self.assertEqual(config['runs'],1)
        self.assertEqual(config['language'],'en')
        self.assertEqual(old['api_key_env'],'LLM_API_KEY')

    def test_custom_config_not_replaced(self):
        original={'base_url':'https://example.com/v1','api_key_env':'CUSTOM_API_KEY'}
        def forbidden():raise AssertionError('Should not prompt')
        self.assertEqual(api.prepare_runtime_config(original,choose=forbidden),original)

    def test_selection_rejects_cross_provider_overrides(self):
        with self.assertRaises(ValueError):
            api.prepare_runtime_config({'provider':'select','api_key_env':'WRONG_KEY'},choose=lambda:'claude')

    def test_aliases(self):
        for alias,canonical in [('chatgpt','openai'),('gork','grok'),('z.ai','zai'),('anthropic','claude'),('zhipu','glm'),('moonshot','kimi'),('moonshot-intl','kimi-intl')]:
            self.assertEqual(api.validate_config({'provider':alias})['provider'],canonical)

    def test_zhipu_and_kimi_regions_never_share_endpoint_or_key(self):
        pairs=[('glm','zai'),('kimi','kimi-intl')]
        for domestic,international in pairs:
            a,b=api.validate_config({'provider':domestic}),api.validate_config({'provider':international})
            self.assertNotEqual(a['base_url'],b['base_url'])
            self.assertNotEqual(a['api_key_env'],b['api_key_env'])
        self.assertEqual(api.validate_config({'provider':'kimi'})['base_url'],'https://api.moonshot.cn/v1')
        self.assertEqual(api.validate_config({'provider':'kimi-intl'})['base_url'],'https://api.moonshot.ai/v1')
        # Moonshot deprecates max_tokens in favour of max_completion_tokens.
        for name in ('kimi','kimi-intl'):
            self.assertEqual(api.validate_config({'provider':name})['token_parameter'],'max_completion_tokens')

    def test_configs_match_catalog(self):
        for p in preset_files():
            self.assertEqual(api.validate_config(json.loads(p.read_text()))['provider'],p.stem)

    def test_explicit_override_and_custom_backward_compatibility(self):
        config=api.validate_config({'provider':'openai','base_url':'http://127.0.0.1:9999/v1','api_key_env':'LOCAL_TEST_KEY'})
        self.assertEqual(config['api_key_env'],'LOCAL_TEST_KEY')
        config=api.validate_config({'base_url':'https://example.com/v1'})
        self.assertEqual(config['protocol'],'chat_completions')
        self.assertEqual(config['api_key_env'],'LLM_API_KEY')

    def test_unknown_and_unsupported_settings(self):
        for config in [{'provider':'not-real'}, {'provider':'claude','temperature':1.5}, {'provider':'claude','extra_body':{'reasoning_effort':'high'}}, {'provider':'claude','token_parameter':'max_completion_tokens'}]:
            with self.assertRaises(ValueError):api.validate_config(config)

    def test_native_claude_auth_pagination_and_response(self):
        ClaudeHandler.records=[];ClaudeHandler.repeat_cursor=False
        server=ThreadingHTTPServer(('127.0.0.1',0),ClaudeHandler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            config=api.validate_config({'provider':'claude','base_url':f'http://127.0.0.1:{server.server_port}/v1'})
            client=api.Client(config,'FAKE_TEST_KEY')
            self.assertEqual(client.models(),['claude-fixture-a','claude-fixture-b'])
            text,meta=client.complete('claude-fixture-a','test-prompt')
            self.assertEqual(text,'Visible answer')
            self.assertNotIn('HIDDEN',text)
            self.assertEqual(meta['finish_reason'],'max_tokens')
            self.assertEqual(meta['usage']['total_tokens'],33)
            for route,headers,body in ClaudeHandler.records:
                headers={k.lower():v for k,v in headers.items()}
                self.assertEqual(headers['x-api-key'],'FAKE_TEST_KEY')
                self.assertEqual(headers['anthropic-version'],'2023-06-01')
                self.assertNotIn('authorization',headers)
            route,headers,body=ClaudeHandler.records[-1]
            self.assertEqual(route,'/v1/messages')
            self.assertEqual(body['max_tokens'],65536)
            self.assertEqual(body['messages'],[{'role':'user','content':'test-prompt'}])
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_repeated_cursor_fails(self):
        config=api.validate_config({'provider':'claude'})
        client=api.Client(config,'FAKE_TEST_KEY')
        with patch.object(client,'request',return_value={'data':[{'id':'a'}],'has_more':True,'last_id':'a'}):
            with self.assertRaises(api.APIError):client.models()


if __name__=='__main__':unittest.main()
