# 07 VS Code、AI CLI 与 GPU 协作

Mac、Ubuntu 游戏本、VS Code、AI CLI 和 GPU 不应该互相抢工作。更稳定的分工是：

```text
Mac
→ 阅读、编辑、Git、文档、轻量测试

Ubuntu
→ Linux 环境、NVIDIA GPU、数据、训练和长任务

VS Code Remote SSH
→ 让 Mac 界面直接操作 Ubuntu 项目

AI CLI
→ 在明确的一台机器和一个工作区中分析、修改和验证
```

---

## 1. Remote SSH 不是远程桌面

它的工作方式是：

```text
Mac 上运行 VS Code 界面
→ 通过 SSH 连接 Ubuntu
→ 文件、终端、扩展和调试运行在 Ubuntu
```

因此远程窗口中的：

- 文件实际存放在 Ubuntu；
- Python 解释器来自 Ubuntu；
- 终端命令在 Ubuntu 执行；
- GPU 由 Ubuntu 使用。

先保证命令行连接正常：

```bash
ssh gpu-laptop
```

然后再使用 VS Code 官方 Remote - SSH 扩展连接现有 SSH 别名。

不要直接打开整个 `/home` 或系统根目录。只打开项目目录，例如：

```text
/home/YOUR_USER/projects/my-project
```

---

## 2. 两种开发模式只能选一个主副本

### 模式 A：Mac 是源码主副本

```text
Mac 本地编辑和 Git
→ rsync 到 Ubuntu
→ Ubuntu 训练
→ 结果同步回 Mac
```

适合日常主要使用 Mac、只在训练时调用 Ubuntu 的情况。

### 模式 B：Ubuntu 是源码主副本

```text
Mac 上的 VS Code
→ Remote SSH
→ 直接编辑 Ubuntu 项目
→ Ubuntu 本地测试和训练
```

适合项目强依赖 Linux、GPU 或本地大型数据的情况。

最危险的状态是 Mac 和 Ubuntu 都被当作主副本，并且两边同时修改。一次任务必须指定唯一修改端。

---

## 3. 远程扩展和本地扩展不同

通常：

```text
需要读取或执行远程代码的扩展
→ 安装到远程 Ubuntu

只影响界面外观的扩展
→ 安装在本地 Mac
```

Python、调试器、语言服务器、Linter 和 Notebook 支持通常需要安装到远程环境。

在远程窗口中选择 Ubuntu 项目的解释器：

```text
/home/YOUR_USER/projects/my-project/.venv/bin/python
```

终端验证：

```bash
which python
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

不要误选 Mac 本地解释器。

---

## 4. 长任务必须离开 VS Code 终端生命周期

在普通 Remote SSH 终端直接运行训练，连接中断时任务可能结束。

使用 tmux：

```bash
tmux new -s train
```

再启动训练并写日志。脱离：

```text
Ctrl + B，然后按 D
```

重新连接：

```bash
tmux attach -t train
```

VS Code 适合编辑和调试，tmux 负责保持长任务，checkpoint 负责进程终止后的恢复。三者不是互相替代关系。

---

## 5. AI CLI 应运行在哪里

### 在 Mac 上运行

适合：

- Mac 是源码主副本；
- 修改不依赖 CUDA；
- 希望在本地查看 Git diff；
- Ubuntu 只负责运行。

### 在 Ubuntu 上运行

适合：

- Ubuntu 是源码主副本；
- 需要直接运行 Linux 测试；
- 需要检查 CUDA、驱动或 GPU；
- 数据和依赖只存在于 Ubuntu。

不要让 Mac 和 Ubuntu 上的两个 Agent 同时修改同一项目的两个副本。否则同步时很难判断哪边应该覆盖哪边。

---

## 6. 工作流一：Mac 修改，Ubuntu 运行

Mac：

```bash
cd ~/Projects/my-project
git status
git switch -c task/experiment-config
claude
```

也可以使用 Codex CLI 或 Grok CLI。完成后先检查：

```bash
git diff
```

预演同步：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ gpu-laptop:~/projects/my-project/
```

确认后正式同步。

Ubuntu：

```bash
ssh gpu-laptop
cd ~/projects/my-project
source .venv/bin/activate
python -c 'import torch; print(torch.cuda.is_available())'
tmux new -s experiment
```

然后创建独立运行目录并启动训练。

---

## 7. 工作流二：Remote SSH 直接开发

1. Mac 上 VS Code 连接 Ubuntu；
2. 打开远程项目目录；
3. 检查 Git 状态并创建任务分支；
4. 在远程终端启动一个 AI CLI；
5. 让它先只读调查；
6. 在 VS Code Source Control 中检查 diff；
7. 运行 Ubuntu 测试；
8. 在 tmux 中训练；
9. 人工提交并推送；
10. 将实验结果拉回 Mac。

这种模式通常不需要 rsync 源码，但仍应通过 GitHub 或其他远程仓库备份。Ubuntu 游戏本不应成为唯一代码副本。

---

## 8. Jupyter 只监听本机并通过隧道访问

Ubuntu：

```bash
jupyter lab --no-browser --ip=127.0.0.1 --port=8888
```

Mac：

```bash
ssh -N -L 18888:127.0.0.1:8888 gpu-laptop
```

浏览器访问：

```text
http://127.0.0.1:18888
```

异网时把主机别名换成 Tailscale 连接别名。不要为了方便把无认证 Jupyter 直接暴露到局域网或公网。

---

## 9. GPU 调试先使用小任务

远程终端检查：

```bash
nvidia-smi
python -c 'import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda")'
```

调试时优先：

- 减小 batch size；
- 限制数据量；
- 缩短训练轮次；
- 必要时关闭多进程 DataLoader；
- 固定随机种子；
- 保存日志。

不要一上来启动完整训练来验证一行代码是否正确。

---

## 10. 排除大型目录

VS Code、语言服务器和 AI CLI 可能递归扫描工作区。不要把数据集、模型、缓存和大量训练结果放在源码目录中。

VS Code 示例：

```json
{
  "files.watcherExclude": {
    "**/data/**": true,
    "**/models/**": true,
    "**/runs/**": true
  },
  "search.exclude": {
    "**/data/**": true,
    "**/models/**": true,
    "**/runs/**": true
  }
}
```

这只影响 VS Code，不会自动影响 Git、rsync 或 AI CLI。每个工具仍要单独配置边界。

---

## 11. 远程 AI CLI 的安全边界

Ubuntu 上的 Agent 可能接触 GPU、数据集、模型、Docker 和远程主目录。任务中明确：

```text
只处理当前项目目录。
不要读取 ~/.ssh、云凭据、浏览器数据或其他项目。
不要修改 datasets、models 和 runs 中的既有数据。
不要停止其他 GPU 进程。
不要修改驱动、CUDA、SSH、防火墙或系统服务。
不要执行 git commit 或 push。
```

从项目根目录启动，并使用受限权限。不要把整个 `$HOME`、Docker Socket 或敏感凭据目录交给不可信容器或扩展。

---

## 12. 推荐的最终分工

```text
Mac
→ 需求、阅读、Git、文档和复核

Ubuntu
→ Linux 测试、CUDA、训练和数据

Remote SSH
→ 远程编辑与调试

AI CLI
→ 当前唯一工作区中的限定任务

tmux
→ 保持长任务

checkpoint
→ 恢复中断训练
```

继续阅读：

- [项目同步与目录规范](02-项目同步与目录规范.md)
- [tmux 与断线后继续训练](03-tmux与断线续跑.md)
- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)

官方参考：

- [VS Code：Remote SSH](https://code.visualstudio.com/docs/remote/ssh)
