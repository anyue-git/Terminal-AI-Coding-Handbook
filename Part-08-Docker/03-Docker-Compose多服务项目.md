# 03 Docker Compose 多服务项目

当项目同时包含 Web、数据库、缓存、后台任务或模型服务时，多条独立 `docker run` 命令很快会失去共同边界。Docker Compose 用一份 YAML 描述服务、网络、卷、端口、环境变量和启动关系，再通过统一命令管理这一组资源。本章建立一个 Nginx、PostgreSQL、一次性检查任务和可选 Adminer 组成的练习项目，重点理解最终配置、服务生命周期、内部 DNS、Healthcheck、存储和安全停止。

## 1. 建立项目，并在启动前解析最终配置

确认当前 Compose 实现：

```bash
docker compose version
```

当前常用形式是 `docker compose`，新文件通常直接从 `services:` 开始，不需要为兼容旧教程添加顶层 `version:`。已有项目应遵循其现有文件和工具版本。

创建网页和 `compose.yaml`：

```bash
mkdir -p ~/terminal-practice/compose-demo/site
cd ~/terminal-practice/compose-demo

cat > site/index.html <<'EOF'
<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8"><title>Compose Demo</title></head>
  <body><h1>Docker Compose is running</h1></body>
</html>
EOF
```

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "127.0.0.1:${WEB_PORT:-18080}:80"
    volumes:
      - ./site:/usr/share/nginx/html:ro

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: demo
      POSTGRES_PASSWORD: demo-local-password
      POSTGRES_DB: demo
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U demo -d demo"]
      interval: 3s
      timeout: 3s
      retries: 10
    volumes:
      - db-data:/var/lib/postgresql/data

  db-check:
    image: postgres:17-alpine
    depends_on:
      db:
        condition: service_healthy
    environment:
      PGPASSWORD: demo-local-password
    command: >-
      psql -h db -U demo -d demo
      -c "select current_database(), current_user;"

  adminer:
    image: adminer:latest
    profiles: ["debug"]
    ports:
      - "127.0.0.1:18081:8080"
    depends_on:
      db:
        condition: service_healthy

volumes:
  db-data:
```

这里的密码只用于本机练习，不能照搬到真实项目。正式仓库应提交变量说明或 `.env.example`，真实秘密由受控环境提供。

启动前解析配置，而不是把 `up` 当成 YAML 检查器：

```bash
pwd
docker context show
docker compose config
docker compose config --services
docker compose config --volumes
docker compose config --profiles
```

Compose 会结合当前目录、环境变量和多文件规则形成最终配置，并按项目名创建容器、网络和 Volume。在错误目录执行同一命令，可能操作另一套资源。

`${WEB_PORT:-18080}` 在 Compose 解析阶段展开；它与容器进程收到的环境变量属于不同阶段。可以临时观察插值结果：

```bash
WEB_PORT=19090 docker compose config
```

`docker compose config` 可能把环境变量值展开到输出中，不能把含真实密码、Token 或私有地址的完整结果直接粘贴到公开聊天或 Issue。本地 `.env` 也不是加密保险箱；仓库可以提交类似下面的 `.env.example`：

```text
WEB_PORT=18080
POSTGRES_USER=demo
POSTGRES_PASSWORD=replace-me
```

## 2. 前台观察启动顺序和服务状态

```bash
docker compose up
```

日志会交错显示：数据库启动并通过 Healthcheck，`db-check` 执行查询后正常退出，Web 持续运行。另开终端查看：

```bash
cd ~/terminal-practice/compose-demo
docker compose ps -a
curl http://127.0.0.1:18080
```

一次性迁移或检查服务退出 0，不代表整个项目失败。前台终端按 `Ctrl + C` 会停止本次附着的服务，但不会删除 Named Volume。

后台运行与查看日志：

```bash
docker compose up -d
docker compose ps
docker compose ps -a
docker compose logs --tail=100
docker compose logs -f web
```

停止并删除项目容器与默认网络：

```bash
docker compose down
```

`down` 默认保留 Named Volume。`docker compose down -v` 会删除项目卷，其中可能包含数据库和用户数据，不应作为普通停止命令。

## 3. 服务名、容器端口和宿主端口属于不同层

Compose 默认网络为服务提供内部 DNS。`db-check` 使用 `-h db`，其中 `db` 是服务名，不是固定 IP；容器重新创建后地址可以变化，服务名保持稳定。

Web 端口配置：

```yaml
ports:
  - "127.0.0.1:18080:80"
