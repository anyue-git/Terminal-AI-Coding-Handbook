# 02 Codex 的 TOML、Profile 与凭证

> 最近核对：2026-07-29

这一章主要讲本地 Codex CLI 和 Codex IDE 扩展读取的配置。它们共享 Codex 的配置层和登录缓存，因此在 CLI 中修改 `~/.codex/config.toml`，通常也会影响 IDE 扩展。Codex 的其他界面或托管运行环境可能还有独立设置，遇到界面行为不一致时，应先确认当前操作的是本地 CLI、IDE 扩展还是云端任务。

学习 TOML 的目的不是背完整配置参考，而是能看懂管理工具写入了什么，知道哪些字段决定模型和供应商，也知道凭证为什么不应该直接粘贴进公开配置。

---

## 1. Codex 默认读取哪些位置

Codex 的本地状态目录由 `CODEX_HOME` 决定，默认是：

```text
~/.codex
```

常见内容包括：

```text
~/.codex/config.toml
~/.codex/auth.json
~/.codex/history.jsonl
```

`config.toml` 保存行为设置，`auth.json` 只在使用文件式凭证存储时出现；系统也可能把凭证放入 Keychain 或 Keyring。历史、日志和缓存同样可能位于 `CODEX_HOME` 下，所以不应把整个目录当作普通配置压缩后发给别人。

先检查当前目录和文件权限：

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
ls -ld "${CODEX_HOME:-$HOME/.codex}" 2>/dev/null
ls -l "${CODEX_HOME:-$HOME/.codex}/config.toml" \
  "${CODEX_HOME:-$HOME/.codex}/auth.json" 2>/dev/null
```

这组命令不会读取文件正文。若 `auth.json` 不存在，可能是尚未登录，也可能是凭证存放在系统凭证库中。

---

## 2. 只学够用的 TOML 语法

TOML 最常见的形式是“键等于值”：

```toml
model = "gpt-5.6"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

左边是配置键，右边是值。字符串使用引号，布尔值写 `true` 或 `false`，数字不加引号。

方括号表示一个配置表：

```toml
[model_providers.company_proxy]
name = "Company Proxy"
base_url = "https://gateway.example.com/v1"
env_key = "COMPANY_OPENAI_API_KEY"
wire_api = "responses"
```

这里的 `company_proxy` 是自定义标识。`env_key` 的值不是 API Key，而是环境变量名称。真正的密钥应由 Shell、密码管理器或凭证辅助程序提供。

TOML 对引号、数组和层级有明确语法。修改后如果 Codex 无法启动，不要继续叠加配置，先检查文件：

```bash
codex --version
codex --help
```

如果报错指出某一行 TOML 解析失败，优先检查缺少引号、重复键、表名拼错和复制时混入的全角符号。

---

## 3. 最小用户配置

一个适合新手理解的基础配置如下：

```toml
model = "gpt-5.6"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
cli_auth_credentials_store = "keyring"
```

它分别控制默认模型、命令审批、文件系统 Sandbox 和凭证存储方式。模型名称和可用设置会随版本变化，不应把示例中的模型永久视为唯一正确选择。

修改前先备份：

```bash
mkdir -p ~/.config-backups/codex
chmod 700 ~/.config-backups ~/.config-backups/codex
cp ~/.codex/config.toml \
  ~/.config-backups/codex/config.toml.before-edit 2>/dev/null || true
```

再使用自己熟悉的编辑器打开：

```bash
nano ~/.codex/config.toml
```

保存后启动一个只读任务，确认配置能够加载：

```bash
codex "只读说明当前目录，不要修改文件"
```

如果客户端仍使用旧模型，检查是否有命令行参数、项目配置或 Profile 覆盖用户配置。

---

## 4. 配置优先级为什么重要

Codex 按层合并配置，优先级从高到低大致为：

1. 命令行参数和 `--config`；
2. 受信任项目中的 `.codex/config.toml`；
3. 通过 `--profile` 选择的 Profile 文件；
4. 用户配置 `~/.codex/config.toml`；
5. 系统配置；
6. 内置默认值。

这意味着你修改了用户配置，却仍可能被项目文件或启动参数覆盖。遇到“文件已经改了但没有生效”时，先查看启动命令和项目中的 `.codex/`，不要立刻删除 `auth.json`。

例如用户配置写了：

```toml
model = "MODEL_A"
```

项目中的 `.codex/config.toml` 写了：

```toml
model = "MODEL_B"
```

在受信任项目中启动时，实际使用的通常是 `MODEL_B`。离开该项目后，又会回到用户默认值。

项目配置适合保存团队共享的审批和 Sandbox 规则，但不应提交真实密钥。Codex 只会为受信任项目加载项目级配置，这是为了降低克隆陌生仓库后自动应用危险设置的风险。

---

## 5. Profile 不是账号

Profile 是一层命名配置，用于保存不同场景下的模型、审批策略或供应商设置。例如建立一个较谨慎的代码审查 Profile：

```toml
# ~/.codex/deep-review.config.toml
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
approval_policy = "on-request"
```

启动时执行：

```bash
codex --profile deep-review
```

当前 Codex 使用独立的 `~/.codex/PROFILE_NAME.config.toml` 文件。旧教程中将内容写在 `[profiles.NAME]` 下的方式已经不适用于 Codex 0.134.0 及以后版本。

