# 03 Claude Code 的配置、凭证与网关

> 最近核对：2026-07-29

Claude Code 的配置方式和 Codex 不同。它没有把主要设置集中在 TOML 中，而是组合使用 `settings.json`、环境变量、`CLAUDE.md`、MCP 文件和登录状态。很多切换工具之所以让人难以理解，是因为它们可能同时修改 JSON、Shell 环境变量和系统凭证库，而界面只显示一个“当前供应商”。

这一章先讲 Claude Code 自己的配置层，再解释官方登录、API Key、Bearer Token 和 LLM Gateway 之间的关系。Claude Desktop 和 Claude Code 也要分开：本章中的 API Key、`apiKeyHelper` 和终端环境变量主要面向 Claude Code CLI，不等于 Claude Desktop 的认证方式。

---

## 1. 常见文件分别负责什么

Claude Code 的用户级设置通常位于：

```text
~/.claude/settings.json
```

项目可以提供团队共享设置：

```text
PROJECT_ROOT/.claude/settings.json
```

个人只在当前项目使用的设置位于：

```text
PROJECT_ROOT/.claude/settings.local.json
```

共享文件可以进入 Git，`settings.local.json` 应保持在本机。Claude Code 创建本地设置时会尝试将它忽略；如果是自己手动创建，仍要检查 `.gitignore`。

此外还会看到：

```text
~/.claude.json
PROJECT_ROOT/.mcp.json
PROJECT_ROOT/CLAUDE.md
```

`~/.claude.json` 包含 OAuth 会话、部分 MCP 配置、项目信任状态和缓存。它不只是普通偏好设置，不能因为文件扩展名是 JSON 就随手复制给别人。`.mcp.json` 保存项目共享的 MCP 服务器定义，`CLAUDE.md` 则用于项目说明和工作规则。

先只查看路径和权限：

```bash
ls -ld ~/.claude 2>/dev/null
ls -l ~/.claude/settings.json ~/.claude.json 2>/dev/null
find . \
  \( -path '*/.claude/settings.json' \
  -o -path '*/.claude/settings.local.json' \
  -o -name CLAUDE.md \
  -o -name .mcp.json \) -print
```

不要用 `cat ~/.claude.json` 作为日常检查方式，其中可能包含会话和认证信息。

---

## 2. `settings.json` 的三个作用域

用户设置适合保存所有项目共用的个人习惯，例如权限默认值和个人插件。项目设置适合团队共同维护的规则，例如允许运行的测试命令。项目本地设置适合只对自己生效的实验配置和权限选择。

一个简化的项目设置如下：

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

JSON 与 TOML 的语法不同。键和值使用双引号，对象使用花括号，列表使用方括号，最后一项后不能随意留下逗号。文件出现语法错误时，Claude Code 可能跳过该设置来源。

修改后，在 Claude Code 内运行：

```text
/status
```

查看 `Setting sources`，确认实际加载了哪些设置文件。文件存在不代表已经成功解析，`/status` 比单纯执行 `ls` 更接近真实状态。

---

## 3. 配置与认证不要混在一起

Claude Code 可以通过 Claude.ai 订阅、Claude Console、企业云平台、API Key 或网关进行认证。不同方法的凭证存储位置不同。

官方文档当前说明：macOS 上的 Claude Code 凭证保存在系统 Keychain；Linux 上通常位于 `~/.claude/.credentials.json`，权限应为 `0600`。`settings.json` 可以决定行为，也可以引用环境变量，但它不是 OAuth 登录缓存的完整替代品。

在 macOS 上检查 Claude Code 是否能访问 Keychain，可以先运行：

```bash
claude doctor
```

如果登录状态异常，优先在 Claude Code 中使用 `/status`、`/logout` 和 `/login`，不要先删除 Keychain 条目。手工删除凭证可能让其他仍然正常的会话一起失效。

---

## 4. 认证优先级会造成“明明登录了却不用订阅”

Claude Code 同时发现多种凭证时，会按优先级选择。当前官方顺序中，云平台认证优先；随后是 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_API_KEY`、`apiKeyHelper`、`CLAUDE_CODE_OAUTH_TOKEN`，最后才是通过 `/login` 保存的订阅 OAuth 凭证。

这解释了一个常见现象：你已经登录 Claude Max，但 Shell 中残留了 `ANTHROPIC_API_KEY`，Claude Code 仍然使用 API Key 计费。

先安全地查看变量是否存在，不打印值：

```bash
for name in \
  ANTHROPIC_AUTH_TOKEN \
  ANTHROPIC_API_KEY \
  CLAUDE_CODE_OAUTH_TOKEN \
  ANTHROPIC_BASE_URL
do
  if [ -n "$(printenv "$name")" ]; then
    printf '%s=<已设置>\n' "$name"
  else
    printf '%s=<未设置>\n' "$name"
  fi
done
```

如果希望回到订阅登录，可以在当前 Shell 临时清除覆盖变量：

```bash
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_API_KEY
unset CLAUDE_CODE_OAUTH_TOKEN
unset ANTHROPIC_BASE_URL
```

然后重新启动 Claude Code，并用 `/status` 确认活动认证。若下次打开终端后变量再次出现，说明它们可能写在 `.zshrc`、`.zprofile`、环境管理工具或切换工具生成的脚本中。

---

## 5. API Key、Auth Token 和 OAuth Token

`ANTHROPIC_API_KEY` 通常作为 `X-Api-Key` 请求头发送，适合直接使用 Anthropic Console API。`ANTHROPIC_AUTH_TOKEN` 会作为 Bearer Token 使用，常见于 LLM Gateway 或代理。两者的名字相近，但服务端期待的请求头不同。

`CLAUDE_CODE_OAUTH_TOKEN` 是另一种认证来源，可由 `claude setup-token` 生成，主要用于没有浏览器登录条件的脚本和自动化环境。它仍然是敏感凭证，不应放进 Git、截图或聊天记录。

不要通过下面的方式检查变量：

```bash
# 不要这样做，它会把完整秘密打印出来
echo "$ANTHROPIC_API_KEY"
```

只需检查长度或是否存在：

```bash
if [ -n "$ANTHROPIC_API_KEY" ]; then
  printf 'ANTHROPIC_API_KEY 已设置，长度为 %s。\n' \
    "${#ANTHROPIC_API_KEY}"
