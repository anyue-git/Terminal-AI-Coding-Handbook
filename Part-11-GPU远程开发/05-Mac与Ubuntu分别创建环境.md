# 05 Mac 与 Ubuntu 为什么必须分别创建环境

> 最近核对：2026-07-29

Mac 上的 `.venv` 不能通过 rsync 复制到 Ubuntu 后继续使用。两台机器的平台不同：

```text
macOS + Apple Silicon + arm64 + MPS
≠
Ubuntu + x86_64 + NVIDIA CUDA
```

虚拟环境不是一个跨平台压缩包。正确做法是共享源码、依赖声明和锁文件，然后在每台机器本地创建兼容环境。

## 1. `.venv` 里有什么

虚拟环境通常包含：

- Python 解释器或解释器链接；
- 写死的绝对路径；
- 平台专用激活脚本；
- macOS 或 Linux 对应 wheel；
- 编译后的动态库；
- CPU 架构相关二进制。

Mac 常见二进制格式是 Mach-O，Ubuntu 是 ELF。即使两边都叫 `.venv`，内部文件也不能互换。

同步时排除：

```text
.venv/
venv/
__pycache__/
*.pyc
```

## 2. 应该共享和不应该共享的内容

应共享：

```text
源码和测试
README
pyproject.toml
uv.lock
.python-version
requirements.txt
environment.yml
配置模板
训练脚本
```

不应直接共享：

```text
.venv/
Conda 环境目录
编译产物
wheel 缓存
模型缓存
系统 CUDA 目录
API Key
SSH 私钥
整个用户配置目录
```

## 3. 建立一个跨平台练习项目

在 Mac：

```bash
mkdir -p ~/Projects/cross-platform-ml/src/cross_platform_ml \
  ~/Projects/cross-platform-ml/tests
cd ~/Projects/cross-platform-ml
```

创建 `pyproject.toml`：

```toml
[project]
name = "cross-platform-ml"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = [
  "numpy>=2",
]

[dependency-groups]
dev = [
  "pytest>=8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

创建模块：

```bash
cat > src/cross_platform_ml/device.py <<'PY'
def describe_device() -> str:
    try:
        import torch
    except ImportError:
        return "torch-not-installed"

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"
PY
```

创建测试：

```bash
cat > tests/test_device.py <<'PY'
from cross_platform_ml.device import describe_device


def test_device_name_is_known():
    assert describe_device() in {
        "cuda",
        "mps",
        "cpu",
        "torch-not-installed",
    }
PY
```

## 4. 推荐路线：使用 uv

在 Mac 项目目录：

```bash
uv python install
uv lock
uv sync --locked
uv run --locked pytest -q
```

生成：

```text
.venv/
uv.lock
```

提交 `uv.lock`，不提交 `.venv`。

在 `.gitignore` 和 `.rsyncignore` 中加入：

```text
.venv/
```

同步到 Ubuntu：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ gpu-laptop:~/projects/cross-platform-ml/
rsync -av \
  --exclude-from='.rsyncignore' \
  ./ gpu-laptop:~/projects/cross-platform-ml/
```

Ubuntu：

```bash
ssh gpu-laptop
cd ~/projects/cross-platform-ml
uv python install
uv sync --locked
uv run --locked pytest -q
```

同一个锁文件可以包含多平台候选，uv 会在每台机器选择兼容的发行包。锁文件相同不代表实际安装的 wheel 字节完全相同。

## 5. PyTorch 为什么需要单独设计

PyTorch 的 CPU、MPS 和 CUDA 构建不完全等价。你需要明确项目策略，而不是在 Ubuntu 临时安装一套 CUDA torch 后就忘记记录。

常见策略有三种。

### 策略 A：核心依赖锁定，PyTorch 按平台说明安装

适合初学和官方安装命令变化较快的项目：

```text
uv sync --locked
→ 安装通用依赖

Mac
→ 按当前官方方式安装适用构建

Ubuntu
→ 按 PyTorch Start Locally 安装当前 CUDA 构建
```

README 必须记录两边命令和核验方式。

### 策略 B：使用平台标记和多个索引

适合能够正确配置 uv/pip 源的项目。需要在两台机器真实测试锁定结果，不应凭空写一份复杂配置。

### 策略 C：容器固定 Ubuntu GPU 环境

Ubuntu 正式训练使用固定镜像；Mac 只安装 CPU 或 MPS 环境做轻量测试。容器仍需要宿主机 NVIDIA 驱动。

## 6. venv + requirements 路线

Mac：

```bash
cd ~/Projects/project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
```

Ubuntu：

