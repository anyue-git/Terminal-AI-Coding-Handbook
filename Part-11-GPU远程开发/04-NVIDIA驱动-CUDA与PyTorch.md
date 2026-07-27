# 04 NVIDIA 驱动、CUDA 与 PyTorch

机器学习新手很容易把下面几层混成“CUDA”：

```text
NVIDIA GPU
→ NVIDIA 驱动
→ CUDA 用户态运行库
→ PyTorch
→ 项目代码
```

任何一层出问题，都可能表现成“GPU 用不了”，但修复方法完全不同。不要遇到错误就把驱动、Toolkit 和 PyTorch 全部重装一遍。

---

## 1. `nvidia-smi` 主要检查驱动层

Ubuntu：

```bash
nvidia-smi
```

它通常显示：

- GPU 型号；
- 驱动版本；
- 显存使用；
- 温度和功耗；
- 当前 GPU 进程；
- 驱动能够支持的 CUDA 兼容上限提示。

其中显示的 `CUDA Version` 不等于：

- 已安装对应版本的 CUDA Toolkit；
- 本机一定存在 `nvcc`；
- 当前 PyTorch 正在使用该版本；
- 项目一定可以正常训练。

如果 `nvidia-smi` 本身失败，先解决驱动层，不要先重装 Python 包。

---

## 2. `nvcc` 属于 CUDA Toolkit

检查：

```bash
nvcc --version
```

CUDA Toolkit 主要提供：

- `nvcc` 编译器；
- CUDA C/C++ 头文件和开发库；
- 调试与分析工具；
- 编译自定义 CUDA 扩展所需组件。

没有 `nvcc` 不代表 PyTorch 一定不能使用 GPU。预编译 PyTorch wheel 通常会携带所需的 CUDA 用户态运行库。

更可能需要系统 Toolkit 的场景：

- 编译自定义 CUDA 扩展；
- 开发 CUDA C/C++；
- 安装必须本地编译的包；
- 项目文档明确要求。

---

## 3. PyTorch 自己报告什么

必须在项目实际使用的 Python 环境中运行：

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
    print("device:", torch.cuda.get_device_name(0))
PY
```

含义：

```text
torch.__version__
→ PyTorch 版本

torch.version.cuda
→ 该 PyTorch 构建关联的 CUDA 运行时版本

torch.cuda.is_available()
→ 当前环境是否真的能使用 CUDA
```

如果 `torch.version.cuda` 是 `None`，通常安装的是 CPU 构建。

---

## 4. 安装 PyTorch 时只使用当前官方选择器

PyTorch 的稳定版本、Python 支持范围和 CUDA wheel 会持续变化。不要从旧博客复制固定安装命令。

使用官方 Start Locally 页面，根据以下条件生成命令：

- 操作系统；
- 包管理器；
- Python 版本；
- CPU 或 CUDA；
- 当前官方提供的构建。

推荐流程：

```text
确认 NVIDIA 驱动正常
→ 创建项目 Python 环境
→ 使用 PyTorch 官方选择器安装
→ 在同一解释器中验证 torch.cuda.is_available()
```

使用 Conda 创建环境，不代表必须从旧的 PyTorch Conda Channel 安装。当前新版本应以 PyTorch 官方页面的实际推荐为准。

---

## 5. 驱动和 PyTorch wheel 的关系

基本原则：

```text
宿主机 NVIDIA 驱动
必须足够新
才能支持 PyTorch wheel 携带的 CUDA Runtime
```

下面这种版本不同不一定是错误：

```text
nvidia-smi 显示的兼容版本
≠ 系统 nvcc 版本
≠ torch.version.cuda
```

它们描述的是不同层。

驱动过旧时可能出现：

- CUDA 初始化失败；
- 驱动版本不足；
- 动态库加载失败；
- 容器无法访问 GPU。

---

## 6. 推荐排错顺序

### 第一步：驱动

```bash
nvidia-smi
```

### 第二步：解释器

```bash
which python
python -c 'import sys; print(sys.executable)'
```

### 第三步：PyTorch 来源

```bash
python -m pip show torch
python -c 'import torch; print(torch.__version__); print(torch.version.cuda)'
```

### 第四步：实际 CUDA 可用性

```bash
python -c 'import torch; print(torch.cuda.is_available())'
```

### 第五步：需要编译扩展时才检查 Toolkit

```bash
nvcc --version
```

按层检查能保留证据。一次性重装全部组件，反而更难知道原问题在哪里。

---

## 7. 不要混用过多安装来源

容易出问题的组合：

```text
apt 装一套 CUDA
NVIDIA 仓库再装一套 Toolkit
Conda 再装一套运行库
pip 安装另一种 CUDA 构建的 PyTorch
PATH 和 LD_LIBRARY_PATH 仍指向旧目录
```

建议：

- 驱动遵循 Ubuntu 或 NVIDIA 官方流程；
- PyTorch 遵循 PyTorch 官方选择器；
- 系统 Toolkit 只在项目确实需要时安装；
- 每个项目使用独立 Python 环境；
- 不随手向 Shell 配置追加多套 CUDA 路径。

---

## 8. 显存不足不是驱动坏了

错误：

```text
CUDA out of memory
```

通常说明 GPU 已经可用，只是任务超过当前可用显存。

常见处理：

- 减小 batch size；
- 缩短序列；
- 使用梯度累积；
- 使用混合精度；
- 使用梯度检查点；
- 更换较小模型；
- 结束自己确认无用的 GPU 进程。

查看：

```bash
watch -n 1 nvidia-smi
```

不要终止不属于自己的进程，也不要误杀桌面环境需要的图形进程。

---

## 9. Mac 的 MPS 不能代替 Ubuntu CUDA 验证

Apple Silicon Mac 常见设备：

```text
cpu
mps
```

Ubuntu NVIDIA 游戏本常见设备：

```text
cpu
cuda
```

检查 MPS：

```bash
python -c 'import torch; print(torch.backends.mps.is_available())'
```

通用设备选择示例：

```python
import torch

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
```

MPS 和 CUDA 的算子支持、性能、内存和数值行为可能不同。Mac 冒烟测试不能替代 Ubuntu CUDA 正式验证。

---

## 10. GPU 容器仍依赖宿主机驱动

```text
Ubuntu 宿主机驱动
→ NVIDIA Container Toolkit
→ 容器中的 CUDA / PyTorch 用户态环境
→ 项目代码
```

宿主机先检查：

```bash
nvidia-smi
nvidia-ctk --version
```

宿主机驱动失败时，重建容器通常没有意义。容器中的 CUDA Runtime 可以不同于宿主机 Toolkit，但仍要满足驱动兼容条件。

详细内容见：[GPU 容器与权限边界](../Part-08-Docker/04-GPU容器与权限边界.md)。

---

## 11. 保存环境证据

每个重要实验至少保存：

```bash
{
  date -Is
  hostname
  python --version
  python -c 'import sys; print(sys.executable)'
  python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
  nvidia-smi
} > environment.txt 2>&1
```

不要默认保存完整环境变量，其中可能包含 API Key、Token 和私有地址。

继续阅读：

- [Mac 与 Ubuntu 分别创建环境](05-Mac与Ubuntu分别创建环境.md)
- [实验日志与 Checkpoint 管理](08-实验日志与Checkpoint管理.md)

官方参考：

- [PyTorch：Start Locally](https://pytorch.org/get-started/locally/)
- [NVIDIA：CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/)
