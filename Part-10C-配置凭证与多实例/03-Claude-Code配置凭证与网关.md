# 03 Claude Code 的配置、凭证与网关

> 最近核对：2026-07-29

Claude Code 不把状态集中在一个 TOML 中，而是组合使用 `settings.json`、环境变量、`CLAUDE.md`、`.mcp.json`、系统凭证库和登录缓存。切换工具还可能同时修改 JSON、Shell 变量、Keychain 与本地代理，而界面只显示一个“当前供应商”。排查时需要沿着“配置来源—认证优先级—请求地址与 Header—进程实际状态”逐层确认。Claude Desktop 与 Claude Code 不是同一认证入口，本章只讨论终端客户端。

## 1. 配置文件、项目规则和认证缓存属于不同作用域

用户级设置通常位于：

```text
~/.claude/settings.json
```

项目共享设置与个人本地设置分别是：

```text
PROJECT_ROOT/.claude/settings.json
PROJECT_ROOT/.claude/settings.local.json
```

共享设置可以进入 Git，本地设置应停留在当前机器并检查 `.gitignore`。项目附近还常见：

```text
~/.claude.json       OAuth 会话、部分 MCP、信任状态和缓存
PROJECT_ROOT/.mcp.json
PROJECT_ROOT/CLAUDE.md
```

`~/.claude.json` 可能包含认证和会话信息，并非普通偏好文件；`.mcp.json` 定义项目共享 MCP；`CLAUDE.md` 保存项目指导。日常只检查路径与权限，不直接输出认证文件正文：

```bash
ls -ld ~/.claude 2>/dev/null
ls -l ~/.claude/settings.json ~/.claude.json 2>/dev/null
find . \
  \( -path '*/.claude/settings.json' \
  -o -path '*/.claude/settings.local.json' \
  -o -name CLAUDE.md \
  -o -name .mcp.json \) -print
```

用户设置适合跨项目共享的个人默认，项目设置适合团队共同维护的权限和工具规则，本地设置用于个人实验。一个简化项目设置可以是：

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

JSON 使用双引号，最后一项不能留下多余逗号。修改后在 Claude Code 中运行 `/status` 查看 Setting sources；文件存在只能证明路径存在，不能证明解析和加载成功。

认证缓存另有自己的位置。Claude Code 可以使用 Claude.ai 订阅、Claude Console、企业云、API Key 或 Gateway；macOS 通常依赖系统 Keychain，Linux 常见 `~/.claude/.credentials.json`，权限应为 `0600`。登录异常时先运行：

```bash
claude doctor
```

随后结合 `/status`、`/logout` 与 `/login` 判断，不要直接删除 Keychain 条目或整份凭证目录，否则可能让仍正常的会话一起失效。

## 2. 认证优先级决定请求最终由谁承担

Claude Code 同时发现多种认证时会按优先级选择。当前官方顺序中，云平台认证优先，其后是 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_API_KEY`、`apiKeyHelper`、`CLAUDE_CODE_OAUTH_TOKEN`，最后才是 `/login` 保存的订阅 OAuth。因此，已经登录 Claude Max 的 Shell 若残留 API Key，客户端仍可能走 API 计费。

只检查变量是否存在，不显示值：

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

希望回到订阅登录时，可在当前 Shell 临时清除覆盖变量：

```bash
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_API_KEY
unset CLAUDE_CODE_OAUTH_TOKEN
unset ANTHROPIC_BASE_URL
```

重新启动后用 `/status` 验证。新终端再次出现变量，来源通常位于 `.zshrc`、`.zprofile`、环境管理器或切换工具。

几种名称相近的凭证承担不同请求语义：`ANTHROPIC_API_KEY` 通常作为 `X-Api-Key` 发送，面向 Anthropic Console API；`ANTHROPIC_AUTH_TOKEN` 作为 Bearer Token，常见于 Gateway；`CLAUDE_CODE_OAUTH_TOKEN` 可由 `claude setup-token` 生成，适合无浏览器脚本和自动化。它们不能随意互换。

检查凭证时只确认存在或长度：

```bash
if [ -n "$ANTHROPIC_API_KEY" ]; then
  printf 'ANTHROPIC_API_KEY 已设置，长度为 %s。\n' \
    "${#ANTHROPIC_API_KEY}"
