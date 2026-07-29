# 04 NVIDIA 驱动、CUDA 与 PyTorch 分层安装

> 最近核对：2026-07-29
>
> 驱动、PyTorch 和 CUDA 安装方式会随 Ubuntu、GPU 型号与官方发布变化。安装前应核对 Ubuntu、NVIDIA 和 PyTorch 当前官方文档，不要长期照搬某个固定版本号。

机器学习新手常把所有 GPU 组件统称为“CUDA”，但实际链路是：

```text
NVIDIA GPU 硬件
→ Linux 内核与 NVIDIA 驱动
→ CUDA 用户态运行库
→ PyTorch 构建
→ 项目 Python 环境
→ 训练代码
```

任何一层出错都可能表现为“GPU 用不了”，但修复方式完全不同。本章建立一个按层验证的流程，避免一次性重装所有组件。

## 1. 先确认当前运行的是 Ubuntu

在 **Ubuntu 游戏本本机或 SSH 会话**中执行：

```bash
hostname
cat /etc/os-release
uname -m
lspci | grep -i -E 'vga|3d|nvidia'
```

典型游戏本通常是：

```text
Ubuntu 24.04
x86_64
NVIDIA GPU
```

如果当前启动的是 Windows，Mac 端 SSH 别名可能连接失败。双系统机器同一时刻只运行其中一个系统，Windows 中安装的 NVIDIA 驱动不会自动提供给 Ubuntu。

## 2. 查看驱动是否已经正常

```bash
nvidia-smi
```

正常时通常显示：

- GPU 型号；
- 驱动版本；
- 温度、功耗和显存；
- 当前 GPU 进程；
- 驱动能够支持的 CUDA 兼容上限。

`nvidia-smi` 中的 `CUDA Version` 不代表：

- 系统一定安装了对应 CUDA Toolkit；
- `nvcc` 一定存在；
- 当前 PyTorch 使用同一版本；
- 项目一定能正常训练。

它首先证明的是“驱动能够识别并与 GPU 通信”。如果 `nvidia-smi` 失败，先停在驱动层，不要先重装 torch。

## 3. 使用 Ubuntu 推荐驱动流程

查看设备和推荐驱动：

```bash
ubuntu-drivers devices
```

自动安装推荐驱动：

```bash
sudo ubuntu-drivers install
```

完成后通常需要重启：

```bash
sudo reboot
```

重启会断开 SSH 和终止所有进程。执行前确认没有训练、未保存编辑或正在写入的 checkpoint。

重启后重新连接：

```bash
ssh gpu-laptop
nvidia-smi
```

不要同时混用多套驱动来源，例如 Ubuntu 仓库、NVIDIA `.run` 安装器和手工复制内核模块。对普通 Ubuntu 游戏本，优先采用 Ubuntu 文档支持的方式。

## 4. Secure Boot 与驱动未加载

部分游戏本开启 Secure Boot 后，安装驱动时可能要求设置并在重启时确认 MOK。典型现象包括：

```text
驱动包已安装
但 nvidia-smi 提示无法与驱动通信
```

检查：

```bash
mokutil --sb-state
lsmod | grep nvidia
journalctl -k --no-pager | grep -i -E 'nvidia|secure boot|module verification' | tail -n 80
```

不要为了省事直接关闭所有安全机制。先确认安装过程中是否遗漏 MOK 注册、内核模块是否为当前内核构建，以及重启后是否加载。

## 5. `nvcc` 属于 CUDA Toolkit

检查：

```bash
command -v nvcc || true
nvcc --version
```

CUDA Toolkit 主要提供：

- `nvcc` 编译器；
- CUDA C/C++ 头文件和开发库；
- 调试、分析工具；
- 编译自定义 CUDA 扩展所需组件。

没有 `nvcc` 不等于 PyTorch 不能使用 GPU。官方预编译 PyTorch 包通常自带所需 CUDA 用户态运行库。

更可能需要系统 Toolkit 的情况：

- 编译自定义 CUDA 扩展；
- 开发 CUDA C/C++；
- 项目明确要求本地编译；
- 安装包没有兼容预编译 wheel。

普通 PyTorch 训练先不安装 Toolkit，减少版本和 PATH 冲突。

## 6. 先创建项目环境

在 Ubuntu 项目目录：

```bash
cd ~/projects/my-project
```

使用 uv 的项目：

```bash
uv python install
uv sync --locked
```

使用 venv 的项目：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

GPU 项目中的 PyTorch 安装命令应来自当前 PyTorch Start Locally 选择器。根据：

```text
Linux
包管理器
Python
CUDA 构建
```

生成命令，不要从旧文章复制长期固定的 CUDA 版本。

## 7. 在同一个解释器中验证 PyTorch

```bash
python - <<'PY'
import sys
import torch

print("python:", sys.executable)
print("torch:", torch.__version__)
print("build_cuda:", torch.version.cuda)
print("cuda_available:", torch.cuda.is_available())
print("device_count:", torch.cuda.device_count())

if torch.cuda.is_available():
    print("device_0:", torch.cuda.get_device_name(0))
    print("capability:", torch.cuda.get_device_capability(0))
PY
```

含义：

```text
sys.executable
→ 当前实际解释器

torch.__version__
→ PyTorch 版本

torch.version.cuda
→ 该 PyTorch 构建关联的 CUDA Runtime

torch.cuda.is_available()
→ 当前进程能否实际使用 CUDA
```

如果 `torch.version.cuda` 为 `None`，通常安装了 CPU 构建。

## 8. 做一次最小 GPU 计算

仅仅返回 `True` 还不够。运行：

