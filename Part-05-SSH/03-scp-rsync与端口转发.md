# 03 scp、rsync 与端口转发

SSH 建立后，不必只用来远程登录。围绕同一条加密连接，还可以复制少量文件、增量同步项目，并把只监听在 Ubuntu 本机的服务映射到 Mac。本章沿用 `gpu-laptop-lan` 别名，依次完成上传小文件、同步项目、下载结果和建立本地端口转发。开始前先验证非交互连接：

```bash
ssh gpu-laptop-lan 'hostname && whoami && pwd'
```

如果这条命令不能稳定执行，应先解决 SSH 连接和认证，而不是继续调试 scp 或 rsync。

## 1. 先分清本地路径、远程路径和传输方向

Mac 本地路径如：

```text
~/Projects/demo
```

远程路径带有 `主机:`：

```text
gpu-laptop-lan:~/projects/demo
```

冒号表示右侧路径由远程 Ubuntu 解释，其中 `~` 指 Ubuntu 用户主目录，不是 Mac 主目录。缺少冒号时，整段文字可能被当作 Mac 本地文件名。传输前先明确“谁是源、谁是目标”，尤其不要把双向同步当成 Git 分支管理的替代品。

## 2. scp 适合一次性、小规模复制

在 Mac 创建练习文件，并在 Ubuntu 建立目标目录：

```bash
mkdir -p ~/terminal-practice/ssh-transfer
cd ~/terminal-practice/ssh-transfer
printf '# SSH transfer practice\n' > report.md

ssh gpu-laptop-lan \
  'mkdir -p ~/projects/ssh-transfer && ls -ld ~/projects/ssh-transfer'
```

从 Mac 上传并远程验证：

```bash
scp report.md gpu-laptop-lan:~/projects/ssh-transfer/
ssh gpu-laptop-lan \
  'ls -l ~/projects/ssh-transfer && cat ~/projects/ssh-transfer/report.md'
```

下载方向相反：

```bash
scp gpu-laptop-lan:~/projects/ssh-transfer/report.md \
  ./report-from-ubuntu.md

diff report.md report-from-ubuntu.md
```

`diff` 没有输出通常表示文本内容一致。scp 可用 `-r` 递归复制目录，但项目文件很多且需要反复同步时，rsync 更合适。使用自定义端口时，scp 的端口选项是大写 `-P`；小写 `-p` 是保留属性。已经在 SSH Config 保存端口时，不必重复填写。

## 3. rsync 用预演控制增量同步

rsync 通常要求两端都有程序，先检查：

```bash
rsync --version
ssh gpu-laptop-lan 'rsync --version'
```

在 Mac 创建一个小项目：

```bash
mkdir -p ~/terminal-practice/rsync-demo/src
cd ~/terminal-practice/rsync-demo
printf 'print("hello from Mac")\n' > src/app.py
printf '# rsync demo\n' > README.md
```

第一次同步只做预演：

```bash
rsync -av --dry-run \
  ~/terminal-practice/rsync-demo/ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

确认文件清单、源和目标无误后，去掉 `--dry-run`，再从远程查看结果：

```bash
rsync -av \
  ~/terminal-practice/rsync-demo/ \
  gpu-laptop-lan:~/projects/rsync-demo/

ssh gpu-laptop-lan \
  'find ~/projects/rsync-demo -type f -print'
```

修改 `src/app.py` 后再次预演，通常只会显示变化文件。源目录末尾斜杠会改变层级：`demo/` 表示复制目录内部内容，`demo` 表示复制目录本身。不要只背规则，始终以预演输出确认。

## 4. 同步源码时排除环境、缓存和秘密

源码同步通常不应包含 `.venv/`、`__pycache__/`、`node_modules/`、运行结果、checkpoint、日志和 `.env`。可以建立项目自己的排除文件：

```text
.git/
.venv/
__pycache__/
.pytest_cache/
node_modules/
runs/
checkpoints/
*.log
.env
```

rsync 不会自动读取 `.rsyncignore`，必须显式指定：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

是否排除 `.git/` 取决于远端如何管理仓库。若 Ubuntu 自己通过 Git 拉取和切换分支，通常不应让 rsync 覆盖其 `.git`。Mac 与 Ubuntu 架构和系统不同，不能把 Mac `.venv` 同步过去继续使用；应共享依赖声明和锁文件，再在两台机器分别创建环境。

`--delete` 会让目标端删除源端不存在的内容，不是普通加速选项。必须使用时只先预演：

```bash
rsync -av --delete --dry-run SOURCE/ DESTINATION/
```

逐项检查删除清单，不能让 Agent 自动去掉 `--dry-run`。更稳妥的职责通常是源码和配置由 Mac 单向到 Ubuntu，训练结果和必要日志由 Ubuntu 回到 Mac；不要让两个自动任务双向覆盖同一批源码，因为 rsync 不理解分支和冲突。

## 5. 将 Ubuntu 结果同步回 Mac

假设远程结果位于 `~/runs/experiment-001/`，先检查远端体积和本地空间，再预演下载：

```bash
ssh gpu-laptop-lan 'du -sh ~/runs/experiment-001'
mkdir -p ~/ML-Runs/experiment-001
df -h ~/ML-Runs

rsync -av --dry-run \
  gpu-laptop-lan:~/runs/experiment-001/ \
  ~/ML-Runs/experiment-001/
```

确认后正式同步。大型 checkpoint 需要额外考虑磁盘空间、断点续传和校验；校验值只能证明传输内容一致，不能证明实验本身正确。

## 6. 本地端口转发让远程本机服务只对 Mac 可见

Ubuntu 上的 Jupyter、开发服务器或监控页面可以只监听远程 `127.0.0.1`，不直接暴露给局域网。练习时在 Ubuntu 启动 Python 自带 HTTP 服务：

```bash
mkdir -p ~/terminal-practice/http-demo
printf 'hello through SSH tunnel\n' \
  > ~/terminal-practice/http-demo/index.html
cd ~/terminal-practice/http-demo
python3 -m http.server 8888 --bind 127.0.0.1
```

在 Mac 另开终端建立隧道：

```bash
ssh -N -L 18888:127.0.0.1:8888 gpu-laptop-lan
```

它表示 Mac 的 `127.0.0.1:18888` 通过 SSH 连接到 Ubuntu 的 `127.0.0.1:8888`；`-N` 只建立连接和转发，不启动远程交互 Shell。随后在 Mac 浏览器或终端访问：

```bash
curl http://127.0.0.1:18888
```

若本地端口被占用，使用 `lsof -nP -iTCP:18888 -sTCP:LISTEN` 找到监听进程，或选择另一个本地端口。结束时先停止 Mac 隧道，再停止 Ubuntu HTTP 服务。转发不会让服务自动具备认证；Jupyter Token、应用登录和数据权限仍要单独设置。

## 7. 传输和转发的检查顺序

```text
先验证普通 SSH 非交互命令
→ 明确源路径、目标路径和机器
→ scp 用于少量一次性文件
→ rsync 永远先 dry run，再检查排除规则和末尾斜杠
→ 删除同步逐项确认
→ 大结果先检查体积与空间
→ 端口转发明确本地端口和远程监听地址
```

AI CLI 可以帮助生成命令，但应要求它先解释源、目标、排除项、删除行为和运行位置，不得自行取消预演或扩大到项目外目录。

继续阅读：

- [SSH 故障排查](04-SSH故障排查.md)
- [项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
