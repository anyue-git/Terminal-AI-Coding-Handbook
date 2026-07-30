# 04 NVIDIA 驱动、CUDA 与 PyTorch 分层验证

> 最近核对：2026-07-29
>
> 驱动、PyTorch 和 CUDA 安装方式会随 Ubuntu、GPU 与官方发布变化。实际安装前核对 Ubuntu、NVIDIA 和 PyTorch 当前文档，不长期照搬固定版本号。

“GPU 用不了”可能发生在不同层：

```text
NVIDIA GPU 硬件
→ Linux 内核与 NVIDIA 驱动
→ CUDA 用户态运行库
→ PyTorch 构建
→ 项目解释器与依赖
→ 训练代码
```

排错时从上到下验证；前一层没有成立，就暂不改动下一层。

## 1. 系统、硬件、驱动与 Secure Boot

在 Ubuntu 游戏本本机或 SSH 会话中确认系统、架构和 PCI 设备：

```bash
hostname
cat /etc/os-release
uname -m
lspci | grep -i -E 'vga|3d|nvidia'
```

双系统同一时刻只运行一个系统，Windows 驱动不会提供给 Ubuntu。接着运行：

```bash
nvidia-smi
```

正常输出会显示 GPU、驱动、温度、显存和当前进程。表头中的 `CUDA Version` 主要表示驱动支持的 CUDA 兼容能力上限，不代表系统已经安装同版本 Toolkit，也不能说明当前 PyTorch 和项目代码已经可用。

`nvidia-smi` 失败时，查看 Ubuntu 推荐驱动并按受支持流程安装：

```bash
ubuntu-drivers devices
sudo ubuntu-drivers install
```

安装后通常需要重启：

```bash
sudo reboot
```

重启会断开 SSH 并终止所有进程，执行前确认没有训练、未保存编辑和正在写入的 checkpoint。系统回来后重新验证：

```bash
ssh gpu-laptop
nvidia-smi
```

普通 Ubuntu 游戏本优先使用 Ubuntu/NVIDIA 当前支持的驱动来源，避免发行版包、旧 PPA、`.run` 安装器和手工内核模块互相覆盖。

Secure Boot 仍属于驱动层。驱动包已经安装但 `nvidia-smi` 无法通信时，检查：

```bash
mokutil --sb-state
lsmod | grep nvidia
journalctl -k --no-pager \
  | grep -i -E 'nvidia|secure boot|module verification' \
  | tail -n 80
```

确认 MOK 注册、模块是否为当前内核构建，以及重启后是否加载。完成驱动层的标准是 `nvidia-smi` 成功，而不是包管理器显示“已安装”。

## 2. 区分驱动兼容上限、Toolkit 和 PyTorch Runtime

检查本机是否有 CUDA Toolkit 编译器：

```bash
command -v nvcc || true
nvcc --version
```

Toolkit 提供 `nvcc`、头文件、开发库和自定义 CUDA 扩展编译工具。官方预编译 PyTorch 包通常自带运行所需的 CUDA 用户态库，所以没有 `nvcc` 并不等于 torch 不能使用 GPU。只有项目需要编译自定义扩展、开发 CUDA C/C++ 或明确依赖系统 Toolkit 时，才把 Toolkit 作为必要层。

一台机器同时出现三个版本很正常：

```text
nvidia-smi 中的 CUDA Version
→ 驱动支持的兼容能力

nvcc --version
→ 系统 CUDA Toolkit 编译器

torch.version.cuda
→ 当前 PyTorch 构建关联的 CUDA Runtime
```

关键关系是宿主驱动能够支持 PyTorch 携带的 Runtime。数字不同本身不能说明配置错误。

## 3. 在项目解释器中验证 PyTorch

进入 Ubuntu 项目，并按项目现有方案创建环境。uv、venv、Conda 以及 Mac/Ubuntu 分别重建环境的完整方法见[Mac 与 Ubuntu 为什么必须分别创建环境](05-Mac与Ubuntu分别创建环境.md)。这里先确认当前解释器：

