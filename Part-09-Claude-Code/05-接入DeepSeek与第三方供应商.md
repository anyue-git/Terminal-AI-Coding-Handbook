# 05 Claude Code 接入 DeepSeek 与第三方供应商

> 最近核对：2026-07-29
>
> Claude Code、DeepSeek API、模型名称和第三方 Gateway 都可能快速变化。实际配置前，应同时查看 Claude Code 当前官方文档、供应商当前官方文档和本机 `claude --version`。

Claude Code 是终端客户端。它负责读取项目、调用工具、修改文件、运行命令和管理会话；真正完成推理的模型由后端供应商提供。因此“使用 Claude Code”不一定等于“请求发送给 Anthropic”，必须检查当前 Base URL、认证来源和模型映射。

整个链路可以分成五层：

```text
Claude Code 客户端
→ 终端交互、权限和工具执行

认证
→ OAuth、API Key、云身份或 Gateway 凭据

Base URL 与协议
→ 请求发送到哪里、使用什么 API 格式

模型映射
→ 主模型、快速模型、子 Agent 分别调用谁

供应商
→ 计费、日志、限速、数据处理和服务支持
```

本章给出一套安全的接入与验证流程。配置文件、凭据存储和多实例原理见 Part 10C，本章不重复把所有配置机制塞进一篇。

## 1. 先决定使用哪条接入路线

Claude Code 常见后端路线包括：

### Anthropic 官方账户或 API

适合：

- 希望使用 Claude 模型；
- 需要 Claude Code 新功能的完整兼容；
- 不希望维护第三方模型映射；
- 可以使用支持的 Claude 账户或 Anthropic Console。

### 受支持的企业云平台

包括 Claude Code 官方支持的 Amazon Bedrock、Google Cloud 平台和 Microsoft Foundry 等路线。组织通常统一管理身份、审计、区域和费用。

### DeepSeek 官方 Anthropic 兼容接口

DeepSeek 提供 Anthropic API 格式端点和 Claude Code 接入说明。终端仍运行 `claude`，但模型请求发送到 DeepSeek，使用 DeepSeek API Key 和 DeepSeek 计费。

这不是把 Claude 网页订阅转换成 API，也不是使用浏览器 Cookie。

### 企业 LLM Gateway

企业可以让 Claude Code 先连接内部 Gateway，再由 Gateway 处理：

- 上游凭据；
- 统一认证；
- 成本和限速；
- 审计日志；
- 模型路由；
- 故障转移；
- 员工离职后的凭据撤销。

### 第三方兼容供应商或中转

这类服务质量、协议完整性、日志和安全性差异很大。能够返回聊天文本，不代表完整支持 Claude Code 的工具调用、长上下文、Web Search、子 Agent 和新协议字段。

## 2. 先确认 Claude Code 客户端本身正常

接入任何供应商前执行：

```bash
type -a claude
claude --version
claude doctor
```

安装和更新应按 Claude Code 当前官方 Setup 完成。DeepSeek 接入页面中的客户端安装小节可能不会与 Claude Code 最新安装要求同步；例如 npm 所需 Node.js 版本可能已经变化。因此：

```text
Claude Code 安装
→ 以 Claude Code 官方文档为准

DeepSeek 环境变量和模型映射
→ 以 DeepSeek 官方接入文档为准
```

不要因为供应商教程仍展示旧 npm 要求，就降级或混装多个 Claude Code 版本。

## 3. 配置前先观察当前路由

不要打印 Token，只检查非敏感元数据：

```bash
printf 'base_url=%s\n' "${ANTHROPIC_BASE_URL:-<not set>}"
printf 'model=%s\n' "${ANTHROPIC_MODEL:-<not set>}"
printf 'opus=%s\n' "${ANTHROPIC_DEFAULT_OPUS_MODEL:-<not set>}"
printf 'sonnet=%s\n' "${ANTHROPIC_DEFAULT_SONNET_MODEL:-<not set>}"
printf 'haiku=%s\n' "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-<not set>}"
printf 'subagent=%s\n' "${CLAUDE_CODE_SUBAGENT_MODEL:-<not set>}"

test -n "$ANTHROPIC_API_KEY" && echo 'ANTHROPIC_API_KEY is set'
test -n "$ANTHROPIC_AUTH_TOKEN" && echo 'ANTHROPIC_AUTH_TOKEN is set'
```

