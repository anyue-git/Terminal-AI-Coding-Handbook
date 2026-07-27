# 05 Mac 与 Ubuntu 为什么必须分别创建环境

Mac 上的 `.venv` 不能直接同步到 Ubuntu 后继续使用，因为两台机器的平台不同：

```text
macOS + Apple Silicon + MPS
≠
Ubuntu + x86_64 + NVIDIA CUDA
```

正确做法是共享源码、依赖声明和锁文件，然后在每台机器上分别创建兼容环境。

---

## 1. 虚拟环境不是跨平台压缩包

`.venv` 里通常包含：

- 解释器或解释器链接；
- 绝对路径；
- 激活脚本；
- 平台相关 wheel；
- 编译后的动态库；
- 架构相关二进制。

Mac 常见的是 arm64 和 Mach-O，Ubuntu 游戏本通常是 x86_64 和 ELF。即使目录名相同，内部文件也不能直接互换。

因此同步时应排除：

```text
.venv/
venv/
__pycache__/
*.pyc
```

---

## 2. 应该共享什么

应共享：

- 源码与测试；
- README；
- `pyproject.toml`；
- `uv.lock`；
- `.python-version`；
- `requirements.txt`；
- `environment.yml`；
- 配置模板和训练脚本。

不应共享：

- `.venv/`；
- Conda 环境目录；
- 编译产物；
- 平台 wheel 缓存；
- 模型缓存；
- API Key；
- SSH 私钥；
- 整个用户配置目录。

---

## 3. 推荐路线一：uv

项目结构：

```text
project/
├── .python-version
├── pyproject.toml
├── uv.lock
├── src/
├── tests/
└── .venv/      每台机器本地生成
```

Mac：

```bash
cd ~/Projects/project
uv python install
uv sync --locked
uv run --locked pytest
```

Ubuntu：

```bash
cd ~/projects/project
uv python install
uv sync --locked
uv run --locked pytest
```

同一个锁文件可以描述多平台候选，但两台机器会安装各自兼容的二进制包。锁文件相同，不等于实际 wheel 完全相同。

GPU 项目还要明确 PyTorch 的安装来源。不能只在 Ubuntu 手工装一套 CUDA 版 torch，却不在 README 或项目配置中记录。

---

## 4. 推荐路线二：venv + requirements

Mac：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ubuntu：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

命令相似，但实际下载内容会根据操作系统、架构和 Python 版本变化。

如果 Ubuntu 需要 CUDA 版 PyTorch，应使用 PyTorch 当前官方安装选择器，并在项目文档中记录安装方式。

不要使用：

```bash
sudo pip install ...
```

也不要用系统 Python 承担项目依赖。

---

## 5. 推荐路线三：Conda

Conda 可以分别创建环境：

```bash
conda env create -f environment.yml
```

但不要把某台机器完整导出的所有构建号，当作跨平台通用文件。

更适合共享的是高层依赖声明；需要精确快照时，在 macOS 和 Linux 分别保存各自导出。

PyTorch 新版本的安装渠道会变化。Conda 可以负责 Python 环境，torch 则按 PyTorch 官方当前建议安装，不要长期照搬旧的 `-c pytorch` 命令。

---

## 6. Mac 与 Ubuntu 的职责不同

Mac：

- 日常编辑；
- Git；
- 文档；
- 单元测试；
- CPU 或 MPS 冒烟测试；
- 配置生成；
- AI CLI 规划和修改。

Ubuntu：

- CUDA 验证；
- 正式训练；
- 大模型推理；
- GPU 容器；
- 显存和性能测试；
- 长时间任务。

不要要求 Mac 完整模拟 Ubuntu CUDA 环境。

---

## 7. 平台特定依赖要显式表达

`pyproject.toml` 可以使用环境标记：

```toml
[project]
dependencies = [
  "numpy>=2",
  "some-macos-package; sys_platform == 'darwin'",
  "some-linux-package; sys_platform == 'linux'",
]
```

GPU wheel 还可能涉及自定义索引。真实配置应依据当前 PyTorch、uv 或 pip 官方能力，并通过两台机器的实际安装测试验证。

不要把平台专用包无条件写进所有环境。

---

## 8. rsync 必须排除环境目录

`.rsyncignore` 示例：

```text
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
runs/
checkpoints/
.env
```

预演：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ~/Projects/project/ \
  gpu-laptop:~/projects/project/
```

确认后再正式执行。

---

## 9. 两台机器分别验证

Mac：

```bash
python --version
python -c 'import sys; print(sys.executable)'
python -c 'import torch; print(torch.__version__); print(torch.backends.mps.is_available())'
python -m pytest
```

Ubuntu：

```bash
python --version
python -c 'import sys; print(sys.executable)'
nvidia-smi
python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
python -m pytest
```

Mac 测试通过，只能证明 Mac 环境通过；Ubuntu CUDA 仍需单独验证。

---

## 10. 环境漂移怎么发现

环境漂移包括：

- Python 版本不同；
- 临时安装的依赖没有写入声明；
- 锁文件未同步；
- 两台机器使用不同分支；
- wheel 来源不同；
- Ubuntu 装了另一套 torch；
- Shell 实际调用了错误解释器。

排查时先记录：

```bash
hostname
pwd
git rev-parse --short HEAD
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

继续阅读：

- [NVIDIA 驱动、CUDA 与 PyTorch](04-NVIDIA驱动-CUDA与PyTorch.md)
- [项目同步与目录规范](02-项目同步与目录规范.md)

官方参考：

- [uv：Projects](https://docs.astral.sh/uv/concepts/projects/)
- [Python：venv](https://docs.python.org/3/library/venv.html)
- [PyTorch：Start Locally](https://pytorch.org/get-started/locally/)
