# 07 Mac 到 Ubuntu GPU 的端到端案例

> 最近核对：2026-07-30  
> 适用环境：Mac 负责日常开发，Ubuntu 24.04 游戏本负责 NVIDIA GPU 训练。局域网使用普通 SSH；异网由 Tailscale 提供可达性后继续使用 OpenSSH。

本案例把前面的工具串成一次任务：改进 checkpoint 保存与恢复逻辑，在 Mac 完成源码修改和 CPU 测试，在 Ubuntu 完成 CUDA 冒烟、短训练与恢复测试，最后拉回证据并独立复核。

为了避免两端互相覆盖，本次固定 **Mac 是源码主副本，Ubuntu 是运行副本**：

```text
Mac:     ~/Projects/my-project/       源码、Git、CPU 测试
Mac:     ~/ML-Runs/my-project/        拉回的运行证据
Ubuntu: ~/projects/my-project/        同步后的运行副本
Ubuntu: ~/datasets/my-dataset/        数据
Ubuntu: ~/models/base-model/          模型与缓存
Ubuntu: ~/runs/my-project/            实验目录
```

虚拟环境、缓存、数据、模型和运行结果不随源码双向同步。Ubuntu 如果产生有价值的源码修改，应通过分支、提交或受控补丁回收，不能反向覆盖 Mac 项目。

## 1. 在 Mac 建立基线并完成最小修改

进入项目，确认 Git、解释器和已有 checkpoint 测试：

```bash
cd ~/Projects/my-project

hostname
pwd
git branch --show-current
git status --short
git rev-parse --short HEAD
python --version
python -c 'import sys; print(sys.executable)'
python -m pytest tests/test_checkpoint.py -q
```

工作区状态清楚后建立分支：

```bash
git switch -c task/improve-checkpoint-resume
```

任选一套 AI CLI 做只读调查：

```text
分析训练配置、checkpoint 保存和恢复流程，不修改文件。
找出训练入口、配置加载、保存/恢复实现、相关测试和旧格式兼容点。
每个结论引用文件或符号，并列出最小修改范围。
```

本次只处理 checkpoint 行为，不顺便重构训练主循环、依赖和配置体系。通用调查与批次 Prompt 见[通用 Prompt 模板库](02-通用Prompt模板库.md)。

第一批补充回归测试，覆盖恢复后 `global_step` 延续、优化器状态恢复、`latest` 不覆盖 `best`，以及旧格式缺少可选字段时的兼容行为。测试应因目标问题失败，而不是导入或环境错误。确认失败准确后，允许修改：

```text
src/training/checkpoint.py
tests/test_checkpoint.py
```

Agent 完成后由人在 Mac 检查实际差异并运行测试：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
python -m pytest tests/test_checkpoint.py -q
python -m pytest -q
```

此时确认的是配置解析、CPU 序列化和单元测试；CUDA、显存和真实中断恢复仍需在 Ubuntu 验证。

## 2. 单向同步源码，并在 Ubuntu 验证运行环境

项目根目录准备 `.rsyncignore`，排除 Git 元数据、虚拟环境、缓存、凭据和运行产物：

```text
.git/
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.env
.env.*
runs/
checkpoints/
*.log
.DS_Store
```

确认远端身份并预演同步：

```bash
ssh gpu-laptop 'hostname && whoami && pwd'

rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

清单正确后正式同步：

```bash
rsync -av \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

对本次关键文件比较摘要：

```bash
shasum -a 256 src/training/checkpoint.py tests/test_checkpoint.py

ssh gpu-laptop \
  'cd ~/projects/my-project && sha256sum src/training/checkpoint.py tests/test_checkpoint.py'
```

摘要一致表示这两个文件按预期到达 Ubuntu。rsync 的方向、排除规则和远端修改回收见[项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)。

登录 Ubuntu，确认目录、解释器和 GPU：

```bash
ssh gpu-laptop
cd ~/projects/my-project

hostname
pwd
git status --short
python --version
python -c 'import sys; print(sys.executable)'
nvidia-smi
```

使用项目解释器执行最小 CUDA 运算：

```bash
python - <<'PY'
import torch