还要检查设置来源：

```bash
find .claude -type f -print 2>/dev/null
ls -la ~/.claude/settings.json 2>/dev/null || true
```

Claude Code 中运行：

```text
/status
```

配置可能来自 Shell 环境、用户设置、项目设置、企业管理配置或切换工具。只看 `.zshrc` 不能证明最终路由。

## 4. DeepSeek 当前官方 Claude Code 配置

截至 2026-07-29，DeepSeek 官方 Claude Code 接入页给出的 macOS/Linux 环境变量是：

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

这里：

```text
ANTHROPIC_BASE_URL
→ DeepSeek 的 Anthropic 兼容端点

ANTHROPIC_AUTH_TOKEN
→ DeepSeek API Key，不是 Anthropic Key

ANTHROPIC_MODEL
→ Claude Code 主模型

DEFAULT_OPUS / SONNET / HAIKU
→ 当客户端按角色选择模型时的映射

CLAUDE_CODE_SUBAGENT_MODEL
→ 子 Agent 使用的模型

CLAUDE_CODE_EFFORT_LEVEL
→ 当前官方建议的努力级别
```

模型名称尤其容易变化。复制命令前应重新打开 DeepSeek 官方接入页，确认主模型、快速模型和子 Agent 映射仍然有效。

## 5. 不要把真实 Key 直接写进命令历史

不推荐：

```bash
export ANTHROPIC_AUTH_TOKEN="sk-real-secret"
```

终端历史、录屏、日志和进程环境都可能暴露敏感值。

一次性测试可以在子 Shell 中隐藏输入：

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

退出这个子 Shell 后，变量不会继续保留在父 Shell 中。这仍不是长期凭据管理方案，正式使用应选择系统 Keychain、组织 Secret 工具、权限受限的本地配置或可信供应商管理工具。

不要把真实 Key 写入：

- Git 仓库；
- `CLAUDE.md`；
- `.claude/settings.json` 的共享部分；
- `.env.example`；
- 教程截图；
- Issue 和 PR；
- AI 对话；
- 多人可读脚本。

## 6. `ANTHROPIC_AUTH_TOKEN` 与 `ANTHROPIC_API_KEY`

DeepSeek 的 Claude Code 官方接入示例使用：

```text
ANTHROPIC_AUTH_TOKEN
```

DeepSeek 的通用 Anthropic SDK 兼容示例则可能使用：

```text
ANTHROPIC_API_KEY
```

它们出现在不同客户端场景中。接入 Claude Code 时，优先按照 DeepSeek 当前 Claude Code 页面使用的变量，不要同时设置多个认证变量后再猜客户端选择了哪一个。

排错时只检查是否存在，不要输出值：

```bash
test -n "$ANTHROPIC_AUTH_TOKEN" && echo 'auth token is set'
test -n "$ANTHROPIC_API_KEY" && echo 'api key is set'
```

## 7. 第一次只验证文本和路由

创建或进入一个不含敏感信息的练习项目：

```bash
cd ~/terminal-practice/claude-first-project
pwd
git status
```

启动 Plan 模式：

```bash
claude --permission-mode plan
```

第一条任务：

```text
不要读取文件，不要调用工具。
请只回答：当前会话是否能够完成普通文本响应，并说明你看到的模型名称。
```

在 Claude Code 中运行：

```text
/status
```

记录：

- Claude Code 版本；
- Base URL；
- 主模型和快速模型映射；
- 供应商返回的错误；
- 是否发生额外登录提示。

不要要求模型回显 API Key。

## 8. 第二步验证只读文件工具

文本正常后：

```text
只读当前目录中的 greeting.py 和 test_greeting.py。
总结各自用途，不要修改文件，不要运行命令。
```

确认：

- 文件读取权限正常；
- 项目目录识别正确；
- 没有读取 `.env` 和项目外目录；
- 模型能正确理解内容；
- 没有工具协议错误。

普通聊天成功并不能证明工具调用成功，因此必须分阶段测试。

## 9. 第三步验证无副作用命令

