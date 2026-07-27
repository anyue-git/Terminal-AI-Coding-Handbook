# 01 Python 解释器与 pip 定位

很多 Python 报错表面上是“包没装好”，实际问题却是：

```text
安装依赖时使用的 pip
≠
运行代码时使用的 Python
```

所以遇到 `ModuleNotFoundError` 时，先不要连续安装三遍。第一步应该确认：当前究竟在使用哪个解释器，它对应的 pip 又在哪里。

---

## 1. `python` 是一个具体文件

查看命令来自哪里：

```bash
type -a python
type -a python3
```

查看真正执行的解释器：

```bash
python -c 'import sys; print(sys.executable)'
python3 -c 'import sys; print(sys.executable)'
```

查看版本只能回答“它是什么版本”：

```bash
python --version
python3 --version
```

不能单靠版本判断它来自系统、Homebrew、Conda、uv 还是项目虚拟环境。

一台机器同时存在多个 Python 很正常，常见来源包括：

- 操作系统；
- Homebrew；
- Python 官方安装器；
- Conda；
- `venv`；
- uv；
- pyenv；
- 某些软件自带的 Python。

真正需要避免的不是“有多个 Python”，而是自己不知道当前用了哪一个。

---

## 2. 用 `sys.prefix` 判断虚拟环境

```bash
python - <<'PY'
import sys
print("version:", sys.version)
print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
PY
```

通常：

```text
sys.prefix != sys.base_prefix
```

说明当前解释器位于 `venv` 类虚拟环境中。

这比只看终端提示符前面有没有 `(.venv)` 更可靠。提示符可以被主题改掉，解释器路径不会因为主题好看就自动正确。

---

## 3. pip 也可能有很多个

检查：

```bash
type -a pip
type -a pip3
pip --version
pip3 --version
```

输出通常包含 pip 所在路径和关联的 Python 版本。

项目中更推荐：

```bash
python -m pip --version
```

因为它明确表示：

> 使用当前这个 Python，调用它对应的 pip 模块。

安装项目依赖时也优先使用：

```bash
python -m pip install PACKAGE
```

而不是只写：

```bash
pip install PACKAGE
```

前者不能解决所有依赖问题，但至少把“装到哪个 Python”说清楚了。

---

## 4. `ModuleNotFoundError` 的固定排查顺序

假设出现：

```text
ModuleNotFoundError: No module named 'requests'
```

先运行：

```bash
pwd
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -m pip show requests
```

如果包已安装，再检查它实际从哪里导入：

```bash
python -c 'import requests; print(requests.__file__)'
```

还要检查项目中是否存在同名文件：

```text
requests.py
numpy.py
torch.py
```

这些文件可能遮蔽真正的第三方包。

查看模块搜索路径：

```bash
python -c 'import sys; print("\n".join(sys.path))'
```

不要在解释器都没确认时不断重装包。那相当于钥匙插错门后，决定再配五把同样的钥匙。

---

## 5. 激活虚拟环境究竟做了什么

创建 `venv`：

```bash
python3 -m venv .venv
```

激活：

```bash
source .venv/bin/activate
```

最主要的变化，是把：

```text
PROJECT/.venv/bin
```

放到当前 Shell 的 `PATH` 前面。

验证：

```bash
type -a python
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

退出：

```bash
deactivate
```

激活虚拟环境不等于启动虚拟机，也不等于进入 Docker 容器。它主要改变当前 Shell 查找 Python 和相关命令的顺序。

---

## 6. 不激活也能精确调用环境

```bash
.venv/bin/python app.py
.venv/bin/python -m pip list
```

这种写法在脚本、CI 和排错中很有用，因为解释器路径不会依赖当前 Shell 是否激活环境。

项目使用 uv 时，也可以直接运行：

```bash
uv run python -c 'import sys; print(sys.executable)'
uv run pytest
```

---

## 7. 不要使用 `sudo pip install`

不推荐：

```bash
sudo pip install PACKAGE
```

它可能把第三方包写入系统 Python，造成：

- 系统包和项目包混杂；
- 权限异常；
- 升级与卸载困难；
- 操作系统工具受影响；
- 后续环境难以复现。

遇到权限错误时，优先确认：

```bash
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

然后使用项目虚拟环境，而不是给安装命令加更高权限。

`pip install --user` 比 `sudo pip` 温和，但它仍会让多个项目共享用户级包，不适合作为项目依赖的默认方案。

---

## 8. Mac 和 Ubuntu 的环境不能直接复制

Mac 常见路径：

```text
/opt/homebrew/bin/python3
/Users/NAME/PROJECT/.venv/bin/python
```

Ubuntu 常见路径：

```text
/usr/bin/python3
/home/NAME/PROJECT/.venv/bin/python
/home/NAME/miniconda3/envs/ENV/bin/python
```

两台机器的操作系统、架构和二进制格式不同。不要把 Mac 的 `.venv` rsync 到 Ubuntu 后继续使用。

应该共享：

- 源码；
- `pyproject.toml`；
- 锁文件；
- `requirements.txt`；
- 环境创建说明。

应该分别创建：

- Mac 的 Python 环境；
- Ubuntu 的 Python 环境；
- 各平台兼容的 PyTorch 和原生依赖。

---

## 9. 编辑器和 AI CLI 也会选错解释器

VS Code、Claude Code、Codex CLI 和 Grok CLI 最终执行的仍是某个具体命令。

任务开始时可以明确：

```text
本项目使用项目根目录下的 .venv。
执行 Python 命令前，先输出：
- 当前目录；
- sys.executable；
- python -m pip --version。

不要使用 sudo pip，不要修改系统 Python。
如果环境不存在或依赖缺失，先说明，不要自动重建整套环境。
```

审批命令时检查：

- 当前目录；
- 解释器路径；
- 是否使用 `python -m pip`；
- 是否在修改依赖文件；
- 是否会影响项目外环境。

---

## 10. 一份最短自检清单

```bash
pwd
type -a python python3 pip pip3
python --version
python -c 'import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)'
python -m pip --version
python -m pip list
```

GPU 项目再检查：

```bash
python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
```

出现问题时，按下面顺序判断：

```text
当前目录
→ 解释器
→ pip 绑定关系
→ 包安装位置
→ 同名文件遮蔽
→ 依赖版本冲突
→ 平台或 GPU 条件
```

继续阅读：

- [venv、Conda 与 uv 怎么选](02-venv-Conda与uv怎么选.md)
- [依赖声明、锁定与环境复现](03-依赖声明锁定与环境复现.md)
- [Mac 与 Ubuntu 分别创建环境](../Part-11-GPU远程开发/05-Mac与Ubuntu分别创建环境.md)

官方参考：

- [Python：venv](https://docs.python.org/3/library/venv.html)
- [Python Packaging User Guide：Installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