```bash
python - <<'PY'
import torch

assert torch.cuda.is_available(), "CUDA is not available"

device = torch.device("cuda:0")
x = torch.randn(2048, 2048, device=device)
y = torch.randn(2048, 2048, device=device)
z = x @ y

torch.cuda.synchronize()
print("device:", z.device)
print("shape:", tuple(z.shape))
print("mean:", z.mean().item())
print("allocated_mb:", torch.cuda.memory_allocated() / 1024**2)
PY
```

同时在另一个终端观察：

```bash
watch -n 1 nvidia-smi
```

这证明当前 Python、torch、驱动和 GPU 至少能完成一次真实计算。

## 9. 理解三个“CUDA 版本”为什么不同

可能同时看到：

```text
nvidia-smi 中的 CUDA Version
nvcc --version
python 中的 torch.version.cuda
```

它们分别表示：

```text
nvidia-smi
→ 驱动支持的 CUDA 兼容能力

nvcc
→ 本机 CUDA Toolkit 编译器版本

torch.version.cuda
→ 当前 PyTorch 构建使用的 CUDA Runtime 版本
```

三者不同不一定有问题。关键是宿主机驱动必须足够新，能支持 PyTorch 所携带的运行时。

## 10. 固定排错顺序

### 第一层：硬件和驱动

```bash
lspci | grep -i nvidia
nvidia-smi
```

### 第二层：当前解释器

```bash
which python
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

### 第三层：PyTorch 来源

```bash
python -m pip show torch
python -c 'import torch; print(torch.__version__); print(torch.version.cuda)'
```

### 第四层：CUDA 可用性

```bash
python -c 'import torch; print(torch.cuda.is_available())'
```

### 第五层：真实 GPU 运算

运行上一节矩阵乘法。

### 第六层：项目代码

```bash
python train.py --help
python train.py --max-steps 2
```

### 第七层：只有需要编译扩展时才检查 Toolkit

```bash
nvcc --version
echo "$CUDA_HOME"
```

按层检查可以保留证据。一次性重装全部组件只会制造更多变量。

## 11. 常见错误怎么判断

### `torch.cuda.is_available()` 为 `False`

检查：

```text
nvidia-smi 是否成功
是否选错 Python
是否安装 CPU 版 torch
容器是否获得 GPU
环境变量是否隐藏 GPU
```

### `CUDA driver version is insufficient`

通常是驱动过旧，无法支持当前 PyTorch CUDA Runtime。优先升级受支持的驱动，而不是随机降低多个包。

### `CUDA out of memory`

这通常说明 GPU 已可用，只是显存不足。尝试：

- 减小 batch size；
- 缩短序列；
- 梯度累积；
- 混合精度；
- 梯度检查点；
- 使用更小模型；
- 检查是否有自己遗留的 GPU 进程。

```bash
nvidia-smi
```

不要终止不属于自己的进程，也不要把桌面图形进程当成训练残留。

### `no kernel image is available`

可能是当前 PyTorch 构建不包含该 GPU 架构，或自定义扩展编译目标不匹配。需要核对 GPU Compute Capability、PyTorch 支持范围和扩展构建参数。

### 动态库冲突

检查是否在 Shell 配置中叠加了多套：

```text
CUDA_HOME
PATH
LD_LIBRARY_PATH
```

不要为了修一个项目，把多个 CUDA 目录永久追加到全局 `.zshrc` 或 `.bashrc`。

## 12. Mac 的 MPS 不是 Ubuntu CUDA

Mac 常见设备：

```text
cpu
mps
```

Ubuntu NVIDIA 常见设备：

```text
cpu
cuda
```

通用选择示例：

```python
import torch

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
```

Mac MPS 冒烟测试可以发现通用 Python 错误，但 MPS 与 CUDA 的算子支持、数值行为、显存模型和性能不同。正式 GPU 验证必须在 Ubuntu 完成。

## 13. GPU 容器仍依赖宿主机驱动

```text
Ubuntu NVIDIA 驱动
→ NVIDIA Container Toolkit
→ Docker GPU 授权
→ 容器 CUDA/PyTorch 环境
→ 项目代码
```

宿主机先检查：

```bash
nvidia-smi
nvidia-ctk --version
```

宿主机驱动失败时，重建容器通常没有意义。容器细节见 [GPU 容器与权限边界](../Part-08-Docker/04-GPU容器与权限边界.md)。

## 14. 保存环境证据

在每个重要实验目录中保存：

```bash
{
  date -Is
  hostname
  uname -a
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > environment.txt 2>&1
```

需要记录 Python 包时，可以保存：

```bash
python -m pip freeze > pip-freeze.txt
```

但 `pip freeze` 是环境快照，不一定适合直接作为跨平台依赖声明。不要保存完整环境变量。

## 15. 完成分层验收

最终验收顺序：

```text
1. Ubuntu 能识别 NVIDIA PCI 设备
2. nvidia-smi 成功
3. 项目解释器正确
4. torch 能导入
5. torch.version.cuda 合理
6. torch.cuda.is_available() 为 True
7. 最小矩阵运算成功
8. 项目短任务成功
9. 日志和退出状态可追踪
```

只有前一层通过，才进入下一层。

## 继续阅读

- [Mac 与 Ubuntu 分别创建环境](05-Mac与Ubuntu分别创建环境.md)
- [tmux、日志与断线后继续训练](03-tmux与断线续跑.md)
- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)

官方参考：

- [Ubuntu：NVIDIA drivers installation](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/)
- [PyTorch：Start Locally](https://pytorch.org/get-started/locally/)
- [NVIDIA：CUDA Compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/)
