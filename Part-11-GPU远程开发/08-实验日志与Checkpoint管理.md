# 08 实验日志、代码快照与 Checkpoint 管理

> 最近核对：2026-07-29

远程训练真正容易丢失的不是终端窗口，而是整套实验上下文：使用了哪份代码和配置、什么数据版本、哪套 Python 与 CUDA 环境、从哪个 checkpoint 恢复，以及结果属于哪一轮。tmux 保留 SSH 断开后的会话，日志记录运行过程，代码与环境快照说明实验起点，checkpoint 保存能够继续训练的状态；它们解决的是不同问题。

```text
tmux
→ SSH 断开后保留会话和仍在运行的进程

日志与指标
→ 记录训练过程、警告、错误和数值变化

代码与环境快照
→ 说明实验基于哪份现实状态

checkpoint
→ 保存可用于恢复的训练状态
```

`tmux attach` 无法复活因关机、程序崩溃、CUDA OOM 或磁盘写满而终止的训练。断点续训必须由训练代码和 checkpoint 共同支持。

## 1. 每轮实验都建立独立目录并保存起点证据

Ubuntu 可以把运行结果放在：

```text
~/runs/my-project/
└── 2026-07-29_14-30-00_baseline_seed42/
```

目录名可包含时间、简短实验名和关键变量，不写 API Key、用户隐私、数据库密码、带凭据的下载 URL 或完整私人数据路径。多轮实验共用 `runs/current/` 会让配置、日志、指标和 checkpoint 相互覆盖。

一个较完整的运行目录可以是：

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

在项目根目录创建本轮目录：

```bash
PROJECT_NAME="my-project"
RUN_NAME="baseline_seed42"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"

mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf 'RUN_DIR=%s\n' "$RUN_DIR"
```

`RUN_DIR` 应作为显式参数传给训练程序，而不是由代码根据当前目录猜测输出位置。

代码证据至少记录提交、工作区和未跟踪路径：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff --binary HEAD > "$RUN_DIR/code.patch"
git ls-files --others --exclude-standard \
  > "$RUN_DIR/untracked-files.txt"
```

`git diff --binary HEAD` 包含已跟踪文件相对 `HEAD` 的已暂存与未暂存变化，却不保存未跟踪文件正文。影响实验的源码若仍是未跟踪文件，应先审查、排除秘密和数据，再加入 Git 并形成可解释提交。SHA、补丁和路径列表只能说明一部分现场，不能自动保证完整复现。

运行目录也不应为了“完整”而复制 `.env`、API Key、OAuth 缓存、`auth.json`、SSH 私钥、云凭据、数据库密码、私有样本或带签名 URL。记录凭据来源类型、数据版本标识和所需变量名称即可，秘密值继续由受控环境提供。

保存主机与软件环境：

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

python -m pip freeze > "$RUN_DIR/pip-freeze.txt"
```

`pip-freeze.txt` 是这台 Ubuntu 当时的安装快照，不是另一平台的通用依赖声明；完整 `env` 也不适合保存，因为它可能混入凭据。训练程序完成参数解析后，应把实际生效且已经脱敏的配置写入 `RUN_DIR/config.yaml`。启动命令保存脱敏版本：

```bash
printf '%q ' python train.py \
  --config config/train.yaml \
  --run-dir "$RUN_DIR" \
  > "$RUN_DIR/command.txt"
printf '\n' >> "$RUN_DIR/command.txt"
```

包含 `--token REAL_SECRET` 的原始 Shell 历史不能直接复制进运行目录。

## 2. 日志、指标、退出状态和 checkpoint 共同描述运行过程

训练命令既要保存标准错误，也要保留 Python 进程本身的退出状态：

```bash
set -o pipefail
python train.py \
  --run-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
TRAIN_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$TRAIN_STATUS" > "$RUN_DIR/exit-status.txt"
exit "$TRAIN_STATUS"
```

`train.log` 适合人阅读，逐步指标则适合 JSON Lines：

```json
{"step":100,"loss":1.42,"lr":0.0001}
{"step":200,"loss":1.18,"lr":0.0001}
```

