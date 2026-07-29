# 07 Mac 到 Ubuntu GPU 的端到端案例

> 最近核对：2026-07-30
>
> 适用环境：Mac 负责日常开发，Ubuntu 24.04 游戏本负责 NVIDIA GPU 训练。局域网使用普通 SSH，异网使用 Tailscale 提供可达性后继续使用 OpenSSH。

本章把前面的 Git、SSH、Python 环境、AI CLI、rsync、tmux、GPU、日志和 checkpoint 串成一次完整任务。

案例目标：

> 改进项目的 checkpoint 保存与恢复逻辑，在 Mac 上完成源码修改和 CPU 测试，在 Ubuntu GPU 节点完成最小 CUDA 验证、短训练、中断恢复与结果回传，最后使用另一个 Agent 独立复核。

## 1. 先看整条路线

```text
Mac 建立基线和任务分支
→ 主 Agent 只读调查
→ 分批修改和 Mac 测试
→ 人工检查 diff
→ rsync 单向同步源码
→ Ubuntu 验证环境和 GPU
→ tmux 中建立独立运行目录
→ 保存代码、配置和环境证据
→ 短训练并生成 checkpoint
→ 模拟中断与恢复
→ 拉回日志、指标和结果
→ 独立 Agent 只读复核
→ 人工暂存、提交和推送
```

本案例规定：

```text
Mac = 源码主副本
Ubuntu = 运行副本
```

Ubuntu 如果临时修改源码，必须通过 Git 分支、提交或补丁回收，不反向 rsync 整个项目覆盖 Mac。

## 2. 目录约定

Mac：

```text
~/Projects/my-project/
→ 源码

~/ML-Runs/my-project/
→ 拉回的实验结果
```

Ubuntu：

```text
~/projects/my-project/
→ 运行副本

~/datasets/my-dataset/
→ 数据

~/models/base-model/
→ 权重

~/runs/my-project/
→ 配置、日志、指标和 checkpoint
```

`.venv`、Conda 环境、缓存、数据集、模型和运行结果不在两台机器之间作为源码同步。

## 3. Mac：建立现实基线

在 **Mac 项目根目录**：

```bash
cd ~/Projects/my-project

hostname
whoami
pwd
git branch --show-current
git status --short
git rev-parse --short HEAD
python --version
python -c 'import sys; print(sys.executable)'
```

运行现有测试：

```bash
python -m pytest tests/test_checkpoint.py -q
```

记录：

```text
当前 HEAD
工作区状态
Python 路径
基线测试结果
当前已知限制
```

工作区不干净时，先判断已有修改属于谁。不要让 Agent 在未知中间状态上继续叠加。

## 4. Mac：创建任务分支

```bash
git switch -c task/improve-checkpoint-resume

git branch --show-current
git status --short
```

任务分支只管理源码变化，不管理 Ubuntu 数据、模型、运行目录或系统配置。

## 5. Mac：让主 Agent 只读调查

任选一个主力工具，从项目根目录启动。第一轮 Prompt：

```text
目标：分析训练配置、checkpoint 保存和恢复流程。

当前阶段只读。不要修改文件、安装依赖、访问外部服务或运行训练。

请找出：
1. 训练入口；
2. 配置加载位置；
3. checkpoint 保存逻辑；
4. 恢复逻辑；
5. 模型、优化器、调度器、scaler、step 和随机状态的保存情况；
6. 相关测试；
7. 可能需要修改的文件；
8. 兼容旧 checkpoint 的风险。

每个结论给出文件路径和符号，并区分事实、推测和未知。
```

人工核对它是否找对入口，是否把 `runs/`、缓存或数据误认为源码。

## 6. Mac：制定批次计划

要求计划不超过三批：

```text
批次 1：补充失败测试
批次 2：最小修改保存与恢复逻辑
批次 3：更新示例配置或文档
```

每批列出：

- 允许修改文件；
- 测试命令；
- 进入条件；
- 退出条件；
- 兼容风险；
- 未验证部分。

