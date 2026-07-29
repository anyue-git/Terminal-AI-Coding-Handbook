# 08 实验日志、代码快照与 Checkpoint 管理

> 最近核对：2026-07-29

远程训练真正容易丢失的，不只是一个终端窗口，而是整套实验上下文：使用了哪份代码、哪个配置、什么数据版本、哪套 Python 与 CUDA 环境、从哪个 checkpoint 恢复，以及结果属于哪一轮。

先分清：

```text
tmux
→ SSH 断开后保留会话和仍在运行的进程

日志
→ 记录训练过程、指标、警告和错误

代码与环境快照
→ 说明实验基于什么现实状态

checkpoint
→ 保存可用于恢复的训练状态
```

`tmux attach` 无法复活因关机、程序崩溃、CUDA OOM 或磁盘写满而终止的训练。断点续训必须由训练程序和 checkpoint 共同支持。

## 1. 每轮实验使用独立目录

Ubuntu 推荐：

```text
~/runs/my-project/
└── 2026-07-29_14-30-00_baseline_seed42/
```

目录名建议包含：

```text
时间 + 简短实验名 + 关键变量
```

不要在目录名中写：

- API Key；
- 用户隐私；
- 数据库密码；
- 带凭据的下载 URL；
- 完整私人数据路径。

不要多轮实验都写入 `runs/current/`，否则日志、配置、指标和 checkpoint 很容易互相覆盖。

## 2. 推荐运行目录结构

```text
RUN_DIR/
├── config.yaml
├── command.txt
├── git-commit.txt
├── git-status.txt
├── code.patch
├── untracked-files.txt
├── environment.txt
├── pip-freeze.txt
├── train.log
├── exit-status.txt
├── metrics.jsonl
├── resumed-from.txt
├── checkpoints/
│   ├── step-001000.pt
│   ├── step-002000.pt
│   ├── best.pt
│   └── latest.pt
└── artifacts/
    ├── loss.png
    └── predictions.csv
```

含义：

```text
config.yaml
→ 本次实际生效且已脱敏的配置

command.txt
→ 已脱敏的启动命令

git-commit.txt
→ 当前 HEAD

git-status.txt
→ 已暂存、未暂存和未跟踪状态摘要

code.patch
→ 相对 HEAD 的已跟踪文件差异

untracked-files.txt
→ 未跟踪路径列表，不包含正文

environment.txt
→ 主机、Python、PyTorch、GPU 信息

metrics.jsonl
→ 机器可读取的逐步指标

checkpoints/
→ 训练恢复状态
```

## 3. 创建运行目录

在 Ubuntu 项目根目录：

```bash
PROJECT_NAME="my-project"
RUN_NAME="baseline_seed42"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"

mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf 'RUN_DIR=%s\n' "$RUN_DIR"
```

把 `RUN_DIR` 作为显式参数传给训练代码，而不是让程序自行猜测输出位置。

## 4. 正确记录 Git 代码状态

保存提交与状态：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
```

保存已跟踪文件相对 `HEAD` 的全部变化：

```bash
git diff --binary HEAD > "$RUN_DIR/code.patch"
```

保存未跟踪文件路径：

```bash
git ls-files --others --exclude-standard \
  > "$RUN_DIR/untracked-files.txt"
```

必须理解差异：

```text
git diff
→ 已跟踪、尚未暂存的修改

git diff --cached
→ 已暂存修改

git diff HEAD
→ 已暂存 + 未暂存的已跟踪修改