fi
```

长度不能证明凭证有效。`apiKeyHelper` 则让 Claude Code 在认证时执行命令并读取临时密钥，适合企业 Vault 和轮换 Token：

```json
{
  "apiKeyHelper": "/Users/YOUR_USERNAME/bin/get-claude-key.sh"
}
```

```bash
#!/bin/sh
exec /usr/local/bin/company-vault read claude-code-token
```

```bash
chmod 700 ~/bin/get-claude-key.sh
```

脚本和它调用的程序都属于凭证链，不能硬编码 Key，也不应打开记录 stdout 的调试日志。刷新间隔可由当前版本的 `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` 控制，HTTP 401 也可能触发重新获取。

## 3. Gateway 同时改变地址、认证头和模型责任链

连接 Bearer Token 网关的常见结构是：

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_GATEWAY_TOKEN"
claude
```

地址、Header 和模型映射必须以网关文档为准。API Key 与 Auth Token 同时设置不会提高成功率，反而可能因为优先级遮住正在测试的凭证。

一次性测试可以隐藏输入并把变量限定在当前进程：

```bash
IFS= read -r -s GATEWAY_TOKEN
printf '\n'
ANTHROPIC_BASE_URL="https://gateway.example.com" \
ANTHROPIC_AUTH_TOKEN="$GATEWAY_TOKEN" \
claude
unset GATEWAY_TOKEN
```

直接在命令中写真实值仍可能进入历史。长期配置更适合 Keychain、Secret Manager 或 Helper，不把 Token 写进项目 `settings.json`。

DeepSeek 和其他 Anthropic 兼容服务会同时改变请求入口、认证方、计费方与模型提供方。排查应从客户端能否启动开始，依次检查 Setting sources、环境变量是否覆盖登录、Base URL、认证头、模型别名、Tool Call 和流式协议。普通文本成功只证明最基本请求可用，不能推出 Agent 工具、长上下文、缓存、图片和流式事件全部兼容；“兼容 Claude”还要区分 Messages API、Claude Code Tool Call 与简单文本接口。

## 4. 切号、多开和故障排查都要确认进程实际继承的状态

替换同一套 Keychain 或凭证文件适合串行切换账号。正在运行的进程可能缓存旧状态，切换后需要退出并重新启动。两个账号同时运行则不能反复替换活动凭证，需要独立 macOS 用户、容器或切换工具提供的隔离环境。

`CLAUDE_CONFIG_DIR` 可以影响部分配置与凭证路径，但 macOS 官方 OAuth 依赖 Keychain，仅靠目录变量是否能完整隔离，要按当前版本和管理工具实现验证。有些多开工具因此还会维护 Keychain 条目、环境变量和独立启动参数；出现两个窗口只说明启动了两个进程，不能证明账号、历史和凭证已经隔离。

故障现象可以按来源判断：已登录订阅却提示无效 API Key时，用 `/status` 查看活动认证并检查残留变量；切换供应商后仍请求旧地址时，关闭旧进程，检查启动 Shell 的 `ANTHROPIC_BASE_URL` 和管理工具的本地代理；401 更接近认证，404 更接近地址、路径或模型路由。配置文件存在但 `/status` 没显示时，验证 JSON 语法、文件路径和作用域。一次只改变 Base URL、Token、模型或代理中的一项，并始终保留回到官方登录与官方端点的路径，否则即使偶然成功，也无法确认是哪项修改生效。

核对来源：

- [Claude Code settings](https://code.claude.com/docs/en/settings)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Claude Code environment variables](https://code.claude.com/docs/en/env-vars)
- [Claude Code LLM gateway configuration](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)
- [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
