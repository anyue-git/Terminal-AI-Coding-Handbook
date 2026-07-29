# 04 GPU 容器与权限边界

在 Ubuntu 游戏本上使用 Docker 运行 GPU 任务，需要同时满足三层条件：宿主机 NVIDIA 驱动正常、NVIDIA Container Toolkit 已把 GPU 接入容器运行时、目标镜像中的框架能够识别 CUDA。任何一层失败，最终都可能表现为“容器看不到 GPU”，但修复位置完全不同。

本章按照固定顺序完成验证，并把 GPU 授权、Compose 配置、镜像选择、文件权限和安全边界放到同一个工作流中。

## 1. 先确认当前机器确实是 Ubuntu GPU 主机

在准备运行 GPU 容器的终端中先执行：

```bash
hostname
uname -a
uname -m
docker context show
```

不要在 Mac 的 Docker Desktop 中执行 NVIDIA CUDA 验证。Apple Silicon Mac 可以构建和运行 Linux CPU 容器，但没有 NVIDIA 驱动和 CUDA GPU。

如果通过 SSH 登录 Ubuntu，还应确认：

```bash
whoami
pwd
```

GPU 排查过程中可能需要重启 Docker daemon，必须先确认没有重要容器和训练任务正在运行。

## 2. 第一层：验证宿主机 NVIDIA 驱动

在 Ubuntu 宿主机运行：

```bash
nvidia-smi
```

成功输出通常包含：

```text
Driver Version
GPU 名称
显存使用
GPU 利用率
正在使用 GPU 的进程
```

如果 `nvidia-smi` 在宿主机失败，应先处理驱动、内核模块、Secure Boot 或硬件识别。此时：

- 重建 Docker 镜像没有作用；
- 重装容器中的 PyTorch没有作用；
- 修改 Compose GPU 字段没有作用；
- 容器无法替代宿主机驱动。

检查设备节点：

```bash
ls -l /dev/nvidia* 2>/dev/null || true
```

查看内核模块：

```bash
lsmod | grep '^nvidia' || true
```

驱动问题应结合 Ubuntu 和 NVIDIA 当前官方文档处理，不要同时混用发行版包、旧 PPA、CUDA runfile 和多个来源的驱动安装方式。

## 3. 第二层：确认 Docker daemon 正常

运行：

```bash
docker version
docker info
docker ps
```

如果普通容器都无法运行，先处理 Docker Engine 和 Socket 权限，不要跳到 NVIDIA Container Toolkit。

检查服务和日志：

```bash
systemctl is-active docker
sudo journalctl -u docker --no-pager -n 100
```

确认当前 Context：

```bash
docker context show
docker info --format 'name={{.Name}} arch={{.Architecture}}'
```

避免在 Ubuntu 同时安装 Docker Desktop for Linux 和 Docker Engine 后，误把 GPU 配置写给一套 daemon，却在另一套 Context 中运行命令。

## 4. NVIDIA Container Toolkit 负责哪一层

NVIDIA Container Toolkit 连接 Docker 与宿主机 GPU。它负责：

- 让容器请求指定 GPU；
- 注入宿主机驱动相关库；
- 设置 NVIDIA 容器运行时；
- 控制可见 GPU 和驱动能力；
- 支持 CDI 等设备描述方式。

它不是：

- NVIDIA 内核驱动；
- 宿主机 CUDA Toolkit；
- PyTorch；
- 训练项目依赖；
- CUDA 容器镜像。

分层关系：

```text
宿主机 NVIDIA 驱动
→ 控制真实硬件

NVIDIA Container Toolkit
→ 把设备和驱动能力交给容器运行时

容器镜像
→ 提供用户态 CUDA Runtime、框架和应用依赖
```

查看工具版本：

```bash
nvidia-ctk --version
```

如果命令不存在，应按 NVIDIA 当前官方安装指南配置仓库和软件包，不要从随机脚本下载二进制。

## 5. 配置 Docker Runtime 前先检查影响

NVIDIA 官方当前常用配置命令是：

