# V3.1 发布说明

> 发布状态：正式发布。公共版本以公共仓库 `main`、`v3.1` 标签和对应 GitHub Release 为准。

《终端与 AI 编程手册》V3.1 是 V3.0 发布后的专项内容更新，不进行全书结构重构。本次修改集中在 Part 10B Grok Build：原有三章已经覆盖安装、认证、权限、Sandbox、项目配置、Headless、Worktree 和扩展系统，但对实际 TUI 中数量众多的斜杠命令、会话与 Memory、后台任务、Goal、Workflow、多 Agent、终端子命令和跨客户端兼容只作了概括。V3.1 将这些能力重新整理为可查询、可排错、能说明恢复边界的完整章节组。

## 版本定位

V3.1 保留 V3.0 的全书结构、叙事规范和公开发布机制，只扩充变化较快且此前覆盖不足的 Grok Build 内容。它不改写其他 Part 的主线，不建立新的全书路线图，也不将一次产品专项更新包装成 V4.0。

本次新增和重写后的 Part 10B 共九章：

1. 安装、登录与基础使用；
2. 权限、Sandbox 与项目配置；
3. Headless、Worktree 与扩展系统；
4. TUI、斜杠命令与交互界面；
5. 会话、Memory 与后台任务；
6. Goal、Workflow 与多 Agent 系统；
7. 扩展系统、MCP、ACP 与跨客户端兼容；
8. 配置、模型、诊断与功能核对；
9. 终端子命令与完整功能索引。

## TUI、斜杠命令与快捷键

V3.1 首先解释斜杠菜单中的三类来源：Agent 后端内置命令、Pager/TUI 内置命令，以及声明为 `user-invocable` 的 Skill。用户实际看到的命令数量取决于版本、功能开关、账号、项目配置、Plugin、Skill 和兼容扫描，因此不能把某张截图或某一版静态清单当作永久契约。

新增章节覆盖会话、模型、权限、分享、转录、查找、上下文压缩、队列、后台任务、定时循环、媒体生成、设置、诊断、扩展管理、账号和隐私等入口，并说明官方在线文档与开源仓库内随包用户指南可能存在短暂同步差异。本机 `/help`、斜杠菜单、`grok --help` 和 `grok inspect` 才是当前安装版本的最终核对入口。

TUI 快捷键不再只写“回车发送”和“Shift+Tab 切模式”。V3.1 补充快捷键面板、Command Palette、中途 Interject、Prompt Queue、Tasks、Todo、后台命令、Sessions、Extensions、Dashboard、Scrollback 逐块导航、Raw Markdown、Viewer、复制与终止后台任务，并解释 `!` Shell mode、`@路径` 文件引用以及 VS Code 系、Apple Terminal、WezTerm 的按键差异。快捷键的效果取决于焦点、输入模式、Vim Scrollback 和终端协议，不能脱离界面状态死记。

`/sessions` 与 `/dashboard` 被解释为当前 Pager 中的活动会话与 Agent Dashboard 入口；`/resume` 和 Shell 层的 `grok sessions list/search/delete` 则负责持久化会话选择与磁盘记录管理。Fullscreen-only、Minimal-only 命令以及 `--no-alt-screen` 的渲染语义也已单独说明。

## 会话、Memory 与恢复边界

V3.1 将以下能力分开说明：

```text
磁盘会话
当前模型上下文
Compact 总结
Transcript、Export 与 Share
跨会话 Memory
Prompt 队列
后台 Agent
定时 Loop
```

`/resume`、`--resume` 和 `--continue` 恢复的是 Grok 会话，不是 Git、文件系统、数据库、容器、远程主机或外部服务快照。`/fork` 和 `--fork-session` 不自动创建 Git 分支，`/rewind` 也不能撤销已经发生的外部副作用。恢复后必须重新检查机器、目录、分支、HEAD、工作区和最终配置。

Memory 部分补充 `/remember`、`/memory`、`/flush`、`/dream`、实验性启用条件、Backend、用户配置以及 `grok memory clear` 的不同清理范围。长期记忆不应用于保存 API Key、Cookie、验证码、私人数据或未经验证的推测。

## Goal、Workflow 与多 Agent

V3.1 明确区分 Goal、Workflow、Subagent、Agent Definition、Persona 和 Dashboard。当前 Background Workflows 默认开启；开启时 `/goal` 使用 Host-owned Workflow Engine，关闭时会回退到旧式 `update_goal` 工具，因此关闭 Workflow 不只影响 `/workflow` 和 `/deep-research`。

