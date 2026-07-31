# 目录

## 00：快速开始

- [01 终端十五分钟上手](00-快速开始/01-终端十五分钟上手.md)
- [02 AI CLI 快速上手](00-快速开始/02-AI-CLI快速上手.md)
- [完整快速入门：终端与 AI CLI](Quickstart/终端与AI-CLI快速入门.md)
- [快捷键速查表](Appendix/快捷键速查表.md)
- [危险命令清单](Appendix/危险命令清单.md)

## 项目说明

- [项目介绍](README.md)
- [全书路线图](ROADMAP.md)
- [V3.0 叙事重构路线图](V3.0-ROADMAP.md)
- [V3.1 发布说明草案](RELEASE_NOTES_V3.1.md)
- [V3.0 发布说明](RELEASE_NOTES_V3.0.md)
- [V2.0 发布说明](RELEASE_NOTES_V2.0.md)
- [写作规范与内容审查标准](CONTRIBUTING.md)

## Part 01：基础篇

- [01 为什么程序员离不开终端](Part-01-基础篇/01-为什么程序员离不开终端.md)
- [02 Terminal 到底是什么](Part-01-基础篇/02-Terminal到底是什么.md)
- [03 Shell 到底是什么](Part-01-基础篇/03-Shell到底是什么.md)
- [04 zsh 到底是什么](Part-01-基础篇/04-zsh到底是什么.md)
- [05 文件系统、目录与路径](Part-01-基础篇/05-文件系统目录与路径.md)

## Part 02：终端命令

- [01 pwd、ls 与 cd](Part-02-终端命令/01-pwd-ls-cd.md)
- [02 创建、复制、移动与删除](Part-02-终端命令/02-创建复制移动与删除.md)
- [03 查看文本文件与日志](Part-02-终端命令/03-查看文本文件与日志.md)
- [04 搜索文件与文本](Part-02-终端命令/04-搜索文件与文本.md)
- [05 管道、重定向与命令组合](Part-02-终端命令/05-管道重定向与命令组合.md)
- [06 进程、前台、后台与任务控制](Part-02-终端命令/06-进程前台后台与任务控制.md)

## Part 03：Shell 快捷键

- [01 命令行编辑核心快捷键](Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)

## Part 04：Git

- [01 Git 心智模型](Part-04-Git/01-Git心智模型.md)
- [02 日常提交与复核流程](Part-04-Git/02-日常提交与复核流程.md)
- [03 分支、合并与安全恢复](Part-04-Git/03-分支合并与安全恢复.md)
- [04 Pull Request 与多人协作](Part-04-Git/04-Pull-Request与多人协作.md)

## Part 05：SSH

- [01 SSH 基础与首次连接](Part-05-SSH/01-SSH基础与首次连接.md)
- [02 密钥登录与 SSH Config](Part-05-SSH/02-密钥登录与SSH-Config.md)
- [03 scp、rsync 与端口转发](Part-05-SSH/03-scp-rsync与端口转发.md)
- [04 SSH 故障排查](Part-05-SSH/04-SSH故障排查.md)

## Part 06：Homebrew

- [01 Homebrew 与 PATH](Part-06-Homebrew/01-Homebrew与PATH.md)
- [02 服务、版本与常见故障](Part-06-Homebrew/02-服务版本与常见故障.md)

## Part 07：Python 环境

- [01 Python 解释器与 pip 定位](Part-07-Python环境/01-Python解释器与pip定位.md)
- [02 venv、Conda 与 uv 怎么选](Part-07-Python环境/02-venv-Conda与uv怎么选.md)
- [03 依赖声明、锁定与环境复现](Part-07-Python环境/03-依赖声明锁定与环境复现.md)

## Part 08：Docker

