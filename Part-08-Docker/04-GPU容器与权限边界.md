# 04 GPU 容器与权限边界

在 Ubuntu 游戏本上使用 Docker 跑 GPU 任务，需要同时满足三层条件：

```text
宿主机 NVIDIA 驱动正常
→ NVIDIA Container Toolkit 把 GPU 交给容器运行时
→ 容器中的框架识别 CUDA
```

Docker 不会自动让容器获得 GPU，也不会替代 NVIDIA 驱动。

---

## 1. 先验证宿主机，不要从容器开始猜

在 Ubuntu 宿主机运行：

```bash
nvidia-smi
```

如果失败，先处理驱动、内核模块或硬件识别。重建镜像、重装 PyTorch 或改 Compose 文件都不会修好宿主机驱动。

继续确认 Docker：

```bash
docker version
docker info
```

两层都正常后，才进入容器 GPU 排查。

---

## 2. NVIDIA Container Toolkit 是什么

它负责让 Docker 等容器运行时：

- 请求 GPU 设备；
- 注入宿主机驱动库；
- 设置 NVIDIA 运行时配置；
- 控制哪些 GPU 对容器可见；
- 使用 CDI 等设备描述机制。

它不是：

- NVIDIA 驱动；
- CUDA Toolkit；
- PyTorch；
- 容器镜像。

分层关系：

```text
宿主机驱动
→ 控制硬件

NVIDIA Container Toolkit
→ 连接容器运行时与 GPU

容器镜像
→ 提供框架和用户态 CUDA 依赖
```

---

## 3. 安装与配置遵循 NVIDIA 当前官方文档

NVIDIA Container Toolkit 更新较快，不在手册中长期固定仓库命令和补丁版本。

安装后检查：

```bash
nvidia-ctk --version
```

为 Docker 配置运行时的常见官方命令是：

```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

它可能修改：

```text
/etc/docker/daemon.json
```

修改前先查看：

```bash
sudo cat /etc/docker/daemon.json 2>/dev/null || true
docker ps
```

然后按官方说明重启 Docker：

```bash
sudo systemctl restart docker
```

重启 daemon 可能影响正在运行的容器。不要在重要训练进行中直接操作。

---

## 4. 先运行最小 GPU 容器测试

使用 NVIDIA 官方文档当前提供的测试镜像和命令。核心形式通常是：

```bash
docker run --rm --gpus all NVIDIA_CUDA_IMAGE nvidia-smi
```

`NVIDIA_CUDA_IMAGE` 必须替换为官方文档当前有效的镜像标签。

测试成功只能证明：

```text
Docker
→ 能把 GPU 提供给这个测试容器
```

还不能证明你的 PyTorch 镜像、项目依赖和训练代码正确。

---

## 5. 在 PyTorch 容器中继续验证

进入目标镜像后检查：

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("build_cuda:", torch.version.cuda)
print("available:", torch.cuda.is_available())
print("count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY
```

排查顺序：

```text
宿主机 nvidia-smi
→ Docker daemon
→ NVIDIA Container Toolkit
→ 容器能否运行 nvidia-smi
→ Python 解释器
→ torch 构建信息
→ torch.cuda.is_available()
→ 项目代码设备选择
```

不要看到容器中 `torch.cuda.is_available()` 为假，就直接重装宿主机驱动。

---

## 6. `--gpus all` 会暴露全部 GPU

```bash
docker run --gpus all ...
```

表示容器可以看见所有允许的 NVIDIA GPU。

多 GPU 环境可以限定设备，具体语法应查看当前 Docker 与 NVIDIA 文档。

还可以在应用层使用：

```text
CUDA_VISIBLE_DEVICES
```

但应用层变量和容器设备授权不是同一层。真正的最小权限应尽量在容器启动时只提供需要的设备。

---

## 7. Compose 中声明 GPU

Compose 对 GPU 设备的声明方式会随规范和运行时能力演进。实际使用前先查看当前 Compose GPU 文档，并运行：

```bash
docker compose config
```

一个项目应明确：

- 哪个服务需要 GPU；
- 需要多少个设备；
- 是否允许访问全部 GPU；
- CPU 环境下是否有降级路径；
- 容器镜像使用什么框架构建；
- 如何执行最小 GPU 测试。