每行是独立 JSON 对象，即使训练中途终止，已经刷新到磁盘的记录通常仍可读取。程序应及时写出关键日志和指标；退出状态为 0 只表示进程按约定结束，仍需检查日志结尾、指标完整性和预期文件。

能够连续训练的 checkpoint 通常要包含模型参数、优化器、学习率调度器、epoch 或 global step、混合精度 scaler、Python/NumPy/PyTorch 随机状态、数据采样器状态、关键配置和最佳指标。只保存模型权重更适合推理或重新开始优化，不能保证无缝续训。概念结构例如：

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

真实字段必须与项目代码匹配。写入时可以先保存临时文件，再在同一文件系统中原子替换正式路径，降低读取到半写文件的概率：

```python
from pathlib import Path
import os
import torch

final_path = Path(run_dir) / "checkpoints" / "latest.pt"
tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

torch.save(state, tmp_path)
os.replace(tmp_path, final_path)
```

原子替换不能替代恢复测试、磁盘监控和历史 checkpoint，也不应在文件正在写入时启动 rsync 回传。建议同时保留 `latest`、`best` 和周期性 `step-XXXX`：前者表示最近恢复点，`best` 由验证指标选出，周期文件提供历史回退；最佳指标的名称、数值和方向也应进入记录。

## 3. 长训练开始前先证明恢复链可用

在数小时训练前，用 5 到 20 个 step 生成 checkpoint，正常停止，再在新的运行目录中恢复 2 到 5 个 step：

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

恢复测试要确认文件能够加载，模型结构兼容，优化器和调度器状态恢复，global step 正确延续，数据路径存在，新日志没有覆盖旧实验，并且恢复后的配置符合预期。新的运行目录与 `resumed-from.txt` 保留来源关系，也避免把恢复过程混进原实验。

checkpoint 可能使用能够构造复杂对象的序列化格式，来源不可信的文件不能因为扩展名为 `.pt` 就直接加载。先查看元数据：

```bash
ls -lh "$CHECKPOINT_PATH"
file "$CHECKPOINT_PATH"
```

只需要权重时，应评估当前 PyTorch 版本提供的安全加载参数和项目兼容性。重要文件还可以生成 SHA-256：

```bash
# Ubuntu
sha256sum "$CHECKPOINT_PATH" \
  > "$CHECKPOINT_PATH.sha256"
```

传输到 Mac 后：

```bash
shasum -a 256 checkpoint.pt
cat checkpoint.pt.sha256
```

校验值能够发现传输后的内容变化，却不能证明来源可信、训练逻辑正确或指标有效。

## 4. 磁盘、保留策略和结果回传也是实验设计的一部分

训练前查看空间与大目录：

```bash
df -h "$HOME/runs"
du -sh "$HOME/runs/$PROJECT_NAME" 2>/dev/null || true

du -h "$HOME/runs/$PROJECT_NAME" \
  | sort -h \
  | tail -n 20
```

磁盘写满可能同时破坏日志、checkpoint、临时文件、数据缓存和 Git 操作。保留策略应明确周期 checkpoint 保留数量、`best` 是否长期保存、哪些关键实验保留完整配置与环境，以及删除前如何同步。未知 `runs` 目录不应交给 AI CLI 自动清理。

结果回传可以先取轻量证据：

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

Mac 收到结果后，应核对文件列表、退出状态、日志结尾、指标完整性、配置脱敏、Git SHA 与工作区状态、checkpoint 校验值和实验目录名称。一张损失曲线只能展示一部分结果，不能单独证明实验可复现。

## 5. 用训练脚本固化外壳，但让项目代码保存真实状态

项目可以创建 `scripts/run-experiment.sh`：

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

这只是通用外壳。真实训练代码仍需保存解析后的配置、结构化指标和 checkpoint，并实现可验证的恢复逻辑。正式运行前检查主机、目录、分支、HEAD、Python、CUDA、数据路径、输出路径、磁盘空间与恢复演练；运行中观察日志、指标、GPU 和周期 checkpoint；结束后核对退出状态、`best/latest/周期` 文件关系、代码与配置证据、结果回传和敏感信息。

## 继续阅读

- [tmux、日志与断线后继续训练](03-tmux与断线续跑.md)
- [VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)
- [Mac 到 Ubuntu GPU 的端到端案例](../Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)
