# 02 Docker Desktop 与 Ubuntu Docker Engine

Mac 和 Ubuntu 都可以执行 `docker`，但同一条命令背后的运行结构并不相同。Mac 上的 Linux 容器运行在 Docker Desktop 管理的 Linux 虚拟机中；Ubuntu 游戏本通常直接运行本机 Docker Engine。理解这一区别，才能解释为什么两台机器的文件挂载、CPU 架构、数据位置、网络路径和 GPU 能力不一样。

本章通过同一个检查流程，分别识别 Mac 和 Ubuntu 上的 Docker 客户端、服务端、Context、架构和数据边界。

## 1. `docker` 命令只是客户端入口

先在当前终端运行：

```bash
docker version
docker context show
docker context ls
docker info
```

`docker version` 通常分成 Client 和 Server 两部分：

```text
Client
→ 当前终端调用的 Docker CLI

Server
→ 当前 Context 指向的 Docker daemon
```

如果 Client 能显示版本，而 Server 报错，并不说明 Docker CLI 没装好。常见原因是：

- Docker Desktop 尚未启动；
- Ubuntu 的 Docker daemon 没运行；
- 当前用户无权访问 Docker Socket；
- `DOCKER_HOST` 指向错误地址；
- 当前 Docker Context 指向另一个 daemon；
- 远程 Docker 主机不可达。

先判断“客户端在连接谁”，再决定修安装、服务、权限还是网络。

## 2. Docker Context 决定当前操作目标

查看：

```bash
docker context ls
```

可能看到：

```text
NAME        DESCRIPTION                               DOCKER ENDPOINT
default *   Current DOCKER_HOST based configuration   unix:///var/run/docker.sock
```

星号表示当前 Context。还可以检查：

```bash
docker context inspect "$(docker context show)"
```

Context 保存 Docker endpoint、TLS 和其他连接信息。同一个 CLI 可以控制本机 daemon，也可以控制远程 daemon。因此在执行删除容器、清理镜像或停止服务前，应先确认：

```bash
hostname
docker context show
docker info --format 'name={{.Name}} os={{.OperatingSystem}} arch={{.Architecture}}'
```

不要只凭终端窗口标题判断操作对象。

环境变量也可能覆盖 Context：

```bash
env | grep '^DOCKER_' || true
```

如果设置了 `DOCKER_HOST`，CLI 的实际目标可能与预期不同。排错时要把 Context 和环境变量一起检查。

## 3. Mac 上实际运行的是 Linux 虚拟机

在 macOS 上，Docker Desktop 会运行一个轻量 Linux 虚拟机，Docker Engine 和 Linux 容器位于虚拟机内部：

```text
Mac Terminal
→ Docker CLI
→ Docker Desktop 后端
→ Linux VM
→ Docker Engine
→ Linux 容器
```

因此容器中运行的是 Linux 用户空间，而不是 macOS。进入容器查看：

```bash
docker run --rm alpine uname -a
```

即使宿主机是 Mac，输出仍会显示 Linux。

这带来几个直接结果：

- macOS 可执行文件不能直接放进 Linux 容器运行；
- Mac 目录通过文件共享层映射到 Linux VM，再进入容器；
- 容器中的 `localhost` 只指容器自己；
- 镜像、容器和 Volume 主要存放在 Docker Desktop 的虚拟磁盘中；
- CPU、内存、磁盘和虚拟机管理器受 Docker Desktop 设置影响。

检查 Docker Desktop 当前资源和磁盘使用：

```bash
docker info
docker system df
```

Finder 中看不到某个 Named Volume 的普通文件夹，不代表数据不存在。它可能位于 Docker Desktop 管理的虚拟磁盘中。

## 4. Ubuntu 上通常直接运行 Docker Engine

在 Ubuntu 游戏本上，常见结构是：

```text
Ubuntu Terminal
→ Docker CLI
→ 本机 dockerd
→ containerd
→ Linux 容器
```

检查服务：

```bash
systemctl is-active docker
systemctl status docker --no-pager
```

查看日志：

```bash
sudo journalctl -u docker --no-pager -n 100
```

确认 daemon Socket：

```bash
ls -l /var/run/docker.sock
```