print('torch:', torch.__version__)
print('build_cuda:', torch.version.cuda)
print('available:', torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit('CUDA unavailable')

x = torch.ones((2, 2), device='cuda')
print('device:', x.device)
print('sum:', x.sum().item())
PY
```

随后运行目标测试并检查磁盘：

```bash
python -m pytest tests/test_checkpoint.py -q
df -h "$HOME" "$HOME/runs"
```

解释器、真实 CUDA 运算、目标测试和磁盘空间都正常后，再进入训练验证。某一层失败时回到对应章节定位，不需要同时重装驱动、环境和依赖。

## 3. 在 tmux 中完成短训练和恢复演练

建立会话和独立运行目录：

```bash
tmux new -s checkpoint-resume-test

cd ~/projects/my-project
PROJECT_NAME='my-project'
RUN_NAME='checkpoint-resume_seed42'
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
```

保存代码与环境证据：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff --binary HEAD > "$RUN_DIR/code.patch"
git ls-files --others --exclude-standard \
  > "$RUN_DIR/untracked-files.txt"

{
  date -Is
  hostname
  pwd
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > "$RUN_DIR/environment.txt" 2>&1
```

训练程序应把最终生效且已脱敏的配置写入 `$RUN_DIR/config.yaml`。未跟踪源码不会进入 `code.patch`；它若影响实验，应进入可解释提交或另行制作受控快照。完整运行目录设计见[实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)。

运行少量 step，并保存退出状态：

```bash
set -o pipefail

python train.py \
  --config "$RUN_DIR/config.yaml" \
  --output-dir "$RUN_DIR" \
  --max-steps 20 \
  2>&1 | tee "$RUN_DIR/train.log"

TRAIN_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$TRAIN_STATUS" > "$RUN_DIR/exit-status.txt"
```

检查日志、checkpoint 和退出状态：

```bash
tail -n 80 "$RUN_DIR/train.log"
ls -lh "$RUN_DIR/checkpoints"
cat "$RUN_DIR/exit-status.txt"

sha256sum "$RUN_DIR/checkpoints/latest.pt" \
  > "$RUN_DIR/checkpoints/latest.pt.sha256"
```

恢复测试使用新的运行目录：

```bash
RESUME_ID="$(date +%Y-%m-%d_%H-%M-%S)_resume-test"
RESUME_DIR="$HOME/runs/$PROJECT_NAME/$RESUME_ID"
mkdir -p "$RESUME_DIR/checkpoints" "$RESUME_DIR/artifacts"
printf '%s\n' "$RUN_DIR/checkpoints/latest.pt" \
  > "$RESUME_DIR/resumed-from.txt"

set -o pipefail
python train.py \
  --config "$RUN_DIR/config.yaml" \
  --resume "$RUN_DIR/checkpoints/latest.pt" \
  --output-dir "$RESUME_DIR" \
  --max-steps 2 \
  2>&1 | tee "$RESUME_DIR/train.log"

RESUME_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$RESUME_STATUS" > "$RESUME_DIR/exit-status.txt"
```

确认 checkpoint 能加载，step 从旧值延续，优化器、调度器和 scaler 等状态符合项目设计，新日志没有覆盖旧运行，并且恢复后还能生成新 checkpoint。离开 tmux 使用 `Ctrl + b` 后按小写 `d`；重新连接后运行：

```bash
tmux ls
tmux attach -t checkpoint-resume-test
```

## 4. 拉回轻量证据并区分已验证范围

回到 Mac，预演结果同步：

```bash
mkdir -p ~/ML-Runs/my-project

rsync -av --dry-run \
  --include '*/' \
  --include 'config.yaml' \
  --include 'environment.txt' \
  --include 'git-commit.txt' \
  --include 'git-status.txt' \
  --include 'code.patch' \
  --include 'untracked-files.txt' \
  --include 'train.log' \
  --include 'metrics.jsonl' \
  --include 'exit-status.txt' \
  --include 'resumed-from.txt' \
  --include '*.png' \
  --include '*.csv' \
  --include '*.sha256' \
  --include 'best.pt' \
  --exclude '*' \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

确认清单后去掉 `--dry-run`。不必把每个周期 checkpoint 都复制到 Mac；关键模型、配置、日志和校验文件应有明确位置。

结果说明要区分已经验证和仍未覆盖的场景：

```text
Mac CPU 测试：通过
Ubuntu CUDA 最小运算：通过
短训练：通过，退出状态 0
恢复测试：通过，step 正确延续
未验证：完整数据集长训练和多 GPU
```

## 5. 独立复核后提交源码

使用没有参与实现的新会话，只读检查 Mac 当前 diff、测试结果，以及拉回的 `environment.txt`、日志、退出状态、配置、代码补丁和 checkpoint 校验记录。复核 Prompt 直接引用[复杂任务拆分与独立复核](05-复杂任务拆分与独立复核.md)，无需再复制一套通用模板。

确认问题处理完后，在 Mac 精确暂存并提交：

```bash
cd ~/Projects/my-project
git status --short
git diff --name-status
git diff

git add src/training/checkpoint.py tests/test_checkpoint.py
git diff --cached
git commit -m "fix: preserve checkpoint resume state"
git show --stat --oneline HEAD
```

到这里，源码修改、CPU 测试、传输摘要、Ubuntu 环境、CUDA 运算、短训练、恢复日志和最终提交能够互相对应。是否推送和创建 Pull Request，仍由人根据项目流程决定。

延伸阅读：[项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)、[tmux 与断线续跑](../Part-11-GPU远程开发/03-tmux与断线续跑.md)、[实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)和[复杂任务拆分与独立复核](05-复杂任务拆分与独立复核.md)。
