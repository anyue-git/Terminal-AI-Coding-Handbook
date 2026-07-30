# 05 Claude Code 接入 DeepSeek 与第三方供应商

> 最近核对：2026-07-29
>
> Claude Code、DeepSeek API、模型名称和 Gateway 都可能变化。配置前同时查看 Claude Code 与供应商官方文档，并运行 `claude --version`。

Claude Code 是终端客户端，真正处理模型请求的是后端服务。启动命令仍然是 `claude`，请求却可能发往 Anthropic、DeepSeek、企业 Gateway 或其他兼容供应商。判断当前路线时，需要同时看认证变量、Base URL、模型映射和最终计费主体。

配置文件、凭据存储和多实例原理由 Part 10C 集中解释。本章只演示怎样观察路由、临时接入 DeepSeek、验证兼容能力并恢复原路线。

## 1. 先确认客户端与当前路由

客户端本身应先通过基本检查：

```bash
type -a claude
claude --version
claude doctor
```

然后查看路由元数据，不打印 Token：

```bash
printf 'base_url=%s\n' "${ANTHROPIC_BASE_URL:-<not set>}"
printf 'model=%s\n' "${ANTHROPIC_MODEL:-<not set>}"
printf 'opus=%s\n' "${ANTHROPIC_DEFAULT_OPUS_MODEL:-<not set>}"
printf 'sonnet=%s\n' "${ANTHROPIC_DEFAULT_SONNET_MODEL:-<not set>}"
printf 'haiku=%s\n' "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-<not set>}"
printf 'subagent=%s\n' "${CLAUDE_CODE_SUBAGENT_MODEL:-<not set>}"

test -n "${ANTHROPIC_API_KEY:-}" && echo 'ANTHROPIC_API_KEY is set'
test -n "${ANTHROPIC_AUTH_TOKEN:-}" && echo 'ANTHROPIC_AUTH_TOKEN is set'

find .claude -type f -print 2>/dev/null
ls -la ~/.claude/settings.json 2>/dev/null || true
```

会话中再用 `/status` 查看认证和模型。配置可能来自当前 Shell、用户或项目 Settings、组织管理、启动脚本和切换工具；只检查 `.zshrc` 不能证明 Claude Code 最终采用了哪一层。

## 2. 后端路线意味着不同责任主体

常见路线大致分为：

- Anthropic 官方账户或 Console API；
- 官方支持的企业云平台；
- DeepSeek 的 Anthropic 兼容端点；
- 组织维护的 LLM Gateway；
- 第三方兼容供应商或中转。

DeepSeek 路线使用 DeepSeek API Key、DeepSeek 模型和 DeepSeek 计费，并不是把 Claude 网页订阅转换成 API。企业 Gateway 可以统一身份、预算、模型路由和撤销，但协议适配与故障排查也由 Gateway 团队承担。第三方兼容服务则需要单独确认模型、日志、数据处理和支持责任。

一个端点能够返回普通文字，只能说明最基本请求成功。文件工具、Bash、流式事件、子 Agent、Web Search、MCP、长上下文和缓存都可能依赖更多协议字段，需要分别测试。

## 3. 在临时子 Shell 中测试 DeepSeek