```bash
cd ~/projects/project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
```

命令相似，但解析到的二进制包可能不同。不要使用：

```bash
sudo pip install ...
```

也不要让系统 Python 承担项目依赖。

普通 `pip freeze` 记录的是当前平台完整环境，不一定适合作为另一个平台的直接输入。应区分：

```text
项目声明
→ 我需要什么

平台锁定或环境快照
→ 这台机器实际安装了什么
```

## 7. Conda 路线

两台机器都可以运行：

```bash
conda env create -f environment.yml
```

但不要把某台机器包含所有构建号和平台包的完整导出，当成跨平台通用文件。

更稳妥的结构：

```text
environment.yml
→ 高层共享依赖

environment.macos.lock.yml
→ Mac 精确快照

environment.linux.lock.yml
→ Ubuntu 精确快照
```

PyTorch 安装渠道应以当前官方页面为准，不长期照搬旧的 Conda Channel 命令。

## 8. Mac 和 Ubuntu 的职责不同

Mac：

- 编辑和阅读；
- Git；
- 单元测试；
- CPU/MPS 冒烟测试；
- 配置生成；
- AI CLI 规划和修改。

Ubuntu：

- Linux 集成测试；
- CUDA 验证；
- 正式训练；
- GPU 推理；
- 显存和性能测试；
- 长时间任务。

不要要求 Mac 完整模拟 Ubuntu CUDA 环境。Mac 通过只能证明 Mac 这一层通过。

## 9. 平台特定依赖要显式表达

`pyproject.toml` 支持环境标记：

```toml
[project]
dependencies = [
  "numpy>=2",
  "some-macos-package; sys_platform == 'darwin'",
  "some-linux-package; sys_platform == 'linux'",
]
```

不要把 Linux 专用包无条件写给 macOS，也不要把 macOS 工具写进 Ubuntu 正式环境。

GPU 包可能还涉及自定义索引、平台标签和 Python 版本约束。每次修改锁文件后都应在 Mac 与 Ubuntu 分别运行严格同步。

## 10. 两边都做解释器核验

Mac：

```bash
hostname
uname -m
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -c 'import torch; print(torch.__version__); print(torch.backends.mps.is_available())' 2>/dev/null || true
python -m pytest
```

Ubuntu：

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

## 11. 发现环境漂移

环境漂移包括：

- Python 版本不同；
- 临时安装依赖但未更新声明；
- 锁文件未同步；
- 两边分支或提交不同；
- wheel 来源不同；
- Ubuntu 装了错误 torch 构建；
- Shell 调用了系统 Python；
- VS Code 选了旧解释器。

记录脚本：

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

两台机器分别生成后比较，注意不要把包含私人路径或敏感信息的环境文件公开提交。

## 12. 依赖更新流程

不要在 Ubuntu 正式训练前临时执行：

```bash
pip install 某个包
```

然后不记录。推荐：

```text
Mac 或指定维护端修改依赖声明
→ 更新锁文件
→ 运行 Mac 测试
→ 提交依赖变化
→ 同步到 Ubuntu
→ Ubuntu 使用 locked 模式重建或同步
→ 运行 CUDA 冒烟测试
```

使用 uv：

```bash
uv add package-name
uv lock
uv sync --locked
```

Ubuntu：

```bash
uv sync --locked
```

## 13. 环境坏了怎样重建

虚拟环境是可重建产物。确认源码和声明都安全后：

```bash
mv .venv .venv.broken
uv sync --locked
```

验证新环境后再删除旧目录。不要一遇到 import 错误就先删除锁文件或升级全部依赖。

venv 路线：

```bash
mv .venv .venv.broken
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

如果重建仍失败，问题更可能位于依赖声明、Python 版本、软件源或系统开发库，而不是旧环境缓存。

## 14. 最终原则

```text
共享：源码、测试、依赖声明、锁文件和配置模板

分别创建：解释器环境、平台二进制和 GPU 运行环境

分别验证：Mac CPU/MPS 与 Ubuntu CUDA
```

## 继续阅读

- [NVIDIA 驱动、CUDA 与 PyTorch](04-NVIDIA驱动-CUDA与PyTorch.md)
- [项目同步与目录规范](02-项目同步与目录规范.md)
- [VS Code、AI CLI 与 GPU 协作](07-VS-Code-AI-CLI与GPU协作.md)

官方参考：

- [uv：Projects](https://docs.astral.sh/uv/concepts/projects/)
- [Python：venv](https://docs.python.org/3/library/venv.html)
- [PyTorch：Start Locally](https://pytorch.org/get-started/locally/)