如果服务没有启动，应先查看日志、配置和磁盘状态。不要把删除 `/var/lib/docker` 当作普通修复步骤，其中可能包含全部镜像、容器和 Volume 数据。

Ubuntu 也可以安装 Docker Desktop for Linux，但它会运行独立 VM，并创建 `desktop-linux` Context；该环境与本机 Docker Engine 的镜像和容器相互独立。个人 GPU 游戏本通常只需要 Docker Engine，不要在不理解 Context 的情况下同时维护两套运行时。

## 5. Docker Socket 是高权限控制入口

Ubuntu Docker Engine 常用：

```text
/var/run/docker.sock
```

拥有该 Socket 控制权的用户，通常可以启动容器并挂载宿主机目录、创建设备映射或调整高权限能力。加入 `docker` 组并不只是“以后不用 sudo”，而是获得接近 root 的 Docker 控制能力。

检查当前身份：

```bash
id
groups
ls -l /var/run/docker.sock
```

不要使用：

```bash
chmod 666 /var/run/docker.sock
```

这会让所有本机用户都能控制 daemon。也不要把 Socket 挂进来源不明的容器：

```text
/var/run/docker.sock
→ 不可信容器
```

一旦容器能调用 Docker API，它可能进一步控制其他容器和宿主机资源。

AI CLI 默认也不应获得 Docker Socket 控制权。需要运行 Docker 命令时，应限定项目、命令和数据范围，并逐项检查高风险参数。

## 6. 在两台机器上运行同一个识别实验

分别在 Mac 和 Ubuntu 执行：

```bash
printf 'host: '
hostname
printf 'host arch: '
uname -m
printf 'docker context: '
docker context show
printf 'docker server arch: '
docker info --format '{{.Architecture}}'
printf 'container os/arch: '
docker run --rm alpine sh -c 'uname -s; uname -m'
```

Apple Silicon Mac 常见：

```text
host arch: arm64
docker server arch: aarch64
container: Linux / aarch64
```

Ubuntu NVIDIA 游戏本常见：

```text
host arch: x86_64
docker server arch: x86_64
container: Linux / x86_64
```

具体输出可能使用 `arm64`、`aarch64`、`amd64` 或 `x86_64` 等不同名称，但核心问题是：两台机器是否原生使用同一架构。

## 7. 多架构镜像与模拟

查看镜像支持的平台：

```bash
docker buildx imagetools inspect alpine:latest
```

一个多架构标签可以针对不同平台指向不同镜像清单。Mac 拉取 arm64 版本，Ubuntu 游戏本拉取 amd64 版本，它们标签相同，但底层镜像 digest 可能不同。

可以显式请求平台：

```bash
docker run --rm --platform linux/amd64 alpine uname -m
```

在 arm64 Mac 上，这可能通过模拟运行 amd64 镜像。能够启动不代表性能和行为等同于真实 amd64 主机，尤其是编译、原生扩展、浏览器和高性能计算任务。

发布多架构镜像时，应使用 Buildx 与 CI 分别构建和测试目标平台。不要只在一台机器上模拟成功，就声称所有平台均已验证。

## 8. Bind Mount 的路径经过不同层次

建立练习目录：

```bash
mkdir -p ~/terminal-practice/docker-host-demo
cd ~/terminal-practice/docker-host-demo
printf 'created on host\n' > note.txt
```

运行：

```bash
docker run --rm \
  --mount type=bind,src="$PWD",dst=/work \
  -w /work \
  alpine \
  sh -c 'printf "container sees: "; cat note.txt; printf "created in container\n" > result.txt'
```

回到宿主机查看：

```bash
cat result.txt
ls -ln note.txt result.txt
```

在 Mac 上，路径经过：

```text
macOS 目录
→ Docker Desktop 文件共享
→ Linux VM
→ 容器
```

在 Ubuntu 上，路径更接近：

```text
Linux 宿主机目录
→ 容器
```

因此大量小文件、包缓存、Git 仓库扫描和文件监听在 Mac Bind Mount 中可能更慢。常见分工是：

- 源码放 Bind Mount，方便编辑；
- 数据库数据、依赖缓存和大量小文件放 Named Volume；
- 大型数据集避免放在持续文件监听的目录；
- 不把 Mac 的 `.venv` 或 `node_modules` 直接带入 Linux 容器。

