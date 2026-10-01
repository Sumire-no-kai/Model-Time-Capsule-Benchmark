# API 服务商预设 / Provider presets

内置九个服务商预设。官方文档核对日期：2026-10-01。`providers.json` 只预填地址、协议、token 参数名和密钥环境变量名；实际密钥填写在独立的 `api_keys.local.json`，不固定模型清单。

| CLI 名称 | 服务 | Base URL | 密钥环境变量 | 协议 | 官方文档 |
|---|---|---|---|---|---|
| `claude` | Claude / Anthropic | `https://api.anthropic.com/v1` | `ANTHROPIC_API_KEY` | `anthropic_messages` | [官方来源](https://platform.claude.com/docs/en/api/messages/create) |
| `openai` | OpenAI / ChatGPT models | `https://api.openai.com/v1` | `OPENAI_API_KEY` | `chat_completions` | [官方来源](https://developers.openai.com/api/reference/overview) |
| `gemini` | Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | `GEMINI_API_KEY` | `chat_completions` | [官方来源](https://ai.google.dev/gemini-api/docs/openai) |
| `glm` | GLM / BigModel China | `https://open.bigmodel.cn/api/paas/v4` | `BIGMODEL_API_KEY` | `chat_completions` | [官方来源](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| `zai` | Z.AI international | `https://api.z.ai/api/paas/v4` | `ZAI_API_KEY` | `chat_completions` | [官方来源](https://docs.z.ai/api-reference/introduction) |
| `kimi` | Kimi / Moonshot China | `https://api.moonshot.cn/v1` | `MOONSHOT_API_KEY` | `chat_completions` | [官方来源](https://platform.kimi.com/docs/api/chat) |
| `kimi-intl` | Kimi / Moonshot international | `https://api.moonshot.ai/v1` | `MOONSHOT_INTL_API_KEY` | `chat_completions` | [官方来源](https://platform.kimi.ai/docs/api/chat) |
| `deepseek` | DeepSeek | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` | `chat_completions` | [官方来源](https://api-docs.deepseek.com/guides/json_mode/) |
| `grok` | Grok / xAI | `https://api.x.ai/v1` | `XAI_API_KEY` | `chat_completions` | [官方来源](https://docs.x.ai/developers/rest-api-reference/inference/chat) |

token 输出参数：`openai`、`kimi`、`kimi-intl` 使用 `max_completion_tokens`，其余使用 `max_tokens`（Claude 原生接口只用 `max_tokens`）。

## 别名

| 别名 | 对应预设 |
|---|---|
| `chatgpt` | `openai` |
| `anthropic` | `claude` |
| `google` | `gemini` |
| `bigmodel`、`zhipu`、`zhipuai` | `glm` |
| `z.ai` | `zai` |
| `moonshot`、`kimi-cn` | `kimi` |
| `moonshot-intl`、`kimi_intl` | `kimi-intl` |
| `xai`、`gork` | `grok` |

ChatGPT 对应此处的 OpenAI API 模型入口。

## 国内站 / 国际站成对预设

- `glm`（智谱 BigModel 国内站）与 `zai`（Z.AI 国际站）
- `kimi`（Moonshot 国内站）与 `kimi-intl`（Moonshot 国际站）

每一对使用不同的 Base URL，账户和密钥通常互不通用，所以故意使用**各自独立的密钥字段和环境变量**（`glm` / `zai` 分别读取 `BIGMODEL_API_KEY` 与 `ZAI_API_KEY`；`kimi` / `kimi-intl` 分别读取 `MOONSHOT_API_KEY` 与 `MOONSHOT_INTL_API_KEY`）。这样不会把一个站点的密钥发到另一个站点。请按你实际开通的站点选择预设。

## 使用 / Usage

```bash
python runner/run_api.py --list-providers
python runner/run_api.py --provider deepseek
python runner/run_api.py --provider claude --list-models
python runner/run_api.py --provider gemini --language en
python runner/run_api.py --config runner/providers/glm.json
```

批量：

```bash
# 预览：打印计划、请求数和密钥状态 key=found / key=MISSING，不发送任何请求
python runner/run_api.py --provider kimi --models MODEL_A,MODEL_B --dry-run

# 列出某服务商上名称含关键词的模型，不生成
python runner/run_api.py --provider kimi-intl --list-models --filter k2

# 批量文件（可跨服务商），中英文各跑一次
python runner/run_api.py --batch runner/batch.example.json --language both --dry-run
```

批量模式的完整说明见 [README.md](README.md)。

直接运行 `python runner/run_api.py`：有 `config.local.json` 时沿用该文件；其 `provider` 为 `"select"` 时先在交互终端选服务商；没有配置文件时同样在交互终端先选服务商。选定后自动读取 `api_keys.local.json` 对应字段，再动态选模型；未填写时才用环境变量或临时输入。`--provider` 不读取本地配置，不能与 `--config` 同时使用。需要修改运行参数时，复制对应的 `runner/providers/*.json` 后编辑；`provider` 字段会补全官方地址等默认值，显式字段覆盖预设。

## 协议说明

- Claude 使用原生 `/messages`、`x-api-key` 与 `anthropic-version` 请求头，模型列表支持 `after_id` 分页。当前原生适配接受 `top_p`，不会把 OpenAI 风格的 `seed` / `reasoning_effort` 当作已生效参数；温度范围为 0–1。跨工作区账户需要的可选 workspace 头尚未加入，预设默认使用绑定工作区的 API key。
- Gemini 使用官方 OpenAI 兼容入口，含兼容的 `/models`。其余预设使用 Chat Completions 路径。部分模型可能仅支持其他接口或限制参数，应以实际响应为准。
- 所有预设都会尝试动态获取模型。若某平台/账户未开放兼容列表，用 `--model` 指定已知且有权限的 ID；`--model` 不是绕过授权的手段，预设地址或公开模型名称也不代表已验证调用权限。

## 关于 Coding Plan 与实测范围

- **不使用 Coding Plan 专用端点。** 预设的都是各家的通用 API 地址；某些服务商的 Coding Plan / 订阅套餐专用地址不会自动混入，也没有被内置。
- **只做过本地模拟测试。** 维护者的工具只用本地 HTTP 模拟服务验证了请求构造、模型发现、分页、失败处理与计分流程，**没有使用任何认证凭据调用真实的服务商接口**。因此各服务商的认证、速率限制和真实生成行为尚未由本项目验证；遇到差异请以服务商官方文档和实际响应为准。

## 配置文件分工 / Configuration layout

- `config.local.json`：你当前使用的选择与运行参数（已被 .gitignore 排除）。`{"provider":"select"}` 语义是启动时显示九家菜单；改为 `"deepseek"` 等名称即可固定一家。模板见 `config.example.json`。
- `providers.json`：九家的完整地址、协议、token 参数、密钥变量与官方来源。这是完整预设目录，不需要把九套地址重复拷进本地配置。
- `providers/*.json`：各服务商的单独示例配置（`runs` 默认 5）。
- `api_keys.local.json`：实际密钥。见 [密钥指南](../开始使用_API密钥.md)。

`provider=select` 不能同时指定 `base_url` / `api_key_env` / `protocol` / `token_parameter`，避免把一家的密钥发送到另一家。旧版 `YOUR-PROVIDER.example` 占位模板会自动进入服务商选择，迁移只针对这个固定占位地址，不会替换已有的自定义真实接口。

## English

Nine official endpoint presets are built in (claude, openai, gemini, glm, zai, kimi, kimi-intl, deepseek, grok), checked against the official documentation on 2026-10-01. Use `--provider NAME`, or a file in `runner/providers/`. `--list-providers` needs no key or network. With `provider="select"` or no local config, interactive startup offers a provider menu. Keys are read first from the shared `api_keys.local.json`, then the provider's environment variable, then temporary hidden input (never in batch mode).

Aliases: chatgpt→openai, anthropic→claude, google→gemini, bigmodel/zhipu/zhipuai→glm, z.ai→zai, moonshot/kimi-cn→kimi, moonshot-intl/kimi_intl→kimi-intl, xai/gork→grok.

Regional pairs (glm/zai and kimi/kimi-intl) use different base URLs and, on purpose, separate key fields and environment variables so that a key for one site is never sent to the other. Claude uses the native Messages API with paginated model discovery; the other presets use Chat Completions (Gemini through its official OpenAI-compatible endpoint). A manually supplied `--model` is not an authorization bypass.

Coding-plan endpoints are not used: only general API endpoints are prefilled. Only local mock tests were run; the maintainers' tooling made no authenticated calls to any real provider, so provider authentication, rate limits and live generation behaviour are unverified.
