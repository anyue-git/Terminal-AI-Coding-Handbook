# 02 Docker Desktop 与 Ubuntu Docker Engine

Mac 和 Ubuntu 都能运行 `docker`，但底层结构不同：

```text
Mac
Docker CLI
→ Docker Desktop
→ Linux 虚拟机
→ Docker Engine
→ Linux 容器

Ubuntu
Docker CLI
→ 本机 Docker Engine
→ Linux 容器
```

理解这一区别，才能解释文件挂载、性能、端口、磁盘和 GPU 为什么在两台机器上表现不同。

---

## 1. 先检查客户端连接到了谁

```bash
docker version
docker info
docker context show
docker context ls
```

`docker version` 会分别显示 Client 和 Server。

只看到 Client、Server 报错，常见原因包括：

- Docker Desktop 没有启动；
- Ubuntu 的 Docker daemon 没运行；
- 当前用户无权访问 Docker Socket；
- Docker Context 指向其他环境；
- 远程 daemon 不可达。

不要只通过反复重装 CLI 解决服务端问题。

---

## 2. Mac 上的 Docker Desktop

macOS 不能直接运行 Linux 容器内核，因此 Docker Desktop 会维护一台 Linux 虚拟机。

这意味着：

- 容器内部是 Linux 用户空间；
- Mac 二进制不能直接在 Linux 容器里运行；
- Bind Mount 要经过文件共享层；
- 容器内 `localhost` 只代表容器自己；
- 镜像、卷和容器主要存放在 Docker Desktop 虚拟磁盘中；
- CPU、内存和磁盘上限受 Docker Desktop 设置影响。

检查：

```bash
docker info
docker system df
```

不要因为 Finder 中看不到 Volume 文件，就认为它们不存在。

---

## 3. Ubuntu 上的 Docker Engine

Ubuntu 上通常直接运行：

```text
dockerd
containerd
Linux 容器
```

查看服务：

```bash
systemctl status docker
systemctl is-active docker
```

查看日志：

```bash
sudo journalctl -u docker --no-pager -n 100
```

如果服务没有启动，先诊断 daemon 和配置，不要急着删除全部 Docker 数据目录。

---

## 4. Docker Socket 是高权限入口

常见 Socket：

```text
/var/run/docker.sock
```

能够控制 Docker daemon 的用户，通常可以启动挂载宿主机目录、修改文件或使用高权限能力的容器。因此：

```text
加入 docker 组
≈ 获得接近 root 的 Docker 控制能力
```

这不是普通“免输 sudo”便利设置。

查看：

```bash
ls -l /var/run/docker.sock
groups
```

不要把 Docker Socket 挂进不可信容器，也不要让普通 AI Agent 默认控制它。

---

## 5. Rootless Docker 的定位

Rootless 模式让 daemon 和容器以普通用户身份运行，可以降低部分宿主机风险。

但它不是万能隔离：

- 仍可能修改用户可访问的文件；
- 某些网络、存储和 GPU 功能需要额外配置；
- 不可信代码仍可能读取挂入容器的凭据；
- 不能替代镜像审查和最小挂载。

是否使用 Rootless，应根据功能需求和官方限制决定，不要为了“更安全”盲目切换后再发现 GPU 或网络工作流不兼容。

---

## 6. Bind Mount 在两台机器上的差异

Mac 示例：

```bash
docker run --rm \
  --mount type=bind,src="$PWD",dst=/app \
  -w /app \
  python:3.12-slim \
  python app.py
```

Ubuntu 命令形式相似，但底层路径处理不同。

Mac：

```text
macOS 目录
→ Docker Desktop 文件共享
→ Linux VM
→ 容器
```

Ubuntu：

```text
Linux 宿主机目录
→ 容器
```

因此大量小文件、依赖目录和文件监视在 Mac 上可能更慢。常见做法是：

- 源码使用 Bind Mount；
- `node_modules`、数据库数据等使用 Volume；
- 不把大型数据集放进频繁扫描的共享目录。

---

## 7. CPU 架构也可能不同

Apple Silicon Mac 通常是：

```text
arm64
```

Ubuntu 游戏本通常是：

```text
amd64 / x86_64
```

检查：

```bash
uname -m
docker info --format '{{.Architecture}}'
```

镜像应支持对应架构。跨架构模拟可能可用，但性能和兼容性不能与原生运行等同。

需要发布多架构镜像时，应使用 Buildx 和 CI 明确构建、测试各平台，而不是只在本机打一个标签。

---

## 8. 端口映射与宿主机访问

容器映射到本地：

```bash
docker run --rm -p 127.0.0.1:8080:8000 demo-web
```

访问宿主机服务时，不要在容器里使用 `localhost`。

Docker Desktop 常提供特殊主机名：

```text
host.docker.internal
```

Linux 上的行为和配置可能不同，应查看当前 Docker 文档和网络方案。

更稳妥的是尽量让相关服务加入同一个 Compose 网络，通过服务名通信，而不是让容器绕回宿主机。

---

## 9. Mac 不负责验证 NVIDIA GPU 容器

Apple Silicon Mac 没有 NVIDIA CUDA。Mac 可以验证：

- Dockerfile 是否能构建；
- CPU 路径；
- Compose 结构；
- 应用基本启动；
- 非 GPU 测试。

Ubuntu 游戏本负责：

- 宿主机 NVIDIA 驱动；
- NVIDIA Container Toolkit；
- GPU 设备请求；
- CUDA 框架验证；
- 显存和性能测试。

不要把 Mac 上容器构建成功写成“GPU 容器已经验证”。

---

## 10. 数据和配置在哪里

需要区分：

```text
项目源码
→ Git 仓库

Bind Mount
→ 宿主机明确目录

Docker Volume
→ Docker 管理的数据

镜像层
→ 构建产物

容器可写层
→ 临时运行状态
```

备份数据库时，应使用数据库支持的备份方式或明确复制 Volume 数据。不要只备份 Compose YAML 就认为数据也已备份。

---

## 11. 常见故障排查

### CLI 能运行但无法连接 Server

```bash
docker version
docker context show
docker info
```

### Ubuntu 权限错误

```bash
ls -l /var/run/docker.sock
groups
```

先理解当前权限模型，不要直接把 Socket 改成所有人可写。

### Mac 文件挂载慢

检查：

- 是否挂载大量小文件；
- 是否把依赖目录放在 Bind Mount；
- Docker Desktop 资源设置；
- 文件监视器是否扫描大目录。

### 容器在一台机器能运行，另一台不能

检查：

- CPU 架构；
- 镜像平台；
- 路径和文件权限；
- 环境变量；
- GPU 条件；
- 换行符和执行位。

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Compose 多服务项目](03-Docker-Compose多服务项目.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)

官方参考：

- [Docker Desktop](https://docs.docker.com/desktop/)
- [Docker Engine](https://docs.docker.com/engine/)
- [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/)
- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
