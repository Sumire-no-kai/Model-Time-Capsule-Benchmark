import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_card_api import api


class CredentialFileTests(unittest.TestCase):
    def test_all_providers_share_one_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'keys.json'
            values={name:'FAKE_'+name for name in api.provider_catalog()}
            p.write_text(json.dumps(values),encoding='utf-8')
            for name in values:
                config=api.validate_config({'provider':name})
                self.assertEqual(api.configured_api_key(config,p),(values[name],'local-json'))

    def test_file_takes_priority(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'DEEPSEEK_API_KEY':'ENV_FAKE'},clear=True):
            p=Path(tmp)/'keys.json';p.write_text('{"deepseek":"FILE_FAKE"}')
            self.assertEqual(api.configured_api_key(api.validate_config({'provider':'deepseek'}),p),('FILE_FAKE','local-json'))

    def test_empty_and_missing_file_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'DEEPSEEK_API_KEY':'ENV_FAKE'},clear=True):
            p=Path(tmp)/'keys.json';c=api.validate_config({'provider':'deepseek'})
            self.assertEqual(api.configured_api_key(c,p),('ENV_FAKE','environment'))
            p.write_text('{"deepseek":"  ","claude":"OTHER_FAKE"}')
            self.assertEqual(api.configured_api_key(c,p),('ENV_FAKE','environment'))

    def test_no_key_available(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True):
            p=Path(tmp)/'keys.json';p.write_text('{"deepseek":""}')
            self.assertEqual(api.configured_api_key(api.validate_config({'provider':'deepseek'}),p),(None,None))

    def test_invalid_file_never_echoes_secret(self):
        bad=['{"SECRET_SENTINEL":"x"}', '{"deepseek":123}', '{"SECRET_SENTINEL":"a","SECRET_SENTINEL":"b"}', '{broken SECRET_SENTINEL', '["SECRET_SENTINEL"]']
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'keys.json'
            for raw in bad:
                p.write_text(raw)
                with self.assertRaises(ValueError) as error:
                    api.configured_api_key(api.validate_config({'provider':'deepseek'}),p)
                self.assertNotIn('SECRET_SENTINEL',str(error.exception))

    def test_custom_and_trimming(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'keys.json';p.write_text('{"custom":"  CUSTOM_FAKE  "}')
            config=api.validate_config({'base_url':'https://example.com/v1'})
            self.assertEqual(api.configured_api_key(config,p),('CUSTOM_FAKE','local-json'))

    def test_example_blank_and_ignore_entry(self):
        root=api.ROOT
        data=json.loads((root/'runner/api_keys.example.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(set(data),set(api.provider_catalog())|{'custom'})
        self.assertTrue(all(value=='' for value in data.values()))
        ignored=(root/'.gitignore').read_text(encoding='utf-8-sig').splitlines()
        self.assertIn('runner/api_keys.local.json',ignored)
        self.assertNotIn('runner/api_keys.example.json',ignored)


if __name__=='__main__':unittest.main()
