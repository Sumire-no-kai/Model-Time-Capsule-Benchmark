# API Key 固定填写位置

**打开 [runner/api_keys.local.json](runner/api_keys.local.json)，把对应服务商的密钥填进空引号里，保存即可。** 该文件已被 .gitignore 排除；仓库里提供的是空白模板 [runner/api_keys.example.json](runner/api_keys.example.json)，若本地还没有 api_keys.local.json，先复制模板再填写。

```json
{
  "claude": "",
  "openai": "",
  "gemini": "",
  "glm": "",
  "zai": "",
  "kimi": "",
  "kimi-intl": "",
  "deepseek": "",
  "grok": "",
  "custom": ""
}
```

- claude：Anthropic API Key。
- openai：OpenAI API Key，对应 ChatGPT 系列 API 模型。
- gemini：Google Gemini API Key。
- glm：智谱国内平台（BigModel）API Key。
- zai：Z.AI 国际平台 API Key。
- kimi：Moonshot / Kimi 国内平台 API Key。
- kimi-intl：Moonshot / Kimi 国际平台 API Key。
- deepseek：DeepSeek API Key。
- grok：xAI API Key。
- custom：自定义 API 的密钥，不使用自定义接口时留空。

glm 与 zai、kimi 与 kimi-intl 是国内/国际站点配对，账户和密钥通常不通用，所以故意分成不同字段，也对应不同的环境变量。

只填你要用的几家，其他保持空字符串。填密钥本身，不加 Bearer、额外引号或说明文字。JSON 不支持注释，最后一项后不要加逗号。

## 启动

在项目根目录运行：

```bash
python runner/run_api.py
```

先选服务商，脚本自动读取对应密钥，再拉取模型列表供选择。也可以指定：

```bash
python runner/run_api.py --provider deepseek
```

只检查模型列表、不生成答案：

```bash
python runner/run_api.py --provider deepseek --list-models
```

默认每个模型独立运行 5 轮（`--runs 5`），每轮两次请求（主卷、B 卷），运行会产生 API 费用。

## 批量运行与密钥检查

批量模式从不提示输入密钥，缺密钥的任务会直接记为失败。正式运行前先用 `--dry-run` 预览：它只打印计划、请求数，并对每个任务显示 `key=found` 或 `key=MISSING`，不发送任何请求。

```bash
# 同一服务商的多个模型
python runner/run_api.py --provider gemini --models MODEL_A,MODEL_B --dry-run

# 批量文件（可跨服务商）
python runner/run_api.py --batch runner/batch.example.json --dry-run

# 确认无误后去掉 --dry-run；--language both 让每个模型中英文各跑一次
python runner/run_api.py --batch runner/batch.example.json --language both
```

批量用法的完整说明见 [runner/README.md](runner/README.md)。

## 读取顺序与文件分工

密钥读取顺序：api_keys.local.json 中当前服务商的非空值 → 对应环境变量 → 终端临时隐藏输入。临时输入不会自动保存回 JSON，批量模式不会提示输入。

| 服务商 | 环境变量 |
|---|---|
| claude | `ANTHROPIC_API_KEY` |
| openai | `OPENAI_API_KEY` |
| gemini | `GEMINI_API_KEY` |
| glm | `BIGMODEL_API_KEY` |
| zai | `ZAI_API_KEY` |
| kimi | `MOONSHOT_API_KEY` |
| kimi-intl | `MOONSHOT_INTL_API_KEY` |
| deepseek | `DEEPSEEK_API_KEY` |
| grok | `XAI_API_KEY` |

自定义接口默认读取环境变量 `LLM_API_KEY`（可用配置里的 `api_key_env` 改名）。

- api_keys.local.json：实际密钥的本地文件，已被 .gitignore 排除。
- api_keys.example.json：空白模板，可以公开，不要往它填写实际密钥。
- config.local.json：选哪家、测几轮、用什么语言等运行参数，不存密钥。
- providers.json：九家的 API URL、协议和备用密钥变量名，不存密钥。

默认从项目内的 runner/api_keys.local.json 读取，不受当前终端目录影响。可用 `--keys-file PATH` 显式指定另一份同结构的密钥文件。

## 安全提醒

- **不要提交密钥文件。** api_keys.local.json 是本地**明文**存储，报告、日志和会话文件都不会包含其内容。
- .gitignore 只防止正常的 `git add`，不会阻止手工上传或强制提交（`git add -f`）；发布到 GitHub 前请确认没有包含该文件。
- 若密钥可能泄露，请到服务商后台撤销并重新生成。
- 示例文件必须保持为空。

## English

Fill your provider keys in runner/api_keys.local.json, using the corresponding blank string; copy runner/api_keys.example.json first if the local file does not exist yet. The file has nine provider fields (claude, openai, gemini, glm, zai, kimi, kimi-intl, deepseek, grok) plus custom. Leave unused providers blank. The regional pairs glm/zai and kimi/kimi-intl keep separate fields and environment variables on purpose. The file is local plaintext storage and is excluded by .gitignore; never manually upload or force-add it to GitHub. The example file must remain empty.

Key lookup order: the selected provider's nonempty JSON value, then its environment variable, then temporary hidden input (interactive terminals only, never saved, never in batch mode). Reports and logs exclude credentials. `--keys-file PATH` selects an alternate JSON file; the default is resolved relative to the project, not the current directory.

Before a batch, run it with `--dry-run`: it sends nothing and prints `key=found` or `key=MISSING` for every job. Default is 5 runs per model, two requests per run.