```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

它会修改或创建：

```text
/etc/docker/daemon.json
```

执行前先保存现状：

```bash
sudo test -f /etc/docker/daemon.json \
  && sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.before-nvidia

sudo cat /etc/docker/daemon.json 2>/dev/null || true
docker ps
```

然后再运行配置命令。重启 Docker daemon：

```bash
sudo systemctl restart docker
```

重启可能中断正在运行的容器。不要在训练、数据库或其他重要服务运行时直接执行。

重启后确认：

```bash
systemctl is-active docker
docker version
docker info
```

Rootless Docker 使用不同配置路径和用户级 daemon。不要把普通 rootful Docker 的命令直接照搬到 Rootless 环境。

## 6. 第三层：运行最小 GPU 容器

先拉取一个明确版本的 NVIDIA CUDA 基础镜像。实际标签应从 NVIDIA 当前镜像目录或官方文档选择，不要长期依赖模糊的 `latest`。

命令结构：

```bash
docker run --rm --gpus all \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi
```

例如把 `NVIDIA_CUDA_IMAGE` 替换成当前存在且适合本机驱动的 `nvidia/cuda:VERSION-base-ubuntuVERSION` 镜像。

成功只能证明：

```text
当前 Docker daemon
→ 能把 NVIDIA GPU 和所需驱动能力交给这个测试容器
```

它还不能证明：

- 你的 PyTorch 镜像正确；
- 训练依赖已安装；
- 项目代码选择了 CUDA；
- 显存足够；
- 数据和文件权限正确。

测试后查看退出状态：

```bash
printf 'exit=%s\n' "$?"
```

## 7. 只授权需要的 GPU

`--gpus all` 会让容器看到全部可用 NVIDIA GPU。单 GPU 游戏本中通常只有一张卡，但多 GPU 机器上应尽量限制范围。

查看 GPU 索引和 UUID：

```bash
nvidia-smi --query-gpu=index,uuid,name --format=csv
```

指定数量：

```bash
docker run --rm --gpus 1 \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi
```

指定设备时，Docker CLI 的引号语法容易写错，应按当前 NVIDIA 文档使用：

```bash
docker run --rm \
  --gpus '"device=0"' \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi
```

也可以通过 GPU UUID 选择设备。设备索引可能随环境变化，长期调度时 UUID 更稳定。

`CUDA_VISIBLE_DEVICES` 属于应用层设备可见性；Docker `--gpus` 属于容器设备授权。最小权限应优先在容器启动时限制设备，而不是把所有 GPU 交给容器后只依赖应用变量。

## 8. 驱动能力也可以限制

NVIDIA Runtime 可以控制注入哪些驱动能力。常见能力包括：

```text
compute
→ CUDA 和 OpenCL 计算

utility
→ nvidia-smi 和 NVML

video
→ 视频编解码

graphics
→ OpenGL 和 Vulkan

display
→ X11 显示
```

纯计算任务通常只需要 `compute` 和 `utility`。不要默认授予所有图形、显示和视频能力。

NVIDIA 官方 CUDA 基础镜像通常已经设置合理的 `NVIDIA_VISIBLE_DEVICES` 和 `NVIDIA_DRIVER_CAPABILITIES` 默认值。自定义时应记录原因，并验证应用需要的功能。

## 9. 在目标 PyTorch 镜像中继续验证

最小 CUDA 容器通过后，再进入项目镜像检查 Python 框架：

```bash
docker run --rm --gpus all \
  PYTORCH_IMAGE \
  python - <<'PY'
import sys
import torch

