# 终端与 AI 编程手册

> **Terminal & AI Coding Handbook**
>
> Terminal · Shell · Git · SSH · Homebrew · Python · Docker · Claude Code · Codex CLI · Grok Build · 配置与凭证 · GPU 远程开发

这是一套写给终端新手的中文实用手册。默认读者日常使用 Mac，已经开始接触 Claude Code、Codex CLI、Grok Build 或其他 AI 编程工具，但对目录、Shell、Git、配置文件和远程 Linux 还不熟悉。全书从“我现在在哪台机器、哪个目录”开始，逐步讲到 Python 环境、Docker、AI Agent、配置与凭证管理，以及使用 Mac 控制 Ubuntu NVIDIA GPU 游戏本。

V2.0 的重写目标不是堆积更多命令，而是把知识放进完整场景。章节会说明命令在哪里运行、为什么运行、可能看到什么输出、怎样确认成功，以及路径、权限、配置或网络不符合预期时应从哪一层排查。涉及删除、覆盖、凭证、远程机器、Docker 数据和 Git 历史时，也会说明预演、备份与恢复边界。

全书反复使用一条工作习惯：

```text
确认机器、用户和目录
→ 明确目标、非目标和允许范围
→ 先调查真实项目
→ 小批修改
→ 运行验证
→ 阅读 Git diff
→ 独立复核
→ 人工决定提交和推送
```

## 从哪里开始

第一次打开终端，阅读[终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md)。它会带你在独立练习目录中导航、创建文件、修改输入和停止前台程序。

已经会使用 `cd` 和 `git status`，第一次接触 AI 编程工具，阅读[AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md)。这一篇完成一个范围很小、能够检查结果的 Agent 任务。

希望沿一条路线练习终端、Git、AI CLI 和人工提交，阅读[终端与 AI CLI 完整快速入门](Quickstart/终端与AI-CLI快速入门.md)。忘记快捷键或担心某条命令的影响时，查看[快捷键速查表](Appendix/快捷键速查表.md)和[危险命令清单](Appendix/危险命令清单.md)。

## 全书路线

### Part 01–03：终端基础

建立 Terminal、Shell、zsh、目录、路径、文件操作、搜索、日志、管道、进程和快捷键的基本认识。

