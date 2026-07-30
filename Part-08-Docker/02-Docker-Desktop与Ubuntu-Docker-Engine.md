# 02 Docker Desktop 与 Ubuntu Docker Engine

Mac 和 Ubuntu 都能执行 `docker`，但同一条命令背后的运行结构不同。Mac 的 Linux 容器位于 Docker Desktop 管理的 Linux 虚拟机中；Ubuntu 游戏本通常直接运行本机 Docker Engine。只有先分清客户端、Context、daemon、宿主架构与数据位置，才能解释挂载速度、文件权限、镜像平台和 GPU 能力为何不同。

## 1. Docker CLI 当前连接的是哪个 Engine

在当前终端执行：

```bash
docker version
docker context show
docker context ls
docker info
```

Client 是当前 CLI，Server 是当前 Context 指向的 daemon。只显示 Client 而 Server 报错，常见原因包括 Docker Desktop 未启动、Ubuntu daemon 未运行、Socket 权限不足、`DOCKER_HOST` 或 Context 指向其他主机。

执行删除、停止或清理前，先确认宿主和目标：

```bash
hostname
docker context show
docker info --format 'name={{.Name}} os={{.OperatingSystem}} arch={{.Architecture}}'
env | grep '^DOCKER_' || true
```

同一 CLI 可以控制本地或远程 Engine，环境变量也可能覆盖 Context。不要只凭终端窗口标题判断操作对象。

## 2. Mac：CLI 通过 Docker Desktop 进入 Linux VM

结构可以表示为：

```text
Mac Terminal
→ Docker CLI
→ Docker Desktop 后端
→ Linux VM
→ Docker Engine
→ Linux 容器
```

因此容器里运行的是 Linux 用户空间：

```bash
docker run --rm alpine uname -a
docker info
docker system df
```

macOS 可执行文件不能直接在 Linux 容器运行；Mac 目录要经过文件共享层进入 VM；容器中的 `localhost` 只指容器自己；镜像、容器和 Named Volume 主要保存在 Docker Desktop 虚拟磁盘中。Finder 看不到普通 Volume 文件夹，不表示数据不存在。

## 3. Ubuntu：CLI 通常直接连接本机 dockerd

常见结构是：

```text
Ubuntu Terminal
→ Docker CLI
→ 本机 dockerd / containerd
→ Linux 容器
```

检查服务、日志与 Socket：

```bash
systemctl is-active docker
systemctl status docker --no-pager
sudo journalctl -u docker --no-pager -n 100
ls -l /var/run/docker.sock
```

服务异常时先看配置、日志和磁盘，不要删除 `/var/lib/docker`，其中可能包含全部镜像、容器和 Volume。Ubuntu 也能安装 Docker Desktop for Linux，但它会创建独立 VM 与 `desktop-linux` Context，和本机 Engine 的资源相互独立；个人 GPU 游戏本通常无需同时维护两套运行时。

## 4. Docker Socket 是高权限控制入口

拥有 `/var/run/docker.sock` 控制权的用户通常能启动高权限容器、挂载宿主目录和映射设备。加入 `docker` 组不仅是“免 sudo”，而是获得接近 root 的 Docker 控制能力。

```bash
id
groups
ls -l /var/run/docker.sock
```

不要执行 `chmod 666 /var/run/docker.sock`，也不要把 Socket 挂入来源不明的容器。容器一旦能调用 Docker API，可能进一步控制其他容器和宿主资源。AI CLI 需要运行 Docker 时，也应限定项目、命令、挂载、端口、设备和数据范围。

## 5. Mac 可以通过 SSH Context 显式操作 Ubuntu Engine

Mac 不必把源码或 Docker 状态复制进 Desktop VM，才能查看 Ubuntu 上的容器。普通 SSH 已经能够连接游戏本、远程用户也有权访问该机 Docker Socket 时，可以在 Mac 创建一个命名 Context。下面假设 `~/.ssh/config` 中已有 `ubuntu-gpu` 主机别名：

```bash
docker context create gpu-laptop \
  --docker "host=ssh://ubuntu-gpu"

docker context inspect gpu-laptop
docker --context gpu-laptop info
docker --context gpu-laptop ps
```

推荐在远程操作中逐条写出 `--context gpu-laptop`，而不是长期执行 `docker context use gpu-laptop` 后依赖记忆。停止容器、删除 Volume 或 prune 之前，再确认返回的 Engine 名称、架构和容器清单：

```bash
docker --context gpu-laptop info \
  --format 'name={{.Name}} os={{.OperatingSystem}} arch={{.Architecture}}'
docker --context gpu-laptop ps -a
docker --context gpu-laptop volume ls
```

