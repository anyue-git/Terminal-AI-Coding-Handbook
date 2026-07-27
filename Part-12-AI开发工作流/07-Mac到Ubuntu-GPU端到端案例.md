# 07 Mac 到 Ubuntu GPU 的端到端案例

> 适用环境：Mac 负责日常开发，Ubuntu 24.04 游戏本负责 NVIDIA GPU 训练。
>
> 这不是一组需要一次背完的命令。先顺着流程走一遍，之后把它当作检查清单使用即可。

Mac 适合写代码、看 diff 和整理结果；Ubuntu 游戏本有 NVIDIA GPU，适合跑训练。让两台机器各做自己擅长的事，通常比强迫 Mac 硬扛 CUDA 省心得多。

本章使用一个虚构任务作为例子：改进项目的 checkpoint 保存与恢复，然后在 Ubuntu 上做一次短训练验证。

---

## 1. 先看懂整条路线

这次会经历五个步骤：

1. 在 Mac 上建立 Git 分支，让 AI CLI 修改代码；
2. 人工检查 diff，并先运行 Mac 能完成的测试；
3. 使用 rsync 把代码同步到 Ubuntu；
4. 在 tmux 中运行训练，保存日志与 checkpoint；
5. 把结果拉回 Mac，再由另一个 Agent 做只读复核。

Mac 是源码的主要编辑端，Ubuntu 是运行端。尽量不要今天在 Mac 改一半、明天又在 Ubuntu 手改另一半，否则两台机器很快会开始互相猜谜。

示例目录如下。

### Mac

```text
~/Projects/my-project/
    项目源码

~/ML-Runs/my-project/
    从 Ubuntu 拉回的实验结果
```

### Ubuntu

```text
~/projects/my-project/
    运行用源码

~/datasets/my-dataset/
    数据集

~/models/base-model/
    基础模型或预训练权重

~/runs/my-project/
    配置、日志、指标、图表和 checkpoint
```

源码、数据集、模型和实验输出最好分开放。`.venv`、Conda 环境和其他平台相关文件也不要在 Mac 与 Ubuntu 之间直接复制；两台机器应分别创建环境。

---

## 2. 先在 Mac 上建立一个干净起点

进入项目：

```bash
cd ~/Projects/my-project
```

确认自己在哪台机器、哪个目录和哪个 Git 分支：

```bash
hostname
whoami
pwd
git status
git branch --show-current
```

如果 `git status` 已经显示未提交修改，先弄清这些修改是谁留下的、属于哪个任务。AI 不会自动知道哪些代码是你昨晚改的；它只会看到工作区里“有东西变了”。

为本次任务创建分支：

```bash
git switch -c task/improve-checkpoint-resume
```

分支名写任务内容，不写工具名称。`task/improve-checkpoint-resume` 比 `claude-test-2` 更有用，因为三个月后你大概只关心改了什么，不关心当时是哪位电子同事值班。

---

## 3. 让 AI 先调查，再动手

任选一个主力工具：Claude Code、Codex CLI 或 Grok CLI。启动前再看一次：

```bash
pwd
git status
git branch --show-current
```

第一轮只让它阅读项目：

```text
目标：分析训练配置和 checkpoint 恢复流程。

当前阶段只读，不要修改文件、安装依赖、访问外部服务或运行训练。

请找出：
1. 训练入口；
2. 配置加载位置；
3. checkpoint 保存和恢复代码；
4. 相关测试；
5. 可能需要修改的文件。

每个结论都给出文件路径，并区分已确认事实与推测。
```

看完调查结果，先判断它是否找对了入口，有没有把缓存、数据集或输出目录误认成源码。调查方向错误时立即纠正，比等它改完十个文件再返工便宜得多。

确认方案后，再给出明确范围：

```text
现在可以实施，但只允许修改：
- configs/train.yaml
- src/training/checkpoint.py
- tests/test_checkpoint.py

禁止：
- 修改其他文件；
- 执行 git add、commit 或 push；
- 安装或升级依赖；
- 修改 SSH、防火墙、Docker 或系统配置；
- 删除 runs、datasets、models 或 checkpoint；
- 读取项目目录之外的凭据文件。

先补充或更新测试，再修改实现。
完成后汇报修改文件、测试命令、测试结果、未验证部分和风险。
```

