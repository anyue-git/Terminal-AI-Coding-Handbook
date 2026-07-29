# 03 tmux、日志与断线后继续训练

> 最近核对：2026-07-29

直接在 SSH 窗口中运行训练时，终端关闭、网络切换或 Mac 休眠都可能让前台进程收到挂断信号。tmux 在 Ubuntu 上创建一个独立终端会话，使训练不再依附于当前 Mac 的 SSH 窗口。

```text
Mac 的 SSH 客户端
→ Ubuntu 上的 tmux 会话
→ Shell
→ 训练进程
```

但 tmux 只解决“客户端断开后终端会话仍在”。它不能解决：

- Ubuntu 关机或休眠；
- Python 进程崩溃；
- CUDA OOM；
- 磁盘写满；
- 训练代码异常退出；
- checkpoint 损坏；
- 机器被重启。

因此要同时理解：

```text
tmux
→ 保持终端会话

日志
→ 记录发生了什么

checkpoint
→ 进程终止后恢复训练状态
```

## 1. 在 Ubuntu 安装 tmux

以下命令在 **Ubuntu 游戏本**执行：

```bash
sudo apt update
sudo apt install tmux
tmux -V
```

输出类似：

```text
tmux 3.x
```

版本号可能不同。确认命令存在即可。

## 2. 创建命名会话

SSH 到 Ubuntu：

```bash
ssh gpu-laptop
```

创建会话：

```bash
tmux new -s train-exp001
```

建议名称包含任务意义：

```text
train-baseline
train-exp001
jupyter
monitor
```

不要长期依赖默认编号，否则多个任务并存时很难判断哪个会话能安全终止。

进入 tmux 后先执行：

```bash
hostname
whoami
pwd
echo "$TMUX"
```

`$TMUX` 非空通常表示当前 Shell 位于 tmux 中。

## 3. 创建独立运行目录

在 tmux 中进入项目：

```bash
cd ~/projects/my-project
```

检查现实状态：

```bash
git branch --show-current
git status --short
git rev-parse --short HEAD
python -c 'import sys; print(sys.executable)'
nvidia-smi
```

创建本次实验目录：

```bash
PROJECT_NAME="my-project"
RUN_NAME="baseline_seed42"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf 'RUN_DIR=%s\n' "$RUN_DIR"
```

不要让所有训练都写入 `runs/current`。独立目录能够避免日志、配置和 checkpoint 相互覆盖。

## 4. 启动前保存最小证据

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"

