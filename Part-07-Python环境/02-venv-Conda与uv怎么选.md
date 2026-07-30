# 02 venv、Conda 与 uv 怎么选

Python 环境工具很多，但它们解决的层次并不相同。`venv` 使用已有 Python 创建隔离环境；Conda 可以同时管理 Python、原生库和环境；uv 则把 Python 版本、项目依赖、锁文件与项目环境整合为一套工作流。选择时不应只比较速度或流行度，而要先看仓库已经采用什么、是否依赖复杂原生库、团队如何复现，以及 Mac 与 Ubuntu 是否需要不同构建。

> 技术核对：2026-07。uv 与 Conda 仍在快速更新，具体命令和默认行为应同时参考仓库说明、本机 `--help` 与官方文档。

## 1. 先把环境管理拆成五个问题

一个项目需要回答：使用哪个 Python 版本，环境隔离在哪里，直接依赖怎样声明，完整解析结果怎样锁定，以及原生库和平台差异由谁处理。

| 工具 | Python 版本 | 隔离环境 | Python 依赖 | 原生库 | 项目锁定 |
|---|---|---|---|---|---|
| `venv` | 使用已有解释器 | 是 | 配合 pip | 不负责 | 需要其他方案 |
| Conda | 可以管理 | 是 | 可以管理 | 可以管理 | 环境文件或受支持的锁文件 |
| uv | 可以管理 | 是 | 可以管理 | 主要面向 Python 生态 | `uv.lock` |

这张表只帮助识别职责，不替代项目约定。已有仓库中的 `uv.lock`、`environment.yml`、Conda 锁文件、requirements 或文档，通常比个人偏好更重要。

## 2. venv：最透明地理解解释器、环境和 pip

建立独立目录，确认基础解释器后创建环境：

```bash
mkdir -p ~/terminal-practice/venv-demo
cd ~/terminal-practice/venv-demo
python3 --version
python3 -c 'import sys; print(sys.executable)'
python3 -m venv .venv
source .venv/bin/activate
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

安装依赖并运行一个最小程序：

```bash
python -m pip install requests

cat > app.py <<'PY'
import requests

print("requests:", requests.__version__)
PY

