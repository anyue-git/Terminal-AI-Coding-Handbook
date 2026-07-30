# 04 GPU 容器与权限边界

Ubuntu 游戏本通过 Docker 运行 GPU 任务，需要一条连续链路：宿主机 NVIDIA 驱动能够工作，Docker CLI 连接正确 daemon，NVIDIA Container Toolkit 把设备交给容器，测试镜像能看到 GPU，目标框架能够完成 CUDA 运算，项目挂载与输出权限也符合预期。

```text
NVIDIA GPU 与宿主驱动
→ Docker Engine
→ NVIDIA Container Toolkit
→ CUDA 测试镜像
→ PyTorch 等框架镜像
→ 项目代码、数据与输出目录
```

“容器看不到 GPU”可能发生在任意一层。本章按这条链验证，同时说明设备授权、Compose、挂载、镜像来源和宿主权限。

## 1. 从宿主驱动和当前 Docker daemon 开始

这组命令在 **Ubuntu 游戏本**执行：

```bash
hostname
whoami
pwd
uname -a
uname -m
nvidia-smi
docker context show
docker version
docker info --format 'name={{.Name}} arch={{.Architecture}}'
```

Apple Silicon Mac 的 Docker Desktop 可以运行 Linux CPU 容器，但没有 NVIDIA 驱动和 CUDA GPU，本章的 CUDA 验证不能在 Mac 上替代完成。

`nvidia-smi` 成功通常会显示 GPU、驱动、显存和当前进程。失败时先处理硬件识别、内核模块、驱动或 Secure Boot：

```bash
ls -l /dev/nvidia* 2>/dev/null || true
lsmod | grep '^nvidia' || true
```

驱动来源应遵循 Ubuntu 与 NVIDIA 当前支持方案，避免发行版包、旧 PPA 和 `.run` 安装器互相覆盖。容器框架主要依赖宿主驱动的兼容能力，宿主机不一定需要安装完整 CUDA Toolkit 或 `nvcc`。

驱动正常后再确认普通 Docker：

```bash
docker ps
systemctl is-active docker
sudo journalctl -u docker --no-pager -n 100
```

普通容器都无法运行时，问题仍在 Engine、Context、磁盘或 Socket 权限。Ubuntu 同时存在 Docker Desktop for Linux 与本机 Engine 时，`docker context show` 尤其重要，因为 Toolkit 可能配置给一个 daemon，而 CLI 正在连接另一个。

## 2. 把 NVIDIA Container Toolkit 接到 Docker

Toolkit 负责将 GPU 设备与宿主驱动库接入容器，不等同于内核驱动、CUDA Toolkit、PyTorch 或项目依赖。先查看版本：

```bash
nvidia-ctk --version
```

未安装时，按 NVIDIA 当前官方仓库说明安装。常见 Docker Runtime 配置命令是：

```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

它可能修改 `/etc/docker/daemon.json`。保留原配置和当前容器清单：

```bash
sudo test -f /etc/docker/daemon.json \
  && sudo cp /etc/docker/daemon.json \
     /etc/docker/daemon.json.before-nvidia
sudo cat /etc/docker/daemon.json 2>/dev/null || true
docker ps
```

配置完成后重启 daemon 并重新检查：

```bash
sudo systemctl restart docker
systemctl is-active docker
docker version
docker info
```

重启会影响当前 daemon 管理的容器，应选择没有重要数据库或训练任务运行的时间。Rootless Docker 使用不同的 daemon 和配置路径，需要遵循对应文档。

## 3. 先测设备接入，再测目标框架

从 NVIDIA 当前镜像目录选择明确且存在的测试镜像：

```bash
docker run --rm --gpus all \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi

printf 'exit=%s\n' "$?"
```

这一步成功，说明当前 Docker daemon 已能把 NVIDIA GPU 与驱动能力交给测试容器；项目使用的 Python、PyTorch 和训练代码仍要继续验证。

多 GPU 主机先查看索引和 UUID：

```bash
nvidia-smi --query-gpu=index,uuid,name --format=csv
```

限制数量或设备：

```bash
docker run --rm --gpus 1 \
  NVIDIA_CUDA_IMAGE nvidia-smi

docker run --rm \
  --gpus '"device=0"' \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi
