# 03 scp、rsync 与端口转发

SSH 建立后，不必只把它当成远程登录工具。围绕同一条加密连接，还可以复制文件、增量同步项目，以及把只监听在 Ubuntu 本机的服务安全地映射到 Mac。本章使用上一章配置好的 `gpu-laptop-lan` 别名，完成三项练习：上传一个小项目、把运行结果同步回来、通过本地端口转发访问远程 HTTP 服务。

开始前先在 Mac 验证非交互连接：

```bash
ssh gpu-laptop-lan 'hostname && whoami && pwd'
```

如果这条命令不能稳定执行，应先解决 SSH 连接和认证问题，而不是继续调试 scp 或 rsync。

## 1. 先分清本地路径与远程路径

在 Mac 普通终端中：

```text
~/Projects/demo
```

表示 Mac 本地目录。

带有 `主机:` 的路径：

```text
gpu-laptop-lan:~/projects/demo
```

表示远程 Ubuntu 路径。冒号非常重要；缺少冒号时，整段文字可能被当作 Mac 上的本地文件名。

连接别名背后的含义可以展开为：

```text
gpu-laptop-lan:~/projects/demo
↓
YOUR_UBUNTU_USERNAME@192.168.1.50:/home/YOUR_UBUNTU_USERNAME/projects/demo
```

`~` 在冒号右侧由远程 Shell 解释，指向 Ubuntu 用户的家目录，不是 Mac 的家目录。

## 2. 用 scp 复制少量文件

在 Mac 建立练习文件：

```bash
mkdir -p ~/terminal-practice/ssh-transfer
cd ~/terminal-practice/ssh-transfer
printf '# SSH transfer practice\n' > report.md
```

先在 Ubuntu 创建目标目录：

```bash
ssh gpu-laptop-lan 'mkdir -p ~/projects/ssh-transfer && ls -ld ~/projects/ssh-transfer'
```

从 Mac 上传文件：

```bash
scp report.md gpu-laptop-lan:~/projects/ssh-transfer/
```

随后远程验证：

```bash
ssh gpu-laptop-lan 'ls -l ~/projects/ssh-transfer && cat ~/projects/ssh-transfer/report.md'
```

从 Ubuntu 下载文件时，方向相反：

```bash
scp gpu-laptop-lan:~/projects/ssh-transfer/report.md ./report-from-ubuntu.md
```

检查两个文件：

```bash
ls -l report.md report-from-ubuntu.md
diff report.md report-from-ubuntu.md
```

`diff` 没有输出通常表示文本内容相同。

scp 也可以递归复制目录：

```bash
scp -r local-directory gpu-laptop-lan:~/projects/
```

它适合一次性、小规模复制。项目包含大量文件且需要反复同步时，scp 每次重新传输的方式通常不如 rsync 合适。

使用自定义端口时，scp 的端口选项是大写 `-P`：

```bash
scp -P 2222 report.md USER@HOST:~/
```

小写 `-p` 用于保留时间和权限等属性，不是端口选项。已经使用 SSH Config 保存端口时，无须在每条 scp 命令中重复填写。

## 3. 用 rsync 增量同步项目目录

先检查 Mac 是否有 rsync：

```bash
rsync --version
```

再检查 Ubuntu：

```bash
ssh gpu-laptop-lan 'rsync --version'
```

rsync 通常要求两端都有对应程序。若 Ubuntu 缺少它，应在 Ubuntu 本机或已确认的远程会话中使用系统包管理器安装，而不是在 Mac 上安装后期待远端自动拥有。

在 Mac 创建一个小项目：

```bash
mkdir -p ~/terminal-practice/rsync-demo/src
cd ~/terminal-practice/rsync-demo
printf 'print("hello from Mac")\n' > src/app.py
printf '# rsync demo\n' > README.md
```

第一次同步前只做预演：

```bash
rsync -av --dry-run \
  ~/terminal-practice/rsync-demo/ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

输出会列出计划传输的文件。确认源路径和目标路径无误后，去掉 `--dry-run`：

```bash
rsync -av \
  ~/terminal-practice/rsync-demo/ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

远程检查：

```bash
ssh gpu-laptop-lan 'find ~/projects/rsync-demo -type f -print'
```

修改一个文件后再次同步：

```bash
printf 'print("second line")\n' >> src/app.py
rsync -av --dry-run \
  ~/terminal-practice/rsync-demo/ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

此时通常只显示发生变化的文件，这就是增量同步的价值。

## 4. 源目录末尾斜杠会改变结果

下面两条命令含义不同：

```bash
rsync -av demo/ gpu-laptop-lan:~/projects/demo/
```

表示复制 `demo` 目录内部的内容。

```bash
rsync -av demo gpu-laptop-lan:~/projects/
```

表示把 `demo` 目录本身复制到目标目录中。

可以把规则记成：

```text
source/   → source 里面的内容
source    → source 目录本身
```

但真正执行前仍要查看 `--dry-run` 输出。很多“多套了一层目录”或“文件落到错误位置”的问题，都来自源路径末尾斜杠没有核对。

## 5. 不要同步虚拟环境、缓存和秘密

源码同步通常不应包含：

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

在项目根目录创建 `.rsyncignore`：

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

预演：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ./ \
  gpu-laptop-lan:~/projects/rsync-demo/
```

`.rsyncignore` 只是本项目使用的约定文件名，rsync 不会自动读取它，必须通过 `--exclude-from` 显式指定。

是否排除 `.git/` 取决于远程项目如何管理。如果 Ubuntu 端通过 Git 自己拉取和切换分支，通常不应让 rsync 覆盖它的 `.git`。如果你不清楚两端各自承担什么角色，先不要同步隐藏目录。

