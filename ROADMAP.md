# 全书路线图

> 最近更新：2026-07-30

这份路线图回答“我应该按什么顺序读、哪些章节可以跳过、进入某个主题前需要什么基础”。版本开发进度和 V3.0 验收状态单独记录在 [V3.0 叙事重构路线图](V3.0-ROADMAP.md)，避免把阅读导航与发布时间线混在一起。

## 1. 根据当前目标选择入口

| 当前情况 | 推荐入口 | 接下来阅读 |
| --- | --- | --- |
| 第一次使用终端 | [终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md) | Part 01–03，然后进入 Git |
| 已会 `cd` 和 `git status`，第一次使用 Agent | [AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md) | Part 04、Part 09–10C、Part 12 |
| 希望从零走完终端、Python、Git 和 AI CLI | [完整 Quickstart](Quickstart/终端与AI-CLI快速入门.md) | 按遇到的问题回到对应正式章节 |
| 想系统学习 Git、SSH、Python 和 Docker | Part 04–08 | 先完成 Part 01–03 的目录、Shell 和进程基础 |
| 想配置 Claude Code、Codex 或 Grok Build | Part 09、10、10B | 先读 Part 10C 的配置与凭证模型，再结合对应客户端专章 |
| 想用 Mac 控制 Ubuntu 游戏本 GPU | Part 11 | 先掌握 SSH、Git、Python 环境和基础 Docker 概念 |
| 想建立可靠 AI 开发工作流 | Part 12 | 至少会查看 Git diff、运行测试并理解权限边界 |

快捷键、术语和危险命令不需要顺序阅读，遇到问题时查询[快捷键速查表](Appendix/快捷键速查表.md)、[术语表](Appendix/术语表.md)和[危险命令清单](Appendix/危险命令清单.md)。

## 2. 第一层：终端与 Shell 基础

```text
00 快速开始
→ Part 01 Terminal、Shell、zsh 与路径
→ Part 02 文件、文本、搜索、管道和进程
→ Part 03 命令行编辑快捷键
```

这一层解决最基础的定位问题：命令在哪台机器、哪个 Shell、哪个目录执行，输入和输出如何流动，怎样停止前台程序，以及为什么路径或通配符会改变命令结果。学完后应能使用 `pwd`、`ls`、`cd`、文件操作、文本查看、搜索、管道、重定向和任务控制，并能在长命令中编辑而不必整行重输。

不必背下所有命令。真正需要形成的是“先确认机器、用户和目录，再执行；看不懂路径和展开结果时先预览”的习惯。

## 3. 第二层：开发基础设施

| 部分 | 主要问题 | 建议前置知识 | 完成后能够做什么 |
| --- | --- | --- | --- |
| Part 04 Git | 工作区、暂存区、提交、分支、恢复和 PR | 目录、文件和文本查看 | 建立任务分支、精确暂存、审查 diff、恢复错误并参与协作 |
| Part 05 SSH | 远程身份、密钥、Config、传输、隧道和故障排查 | 路径、权限、进程、基础 Git | 从 Mac 安全连接 Ubuntu，传输文件并访问远程服务 |
| Part 06 Homebrew | Mac 软件来源、PATH、服务和多版本 | Shell 启动文件与 PATH | 判断实际运行哪份命令，管理本地服务并避免重复安装 |
| Part 07 Python 环境 | 解释器、pip、venv、Conda、uv、声明和锁文件 | PATH、Git、文件结构 | 为项目建立可重建环境，分清依赖声明与机器快照 |
| Part 08 Docker | Image、Container、Volume、Network、Compose 和 GPU | 进程、端口、文件系统、Python 环境 | 运行多服务项目，理解持久数据、挂载与宿主机权限边界 |

建议至少完整阅读 Git 和 SSH。Homebrew、Python 和 Docker 可以按项目需要选择，但进入远程 GPU 开发前，应理解 Python 环境不能在 Mac 与 Ubuntu 之间直接复制，容器也不能替代宿主机驱动与系统权限。

## 4. 第三层：AI 编程客户端与配置体系

三个客户端专章和统一配置模块承担不同职责：