python app.py
deactivate
```

venv 的优点是层次清楚：基础 Python 由你选择，项目环境位于 `.venv`，依赖由环境内 Python 的 pip 安装。它适合教学、小型项目、主要依赖来自 PyPI 的普通应用，以及已经使用 requirements 的仓库。

它不负责下载 Python 本身，也不管理 CUDA、数据库和复杂系统库；标准库没有内置项目锁文件，依赖声明和严格复现需要配合其他工具。将项目交给另一台机器时，不复制 `.venv`，而是共享源码、依赖声明和创建命令：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Mac arm64 与 Ubuntu x86_64 即使依赖版本相同，也可能安装不同 wheel。

## 3. Conda：环境中还包含 Python 之外的依赖

Conda 可以选择 Python 版本并管理原生库。典型流程：

```bash
conda create -n conda-demo python=3.12 pip
conda activate conda-demo
python -c 'import sys; print(sys.executable)'
conda info --envs
conda list
conda install requests
```

只有 Conda 生态中没有目标包时，才在已激活环境中补充：

```bash
python -m pip install PACKAGE
```

不要无计划地在同一环境中反复交替多个 Channel、Conda 与 pip。较稳妥的顺序是先由 Conda 安装它能管理的原生和 Python 包，最后补必要的 pip 包，并记录来源。Conda 常适合科学计算、复杂 C/C++/Fortran 依赖、需要 Python 之外工具的项目，以及已有成熟 Channel 和环境规范的团队。

不要把 `base` 当作所有项目共用环境。长期堆积依赖后，升级会影响多个项目，也难以解释包的来源。项目专用环境更容易复现和删除。

传统项目常用 `environment.yml`。较新的 Conda 版本还提供原生多平台锁文件能力；源文档核对时以 26.5 及以后版本为界，但命令、格式和创建行为应以当前版本帮助为准：

```bash
conda --version
conda export --name my-env --file conda-lock.yaml
```

不能因为新版支持锁文件，就假设旧仓库中的 `environment.yml` 已自动成为精确锁定，也不能未经讨论提高项目最低 Conda 版本。

## 4. uv：把项目声明、锁定、环境和运行串在一起

在独立目录中：

```bash
mkdir -p ~/terminal-practice/uv-demo
cd ~/terminal-practice/uv-demo
uv --version
uv init
find . -print
cat pyproject.toml
```

添加依赖会更新项目声明、锁文件和环境：

```bash
uv add requests
uv lock --check
uv run python -c 'import sys, requests; print(sys.executable); print(requests.__version__)'
```

uv 项目通常包含 `pyproject.toml`、`uv.lock` 和本机 `.venv/`。前两者进入 Git，`.venv` 不进入版本控制，也不跨平台同步。

显式同步使用：

```bash
uv sync
```

当前 uv 的精确同步会移除锁文件中没有声明的额外包；希望保留额外包时才评估 `--inexact`。正式复现和 CI 应明确要求锁文件不被隐式更新：

```bash
uv sync --locked
uv lock --check
```

`uv run` 会确保项目所需环境可用，但其隐式同步与显式 `uv sync` 的语义不应混为一谈。已有锁文件不会因为上游发布新版本自动变化；升级应作为独立任务：

```bash
uv lock --upgrade
uv lock --upgrade-package requests
```

升级仍受 `pyproject.toml` 版本范围限制。不要在修复普通业务问题时顺手升级全部依赖和锁文件。

## 5. 根据项目和依赖选择，而不是混用三套环境

学习 Python 环境原理时，`venv + python -m pip` 最透明；新建普通长期 Python 项目时，可以考虑 uv 统一 Python、声明、锁定与运行；科学计算和复杂原生依赖项目可以考虑 Conda，尤其当团队已有成熟规范。

已有仓库先识别权威文件：

```text
看到 uv.lock
→ 先按 uv 流程

看到 environment.yml 或 Conda 锁文件
→ 先读项目的 Conda 说明

看到 requirements.txt 与 .venv 约定
→ 按项目指定 Python 创建 venv

同时出现多套文件
→ 先查 README、CI 和维护者说明，确认谁是权威来源
```

不要在同一个项目目录中同时创建并激活 venv、Conda 与 uv 环境，再通过 PATH 碰运气。切换工具属于项目迁移，需要明确源依赖、目标格式、锁文件变化、CI 修改和回滚方式。

## 6. Mac、Ubuntu 与 GPU 项目需要平台意识

环境工具可以共享声明和锁定信息，却不能让 macOS arm64 与 Linux x86_64 使用同一份环境目录或完全相同的二进制。GPU 项目还涉及 Ubuntu 驱动、CUDA 运行时和框架构建。

正确模式是共享源码和环境描述，在每台机器本地创建环境，并分别验证解释器、包来源和设备能力。锁文件若支持多平台，也只是记录各平台解析结果，不代表所有依赖在每个平台都有可用构建。

## 7. 选择前的最小检查

```bash
pwd
python3 -c 'import sys; print(sys.executable)'
ls -la
find . -maxdepth 2 \
  \( -name 'pyproject.toml' -o -name 'uv.lock' \
     -o -name 'requirements*.txt' -o -name 'environment.yml' \
     -o -name 'conda-lock.yaml' \) -print
```

先识别项目现有工具、Python 版本与平台需求，再决定创建环境。让 AI 提方案时，要求它说明为什么选择某套工具、哪些现有文件是权威来源，以及迁移是否会改变锁文件和 CI。

继续阅读：

- [Python 解释器与 pip 定位](01-Python解释器与pip定位.md)
- [依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)
- [Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)
