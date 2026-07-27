# 03 tmux 与断线后继续训练

SSH 窗口关闭后，直接依附在该终端上的训练可能一起结束。tmux 会在 Ubuntu 上创建一个独立终端会话，让你断开 SSH 后还能重新回来。

```text
Mac 的 SSH 连接
→ Ubuntu 上的 tmux 会话
→ Shell
→ 训练进程
```

但 tmux 只解决“终端断开”，不解决关机、休眠、程序崩溃、显存不足和磁盘写满。真正的断点续训仍依赖 checkpoint。

---

## 1. 安装和创建会话

Ubuntu：

```bash
sudo apt update
sudo apt install tmux
tmux -V
```

创建命名会话：

```bash
tmux new -s train-baseline
```

名称应体现用途，例如：

```text
train-baseline
train-exp001
jupyter
monitor
```

不要把所有任务都留成默认编号。

---

## 2. 在 tmux 中先确认环境

```bash
cd ~/projects/my-project
hostname
pwd
git status
python -c 'import sys; print(sys.executable)'
nvidia-smi
```

确认无误后再启动训练。

建议先创建独立实验目录：

```bash
RUN_DIR="$HOME/runs/my-project/$(date +%Y-%m-%d_%H-%M-%S)_baseline"
mkdir -p "$RUN_DIR"
printf '%s\n' "$RUN_DIR"
```

记录代码和环境：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
{
  date -Is
  hostname
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1
```

启动训练并保存日志：

```bash
set -o pipefail
python train.py 2>&1 | tee "$RUN_DIR/train.log"
```

`pipefail` 能让训练程序失败时，整条管道返回失败，而不是只看 `tee` 是否成功。

---

## 3. 正确离开：Detach，不是退出

默认前缀键：

```text
Ctrl + b
```

脱离会话：

```text
先按 Ctrl + b，松开，再按小写 d
```

看到类似：

```text
[detached from train-baseline]
```

之后可以退出 SSH：

```bash
exit
```

不要在 tmux 中输入 `exit` 来表示“暂时离开”。如果当前窗口最后一个 Shell 退出，窗口或整个会话可能结束。

---

## 4. 重新连接

```bash
ssh gpu-laptop
tmux ls
tmux attach -t train-baseline
```

简写：

```bash
tmux a -t train-baseline
```

如果会话已附着：

```bash
tmux attach -d -t train-baseline
```

`-d` 会把原客户端踢出附着状态。多人共同查看时不要随意使用。

---

## 5. 常用窗口操作

新建窗口：

```text
Ctrl + b，然后按小写 c
```

下一个窗口：

```text
Ctrl + b，然后按小写 n
```

上一个窗口：

```text
Ctrl + b，然后按小写 p
```

窗口列表：

```text
Ctrl + b，然后按小写 w
```

常见组织方式：

```text
窗口 0：训练
窗口 1：nvidia-smi
窗口 2：日志
窗口 3：Shell 或 AI CLI
```

刚开始只需要掌握创建、脱离、列出和恢复，不必立刻学习复杂分屏。

---

## 6. 日志不要只存在 tmux 滚动区

查看日志：

```bash
tail -f "$RUN_DIR/train.log"
```

`Ctrl + C` 只停止当前 `tail -f`，不会自动停止另一个窗口中的训练。

查看历史输出可以进入复制模式：

```text
Ctrl + b，然后按 [
```

但 tmux 滚动缓存不是实验日志，也不会在所有情况下永久保存。

---

## 7. 判断训练是否真的还活着

```bash
tmux ls
pgrep -af python
nvidia-smi
uptime
df -h "$HOME/runs"
```

需要结合判断：

- tmux 会话存在，不代表训练进程还在；
- Python 进程存在，不代表没有卡住；
- GPU 利用率低，不一定表示训练失败；
- 日志不更新，可能是缓冲、阻塞或程序停止。

检查最后日志：

```bash
tail -n 100 "$RUN_DIR/train.log"
```

---

## 8. 不要误杀会话

终止指定会话：

```bash
tmux kill-session -t train-baseline
```

这会终止其中全部窗口和进程。执行前确认训练已经结束或确实需要停止。

不要把下面命令当普通退出方式：

```bash
tmux kill-server
```

它会终止当前用户的所有 tmux 会话。

---

## 9. tmux、nohup 和 systemd 怎么选

### tmux

适合交互调试、手动训练和新手远程开发。

### nohup

适合简单、完全非交互并且日志重定向明确的命令。

### systemd

适合长期服务、开机启动、自动重启和规范化权限，不适合每个临时实验都单独配置。

机器学习实验的第一选择通常是 tmux；长期服务再考虑 systemd。

---

## 10. 最短操作卡片

```text
创建：tmux new -s NAME
脱离：Ctrl+b，再按小写 d
查看：tmux ls
恢复：tmux attach -t NAME
```

请牢记：

```text
tmux
→ 防 SSH 断线

checkpoint
→ 防训练进程终止后无法恢复
```

继续阅读：

- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)
- [VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)
