# 02 venv、Conda 与 uv 怎么选

Python 环境工具很多，但它们覆盖的层次不同。`venv` 使用一个已经存在的 Python 创建隔离环境；Conda 可以同时管理 Python、原生库和环境；uv 则把 Python 版本、项目依赖、锁文件和项目环境整合到一套工作流中。选择工具时，不应只比较安装速度，而应先看项目现状、原生依赖、团队规范和复现要求。

本章会用同一个简单项目分别展示三种工作方式。它们是相互独立的示例，不要在同一练习目录中同时创建三套环境并混合使用。

> 技术核对：2026-07。uv 和 Conda 仍在快速更新，命令细节应同时参考本机 `--help` 与官方文档。

## 1. 先把环境问题拆成五层

一个项目通常需要回答：

```text
使用哪个 Python 版本
→ 环境隔离在哪里
→ 直接依赖怎样声明
→ 完整解析结果怎样锁定
→ 原生库和平台差异怎样处理
```

三种工具的入门定位如下：

| 工具 | Python 版本 | 隔离环境 | Python 依赖 | 原生库 | 项目锁定 |
|---|---|---|---|---|---|
| `venv` | 使用已有解释器 | 是 | 配合 pip | 不负责 | 需要其他方案 |
| Conda | 可以管理 | 是 | 可以管理 | 可以管理 | 新版支持原生锁文件，也可使用环境文件 |
| uv | 可以管理 | 是 | 可以管理 | 主要面向 Python 生态 | `uv.lock` |

这张表只是帮助选方向。项目已经采用哪套工具，通常比个人偏好更重要。

## 2. venv：最透明的入门方式

创建练习目录：

```bash
mkdir -p ~/terminal-practice/venv-demo
cd ~/terminal-practice/venv-demo
```

查看将要使用的基础解释器：

```bash
python3 --version
python3 -c 'import sys; print(sys.executable)'
```

创建环境：

```bash
python3 -m venv .venv
```

激活并验证：

```bash
source .venv/bin/activate
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

安装一个依赖：

```bash
python -m pip install requests
```

创建程序：

```bash
cat > app.py <<'PY'
import requests

print("requests:", requests.__version__)
PY
```

运行：

```bash
python app.py
```

退出环境：

```bash
deactivate
```

`venv` 的优点是每一层都很清楚：基础 Python 由你选择，环境位于 `.venv`，依赖通过当前 Python 的 pip 安装。它适合教学、小型项目、主要依赖来自 PyPI 的普通应用，以及已经使用 `requirements.txt` 的仓库。

它的边界也很明确：

- 不负责下载和选择 Python 本身；
- 不管理系统级 C/C++ 库、CUDA 或数据库；
- 标准库没有内置项目锁文件；
- 依赖声明和复现流程需要额外维护。

## 3. venv 项目怎样交给另一台机器

不要复制 `.venv`。提交或同步：

```text
app.py
requirements.txt 或 pyproject.toml
README 中的创建命令
```

在另一台机器重新执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

这会根据另一台机器的平台安装兼容的包。Mac arm64 和 Ubuntu x86_64 环境即使依赖版本相同，实际 wheel 也可能不同。

## 4. Conda：同时管理 Python 与原生依赖

Conda 更像一套跨平台环境与包管理系统。它可以选择 Python 版本，也能安装 Python 之外的原生库。典型创建方式：

```bash
conda create -n conda-demo python=3.12 pip
conda activate conda-demo
```

验证：

```bash
python -c 'import sys; print(sys.executable)'
conda info --envs
conda list
```

安装包时，应先明确来源和 Channel：

```bash
conda install requests
```

如果某个包只能通过 pip 获得，可以在已激活的 Conda 环境中使用：

```bash
python -m pip install PACKAGE
```

但不要无计划地在同一个环境中反复交替使用多个 Channel、Conda 和 pip。较稳妥的顺序通常是先安装 Conda 能管理的包，最后再补必要的 pip 包，并把来源记录到项目环境说明中。

## 5. Conda 适合哪些项目

Conda 常适合：

- 科学计算和数据分析；
- 依赖复杂 C/C++、Fortran 或系统库的项目；
- 需要 Python 以外工具的环境；
- 团队已经有成熟 Conda 流程；
- 某些包在 Conda 生态中更容易获得兼容构建。

不要把 `base` 环境当成所有项目共用环境。`base` 中不断积累依赖后，任何升级都可能影响多个项目，也很难判断某个包究竟为何存在。

查看当前环境：

```bash
conda info --envs
```

创建项目专用环境比长期污染 `base` 更容易维护。

## 6. 新版 Conda 的环境文件与锁文件

传统 Conda 项目常见：

```text
environment.yml
```

它可以记录名称、Channel 和依赖范围，但是否完全精确取决于内容。较新的 Conda 26.5 及以后版本加入了原生多平台锁文件支持，可以记录精确包、版本、构建和 Channel。

先查看版本：

```bash
conda --version
```

若版本支持，官方文档提供的锁文件流程包括导出：

```bash
conda export --name my-env --file conda-lock.yaml
```

锁文件可以用于跳过重新求解并创建一致环境。具体创建命令、支持格式和多平台行为变化较快，应以当前 Conda 文档和 `conda create --help` 为准。

不能因为新版 Conda 支持锁文件，就假设旧仓库中的 `environment.yml` 已自动变成精确锁定。应先确认项目当前采用哪种格式和最低 Conda 版本。

## 7. uv：面向现代 Python 项目的整合流程

uv 可以管理 Python、项目 `.venv`、依赖声明和 `uv.lock`。先确认版本：

```bash
uv --version
```

建立独立练习目录：

```bash
mkdir -p ~/terminal-practice/uv-demo
cd ~/terminal-practice/uv-demo
uv init
```

`uv init` 会建立项目文件。查看：

```bash
find . -print
cat pyproject.toml
```

添加依赖：

```bash
uv add requests
```

这会更新 `pyproject.toml`，同时更新锁文件和项目环境。检查：

```bash
ls -la
uv lock --check
```

运行：

```bash
uv run python -c 'import sys, requests; print(sys.executable); print(requests.__version__)'
```

无需手工激活环境，`uv run` 会使用项目环境。

## 8. uv 的锁定和同步行为

uv 项目常见文件：

```text
pyproject.toml
uv.lock
.venv/
```

其中：

- `pyproject.toml` 记录项目元数据和依赖要求；
- `uv.lock` 记录解析后的锁定结果，应进入 Git；
- `.venv` 是本机环境，不应进入 Git，也不应跨平台同步。

显式同步：

```bash
uv sync
```

当前 uv 中，`uv sync` 默认执行精确同步，会移除锁文件中没有声明的多余包。希望保留额外包时才使用 `--inexact`。这意味着在一个被手工塞入大量临时包的环境中运行 `uv sync`，可能清理这些额外包；执行前应先知道项目环境是否被当作共享实验环境使用。

要求锁文件必须已经与项目声明一致，不允许命令自行更新锁文件：

```bash
uv sync --locked
```

只检查锁文件：

```bash
uv lock --check
```

`uv run` 通常会确保必要依赖存在，但默认同步语义与显式 `uv sync` 不完全相同。涉及 CI 和严格复现时，应在流程中明确使用 `uv sync --locked`，而不是依赖隐式行为。

## 9. uv 升级依赖不是自动发生的

已有 `uv.lock` 时，uv 会优先保留锁定版本。新版本发布并不会自动让锁文件过期。

升级所有锁定包：

```bash
uv lock --upgrade
```

只升级一个包：

```bash
uv lock --upgrade-package requests
```

升级仍受 `pyproject.toml` 中版本范围限制。依赖升级应独立完成并运行测试，不要在修复普通代码问题时顺手更新全部锁文件。

## 10. 三种工具怎样选择

### 学习 Python 环境原理

优先：

```text
venv + python -m pip
```

它让解释器、PATH、pip 和环境目录之间的关系最透明。

### 新建长期维护的普通 Python 项目

可以优先考虑：

```text
uv + pyproject.toml + uv.lock
```

适合希望统一 Python 版本、环境、依赖声明、锁定和运行命令的团队。

### 科学计算或复杂原生依赖

可以考虑：

```text
Conda 项目环境
```

尤其当团队已有 Channel、环境文件、锁文件和 GPU 依赖规范时。

### 已有仓库

先遵循项目当前工具：

```text
看到 uv.lock
→ 先使用 uv