Mac 与 Ubuntu 的操作系统和架构不同，不能把 Mac 的 `.venv` 同步到 Ubuntu 后继续使用。应同步依赖声明和锁文件，再在两台机器分别创建环境。

## 6. `--delete` 是删除同步，不是普通加速选项

`--delete` 会让目标端删除源端不存在的内容。源和目标写反、源目录临时为空、排除规则错误，都可能导致大范围删除。

必须评估删除同步时，只先运行预演：

```bash
rsync -av --delete --dry-run SOURCE/ DESTINATION/
```

重点检查输出中标记为删除的每个路径。不要让 AI CLI 自动去掉 `--dry-run`，也不要把 `--delete` 写进自己尚未理解的长期脚本。

对于源码，通常更稳妥的模式是明确单向来源：

```text
源码和配置：Mac → Ubuntu
训练结果和必要日志：Ubuntu → Mac
```

不要让两个自动任务双向同步同一批源码。两端同时修改时，rsync 不会像 Git 一样理解分支和冲突，较新的文件也不一定代表正确版本。

## 7. 把 Ubuntu 结果同步回 Mac

假设 Ubuntu 生成了结果目录：

```text
~/runs/experiment-001/
```

先在 Mac 预演下载：

```bash
mkdir -p ~/ML-Runs/experiment-001
rsync -av --dry-run \
  gpu-laptop-lan:~/runs/experiment-001/ \
  ~/ML-Runs/experiment-001/
```

确认后正式同步：

```bash
rsync -av \
  gpu-laptop-lan:~/runs/experiment-001/ \
  ~/ML-Runs/experiment-001/
```

大型 checkpoint 应先检查大小和剩余磁盘空间：

```bash
ssh gpu-laptop-lan 'du -sh ~/runs/experiment-001'
df -h ~/ML-Runs
```

需要验证完整性时，可以在两端生成相同算法的校验值，再比较结果。校验可以发现传输损坏，但不能证明实验结果本身正确。

## 8. 本地端口转发解决什么问题

Ubuntu 上的 Jupyter、开发服务器或监控页面可以只监听远程本机地址：

```text
Ubuntu 127.0.0.1:8888
```

这种服务不会直接暴露到局域网。Mac 可以通过 SSH 本地端口转发访问它：

```text
Mac 127.0.0.1:18888
→ SSH 加密连接
→ Ubuntu 127.0.0.1:8888
```

为了练习，不必先安装 Jupyter。登录 Ubuntu 后运行 Python 自带的临时 HTTP 服务：

```bash
mkdir -p ~/terminal-practice/http-demo
printf 'hello through SSH tunnel\n' > ~/terminal-practice/http-demo/index.html
cd ~/terminal-practice/http-demo
python3 -m http.server 8888 --bind 127.0.0.1
```

这个终端会被服务占用，暂时保持运行。

在 Mac 新开一个终端，建立隧道：

```bash
ssh -N -L 18888:127.0.0.1:8888 gpu-laptop-lan
```

`-L` 后面的三部分分别是：

```text
Mac 本地端口 : Ubuntu 目标地址 : Ubuntu 目标端口
```

`-N` 表示不启动远程交互 Shell，只建立 SSH 连接和转发。随后在 Mac 浏览器访问：

```text
http://127.0.0.1:18888
```

应看到：

```text
hello through SSH tunnel
```

结束练习时，先在 Mac 的隧道终端按 `Ctrl + C`，再到 Ubuntu 的 HTTP 服务终端按 `Ctrl + C`。

## 9. 端口占用与监听范围

如果 Mac 的 18888 已被占用，SSH 可能提示无法绑定。检查：

```bash
lsof -nP -iTCP:18888 -sTCP:LISTEN
```

可以选择另一个本地端口，例如：

```bash
ssh -N -L 18889:127.0.0.1:8888 gpu-laptop-lan
```

默认绑定到 Mac 的回环地址更安全。不要为了让其他设备访问，随意改成监听所有接口。那会改变服务暴露范围，需要额外考虑本地防火墙、认证和网络中的其他设备。

远程服务仍应有自己的身份验证。SSH 隧道保护传输路径，但不能替代 Jupyter Token、应用登录、访问权限和数据隔离。

## 10. 远程转发和动态转发先知道边界

OpenSSH 还支持：

```text
-R   远程端口转发
-D   动态 SOCKS 代理
```

它们会改变服务从哪一端可见，可能受到 `GatewayPorts`、服务端 SSH 配置和网络策略影响。只需要从 Mac 访问 Ubuntu 本机服务时，优先使用容易审查的 `-L`。

不要把动态转发当作规避网络管理或隐藏流量的通用工具。本手册只讨论自己设备和授权网络中的开发用途。

## 11. 给 AI CLI 的传输约束

让 Agent 协助同步前，可以明确：

```text
先只读检查源目录、目标目录、预计传输大小和排除规则。
所有 rsync 先使用 --dry-run。
未经批准不要使用 --delete。
不要同步 .env、SSH 私钥、云凭据、虚拟环境、整个 HOME 或未知隐藏目录。
不要建立监听在所有网络接口上的无认证服务。
完成后报告实际传输路径、文件数量和验证方法。
```

Agent 能生成命令，但无法仅凭目录名判断哪些结果已经备份、哪些凭证可上传、哪一端才是权威来源。这些边界仍需由项目负责人决定。

继续阅读：

- [项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)
- [SSH 故障排查](04-SSH故障排查.md)