Profile 默认叠加在同一个 `CODEX_HOME` 上，因此通常仍共享登录缓存。换句话说：

```text
切换 Profile
≠ 切换 ChatGPT 账号
≠ 建立独立实例
```

如果 Profile 只改变模型或供应商，它不会自动创建另一份 `auth.json`。

---

## 6. 自定义供应商与中转站

Codex 支持在 `model_providers` 中定义额外供应商。下面是结构示例，地址和模型名必须替换为服务方实际提供的值：

```toml
model = "PROVIDER_MODEL_NAME"
model_provider = "my_gateway"

[model_providers.my_gateway]
name = "My Gateway"
base_url = "https://gateway.example.com/v1"
env_key = "MY_GATEWAY_API_KEY"
wire_api = "responses"
```

在当前 Shell 中临时设置密钥：

```bash
read -s MY_GATEWAY_API_KEY
export MY_GATEWAY_API_KEY
printf '\n密钥已写入当前 Shell 环境，不会显示正文。\n'
```

`read -s` 不回显输入，但变量仍存在于当前 Shell 进程中。关闭终端后通常会消失。长期使用时，应采用系统凭证库、可信密码管理器或服务方支持的凭证辅助程序，不要直接把密钥写入仓库中的 `.env`。

Codex 官方还支持由外部命令获取 Bearer Token：

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

这种方式适合企业短期令牌。辅助命令会接触凭证，应由可信管理员提供并限制文件权限。

---

## 7. `wire_api` 与协议兼容

Base URL 能连通，不代表服务就兼容 Codex。Codex 当前主要围绕 Responses 协议工作，自定义 Provider 中的 `wire_api = "responses"` 表示按 Responses 形式通信。

常见故障可以按下面的顺序判断：

- **401 或 403**：先检查密钥、授权范围和请求头；
- **404**：检查 Base URL 是否已经包含 `/v1`、服务端是否提供对应路径；
- **model not found**：检查模型名称和账号权限；
- **能对话但工具调用失败**：检查服务是否完整兼容 Responses、流式事件和工具调用；
- **返回 Chat Completions 格式错误**：上游可能只支持 `/chat/completions`，需要兼容网关做协议转换。

不要因为服务宣传“OpenAI compatible”就默认它支持 Codex 所需的全部事件。兼容普通聊天接口与兼容 Codex Agent 工作流是不同要求。

---

## 8. `auth.json` 与 Keyring

Codex 可以把缓存凭证保存到 `auth.json`，也可以使用操作系统凭证库。配置键如下：

```toml
cli_auth_credentials_store = "keyring"
```

可选值包括：

- `file`：保存到 `CODEX_HOME/auth.json`；
- `keyring`：保存到系统凭证库；
- `auto`：能使用系统凭证库时优先使用，否则退回文件。

如果使用文件方式，`auth.json` 可能包含访问令牌，应当像密码一样处理。不要执行：

```bash
cat ~/.codex/auth.json
```

然后把输出贴到聊天、Issue 或群组中。需要确认文件是否存在，只运行：

```bash
ls -l ~/.codex/auth.json
```

退出登录会影响 CLI 和 IDE 扩展共享的缓存。删除文件不是日常排错的第一步，因为你可能同时失去仍然有效的官方登录。

---

## 9. 用 `CODEX_HOME` 建立第二套实例

Profile 适合切换配置，不适合完整隔离账号。要建立第二套状态目录，可以临时指定：

```bash
mkdir -p ~/.codex-work
chmod 700 ~/.codex-work
CODEX_HOME="$HOME/.codex-work" codex
```

第一次启动时，这套实例会在新的 `CODEX_HOME` 中创建自己的配置、登录缓存和历史。原来的 `~/.codex` 不会自动复制过去。

可以准备两个启动脚本，但不要把密钥写进脚本：

```bash
#!/bin/sh
CODEX_HOME="$HOME/.codex-personal" exec codex "$@"
```

```bash
#!/bin/sh
CODEX_HOME="$HOME/.codex-work" exec codex "$@"
```

为脚本增加执行权限后，就能从两个终端分别启动。此方式仍需确认 Codex 版本是否把所有相关状态都放在 `CODEX_HOME`，以及系统 Keyring 中的条目是否会跨目录共享。真正需要强隔离时，独立系统用户或容器边界更清楚。

---

## 10. 管理工具切换 Codex 时应检查什么

使用 CC Switch 或 Cockpit Tools 切换后，至少检查：

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
grep -E '^(model|model_provider|openai_base_url|cli_auth_credentials_store)' \
  "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null
```

这只查看少数非密钥字段。不要把整个配置文件发送给别人，因为自定义 Header 或实验字段中仍可能含有秘密。

如果工具启用了本地路由，Base URL 可能指向 `127.0.0.1`。此时还要检查本地服务是否运行、监听哪个端口，以及它选择了哪个上游账号。恢复官方配置前，先使用工具提供的退出接管或恢复功能，不要同时手工覆盖文件和点击切换按钮。

### 核对来源

- [Codex Config basics](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex Advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced)
- [Codex Authentication](https://learn.chatgpt.com/docs/auth)