## 7. Mac：第一批只补回归测试

Prompt 示例：

```text
这次只修改 tests/test_checkpoint.py。

增加最小测试，验证 checkpoint 恢复后：
- global_step 正确延续；
- 优化器状态可恢复；
- latest 路径不会覆盖 best；
- 旧格式缺少可选字段时有明确兼容行为。

不要修改生产代码。
运行目标测试并报告命令、退出状态和失败原因。
```

确认测试确实因为目标行为失败，而不是环境或导入错误。

## 8. Mac：第二批做最小实现

Prompt：

```text
现在只允许修改：
- src/training/checkpoint.py
- tests/test_checkpoint.py

只修复已经由回归测试覆盖的保存与恢复行为。
不要修改训练主循环、依赖、CI 或无关配置。
不要执行 git add、commit 或 push。

完成后运行：
1. 目标测试；
2. tests/test_checkpoint.py；
3. 项目相关静态检查。

汇报修改、命令、退出状态、测试数量、未验证部分和风险。
```

## 9. Mac：人工检查真实 diff

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

重点检查：

- 是否只修改允许文件；
- 是否改变 checkpoint 格式；
- 是否保存必要训练状态；
- 恢复时是否覆盖新运行目录；
- 是否用削弱测试换取通过；
- 是否加入真实路径或秘密；
- 是否生成大文件。

运行 Mac 可以完成的测试：

```bash
python -m pytest tests/test_checkpoint.py -q
python -m pytest -q
```

记录边界：

```text
Mac 已验证：
- 配置解析
- CPU 单元测试
- checkpoint 序列化逻辑

Mac 未验证：
- CUDA 执行
- GPU 显存
- 长训练
- 实际中断恢复
```

## 10. Mac：准备同步排除规则

项目根目录 `.rsyncignore`：

```text
.git/
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
.env
.env.*
runs/
checkpoints/
*.log
.DS_Store
```

确认 SSH：

```bash
ssh gpu-laptop 'hostname && whoami && pwd'
```

## 11. Mac：预演并同步源码

先 dry run：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

确认：

- 源目录正确；
- 目标目录正确；
- 未同步 `.git`、虚拟环境、凭据和运行结果；
- 没有大量意外文件；
- 没有使用 `--delete`。

正式同步：

```bash
rsync -av \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

同步后验证关键文件摘要：

```bash
shasum -a 256 src/training/checkpoint.py tests/test_checkpoint.py

ssh gpu-laptop \
  'cd ~/projects/my-project && sha256sum src/training/checkpoint.py tests/test_checkpoint.py'
```

两端摘要应一致。

## 12. Ubuntu：确认远程运行环境

登录：

```bash
ssh gpu-laptop
cd ~/projects/my-project
```

确认：

```bash
hostname
whoami
pwd
git status --short
python --version
python -c 'import sys; print(sys.executable)'
nvidia-smi
```

如果 Ubuntu 运行副本保留自己的 `.git`，rsync 已排除 `.git`，此时 `git status` 会把同步代码显示为本地修改，这是正常的运行副本状态。要避免在这里提交与 Mac 相冲突的历史。

验证 PyTorch：

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

运行相关测试：

```bash
python -m pytest tests/test_checkpoint.py -q
```

检查磁盘：

```bash
df -h "$HOME" "$HOME/runs"
```

任一步失败都先停，不要直接重装驱动。

## 13. Ubuntu：创建 tmux 会话和运行目录

```bash
tmux new -s checkpoint-resume-test
```

在 **tmux 内**：

```bash
cd ~/projects/my-project

PROJECT_NAME='my-project'
RUN_NAME='checkpoint-resume_seed42'
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)_${RUN_NAME}"
RUN_DIR="$HOME/runs/$PROJECT_NAME/$RUN_ID"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
printf '%s\n' "$RUN_DIR" \
  > "$HOME/runs/$PROJECT_NAME/latest-run.txt"
```

## 14. Ubuntu：保存代码状态，正确覆盖暂存与未跟踪范围

保存基线提交和状态：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
```

