# 03 Docker Compose 多服务项目

当项目同时包含 Web、数据库、Redis、后台任务或模型服务时，单独维护多条 `docker run` 命令很快会失控。Docker Compose 用一份 YAML 描述服务、网络、卷、端口和环境变量，再统一启动与停止。

当前常用命令是：

```bash
docker compose
```

而不是旧式的独立命令：

```text
docker-compose
```

新 Compose 文件通常直接从 `services:` 开始，不需要再写顶层 `version`。

---

## 1. 最小示例

```yaml
services:
  web:
    build: .
    ports:
      - "127.0.0.1:8080:8000"
    environment:
      APP_ENV: development
```

启动：

```bash
docker compose up
```

后台启动：

```bash
docker compose up -d
```

查看状态和日志：

```bash
docker compose ps
docker compose logs
docker compose logs -f web
```

停止并删除本项目容器和默认网络：

```bash
docker compose down
```

`down` 默认不等于删除所有 Volume。添加额外删除参数前必须先确认数据影响。

---

## 2. 先用 `config` 检查最终配置

```bash
docker compose config
```

它会解析：

- YAML；
- 环境变量替换；
- 多文件合并；
- Profiles；
- 服务配置。

输出最终配置但不启动容器，适合在执行前发现变量缺失、缩进和合并问题。

不要把 `docker compose up` 当成 YAML 语法检查器。数据库已经启动以后再发现端口和 Volume 写错，代价通常更高。

---

## 3. 服务之间使用服务名通信

```yaml
services:
  web:
    build: .
    environment:
      DATABASE_HOST: db
    depends_on:
      - db

  db:
    image: postgres:17
```

在 `web` 容器中，数据库主机应使用：

```text
db
```

不是：

```text
localhost
```

容器内 `localhost` 只表示当前容器自己。

Compose 默认会为项目创建网络，并为服务提供 DNS 名称。

---

## 4. `depends_on` 不等于应用已经可用

`depends_on` 可以控制启动顺序，但数据库进程启动不代表它已经接受连接。

应结合 Healthcheck：

```yaml
services:
  db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10

  web:
    build: .
    depends_on:
      db:
        condition: service_healthy
```

应用自身仍应具备合理的重试和失败处理，不要只依赖启动顺序。

---

## 5. Volume 与 Bind Mount 分工

```yaml
services:
  web:
    build: .
    volumes:
      - .:/app

  db:
    image: postgres:17
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

通常：

```text
源码
→ Bind Mount

数据库持久数据
→ Named Volume
```

开发环境可以挂载源码，生产镜像通常应把经过构建的应用放进镜像，而不是依赖宿主机源码目录。

删除 Volume 前先确认是否包含数据库、用户上传内容或实验结果。

---

## 6. 环境变量与秘密

普通非敏感变量可以写在 Compose 文件中：

```yaml
environment:
  APP_ENV: development
```

本地变量也可以来自 `.env`，但要注意：

- `.env` 不应提交真实密码和 Token；
- `docker compose config` 的输出可能展开敏感值；
- 容器环境变量可能被具有 Docker 权限的人查看；
- 不要把生产秘密写入镜像；
- 团队和生产环境应使用正式秘密管理方式。

可以提交：

```text
.env.example
```

只保留变量名和非敏感示例。

---

## 7. 端口只暴露真正需要的服务

```yaml
ports:
  - "127.0.0.1:8080:8000"
```

这会把服务绑定到宿主机本地回环地址。

内部数据库如果只供 Compose 网络中的服务使用，通常不需要 `ports`：

```yaml
services:
  db:
    image: postgres:17
```

不要因为调试方便，就把数据库、Redis 和管理面板全部绑定到所有网络接口。

---

## 8. 构建与运行要区分

构建：

```bash
docker compose build
```

启动并在需要时构建：

```bash
docker compose up --build
```

查看镜像：

```bash
docker compose images
```

如果应用代码通过 Bind Mount 覆盖了镜像中的目录，容器实际运行的内容可能与构建时镜像不同。排查时要确认：

- 镜像中有什么；
- 挂载后又覆盖了什么；
- 当前容器到底运行哪份文件。

---

## 9. 多份 Compose 文件

常见结构：

```text
compose.yaml
compose.override.yaml
compose.gpu.yaml
```

显式组合：

```bash
docker compose \
  -f compose.yaml \
  -f compose.gpu.yaml \
  config
```

后面的文件会按 Compose 规则合并或覆盖前面的配置。

不要靠记忆判断最终结果，始终先运行 `docker compose config`。

---

## 10. Profiles 用于可选服务

```yaml
services:
  debug-ui:
    image: demo-debug
    profiles: ["debug"]
```

启动：

```bash
docker compose --profile debug up
```

适合可选调试工具、管理界面和本地辅助服务。

不要使用 Profiles 隐藏关键生产依赖，否则别人可能在不知道缺少服务的情况下启动出一套不完整环境。

---

## 11. 日志和退出状态

查看服务状态：

```bash
docker compose ps
```

查看退出容器：

```bash
docker compose ps -a
```

日志：

```bash
docker compose logs --tail=200 web
```

一次性任务：

```bash
docker compose run --rm web python -m pytest
```

或者在已运行服务中执行：

```bash
docker compose exec web python -m pytest
```

`run` 会创建一次性容器，`exec` 在现有容器中执行。两者不是完全相同的运行环境。

---

## 12. 不要直接使用高破坏性清理

高风险操作包括：

- `docker compose down -v`；
- 删除数据库 Volume；
- 删除 Bind Mount 对应宿主机目录；
- 全局 prune；
- 重建时覆盖未备份数据；
- 在错误项目目录运行 Compose。

执行前检查：

```bash
pwd
docker compose config --services
docker compose ps
docker volume ls
```

Compose 的项目名可能影响容器、网络和 Volume 名称。不要只看服务名就认为操作目标正确。

---

## 13. 给 AI CLI 的 Compose 约束

```text
先只读检查 compose.yaml、Dockerfile、.env.example 和相关脚本。
先运行 docker compose config，不要启动服务。

说明：
- 每个服务的职责；
- 暴露的端口；
- 持久数据位于哪里；
- 使用了哪些秘密；
- 哪些服务只应内部访问；
- 修改后的验证方式。

不要删除容器、Volume 或 Bind Mount 数据。
不要执行 down -v、prune 或生产环境操作。
```

继续阅读：

- [镜像、容器、卷与网络](01-镜像容器卷与网络.md)
- [Docker Desktop 与 Ubuntu Docker Engine](02-Docker-Desktop与Ubuntu-Docker-Engine.md)
- [GPU 容器与权限边界](04-GPU容器与权限边界.md)

官方参考：

- [Docker Compose](https://docs.docker.com/compose/)
- [Compose Specification](https://docs.docker.com/reference/compose-file/)
- [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/)
