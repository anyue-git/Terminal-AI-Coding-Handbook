# V2.0 发布说明

发布日期：2026-07-30

《终端与 AI 编程手册》V2.0 是一次面向终端新手的系统性重写。V1.0 以知识卡片和命令速查为主，V2.0 则把核心知识放入连续场景，补充执行位置、代表性输出、成功判断、故障层级、权限边界与恢复方法。

## 主要变化

### 更完整的新手路径

新增“终端十五分钟上手”“AI CLI 快速上手”和完整 Quickstart。读者可以在独立练习目录中完成导航、文件操作、Git 检查和一个受控的 AI Agent 任务，而不是先背完全部命令。

### 终端与开发基础重写

重新组织 Terminal、Shell、zsh、路径、文件操作、搜索、日志、管道、进程、Git、SSH、Homebrew、Python 和 Docker。重要命令尽量说明在哪台机器和哪个目录执行、可能看到什么输出、怎样确认成功，以及出错后先检查哪一层。

### AI 编程客户端体系

系统覆盖 Claude Code、Codex CLI 和 Grok Build，包括安装认证、权限、Sandbox、审批、会话、非交互运行、Worktree、Hooks、MCP、Plugins、Skills 与多 Agent 协作。

### 配置、凭证与多实例

新增 Part 10C，区分客户端、模型、Provider、Profile、账号、凭证、状态目录和独立实例，并讲解 Codex `config.toml`、`auth.json`、Claude Code Settings、Gateway、CC Switch、ccswitch 与 Cockpit Tools 的配置链和恢复方式。

### Mac 与 Ubuntu GPU 协作

Part 11 以 Mac 日常开发、Ubuntu 24.04 NVIDIA 游戏本承担训练为默认场景，覆盖局域网 OpenSSH、rsync、Tailscale、tmux、NVIDIA 驱动、CUDA、PyTorch、VS Code Remote SSH、AI CLI、日志和 checkpoint。

### 通用 AI 开发闭环

Part 12 统一采用：

```text
定义完成标准
→ 建立现实基线
→ 只读调查
→ 选择方案
→ 小批实施
→ 证据验证
→ 独立复核与人工提交
```

并补充复杂任务拆分、权限分层、证据账本、多 Agent Worktree 协作和 Mac 到 Ubuntu GPU 的端到端案例。

## 安全与兼容性修正

- 不提供真实 Token、Cookie、Refresh Token、私钥或登录缓存；
- 不把递归删除、Git 历史重写、Volume 删除或高权限容器作为普通模板；
- SSH 不关闭主机身份验证，也不建议直接暴露公网 TCP 22；
- Docker 不默认挂载 Socket、整个 HOME 或使用 `--privileged`；
- AI CLI 不默认跳过审批或获得最大权限；
- 已匿名化正文中的个人用户名、主目录和 SSH 用户示例；
- 已移除依赖 GNU `find -maxdepth` 的 Mac 示例；
- 实验补丁使用 `git diff --binary HEAD`，未跟踪文件单独记录。

## 验证

V2.0 私有源仓库最终重写 PR 为 #2，经过全量补丁审查和 Markdown Check #176，结果为成功。自动检查覆盖 UTF-8、标题、围栏代码块、内部链接、目录引用和异常短文件。

自动检查不能证明所有外部链接永久有效，也不能替代每台 Mac、Ubuntu、Docker、GPU 或 AI CLI 环境中的真实执行。快速变化的软件行为仍以当前官方文档和本机帮助为准。

## 升级方式

V2.0 将作为正常升级提交进入原有公共仓库，保留 V1.0 历史，不强制重写公开分支。公开仓库将使用 V2.0 标签和 GitHub Release 标记本次版本。

## 许可证说明

截至本次发布准备，作者尚未明确选择开源许可证，因此不会自动加入许可证文件。公开可见不等于自动授予复制、修改和再分发权限；后续如选择许可证，将单独记录。