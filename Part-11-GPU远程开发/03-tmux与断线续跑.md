# 03 tmux、日志与断线后继续训练

> 最近核对：2026-07-29

直接在 SSH 前台运行训练时，终端关闭、网络切换或 Mac 休眠都可能影响前台进程。tmux 在 Ubuntu 上建立独立终端会话，使训练不再依附当前 Mac 的 SSH 窗口：

```text
Mac 的 SSH 客户端
→ Ubuntu 上的 tmux 会话
→ Shell
→ 训练进程
```

tmux 只解决客户端断开后的会话保留。Ubuntu 关机、Python 崩溃、CUDA OOM、磁盘写满或机器重启仍会结束训练；这些情况要靠日志和 checkpoint 判断与恢复。

## 1. 创建有名字的会话，并让任务留下正式日志

在 Ubuntu 安装 tmux：

```bash
sudo apt update
sudo apt install tmux
tmux -V
```

从 Mac 连接游戏本并创建会话：

```bash
ssh gpu-laptop
tmux new -s train-exp001
```

`train-baseline`、`train-exp001`、`jupyter` 和 `monitor` 比默认编号更容易辨认。进入后确认自己确实位于 Ubuntu 和 tmux 中：

```bash
hostname
whoami
pwd
echo "$TMUX"
```

`$TMUX` 非空通常表示当前 Shell 位于 tmux 会话。接着进入项目并检查代码、解释器与 GPU：

```bash
cd ~/projects/my-project
git branch --show-current
git status --short
git rev-parse --short HEAD
python -c 'import sys; print(sys.executable)'
nvidia-smi
```

每轮实验应使用自己的运行目录。完整目录结构、代码快照、配置和 checkpoint 规则见[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)；这里假设已经得到：

```bash
RUN_DIR="$HOME/runs/my-project/2026-07-30_baseline"
mkdir -p "$RUN_DIR"
```

启动训练时同时保存 stdout、stderr 和 Python 进程本身的退出状态：

```bash
set -o pipefail
python train.py \
  --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"

TRAIN_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$TRAIN_STATUS" > "$RUN_DIR/exit-status.txt"
exit "$TRAIN_STATUS"
```

`2>&1` 把错误信息送入日志，`tee` 同时显示和写文件，`PIPESTATUS[0]` 取得 Python 而不是 `tee` 的退出状态。实时观察与回看使用：

```bash
tail -f "$RUN_DIR/train.log"
tail -n 100 "$RUN_DIR/train.log"
```

`Ctrl + b` 后按 `[` 可以进入 tmux 复制模式，但滚动缓存不能代替正式实验日志。

## 2. 脱离、恢复和窗口管理

tmux 默认前缀键是 `Ctrl + b`。暂时离开会话时，按下前缀并松开，再按小写 `d`。看到类似：

```text
[detached from train-exp001]
```

说明已经回到普通 SSH Shell，这时可以使用 `exit` 关闭连接。训练窗口最后一个 Shell 中的 `exit` 会结束窗口，并可能结束其中的前台进程，不能用它表示“暂时离开”。

重新连接后恢复会话：

```bash
ssh gpu-laptop
tmux ls
tmux attach -t train-exp001
```

简写为：

```bash
tmux a -t train-exp001
```

会话被自己的另一条连接附着时，可以接管：

```bash
tmux attach -d -t train-exp001
```

`-d` 会让原客户端脱离，多人共同观察时不应随意使用。

一个会话可以分多个窗口：

```text
新建窗口：Ctrl + b，然后按小写 c
下一个窗口：Ctrl + b，然后按小写 n
上一个窗口：Ctrl + b，然后按小写 p
窗口列表：Ctrl + b，然后按小写 w
重命名窗口：Ctrl + b，然后按逗号
```

常见安排是训练、`watch -n 2 nvidia-smi`、`tail -f train.log` 和普通 Shell 各占一个窗口。停止监控命令不会影响另一窗口中的训练。

## 3. 会话存在并不能单独证明训练正常

结合进程、GPU、日志更新时间和磁盘空间判断：

```bash
tmux ls
pgrep -af 'python.*train'
nvidia-smi
tail -n 50 "$RUN_DIR/train.log"
stat "$RUN_DIR/train.log"
df -h "$HOME/runs"
```

```text
tmux 会话存在
≠ 训练进程仍存在

Python 进程存在
≠ 程序没有阻塞

GPU 利用率短时为 0
≠ 一定失败
```

日志长时间不更新可能来自输出缓冲、数据加载、程序阻塞、进程结束或磁盘问题，需要与进程和资源状态一起判断。

## 4. 停止训练和清理会话是两个动作

需要正常中断时，在训练窗口按 `Ctrl + C`。项目能否在收到中断时保存 checkpoint，取决于训练代码。准备结束整个会话前查看窗口和进程：

```bash
tmux list-windows -t train-exp001
pgrep -af 'python.*train'
```

确认后删除指定会话：

```bash
tmux kill-session -t train-exp001
```

这会结束该会话中的全部窗口和进程。`tmux kill-server` 会结束当前用户的所有 tmux 会话，不适合作为普通退出方式。

## 5. 正式训练前演练断线，并理解 tmux 的边界

在 Ubuntu tmux 中运行一个两分钟任务：

```bash
for i in $(seq 1 120); do
  printf '%s step=%s\n' "$(date -Is)" "$i"
  sleep 1
done | tee ~/tmux-network-test.log
```

用 `Ctrl + b`、小写 `d` 脱离，关闭 Mac 当前 SSH 窗口，稍后重新连接并 attach，确认任务和日志仍在继续。这项演练证明的是 SSH 断开不会带走 tmux 中的进程。

```text
SSH 断开
→ tmux 中的进程通常继续

Python 崩溃、OOM、重启或关机
→ tmux 无法恢复
→ 训练程序需要从 checkpoint 恢复
```

正式长训练前还应运行少量 step、生成 checkpoint、正常停止，再从该 checkpoint 恢复几个 step。记录和恢复验证见[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)。

手动训练和实时观察优先使用 tmux；`nohup` 适合完全非交互的单条命令，但需要自行管理 PID、日志和停止方式；systemd 适合长期服务；多人 GPU 服务器通常应使用 Slurm 等调度器。最短操作卡片仍是：创建 `tmux new -s NAME`，脱离时按 `Ctrl + b` 后按小写 `d`，查看 `tmux ls`，恢复 `tmux attach -t NAME`。

继续阅读：[NVIDIA 驱动、CUDA 与 PyTorch](04-NVIDIA驱动-CUDA与PyTorch.md)、[VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)和[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)。