截至核对日期，DeepSeek 官方 Claude Code 接入页给出的 macOS/Linux 变量是：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="YOUR_DEEPSEEK_API_KEY"
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_EFFORT_LEVEL="max"
```

这些名称和推荐映射容易变化，复制前重新核对官方页面。Claude Code 场景按当前页面使用 `ANTHROPIC_AUTH_TOKEN`，不要同时设置多个认证变量后猜测优先级。

第一次测试可以放在子 Shell 中，并通过隐藏输入读取 Key：

```bash
(
  export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
  export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
  export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
  export CLAUDE_CODE_EFFORT_LEVEL="max"

  printf 'DeepSeek API Key: ' >&2
  IFS= read -r -s ANTHROPIC_AUTH_TOKEN
  printf '\n' >&2
  export ANTHROPIC_AUTH_TOKEN

  claude --permission-mode plan
)
```

退出括号内的 Shell 后，这些临时变量不会保留在父 Shell。这个方式适合兼容性试验，不是长期凭据管理方案。正式使用可选择 Keychain、Secret Manager、权限受限的本地环境注入、企业凭据分发或经过审查的配置工具。

## 4. 用能力阶梯判断“兼容到什么程度”

先在没有秘密和重要数据的练习项目中确认普通文本，然后逐层增加能力：

```text
普通文本
→ 读取一个短文件
→ pwd 与 git status --short
→ 项目单元测试
→ 专用分支中的最小编辑
→ 子 Agent
→ Web Search
→ MCP 与 Hooks
→ 长上下文、流式事件和缓存
```

每一层只增加一个变量。文本成功后立即测试大型真实项目，很难判断失败来自工具调用、模型映射、上下文、Gateway 还是项目本身。

最小编辑后查看真实工作区：

```bash
git status --short
git diff --stat
git diff
```

普通文本、Read、Bash、Edit 和项目测试都正常，可以称为“基本适配日常 Claude Code 工作流”。子 Agent、Web Search、长上下文和缓存仍需按需单独验证，因为主模型、快速模型和子 Agent 可能映射到不同后端。

界面中的 Opus、Sonnet 或 Haiku 在兼容路线中可能只是角色名称，实际后端仍是 DeepSeek 或其他供应商模型。模型质量、工具调用、上下文、缓存和计费应按实际供应商理解。

## 5. 根据第一次失败的位置排查

仍要求 Anthropic 登录时，检查当前进程是否继承了环境变量、Base URL 与认证变量是否成对、项目或组织 Settings 是否覆盖，以及切换工具或本地 Gateway 是否正在接管。

常见错误可以按层判断：

- `401` 或 `403`：Key 所属供应商、额度、权限、认证头、系统时间或组织策略；
- `404`、模型不存在：端点是否缺少 `/anthropic`、是否误用其他兼容协议、模型 ID 或上下文后缀是否过期；
- 文本正常但工具失败：从 Read、Bash、Edit、测试、子 Agent、Web Search、MCP 的顺序找到第一层失败；
- 长任务中途失败：检查单模型限速、额外子请求、Gateway 预算、流式事件和供应商错误正文。

企业或第三方 Gateway 出现问题时，需要区分客户端、Gateway 和上游供应商。Claude Code 官方 Gateway 文档不会替第三方 Gateway 或非 Claude 模型保证完整兼容，DeepSeek 的第三方工具接入页也不等于 Anthropic 对该组合提供支持。

## 6. 恢复原路线

若所有变量只存在于临时子 Shell，退出后即可恢复。已经写入当前环境时清除：

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset CLAUDE_CODE_SUBAGENT_MODEL
unset CLAUDE_CODE_EFFORT_LEVEL

test -n "${ANTHROPIC_API_KEY:-}" && echo 'ANTHROPIC_API_KEY is still set'
```

若变量来自 `.zshrc`、`.zprofile`、用户或项目 Settings、企业管理、CC Switch、ccswitch 或 Cockpit Tools，当前 Shell 的 `unset` 只能临时覆盖。应回到真正的配置来源停止接管或恢复备份，再开新终端运行：

```bash
type -a claude
claude doctor
```

进入会话后用 `/status` 确认认证、Base URL 和模型后端已经回到预期路线。

## 7. 接入完成后应该说清什么

一套可维护的接入至少能够回答：客户端版本是什么，请求发到哪个 Base URL，凭据属于哪个供应商，主模型、快速模型和子 Agent怎样映射，谁负责计费与数据处理，哪些能力已经实际测试，以及怎样恢复官方路线。

真实 Key 不进入 Git、共享 Settings、`CLAUDE.md`、截图、Issue、PR 或 AI 对话。浏览器 Cookie、Session Token、他人登录缓存和来源不明的“订阅转 API”也不属于正常的供应商接入方式。

继续阅读：[配置、凭证、供应商与实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)、[Claude Code 的配置、凭证与网关](../Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)和[CC Switch、ccswitch 与 Cockpit Tools](../Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)。

官方参考：

- [Claude Code documentation](https://code.claude.com/docs/)
- [Claude Code LLM gateway configuration](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)
- [DeepSeek Claude Code 接入文档](https://api-docs.deepseek.com/guides/anthropic_api)