print("python:", sys.executable)
print("torch:", torch.__version__)
print("torch build cuda:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
print("device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device 0:", torch.cuda.get_device_name(0))
PY
```

排查顺序应保持：

```text
宿主机 nvidia-smi
→ Docker daemon
→ NVIDIA Container Toolkit
→ CUDA 测试容器 nvidia-smi
→ 目标镜像 Python
→ PyTorch 构建信息
→ torch.cuda.is_available()
→ 项目设备选择逻辑
```

不要看到 `torch.cuda.is_available()` 为假就直接重装宿主机驱动。可能是目标镜像安装了 CPU 版 PyTorch、当前 Python 不是预期环境，或者容器启动时没有请求 GPU。

## 10. 宿主机 CUDA 与容器 CUDA 不必数字完全一致

容器镜像通常自带用户态 CUDA Runtime 和框架依赖。宿主机最关键的是 NVIDIA 驱动是否足够新，能够支持容器要求的 CUDA Runtime。

以下数字属于不同层：

```text
nvidia-smi 显示的 CUDA 兼容上限
宿主机 nvcc 版本
容器 CUDA Runtime 版本
PyTorch 构建使用的 CUDA 版本
```

它们不要求逐字相同。宿主机甚至可以没有 `nvcc`，容器中的 PyTorch 仍可能正常使用 GPU。

不要为了让数字看起来一致，在宿主机安装多套 CUDA Toolkit。应根据目标框架、容器镜像和驱动兼容要求判断。

## 11. 用 Compose 声明 GPU

建立一个 GPU 验证目录：

```bash
mkdir -p ~/terminal-practice/compose-gpu
cd ~/terminal-practice/compose-gpu
```

创建 `compose.yaml`，把镜像标签替换为当前有效版本：

```yaml
services:
  gpu-check:
    image: NVIDIA_CUDA_IMAGE
    command: nvidia-smi
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

先解析：

```bash
docker compose config
```

然后运行一次：

```bash
docker compose run --rm gpu-check
```

Compose GPU reservation 中：

- `capabilities: [gpu]` 是必填项；
- `count` 可以限制数量；
- `device_ids` 可以指定宿主机设备；
- `count` 与 `device_ids` 不能同时使用。

项目中只给需要 GPU 的训练或推理服务声明设备。数据库、Web、Redis 和文档服务通常不需要 GPU。

## 12. 为 CPU 和 GPU 路径建立明确分工

Mac 与 Ubuntu 可以共享：

- Dockerfile；
- Compose 基础文件；
- Python 依赖声明；
- 训练代码；
- 测试；
- Git 提交。

Mac 负责：

```text
构建基本镜像
CPU 单元测试
Compose 结构验证
非 CUDA 代码路径
```

Ubuntu GPU 主机负责：

```text
宿主机驱动验证
NVIDIA Container Toolkit
GPU 容器测试
CUDA 框架验证
显存和性能测试
```

可以使用两份 Compose 文件：

```text
compose.yaml
compose.gpu.yaml
```

启动前先合并检查：

```bash
docker compose \
  -f compose.yaml \
  -f compose.gpu.yaml \
  config
```

不要在基础文件中给所有服务无条件加入 GPU，使 Mac 开发环境无法启动。

## 13. GPU 容器仍然不是安全沙箱

GPU 容器共享宿主机 Linux 内核，并可能接触高价值资源。风险包括：

- 读取挂载的数据集、模型和源码；
- 修改 Bind Mount 中的文件；
- 占满显存或计算资源；
- 使用注入的 API Key；
- 访问网络并上传内容；
- 加载来源不明的模型自定义代码；
- 通过 Docker Socket控制其他容器和宿主机。

尤其不要组合：

```text
来源不明镜像
+ --privileged
+ Docker Socket
+ 整个 HOME 挂载
+ 全部 GPU
+ 真实云凭据
```

GPU 支持本身通常不要求 `--privileged`。遇到权限错误时，应找出具体缺少的设备、目录或 Capability，而不是打开全部权限。

## 14. 镜像与模型代码都要审查

拉取镜像后记录来源和 digest：

```bash
docker image inspect IMAGE_NAME \
  --format 'id={{.Id}} digests={{json .RepoDigests}}'
```

尽量使用：

- 官方或可信组织镜像；
- 明确版本标签；
- 可审查 Dockerfile；
- 固定 digest 的重要实验；
- 经过漏洞和许可证检查的依赖。

机器学习项目中的模型仓库可能包含自定义 Python 代码。启用远程代码执行、安装任意仓库依赖或运行陌生训练脚本，都应视为执行不可信代码，而不只是“下载模型”。

## 15. Bind Mount 和文件权限

容器默认可能以 root 写入宿主机项目目录。检查：

```bash
id
ls -ln PROJECT_PATH
```

在容器内检查：

```bash
docker run --rm --gpus all \
  -v "$PWD:/work" \
  -w /work \
  PYTORCH_IMAGE \
  id
```

镜像可以创建非 root 用户，Compose 也可以设置 `user:`。UID/GID 策略应与宿主机目录和团队工作流统一。

不要让 AI 为修一个权限错误而递归修改整个用户主目录、数据盘或模型目录的所有权。

## 16. CUDA OOM 说明 GPU 通常已经可用

出现：

```text
CUDA out of memory
```

通常表示框架已经成功访问 GPU，只是任务需要的显存超过当前可用量。

检查：

```bash
nvidia-smi
docker stats
```

处理方向可能包括：

- 减小 batch size；
- 缩短序列长度；
- 使用梯度累积；
- 使用混合精度；
- 启用梯度检查点；
- 使用更小模型；
- 停止自己确认无用的任务。

不要停止其他用户的 GPU 进程，也不要把重装驱动当作“清显存”方法。

## 17. 重要实验应保存可复现记录

为每次正式运行建立实验目录，记录：

```bash
mkdir -p run-metadata
nvidia-smi > run-metadata/host-nvidia-smi.txt
docker version > run-metadata/docker-version.txt
docker info > run-metadata/docker-info.txt
git rev-parse HEAD > run-metadata/git-commit.txt
```

保存镜像信息：

```bash
docker image inspect IMAGE_NAME > run-metadata/image-inspect.json
```

容器内保存框架信息：

```bash
python - <<'PY' > run-metadata/framework.txt
import platform
import torch
print("platform:", platform.platform())
print("torch:", torch.__version__)
print("cuda build:", torch.version.cuda)
print("available:", torch.cuda.is_available())
PY
```

还应记录：

- 镜像名称和 digest；
- Dockerfile 和 Compose 文件；
- 启动命令；
- GPU 设备范围；
- Python 环境和锁文件；
- 数据版本；
- 随机种子；
- 日志和 checkpoint；
- 测试结果。

只保存一个可变镜像标签，不能保证以后拉取到完全相同内容。

## 18. 固定故障排查表

宿主机层：

```bash
hostname
nvidia-smi
lsmod | grep '^nvidia' || true
```

Docker 层：

```bash
docker context show
docker version
docker info
systemctl is-active docker
```

Toolkit 层：

```bash
nvidia-ctk --version
sudo cat /etc/docker/daemon.json 2>/dev/null || true
sudo journalctl -u docker --no-pager -n 100
```

最小容器层：

```bash
docker run --rm --gpus all NVIDIA_CUDA_IMAGE nvidia-smi
```

框架层：

```bash
python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())'
```

应用层再检查设备选择、batch size、数据类型、分布式配置和显存占用。

## 19. 给 AI CLI 的 GPU 容器边界

```text
当前阶段只读，不要修改驱动、Docker daemon 或 NVIDIA Container Toolkit。

按顺序检查：
1. 宿主机 nvidia-smi；
2. Docker Context 和 daemon；
3. nvidia-ctk；
4. 最小 CUDA 容器；
5. 目标镜像中的 Python 和 PyTorch；
6. 项目代码的设备选择。

不要使用 --privileged。
不要挂载 Docker Socket、整个 HOME、SSH、云凭据或无关数据目录。
不要停止其他 GPU 进程。
不要自动重启 Docker daemon。

需要修改 /etc/docker/daemon.json、安装驱动、安装 Toolkit 或重启服务时，先说明当前状态、影响范围、备份、验证和回滚方式，等待确认。
```

继续阅读：

- [NVIDIA 驱动、CUDA 与 PyTorch](../Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)
- [Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)

官方参考：

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
- [NVIDIA Container Toolkit installation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [NVIDIA Docker specialized configurations](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html)
- [Docker GPU access](https://docs.docker.com/engine/containers/resource_constraints/#gpu)
- [Docker Compose GPU support](https://docs.docker.com/compose/how-tos/gpu-support/)
