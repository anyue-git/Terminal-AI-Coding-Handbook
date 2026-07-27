# 08 实验日志与 Checkpoint 管理

远程训练真正容易丢失的，不只是终端窗口，而是实验上下文：用了哪份代码、什么配置、哪个数据版本、从哪个 checkpoint 恢复，以及结果到底属于哪一轮。

先分清：

```text
tmux
→ SSH 断开后保留终端和仍在运行的进程

日志
→ 记录训练过程、指标和错误

checkpoint
→ 保存可以用于恢复的训练状态
```

`tmux attach` 不能复活已经因为关机、崩溃、显存不足或磁盘写满而终止的训练。断点续训必须由训练程序和 checkpoint 共同支持。

---

## 1. 每轮实验使用独立目录

推荐：

```text
~/runs/my-project/
└── 2026-07-28_14-30-00_baseline_seed42/
```

目录名可以包含：

```text
时间 + 简短实验名 + 随机种子
```

不要多轮训练都写入 `runs/current/`，否则容易发生：

- 日志互相追加；
- 新 checkpoint 覆盖旧文件；
- 指标和配置对应不上；
- 恢复时读错实验；
- 清理文件时无法判断哪些仍有用。

不要在目录名中写 API Key、用户信息或私人数据路径。

---

## 2. 推荐目录结构

```text
RUN_DIR/
├── config.yaml
├── command.txt
├── git-commit.txt
├── git-status.txt
├── code.patch
├── untracked-files.txt
├── environment.txt
├── train.log
├── metrics.jsonl
├── checkpoints/
│   ├── epoch-0005.pt
│   ├── epoch-0010.pt
│   ├── best.pt
│   └── latest.pt
└── artifacts/
    ├── loss.png
    └── predictions.csv
```

其中：

- `config.yaml`：本次实际解析后的配置；
- `command.txt`：脱敏后的启动命令；
- `git-commit.txt`：源码提交；
- `git-status.txt`：启动时已暂存、未暂存和未跟踪文件的简短状态；
- `code.patch`：相对 `HEAD` 的已暂存和未暂存的已跟踪文件差异；
- `untracked-files.txt`：未跟踪文件的路径清单，不包含文件内容；
- `environment.txt`：Python、PyTorch、GPU 和主机信息；
- `train.log`：人类可读日志；
- `metrics.jsonl`：程序可解析指标；
- `checkpoints/`：恢复状态；
- `artifacts/`：图表和预测结果。

---

## 3. 启动前保存可追溯信息

```bash
PROJECT_NAME="my-project"
RUN_NAME="baseline_seed42"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf '%s\n' "$RUN_DIR"
```

