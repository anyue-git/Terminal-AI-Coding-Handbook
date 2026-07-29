# 07 VS Code、AI CLI 与 GPU 协作

> 最近核对：2026-07-29

Mac、Ubuntu 游戏本、VS Code、AI CLI 和 GPU 不应该互相抢工作。真正稳定的方案不是“所有工具同时打开”，而是让每个工具承担明确职责，并保证同一时刻只有一个源码主副本。

```text
Mac
→ 阅读、编辑、Git、文档和人工复核

Ubuntu
→ Linux 环境、NVIDIA GPU、数据、训练和长任务

VS Code Remote SSH
→ Mac 界面连接 Ubuntu 工作区

AI CLI
→ 在明确的一台机器和一个项目目录中分析、修改和验证

tmux
→ 保持长任务

checkpoint
→ 恢复终止的训练
```

## 1. Remote SSH 不是远程桌面

它的工作方式是：

```text
Mac 上运行 VS Code 图形界面
→ 通过 SSH 连接 Ubuntu
→ 文件、终端、扩展和调试进程位于 Ubuntu
```

因此远程窗口中：

- 文件实际存放在 Ubuntu；
- Python 解释器来自 Ubuntu；
- Shell 命令在 Ubuntu 执行；
- CUDA 和 GPU 来自 Ubuntu；
- 远程扩展安装在 Ubuntu 侧。

先在 Mac 终端验证：

```bash
ssh gpu-laptop
```

命令行连接正常后，再使用 VS Code 官方 Remote - SSH 扩展。不要用 VS Code 扩展掩盖基础 SSH 问题。

## 2. 只打开项目目录

远程窗口应打开：

```text
/home/YOUR_USER/projects/my-project
```

不要打开：

```text
/home/YOUR_USER
/
~/datasets
~/models
~/runs
```

打开范围过大会让文件监视器、搜索、语言服务器和 AI 扩展扫描大量数据、模型、缓存与凭据。

## 3. 两种开发模式必须二选一

### 模式 A：Mac 是源码主副本

```text
Mac 本地编辑与 Git
→ rsync 到 Ubuntu
→ Ubuntu 测试和训练
→ 结果同步回 Mac
```

适合日常主要使用 Mac，只把游戏本当 GPU 节点。

### 模式 B：Ubuntu 是源码主副本

```text
Mac VS Code
→ Remote SSH
→ 直接编辑 Ubuntu 项目
→ Ubuntu 本地测试和训练
```

适合项目强依赖 Linux、CUDA、大数据或只能在 Ubuntu 复现。

最危险的状态：

```text
Mac 本地 Agent 修改副本 A
同时
Ubuntu 远程 Agent 修改副本 B
然后 rsync 相互覆盖
```

一次任务必须明确唯一修改端。

## 4. 判断当前 VS Code 窗口在哪台机器

远程窗口左下角应显示 SSH 主机。终端中执行：

```bash
hostname
uname -a
pwd
```

再检查解释器：

```bash
which python
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

远程 Ubuntu 项目应使用类似：

```text
/home/YOUR_USER/projects/my-project/.venv/bin/python
```

不要误选 Mac 的本地解释器，也不要把 Ubuntu 系统 Python 当作项目环境。

## 5. 本地扩展与远程扩展

一般规律：

```text
界面主题、键位、纯 UI 扩展
→ Mac 本地