## 9. 容器用户与宿主机文件权限

容器默认可能以 root 运行。Ubuntu 上，容器向 Bind Mount 写文件后，宿主机可能看到 root 所有文件：

```bash
ls -ln result.txt
```

不要用递归 `sudo chown` 整个项目作为常规补救。先确认容器用户：

```bash
docker run --rm alpine id
```

可以通过镜像中的 `USER`、Compose 的 `user:`，或者运行参数指定 UID/GID。具体策略要与镜像、团队和部署环境一致。

Docker Desktop 的容器 root 位于 Linux VM 中，不自动等同于 macOS host root；但被 Bind Mount 的宿主机文件仍是重要边界，容器可以按挂载权限读取或修改它们。

## 10. 端口映射与访问方向

运行一个临时 Web 服务：

```bash
docker run --rm \
  -p 127.0.0.1:18080:80 \
  nginx:alpine
```

在另一个终端访问：

```bash
curl http://127.0.0.1:18080
```

映射含义：

```text
宿主机 127.0.0.1:18080
→ 容器 80
```

绑定 `127.0.0.1` 表示只允许宿主机本地访问；写成 `18080:80` 通常会绑定所有宿主机接口，可能让局域网其他设备访问。

容器访问自己时使用 `localhost`；容器访问另一个 Compose 服务时应使用服务名；容器访问宿主机服务时，Docker Desktop 常用 `host.docker.internal`。Linux Docker Engine 的对应行为需要明确配置，不应假设所有平台完全一致。

## 11. 数据究竟位于哪里

需要区分五种位置：

```text
Git 仓库源码
→ 宿主机普通目录

Bind Mount
→ 宿主机明确路径

Named Volume
→ Docker 管理的数据区域

镜像层
→ 只读构建产物

容器可写层
→ 随容器删除而可能消失的运行状态
```

查看：

```bash
docker volume ls
docker volume inspect VOLUME_NAME
docker system df -v
```

Compose YAML 只描述 Volume，不等于备份了里面的数据。数据库应使用数据库自身的导出或经过验证的 Volume 备份方案。

## 12. Mac 与 Ubuntu 的 GPU 分工

Apple Silicon Mac 没有 NVIDIA CUDA。Mac 可以验证：

- Dockerfile 是否能够构建；
- CPU 执行路径；
- Compose 配置结构；
- 普通服务是否启动；
- 非 GPU 测试。

Ubuntu 游戏本负责验证：

- NVIDIA 驱动；
- NVIDIA Container Toolkit；
- GPU 设备授权；
- CUDA 框架；
- 显存和真实训练性能。

Mac 上构建镜像成功，不能写成“GPU 容器验证通过”。两台机器应共享 Dockerfile、Compose 文件和源码，但分别完成平台相关测试。

## 13. 固定诊断顺序

CLI 无法连接 Server：

```bash
docker version
docker context show
docker context ls
env | grep '^DOCKER_' || true
docker info
```

Ubuntu 服务问题：

```bash
systemctl status docker --no-pager
sudo journalctl -u docker --no-pager -n 100
ls -l /var/run/docker.sock
id
```

跨机器不一致：

```bash
uname -m
docker info --format '{{.Architecture}}'
docker image inspect IMAGE --format '{{.Os}}/{{.Architecture}}'
docker inspect CONTAINER
```

还要检查 Bind Mount 路径、文件权限、环境变量、镜像 digest、端口绑定和 GPU 条件。

## 14. 给 AI CLI 的边界

```text
先输出 hostname、pwd、docker context show、docker version 和 docker info 摘要。
不要假设当前连接的是本机 daemon。

只读检查容器、镜像、网络和 Volume。
未经确认不要 stop、rm、prune、删除 Volume、重启 Docker daemon 或切换 Context。

不要挂载 Docker Socket、整个 HOME、SSH 目录或云凭据目录。
不要使用 --privileged 来绕过具体权限问题。
涉及 Bind Mount 时明确宿主机源路径和容器目标路径。
涉及 Mac 与 Ubuntu 时分别说明平台、架构和验证结果。
```

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)

官方参考：

- [Docker Desktop](https://docs.docker.com/desktop/)
- [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/)
- [Docker Engine](https://docs.docker.com/engine/)
- [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/)
- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