这些命令由 Mac 上的 CLI 发起，但实际操作的是 Ubuntu daemon；镜像、容器、网络和 Volume 都留在 Ubuntu。远程 Bind Mount 的源路径也由 Ubuntu 解释，因此下面的 `src=` 必须是游戏本上存在的路径，不能直接使用只在 Mac 存在的 `$PWD`：

```bash
docker --context gpu-laptop run --rm \
  --mount type=bind,src=/home/USER/Projects/demo,dst=/work,readonly \
  alpine ls -la /work
```

SSH Context 复用 SSH 的主机身份与认证，但不会降低远端 Docker 权限；远程用户如果属于 `docker` 组，仍拥有高影响控制能力。它也不要求把未加密 Docker TCP 端口暴露到局域网或公网。Context 不再使用时先确认没有脚本依赖，再决定是否执行 `docker context rm gpu-laptop`。

## 6. 同一标签在两台机器上可能对应不同架构镜像

分别在 Mac 和 Ubuntu 执行：

```bash
printf 'host: '; hostname
printf 'host arch: '; uname -m
printf 'context: '; docker context show
printf 'server arch: '; docker info --format '{{.Architecture}}'
docker run --rm alpine sh -c 'uname -s; uname -m'
```

Apple Silicon 常见 arm64/aarch64，Ubuntu 游戏本常见 x86_64/amd64。多架构标签会根据平台选择不同镜像清单：

```bash
docker buildx imagetools inspect alpine:latest
docker run --rm --platform linux/amd64 alpine uname -m
```

arm64 Mac 可以模拟 amd64，但能启动不代表性能、原生扩展和高性能计算行为与真实 x86_64 相同。发布多架构镜像需要分别构建和测试目标平台。

## 7. Bind Mount 在 Mac 与 Ubuntu 经过不同路径

创建练习目录并让容器读写：

```bash
mkdir -p ~/terminal-practice/docker-host-demo
cd ~/terminal-practice/docker-host-demo
printf 'created on host\n' > note.txt

docker run --rm \
  --mount type=bind,src="$PWD",dst=/work \
  -w /work \
  alpine \
  sh -c 'cat note.txt; printf "created in container\n" > result.txt'

cat result.txt
ls -ln note.txt result.txt
```

Mac 路径经过 macOS、Docker Desktop 文件共享、Linux VM 再到容器；Ubuntu 更接近宿主目录直接挂载。因此 Mac 上大量小文件、包缓存、Git 扫描和文件监听可能更慢。常见分工是源码用 Bind Mount，数据库与依赖缓存用 Volume，不把 Mac `.venv` 或 `node_modules` 直接当成 Linux 容器依赖。

Ubuntu 上容器默认 root 写入 Bind Mount 时，宿主可能出现 root 所有文件。先检查容器用户，再通过 Dockerfile `USER`、Compose `user:` 或明确 UID/GID 解决，不要把递归 `sudo chown` 整个项目当作固定补救。Docker Desktop 中的容器 root 不等同于 macOS root，但对已挂载文件仍具有相应读写能力。

## 8. 端口和 localhost 要从当前网络命名空间理解

```bash
docker run --rm \
  -p 127.0.0.1:18080:80 \
  nginx:alpine
```

宿主访问 `127.0.0.1:18080`，容器服务监听 80。绑定回环地址只供宿主本机访问；省略地址可能暴露给局域网。容器访问自己使用 `localhost`，Compose 服务间使用服务名；容器访问宿主服务时，Docker Desktop 常提供 `host.docker.internal`，Linux Engine 则需明确配置，不能假设平台行为相同。

## 9. 数据位置与清理对象必须逐层确认

需要区分宿主 Bind Mount、容器可写层、Named Volume、镜像层和 Docker Desktop 虚拟磁盘或 Ubuntu `/var/lib/docker`。检查：

```bash
docker ps -a
docker image ls
docker volume ls
docker system df
```

清理前确认 Context、资源名称、是否可重建和是否含唯一数据。不要因为磁盘占用大就直接 prune 全部资源或删除 Docker 数据目录。

## 10. 跨机器 Docker 的固定检查顺序

```text
确认当前宿主机
→ 查看 Docker Context 与环境变量
→ 区分 Mac Desktop VM 和 Ubuntu 本机 Engine
→ 核对 daemon、Socket 权限与架构
→ 远程操作时显式写出目标 Context
→ 分清 Bind Mount、Volume 和容器可写层
→ 检查端口绑定与网络访问方向
→ 清理前确认资源属于哪套 Engine
```

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)