Python、调试器、Linter、语言服务器、Notebook、AI CLI 集成
→ Ubuntu 远程
```

安装扩展时注意 VS Code 按钮显示的是：

```text
Install Locally
Install in SSH: gpu-laptop
```

需要访问远程源码和解释器的扩展，应安装到远程侧。

## 6. 工作流一：Mac 修改，Ubuntu 运行

### Mac：建立任务分支

```bash
cd ~/Projects/my-project
git status
git switch -c task/experiment-config
```

在项目根目录启动一个 AI CLI：

```bash
claude
```

也可以使用：

```bash
codex
grok
```

任务边界示例：

```text
先只读检查训练入口和配置。
只允许修改 src/train.py、config.example.yaml 和对应测试。
不要安装依赖，不要修改数据、模型或 runs。
不要执行 git add、commit 或 push。
完成后给出测试命令和 Ubuntu CUDA 验证步骤。
```

修改后：

```bash
git status --short
git diff --stat
git diff
python -m pytest
```

### Mac：同步到 Ubuntu

```bash
./scripts/sync-to-gpu.sh --dry-run
./scripts/sync-to-gpu.sh
```

### Ubuntu：验证现实状态

```bash
ssh gpu-laptop
cd ~/projects/my-project
hostname
pwd
git status --short
python -c 'import sys; print(sys.executable)'
python -c 'import torch; print(torch.cuda.is_available())'
```

不要因为同步成功就直接启动数小时训练。先运行：

```bash
python train.py --max-steps 2
```

短任务通过后再进入 tmux 正式运行。

## 7. 工作流二：Remote SSH 直接开发

步骤：

1. Mac VS Code 连接 `gpu-laptop`；
2. 打开 Ubuntu 项目目录；
3. `git status` 并建立任务分支；
4. 选择 Ubuntu `.venv`；
5. 在远程终端启动一个 AI CLI；
6. 第一轮只读调查；
7. 修改少量文件；
8. 在 VS Code Source Control 与 `git diff` 中复核；
9. 运行 Ubuntu 测试与 CUDA 冒烟测试；
10. 在 tmux 中正式训练；
11. 人工提交和推送；
12. 拉回实验结果。

这种模式不需要 rsync 源码，但 Ubuntu 不能成为唯一代码副本。稳定进度仍应通过 Git 远程仓库保存。

## 8. AI CLI 应运行在哪里

### 在 Mac 运行

适合：

- Mac 是源码主副本；
- 任务不依赖 CUDA；
- 希望本地检查 Git diff；
- Ubuntu 只负责运行和验证。

### 在 Ubuntu 运行

适合：

- Ubuntu 是源码主副本；
- 需要 Linux 测试；
- 需要读取 GPU、驱动或 CUDA 状态；
- 数据和依赖只存在于 Ubuntu；
- 调试只在远程环境复现的问题。

### 不要这样做

```text
Mac Claude Code 修改项目
Ubuntu Codex 同时修改另一份项目
Grok 在第三个 Worktree 自动重构
```

除非三者位于明确隔离的分支或 Worktree，并由人统一比较，否则会制造难以合并的状态。

## 9. 远程 AI CLI 的权限边界

Ubuntu 上的 Agent 可能接触：

- GPU；
- 数据集和模型；
- Docker；
- SSH 配置；
- 云服务凭据；
- 其他项目；
- 长时间训练进程。

Prompt 中明确：

```text
只处理当前项目目录。
不要读取 ~/.ssh、云凭据、浏览器数据或其他项目。
不要修改 ~/datasets、~/models 和 ~/runs 中已有内容。
不要停止其他 GPU 进程。
不要修改驱动、CUDA、SSH、防火墙、Tailscale 或系统服务。
不要运行 sudo。
不要执行 git commit、push、reset、clean 或 rebase。
安装依赖和扩大范围前先说明。
```

同时使用客户端真实 Sandbox 和审批机制。Prompt 不是操作系统隔离。

## 10. 配置与凭证如何同步

项目规则可以通过 Git 同步，例如：

```text
AGENTS.md
CLAUDE.md
项目测试命令
配置模板
```

不要直接 rsync：

```text
~/.codex/
~/.claude/
~/.grok/
Keychain 或 Keyring
API Key
OAuth 缓存
```

Mac 和 Ubuntu 上的 AI CLI 应分别安装、登录和配置。需要接入第三方供应商、CC Switch 或 Cockpit Tools 时，先阅读 Part 10C：

- [Codex 的 TOML、Profile 与凭证](../Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)
- [Claude Code 配置、凭证与网关](../Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)
- [CC Switch、ccswitch 与 Cockpit Tools](../Part-10C-配置凭证与多实例/04-CC-Switch-ccswitch与Cockpit-Tools.md)

Mac 上切换供应商，不会自动改变 Ubuntu 远程 Agent 的配置。

## 11. 长任务必须脱离 VS Code 终端生命周期

在 Remote SSH 普通终端中直接启动训练，窗口重载、网络中断或 VS Code 关闭时可能影响进程。

Ubuntu：

```bash
tmux new -s train-exp001
cd ~/projects/my-project
./scripts/run-train.sh exp001
```

脱离：

```text
Ctrl + b，然后按小写 d
```

重新连接：

```bash
ssh gpu-laptop
tmux attach -t train-exp001
```

职责：

```text
VS Code
→ 编辑和调试