- [01 镜像、容器、卷与网络](Part-08-Docker/01-镜像容器卷与网络.md)
- [02 Docker Desktop 与 Ubuntu Docker Engine](Part-08-Docker/02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [03 Docker Compose 多服务项目](Part-08-Docker/03-Docker-Compose多服务项目.md)
- [04 GPU 容器与权限边界](Part-08-Docker/04-GPU容器与权限边界.md)

## Part 09：Claude Code

- [01 安装、登录与启动](Part-09-Claude-Code/01-安装登录与启动.md)
- [02 权限、审批与安全边界](Part-09-Claude-Code/02-权限审批与安全边界.md)
- [03 会话、记忆、Hooks 与 MCP](Part-09-Claude-Code/03-会话记忆Hooks与MCP.md)
- [04 大项目与多阶段任务工作流](Part-09-Claude-Code/04-大项目与多阶段任务工作流.md)
- [05 接入 DeepSeek 与第三方供应商](Part-09-Claude-Code/05-接入DeepSeek与第三方供应商.md)

## Part 10：Codex CLI

- [01 安装、登录与启动](Part-10-Codex-CLI/01-安装登录与启动.md)
- [02 Sandbox、审批与配置](Part-10-Codex-CLI/02-Sandbox审批与配置.md)
- [03 交互模式与自动化](Part-10-Codex-CLI/03-交互模式与自动化.md)
- [04 Codex CLI 与 Git 协作案例](Part-10-Codex-CLI/04-Codex与Git协作案例.md)

## Part 10B：Grok Build

> xAI 官方产品名为 Grok Build，终端命令为 `grok`。目录名保留 `Grok-CLI` 以兼容现有路径。

- [01 安装、登录与基础使用](Part-10B-Grok-CLI/01-安装登录与基础使用.md)
- [02 权限、Sandbox 与项目配置](Part-10B-Grok-CLI/02-权限Sandbox与项目配置.md)
- [03 Headless、Worktree 与扩展系统](Part-10B-Grok-CLI/03-Headless-Worktree与扩展系统.md)
- [04 TUI、斜杠命令与交互界面](Part-10B-Grok-CLI/04-TUI斜杠命令与交互界面.md)
- [05 会话、Memory 与后台任务](Part-10B-Grok-CLI/05-会话快照Memory与后台任务.md)
- [06 Goal、Workflow 与多 Agent 系统](Part-10B-Grok-CLI/06-Goal-Workflow与多Agent系统.md)
- [07 扩展系统、MCP、ACP 与跨客户端兼容](Part-10B-Grok-CLI/07-扩展系统MCP-ACP与跨客户端兼容.md)
- [08 配置、模型、诊断与功能核对](Part-10B-Grok-CLI/08-配置模型诊断与功能核对.md)
- [09 终端子命令与完整功能索引](Part-10B-Grok-CLI/09-终端子命令与完整功能索引.md)

## Part 10C：配置、凭证与多实例

> 先理解客户端、模型、Provider、凭证、Profile 和实例，再使用 CC Switch、ccswitch 或 Cockpit Tools。

- [01 先分清配置、凭证、供应商与实例](Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)
- [02 Codex 的 TOML、Profile 与凭证](Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)
- [03 Claude Code 的配置、凭证与网关](Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)
- [04 CC Switch、ccswitch 与 Cockpit Tools](Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)

## Part 11：GPU 远程开发

- [01 Mac 与 Ubuntu 游戏本的局域网部署](Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md)
- [02 项目同步与目录规范](Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [03 tmux 与断线后继续训练](Part-11-GPU远程开发/03-tmux与断线续跑.md)
- [04 NVIDIA 驱动、CUDA 与 PyTorch](Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)
- [05 Mac 与 Ubuntu 分别创建环境](Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)
- [06 异网安全连接](Part-11-GPU远程开发/06-异网安全连接.md)
- [07 VS Code、AI CLI 与 GPU 协作](Part-11-GPU远程开发/07-VS-Code-AI-CLI与GPU协作.md)
- [08 实验日志与 Checkpoint 管理](Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)

## Part 12：AI 开发工作流

- [01 通用 AI 编程闭环](Part-12-AI开发工作流/01-通用AI编程闭环.md)
- [02 通用 Prompt 模板库](Part-12-AI开发工作流/02-通用Prompt模板库.md)
- [03 基础设施与远程开发 Prompt 模板](Part-12-AI开发工作流/03-基础设施Prompt模板.md)
- [04 权限与安全边界总览](Part-12-AI开发工作流/04-权限与安全边界总览.md)
- [05 复杂任务拆分与独立复核](Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)
- [06 Claude Code、Codex CLI 与 Grok Build 对照协作](Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)
- [07 Mac 到 Ubuntu GPU 的端到端案例](Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)

## 附录与维护

- [快捷键速查表](Appendix/快捷键速查表.md)
- [危险命令清单](Appendix/危险命令清单.md)
- [术语表](Appendix/术语表.md)
- [版本化工具核对表](Appendix/版本化工具核对表.md)
- [公开仓库发布流程](Appendix/公开发布流程.md)
- [V3.1 Grok Build 专项审查](Appendix/V3.1-Grok-Build专项审查.md)
- [V3.0 叙事结构审计](Appendix/V3.0-叙事结构审计.md)
- [V3.0 文风二次审查](Appendix/V3.0-文风二次审查.md)
- [V3.0 样章内容覆盖](Appendix/V3.0-样章内容覆盖.md)
- [V3.0 批次一内容覆盖](Appendix/V3.0-批次一内容覆盖.md)
- [V3.0 批次二内容覆盖](Appendix/V3.0-批次二内容覆盖.md)
- [V3.0 批次三内容覆盖](Appendix/V3.0-批次三内容覆盖.md)
- [V3.0 批次四内容覆盖](Appendix/V3.0-批次四内容覆盖.md)
- [内容审查记录](Appendix/内容审查记录.md)
- [更新记录](Appendix/更新记录.md)