```bash
cd ~/projects/my-project
python --version
python -c 'import sys; print(sys.executable)'
python -m pip --version
```

PyTorch 安装命令从当前 `Start Locally` 选择器生成，明确 Linux、包管理器、Python 和目标 CUDA 构建。安装完成后在同一个解释器中查看元数据：

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

`sys.executable` 表示真实解释器，`torch.version.cuda` 表示当前 torch 构建关联的 Runtime，`torch.cuda.is_available()` 才回答这个进程能否使用 CUDA。`torch.version.cuda` 为 `None` 时通常是 CPU 构建。

## 4. 用真实运算和项目短任务完成验证

`torch.cuda.is_available()` 返回 `True` 后运行最小矩阵乘法：

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

另一个终端观察：

```bash
watch -n 1 nvidia-smi
```

这一步证明当前解释器、torch 构建、驱动和 GPU 至少完成一次真实运算。随后运行项目级短任务：

```bash
python train.py --help
python train.py --max-steps 2
```

短任务应覆盖真实数据加载和模型入口，同时把输出写入独立练习目录。正式长训练不适合用来验证一行配置是否正确。

Mac 上的 CPU/MPS 冒烟测试能够发现通用 Python 错误，却不能代替 Ubuntu CUDA 结果。GPU 容器也依赖宿主机驱动与 NVIDIA Container Toolkit，具体链路见[GPU 容器与权限边界](../Part-08-Docker/04-GPU容器与权限边界.md)。

## 5. 失败时沿同一条链定位

```bash
# 1. 硬件和驱动
lspci | grep -i nvidia
nvidia-smi

# 2. 当前解释器
which python
python -c 'import sys; print(sys.executable)'
python -m pip --version

# 3. PyTorch 来源与构建
python -m pip show torch
python -c 'import torch; print(torch.__version__); print(torch.version.cuda)'

# 4. 当前进程能否使用 CUDA
python -c 'import torch; print(torch.cuda.is_available())'

# 5. 真实 GPU 运算
# 运行上一节矩阵乘法

# 6. 项目短任务
python train.py --help
python train.py --max-steps 2

# 7. 只有编译扩展时检查 Toolkit
nvcc --version
echo "$CUDA_HOME"
```

常见现象：

- `torch.cuda.is_available()` 为 `False`：先看 `nvidia-smi`、解释器和 torch 是否为 CPU 构建，也检查容器设备授权与隐藏 GPU 的环境变量。
- `CUDA driver version is insufficient`：驱动通常无法支持当前 PyTorch Runtime，应按受支持路径更新驱动，而不是同时随机降级多个包。
- `CUDA out of memory`：GPU 已经可用，问题转为显存；检查遗留进程，并调整 batch、序列长度、梯度累积、混合精度、梯度检查点或模型大小。
- `no kernel image is available`：当前构建可能不包含这张 GPU 的架构，或自定义扩展编译目标不匹配，需要核对 Compute Capability。
- 动态库冲突：查看 Shell 是否叠加多套 `CUDA_HOME`、`PATH` 和 `LD_LIBRARY_PATH`，再确定项目实际需要哪一套。

重要实验应记录机器、系统、解释器、torch 构建、`nvidia-smi`、项目提交、测试和退出状态。完整运行目录与 checkpoint 证据见[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)，不在本章重新复制一套记录模板。

最终验收顺序是：PCI 设备可见，`nvidia-smi` 成功，项目解释器正确，torch 能导入，Runtime 信息合理，`torch.cuda.is_available()` 为 `True`，最小矩阵运算成功，项目短任务成功。每一步都对应一层，失败时回到该层处理。

继续阅读：[Mac 与 Ubuntu 分别创建环境](05-Mac与Ubuntu分别创建环境.md)、[GPU 容器与权限边界](../Part-08-Docker/04-GPU容器与权限边界.md)和[实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)。

官方参考：[PyTorch Start Locally](https://pytorch.org/get-started/locally/)。