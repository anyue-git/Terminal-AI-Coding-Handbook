# 02 venv、Conda 与 uv 怎么选

Python 环境工具很多，但它们解决的问题不完全相同：

```text
venv
→ 使用已有 Python 创建轻量隔离环境

Conda
→ 同时管理 Python、原生库和多语言依赖

uv
→ 管理 Python、项目环境、依赖解析和锁文件
```

不要只问“哪个最快”，应先确认项目真正需要什么。

---

## 1. 先拆成四个问题

```text
使用哪个 Python 版本
→ 环境隔离在哪里
→ 直接依赖如何声明
→ 完整解析结果如何锁定
```

| 工具 | Python 版本 | 虚拟环境 | Python 包 | 原生库 | 项目锁文件 |
|---|---:|---:|---:|---:|---:|
| `venv` | 依赖已有解释器 | 是 | 配合 pip | 否 | 否 |
| Conda | 是 | 是 | 是 | 是 | 以环境文件为主 |
| uv | 是 | 是 | 是 | 主要面向 Python 生态 | `uv.lock` |

这只是入门心智模型，不代表工具的全部高级能力。

---

## 2. venv：最透明、最容易理解

创建：

```bash
python3 -m venv .venv
```

激活：

```bash
source .venv/bin/activate
```

验证：

```bash
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

适合：

- 小型项目；
- 主要依赖来自 PyPI；
- 团队已有 `requirements.txt`；
- 希望少引入一层工具；
- 需要清楚理解 Python 与 pip 的关系。

局限：

- 不负责安装 Python 本身；
- 不直接管理系统原生库；
- 没有内置项目锁文件；
- 依赖复现需要配合其他工具。

---

## 3. Conda：适合复杂原生依赖

创建环境：

```bash
conda create -n my-project python=3.12 pip
conda activate my-project
```

验证：

```bash
python -c 'import sys; print(sys.executable)'
conda list
```

适合：

- 科学计算；
- 依赖复杂 C/C++、Fortran 或系统库；
- 需要同时管理 Python 以外的软件；
- 团队已有成熟 Conda 环境；
- 某些包在 Conda 生态中更容易安装。

注意：

- `base` 不适合作为所有项目共用环境；
- 不要无计划地混用多个 Channel；
- `pip` 和 Conda 混装时，先装 Conda 包，再补必要的 pip 包；
- 环境导出不等于跨平台复制整个环境目录。

对新版本 PyTorch，不能继续把旧的 `conda install pytorch ... -c pytorch` 当成永久标准。应查看 PyTorch 当前官方安装建议。

---

## 4. uv：适合现代 Python 项目

初始化项目：

```bash
uv init
```

添加依赖：

```bash
uv add requests
```

同步锁定环境：

```bash
uv sync --locked
```

运行命令：

```bash
uv run python -c 'import sys; print(sys.executable)'
uv run pytest
```

适合：

- 新建 Python 项目；
- 希望统一管理 Python、环境、依赖与锁文件；
- 需要 Mac、Ubuntu 和 CI 使用同一项目声明；
- 团队愿意统一使用 uv；
- 希望减少手工激活环境的步骤。

需要理解：

- uv 快，不代表依赖冲突消失；
- `uv.lock` 应进入版本控制；
- 平台不同仍会安装各自兼容的 wheel；
- GPU 包和自定义索引需要明确记录；
- 不应把 `.venv` 提交或同步到另一台机器。

---

## 5. 怎样选择

### 普通学习项目

```text
venv + pip
```

优点是概念透明，遇到问题容易理解每一层。

### 新建长期维护项目

```text
uv + pyproject.toml + uv.lock
```

适合把依赖声明、锁定和运行命令统一起来。

### 科学计算或复杂原生库

```text
Conda 环境
+ 必要时在环境内使用 pip
```

但应保持安装来源和顺序清楚。

### 团队已有标准

优先遵循项目现有工具。不要因为自己喜欢另一个工具，就把整个仓库的环境体系重写一遍。

---

## 6. GPU 项目没有“一套环境两台机器通吃”

Mac 常见：

```text
CPU
MPS
```

Ubuntu NVIDIA 游戏本常见：

```text
CPU
CUDA
```

正确流程：

```text
共享源码、依赖声明和锁文件
→ Mac 单独创建环境
→ Ubuntu 单独创建环境
→ 各自安装平台兼容包
→ 分别运行测试
```

环境工具可以相同，但实际二进制包未必相同。

---

## 7. 常见错误

### 把 `.venv` 同步到另一台机器

环境内含绝对路径和平台二进制，不能跨 macOS 与 Ubuntu 直接使用。

### 所有项目都用 Conda base

容易形成无法追踪的共享依赖池。

### 同一个项目同时维护多套互不一致的声明

例如：

```text
requirements.txt
pyproject.toml
environment.yml
手工安装说明
```

如果它们都声称是唯一真相，却没有生成关系，很快会互相冲突。

### 为了修一个包而整体升级环境

先确认解释器、包来源和错误原因，再决定是否更新依赖。

---

## 8. 给 AI CLI 的环境约束

```text
先读取项目现有的 pyproject.toml、uv.lock、requirements.txt 或 environment.yml。
不要擅自把项目迁移到另一种环境工具。

执行 Python 命令前，先输出 sys.executable。
安装依赖前说明：
- 使用哪个环境；
- 修改哪个依赖文件；
- 为什么需要该依赖；
- 如何验证；
- 是否会影响锁文件。

不要使用 sudo pip，不要修改系统 Python。
```

继续阅读：

- [Python 解释器与 pip 定位](01-Python解释器与pip定位.md)
- [依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)
- [Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)

官方参考：

- [Python：venv](https://docs.python.org/3/library/venv.html)
- [Conda：Managing environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
- [uv：Projects](https://docs.astral.sh/uv/guides/projects/)