Workflow 章节说明 Rhai 脚本作用域、定义优先级、Pause/Resume、同进程恢复、进程重启后的中断边界和非 exactly-once 风险。当前 Agent Budget 默认 128，显式范围为 1–1024；它与 Goal Token Budget、模型/API 费用和运行时间是不同资源。

多 Agent 场景继续坚持一个未提交工作区只有一个写入者。调查、验证和复核 Agent 默认只读，多个实现使用独立 Worktree；Worktree 只隔离 Git 目录和分支，不隔离认证、网络、数据库、Docker、GPU 和项目外文件。

## 扩展、兼容与跨客户端导入

扩展章节补充 Skill、Plugin、Marketplace、Hook、MCP、LSP、代码索引和 ACP 的来源、作用域、信任与凭据边界。Grok 可以自动发现部分 Claude Code 生态配置，但“能够读取”不表示权限规则、Hook JSON、退出码、Agent 工具或执行顺序完全相同。

V3.1 特别区分三种容易混淆的 Claude 路线：

```text
/import-claude      导入 Claude 设置

grok import        导入 Claude Code 会话

resume-claude Skill 与兼容 Session Cell
                    staged 的扫描器路线
```

Codex 和 Cursor 的会话兼容单元当前同样被上游配置文档标记为 staged，并要求存在匹配的 `resume-codex` 或 `resume-cursor` Skill。看到 `/resume-codex` 只能证明当前环境存在一个可调用 Skill，不能据此宣称稳定的 Codex Session Scanner 已经接通。

## 配置、认证与诊断

配置章节不再把所有设置简化成一条永久覆盖链。普通运行时参数、用户配置、项目 MCP/Plugin、Permission Rule、企业 Managed 默认、Requirements Policy Pin 和 Version Bound 使用不同合并语义；其中 `requirements.toml` 中受支持的组织策略不能由用户配置、环境变量或远程设置放宽。

认证部分明确当前凭据顺序：`model.api_key` 高于 `model.env_key` 指向的环境变量，二者高于活动 Session Token，活动 Session Token 高于 `XAI_API_KEY`。已经登录时，`XAI_API_KEY` 只是回退；验证 API Project 路线应退出登录或使用隔离的 `GROK_HOME`。OAuth 同时保留 `grok login --oauth` 和欢迎页全局入口 `grok --oauth`；`--device-code` 作为 `--device-auth` 的别名处理。

权限部分新增 `dontAsk`、`acceptEdits` 和企业 Bypass Lock，并明确 Plan Mode 只限制普通 Edit 工具，不会自动约束 Bash 重定向、写入型 MCP 或子 Agent。新增 `--plugin-dir` 后，也进一步区分临时加载、安装、启用与信任。

同时新增自定义模型、工具超时与输出上限、Web Fetch 本地网络边界、通知、Pager、Privacy、Telemetry、Trace、外部 OpenTelemetry、日志和企业版本限制等诊断内容。

## 终端子命令索引

新增第九章集中整理官方文档公开的 Shell 入口，包括：

```text
login、logout、inspect、models
mcp、plugin、plugin marketplace
sessions、export、import、memory clear
worktree、dashboard、agent stdio
wrap、update、version、completions、setup
```

同时整理工作目录、会话、Worktree、模型、权限、Sandbox、工具集合、System Prompt、Headless 输出、最大轮数、单次关闭功能和终端呈现相关 Flags。索引不包含内部开发二进制、隐藏调试命令和没有公开契约的实现细节。

## 事实核对方法

本次内容以 2026-07-31 的 xAI 官方在线文档和 `xai-org/grok-build` 上游用户指南为主要依据，并区分：

```text
正式在线文档已公开的能力
开源仓库随包用户指南中的完整实现说明
需要功能开关或 Backend 的条件能力
Plugin、Skill 或兼容层提供的扩展能力
仅预留或 staged 的兼容单元
```

在线文档与仓库内文档出现短暂不一致时，正文会明确记录，不选择性删除不一致项。读者实际使用时仍应以本机 `/help`、`grok --help`、`grok inspect` 和真实运行结果为准。

## 发布与验证说明

V3.1 的私有源分支已通过 Markdown Check 与 Source Release Audit。检查范围包括严格 Markdown、内部链接、辅助脚本测试、敏感信息与 Git 历史扫描、公开导出 dry-run、公共目标仓库不变性检查、隔离公开快照和外链审计。

自动检查只能证明其覆盖的静态规则和导出流程通过，不能证明全部功能在每个账号、平台、终端和组织策略中都可用。尤其是 Memory Backend、Workflow Driver、`resume-codex`、第三方 Plugin/MCP 和终端快捷键，仍需读者结合自己的版本和环境核对。