```text
只运行以下命令：
- pwd
- git status --short
- python3 -m unittest -v

不要修改文件，不要安装依赖，不要执行 Git 写操作。
完成后报告每条命令的退出状态。
```

这一阶段验证 Bash 工具、命令输出和模型对退出状态的处理。

如果供应商只实现了基础消息接口，而工具调用格式不完整，问题可能在此阶段出现。

## 10. 第四步验证最小编辑

在专用分支或练习项目中：

```text
只修改 test_greeting.py，增加一个简单测试。
不要修改其他文件，不要执行 git add、commit 或 push。
完成后运行 python3 -m unittest -v 并停止。
```

人工检查：

```bash
git status --short
git diff --stat
git diff
```

只有文本、读取、Bash、编辑和测试都正常后，才能认为当前供应商基本适配日常 Claude Code 工作流。

## 11. 子 Agent、Web Search 和长上下文需要单独测试

DeepSeek 当前官方说明中，Claude Code Web Search 可以通过 DeepSeek API 触发，并会产生额外模型请求和 Token 费用。启用前应确认：

- 当前任务是否真的需要联网；
- 搜索内容是否会再次发送给模型总结；
- 费用和限速；
- 结果中的提示注入；
- 学校、团队或公司的数据规则。

还要分别测试：

- 子 Agent 是否使用预期模型；
- 快速模型映射是否有效；
- 长上下文是否达到供应商宣传范围；
- Tool Call 是否稳定；
- Prompt 缓存是否支持；
- 流式输出是否正常；
- MCP 与 Hooks 是否受影响。

一个简单问答成功，不能代表这些高级能力全部兼容。

## 12. 兼容接口不等于 Claude 模型

DeepSeek 的 Anthropic 兼容端点让请求格式进入 Anthropic API 生态，但实际模型仍是 DeepSeek。

可能存在差异：

- 代码质量和推理风格；
- 工具调用成功率；
- 上下文限制；
- 思考和努力级别；
- 模型角色映射；
- 子 Agent 行为；
- Web Search；
- 流式事件；
- 缓存和计费；
- Claude Code 新字段的适配速度。

不要把界面中显示的 Opus、Sonnet 或 Haiku 角色名误认为实际调用了 Anthropic 对应模型。环境变量可能把这些角色映射到其他模型。

## 13. DeepSeek 官方支持边界与 Claude Code 官方支持边界

DeepSeek 的接入页面明确把 Claude Code称为第三方工具，并表示不保证其有效性和安全性。另一方面，Claude Code 官方 Gateway 文档也说明，Anthropic 不为第三方 Gateway 背书或审计，并不支持通过 Gateway 将 Claude Code 路由到非 Claude 模型。

因此这条路线应理解为：

```text
DeepSeek 提供的兼容接入方案
≠ Anthropic 对非 Claude 模型的官方支持承诺
```

遇到兼容问题时，可能需要分别向客户端、供应商或 Gateway 维护者排查，不能假设任一方会为完整组合负责。

## 14. 企业 Gateway 的合理用途

组织 Gateway 可以让上游供应商 Key 留在服务器端，开发者只持有个人 Gateway 凭据，并统一完成：

- 员工身份；
- 用量归属；
- 预算和限速；
- 审计日志；
- 上游模型切换；
- 离职撤销；
- 区域与数据策略。

但 Gateway 也成为关键基础设施。它必须持续跟进 Claude Code 新增的 API 字段和功能，否则可能出现：

- 普通聊天正常、工具调用失败；
- 新模型字段被丢弃；
- 流式事件不完整；
- Token 计数错误；
- 子 Agent 和 Web Search 不兼容；
- 错误码被重写。

个人用户不应仅因为 Gateway 提供“统一模型入口”，就忽略运营者、日志、凭据和数据去向。

## 15. 第三方切换工具改变的是配置，不是供应商信誉

CC Switch 一类工具可以管理：

- Base URL；
- API Key 引用；
- 主模型和角色模型；
- MCP 与 Skills；
- 多客户端配置；
- 本地路由。

它不会自动保证：

- 上游模型真实；
- 额度和计费准确；
- 服务不保存源码；
- API Key 不会泄露；
- 工具调用完整兼容；
- 供应商遵守组织政策。