```text
Part 09 Claude Code
→ 客户端认证、权限、会话、CLAUDE.md、Hooks、MCP、大任务与第三方后端

Part 10 Codex CLI
→ 认证、Sandbox/审批、codex exec 自动化、Review 与 Git 案例

Part 10B Grok Build
→ 认证、Ask/Auto/Always-approve、项目配置、Headless、Worktree 与扩展

Part 10C 配置、凭证与多实例
→ 模型、Provider、Base URL、凭证、Profile、状态目录、独立实例和切换工具
```

第一次使用任一 Agent 时，可以先读对应安装章和权限章；需要换模型、换供应商、换账号或多开实例时，再进入 Part 10C。不要把客户端、模型、订阅、API、Base URL 和账号缓存混成一个“配置”。

本层默认读者已经会从项目根目录启动工具、查看 `git status` 和 `git diff`、运行基础测试，并知道 `.env`、Token、SSH 私钥和登录缓存不能交给不可信工具。

## 5. 第四层：远程 GPU 与 AI 工作流

Part 11 按真实远程训练链排列：

```text
局域网 SSH
→ 项目同步与目录分工
→ tmux、日志与断线续跑
→ NVIDIA Driver、CUDA 与 PyTorch
→ Mac/Ubuntu 分别创建环境
→ Tailscale 异网连接
→ VS Code、AI CLI 与 GPU 协作
→ 实验日志、代码快照与 checkpoint
```

建议按顺序阅读。网络链路尚未稳定时不要直接开始 CUDA；解释器、驱动和真实 GPU 运算尚未通过时不要启动长训练；没有日志和恢复演练时不要把 tmux 当作完整容错方案。

Part 12 把前面能力组合成通用闭环：

```text
定义完成标准
→ 建立现实基线
→ 只读调查
→ 选择方案
→ 小批实施
→ 证据验证
→ 独立复核与人工提交
```

Prompt 模板、基础设施任务、安全边界、复杂任务拆分、三个 AI CLI 协作和 Mac 到 Ubuntu GPU 案例都围绕这条闭环展开。工具可以不同，但一个工作区同一时刻只有一个实施者，其他 Agent 应只读复核或进入独立 Worktree。

## 6. 推荐的四条完整学习路线

### 终端新手路线

```text
终端十五分钟上手
→ Part 01
→ Part 02
→ Part 03
→ Part 04 Git
→ AI CLI 快速上手
```

### 日常开发路线

```text
Part 01–04
→ Part 06 Homebrew
→ Part 07 Python
→ Part 08 Docker
→ 选择一个 AI CLI
→ Part 12 通用工作流
```

### AI 编程工具路线

```text
AI CLI 快速上手
→ Part 04 Git
→ 对应客户端安装与权限章
→ Part 10C 配置与凭证
→ Part 12 Prompt、安全、复核与多 Agent
```

### Mac 到 Ubuntu GPU 路线

```text
Part 04 Git
→ Part 05 SSH
→ Part 07 Python 环境
→ Part 11 按顺序阅读
→ Part 12 端到端案例
```

## 7. 哪些内容可以暂时跳过

只在 Mac 上做普通 Python 项目时，可以暂时跳过 Part 11 的 NVIDIA、Tailscale 和 checkpoint 细节；不使用 Docker 时可以先读对象模型和权限边界，再跳过 Compose 练习；只使用官方账号和默认模型时，可以晚些阅读第三方 Provider 与多实例；单人小项目不必立即实践多 Agent Worktree，但仍应掌握任务分支、测试和独立 diff 审查。

不能跳过的是机器与目录确认、Git 基线、凭据保护、危险命令预演、测试证据和人工提交决定。这些不是某个工具的附加技巧，而是贯穿全书的可靠性底线。

## 8. 项目与版本状态

```text
V1.0
→ 历史公共版本

V2.0
→ 已完成技术扩展和教程化重写，并作为公共版本保留

V3.0
→ 在私有源仓库 agent/v3-narrative-restructure 分支和 Draft PR #7 中进行
→ 四个正文批次已完成
→ 当前进行全书统稿、事实抽检和发布准备
```

V3.0 尚未合并，也没有修改公共仓库。自动检查能够验证 Markdown、内部链接、目录引用、脚本语法和叙事趋势，但不能替代外部官方文档核对、真实设备抽样、敏感信息扫描和人工通读。开发与验收细节见 [V3.0 路线图](V3.0-ROADMAP.md)和[内容审查记录](Appendix/内容审查记录.md)。