# 06 Claude Code、Codex CLI 与 Grok Build 对照协作

> 最近核对：2026-07-30  
> 三个工具变化很快。本章只比较相对稳定的工作方式；安装、认证、参数和权限细节以各自专章、本机 `--help` 与官方文档为准。

Claude Code、Codex CLI 和 Grok Build 都能读取项目、修改文件、运行命令和查看 Git 差异。选择主力工具时，模型能力只是一个变量；任务需要多长的交互、是否要进入脚本或 CI、项目已经维护哪套规则文件、是否需要结构化输出、独立 Review、Worktree 或特定扩展，往往更能决定实际体验。

## 1. 用稳定差异判断工具是否匹配任务

| 维度 | Claude Code | Codex CLI | Grok Build |
|---|---|---|---|
| 交互入口 | `claude` | `codex` | `grok` |
| 非交互 | 打印模式等 | `codex exec` | Headless / single prompt |
| 项目规则 | `CLAUDE.md`、Settings | `AGENTS.md`、Codex 配置 | 项目规则、Memory、用户与项目配置 |
| 权限结构 | Permission Mode、Allow/Deny、Sandbox | 审批策略与 Sandbox 分开；另有 beta Permission Profiles | Ask、Auto、Always-approve 与 Sandbox 分开 |
| 会话能力 | 继续、恢复、分叉、命名会话 | 恢复、分叉、Review | 列表、恢复、继续、分叉 |
| 扩展能力 | Hooks、MCP、子 Agent | MCP、Skills、Hooks、Subagents | Skills、Plugins、Agents、Hooks、MCP、LSP、ACP |
| Worktree | Claude Worktree 或原生 Git Worktree | 通常配合原生 Git Worktree | 提供较直接的 Worktree 会话入口 |
| 结构化输出 | 依当前打印输出能力 | JSONL、Schema、最后消息文件 | JSON、streaming JSON |

表格给的是选择方向，不是永久功能清单。实际使用前查看当前版本：

```bash
claude --version
claude --help

codex --version
codex --help

grok version
grok --help
```

Claude Code 适合持续阅读较大代码库、多阶段交互，或项目已经认真维护 `CLAUDE.md`、Hooks、MCP 和子 Agent；Codex CLI 适合把交互开发、`codex exec` 自动化和 `codex review` 接入同一流程；Grok Build 适合需要 Ask/Auto、独立 Plan、Headless、streaming JSON、Grok Worktree 或更广扩展类型的场景。具体能力与权限由各产品专章解释，这里不再复制参数清单。

## 2. 任务决定主实施者，不要求三套工具同时出现

小型修改通常只需要一套熟悉的客户端、人工 diff 和一次独立阅读。中型任务若依赖较长的代码探索与多轮澄清，Claude Code 往往更顺手；需要脚本化、JSONL、Schema 或独立 Review 时，Codex CLI 更合适；任务明确依赖 Grok Headless、Worktree 或扩展系统时，再选择 Grok Build。

项目已有成熟的 `CLAUDE.md`、`AGENTS.md` 或 `.grok` 配置时，沿用现有规则体系通常比为了模型偏好临时切换工具更省力。反过来，项目规则文件内容陈旧、权限过宽或加载来源不明时，工具“原生支持”也不应成为继续使用的理由。

后端模型、认证和工具客户端也要分开看。同一个客户端可以接入不同 Provider，同一个模型也可能通过不同 Gateway 使用；比较结果需要记录客户端版本、实际后端、权限、项目状态和测试条件，不能只写“Claude/Codex/Grok 谁更好”。

## 3. 协作时保持一个写入者，其余会话提供不同阅读路径

最常用的组合是一个实施者和一个只读复核者。实施者在确定的分支或 Worktree 中修改并运行测试，复核者读取原始需求、当前 diff 和真实测试结果，从另一条路径寻找范围外修改、兼容问题和测试缺口。复核不要求使用同一客户端；使用另一工具的价值在于减少实现者的路径依赖，而不是自动获得更高正确率。

三个 Agent 也不意味着三者同时写代码。一种清楚的职责关系是：

```text
只读调查：找到入口、测试和风险
单一实施者：在任务分支或独立 Worktree 中修改
只读复核：检查 diff、测试和未验证内容
人：确认需求、处理分歧并决定提交
```

同一未提交工作区同时只有一个写入者。其他会话保持只读，或使用独立 Worktree；否则测试结果无法对应到确定版本，Agent 也会把彼此的半成品当作项目现实。Worktree 的建立、外部资源共享和整合规则见[复杂任务拆分与独立复核](05-复杂任务拆分与独立复核.md)，本章不再重复完整命令。

复核意见也不能整批自动实施。先把发现分成已确认问题、需要进一步验证、可选改进和误报，再把确定问题交给实施者形成下一次小修改。两套 Agent 给出相反意见时，回到代码、测试、性能数据或产品规则，不通过再增加第三个模型“投票”解决。

## 4. 使用最少但足够的组合，并分别管理每台机器

简单任务采用一套主力工具加人工 diff；需要第二意见时增加只读会话；需要对照两个实现时增加 Worktree；需要机器可读报告时使用 Codex `exec` 或 Grok Headless。只有职责确实不同、输入与输出边界明确时，第三个 Agent 才可能带来额外价值。

非交互任务仍需明确工作目录、外层超时、最大轮数、输出格式、退出状态和任务后的 Git diff。这些是自动化共同要求，不因选择某个产品而消失，完整方法见对应自动化章节。

Mac 与 Ubuntu 也是两套独立环境。SSH 或 rsync 可以同步源码，却不会自动同步 CLI 安装、登录缓存、TOML/Settings、MCP、Hook、Plugin、Skill、Shell 变量和系统凭据库。两台机器分别安装和配置，认证目录不整目录复制；比较两个工具时，也要避免把不同机器和不同后端的差异误归因于客户端本身。

工具越多，配置、权限、上下文和结果整合成本越高。清楚的需求、可查看的 diff、真实测试和独立复核，通常比同时启动三套客户端更有价值。

延伸阅读：[Claude Code](../Part-09-Claude-Code/01-安装登录与启动.md)、[Codex CLI](../Part-10-Codex-CLI/01-安装登录与启动.md)、[Grok Build](../Part-10B-Grok-CLI/01-安装登录与基础使用.md)、[复杂任务拆分与独立复核](05-复杂任务拆分与独立复核.md)和[配置、凭证与多实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)。