不要为了让一个训练服务工作，就把数据库、Web 服务和调试工具也全部授予 GPU。

---

## 8. 宿主机 Toolkit 与容器 Runtime 可以不同

容器镜像通常携带自己的用户态 CUDA Runtime 和框架依赖。宿主机最关键的是：

```text
NVIDIA 驱动足够新
→ 能支持容器需要的 CUDA Runtime
```

所以以下数字不必完全一致：

```text
宿主机 nvcc 版本
容器 CUDA Runtime
PyTorch 构建 CUDA 版本
nvidia-smi 显示的兼容版本
```

它们属于不同层。不要为了追求数字看起来一致而安装多套 CUDA。

---

## 9. GPU 容器不等于安全沙箱

GPU 容器仍然共享宿主机内核，并可能获得高价值资源。

风险包括：

- 读取挂入容器的数据集和模型；
- 修改 Bind Mount 中的源码和结果；
- 使用全部显存，影响其他任务；
- 通过 Docker Socket 控制宿主机容器；
- 读取注入的 API Key；
- 运行来源不明的模型代码；
- 通过网络上传项目内容。

尤其不要组合：

```text
来源不明镜像
+ Docker Socket
+ 整个 HOME 挂载
+ 全部 GPU
+ 真实云凭据
```

这不是开发便利配置，而是把多个高权限入口同时交出去。

---

## 10. 不要默认使用特权容器

高风险参数包括：

- `--privileged`；
- 挂载 `/var/run/docker.sock`；
- 挂载宿主机根目录；
- Host Network；
- 额外设备和 Capabilities；
- 以 root 写入共享项目目录。

GPU 支持本身通常不要求把容器设为完全特权。遇到权限问题时，应找出具体缺少哪项能力，而不是直接打开所有权限。

---

## 11. 文件权限与用户身份

容器以 root 写入 Bind Mount 时，宿主机可能出现 root 所有的文件。

检查：

```bash
ls -ln PROJECT_PATH
id
```

镜像可以创建非 root 用户，运行时也可以指定用户。具体 UID/GID 策略应结合镜像和宿主机设计。

不要让 AI 为了“修权限”递归修改整个项目、用户主目录或数据盘的所有权。

---

## 12. 显存不足不是容器运行时坏了

出现：

```text
CUDA out of memory
```

通常说明 GPU 已经能够使用，只是任务需求超过当前可用显存。

检查：

```bash
nvidia-smi
docker stats
```

处理方向可能包括：

- 减小 batch size；
- 缩短序列；
- 梯度累积；
- 混合精度；
- 梯度检查点；
- 更小模型；
- 结束自己确认无用的进程。

不要停止不属于自己的 GPU 进程，也不要把重装驱动当作显存清理方法。

---

## 13. GPU 容器的可复现记录

每次重要实验至少记录：

```bash
nvidia-smi > host-nvidia-smi.txt
docker version > docker-version.txt
docker image inspect IMAGE_NAME > image-inspect.json
```

还应保存：

- 镜像名称和 digest；
- Dockerfile；
- Compose 文件；
- Git 提交；
- 启动命令；
- GPU 设备范围；
- PyTorch 与 CUDA 构建信息；
- 测试结果。

只保存一个可变镜像标签，不能保证未来拉取到同样内容。

---

## 14. 给 AI CLI 的 GPU 容器约束

```text
当前阶段只读分析，不要修改驱动、Docker daemon 或 NVIDIA Container Toolkit。

请按层检查：
1. 宿主机 nvidia-smi；
2. Docker daemon；
3. nvidia-ctk；
4. 最小 GPU 容器；
5. 目标镜像中的 PyTorch；
6. 项目代码的设备选择。

不要使用 --privileged。
不要挂载 Docker Socket、整个 HOME、SSH 或云凭据目录。
不要停止其他 GPU 进程。
需要重启 Docker 或修改 /etc/docker/daemon.json 时，先说明影响并等待确认。
```

继续阅读：

- [NVIDIA 驱动、CUDA 与 PyTorch](../Part-11-GPU远程开发/04-NVIDIA驱动-CUDA与PyTorch.md)
- [Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)

官方参考：

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
- [Docker：GPU access](https://docs.docker.com/engine/containers/resource_constraints/#gpu)
- [Docker Compose：GPU support](https://docs.docker.com/compose/how-tos/gpu-support/)
