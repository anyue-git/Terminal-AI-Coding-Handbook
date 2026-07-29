# 03 Docker Compose 多服务项目

当一个项目同时包含 Web、数据库、缓存、后台任务或模型服务时，继续维护多条独立 `docker run` 命令会很快失去控制。Docker Compose 用一份 YAML 描述服务、网络、卷、端口、环境变量和启动关系，再通过统一命令创建和管理这一组资源。

本章建立一个可运行的练习项目：Nginx 提供本地 Web 页面，PostgreSQL 保存数据，另一个一次性服务等待数据库健康后执行查询。这个例子用来理解 Compose 的项目边界、服务名 DNS、Healthcheck、Named Volume、Profiles 和安全停止方式。

## 1. 先确认当前使用的是 Compose V2

运行：

```bash
docker compose version
```

当前常用命令形式是：

```bash
docker compose
```

而不是旧的独立可执行文件：

```text
docker-compose
```

新 Compose 文件通常直接从 `services:` 开始，不需要为了兼容旧教程添加顶层 `version:`。如果项目已经有现成 Compose 文件，应先遵循项目约定，不要为了形式统一随意重写。

## 2. 建立练习项目

创建目录：

```bash
mkdir -p ~/terminal-practice/compose-demo/site
cd ~/terminal-practice/compose-demo
```

创建一个网页：

```bash
cat > site/index.html <<'EOF'
<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8"><title>Compose Demo</title></head>
  <body><h1>Docker Compose is running</h1></body>
</html>
EOF
```

创建 `compose.yaml`：

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "127.0.0.1:18080:80"
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
    command:
      - sh
      - -c
      - >-
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

这里的密码只用于本机练习，不应照搬到真实项目。正式项目应提交 `.env.example` 或变量说明，而不是把生产秘密写进 Compose 文件。

## 3. 启动前先解析最终配置

不要把 `docker compose up` 当作 YAML 检查器。先运行：

```bash
docker compose config
```

这会解析：

- YAML 缩进和字段；
- 环境变量替换；
- 多文件合并；
- Profiles；
- Volume 与网络声明；
- 服务的最终配置。

只查看服务名：

```bash
docker compose config --services
```

输出应包含：

```text
web
db
db-check
```

`adminer` 带有 `debug` Profile，默认不会启动。

还应确认当前目录和 Docker 目标：

```bash
pwd
docker context show
docker compose config --volumes
docker compose config --profiles
```

Compose 会根据项目目录和项目名创建容器、网络和 Volume。在错误目录中执行相同命令，可能操作另一套同名服务。

## 4. 前台启动并观察生命周期

运行：

```bash
docker compose up
```

你会看到多个服务的日志交错输出。预期过程是：

```text
db 启动
→ Healthcheck 变为 healthy
→ db-check 执行 SQL 并退出 0
→ web 持续运行
```

另开终端检查：

```bash
cd ~/terminal-practice/compose-demo
docker compose ps -a
```

`web` 和 `db` 应处于运行状态，`db-check` 可能显示已成功退出。一次性迁移、初始化和测试服务正常退出，并不等于整个 Compose 项目失败。

访问网页：

```bash
curl http://127.0.0.1:18080
```

完成观察后，在前台终端按 `Ctrl + C`。这会停止由本次 `up` 附着的服务，但不会删除 Named Volume。

## 5. 后台运行、查看日志和停止

后台启动：

```bash
docker compose up -d
```

查看状态：

```bash
docker compose ps
docker compose ps -a
```

查看全部日志：

```bash
docker compose logs --tail=100
```

持续观察某个服务：

```bash
docker compose logs -f web
```

停止并删除本项目容器和默认网络：

```bash
docker compose down
```

`down` 默认不会删除 Named Volume。不要把下面的附加删除操作当作普通停止方式：

```text
docker compose down -v
```

它会删除项目 Volume，其中可能包含数据库和用户数据。

## 6. 服务名是容器网络中的稳定地址

Compose 默认会为项目创建一个网络，服务会通过内部 DNS 使用服务名互相发现。在 `db-check` 中：

```text
psql -h db
```

这里的 `db` 是 Compose 服务名，不是固定 IP。

查看网络：

```bash
docker network ls | grep compose-demo || true
docker compose exec db hostname
```

容器重新创建后 IP 可能变化，但服务名保持稳定。因此服务间连接应该写：

```text
db:5432
```

而不是把某次检查得到的容器 IP 写进配置。

容器内的 `localhost` 只指当前容器。`web` 容器中的 `localhost:5432` 不会自动连接到 `db` 容器。

## 7. 容器端口与宿主机端口不是一回事

Web 配置：

```yaml
ports:
  - "127.0.0.1:18080:80"
```

含义是：

```text
宿主机 127.0.0.1:18080
→ web 容器 80
```

从 Mac 或 Ubuntu 宿主机访问时使用 `127.0.0.1:18080`；Compose 服务之间通信时使用服务名和容器端口。

查看实际映射：

```bash
docker compose port web 80
```

数据库没有声明 `ports`，因此只能从 Compose 网络内部访问。这个默认更适合开发安全边界：不需要宿主机直接连接的服务，不要为了“方便排错”暴露到所有网络接口。

## 8. `depends_on` 与 Healthcheck 的区别

简单写法：

```yaml
depends_on:
  - db
```

只能表达启动顺序，不能证明数据库已经接受连接。

本章使用：

```yaml
depends_on:
  db:
    condition: service_healthy
```

并为数据库定义 `healthcheck`。这样 `db-check` 会等待数据库健康。

检查健康状态：

```bash
docker compose ps
docker inspect "$(docker compose ps -q db)" \
  --format '{{json .State.Health}}'
```