tmux
→ 保持长任务

checkpoint
→ 进程终止后恢复
```

## 12. Jupyter 通过隧道使用

Ubuntu：

```bash
jupyter lab \
  --no-browser \
  --ip=127.0.0.1 \
  --port=8888
```

Mac：

```bash
ssh -N \
  -L 18888:127.0.0.1:8888 \
  gpu-laptop
```

异网时：

```bash
ssh -N \
  -L 18888:127.0.0.1:8888 \
  gpu-laptop-remote
```

浏览器访问：

```text
http://127.0.0.1:18888
```

不要把 Notebook 直接监听到公网或整个局域网。

## 13. GPU 调试使用小任务

先检查：

```bash
nvidia-smi
python - <<'PY'
import torch
print("available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY
```

调试训练优先：

- 少量样本；
- 2 到 10 个 step；
- 小 batch；
- 单进程 DataLoader；
- 固定随机种子；
- 保存日志；
- 禁用不必要的分布式组件。

不要用完整训练验证一行代码是否正确。

## 14. 排除大型目录

项目级 VS Code 设置示例：

```json
{
  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/data/**": true,
    "**/models/**": true,
    "**/runs/**": true
  },
  "search.exclude": {
    "**/.venv/**": true,
    "**/data/**": true,
    "**/models/**": true,
    "**/runs/**": true
  }
}
```

这只影响 VS Code。Git、rsync、AI CLI、Docker 和语言服务器仍需自己的排除规则。

## 15. 并行方案使用 Worktree

需要比较两个 Agent 方案时，在 Ubuntu 或 Mac 创建独立 Worktree：

```bash
git worktree add ../my-project-agent-a -b experiment/agent-a main
git worktree add ../my-project-agent-b -b experiment/agent-b main
```

分别运行 Agent，最终比较：

```bash
git diff main...experiment/agent-a
git diff main...experiment/agent-b
```

Worktree 只隔离 Git 工作目录，不隔离：

- 家目录；
- AI CLI 登录；
- GPU；
- Docker Socket；
- 网络；
- 数据集和模型。

不要让两个长训练争用同一块 GPU，却误以为 Worktree 已经完成资源隔离。

## 16. 一次端到端协作模板

```text
Mac
1. 明确任务和修改端
2. 建立 Git 分支
3. 让 AI CLI 只读分析
4. 修改和运行本地测试
5. 人工检查 diff
6. rsync 预演和同步

Ubuntu
7. 核对主机、目录、提交和解释器
8. CUDA 冒烟测试
9. 短训练
10. 创建运行目录
11. 在 tmux 中正式训练
12. 保存日志和 checkpoint

Mac
13. 拉回指标和图表
14. 独立审查代码与结果
15. 人工提交或创建 PR
```

## 继续阅读

- [项目同步与目录规范](02-项目同步与目录规范.md)
- [tmux、日志与断线后继续训练](03-tmux与断线续跑.md)
- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)

官方参考：

- [VS Code：Remote SSH](https://code.visualstudio.com/docs/remote/ssh)