使用后仍要通过 `/status`、环境变量元数据和真实请求验证最终路由。详细分析见：

- [CC Switch、ccswitch 与 Cockpit Tools](../Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)

## 16. 常见错误：仍然要求 Anthropic 登录

可能原因：

- 当前 Shell 没有加载 DeepSeek 变量；
- 配置写在另一个终端或用户；
- Claude Code由 GUI、IDE 或后台进程启动，没有继承当前 Shell；
- Base URL 拼写错误；
- 认证变量使用错误；
- 项目或组织设置覆盖环境；
- 切换工具没有真正启用配置；
- 本地 Gateway 没有运行。

检查：

```bash
printf '%s\n' "${ANTHROPIC_BASE_URL:-<not set>}"
printf '%s\n' "${ANTHROPIC_MODEL:-<not set>}"
test -n "$ANTHROPIC_AUTH_TOKEN" && echo 'auth token is set'
type -a claude
claude --version
```

不要把 Token 打印出来。

## 17. 401、403 与认证错误

检查：

```text
API Key 是否属于当前供应商
Base URL 是否与 Key 匹配
Key 是否被停用或限制
账户是否有额度
认证变量是否正确
Gateway 是否要求额外 Header
本机时间是否严重错误
组织策略是否拒绝当前请求
```

不要用同一个 Key 在多个来源不明的中转站反复测试。怀疑泄露时立即撤销并生成新 Key。

## 18. 404、模型不存在和映射错误

常见原因：

- Base URL 缺少 `/anthropic`；
- 使用了通用 OpenAI 兼容端点；
- 模型 ID 已更新；
- `[1m]` 等上下文后缀被遗漏或写错；
- 主模型和默认角色模型不一致；
- 子 Agent 模型不存在；
- Gateway 没有对应路由。

不要凭记忆猜模型名。重新查看供应商当前官方接入页，并记录：

```bash
printf '%s\n' "$ANTHROPIC_MODEL"
printf '%s\n' "$ANTHROPIC_DEFAULT_OPUS_MODEL"
printf '%s\n' "$ANTHROPIC_DEFAULT_SONNET_MODEL"
printf '%s\n' "$ANTHROPIC_DEFAULT_HAIKU_MODEL"
printf '%s\n' "$CLAUDE_CODE_SUBAGENT_MODEL"
```

## 19. 普通聊天正常，但工具调用失败

按最小能力逐步测试：

```text
1. 纯文本响应
2. 读取一个短文件
3. 运行 pwd
4. 运行 git status
5. 编辑一个测试文件
6. 运行单元测试
7. 子 Agent
8. Web Search
9. MCP
```

记录哪一步第一次失败。这样可以区分：

- 基础 API；
- Tool Call 协议；
- 权限规则；
- 模型映射；
- Gateway 转发；
- 外部工具问题。

不要直接在真实项目中执行大型任务来测试兼容性。

## 20. 上下文过长、限速和费用错误

长任务失败可能来自：

- 当前模型上下文不足；
- 供应商对长上下文模型有单独限速；
- `[1m]` 模型需要不同权限或价格；
- 输入缓存没有命中；
- Web Search 产生额外请求；
- 子 Agent 并发放大费用；
- Gateway 自己设置预算和速率限制。

检查供应商错误正文和用量面板，不要只看 Claude Code 的最后一行提示。

长上下文并不代表应把整个仓库、日志和数据全部读入。先用搜索和子 Agent 缩小范围，仍然是更可靠的工作方式。

## 21. 新终端中配置消失

直接 `export` 只影响当前 Shell 和它启动的子进程。关闭窗口后，新 Shell 不会自动继承。

长期配置可以选择：

- 系统 Keychain 或 Secret Manager；
- 权限受限的本地脚本；
- 企业管理设置；
- Gateway 凭据分发；
- 可信配置切换工具；
- 专用 Claude 配置目录或隔离实例。

不要把 `.zshrc` 当作加密保险箱，也不要反复向其中追加同一组变量。

## 22. 恢复 Anthropic 官方路线