保存代码状态：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff --binary HEAD > "$RUN_DIR/code.patch"
git ls-files --others --exclude-standard > "$RUN_DIR/untracked-files.txt"
```

这些命令的范围不同：

- `git diff`：只记录已跟踪文件中尚未暂存的修改；
- `git diff --cached`：只记录已经加入暂存区的修改；
- `git diff HEAD`：同时记录已暂存和未暂存的已跟踪文件修改；
- 未跟踪文件不会被上述任何 `diff` 自动记录。

这里使用 `git diff --binary HEAD`，让 `code.patch` 覆盖相对当前提交的已暂存和未暂存的已跟踪文件差异；`--binary` 还会为 Git 能表示的二进制修改生成补丁信息。`untracked-files.txt` 只保存未跟踪文件名，不能保存这些文件的内容。

如果真正影响实验的源码仍处于未跟踪状态，应在启动前审查并提交，或者在排除 `.env`、凭据、数据集和其他敏感内容后，另行复制到受控的实验快照。仅有提交 SHA、补丁和未跟踪文件名清单，仍不一定足以完整复现实验。

保存环境：

```bash
{
  date -Is
  hostname
  whoami
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1
```

不要保存完整环境变量。里面可能有 API Key、Token 和私有地址。

---

## 4. 保存实际生效的配置

不要只复制项目默认配置，因为命令行参数、环境变量和代码逻辑可能覆盖它。

训练程序应把最终解析后的配置写入：

```text
RUN_DIR/config.yaml
```

写入前删除：

- API Key；
- 数据库密码；
- 私有下载令牌；
- Cookie；
- 无需记录的个人路径。

`command.txt` 同样保存脱敏版本，不要把秘密值写进实验目录。

---

## 5. 日志既要给人看，也要给程序读

启动脚本中：

```bash
set -euo pipefail
python train.py --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/train.log"
```

`pipefail` 能保留训练程序失败的退出状态。

程序可解析指标适合使用 JSON Lines：

```json
{"step":100,"loss":1.42,"lr":0.0001}
{"step":200,"loss":1.18,"lr":0.0001}
```

每行是一个独立 JSON 对象，即使训练中途结束，已经写入的行通常仍可读取。程序应及时刷新关键日志，而不是等退出时一次写完。

---

## 6. checkpoint 要保存哪些状态

典型训练恢复可能需要：

- 模型参数；
- 优化器状态；
- 学习率调度器状态；
- 当前 epoch 或 step；
- 混合精度 scaler；
- 随机数状态；
- 数据采样器状态；
- 关键配置。

只保存模型权重通常适合推理或重新开始优化，不一定能无缝续训。

概念示例：

```python
state = {
    "model": model.state_dict(),
    "optimizer": optimizer.state_dict(),
    "epoch": epoch,
    "global_step": global_step,
}
```

实际字段必须和项目训练代码匹配。

---

## 7. 避免写出半个 checkpoint

更稳妥的保存流程：

```text
先写临时文件
→ 确认写入结束
→ 再替换正式文件
```

示例：

```python
from pathlib import Path
import os
import torch

final_path = Path(run_dir) / "checkpoints" / "latest.pt"
tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

torch.save(state, tmp_path)
os.replace(tmp_path, final_path)
```

同一文件系统中的 `os.replace` 通常能提供原子替换，但仍不能代替恢复测试和磁盘监控。

不要同步或读取一个仍在写入的 checkpoint。

---

## 8. `latest` 和 `best` 不是一回事

```text
latest
→ 最近一次可恢复状态

best
→ 根据验证指标选出的最佳状态
```

建议同时保留：

- 周期性 checkpoint；
- `latest`；
- `best`；
- 明确的最佳指标和方向。

不要只保留一个持续覆盖的文件。它一旦损坏，就没有回退点。

---

## 9. 恢复训练前先做最小验证

先检查：

```bash
ls -lh "$CHECKPOINT_PATH"
file "$CHECKPOINT_PATH"
df -h "$HOME/runs"
```

再运行项目支持的最小恢复任务，例如：

```bash
python train.py \
  --resume "$CHECKPOINT_PATH" \
  --max-steps 2 \
  --run-dir "$NEW_RUN_DIR"
```

确认：

- 文件能成功加载；
- 模型结构兼容；
- 优化器状态恢复；
- epoch 或 step 正确延续；
- 数据路径仍存在；
- 新日志没有覆盖旧实验；
- 恢复后配置符合预期。

恢复训练建议创建新的运行目录，并保存：

```text
resumed-from.txt
```

不要无说明地继续向旧目录追加日志。

---

## 10. 对重要 checkpoint 生成校验值

Ubuntu：

```bash
sha256sum checkpoint.pt > checkpoint.pt.sha256
```

Mac：

```bash
shasum -a 256 checkpoint.pt > checkpoint.pt.sha256
```

校验值可以发现传输错误或内容变化，但不能证明 checkpoint 本身安全。不要加载来源不可信的模型文件；某些序列化格式在加载时存在执行风险。

---

## 11. 磁盘空间和保留策略

训练前：

```bash
df -h "$HOME/runs"
du -sh "$HOME/runs/my-project"
```

查看大目录：

```bash
du -h "$HOME/runs/my-project" | sort -h | tail -n 20
```

制定明确策略，例如：

- 保留最近若干周期 checkpoint；
- 永久保留 `best`；
- 关键实验保留完整环境和配置；
- 删除前先同步重要结果；
- 不让 AI CLI 自动批量清理未知实验目录。

磁盘写满可能让日志和 checkpoint 同时损坏，所以磁盘监控属于训练流程的一部分。

---

## 12. 同步结果回 Mac

先预演：

```bash
rsync -av --dry-run \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

checkpoint 很大时，可以只拉回：

- 配置；
- 日志；
- 指标；
- 图表；
- 最佳 checkpoint；
- 校验文件。

复杂 include/exclude 规则必须先使用 `--dry-run`。

---

## 13. 一份标准启动脚本

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/projects/my-project"

RUN_NAME="${1:-baseline}"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/my-project/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf '%s\n' "$RUN_DIR" > "$HOME/runs/my-project/latest-run.txt"

git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff --binary HEAD > "$RUN_DIR/code.patch"
git ls-files --others --exclude-standard > "$RUN_DIR/untracked-files.txt"

{
  date -Is
  hostname
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1

python train.py --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/train.log"
```

脚本仍需要根据项目参数修改。不要把项目外路径、秘密值或不可逆清理操作写进通用启动脚本。

继续阅读：

- [tmux 与断线后继续训练](03-tmux与断线续跑.md)
- [项目同步与目录规范](02-项目同步与目录规范.md)
- [Mac 到 Ubuntu GPU 的端到端案例](../Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)
