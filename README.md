# 终端与 AI 编程手册

> **Terminal & AI Coding Handbook**
>
> Terminal · Shell · Git · SSH · Homebrew · Python · Docker · Claude Code · Codex CLI · Grok Build · 配置与凭证 · GPU 远程开发

这是一套写给终端新手的中文实用手册。默认读者日常使用 Mac，已经接触 Claude Code、Codex CLI、Grok Build 或其他 AI 编程工具，却还不熟悉目录、Shell、Git、配置文件和远程 Linux。全书从一个最基本的问题出发：我现在在哪台机器、哪个目录，接下来这条命令会影响什么？

书中的例子尽量组成连续任务，而不是让读者背一张命令表。你会从文件和路径开始，逐步进入 Git、Python、Docker、AI CLI、配置与凭证管理，最后完成 Mac 控制 Ubuntu NVIDIA GPU 游戏本的远程开发流程。涉及删除、覆盖、凭证、远程机器、Docker 数据和 Git 历史时，正文会说明影响范围、观察方法和恢复边界。

## 从哪里开始

第一次打开终端，先读[终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md)。它只使用一个独立练习目录，带你确认位置、创建和移动文件，并分清取消命令、暂停程序和清理屏幕。

已经会使用 `cd` 和 `git status`，准备第一次在真实项目中使用 Agent，可以进入[AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md)。这一篇围绕一个小修改展开：调查项目、限定范围、让 Agent 分步实施，再由你阅读 diff 和运行测试。

希望从零走完“终端、Python、Git、AI CLI、人工提交”的完整流程，直接使用[终端与 AI CLI 完整快速入门](Quickstart/终端与AI-CLI快速入门.md)。忘记某个按键或担心命令影响时，再查[快捷键速查表](Appendix/快捷键速查表.md)和[危险命令清单](Appendix/危险命令清单.md)。

## 全书内容

Part 01–03 解释 Terminal、Shell、zsh、文件系统、路径、常用命令、管道、进程和快捷键。目标不是记住所有选项，而是理解命令由谁解释、作用在哪个目录、输入输出流向哪里，以及报错时应该先检查哪一层。

Part 04–08 进入日常开发基础：Git、SSH、Homebrew、Python 环境和 Docker。相关章节会同时标出 macOS 与 Ubuntu、BSD 与 GNU 工具、Apple Silicon 与 x86_64 等差异，避免把一台机器上的路径和环境原样复制到另一台机器。

Part 09–10C 分别介绍 Claude Code、Codex CLI 和 Grok Build，再集中讲清模型、Provider、Base URL、Profile、账号、凭证、状态目录、独立实例和本地网关。CC Switch、ccswitch 与 Cockpit Tools 等工具也放在这一部分讨论，但重点始终是弄清它们实际改动了哪一层。

Part 11 使用一台日常 Mac、一台安装 Ubuntu 24.04 的 NVIDIA 游戏本和一个自己管理的路由器，完成局域网 SSH、项目同步、tmux、CUDA/PyTorch、异网连接、VS Code Remote SSH、AI CLI 协作、实验日志与 Checkpoint 管理。Mac 负责主要编辑、Git 和复核，Ubuntu 负责 Linux 依赖、GPU 计算和长时间训练。

Part 12 把前面的能力组合成可检查的 AI 开发流程，包括任务定义、只读调查、小批实施、测试证据、独立复核、权限边界、多 Agent 协作，以及 Mac 到 Ubuntu GPU 的端到端案例。完整章节见[目录](SUMMARY.md)，推荐顺序和章节依赖见[全书路线图](ROADMAP.md)。

## 默认环境与安全边界

本书优先使用 macOS 和 zsh 展示日常操作，再扩展到 Ubuntu、SSH、Tailscale、Docker Engine、NVIDIA CUDA 和远程训练。多台机器或多层环境同时出现时，正文会标明命令运行位置。Mac 的 `.venv`、本地可执行文件和 AI CLI 状态目录不能复制到 Ubuntu 后继续使用；容器内外、SSH 前后和 VS Code 本地/远程终端也要分别确认。

示例不会提供真实 API Key、Session Token、Cookie、Refresh Token、登录缓存或 SSH 私钥。第三方 Provider、Gateway、MCP、Hook、Plugin、Skill 和配置管理工具会扩大数据与权限链；工具能够运行，只能证明当前组合暂时可用，不能替代对账号、计费、数据处理和服务条款的判断。

## 项目与维护

V1.0 作为历史版本保留，V2.0 已发布。V3.0 正在私有源仓库中进行最终审查，尚未合并或同步到公共仓库。重构方法和当前进度见[V3.0 路线图](V3.0-ROADMAP.md)，准备中的发布文案见[V3.0 发布说明草案](RELEASE_NOTES_V3.0.md)。

本项目采用双许可证：正文、解释、表格和练习使用 CC BY-NC-SA 4.0；脚本、工作流、命令和配置示例使用 MIT License。详细条款见[LICENSE](LICENSE)，写作和审查约定见[CONTRIBUTING.md](CONTRIBUTING.md)。