fi
```

长度只能证明变量有值，不能证明密钥有效。

---

## 6. 用环境变量接入网关

连接一个使用 Bearer Token 的 Anthropic 兼容网关时，常见结构是：

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_GATEWAY_TOKEN"
claude
```

这里的地址、认证类型和模型映射必须以网关文档为准。不要同时设置 `ANTHROPIC_AUTH_TOKEN` 和 `ANTHROPIC_API_KEY` 来“提高成功率”，因为更高优先级的变量可能遮住真正想测试的凭证。

如果只想临时测试，使用一次性环境：

```bash
ANTHROPIC_BASE_URL="https://gateway.example.com" \
ANTHROPIC_AUTH_TOKEN="YOUR_GATEWAY_TOKEN" \
claude
```

这种写法只对本次进程及其子进程生效，但命令可能进入 Shell 历史。更安全的方式是用 `read -s` 读取密钥：

```bash
read -s GATEWAY_TOKEN
printf '\n'
ANTHROPIC_BASE_URL="https://gateway.example.com" \
ANTHROPIC_AUTH_TOKEN="$GATEWAY_TOKEN" \
claude
unset GATEWAY_TOKEN
```

长期配置可以放入可信凭证管理器或 `apiKeyHelper`，不建议把真实 Token 写进项目级 `settings.json`。

---

## 7. `apiKeyHelper` 适合什么场景

`apiKeyHelper` 让 Claude Code 在需要认证时执行一个命令，由该命令输出临时密钥。它适合企业 Vault、短期 Token 和定期轮换的凭证。

用户级设置示例：

```json
{
  "apiKeyHelper": "/Users/YOUR_USERNAME/bin/get-claude-key.sh"
}
```

辅助脚本的最小形式可能是：

```bash
#!/bin/sh
exec /usr/local/bin/company-vault read claude-code-token
```

脚本输出会被 Claude Code 当作认证值发送，因此脚本和它调用的程序都属于凭证链的一部分。限制脚本权限：

```bash
chmod 700 ~/bin/get-claude-key.sh
```

不要在脚本里硬编码密钥，也不要开启会把命令输出记录到日志的调试选项。Claude Code 可以通过 `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` 控制刷新间隔；HTTP 401 也可能触发重新获取。

---

## 8. DeepSeek 和其他 Anthropic 兼容服务

接入 DeepSeek 或其他兼容服务时，Claude Code 仍然是客户端，但请求入口、认证方、计费方和模型提供方已经变化。通常需要配置 Base URL、认证 Token 和模型映射，具体键和值以服务方当前文档为准。

排错时按层检查：

```text
Claude Code 是否启动
→ 设置来源是否加载
→ 环境变量是否覆盖登录
→ Base URL 是否正确
→ 服务端接受哪种认证头
→ 模型别名是否存在
→ 工具调用和流式协议是否兼容
```

普通聊天成功，不代表 Agent 工具调用、长上下文、缓存、图片输入或流式事件全部兼容。中转站声称“兼容 Claude”时，需要进一步确认它兼容的是 Messages API、Claude Code 的工具调用，还是只兼容最基本的文本请求。

---

## 9. 多账号切换与并行实例

在同一套 Claude Code 状态上替换 Keychain 凭证，适合串行切换账号。已经运行的 Claude Code 进程可能保留旧状态，因此切换后通常应关闭并重新启动。

如果需要两个账号同时运行，单纯替换 Keychain 不够。可以考虑独立 macOS 用户、容器或工具提供的隔离配置目录。Claude Code 提供 `CLAUDE_CONFIG_DIR` 影响部分配置和凭证位置，但在 macOS 上官方 OAuth 凭证使用 Keychain，是否能够仅靠目录变量实现完整隔离，需要根据当前版本和管理工具的实现验证。

这也是为什么某些多开工具不仅复制 `settings.json`，还会维护 Keychain 条目、环境变量或单独启动参数。使用前必须看清它的隔离范围。

---

## 10. 常见故障案例

### 已登录订阅，却收到无效 API Key

先运行 `/status` 查看活动认证，再检查 `ANTHROPIC_API_KEY` 是否存在。环境变量优先于订阅 OAuth，失效的旧 Key 会遮住正常登录。

### 切换供应商后仍请求旧地址

关闭 Claude Code，检查启动 Shell 中的 `ANTHROPIC_BASE_URL`，再查看管理工具是否通过本地代理接管。某些设置可以热加载，环境变量通常在启动时读取。

### 401 与 404 反复交替

401 更接近认证问题；404 更接近地址、路径或模型路由问题。不要一次同时改变 Base URL、Token、模型名和代理设置，否则即使成功也不知道是哪项修复起作用。

### 配置文件存在，但 `/status` 没显示

检查 JSON 是否有效，以及文件是否放在正确的用户、项目或本地作用域。Claude Code 只会在成功加载至少一个设置时显示对应来源。

### 核对来源

- [Claude Code settings](https://code.claude.com/docs/en/settings)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Claude Code environment variables](https://code.claude.com/docs/en/env-vars)
- [Claude Code LLM gateway configuration](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)
- [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