这里的文件名只是例子，应替换成真实项目路径。

---

## 4. 在 Mac 上检查 AI 到底改了什么

Agent 说“完成”之后，先别急着庆祝。它的“完成”更像交卷，不等于老师已经批完。

运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

重点检查：

- 是否只修改了允许的文件；
- 是否出现没有解释的删除；
- 是否加入绝对路径、用户名或真实数据路径；
- 是否把 `.env`、Token、私钥或大型文件放进项目；
- 是否通过削弱测试来让结果变绿；
- checkpoint 格式是否仍与旧版本兼容。

运行 Mac 能完成的测试，例如：

```bash
python -m pytest tests/test_checkpoint.py
```

Mac 没有 CUDA 时，可以验证配置解析、CPU 单元测试和静态检查，但不能把 GPU 部分写成“已经通过”。最好明确记录：

```text
Mac 已验证：配置解析、CPU 单元测试
Mac 未验证：CUDA 执行、显存占用、长训练恢复
```

这不是客气话，而是实验边界。

---

## 5. 同步前先排除不该传的东西

在项目根目录准备 `.rsyncignore`：

```text
.git/
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
node_modules/
.env
.env.*
runs/
checkpoints/
*.log
.DS_Store
```

`.gitignore` 决定 Git 忽略什么；`.rsyncignore` 只有在 rsync 命令明确引用它时才生效。两者名字有点像，但并不是失散多年的双胞胎。

假设 SSH Config 中已经配置主机别名 `gpu-laptop`。先确认连到的是预期机器：

```bash
ssh gpu-laptop 'hostname && pwd'
```

然后只做预演：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

查看输出，确认：

- 源目录就是当前项目；
- 目标是 Ubuntu 上的正确目录；
- 没有传输 `.env`、虚拟环境、日志、模型或数据集；
- 没有出现大量意外文件。

确认后去掉 `--dry-run`：

```bash
rsync -av \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop:~/projects/my-project/
```

本例不使用 `--delete`。它会删除目标端存在、源端不存在的文件，尤其容易误伤 Ubuntu 上单独生成的实验结果。以后确实需要时，也必须先 dry run。

---

## 6. 在 Ubuntu 上做一次最小检查

登录 Ubuntu：

```bash
ssh gpu-laptop
```

进入项目：

```bash
cd ~/projects/my-project
```

确认机器、目录、Python 和 GPU：

```bash
hostname
whoami
pwd
git status
which python
python --version
nvidia-smi
```

