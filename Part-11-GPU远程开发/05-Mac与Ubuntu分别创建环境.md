# 05 Mac 与 Ubuntu 为什么必须分别创建环境

> 最近核对：2026-07-29

Mac 上的 `.venv` 不能通过 rsync 复制到 Ubuntu 后继续使用。两台机器的操作系统、CPU 架构和 GPU 后端不同：

```text
macOS + Apple Silicon + arm64 + CPU/MPS
≠
Ubuntu + x86_64 + NVIDIA CUDA
```

虚拟环境包含解释器或绝对路径、平台专用脚本、wheel、动态库和编译产物；Mac 常见 Mach-O，Ubuntu 使用 ELF。两边可以共享源码、测试和依赖决策，但已经安装好的环境必须各自在本机创建。

## 1. 同步项目声明，不同步环境目录

适合通过 Git 或 rsync 共享的内容包括：

```text
源码与测试
pyproject.toml / uv.lock / .python-version
requirements.txt
environment.yml
配置模板和训练脚本
```

本地生成的 `.venv/`、Conda 环境目录、`__pycache__/`、wheel 缓存、模型缓存和系统 CUDA 目录不进入源码同步；认证目录、API Key 和 SSH 私钥也不属于项目环境。最小排除项：

```text
.venv/
venv/
__pycache__/
*.pyc
```

共享锁文件表示两台机器基于同一依赖决策解析平台适配包，不代表最终安装的二进制字节相同。一个锁文件可以包含平台标记和多个候选构建，实际选择仍由系统、架构和 Python 版本决定。

## 2. 用同一项目文件在两台机器分别同步

以 uv 项目为例，Mac 中进入项目并建立本地环境：

```bash
cd ~/Projects/cross-platform-ml
uv python install
uv lock
uv sync --locked
uv run --locked pytest -q
```

提交 `pyproject.toml`、`uv.lock` 和源码，忽略 `.venv/`。把项目同步到 Ubuntu：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ gpu-laptop:~/projects/cross-platform-ml/

rsync -av \
  --exclude-from='.rsyncignore' \
  ./ gpu-laptop:~/projects/cross-platform-ml/
```

Ubuntu 在自己的项目目录重新创建：

```bash
ssh gpu-laptop
cd ~/projects/cross-platform-ml
uv python install
uv sync --locked
uv run --locked pytest -q
```

这条流程共享的是项目声明、锁文件和测试，两个 `.venv` 始终属于各自平台。uv 的声明、锁定与精确同步细节见[依赖声明、锁定与环境复现](../Part-07-Python环境/03-依赖声明锁定与环境复现.md)。

使用 venv 或 Conda 时原则不变。两台机器分别创建目录并安装同一份高层声明：

```bash
# 在各自机器的项目目录中执行
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
```

Conda 的 `environment.yml` 适合保存高层共享依赖；需要精确平台快照时，可以分别维护：

```text
environment.yml
→ 高层共享依赖

environment.macos.lock.yml
→ Mac 精确快照

environment.linux.lock.yml
→ Ubuntu 精确快照
```

## 3. PyTorch 需要明确平台策略

Mac 的 CPU/MPS 构建与 Ubuntu 的 CUDA 构建不是同一包形态。项目应公开说明两台机器怎样安装和验证 PyTorch，而不是只在 Ubuntu 临时安装一次。

对初学者最清楚的策略是：锁定通用核心依赖，PyTorch 根据当前官方安装选择器按平台安装。Mac 选择 CPU/MPS 适配构建，Ubuntu 根据驱动兼容情况选择 CUDA 构建；README 记录两端命令和验证方式。

更成熟的项目可以通过环境标记、多个索引或包管理器源规则表达差异：

```toml
[project]
dependencies = [
  "numpy>=2",
  "some-macos-package; sys_platform == 'darwin'",
  "some-linux-package; sys_platform == 'linux'",
]
```

复杂配置只有在 Mac 与 Ubuntu 都实际完成 locked 同步后才算可用。另一种方案是把 Ubuntu GPU 环境固定在容器中，Mac 只承担 CPU/MPS 测试；容器仍依赖 Ubuntu 宿主机的 NVIDIA 驱动。

## 4. 两台机器分别验证自己的职责

Mac 常用于编辑、Git、单元测试、CPU/MPS 冒烟和配置生成：

```bash
hostname
uname -m
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -c 'import torch; print(torch.__version__); print(torch.backends.mps.is_available())' 2>/dev/null || true
python -m pytest
```

Ubuntu 负责 Linux 集成、CUDA、显存和正式训练：

```bash
hostname
uname -m
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
nvidia-smi
python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
python -m pytest
```

Mac 测试通过证明通用逻辑在 Mac 环境中成立，无法代替 CUDA 算子和驱动验证。两端出现差异时，比较 Python、解释器路径、包管理器、Git HEAD、锁文件和 torch 构建，而不是先复制另一端的环境目录。

可以分别生成摘要：

```bash
{
  hostname
  uname -m
  pwd
  git rev-parse --short HEAD
  python --version
  python -c 'import sys; print(sys.executable)'
  python -m pip --version
} > environment-summary.txt 2>&1
```

摘要可能包含用户名和绝对路径，公开前检查内容。

## 5. 依赖更新从一个维护端发起

指定一台机器或 CI 负责修改依赖声明和锁文件，再让其他平台按 locked 模式重建。uv 路线例如：

```bash
# 维护端
uv add package-name
uv lock
uv sync --locked

# Ubuntu
uv sync --locked
```

修改后在 Mac 运行通用测试，在 Ubuntu 运行 CUDA 冒烟与项目短任务。训练机上临时安装包却不更新声明，会让下一次重建无法复现当前环境。

虚拟环境本身属于可重建产物。确认源码和依赖文件安全后，环境损坏可以先保留旧目录，再创建新环境：

```bash
mv .venv .venv.broken
uv sync --locked
```

venv 项目则重新创建并从 requirements 安装。新环境验证成功后再清理旧目录；若重建仍失败，应回到 Python 版本、包来源、声明或系统开发库调查。

跨平台工作流最终只需坚持一件事：共享源码、测试、依赖声明、锁文件和配置模板；Mac 与 Ubuntu 分别创建解释器、平台二进制和 GPU 运行环境，并分别验证它们承担的任务。

继续阅读：[依赖声明、锁定与环境复现](../Part-07-Python环境/03-依赖声明锁定与环境复现.md)、[NVIDIA 驱动、CUDA 与 PyTorch](04-NVIDIA驱动-CUDA与PyTorch.md)、[项目同步与目录规范](02-项目同步与目录规范.md)和[VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)。

官方参考：

- [uv：Projects](https://docs.astral.sh/uv/concepts/projects/)
- [Python：venv](https://docs.python.org/3/library/venv.html)
- [PyTorch：Start Locally](https://pytorch.org/get-started/locally/)