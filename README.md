# 终端与 AI 编程手册

> **Terminal & AI Coding Handbook**
>
> Terminal · Shell · Git · SSH · Homebrew · Python · Docker · Claude Code · Codex CLI · Grok CLI · GPU 远程开发

这是一套面向终端新手的实用手册，默认使用 **Mac** 作为日常设备，从最基础的目录、文件和快捷键开始，逐步讲到 Git、Python、Docker 和 AI 编程 CLI。

Ubuntu、SSH、Tailscale、NVIDIA GPU 和远程训练属于后续扩展内容。没有 Ubuntu 游戏本或独立 GPU，也不影响阅读和使用前面的大部分章节。

这本手册不追求收录所有命令，更关注一套能够真正落地的操作习惯：

```text
先确认当前目录和环境
→ 再限定任务范围
→ 修改后运行真实验证
→ 查看 diff
→ 最后决定是否提交
```

---

## 快速开始

刚接触终端，可以从以下三个入口中选择：

- [终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md)  
  快速掌握 `pwd`、`ls`、`cd`、常用快捷键、停止程序和基础 Git 检查。

- [AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md)  
  在正确目录中启动 Claude Code、Codex CLI 或 Grok CLI，完成第一次受控修改。

- [终端与 AI CLI 完整快速入门](Quickstart/终端与AI-CLI快速入门.md)  
  用一条完整路线串联终端、Git、AI CLI 和远程开发的基本方法。

常用速查：

- [快捷键速查表](Appendix/快捷键速查表.md)
- [危险命令清单](Appendix/危险命令清单.md)
- [术语表](Appendix/术语表.md)

---

## 完整章节

README 直接列出全部正式章节，便于第一次进入仓库时了解手册的完整范围。

### Part 01：基础篇

建立 Terminal、Shell、zsh、目录和路径的基本心智模型。

- [01 为什么程序员离不开终端](Part-01-基础篇/01-为什么程序员离不开终端.md)
- [02 Terminal 到底是什么](Part-01-基础篇/02-Terminal到底是什么.md)
- [03 Shell 到底是什么](Part-01-基础篇/03-Shell到底是什么.md)
- [04 zsh 到底是什么](Part-01-基础篇/04-zsh到底是什么.md)
- [05 文件系统、目录与路径](Part-01-基础篇/05-文件系统目录与路径.md)

### Part 02：终端命令

学习文件导航、创建、复制、删除、搜索、日志、管道和进程管理。

- [01 pwd、ls 与 cd](Part-02-终端命令/01-pwd-ls-cd.md)
- [02 创建、复制、移动与删除](Part-02-终端命令/02-创建复制移动与删除.md)
- [03 查看文本文件与日志](Part-02-终端命令/03-查看文本文件与日志.md)
- [04 搜索文件与文本](Part-02-终端命令/04-搜索文件与文本.md)
- [05 管道、重定向与命令组合](Part-02-终端命令/05-管道重定向与命令组合.md)
- [06 进程、前台、后台与任务控制](Part-02-终端命令/06-进程前台后台与任务控制.md)

### Part 03：Shell 快捷键

解决长命令输入、整行删除、历史搜索和程序中断等高频问题。

- [01 命令行编辑核心快捷键](Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)

### Part 04：Git

使用 Git 保存、比较、恢复和审查人工或 AI 产生的修改。

- [01 Git 心智模型](Part-04-Git/01-Git心智模型.md)
- [02 日常提交与复核流程](Part-04-Git/02-日常提交与复核流程.md)
- [03 分支、合并与安全恢复](Part-04-Git/03-分支合并与安全恢复.md)
- [04 Pull Request 与多人协作](Part-04-Git/04-Pull-Request与多人协作.md)

### Part 05：SSH

连接远程 Ubuntu、传输文件、建立端口转发并排查连接问题。

- [01 SSH 基础与首次连接](Part-05-SSH/01-SSH基础与首次连接.md)
- [02 密钥登录与 SSH Config](Part-05-SSH/02-密钥登录与SSH-Config.md)
- [03 scp、rsync 与端口转发](Part-05-SSH/03-scp-rsync与端口转发.md)
- [04 SSH 故障排查](Part-05-SSH/04-SSH故障排查.md)

### Part 06：Homebrew

管理 Mac 上的命令行工具、PATH、软件版本和后台服务。

- [01 Homebrew 与 PATH](Part-06-Homebrew/01-Homebrew与PATH.md)
- [02 服务、版本与常见故障](Part-06-Homebrew/02-服务版本与常见故障.md)