{
  date -Is
  hostname
  whoami
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1
```

不要把完整 `env` 输出写入实验目录，因为环境变量中可能包含 API Key、Token 和私有地址。

## 5. 用 `tee` 保存训练日志并保留退出状态

最简单的训练命令：

```bash
python train.py
```

更适合远程实验的形式：

```bash
set -o pipefail
python train.py \
  --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
TRAIN_STATUS=${PIPESTATUS[0]}
printf 'training exit status: %s\n' "$TRAIN_STATUS" \
  | tee -a "$RUN_DIR/train.log"
exit "$TRAIN_STATUS"
```

关键点：

```text
2>&1
→ 标准错误也进入日志

tee
→ 屏幕显示的同时写文件

pipefail / PIPESTATUS
→ 不把 tee 成功误认为训练成功
```

如果训练程序退出码为非零，Shell 也应保留失败状态。

## 6. 正确脱离：Detach，不是退出

默认 tmux 前缀键：

```text
Ctrl + b
```

脱离会话：

```text
先按 Ctrl + b
松开
再按小写 d
```

看到类似：

```text
[detached from train-exp001]
```

说明已经回到普通 SSH Shell。此时可以：

```bash
exit
```

不要在 tmux 中输入 `exit` 来表示“暂时离开”。如果当前窗口最后一个 Shell 退出，窗口和会话可能结束，其中的前台进程也会终止。

## 7. 重新连接和恢复会话

Mac：

```bash
ssh gpu-laptop
```

Ubuntu：

```bash
tmux ls
tmux attach -t train-exp001
```

简写：

```bash
tmux a -t train-exp001
```

如果显示会话已被另一个客户端附着，可以先判断是否真的是自己另一台终端。强制接管：

```bash
tmux attach -d -t train-exp001
```

`-d` 会让原客户端脱离，多人共同观察时不要随意使用。

## 8. 用多个窗口分离训练、监控与日志

在 tmux 中：

```text
新建窗口：Ctrl + b，然后按小写 c
下一个窗口：Ctrl + b，然后按小写 n
上一个窗口：Ctrl + b，然后按小写 p
窗口列表：Ctrl + b，然后按小写 w
重命名窗口：Ctrl + b，然后按逗号
```

推荐布局：

```text
窗口 0：训练
窗口 1：watch -n 2 nvidia-smi
窗口 2：tail -f train.log
窗口 3：Shell、Git 检查或 AI CLI
```

训练窗口和监控窗口分开后，按 `Ctrl + C` 停止 `watch` 或 `tail -f`，不会自动停止另一个窗口中的训练。

## 9. 日志不要只留在滚动区

查看实时日志：

```bash
tail -f "$RUN_DIR/train.log"
```

查看最后 100 行：

```bash
tail -n 100 "$RUN_DIR/train.log"
```

tmux 复制模式：

```text
Ctrl + b，然后按 [
```

复制模式适合临时回看，但 tmux 滚动缓存不是正式实验记录，也可能因为会话结束而消失。

## 10. 判断训练是否真的运行

不要只看 `tmux ls`。按层检查：

```bash
tmux ls
pgrep -af 'python.*train'
nvidia-smi
tail -n 50 "$RUN_DIR/train.log"
stat "$RUN_DIR/train.log"
df -h "$HOME/runs"
```

解释：

```text
tmux 会话存在
≠ 训练进程存在

Python 进程存在
≠ 训练没有卡死

GPU 利用率短时为 0
≠ 一定失败

日志未更新
→ 可能是缓冲、数据加载、阻塞、程序结束或磁盘问题
```

需要结合进程、GPU、日志时间戳和训练指标判断。

## 11. 网络断开演练

不要等正式训练时才第一次验证 tmux。

在 Ubuntu tmux 中运行：

```bash
for i in $(seq 1 120); do
  printf '%s step=%s\n' "$(date -Is)" "$i"
  sleep 1
done | tee ~/tmux-network-test.log
```

然后：

1. 使用 `Ctrl + b`、小写 `d` 脱离；
2. 关闭 Mac 当前 SSH 窗口；
3. 等待十几秒；
4. 重新 `ssh gpu-laptop`；
5. `tmux attach -t 会话名`；
6. 检查日志是否继续增长。

这只能证明 SSH 断开不会终止 tmux 中的进程，不代表关机后也能继续。

## 12. 停止训练与终止会话是两件事

训练窗口中按：

```text
Ctrl + C
```

通常向前台进程发送中断信号。训练程序是否会先保存 checkpoint，取决于代码实现。

终止整个会话：

```bash
tmux kill-session -t train-exp001
```

这会终止该会话的全部窗口和其中进程。执行前检查：

```bash
tmux list-windows -t train-exp001
pgrep -af 'python.*train'
```

不要把：

```bash
tmux kill-server
```

当作普通退出方式。它会终止当前用户的所有 tmux 会话。

## 13. tmux、nohup、systemd 怎么选

### tmux

适合：

- 手动训练；
- 需要实时观察和交互；
- 新手远程开发；
- 同时保留训练、日志和监控窗口。

### nohup

适合简单、完全非交互的单条命令，但必须自己处理 PID、日志、退出状态和停止方式。它不提供方便的交互会话。

### systemd

适合长期服务、开机启动、权限隔离和自动重启。临时实验每次都手写 systemd Service，维护成本较高。

### 任务调度器

团队服务器或多用户 GPU 环境更适合 Slurm 等调度器，而不是每个人用 tmux 抢占 GPU。本手册的单人游戏本场景优先使用 tmux。

## 14. 断线续跑与断点续训

```text
SSH 断开
→ tmux 中进程通常继续

Python 崩溃、OOM、重启或关机
→ tmux 无法恢复
→ 只能从训练程序保存的 checkpoint 恢复
```

正式长训练前应进行一次最小恢复测试：

```text
运行少量 step
→ 生成 checkpoint
→ 正常停止
→ 从 checkpoint 恢复 2 到 5 个 step
→ 验证 step、优化器和日志正确延续
```

详细流程见 [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)。

## 15. 推荐启动脚本

项目中创建：

```text
scripts/run-train.sh
```

示例：

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PROJECT_NAME="my-project"
RUN_NAME="${1:-baseline}"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"

printf '%s\n' "$RUN_DIR" > "$RUN_DIR/run-dir.txt"
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

printf 'python train.py --run-dir %q\n' "$RUN_DIR" \
  > "$RUN_DIR/command.txt"

set -o pipefail
python train.py --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
```

赋予权限：

```bash
chmod +x scripts/run-train.sh
```

在 tmux 中运行：

```bash
./scripts/run-train.sh baseline
```

真实项目还应保存最终解析配置、代码差异和 checkpoint 来源，下一章会继续完善。

## 最短操作卡片

```text
创建：tmux new -s NAME
脱离：Ctrl + b，然后按小写 d
查看：tmux ls
恢复：tmux attach -t NAME
```

请始终记住：

```text
tmux 防止 SSH 断线带走进程
checkpoint 防止训练进程终止后从零开始
```

## 继续阅读

- [NVIDIA 驱动、CUDA 与 PyTorch](04-NVIDIA驱动-CUDA与PyTorch.md)
- [VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)
- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)
