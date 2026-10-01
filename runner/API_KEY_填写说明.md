# API Key 填在这里

打开同目录的 [api_keys.local.json](api_keys.local.json)，把密钥填进相应服务商的空引号，保存。文件里有九个服务商字段加一个 custom：claude、openai、gemini、glm、zai、kimi、kimi-intl、deepseek、grok、custom。只填你要用的几家，其余留空。

例如使用 DeepSeek，就填写 deepseek 字段；使用 Moonshot 国内站填 kimi，国际站填 kimi-intl（国内/国际站的密钥不通用，分开填写）。

然后从项目根目录运行：

```bash
python runner/run_api.py
```

批量运行前先预览（不发送请求，会显示每个任务的 `key=found` / `key=MISSING`）：

```bash
python runner/run_api.py --provider kimi --models MODEL_A,MODEL_B --dry-run
python runner/run_api.py --batch runner/batch.example.json --dry-run
```

[详细说明与读取优先级](../开始使用_API密钥.md)。实际密钥文件已加入 .gitignore；api_keys.example.json 仅作空白示例，不要往里面填真实密钥。

Fill the matching provider field in api_keys.local.json (nine providers plus custom). This local plaintext file is gitignored; the example stays blank. Use `--dry-run` to check which keys are `found` or `MISSING` before a batch. See the bilingual guide above.
