# 07 VS Code、AI CLI 与 GPU 协作

> 最近核对：2026-07-29

把 Mac、Ubuntu 游戏本、VS Code、AI CLI 和 GPU 接到一起之后，最重要的不是再增加一个工具，而是确定源码究竟以哪一端为准。Mac 和 Ubuntu 各保存一份可写副本、两边的 Agent 同时修改，最后再用 rsync 覆盖，是这套工作流中最容易制造混乱的状态。

本章只解决三件事：VS Code Remote SSH 中的程序实际运行在哪里，Mac 主副本与 Ubuntu 主副本怎样选择，以及 AI CLI 应在哪台机器工作。项目同步、tmux 和 checkpoint 已在前面的章节单独讲解，这里只保留连接它们所需的步骤。

## 1. Remote SSH 中的“本地”和“远程”

VS Code Remote SSH 不是远程桌面。图形界面仍在 Mac 上，但远程窗口里的项目文件、终端、解释器、调试进程和远程扩展位于 Ubuntu：

```text
Mac 上的 VS Code 界面
→ SSH 连接
→ Ubuntu 上的项目、Shell、Python、CUDA 和扩展
```

先在 Mac 终端确认普通 SSH 正常：

```bash
ssh gpu-laptop
```

随后使用 VS Code 的 Remote - SSH 扩展连接同一主机，只打开项目目录，例如：

```text
/home/YOUR_USER/projects/my-project
```

打开整个 `/`、完整家目录、数据集或运行结果目录，会让搜索、文件监视器、语言服务器和 AI 扩展扫描大量无关内容。远程窗口建立后，在终端确认实际环境：

```bash
hostname
uname -a
pwd
which python
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

项目解释器通常应指向 Ubuntu 项目中的 `.venv/bin/python`。Python、调试器、Linter、语言服务器、Notebook 和需要访问源码的 AI 扩展一般安装在远程侧；主题、键位和纯界面扩展留在 Mac。VS Code 显示 `Install Locally` 与 `Install in SSH: gpu-laptop` 时，选择依据是扩展要读取哪一端的文件和进程。

## 2. 一次任务只选一个源码主副本

**Mac 主副本**适合日常主要在 Mac 编辑，只把游戏本当作 GPU 节点：

```text
Mac 编辑与 Git
→ rsync 到 Ubuntu
→ Ubuntu 测试和训练
→ 指标与产物回传 Mac
```

**Ubuntu 主副本**适合项目强依赖 Linux、CUDA、大数据或远端环境：

```text
Mac 的 VS Code 界面
→ Remote SSH
→ 直接编辑 Ubuntu 项目
→ Ubuntu 本地测试和训练
```

模式选择以后，当前任务中的 Git、编辑器和 Agent 都围绕这份主副本工作。切换模式前处理完已有修改：提交、回收或明确放弃；不能让 Mac 和 Ubuntu 都保留一份“稍后再合并”的未提交版本。

## 3. AI CLI 应运行在能够完成主要验证的机器上

Mac 主副本模式下，从 Mac 项目根目录启动 Claude Code、Codex CLI 或 Grok Build。它负责不依赖 CUDA 的代码和测试，修改完成后由人阅读 diff，再通过同步脚本传到 Ubuntu：

```bash
cd ~/Projects/my-project
git status
git switch -c task/experiment-config
claude

# 修改并完成本地测试后
git status --short
git diff --stat
git diff
python -m pytest

./scripts/sync-to-gpu.sh --dry-run
./scripts/sync-to-gpu.sh
```

Ubuntu 收到文件后重新检查远端现实状态：

```bash
ssh gpu-laptop
cd ~/projects/my-project
hostname
pwd
git status --short
python -c 'import sys; print(sys.executable)'
python -c 'import torch; print(torch.cuda.is_available())'
python train.py --max-steps 2
```

同步成功只说明文件传输完成。解释器、依赖、CUDA 和训练入口仍需在 Ubuntu 验证。

Ubuntu 主副本模式下，AI CLI 直接运行在 VS Code 的远程终端中。它看到的就是 Ubuntu 文件和 Linux 环境，可以执行 CUDA 冒烟测试和远端专用问题复现。达到稳定检查点后，仍应由人查看 Git diff 并通过远程仓库保存代码；Ubuntu 不应成为唯一代码副本。

任务边界可引用项目中的 `AGENTS.md`、`CLAUDE.md` 和测试说明。Mac 与 Ubuntu 上的 CLI 应分别安装、登录和配置；`~/.codex`、`~/.claude`、`~/.grok`、Keychain/Keyring 和 OAuth 缓存不适合通过 rsync 整目录复制。

## 4. 编辑、调试和长任务分别交给不同工具

VS Code 适合编辑、断点调试和短测试。数小时训练放在普通 Remote SSH 终端中，一旦窗口关闭或连接中断，进程可能随会话结束。Ubuntu 上使用 tmux：

```bash
tmux new -s train-exp001
cd ~/projects/my-project
./scripts/run-train.sh exp001
```

脱离会话使用 `Ctrl + b` 后按小写 `d`。重新连接后恢复：

```bash
ssh gpu-laptop
tmux attach -t train-exp001
```

VS Code 保留编辑体验，tmux 保持仍在运行的进程，checkpoint 负责进程已经终止后的恢复。三者解决的问题不同。

Jupyter 建议只监听 Ubuntu 回环地址：

```bash
# Ubuntu
jupyter lab \
  --no-browser \
  --ip=127.0.0.1 \
  --port=8888
```

Mac 建立 SSH 隧道：

```bash
ssh -N \
  -L 18888:127.0.0.1:8888 \
  gpu-laptop
```

浏览器访问 `http://127.0.0.1:18888`。异网连接时使用对应的 Tailscale SSH 别名，Notebook 仍保持只监听远端回环地址。

GPU 改动先用少量样本和短训练验证：

```bash
nvidia-smi
python - <<'PY'
import torch
print("available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY
```

## 5. 控制 VS Code 的扫描范围

远程项目可以排除虚拟环境、数据、模型和运行目录：

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

这些设置只约束 VS Code 自己。Git、rsync、AI CLI、Docker 和语言服务器仍有各自的忽略或访问规则，不能把一个工具的排除配置当成整台机器的权限控制。

## 6. 并行方案使用 Worktree，而不是两端副本

需要比较两个实现时，在同一源码主端创建独立 Worktree：

```bash
git worktree add ../my-project-agent-a -b experiment/agent-a main
git worktree add ../my-project-agent-b -b experiment/agent-b main
```

两个目录分别运行 Agent 和测试，最后比较：

```bash
git diff main...experiment/agent-a
git diff main...experiment/agent-b
```

Worktree 能防止两个实现覆盖同一文件，但仍共享主机的凭证、网络、Docker、数据和 GPU。若两个方案都启动训练，还需要单独安排显存和数据访问。

一套清楚的端到端节奏是：先决定 Mac 或 Ubuntu 哪一端拥有当前源码主副本；在这一端建立分支并完成编辑与 diff；需要 GPU 时把已检查的版本送到 Ubuntu，运行 CUDA 冒烟和短训练；正式任务进入 tmux 和独立运行目录；结果回传后，再由人判断代码、指标和提交是否可以进入 PR。

继续阅读：[项目同步与目录规范](02-项目同步与目录规范.md)、[tmux、日志与断线后继续训练](03-tmux与断线续跑.md)和[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)。

官方参考：

- [VS Code：Remote SSH](https://code.visualstudio.com/docs/remote/ssh)