### Part 07：Python 环境

理解 Python 解释器、pip、venv、Conda、uv 和依赖复现。

- [01 Python 解释器与 pip 定位](Part-07-Python环境/01-Python解释器与pip定位.md)
- [02 venv、Conda 与 uv 怎么选](Part-07-Python环境/02-venv-Conda与uv怎么选.md)
- [03 依赖声明、锁定与环境复现](Part-07-Python环境/03-依赖声明锁定与环境复现.md)

### Part 08：Docker

理解镜像、容器、卷、网络、Compose 和 GPU 容器的边界。

- [01 镜像、容器、卷与网络](Part-08-Docker/01-镜像容器卷与网络.md)
- [02 Docker Desktop 与 Ubuntu Docker Engine](Part-08-Docker/02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [03 Docker Compose 多服务项目](Part-08-Docker/03-Docker-Compose多服务项目.md)
- [04 GPU 容器与权限边界](Part-08-Docker/04-GPU容器与权限边界.md)

### Part 09：Claude Code

围绕 Claude Code 客户端，讲解安装、模型接入、权限、会话、Hooks、MCP 和复杂任务工作流。

- [01 安装、接入与启动](Part-09-Claude-Code/01-安装登录与启动.md)
- [02 权限、审批与安全边界](Part-09-Claude-Code/02-权限审批与安全边界.md)
- [03 会话、记忆、Hooks 与 MCP](Part-09-Claude-Code/03-会话记忆Hooks与MCP.md)
- [04 大项目与多阶段任务工作流](Part-09-Claude-Code/04-大项目与多阶段任务工作流.md)
- [05 接入 DeepSeek 与第三方供应商](Part-09-Claude-Code/05-接入DeepSeek与第三方供应商.md)

Claude Code 可以使用 Anthropic 官方账户或 API，也可以接入受支持的云平台、DeepSeek 官方兼容接口、团队 LLM Gateway 或其他供应商。需要管理多套供应商配置时，也可以使用 CC Switch，具体使用方法可查阅 CC Switch 官方文档及本书相关章节。

### Part 10：Codex CLI

学习 Codex CLI 的安装、Sandbox、审批、交互模式、自动化和 Git 协作。

- [01 安装、登录与启动](Part-10-Codex-CLI/01-安装登录与启动.md)
- [02 Sandbox、审批与配置](Part-10-Codex-CLI/02-Sandbox审批与配置.md)
- [03 交互模式与自动化](Part-10-Codex-CLI/03-交互模式与自动化.md)
- [04 Codex CLI 与 Git 协作案例](Part-10-Codex-CLI/04-Codex与Git协作案例.md)

### Part 10B：Grok CLI

学习 Grok CLI 的基础使用、权限、Sandbox、Headless、Worktree 和扩展系统。

- [01 安装、登录与基础使用](Part-10B-Grok-CLI/01-安装登录与基础使用.md)
- [02 权限、Sandbox 与项目配置](Part-10B-Grok-CLI/02-权限Sandbox与项目配置.md)
- [03 Headless、Worktree 与扩展系统](Part-10B-Grok-CLI/03-Headless-Worktree与扩展系统.md)

### Part 11：GPU 远程开发

这一部分属于可选扩展，适合希望用 Mac 负责日常开发、让 Ubuntu 或远程服务器负责 NVIDIA GPU 计算的读者。

- [01 Mac 与 Ubuntu 游戏本的局域网部署](Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md)
- [02 项目同步与目录规范](Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [03 tmux 与断线后继续训练](Part-11-GPU远程开发/03-tmux与断线续跑.md)
- [04 NVIDIA 驱动、CUDA 与 PyTorch](Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)
- [05 Mac 与 Ubuntu 分别创建环境](Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)
- [06 异网安全连接](Part-11-GPU远程开发/06-异网安全连接.md)
- [07 VS Code、AI CLI 与 GPU 协作](Part-11-GPU远程开发/07-VS-Code-AI-CLI与GPU协作.md)
- [08 实验日志与 Checkpoint 管理](Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)

### Part 12：AI 开发工作流

把不同 AI 编程工具统一到同一套调查、计划、实现、测试和复核流程中。

- [01 通用 AI 编程闭环](Part-12-AI开发工作流/01-通用AI编程闭环.md)
- [02 通用 Prompt 模板库](Part-12-AI开发工作流/02-通用Prompt模板库.md)
- [03 基础设施与远程开发 Prompt 模板](Part-12-AI开发工作流/03-基础设施Prompt模板.md)
- [04 权限与安全边界总览](Part-12-AI开发工作流/04-权限与安全边界总览.md)
- [05 复杂任务拆分与独立复核](Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)
- [06 Claude Code、Codex CLI 与 Grok CLI 对照协作](Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)
- [07 Mac 到 Ubuntu GPU 的端到端案例](Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)

### 附录与维护

- [快捷键速查表](Appendix/快捷键速查表.md)
- [危险命令清单](Appendix/危险命令清单.md)
- [术语表](Appendix/术语表.md)
- [版本化工具核对表](Appendix/版本化工具核对表.md)
- [内容审查记录](Appendix/内容审查记录.md)
- [更新记录](Appendix/更新记录.md)
- [自动检查报告](Appendix/自动检查报告.md)

---

## 默认环境与可选扩展

本书默认设备环境为：

```text
Mac
```

因此，终端基础、zsh、Homebrew、Git、Python、Docker Desktop 和 AI CLI 章节都优先从 Mac 用户的实际体验出发。

后续内容会根据需要扩展到：

- Ubuntu 或其他 Linux 环境；
- SSH 与远程服务器；
- Tailscale 异网组网；
- NVIDIA GPU、CUDA 和 PyTorch；
- tmux、训练日志和 checkpoint；
- Docker Engine 与 GPU 容器。

这些扩展章节彼此可以独立使用，不要求读者同时拥有 Mac、Ubuntu 游戏本、独立路由器和 NVIDIA GPU。

---

## 你可以建立怎样的工作流

只使用一台 Mac，也可以完成：

```text
进入项目目录
→ 创建 Git 分支
→ 使用 AI CLI 调查和修改
→ 运行测试
→ 检查 git diff
→ 提交或继续修改
```

需要远程计算时，再扩展为：

```text
Mac 上开发和复核
→ SSH 或 Tailscale 连接远程 Linux
→ Git 或 rsync 传输项目
→ tmux 中运行长任务
→ 保存日志、配置和 checkpoint
→ 把结果同步回 Mac
```

---

## 这本手册适合谁

- 日常主力设备是 Mac；
- 对终端、Shell 或 Linux 经验有限；
- 正在使用 Claude Code、Codex CLI 或 Grok CLI；
- 希望学习 Git、Python、Docker 等开发基础设施；
- 可能需要连接 Ubuntu、服务器或 GPU 机器；
- 希望理解命令为什么这样工作，而不是只复制粘贴；
- 希望 AI 帮助编程，同时保留对权限、测试和提交的控制。

---

## 写作原则

### 先说明上下文，再给命令

每条重要命令尽量回答：

```text
在哪台机器运行
当前目录是什么
会读取或修改哪些内容
怎样确认成功
失败后怎样停止或恢复
```

### 区分稳定知识与版本化知识

路径、Shell 和 Git 的基本模型相对稳定；Claude Code、Codex CLI、Grok CLI、Docker、uv、Tailscale、PyTorch 和模型接口更新较快。相关章节会保留稳定心智模型，同时要求结合当前官方文档和本机 `--help` 验证。

### 修改结果必须能够检查

AI CLI 完成修改后，至少查看：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

再运行项目规定的测试。工具给出的完成总结不能代替真实文件差异和测试结果。

---

## 项目状态

主体章节已经完成第一轮系统重写，目前覆盖：

- 终端、Shell、Git、SSH、Homebrew、Python 和 Docker；
- Claude Code、Codex CLI 和 Grok CLI；
- 多种 Claude Code 模型与供应商接入方式；
- Mac 与远程 Linux / GPU 协作；
- 通用 AI 编程闭环和 Prompt 模板；
- Markdown 结构、本地链接和目录引用自动检查。

自动检查报告位于 [Appendix/自动检查报告.md](Appendix/自动检查报告.md)。结构检查可以发现链接、标题和代码块问题，但不能替代外部链接检查、技术事实核对和真实环境测试。

---

## 项目维护

- [全书路线图](ROADMAP.md)
- [写作规范与内容审查标准](CONTRIBUTING.md)
- [内容审查记录](Appendix/内容审查记录.md)
- [更新记录](Appendix/更新记录.md)
- [自动检查报告](Appendix/自动检查报告.md)

手册中的命令必须结合自己的系统、目录、权限、软件版本、网络环境和备份情况执行。涉及删除、覆盖、管理员权限、远程机器、Git 历史和凭据时，先确认影响范围与恢复方式。