```

`--gpus` 控制容器启动时获得哪些设备，`CUDA_VISIBLE_DEVICES` 则影响应用层可见性。共享服务器上优先在容器授权层限制设备，而不是先给出全部 GPU 再依赖应用自律。纯计算任务通常只需要 compute 与 utility 能力；graphics、display 和 video 根据实际程序再增加。自定义 `NVIDIA_VISIBLE_DEVICES` 或 `NVIDIA_DRIVER_CAPABILITIES` 时，应记录原因并验证应用需要的功能。

测试镜像通过后，验证项目采用的框架镜像：

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

如果测试容器的 `nvidia-smi` 正常，而框架返回 `False`，检查镜像是否包含 CUDA 构建、启动时是否请求 GPU、容器里的 Python 和 torch 来源是否正确。宿主 `nvidia-smi` 显示的兼容上限、宿主 `nvcc`、容器 CUDA Runtime 和 `torch.version.cuda` 含义不同，不要求数字完全一致。

## 4. Compose 只给需要 GPU 的服务授权

一个最小 GPU 服务：

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

解析并运行：

```bash
docker compose config
docker compose run --rm gpu-check
```

`capabilities: [gpu]` 是设备声明的必要字段；`count` 限制数量，`device_ids` 指定具体设备，两者按当前 Compose 规范择一使用。数据库、Web、Redis 和文档服务通常不需要 GPU，授权应集中在训练、推理或 GPU 检查服务。

Mac 与 Ubuntu 可以共享 Dockerfile、基础 Compose 文件、训练代码、依赖声明和测试；GPU 设备声明更适合单独放入覆盖文件：

```text
compose.yaml
compose.gpu.yaml
```

Ubuntu 启动前先检查合并结果：

```bash
docker compose \
  -f compose.yaml \
  -f compose.gpu.yaml \
  config
```

这样 Mac 可以使用基础文件做 CPU 测试和结构验证，不会因为所有服务都无条件要求 NVIDIA GPU 而无法启动。多文件的合并顺序与项目名边界见[Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)。

Compose 验证仍沿同一条链：宿主 `nvidia-smi`、Docker daemon、Toolkit、测试镜像、框架镜像，最后才是项目命令。这样能够知道失败发生在哪一层，而不是同时重建镜像、升级驱动和修改 YAML。

## 5. 镜像来源、挂载和容器用户决定宿主影响

训练容器通常需要读取源码和数据，写入运行结果。可以把源码设为只读，并把输出集中到明确目录：

```bash
docker run --rm --gpus 1 \
  --mount type=bind,src="$PWD",dst=/workspace,readonly \
  --mount type=bind,src="$HOME/ml-runs",dst=/runs \
  -w /workspace \
  PYTORCH_IMAGE \
  python train.py --output /runs/experiment-001
```

数据集是否可写由任务决定。整个 HOME、`~/.ssh`、云凭据和 Docker Socket 不属于普通训练所需挂载；`--privileged` 或映射全部 `/dev` 也会把“使用一张 GPU”扩大成更广的宿主控制。

镜像和模型代码也属于执行来源。正式实验应优先使用可信组织维护、标签明确、Dockerfile 可审查的镜像，并记录 digest：

```bash
docker image inspect IMAGE_NAME \
  --format 'id={{.Id}} digests={{json .RepoDigests}}'
```

重要实验只记录可变标签，不能保证以后获得相同内容。模型仓库若要求启用远程自定义 Python 代码、安装任意依赖或执行陌生训练脚本，应按运行不可信代码处理，而不是仅当作下载权重。

Ubuntu 上以容器 root 写 Bind Mount，可能生成 root 所有文件。检查宿主与容器身份：

```bash
id
ls -ln "$HOME/ml-runs"

docker run --rm --gpus all \
  -v "$PWD:/work" \
  -w /work \
  PYTORCH_IMAGE \
  id
```

镜像可以建立普通用户，Compose 也可以设置 `user:` 或明确 UID/GID。输出目录的权限应在设计阶段解决，而不是训练结束后对整个项目、HOME 或数据盘递归 `sudo chown`。

删除容器不会自动删除 Bind Mount 中的宿主文件，但容器进程可以按挂载权限覆盖它们。Named Volume 同样不是备份。训练结果应落在独立 Run Directory 中，并从宿主检查日志、checkpoint、退出状态和文件所有权。

## 6. 按六层证据验收

完整检查可以整理为：

```bash
hostname
nvidia-smi
docker context show
docker version
nvidia-ctk --version

docker run --rm --gpus all \
  NVIDIA_CUDA_IMAGE \
  nvidia-smi

# 随后在目标框架镜像中验证 torch.cuda 和项目最小任务
```

最终记录宿主与驱动、Docker daemon、Toolkit、测试镜像、目标框架镜像及 digest、GPU 授权范围、项目命令、退出状态、挂载、容器用户和输出目录。六层连续通过，才能说明当前组合可用于 GPU 容器任务。实验日志、Git 快照、配置、随机种子、checkpoint 和恢复演练由[实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)统一记录。

让 AI CLI 协助排查时，可以先只读收集上述证据。重启 daemon、改写 `daemon.json`、停止其他容器、扩大设备权限、挂载凭据和删除 Volume 属于明确的系统变更，需要在知道当前运行任务与恢复方式后单独决定。

继续阅读：[Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)、[Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)和[NVIDIA 驱动、CUDA 与 PyTorch](../Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)。