```

表示宿主机回环地址 18080 映射到 Web 容器 80。宿主访问 `127.0.0.1:18080`，服务之间使用 `db:5432` 等服务名和容器端口。容器内 `localhost` 只指当前容器，不会自动连接另一服务。

```bash
docker compose port web 80
docker network ls | grep compose-demo || true
docker compose exec db hostname
```

数据库未声明 `ports`，默认只供 Compose 网络内部访问。不需要宿主直接连接的服务，不应为了排错暴露到所有网络接口。

服务间连接失败时，先确认两个服务是否属于同一 Compose 项目与网络，再在容器内部测试服务名和端口。需要查看具体网络时，可以先找到服务容器：

```bash
docker compose ps -q db
docker inspect "$(docker compose ps -q db)" \
  --format '{{json .NetworkSettings.Networks}}'
```

这比把某次看到的容器 IP 写死进配置更可靠。

## 4. 启动顺序不等于服务已就绪

简单 `depends_on` 只能表达创建顺序，不能证明数据库已接受连接。本例为数据库设置 Healthcheck，并让 `db-check` 等待 `service_healthy`。

```bash
docker compose ps
docker inspect "$(docker compose ps -q db)" \
  --format '{{json .State.Health}}'
```

Healthcheck 也不是业务完整性证明。应用仍需处理数据库重启、短暂断线和连接恢复，不能只依赖首次启动顺序。

## 5. 源码用 Bind Mount，持久数据用 Named Volume

```text
./site:/usr/share/nginx/html:ro
→ 宿主机直接编辑的网页源码

db-data:/var/lib/postgresql/data
→ Docker 管理的数据库数据
```

只读挂载降低 Web 容器误改源码的机会。查看卷：

```bash
docker compose config --volumes
docker volume ls
docker volume inspect compose-demo_db-data
```

实际名称可能受项目名影响。Compose 文件描述卷的存在和挂载方式，不等于已经备份数据。停止、重新创建容器后卷仍在；删除卷、磁盘损坏或数据库写坏仍会造成损失。

## 6. `exec`、`run`、Profile、多文件与项目名解决不同边界

在正在运行的数据库容器中执行命令：

```bash
docker compose exec db \
  psql -U demo -d demo -c 'select now();'
```

根据服务定义创建一次性容器：

```bash
docker compose run --rm db-check
```

`exec` 使用现有容器现场，`run --rm` 创建临时容器，二者的进程、可写层和端口行为不同。一次性容器成功不能代替真实服务验证。

默认启动不会包含带 `debug` Profile 的 Adminer：

```bash
docker compose --profile debug up -d
```

使用时数据库主机填写服务名 `db`。Profiles 适合调试 UI、观测工具和开发辅助服务，不应隐藏生产必需依赖。

项目常把基础、开发或 GPU 配置拆成多份文件：

```text
compose.yaml
compose.dev.yaml
compose.gpu.yaml
```

后面的文件会按 Compose 合并规则覆盖或追加前面的映射与列表。启动前先查看最终结果，并在启动时保持相同的 `-f` 顺序：

```bash
docker compose \
  -f compose.yaml \
  -f compose.dev.yaml \
  config

docker compose \
  -f compose.yaml \
  -f compose.dev.yaml \
  up -d
```

只检查一组文件却用另一组文件启动，会让验证与实际运行脱节。

Compose 项目名通常来自目录，也可以显式指定：

```bash
docker compose -p compose-lesson config
docker compose ls
```

不同项目名会产生不同容器、网络和 Volume。自动化脚本应固定项目目录、项目名和 Compose 文件顺序，避免在错误位置操作另一套环境。

## 7. 更新镜像、重新创建和故障排查要有明确范围

```bash
docker compose pull
docker compose up -d
```

拉取新镜像和重建服务可能改变应用、数据库版本与兼容性。生产或重要开发数据应先阅读变更、备份卷并验证迁移。只想重建一个服务时明确写出服务名，避免无意义地重启整组项目。

项目故障时沿对象层次检查：

```bash
pwd
docker context show
docker compose config
docker compose config --services
docker compose ps -a
docker compose logs --tail=200 SERVICE
docker compose images
docker compose port web 80
docker compose config --volumes
docker volume ls
```

配置解析、容器生命周期、服务日志、端口和数据属于不同层。排查时不应第一反应执行 `down -v`、删除全部卷或清理整个 Docker Engine。

## 8. Compose 项目的完整工作流

```text
进入正确项目目录并确认 Docker Context、项目名和文件组合
→ docker compose config 解析最终配置与变量插值
→ 前台 up 观察首次生命周期
→ ps、日志、端口和协议分别验证
→ 服务间使用服务名，宿主使用映射端口
→ 源码与数据选择不同存储
→ 后台运行后持续观察
→ down 停止，删除 Volume 单独决策
```

让 Agent 修改 Compose 时，应要求它先读取 Compose 文件、Dockerfile、`.env.example` 和启动脚本，输出最终配置与资源影响，说明服务职责、内部/宿主端口、存储位置、秘密来源、一次性服务和 Profile。删除卷、扩大端口暴露、输出真实秘密、升级数据库主版本或改变项目名都需要单独确认。

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)
