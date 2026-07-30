# 02 Codex 的 TOML、Profile 与凭证

> 最近核对：2026-07-29

本章讨论本地 Codex CLI 与 Codex IDE 扩展共享的配置层和登录缓存。云端任务或其他 Codex 界面可能有独立设置，行为不一致时应先确认当前操作的是 CLI、IDE 扩展还是托管环境。学习 TOML 的目的不是背完整参考，而是能够沿着 `CODEX_HOME`、配置优先级、Provider、凭证存储和进程启动参数，解释当前请求为什么走向某个模型或账号。

## 1. `CODEX_HOME` 定义状态边界，TOML 描述行为

Codex 状态目录由 `CODEX_HOME` 决定，默认是：

```text
~/.codex
```

常见内容包括：

```text
config.toml    行为与 Provider 配置
auth.json      文件式凭证缓存（只有采用该方式时才存在）
history.jsonl  本地历史
```

系统也可能把凭证放进 Keychain 或 Keyring。日志、缓存和历史同样可能位于状态目录，因此整个 `~/.codex` 不能作为普通配置包发送给别人。只检查目录与权限：

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
ls -ld "${CODEX_HOME:-$HOME/.codex}" 2>/dev/null
ls -l \
  "${CODEX_HOME:-$HOME/.codex}/config.toml" \
  "${CODEX_HOME:-$HOME/.codex}/auth.json" 2>/dev/null
```

`auth.json` 不存在既可能表示尚未登录，也可能表示凭证存放在系统库中。

日常阅读 TOML 只需先掌握键值和配置表：

```toml
model = "gpt-5.6"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

字符串有引号，布尔值写 `true`/`false`，数字不加引号。方括号建立配置表：

```toml
[model_providers.company_proxy]
name = "Company Proxy"
base_url = "https://gateway.example.com/v1"
env_key = "COMPANY_OPENAI_API_KEY"
wire_api = "responses"
```

`company_proxy` 是自定义标识，`env_key` 是环境变量名称，不是密钥正文。真正凭证由 Shell、Keyring、密码管理器或可信辅助程序提供。

一个便于理解的最小用户配置：

```toml
model = "gpt-5.6"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
cli_auth_credentials_store = "keyring"
```

模型名和字段会变化，示例不代表永久唯一值。修改前建立备份：

```bash
mkdir -p ~/.config-backups/codex
chmod 700 ~/.config-backups ~/.config-backups/codex
cp ~/.codex/config.toml \
  ~/.config-backups/codex/config.toml.before-edit 2>/dev/null || true

nano ~/.codex/config.toml
```

保存后用低风险只读会话验证解析：

```bash
codex "只读说明当前目录，不要修改文件"
```

启动失败时检查引号、重复键、表名和全角字符；继续叠加配置只会让错误来源更难判断。

## 2. 配置优先级与 Profile 决定当前场景，不自动切换账号

Codex 按层合并配置，当前大致从高到低为：命令行参数与 `--config`、受信任项目的 `.codex/config.toml`、`--profile` 选择的 Profile、用户 `~/.codex/config.toml`、系统配置、内置默认值。用户文件写了 `MODEL_A`，受信任项目写了 `MODEL_B`，在该项目中通常使用 `MODEL_B`，离开项目又回到用户默认。

项目配置适合团队共享审批、Sandbox 和非敏感模型规则，不应提交真实 Key。Codex 只为受信任项目加载项目配置，以降低陌生仓库自动应用危险设置的风险。遇到旧模型或设置时，应检查启动参数、当前项目 `.codex/` 与 Profile，而不是直接删除登录缓存。

Profile 用于保存命名场景，例如更高推理强度的审查：

```toml
# ~/.codex/deep-review.config.toml
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
approval_policy = "on-request"
```

```bash
codex --profile deep-review
```

当前 Codex 使用独立的 `~/.codex/PROFILE_NAME.config.toml`；旧教程把内容放在 `[profiles.NAME]` 中的写法已不适用于 Codex 0.134.0 及以后版本。Profile 默认叠加在同一 `CODEX_HOME` 上，通常共享官方登录、`auth.json`、Keyring 和历史：

