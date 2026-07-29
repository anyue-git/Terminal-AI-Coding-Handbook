# 01 Python 解释器与 pip 定位

很多 Python 故障看起来像“包没装上”，实际原因却是安装依赖时使用的 pip，与运行代码时使用的 Python 不属于同一个环境。一台 Mac 或 Ubuntu 同时存在多个 Python 很正常；真正需要避免的是不知道当前命令最终指向哪一个文件。

本章会建立一个练习项目，分别观察系统或 Homebrew Python、项目虚拟环境及其 pip，让 `ModuleNotFoundError` 的排查不再依赖反复重装。

## 1. `python` 和 `python3` 最终都是具体可执行文件

先建立练习目录：

```bash
mkdir -p ~/terminal-practice/python-location
cd ~/terminal-practice/python-location
pwd
```

查看当前 Shell 能找到哪些候选：

```bash
type -a python 2>/dev/null
type -a python3
```

再查看当前默认解析结果：

```bash
command -v python 2>/dev/null
command -v python3
```

macOS 上可能只有 `python3`，也可能因为 Homebrew、Conda、uv、pyenv 或虚拟环境而同时存在多个命令。版本信息只能回答“这个解释器是什么版本”：

```bash
python3 --version
```

要知道真正运行的文件，使用：

```bash
python3 -c 'import sys; print(sys.executable)'
```

Apple Silicon Homebrew Python 可能输出：

```text
/opt/homebrew/bin/python3
```

Ubuntu 系统 Python 可能输出：

```text
/usr/bin/python3
```

路径比提示符和别名更可靠。终端主题显示了 `(base)` 或 `(.venv)`，也不能替代 `sys.executable` 的实际结果。

## 2. 一台机器为什么会有多个 Python

常见来源包括：

- 操作系统或 Linux 发行版；
- Homebrew；
- python.org 安装器；
- Conda；
- pyenv；
- uv 管理的 Python；
- 项目中的 `venv`；
- 某些应用自带的运行时。

这些解释器可能拥有不同版本、不同标准库位置和不同第三方包目录。检查详细信息：

```bash
python3 - <<'PY'
import platform
import sys

print("version:", sys.version)
print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
print("platform:", platform.platform())
PY
```

`sys.prefix` 表示当前环境前缀，`sys.base_prefix` 表示创建虚拟环境时使用的基础 Python。对于标准 `venv`，通常：

```text
sys.prefix != sys.base_prefix
```

说明当前正在使用虚拟环境。

## 3. pip 也不是唯一的一份

查看候选命令：

```bash
type -a pip 2>/dev/null
type -a pip3 2>/dev/null
```

查看版本：

```bash
pip3 --version
```

输出通常同时包含 pip 的安装路径和关联 Python，例如：

```text
pip ... from .../site-packages/pip (python 3.12)
```

项目中更推荐使用：

```bash
python3 -m pip --version
```

这句话的含义非常明确：用当前这个 `python3` 启动它自己的 `pip` 模块。安装依赖时同样优先写：

```bash
python3 -m pip install PACKAGE
```

而不是只写：

```bash
pip install PACKAGE
```

`python -m pip` 不能解决所有依赖冲突，但至少能确认包将安装到哪个解释器所属的环境。

## 4. 创建项目虚拟环境并观察变化

在练习目录执行：

```bash
python3 -m venv .venv
```

这会在当前项目中创建一个隔离环境。激活：

```bash
source .venv/bin/activate
```

现在检查：

```bash
command -v python
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

应看到解释器和 pip 位于项目下：

```text
.../python-location/.venv/bin/python
.../python-location/.venv/lib/python.../site-packages/pip
```

激活脚本最主要的作用，是把 `.venv/bin` 放到当前 Shell 的 PATH 前面，并设置一些环境标记。它不是虚拟机，不会模拟另一套操作系统，也不会创建 Docker 容器。

查看 PATH 前几项：

```bash
printf '%s\n' "$PATH" | tr ':' '\n' | head
```

第一项通常是：

```text
.../python-location/.venv/bin
```

退出虚拟环境：

```bash
deactivate
```

再次检查：

```bash
command -v python3
python3 -c 'import sys; print(sys.executable)'
```

路径会回到激活前的解释器。

## 5. 不激活也能精确使用虚拟环境

激活只是方便当前交互式 Shell。虚拟环境中的解释器可以直接调用：

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
```

运行脚本：

```bash
printf '%s\n' \
  'import sys' \
  'print(sys.executable)' \
  > show_python.py

.venv/bin/python show_python.py
```

这种写法适合脚本、CI、Makefile 和排错，因为它不依赖当前 Shell 是否已经执行 `activate`。

Python 官方文档也说明，激活不是使用虚拟环境的必需步骤。只要明确调用环境内的可执行文件，就能得到相同隔离效果。

## 6. 制造一次可控的 `ModuleNotFoundError`

先确认虚拟环境中没有 `requests`：

```bash
.venv/bin/python -m pip show requests
```

如果没有安装，通常会提示找不到包。创建脚本：

```bash
printf '%s\n' \
  'import requests' \
  'print(requests.__version__)' \
  > check_requests.py
```

运行：

```bash
.venv/bin/python check_requests.py
```

可能看到：

```text
ModuleNotFoundError: No module named 'requests'
```

这时先记录解释器和 pip：

```bash
.venv/bin/python -c 'import sys; print(sys.executable)'
.venv/bin/python -m pip --version
```

