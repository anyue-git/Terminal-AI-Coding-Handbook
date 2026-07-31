# 终端与 AI 编程手册

> **Terminal & AI Coding Handbook**
>
> Terminal · Shell · Git · SSH · Homebrew · Python · Docker · Claude Code · Codex CLI · Grok Build · 配置与凭证 · GPU 远程开发

[快速开始](#从哪里开始) · [全书目录](#全书目录) · [默认环境与安全边界](#默认环境与安全边界) · [项目与许可证](#项目与许可证)

这是一套写给终端新手的中文实用手册。默认读者日常使用 Mac，已经接触 Claude Code、Codex CLI、Grok Build 或其他 AI 编程工具，却还不熟悉目录、Shell、Git、配置文件和远程 Linux。全书从一个最基本的问题出发：**我现在在哪台机器、哪个目录，接下来这条命令会影响什么？**

书中的例子尽量组成连续任务，而不是让读者背一张命令表。你会从文件和路径开始，逐步进入 Git、Python、Docker、AI CLI、配置与凭证管理，最后完成 Mac 控制 Ubuntu NVIDIA GPU 游戏本的远程开发流程。涉及删除、覆盖、凭证、远程机器、Docker 数据和 Git 历史时，正文会同时说明影响范围、观察方法和恢复边界。

## 从哪里开始

第一次打开终端，先读[终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md)。它只使用一个独立练习目录，带你确认位置、创建和移动文件，并分清取消命令、暂停程序和清理屏幕。

已经会使用 `cd` 和 `git status`，准备第一次在真实项目中使用 Agent，可以进入[AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md)。这一篇围绕一个小修改展开：调查项目、限定范围、让 Agent 分步实施，再由你阅读 diff 和运行测试。

希望从零走完“终端、Python、Git、AI CLI、人工提交”的完整流程，直接使用[终端与 AI CLI 完整快速入门](Quickstart/终端与AI-CLI快速入门.md)。忘记某个按键或担心命令影响时，再查[快捷键速查表](Appendix/快捷键速查表.md)和[危险命令清单](Appendix/危险命令清单.md)。

## 全书目录

> 下面直接列出全书正文入口。第一次阅读可以按 Part 顺序推进，已经有基础的读者也可以直接跳到 Git、Docker、AI CLI、配置凭证或 GPU 远程开发。更适合查阅的纵向目录见 [SUMMARY.md](SUMMARY.md)，章节依赖与推荐路径见[全书路线图](ROADMAP.md)。

- **00 · 快速开始**：[终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md) · [AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md) · [终端与 AI CLI 完整快速入门](Quickstart/终端与AI-CLI快速入门.md)
- **Part 01 · 基础篇**：[为什么程序员离不开终端](Part-01-基础篇/01-为什么程序员离不开终端.md) · [Terminal 到底是什么](Part-01-基础篇/02-Terminal到底是什么.md) · [Shell 到底是什么](Part-01-基础篇/03-Shell到底是什么.md) · [zsh 到底是什么](Part-01-基础篇/04-zsh到底是什么.md) · [文件系统、目录与路径](Part-01-基础篇/05-文件系统目录与路径.md)
- **Part 02 · 终端命令**：[pwd、ls 与 cd](Part-02-终端命令/01-pwd-ls-cd.md) · [创建、复制、移动与删除](Part-02-终端命令/02-创建复制移动与删除.md) · [查看文本文件与日志](Part-02-终端命令/03-查看文本文件与日志.md) · [搜索文件与文本](Part-02-终端命令/04-搜索文件与文本.md) · [管道、重定向与命令组合](Part-02-终端命令/05-管道重定向与命令组合.md) · [进程与任务控制](Part-02-终端命令/06-进程前台后台与任务控制.md)
- **Part 03 · Shell 快捷键**：[命令行编辑核心快捷键](Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
- **Part 04 · Git**：[Git 心智模型](Part-04-Git/01-Git心智模型.md) · [日常提交与复核流程](Part-04-Git/02-日常提交与复核流程.md) · [分支、合并与安全恢复](Part-04-Git/03-分支合并与安全恢复.md) · [Pull Request 与多人协作](Part-04-Git/04-Pull-Request与多人协作.md)
- **Part 05 · SSH**：[SSH 基础与首次连接](Part-05-SSH/01-SSH基础与首次连接.md) · [密钥登录与 SSH Config](Part-05-SSH/02-密钥登录与SSH-Config.md) · [scp、rsync 与端口转发](Part-05-SSH/03-scp-rsync与端口转发.md) · [SSH 故障排查](Part-05-SSH/04-SSH故障排查.md)
- **Part 06 · Homebrew**：[Homebrew 与 PATH](Part-06-Homebrew/01-Homebrew与PATH.md) · [服务、版本与常见故障](Part-06-Homebrew/02-服务版本与常见故障.md)
- **Part 07 · Python 环境**：[Python 解释器与 pip 定位](Part-07-Python环境/01-Python解释器与pip定位.md) · [venv、Conda 与 uv 怎么选](Part-07-Python环境/02-venv-Conda与uv怎么选.md) · [依赖声明、锁定与环境复现](Part-07-Python环境/03-依赖声明锁定与环境复现.md)
- **Part 08 · Docker**：[镜像、容器、卷与网络](Part-08-Docker/01-镜像容器卷与网络.md) · [Docker Desktop 与 Ubuntu Docker Engine](Part-08-Docker/02-Docker-Desktop与Ubuntu-Docker-Engine.md) · [Docker Compose 多服务项目](Part-08-Docker/03-Docker-Compose多服务项目.md) · [GPU 容器与权限边界](Part-08-Docker/04-GPU容器与权限边界.md)
- **Part 09 · Claude Code**：[安装、登录与启动](Part-09-Claude-Code/01-安装登录与启动.md) · [权限、审批与安全边界](Part-09-Claude-Code/02-权限审批与安全边界.md) · [会话、记忆、Hooks 与 MCP](Part-09-Claude-Code/03-会话记忆Hooks与MCP.md) · [大项目与多阶段任务](Part-09-Claude-Code/04-大项目与多阶段任务工作流.md) · [接入 DeepSeek 与第三方供应商](Part-09-Claude-Code/05-接入DeepSeek与第三方供应商.md)
- **Part 10 · Codex CLI**：[安装、登录与启动](Part-10-Codex-CLI/01-安装登录与启动.md) · [Sandbox、审批与配置](Part-10-Codex-CLI/02-Sandbox审批与配置.md) · [交互模式与自动化](Part-10-Codex-CLI/03-交互模式与自动化.md) · [Codex CLI 与 Git 协作案例](Part-10-Codex-CLI/04-Codex与Git协作案例.md)
- **Part 10B · Grok Build**：[安装、登录与基础使用](Part-10B-Grok-CLI/01-安装登录与基础使用.md) · [权限、Sandbox 与项目配置](Part-10B-Grok-CLI/02-权限Sandbox与项目配置.md) · [Headless、Worktree 与扩展系统](Part-10B-Grok-CLI/03-Headless-Worktree与扩展系统.md) · [TUI、斜杠命令与交互界面](Part-10B-Grok-CLI/04-TUI斜杠命令与交互界面.md) · [会话、Memory 与后台任务](Part-10B-Grok-CLI/05-会话快照Memory与后台任务.md) · [Goal、Workflow 与多 Agent 系统](Part-10B-Grok-CLI/06-Goal-Workflow与多Agent系统.md) · [扩展系统、MCP、ACP 与跨客户端兼容](Part-10B-Grok-CLI/07-扩展系统MCP-ACP与跨客户端兼容.md) · [配置、模型、诊断与功能核对](Part-10B-Grok-CLI/08-配置模型诊断与功能核对.md) · [终端子命令与完整功能索引](Part-10B-Grok-CLI/09-终端子命令与完整功能索引.md)
- **Part 10C · 配置、凭证与多实例**：[先分清配置、凭证、供应商与实例](Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md) · [Codex 的 TOML、Profile 与凭证](Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md) · [Claude Code 的配置、凭证与网关](Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md) · [CC Switch、ccswitch 与 Cockpit Tools](Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)
- **Part 11 · GPU 远程开发**：[Mac 与 Ubuntu 局域网部署](Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md) · [项目同步与目录规范](Part-11-GPU远程开发/02-项目同步与目录规范.md) · [tmux 与断线续跑](Part-11-GPU远程开发/03-tmux与断线续跑.md) · [NVIDIA 驱动、CUDA 与 PyTorch](Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md) · [Mac 与 Ubuntu 分别创建环境](Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md) · [异网安全连接](Part-11-GPU远程开发/06-异网安全连接.md) · [VS Code、AI CLI 与 GPU 协作](Part-11-GPU远程开发/07-VS-Code-AI-CLI与GPU协作.md) · [实验日志与 Checkpoint 管理](Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)
- **Part 12 · AI 开发工作流**：[通用 AI 编程闭环](Part-12-AI开发工作流/01-通用AI编程闭环.md) · [通用 Prompt 模板库](Part-12-AI开发工作流/02-通用Prompt模板库.md) · [基础设施与远程开发 Prompt](Part-12-AI开发工作流/03-基础设施Prompt模板.md) · [权限与安全边界总览](Part-12-AI开发工作流/04-权限与安全边界总览.md) · [复杂任务拆分与独立复核](Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md) · [Claude Code、Codex CLI 与 Grok Build 协作](Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md) · [Mac 到 Ubuntu GPU 端到端案例](Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)
- **附录与速查**：[快捷键速查表](Appendix/快捷键速查表.md) · [危险命令清单](Appendix/危险命令清单.md) · [术语表](Appendix/术语表.md) · [版本化工具核对表](Appendix/版本化工具核对表.md) · [V3.1 Grok Build 专项审查](Appendix/V3.1-Grok-Build专项审查.md) · [内容审查记录](Appendix/内容审查记录.md) · [更新记录](Appendix/更新记录.md)

## 你会在这本手册里完成什么

Part 01–03 帮你建立 Terminal、Shell、zsh、路径、输入输出和进程的基本心智模型；Part 04–08 进入 Git、SSH、Homebrew、Python 和 Docker；Part 09–10C 分别处理三套 AI CLI 及其模型、Provider、Base URL、Profile、账号、凭证和本地网关；Part 11 完成 Mac 与 Ubuntu NVIDIA 游戏本的远程 GPU 开发；Part 12 将这些能力组合为可检查、可复核、可恢复的 AI 编程流程。

这套内容不是按“工具百科”组织，而是围绕真实任务逐步增加能力：先确认位置和影响范围，再修改；先看状态和差异，再提交；先验证环境和权限，再让 Agent 执行更大的任务。你不需要一次读完，也不需要记住所有命令，目录中的每个入口都可以独立回查。

## 默认环境与安全边界

本书优先使用 macOS 和 zsh 展示日常操作，再扩展到 Ubuntu、SSH、Tailscale、Docker Engine、NVIDIA CUDA 和远程训练。多台机器或多层环境同时出现时，正文会标明命令运行位置。Mac 的 `.venv`、本地可执行文件和 AI CLI 状态目录不能复制到 Ubuntu 后继续使用；容器内外、SSH 前后和 VS Code 本地/远程终端也要分别确认。

示例不会提供真实 API Key、Session Token、Cookie、Refresh Token、登录缓存或 SSH 私钥。第三方 Provider、Gateway、MCP、Hook、Plugin、Skill 和配置管理工具会扩大数据与权限链；工具能够运行，只能证明当前组合暂时可用，不能替代对账号、计费、数据处理和服务条款的判断。

## 项目与许可证

V1.0 与 V2.0 作为历史版本保留，V3.0 已完成叙事重构、内容覆盖反查和公共仓库发布。V3.0 的重构方法与审计过程见[V3.0 路线图](V3.0-ROADMAP.md)，完整变化见[V3.0 发布说明](RELEASE_NOTES_V3.0.md)。

V3.1 是 V3.0 后的 Grok Build 专项补充，当前仍在私有源仓库 Draft PR 中开发，尚未合并或同步到公共仓库。更新范围与验证边界见[V3.1 发布说明](RELEASE_NOTES_V3.1.md)和[V3.1 Grok Build 专项审查](Appendix/V3.1-Grok-Build专项审查.md)。

本项目采用双许可证：正文、解释、表格和练习使用 CC BY-NC-SA 4.0；脚本、工作流、命令和配置示例使用 MIT License。详细条款见[LICENSE](LICENSE)，写作和审查约定见[CONTRIBUTING.md](CONTRIBUTING.md)。