- [Part 01：基础篇](SUMMARY.md#part-01基础篇)
- [Part 02：终端命令](SUMMARY.md#part-02终端命令)
- [Part 03：Shell 快捷键](SUMMARY.md#part-03shell-快捷键)

### Part 04：Git

学习工作区、暂存区、提交、分支、恢复、Worktree 和 Pull Request，让人工修改与 AI 修改都能被检查和回退。

- [Git 心智模型](Part-04-Git/01-Git心智模型.md)
- [日常提交与复核流程](Part-04-Git/02-日常提交与复核流程.md)
- [分支、合并与安全恢复](Part-04-Git/03-分支合并与安全恢复.md)
- [Pull Request 与多人协作](Part-04-Git/04-Pull-Request与多人协作.md)

### Part 05–08：开发基础设施

这一部分覆盖 Mac 和 Ubuntu 上最常见的开发环境：

- [SSH](SUMMARY.md#part-05ssh)：远程登录、密钥、传输、隧道和故障排查；
- [Homebrew](SUMMARY.md#part-06homebrew)：安装、PATH、服务和版本冲突；
- [Python 环境](SUMMARY.md#part-07python-环境)：解释器、pip、venv、Conda、uv 和锁文件；
- [Docker](SUMMARY.md#part-08docker)：镜像、容器、Volume、Compose 和 GPU 容器。

### Part 09：Claude Code

覆盖客户端安装与认证、权限和 Sandbox、会话与记忆、Hooks、MCP、大项目工作流，以及 DeepSeek、企业 Gateway 和兼容供应商。

- [安装、登录与启动](Part-09-Claude-Code/01-安装登录与启动.md)
- [权限、审批与安全边界](Part-09-Claude-Code/02-权限审批与安全边界.md)
- [会话、记忆、Hooks 与 MCP](Part-09-Claude-Code/03-会话记忆Hooks与MCP.md)
- [大项目与多阶段任务工作流](Part-09-Claude-Code/04-大项目与多阶段任务工作流.md)
- [接入 DeepSeek 与第三方供应商](Part-09-Claude-Code/05-接入DeepSeek与第三方供应商.md)

### Part 10：Codex CLI

覆盖安装、ChatGPT/API 认证、Sandbox、审批、`AGENTS.md`、交互模式、`codex exec`、结构化输出、Review、会话恢复和 Git 协作。

- [安装、登录与启动](Part-10-Codex-CLI/01-安装登录与启动.md)
- [Sandbox、审批与配置](Part-10-Codex-CLI/02-Sandbox审批与配置.md)
- [交互模式与自动化](Part-10-Codex-CLI/03-交互模式与自动化.md)
- [Codex CLI 与 Git 协作案例](Part-10-Codex-CLI/04-Codex与Git协作案例.md)

### Part 10B：Grok Build

xAI 官方产品名为 Grok Build，终端命令为 `grok`。这一部分覆盖认证、Ask/Auto/Always-approve、Plan、Sandbox、Headless、Worktree、会话和扩展系统。目录名保留 `Grok-CLI` 是为了兼容现有路径。

- [安装、登录与基础使用](Part-10B-Grok-CLI/01-安装登录与基础使用.md)
- [权限、Sandbox 与项目配置](Part-10B-Grok-CLI/02-权限Sandbox与项目配置.md)
- [Headless、Worktree 与扩展系统](Part-10B-Grok-CLI/03-Headless-Worktree与扩展系统.md)

### Part 10C：配置、凭证与多实例

这是 V2.0 新增核心模块。它解释配置、凭证、模型、Provider、Profile、实例和本地网关之间的区别，并拆解 Claude Code、Codex、CC Switch、ccswitch 与 Cockpit Tools 的实际配置链。

- [先分清配置、凭证、供应商与实例](Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)
- [Codex 的 TOML、Profile 与凭证](Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)
- [Claude Code 的配置、凭证与网关](Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)
- [CC Switch、ccswitch 与 Cockpit Tools](Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)

读者应能判断一次切换究竟改变了模型、供应商、账号、Profile、Base URL，还是整套独立实例，并能在第三方工具失效时恢复原生配置。

### Part 11：GPU 远程开发

默认场景是一台日常使用的 Mac、一台安装 Ubuntu 24.04 的 NVIDIA 游戏本和一个自己管理的路由器。Mac 负责编辑、Git 和复核，Ubuntu 负责 Linux、CUDA 和长时间训练。

内容包括：

- 局域网 OpenSSH 与主机指纹；
- rsync 与 Git 的同步边界；
- tmux、日志与断线续跑；
- NVIDIA Driver、CUDA Toolkit、Runtime 和 PyTorch；
- Mac 与 Ubuntu 分别创建 Python 环境；
- Tailscale 异网连接；
- VS Code Remote SSH 与 AI CLI；
- Run Directory、Checkpoint 和恢复测试。

[查看 Part 11 全部章节](SUMMARY.md#part-11gpu-远程开发)

### Part 12：AI 开发工作流

最后一部分把不同 AI 客户端放进同一条可检查的闭环，覆盖 Prompt、基础设施任务、权限、安全、复杂任务、多 Agent 和完整 GPU 案例。

- [通用 AI 编程闭环](Part-12-AI开发工作流/01-通用AI编程闭环.md)
- [通用 Prompt 模板库](Part-12-AI开发工作流/02-通用Prompt模板库.md)
- [基础设施与远程开发 Prompt](Part-12-AI开发工作流/03-基础设施Prompt模板.md)
- [权限与安全边界总览](Part-12-AI开发工作流/04-权限与安全边界总览.md)
- [复杂任务拆分与独立复核](Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)
- [Claude Code、Codex CLI 与 Grok Build 对照协作](Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)
- [Mac 到 Ubuntu GPU 的端到端案例](Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)

## 默认环境与安全边界

本书优先使用 macOS 和 zsh 展示日常操作，再扩展到 Ubuntu、SSH、Tailscale、Docker Engine、NVIDIA CUDA 和远程训练。不同平台的参数和路径不同时，章节会单独标注。Mac 的 `.venv`、可执行文件和 AI CLI 状态目录不能直接复制到 Ubuntu 后继续使用。

书中不会提供真实 API Key、Session Token、Cookie、Refresh Token、登录缓存或 SSH 私钥。涉及 `auth.json`、Keychain、Keyring、`.credentials.json` 和第三方账号工具时，只说明职责、位置、权限和活动来源，不展示秘密正文。

第三方 Provider、Gateway、MCP、Hook、Plugin、Skill 和配置管理工具会扩大数据与权限链。能够运行不等于官方支持，也不等于上游账号、计费和数据处理没有额外风险。

## 项目状态

V1.0 已作为公共历史版本保留。V2.0 主体教程化重写、技术终审和私有源仓库合并已经完成：

```text
私有源仓库：anyue-git/Terminal-AI-Coding-Handbook
V2.0 Pull Request：#2
状态：已通过 squash merge 合入 main
合并提交：abe389994f1841c90f35c670b16420f18859c9ba
```

当前仓库包含 74 个 Markdown 文件。严格自动检查验证 UTF-8、标题、代码块、内部链接和目录引用；合并前最终 Markdown Check #176 成功。自动检查不能代替官方文档核对、外部链接检查、敏感信息扫描和真实设备测试。

V2.0 已作为正常升级提交发布到当前公共仓库，V1.0 提交历史继续保留，并已创建 `v2.0.0` 标签与 GitHub Release。许可证尚未由作者明确选择，因此当前没有自动加入许可证文件。

维护入口：

- [目录](SUMMARY.md)
- [全书路线图](ROADMAP.md)
- [写作规范与内容审查标准](CONTRIBUTING.md)
- [内容审查记录](Appendix/内容审查记录.md)
- [更新记录](Appendix/更新记录.md)
- [版本化工具核对表](Appendix/版本化工具核对表.md)
- [自动检查报告](Appendix/自动检查报告.md)

执行任何命令前，请结合自己的机器、目录、权限、软件版本、网络和备份情况判断。涉及删除、覆盖、管理员权限、远程机器、Git 历史和凭据时，应先确认影响范围与恢复方式。