`nvidia-smi` 正常，只能说明驱动大体能够看到 GPU，不能证明当前 Python 环境里的 PyTorch 一定能用 CUDA。继续检查：

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('Build CUDA:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available())"
```

再做一个很小的 GPU 运算：

```bash
python -c "import torch; x=torch.ones(1, device='cuda'); print(x, x.device)"
```

运行相关测试：

```bash
python -m pytest tests/test_checkpoint.py
```

最后看看磁盘空间：

```bash
df -h "$HOME"
```

其中任何一步失败，都先停在这里排查。不要因为一个 Python 环境找不到 CUDA，就立刻重装驱动。驱动没有惹你时，先别惹驱动。

---

## 7. 在 tmux 中创建实验并启动训练

创建会话：

```bash
tmux new -s checkpoint-test
```

进入项目，并在 **tmux 里面** 定义实验目录：

```bash
cd ~/projects/my-project

RUN_NAME="checkpoint-resume_seed42"
RUN_DIR="$HOME/runs/my-project/$(date +%Y-%m-%d_%H-%M-%S)_$RUN_NAME"
mkdir -p "$RUN_DIR/checkpoints" "$RUN_DIR/artifacts"
```

把最近一次实验路径记下来，之后重新登录时就不需要手动翻目录：

```bash
printf '%s\n' "$RUN_DIR" > "$HOME/runs/my-project/latest-run.txt"
```

记录代码和环境：

```bash
git rev-parse HEAD > "$RUN_DIR/git-commit.txt"
git status --short > "$RUN_DIR/git-status.txt"
git diff > "$RUN_DIR/code.patch"

python --version > "$RUN_DIR/environment.txt"
which python >> "$RUN_DIR/environment.txt"
nvidia-smi >> "$RUN_DIR/environment.txt"

cp configs/train.yaml "$RUN_DIR/config.yaml"
```

`git-commit.txt` 记录基线提交，`code.patch` 记录尚未提交的实际修改。只记提交哈希而不保存 diff，可能会漏掉本次通过 rsync 同步来的改动。

不要把完整环境变量直接写入日志，里面可能混着 API Key、Token 和私有地址。

启动训练前启用 `pipefail`：

```bash
set -o pipefail
```

然后运行训练：

```bash
python train.py \
  --config "$RUN_DIR/config.yaml" \
  --output-dir "$RUN_DIR" \
  2>&1 | tee "$RUN_DIR/train.log"
```

这里的 `train.py` 和参数名只是示例。`tee` 会一边显示输出、一边写日志；`pipefail` 则保证 Python 失败时，整条流水线不会因为 `tee` 正常结束而假装成功。

训练正常启动后，脱离 tmux：

```text
先按 Ctrl + B，松开，再按 D
```

随后可以退出 SSH：

```bash
exit
```

tmux 能保护进程不受 SSH 断线影响，但挡不住关机、断电、程序崩溃、显存不足或磁盘写满。tmux 是雨伞，不是防空洞；真正用于恢复训练的是 checkpoint。

---

## 8. 断开后怎样重新查看训练

重新连接：

```bash
ssh gpu-laptop
```

读取最近一次实验目录：

```bash
RUN_DIR=$(cat "$HOME/runs/my-project/latest-run.txt")
printf '%s\n' "$RUN_DIR"
```

查看 tmux 会话：

```bash
tmux ls
```

重新进入：

```bash
tmux attach -t checkpoint-test
```

只想看日志时，不必进入 tmux：

```bash
tail -f "$RUN_DIR/train.log"
```

按 `Ctrl + C` 只能停止 `tail -f`，不会停止 tmux 里的训练。

同时检查进程、GPU 和磁盘：

```bash
pgrep -af python
nvidia-smi
df -h "$HOME/runs"
```

只有 tmux 会话还在，不代表训练一定健康。它也可能正在报错、卡住或者快乐地把磁盘写满。

---

## 9. 别等正式训练崩了才测试恢复

checkpoint 至少通常需要包含：

- 模型状态；
- 优化器状态；
- 学习率调度器状态；
- epoch 或 global step；
- 混合精度 scaler 状态（如果使用）；
- 恢复所需的随机状态；
- 配置与最佳指标。

`latest` 通常表示最近一次可恢复状态，`best` 表示验证指标最好的一次。二者用途不同，不要只保留 `best` 后才发现它离崩溃前已经隔了三小时。

为恢复测试创建新目录：

```bash
RESUME_DIR="$HOME/runs/my-project/$(date +%Y-%m-%d_%H-%M-%S)_resume-test"
mkdir -p "$RESUME_DIR"
```

检查文件：

```bash
ls -lh "$RUN_DIR/checkpoints"
file "$RUN_DIR/checkpoints/latest.pt"
```

按真实项目接口启动恢复测试，例如：

```bash
set -o pipefail

python train.py \
  --config "$RUN_DIR/config.yaml" \
  --resume "$RUN_DIR/checkpoints/latest.pt" \
  --output-dir "$RESUME_DIR" \
  2>&1 | tee "$RESUME_DIR/train.log"
```

确认它不是“成功读取文件后又从零开始”。至少检查：

- step 或 epoch 是否延续；
- 优化器和调度器状态是否恢复；
- 模型结构是否兼容；
- 新输出是否写入 `RESUME_DIR`；
- 原来的 checkpoint 是否没有被覆盖。

---

## 10. 把结果拉回 Mac

回到 Mac，先预演：

```bash
rsync -av --dry-run \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

确认目标后执行：

```bash
rsync -av \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

checkpoint 很大时，可以只同步配置、日志、指标和图表：

```bash
rsync -av --dry-run \
  --include '*/' \
  --include 'config.yaml' \
  --include 'metrics.json' \
  --include 'metrics.jsonl' \
  --include 'train.log' \
  --include 'environment.txt' \
  --include 'git-commit.txt' \
  --include 'git-status.txt' \
  --include 'code.patch' \
  --include '*.png' \
  --include '*.csv' \
  --exclude '*' \
  gpu-laptop:~/runs/my-project/ \
  ~/ML-Runs/my-project/
```

复杂的 include 和 exclude 规则先 dry run。大型 checkpoint 可以留在 Ubuntu，但实验记录中应写清路径、是否备份，以及以后由谁清理。

每次实验至少保留：

```text
config.yaml
train.log
metrics.json 或 metrics.jsonl
git-commit.txt
git-status.txt
code.patch
environment.txt
关键图表
checkpoint 的位置和备份状态
```

失败实验也值得保留简短说明。它至少能告诉你哪条路已经撞过墙，免得下次换个 Agent 再撞一遍。

---

## 11. 用另一个 Agent 做只读复核

回到 Mac 项目后，启动另一个工具或新的独立会话。不要先把实现者的“自我表扬”发给复核者，只给它原始需求、diff、测试结果和实验记录。

提示模板：

```text
你只负责独立审查，不要修改文件、安装依赖、提交或推送。

原始目标：改进 checkpoint 保存和恢复流程。

请检查：
1. 当前 Git diff；
2. 相关测试；
3. 从 Ubuntu 拉回的实验记录；
4. checkpoint 恢复是否真的延续了训练状态；
5. 是否存在兼容性、路径、安全或覆盖风险。

把结论分为：
- 已确认问题；
- 可能问题；
- 无法验证；
- 建议补充的测试。
```

复核结束后，由人再次查看：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

只暂存确认过的文件：

```bash
git add configs/train.yaml \
  src/training/checkpoint.py \
  tests/test_checkpoint.py
```

检查暂存区：

```bash
git diff --cached --name-status
git diff --cached
```

确认后提交：

```bash
git commit -m "改进 checkpoint 保存与恢复验证"
```

是否 push 或创建 Pull Request，仍由人决定。

---

## 12. 出问题时先查哪里

### rsync 预演出现一大堆陌生文件

先停止同步，检查：

- 当前目录；
- `.rsyncignore`；
- 源路径末尾的 `/`；
- SSH 主机别名；
- 远程目标路径。

### `nvidia-smi` 正常，但 PyTorch 看不到 GPU

检查：

```bash
which python
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

通常先排查是否进入了错误 Python 环境，不要直接重装驱动。

### SSH 突然断开

重新连接后运行：

```bash
tmux ls
pgrep -af python
nvidia-smi
```

### 训练退出

读取最近实验目录并看日志末尾：

```bash
RUN_DIR=$(cat "$HOME/runs/my-project/latest-run.txt")
tail -n 100 "$RUN_DIR/train.log"
df -h "$HOME/runs"
nvidia-smi
```

然后判断能否从 checkpoint 恢复。

### 结果和代码版本对不上

查看：

```text
git-commit.txt
git-status.txt
code.patch
config.yaml
environment.txt
```

仍然无法对应时，不应把这次实验称为可复现结果。

---

## 13. 最后检查一遍

### Mac 修改代码时

```text
[ ] 确认机器、目录和 Git 状态
[ ] 使用独立分支
[ ] 让 Agent 先只读调查
[ ] 限定允许修改的文件
[ ] 检查 diff 并运行本地测试
```

### 同步和训练前

```text
[ ] rsync 先使用 --dry-run
[ ] Ubuntu 上确认 Python 和 CUDA
[ ] 运行最小 GPU 测试
[ ] 检查磁盘空间
[ ] 在 tmux 内创建独立 RUN_DIR
```

### 训练后

```text
[ ] 保存配置、日志、环境和代码 patch
[ ] 实际测试 checkpoint 恢复
[ ] 同步结果前再次 dry run
[ ] 使用另一个 Agent 只读复核
[ ] 人工检查暂存区后再提交
```

这条流程看起来比“把项目扔给 Agent，让它自己跑”多了几步，但每一步都能停、能查、能恢复。真正省时间的地方，通常不是少敲三条命令，而是出问题时知道自己该从哪一步重新开始。

延伸阅读：

- [项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [tmux 与断线后继续训练](../Part-11-GPU远程开发/03-tmux与断线续跑.md)
- [NVIDIA 驱动、CUDA 与 PyTorch](../Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)
- [实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)
- [Claude Code、Codex CLI 与 Grok CLI 对照协作](06-Claude-Code-Codex-Grok对照与协作.md)