保存相对 `HEAD` 的已跟踪文件差异，包括已暂存和未暂存：

```bash
git diff --binary HEAD > "$RUN_DIR/code.patch"
```

保存未跟踪文件路径：

```bash
git ls-files --others --exclude-standard \
  > "$RUN_DIR/untracked-files.txt"
```

区别：

```text
git diff
→ 未暂存的已跟踪修改

git diff --cached
→ 已暂存修改

git diff HEAD
→ 已暂存 + 未暂存的已跟踪修改

未跟踪文件
→ 不会进入上述 diff
```

因此本案例使用 `git diff --binary HEAD`，并另外记录未跟踪文件名。未跟踪文件内容仍不会自动保存；真正影响实验的源码应提交，或在排除秘密和数据后另行制作受控快照。

## 15. Ubuntu：保存环境与实际配置

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

不要保存完整环境变量。

训练程序应把最终解析后的配置写入：

```text
$RUN_DIR/config.yaml
```

而不是只复制默认配置。写入前删除 Token、Cookie、数据库密码和私人路径。

保存脱敏命令：

```bash
cat > "$RUN_DIR/command.txt" <<'EOF'
python train.py --config RUN_DIR/config.yaml --output-dir RUN_DIR
EOF
```

## 16. Ubuntu：启动短训练

本案例先跑短任务，不直接启动完整训练：

```bash
set -o pipefail

python train.py \
  --config "$RUN_DIR/config.yaml" \
  --output-dir "$RUN_DIR" \
  --max-steps 20 \
  2>&1 | tee "$RUN_DIR/train.log"

TRAIN_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$TRAIN_STATUS" > "$RUN_DIR/exit-status.txt"
exit "$TRAIN_STATUS"
```

实际参数按项目修改。

训练应至少产生：

```text
train.log
metrics.jsonl
checkpoints/latest.pt
```

检查：

```bash
tail -n 80 "$RUN_DIR/train.log"
ls -lh "$RUN_DIR/checkpoints"
cat "$RUN_DIR/exit-status.txt"
```

## 17. Ubuntu：测试断点恢复

先对 checkpoint 生成校验值：

```bash
sha256sum "$RUN_DIR/checkpoints/latest.pt" \
  > "$RUN_DIR/checkpoints/latest.pt.sha256"
```

创建新的恢复运行目录：

```bash
RESUME_ID="$(date +%Y-%m-%d_%H-%M-%S)_resume-test"
RESUME_DIR="$HOME/runs/$PROJECT_NAME/$RESUME_ID"
mkdir -p "$RESUME_DIR/checkpoints" "$RESUME_DIR/artifacts"
printf '%s\n' "$RUN_DIR/checkpoints/latest.pt" \
  > "$RESUME_DIR/resumed-from.txt"
```

运行最小恢复：

```bash
set -o pipefail

python train.py \
  --config "$RUN_DIR/config.yaml" \
  --resume "$RUN_DIR/checkpoints/latest.pt" \
  --output-dir "$RESUME_DIR" \
  --max-steps 2 \
  2>&1 | tee "$RESUME_DIR/train.log"

RESUME_STATUS=${PIPESTATUS[0]}
printf '%s\n' "$RESUME_STATUS" \
  > "$RESUME_DIR/exit-status.txt"
exit "$RESUME_STATUS"
```

确认：

- checkpoint 能加载；
- step 从旧值延续；
- 优化器等状态符合设计；
- 新日志没有覆盖旧运行；
- 恢复配置和数据路径正确；
- 新 checkpoint 能继续保存。

## 18. Ubuntu：正确脱离和恢复 tmux

脱离：

```text
Ctrl + b，松开，再按小写 d
```

退出 SSH 后重新连接：

```bash
ssh gpu-laptop
tmux ls
tmux attach -t checkpoint-resume-test
```

`tmux` 只保护仍在运行的进程。关机、程序崩溃或 OOM 后需要 checkpoint 恢复。

## 19. Mac：拉回实验结果