看到 environment.yml / conda-lock.yaml
→ 先查项目 Conda 说明

看到 requirements.txt 与 .venv 说明
→ 使用 venv + pip
```

不要因为个人更喜欢另一套工具，就在修复小问题时把整个仓库迁移到新环境体系。

## 11. GPU 项目不能共享整个环境目录

Mac 常见计算后端：

```text
CPU
Apple MPS
```

Ubuntu NVIDIA 游戏本常见：

```text
CPU
CUDA
```

正确流程是：

```text
共享源码、pyproject、锁文件或环境声明
→ Mac 创建自己的环境
→ Ubuntu 创建自己的环境
→ 各自安装平台兼容包
→ 分别运行基础测试
→ 在 Ubuntu 验证 CUDA
```

即使两端都使用 uv 或 Conda，安装到环境中的二进制也可能不同。锁文件用于描述可复现的选择规则和解析结果，不是把 macOS 二进制变成 Linux 二进制。

## 12. 常见混用问题

### 激活 Conda 后又激活项目 venv

此时 PATH 会叠加，基础解释器和动态库来源可能难以判断。先退出一个环境，再决定项目真正使用哪套工具。

检查：

```bash
python -c 'import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)'
printf '%s\n' "$CONDA_PREFIX"
```

### uv 项目中手工使用 pip 安装依赖

临时安装可能没有进入 `pyproject.toml` 和 `uv.lock`，下一次精确同步还可能被移除。项目依赖应使用：

```bash
uv add PACKAGE
```

### 所有项目共用 Conda base

包来源、版本和用途会逐渐无法追踪。为每个项目创建独立环境。

### 同时维护多套互不关联的声明

例如仓库同时出现：

```text
requirements.txt
pyproject.toml
uv.lock
environment.yml
手工安装说明
```

这些文件可以有合理分工，但必须说明谁是权威来源、哪些由工具生成。若每一份都声称是唯一真相，很快会发生漂移。

## 13. 给 AI CLI 的环境约束

```text
先读取项目现有的 pyproject.toml、uv.lock、requirements 文件、environment.yml 或 Conda 锁文件。
判断当前项目实际使用哪种环境工具，不要擅自迁移。
执行 Python 命令前先输出 pwd 和 sys.executable。
安装依赖前说明：
- 使用哪个环境；
- 修改哪个声明或锁文件；
- 为什么需要依赖；
- 是否改变包来源；
- 如何验证。
不要使用 sudo pip，不要修改系统 Python，不要复制或提交 .venv。
```

继续阅读：

- [Python 解释器与 pip 定位](01-Python解释器与pip定位.md)
- [依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)
- [Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)

官方参考：

- [Python：venv](https://docs.python.org/3/library/venv.html)
- [Conda：Managing environments](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)
- [uv：Projects](https://docs.astral.sh/uv/guides/projects/)
- [uv：Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