然后把包安装到同一个解释器：

```bash
.venv/bin/python -m pip install requests
```

再次运行：

```bash
.venv/bin/python check_requests.py
```

如果网络和包索引正常，应输出版本号。最后查看模块实际来自哪里：

```bash
.venv/bin/python -c 'import requests; print(requests.__file__)'
```

路径应位于项目 `.venv` 中。这套过程证明了“安装命令”和“运行命令”使用的是同一个解释器。

## 7. `ModuleNotFoundError` 的固定排查顺序

假设项目提示：

```text
ModuleNotFoundError: No module named 'PACKAGE'
```

先运行：

```bash
pwd
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -m pip show PACKAGE
```

如果 `show` 能找到包，再检查导入路径：

```bash
python -c 'import PACKAGE; print(PACKAGE.__file__)'
```

若导入失败，还要检查项目中是否存在同名文件或目录，例如：

```text
requests.py
numpy.py
torch.py
json.py
```

本地文件可能遮蔽第三方包或标准库。搜索：

```bash
find . -type f -name 'PACKAGE.py' -print
find . -type d -name 'PACKAGE' -print
```

查看模块搜索路径：

```bash
python -c 'import sys; print("\n".join(sys.path))'
```

按下面顺序定位：

```text
当前目录
→ 实际解释器
→ 解释器对应的 pip
→ 包是否安装在该环境
→ 项目中是否有同名文件
→ sys.path 是否异常
→ 包版本与平台是否兼容
```

解释器尚未确认时连续运行多个 `pip install`，往往只会把包安装到更多不相关的环境。

## 8. `pip show`、`pip list` 和 `pip freeze` 分别回答什么

查看一个包：

```bash
python -m pip show requests
```

查看当前环境所有已安装分发包：

```bash
python -m pip list
```

导出当前环境的版本快照：

```bash
python -m pip freeze
```

`pip freeze` 描述“这个环境当前装了什么”，不自动区分直接依赖、传递依赖、临时工具和其他项目残留。它可以作为故障证据或临时快照，但不等同于经过设计的项目依赖声明。

## 9. 不要使用 `sudo pip install`

不应执行：

```bash
sudo pip install PACKAGE
```

它可能把第三方包写入系统或包管理器管理的 Python，产生权限冲突、升级困难和不可复现的共享环境。Ubuntu 的系统工具也可能依赖发行版提供的 Python 包，随意覆盖会影响系统功能。

遇到权限错误时，先确认：

```bash
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

然后为项目创建虚拟环境，而不是给安装命令添加管理员权限。

`pip install --user` 会安装到用户级目录，比 sudo 温和，但多个项目会共享这些包，命令还可能被放到尚未进入 PATH 的用户 bin 目录。它不适合作为项目依赖的默认方案。独立的全局 Python CLI 更适合通过 pipx、uv tool 或系统包管理器安装。

## 10. Mac 和 Ubuntu 不能复制同一个 `.venv`

Mac 环境可能包含：

```text
/Users/NAME/project/.venv/bin/python
macOS arm64 wheel
```

Ubuntu 环境可能需要：

```text
/home/NAME/project/.venv/bin/python
Linux x86_64 wheel
CUDA 相关构建
```

虚拟环境中常含绝对路径、启动脚本和平台二进制。把 Mac 的 `.venv` 通过 rsync 复制到 Ubuntu，通常无法正常使用，即使某些纯 Python 文件看起来相同。

应该共享：

- 源码；
- `pyproject.toml`；
- `uv.lock` 或其他锁文件；
- `requirements.txt`；
- 环境创建和测试命令。

应该分别创建：

- Mac 的项目环境；
- Ubuntu 的项目环境；
- 各平台兼容的原生包和 GPU 依赖。

## 11. VS Code、Notebook 和 AI CLI 也可能选择错误解释器

VS Code 状态栏、Jupyter Kernel、终端虚拟环境和 Agent 执行命令可能各自指向不同 Python。遇到“终端能导入，Notebook 不能导入”时，在对应环境内直接运行：

```python
import sys
print(sys.executable)
```

Notebook 中安装依赖时，应使用当前内核对应的解释器，而不是猜测外部终端中的 `pip`。在脚本或 Notebook 需要调用 Python 命令时，也应基于 `sys.executable` 保持一致。

给 AI CLI 的约束可以写成：

```text
本项目使用项目根目录的 .venv。
执行 Python 命令前先输出 pwd、sys.executable 和 python -m pip --version。
不要使用 sudo pip，不要修改系统 Python。
如果环境不存在、Python 版本不符或依赖缺失，先报告现状和建议，不要自动重建或全量升级。
```

## 12. 最短自检清单

普通项目：

```bash
pwd
type -a python python3 pip pip3
python --version
python -c 'import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)'
python -m pip --version
python -m pip list
```

不确定是否激活环境时：

```bash
python - <<'PY'
import sys
print("executable:", sys.executable)
print("in_venv:", sys.prefix != sys.base_prefix)
PY
```

GPU 项目在 Ubuntu 环境中还可检查：

```bash
python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
```

这条命令只能验证当前 PyTorch 环境的视角，完整 GPU 排查还需要驱动、设备和系统层检查。

继续阅读：

- [venv、Conda 与 uv 怎么选](02-venv-Conda与uv怎么选.md)
- [依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)
- [Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)

官方参考：

- [Python：venv](https://docs.python.org/3/library/venv.html)
- [Python Packaging User Guide：Installing Packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