在 Mac 创建目录：

```bash
mkdir -p ~/ML-Runs/my-project
```

先预演，只拉回配置、日志、指标、图表、校验文件和最佳 checkpoint：

```bash
rsync -av --dry-run \
  --include '*/' \
  --include 'config.yaml' \
  --include 'command.txt' \
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

确认后去掉 `--dry-run`。

大 checkpoint 不必全部拉回。关键 checkpoint 应保留校验值和明确存储位置。

## 20. Mac：检查结果而不是只看训练最后一行

```bash
find ~/ML-Runs/my-project -type f -print
```

检查：

- 训练退出状态；
- 恢复退出状态；
- 日志中的 step；
- metrics 是否连续；
- 配置是否脱敏；
- 代码 patch 是否对应 Mac 当前 diff；
- 未跟踪文件是否影响复现；
- checkpoint 校验值。

可以写一个简短结论：

```text
Mac CPU 测试：通过
Ubuntu CUDA 最小运算：通过
短训练：通过，退出状态 0
恢复测试：通过，step 正确延续
未验证：完整数据集长训练和多 GPU
```

## 21. 使用另一个 Agent 独立复核

复核者只读，不修改：

```text
你没有参与实现，只负责审查。

原始目标：改进 checkpoint 保存与恢复，并在 Ubuntu GPU 上验证。

请检查：
1. Mac 当前 Git diff；
2. tests/test_checkpoint.py 结果；
3. Ubuntu environment.txt；
4. 短训练和恢复日志；
5. exit-status.txt；
6. config.yaml；
7. git-commit.txt、code.patch 和 untracked-files.txt；
8. checkpoint 校验记录。

判断：
- 是否满足目标；
- 是否存在兼容、状态遗漏或覆盖风险；
- 测试和短训练是否足以支持结论；
- 哪些内容仍无法验证。

分类为已确认问题、可能问题、无法验证和可选改进。
不要修改文件。
```

复核 Agent 可以是另一个品牌，也可以是同一工具的新会话。关键是不要继承实施者的自我总结。

## 22. 人工处理复核意见

将意见分成：

```text
必须修复
需要确认
可选改进
误报
```

必须修复项重新进入：

```text
复现
→ 最小修改
→ Mac 测试
→ rsync
→ Ubuntu 最小验证
→ 更新证据
```

不要因为复核报告很长，就要求主 Agent 一次“全部优化”。

## 23. Mac：最终暂存和提交

最终检查：

```bash
cd ~/Projects/my-project
git status --short
git diff --name-status
git diff --stat
git diff
```

精确暂存：

```bash
git add src/training/checkpoint.py tests/test_checkpoint.py
```

检查暂存区：

```bash
git diff --cached --name-status
git diff --cached
```

提交：

```bash
git commit -m "fix: preserve checkpoint resume state"
```

提交后：

```bash
git status
git show --stat --oneline HEAD
```

是否推送和创建 PR 由人决定。

## 24. 本案例的最终证据链

```text
原始需求
→ checkpoint 保存与恢复

Mac 基线
→ 分支、HEAD、原测试

代码变化
→ Git diff

Mac 验证
→ CPU 单元测试

同步证据
→ 两端文件摘要

Ubuntu 环境
→ Python、PyTorch、CUDA、GPU

训练证据
→ 配置、日志、指标、退出状态

代码快照
→ commit + git diff HEAD + 未跟踪文件清单

恢复证据
→ resumed-from + 恢复日志 + 新运行目录

独立复核
→ 问题分类与未验证范围

最终提交
→ 人工确认后的源码版本
```

当这些证据能够互相对应时，Mac 与 Ubuntu 才真正组成了一套可复核的开发和训练流程，而不是两台通过 SSH 偶尔传文件的电脑。

## 延伸阅读

- [项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [tmux 与断线续跑](../Part-11-GPU远程开发/03-tmux与断线续跑.md)
- [实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)
- [复杂任务拆分与独立复核](05-复杂任务拆分与独立复核.md)