临时 DeepSeek 子 Shell退出后，父 Shell不会保留变量。如果变量已经写入当前 Shell，可执行：

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset CLAUDE_CODE_SUBAGENT_MODEL
unset CLAUDE_CODE_EFFORT_LEVEL
```

同时检查是否还设置了：

```bash
test -n "$ANTHROPIC_API_KEY" && echo 'ANTHROPIC_API_KEY is still set'
```

如果变量写入 `~/.zshrc`、`~/.zprofile`、用户 `settings.json`、项目设置或切换工具，仅在当前 Shell `unset` 不能永久恢复。需要从实际来源删除或切换。

新开终端后检查：

```bash
printf '%s\n' "${ANTHROPIC_BASE_URL:-<not set>}"
type -a claude
claude doctor
```

启动 Claude Code，使用 `/status` 确认认证和模型后端，再按官方账户或 Console 流程登录。

## 23. 切换后端前保存元数据，不保存秘密

可以建立一个本地诊断文件：

```bash
{
  printf 'date=%s\n' "$(date -Iseconds)"
  printf 'host=%s\n' "$(hostname)"
  printf 'claude=%s\n' "$(claude --version 2>&1)"
  printf 'base_url=%s\n' "${ANTHROPIC_BASE_URL:-<not set>}"
  printf 'model=%s\n' "${ANTHROPIC_MODEL:-<not set>}"
  printf 'haiku=%s\n' "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-<not set>}"
  printf 'subagent=%s\n' "${CLAUDE_CODE_SUBAGENT_MODEL:-<not set>}"
  test -n "$ANTHROPIC_AUTH_TOKEN" && echo 'auth_token=set'
} > claude-provider-diagnostic.txt
```

检查后不要提交：

```bash
git status --short
```

诊断文件不含 Key，但可能包含内部 Base URL、主机名和模型信息，发送给外部人员前仍需脱敏。

## 24. 选择供应商时真正需要比较什么

不要只比较模型名称和标价。还要比较：

```text
客户端功能兼容度
工具调用稳定性
长上下文与实际限速
缓存和附加请求费用
数据保留与训练政策
日志和审计
网络延迟与可用性
模型真实性与版本透明度
凭据存储
组织与地区合规
故障支持责任
```

对高价值私有代码，较短请求链路和清晰责任边界通常比最低单价更重要。

## 25. 给 AI CLI 的供应商切换边界

```text
只读检查当前 Base URL、模型映射和配置来源，不要输出任何 API Key。

不要修改 ~/.zshrc、~/.zprofile、~/.claude/settings.json 或项目设置，除非先说明：
- 当前生效来源；
- 准备修改的文件；
- 是否会影响其他项目；
- 凭据如何安全提供；
- 验证方式；
- 恢复官方路线的方法。

先在独立练习项目按顺序验证：
文本 → 文件读取 → 只读 Bash → 最小编辑 → 测试。

不要使用浏览器 Cookie、Session Token、他人账号缓存或来源不明的订阅转 API 服务。
```

## 26. 一套完整接入检查清单

```text
客户端
□ claude --version 已确认
□ 安装方式唯一且更新机制清楚

供应商
□ Base URL 来自官方文档
□ Key 属于当前供应商
□ 主模型、快速模型和子 Agent 映射已核对
□ 计费和数据处理主体明确

配置
□ 不打印真实凭据
□ 变量和 settings 的优先级清楚
□ 新终端和 GUI 启动环境已验证
□ 恢复官方路线的方法已记录

能力测试
□ 普通文本
□ 文件读取
□ 只读命令
□ 文件编辑
□ 测试
□ 子 Agent
□ Web Search / MCP 按需验证

安全
□ 不使用 Cookie 或 Session
□ 不提交 Key
□ 不在真实生产项目直接试错
□ 不把兼容端点理解为官方完整支持
```

继续阅读：

- [安装、认证与第一次启动](01-安装登录与启动.md)
- [权限、审批、Sandbox 与安全边界](02-权限审批与安全边界.md)
- [Claude Code 的配置、凭证与网关](../Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)
- [CC Switch、ccswitch 与 Cockpit Tools](../Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)

官方参考：

- [DeepSeek：接入 Claude Code](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code/)
- [DeepSeek：Anthropic API](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api/)
- [Claude Code：Other LLM gateways](https://code.claude.com/docs/en/llm-gateway)
- [Claude Code：Authentication](https://code.claude.com/docs/en/authentication)