```text
切换 Profile
≠ 切换 ChatGPT 账号
≠ 建立独立实例
```

因此 Profile 适合切换模型、Provider、审批和 Sandbox 场景，不应被当成账号容器。

## 3. Provider、协议和凭证存储必须同时匹配

自定义 Provider 的基本结构：

```toml
model = "PROVIDER_MODEL_NAME"
model_provider = "my_gateway"

[model_providers.my_gateway]
name = "My Gateway"
base_url = "https://gateway.example.com/v1"
env_key = "MY_GATEWAY_API_KEY"
wire_api = "responses"
```

临时提供 Key：

```bash
IFS= read -r -s MY_GATEWAY_API_KEY
export MY_GATEWAY_API_KEY
printf '\n密钥已写入当前 Shell 环境，不会显示正文。\n'
```

`read -s` 只是不回显，变量仍存在于当前进程。长期使用应采用 Keyring、可信密码管理器或供应商支持的辅助程序，不把 Key 写入项目 `.env` 或 TOML。

企业短期 Token 可以由外部命令获取：

```toml
[model_providers.company_gateway]
name = "Company Gateway"
base_url = "https://gateway.example.com/v1"
wire_api = "responses"

[model_providers.company_gateway.auth]
command = "/usr/local/bin/fetch-codex-token"
args = ["--audience", "codex"]
timeout_ms = 5000
refresh_interval_ms = 300000
```

辅助命令会接触凭证，应由可信管理员提供并限制权限。

Base URL 能建立连接不代表兼容 Codex。当前 Codex 主要围绕 Responses 协议，`wire_api = "responses"` 表示按该协议通信。401/403 更接近 Key、权限范围和 Header；404 更接近 Base URL 路径；`model not found` 要检查名称与账号权限；普通对话成功但工具调用失败，通常说明上游没有完整支持 Responses 流式事件和 Tool Call；只支持 `/chat/completions` 的服务通常需要网关转换。“OpenAI compatible”不能直接等同于 Codex Agent 兼容。

凭据存储由以下字段控制：

```toml
cli_auth_credentials_store = "keyring"
```

当前可选值包括 `file`（保存到 `CODEX_HOME/auth.json`）、`keyring`（系统凭证库）和 `auto`（优先系统库，必要时退回文件）。文件式 `auth.json` 可能包含访问令牌，只确认路径和权限：

```bash
ls -l ~/.codex/auth.json
```

CLI 与 IDE 扩展共享缓存时，logout、删除文件或切换凭证可能同时影响两端。删除缓存不是常规排错第一步，也不能把认证文件正文粘贴到聊天、Issue 或群组。

## 4. 真正的第二实例需要独立状态目录，并验证剩余共享层

创建第二套本地状态：

```bash
mkdir -p ~/.codex-work
chmod 700 ~/.codex-work
CODEX_HOME="$HOME/.codex-work" codex
```

新目录会建立自己的配置、登录缓存和历史，不自动复制 `~/.codex`。可以准备不含密钥的启动脚本：

```bash
#!/bin/sh
CODEX_HOME="$HOME/.codex-personal" exec codex "$@"
```

```bash
#!/bin/sh
CODEX_HOME="$HOME/.codex-work" exec codex "$@"
```

这种隔离仍需验证当前版本是否把全部状态放在 `CODEX_HOME`，以及系统 Keyring 条目是否跨目录共享。需要更强边界时，独立系统用户或容器更清楚。

管理工具切换后至少检查：

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
grep -E '^(model|model_provider|openai_base_url|cli_auth_credentials_store)' \
  "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null
```

这里仅读取非密钥字段，完整配置仍可能包含自定义 Header 或实验秘密。Base URL 指向 localhost 时，还要检查本地路由进程、端口和上游账号。恢复官方配置时优先使用管理工具的退出接管或恢复功能，不要一边手工覆盖文件，一边让工具继续监控并写回。

核对来源：

- [Codex Config basics](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex Advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced)
- [Codex Authentication](https://learn.chatgpt.com/docs/auth)