未跟踪文件
→ 不会被任何 git diff 自动记录
```

这里使用 `git diff --binary HEAD`，能够覆盖相对当前提交的已暂存与未暂存已跟踪文件变化。它仍然不保存未跟踪文件内容。

如果影响实验的源码仍是未跟踪文件，最稳妥的方法是：

```text
先审查
→ 排除秘密和数据
→ 加入 Git
→ 创建可解释提交
→ 再启动实验
```

只有 SHA、补丁和未跟踪文件名，并不能保证完整复现。

## 5. 不要把敏感文件打进代码快照

以下内容不能为了“可复现”直接复制到运行目录：

```text
.env
API Key
OAuth 缓存
auth.json
SSH 私钥
云凭据
数据库密码
私有数据样本
带签名的下载 URL
```

需要记录的是：

```text
使用了哪种凭据来源
使用了哪个数据版本标识
需要哪些环境变量名称
```

而不是秘密值本身。

## 6. 保存环境证据

```bash
{
  date -Is
  hostname
  whoami
  uname -a
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1
```

可选保存 Python 环境快照：

```bash
python -m pip freeze > "$RUN_DIR/pip-freeze.txt"
```

`pip-freeze.txt` 用于说明这台 Ubuntu 当时实际安装了什么，不一定适合作为 Mac 或另一台 Linux 机器的直接依赖文件。

不要保存完整 `env`，其中可能含有 Token 和私有地址。

## 7. 保存实际生效的配置

不要只复制项目默认配置。命令行参数、环境变量和代码默认值可能覆盖配置文件。

训练程序应在完成参数解析后，把最终配置写入：

```text
RUN_DIR/config.yaml
```

保存前删除或遮盖：

- Token；
- 密码；
- Cookie；
- 私有 URL 查询参数；
- 用户个人目录中无关部分。

`command.txt` 也保存脱敏版本。例如：

```bash
printf '%q ' python train.py \
  --config config/train.yaml \
  --run-dir "$RUN_DIR" \
  > "$RUN_DIR/command.txt"
printf '\n' >> "$RUN_DIR/command.txt"
```

不要把包含 `--token REAL_SECRET` 的原始 Shell 历史复制进去。

## 8. 同时保留人类日志和结构化指标

训练命令：

```bash
set -o pipefail
python train.py \
  --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
TRAIN_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$TRAIN_STATUS" > "$RUN_DIR/exit-status.txt"
exit "$TRAIN_STATUS"
```

结构化指标适合 JSON Lines：

```json
{"step":100,"loss":1.42,"lr":0.0001}
{"step":200,"loss":1.18,"lr":0.0001}
```

每行是一个独立 JSON 对象。训练中途结束时，已写入的行通常仍能读取。程序应及时刷新关键日志，不能等正常退出时才一次性写出。

## 9. checkpoint 应保存哪些状态

连续训练通常需要：

- 模型参数；
- 优化器状态；
- 学习率调度器；
- epoch 或 global step；
- 混合精度 scaler；
- Python、NumPy、PyTorch 随机状态；
- 数据采样器状态；
- 关键配置；
- 最佳指标。

只保存模型权重通常适合推理或重新开始优化，不保证无缝续训。

概念示例：

```python
state = {
    "model": model.state_dict(),
    "optimizer": optimizer.state_dict(),
    "scheduler": scheduler.state_dict(),
    "epoch": epoch,
    "global_step": global_step,
    "best_metric": best_metric,
}
```

实际字段必须和项目代码匹配。

## 10. 使用临时文件避免半个 checkpoint

```python
from pathlib import Path
import os
import torch

final_path = Path(run_dir) / "checkpoints" / "latest.pt"
tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

torch.save(state, tmp_path)
os.replace(tmp_path, final_path)
```

流程：

```text
写临时文件
→ 完成并关闭
→ 原子替换正式路径
```

同一文件系统中的 `os.replace` 通常能减少读取到半写文件的风险，但不能代替恢复测试、磁盘监控和保留历史 checkpoint。

不要在 checkpoint 正在写入时启动 rsync 回传。

## 11. `latest`、`best` 和周期性文件

```text
latest
→ 最近可恢复状态

best
→ 按验证指标选出的最佳模型

step-XXXX
→ 历史恢复点
```

建议同时保留：

- 最近若干周期 checkpoint；
- `latest`；
- `best`；
- 最佳指标名称、值和方向。

只有一个不断覆盖的 `latest.pt` 时，文件一旦损坏就没有回退点。

## 12. 正式训练前先验证恢复

不要训练十小时后才第一次测试 `--resume`。

推荐演练：

```text
1. 运行 5 到 20 个 step
2. 生成 checkpoint
3. 正常停止
4. 建立新的运行目录
5. 从 checkpoint 恢复 2 到 5 个 step
6. 核对 global step、优化器和日志
```

示例：

```bash
CHECKPOINT_PATH="$RUN_DIR/checkpoints/latest.pt"
NEW_RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_resume-test"
NEW_RUN_DIR="$HOME/runs/$PROJECT_NAME/$NEW_RUN_ID"
mkdir -p "$NEW_RUN_DIR/checkpoints" "$NEW_RUN_DIR/artifacts"

printf '%s\n' "$CHECKPOINT_PATH" \
  > "$NEW_RUN_DIR/resumed-from.txt"

python train.py \
  --resume "$CHECKPOINT_PATH" \
  --max-steps 2 \
  --run-dir "$NEW_RUN_DIR"
```

确认：

- 文件成功加载；
- 模型结构兼容；
- 优化器和调度器恢复；
- step 正确延续；
- 数据路径存在；
- 新日志没有覆盖旧实验；
- 恢复配置符合预期。

恢复训练建议创建新运行目录，并使用 `resumed-from.txt` 建立来源关系。

## 13. checkpoint 安全与可信来源

模型和 checkpoint 文件可能使用能够构造复杂对象的序列化格式。不要加载来源不可信的文件。

检查：

```bash
ls -lh "$CHECKPOINT_PATH"
file "$CHECKPOINT_PATH"
```

PyTorch 项目在只需要权重时，应评估当前版本提供的安全加载参数和项目兼容性。不能因为扩展名是 `.pt` 就认为文件只包含无害数字。

## 14. 为重要文件生成校验值

Ubuntu：

```bash
sha256sum "$CHECKPOINT_PATH" \
  > "$CHECKPOINT_PATH.sha256"
```

传输后在 Mac：

```bash
shasum -a 256 checkpoint.pt
cat checkpoint.pt.sha256
```

或使用兼容校验命令。SHA-256 可以发现传输后内容变化，但不能证明文件来源可信或训练结果正确。

## 15. 磁盘空间属于训练条件

训练前：

```bash
df -h "$HOME/runs"
du -sh "$HOME/runs/$PROJECT_NAME" 2>/dev/null || true
```

查看大型目录：

```bash
du -h "$HOME/runs/$PROJECT_NAME" \
  | sort -h \
  | tail -n 20
```

磁盘写满可能同时损坏：

- 日志；
- checkpoint；
- 临时文件；
- 数据缓存；
- Git 操作。

建立保留策略：

```text
保留最近 N 个周期 checkpoint
永久保留 best
关键实验保留完整配置和环境
删除前先同步重要结果
AI CLI 不自动清理未知 runs 目录
```

## 16. 结果回传到 Mac

先拉回轻量结果：

```bash
mkdir -p ~/ML-Runs/my-project
rsync -av --dry-run \
  --include '*/' \
  --include 'config.yaml' \
  --include 'command.txt' \
  --include 'git-commit.txt' \
  --include 'git-status.txt' \
  --include 'environment.txt' \
  --include 'train.log' \
  --include 'exit-status.txt' \
  --include 'metrics.jsonl' \
  --include '*.png' \
  --include '*.csv' \
  --include '*.sha256' \
  --exclude '*' \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

确认后去掉 `--dry-run`。

大型 checkpoint 可以等回到局域网再传，或只传 `best` 与校验文件。不要在训练仍写入目标文件时同步。

## 17. 结果回传后的人工核验

Mac：

```bash
find ~/ML-Runs/my-project -type f -print
```

对每轮重要实验检查：

```text
退出状态是否为 0
日志是否正常结束
指标是否完整
配置是否脱敏
Git SHA 是否存在
工作区是否有未提交差异
checkpoint 是否有校验值
结果是否对应预期实验名
```

不要只看一张漂亮的损失曲线就认定实验可复现。

## 18. 完整训练启动脚本

项目创建：

```text
scripts/run-experiment.sh
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

printf 'run_dir=%s\n' "$RUN_DIR"

git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff --binary HEAD > "$RUN_DIR/code.patch"
git ls-files --others --exclude-standard \
  > "$RUN_DIR/untracked-files.txt"

{
  date -Is
  hostname
  whoami
  uname -a
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1

python -m pip freeze > "$RUN_DIR/pip-freeze.txt"

printf 'python train.py --run-dir %q\n' "$RUN_DIR" \
  > "$RUN_DIR/command.txt"

set +e
set -o pipefail
python train.py --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
STATUS=${PIPESTATUS[0]}
set -e

printf '%s\n' "$STATUS" > "$RUN_DIR/exit-status.txt"
exit "$STATUS"
```

这仍是通用模板。真实训练代码需要自己保存解析配置、指标和 checkpoint。

## 19. 一轮实验的验收表

```text
开始前
□ 主机、目录、分支和 HEAD 正确
□ Python 与 CUDA 验证通过
□ 数据和输出路径正确
□ 磁盘空间足够
□ 恢复流程已做过小规模测试

运行中
□ tmux 会话存在
□ 日志持续写入
□ 指标合理
□ GPU 和显存符合预期
□ checkpoint 周期性生成

结束后
□ exit-status 已记录
□ 日志完整
□ best/latest/周期 checkpoint 关系清楚
□ 代码状态和配置可追踪
□ 结果已回传或备份
□ 未把秘密写进运行目录
```

## 继续阅读

- [tmux、日志与断线后继续训练](03-tmux与断线续跑.md)
- [VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)
- [Mac 到 Ubuntu GPU 的端到端案例](../Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)
