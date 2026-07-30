# 01 Python 解释器与 pip 定位

很多“包没装上”的故障，实际是安装依赖时使用的 pip 与运行代码时使用的 Python 不属于同一环境。一台 Mac 或 Ubuntu 同时存在系统 Python、Homebrew、Conda、uv、pyenv 和项目虚拟环境很正常；排错的关键是找到当前命令最终指向的可执行文件。

本章在练习目录中定位解释器与 pip，观察虚拟环境如何改变 PATH，再制造一次可控的 `ModuleNotFoundError`。

## 1. 从命令名称追到解释器和 pip

```bash
mkdir -p ~/terminal-practice/python-location
cd ~/terminal-practice/python-location
pwd

type -a python 2>/dev/null
type -a python3
command -v python 2>/dev/null
command -v python3
python3 --version
python3 -c 'import sys; print(sys.executable)'
```

版本号说明解释器版本，`sys.executable` 才给出当前进程的真实文件。Apple Silicon 的 Homebrew Python 可能位于 `/opt/homebrew/bin/python3`，Ubuntu 系统 Python 常见 `/usr/bin/python3`；提示符显示 `(base)` 或 `(.venv)` 也不能替代路径检查。

需要更多上下文时查看环境前缀和平台：

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

标准 `venv` 中通常有 `sys.prefix != sys.base_prefix`。每个解释器拥有自己的标准库、第三方包目录和平台兼容范围。

pip 也可能有多个候选：

```bash
type -a pip 2>/dev/null
type -a pip3 2>/dev/null
pip3 --version
python3 -m pip --version
```

项目中优先使用：

```bash
python3 -m pip install PACKAGE
```

它表示“让当前 Python 启动自己的 pip 模块”，把安装目标与运行解释器绑定在同一条命令中。查看包和环境快照也保持同一形式：

```bash
python3 -m pip show PACKAGE
python3 -m pip list
python3 -m pip freeze
```

`pip freeze` 记录当前环境安装结果，可能同时包含直接依赖、传递依赖、临时工具和其他项目残留，适合作为快照与故障证据，不自动成为项目依赖设计。

## 2. 创建虚拟环境并观察路径变化

```bash
python3 -m venv .venv
source .venv/bin/activate

command -v python
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
printf '%s\n' "$PATH" | tr ':' '\n' | head
```

激活后，解释器和 pip 应位于当前项目的 `.venv`。激活脚本主要把 `.venv/bin` 放到当前 Shell 的 PATH 前面并设置少量标记；它不是虚拟机或另一套操作系统。

退出环境：

```bash
deactivate
command -v python3
python3 -c 'import sys; print(sys.executable)'
```

脚本、CI 和排错时可以不依赖激活，直接调用环境内解释器：

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version

printf '%s\n' \
  'import sys' \
  'print(sys.executable)' \
  > show_python.py

.venv/bin/python show_python.py
```

这种写法明确指出程序由哪一个 Python 运行。

## 3. 用受控缺包验证安装与运行的一致性

先查看虚拟环境中是否已有 `requests`：

```bash
.venv/bin/python -m pip show requests
```

若未安装，创建脚本并运行：

```bash
printf '%s\n' \
  'import requests' \
  'print(requests.__version__)' \
  > check_requests.py

.venv/bin/python check_requests.py
```

出现 `ModuleNotFoundError` 后，记录解释器与 pip，再把包安装到同一个环境：

```bash
.venv/bin/python -c 'import sys; print(sys.executable)'
.venv/bin/python -m pip --version
.venv/bin/python -m pip install requests
.venv/bin/python check_requests.py
.venv/bin/python -c 'import requests; print(requests.__file__)'
```

最后一条路径应位于项目 `.venv`。这组命令把安装工具、运行解释器和模块来源连在一起，避免包被装到另一套 Python 后仍反复修改当前项目。

## 4. 缺包与权限问题按同一顺序排查

项目报缺包时先运行：

```bash
pwd
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -m pip show PACKAGE
```

`pip show` 能找到包而导入失败时，继续检查包来源、项目同名文件和搜索路径：

```bash
python -c 'import PACKAGE; print(PACKAGE.__file__)'
find . -type f -name 'PACKAGE.py' -print
find . -type d -name 'PACKAGE' -print
python -c 'import sys; print("\n".join(sys.path))'
```

`requests.py`、`numpy.py`、`torch.py` 或 `json.py` 等本地文件可能遮蔽第三方包或标准库。固定顺序是：当前目录、真实解释器、对应 pip、包安装位置、同名文件、`sys.path`，最后才判断版本与平台兼容性。

不使用：

```bash
sudo pip install PACKAGE
```

它可能把包写进系统或包管理器维护的 Python，带来权限冲突和升级问题。在项目中创建虚拟环境；独立的全局 Python CLI 更适合由 pipx、uv tool 或系统包管理器安装。`pip install --user` 虽然比 sudo 温和，但用户级包会被多个项目共享，也不适合作为项目依赖默认路线。

解释器问题的最小检查集可以保留为：

```bash
pwd
type -a python python3 pip pip3
command -v python3
python3 -c 'import sys; print(sys.executable)'
python3 -m pip --version
python3 -m pip show PACKAGE
```

IDE 与终端行为不一致时，也让它们分别报告真实解释器，而不是根据界面中的环境名称猜测。

## 5. Mac 与 Ubuntu共享声明，分别创建环境

Mac `.venv` 可能包含 macOS arm64 可执行文件和 wheel，Ubuntu 需要 Linux x86_64 路径与可能的 CUDA 构建。两台机器共享源码、`pyproject.toml`、requirements 和锁文件，在各自平台本地创建环境：

```bash
python -c 'import sys, platform; print(sys.executable); print(platform.platform())'
python -m pip --version
```

GPU 项目还要区分 Python 环境、PyTorch 构建、宿主 NVIDIA 驱动和 CUDA Runtime。完整跨平台流程见[Mac 与 Ubuntu 为什么必须分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)。

继续阅读：[venv、Conda 与 uv 怎么选](02-venv-Conda与uv怎么选.md)、[依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)和[Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)。