Healthcheck 不是业务完整性证明。应用仍应处理数据库重启、短暂断线和连接重建，不能只依赖第一次启动顺序。

## 9. Bind Mount 与 Named Volume 分工

练习项目使用两类存储：

```text
./site:/usr/share/nginx/html:ro
→ Bind Mount
→ 宿主机可直接编辑的网页源码

 db-data:/var/lib/postgresql/data
→ Named Volume
→ Docker 管理的数据库持久数据
```

`ro` 表示 Web 容器只读挂载网页目录，降低容器误改源码的机会。

查看 Volume：

```bash
docker volume ls
docker volume inspect compose-demo_db-data
```

实际名称可能因项目名而不同。使用：

```bash
docker compose config --volumes
```

先确认逻辑名，再通过 `docker volume ls` 找到实际资源。

停止并重新启动项目后，数据库 Volume 仍存在。Compose 文件只描述 Volume，不等于已经备份数据。

## 10. `run`、`exec` 和普通服务的区别

在已经运行的数据库容器中执行命令：

```bash
docker compose exec db \
  psql -U demo -d demo -c 'select now();'
```

`exec` 在现有容器中运行。

创建一次性新容器：

```bash
docker compose run --rm db-check
```

`run` 根据服务定义创建新的临时容器。它与正在运行的服务不是同一个进程和可写层，端口行为也可能不同。

常见用途：

```text
exec
→ 进入已经运行的应用或数据库检查现场

run --rm
→ 测试、迁移、管理命令和一次性任务
```

不要在不清楚环境差异时，用一次性容器的成功代替真实服务验证。

## 11. Profiles 管理可选服务

启动默认服务：

```bash
docker compose up -d
```

不会启动 `adminer`。

启用调试 Profile：

```bash
docker compose --profile debug up -d
```

然后访问：

```text
http://127.0.0.1:18081
```

Adminer 连接参数中，数据库主机应填写服务名：

```text
db
```

Profiles 适合可选调试 UI、观测工具和开发辅助服务。不要用 Profile 隐藏生产必需依赖，否则其他人可能在不知情的情况下启动一套不完整系统。

使用完调试工具后：

```bash
docker compose --profile debug down
```

## 12. 环境变量和秘密的两种阶段

Compose 有两个不同阶段会使用环境变量：

```text
Compose 插值阶段
→ 生成最终 YAML

容器运行阶段
→ 注入服务环境变量
```

例如：

```yaml
ports:
  - "127.0.0.1:${WEB_PORT:-18080}:80"
```

`${WEB_PORT:-18080}` 在 Compose 解析阶段展开。

查看插值：

```bash
WEB_PORT=19090 docker compose config
```

注意 `docker compose config` 可能把环境变量值展开到输出中。不要把含真实密码、Token 或私有地址的完整结果直接发到公开聊天或 Issue。

本地 `.env` 不是加密保险箱。可以提交 `.env.example`：

```text
WEB_PORT=18080
POSTGRES_USER=demo
POSTGRES_PASSWORD=replace-me
```

真实秘密应通过组织认可的 Secret 管理、CI Secret 或权限受限的本地配置提供。

## 13. 多份 Compose 文件必须先看合并结果

常见结构：

```text
compose.yaml
compose.dev.yaml
compose.gpu.yaml
```

检查合并后的配置：

```bash
docker compose \
  -f compose.yaml \
  -f compose.dev.yaml \
  config
```

后面的文件会按照 Compose 合并规则追加或覆盖前面的内容。列表、映射和路径的行为并不总是符合直觉。

启动时要使用同样的 `-f` 顺序：

```bash
docker compose \
  -f compose.yaml \
  -f compose.dev.yaml \
  up -d
```

不要只检查一组文件，却用另一组文件启动。

## 14. 项目名会改变资源名称

Compose 项目名通常来自目录名，也可以通过参数覆盖：

```bash
docker compose -p compose-lesson config
```

不同项目名会创建不同的容器、网络和 Volume。检查：

```bash
docker compose ls
docker compose ps
```

自动化脚本中应明确项目目录和项目名，防止在错误位置操作另一套环境。

## 15. 一套分层排错顺序

先检查最终配置和目标：

```bash
pwd
docker context show
docker compose config
docker compose config --services
```

再看生命周期：

```bash
docker compose ps -a
docker compose logs --tail=200
```

服务间连接失败时：

```bash
docker compose exec db hostname
docker network inspect "$(docker compose ps -q db | xargs docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
```

更简单时，可以先检查服务是否在同一网络，并在容器内部测试服务名解析和端口。不要先改成固定 IP。

端口问题：

```bash
docker compose port web 80
curl http://127.0.0.1:18080
```

数据问题：

```bash
docker compose config --volumes
docker volume ls
docker volume inspect VOLUME_NAME
```

## 16. 给 AI CLI 的 Compose 边界

```text
先只读检查 compose.yaml、Dockerfile、.env.example 和启动脚本。
先运行 docker compose config，不要直接 up。

说明：
- 每个服务的职责；
- 服务间使用的名称和端口；
- 哪些端口暴露到宿主机；
- 哪些数据位于 Bind Mount 或 Named Volume；
- 哪些值属于秘密；
- 哪些服务是一次性任务或 Profile；
- 修改后的验证和停止方式。

未经确认不要执行 down -v、prune、删除 Volume、修改生产环境或扩大端口暴露。
不要把数据库密码、Token 或完整 docker compose config 输出发给外部服务。
```

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)

官方参考：

- [Docker Compose](https://docs.docker.com/compose/)
- [Compose Specification](https://docs.docker.com/reference/compose-file/)
- [Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Compose environment variables](https://docs.docker.com/compose/how-tos/environment-variables/)
