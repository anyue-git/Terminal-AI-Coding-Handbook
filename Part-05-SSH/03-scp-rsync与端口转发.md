# 03 scp、rsync 与端口转发

SSH 不只用于登录。围绕 SSH 还有三类常用能力：

```text
scp
→ 一次性复制文件

rsync
→ 增量同步目录

ssh -L
→ 把远程服务安全映射到本机
```

---

## 1. 本地路径与远程路径

本地路径：

```text
~/Projects/demo
```

远程路径：

```text
USER@HOST:/home/USER/projects/demo
```

配置 SSH 别名后：

```text
gpu-laptop:~/projects/demo
```

冒号很重要。没有冒号时，字符串可能被当作本地文件名。

---

## 2. scp 适合简单复制

Mac 上传单个文件：

```bash
scp report.md gpu-laptop:~/projects/demo/
```

从 Ubuntu 下载：

```bash
scp gpu-laptop:~/projects/demo/result.json ~/Downloads/
```

复制目录：

```bash
scp -r demo gpu-laptop:~/projects/
```

自定义端口使用大写 `-P`：

```bash
scp -P 2222 report.md USER@HOST:~/
```

小写 `-p` 与 SSH 的端口选项不是同一回事。

---

## 3. rsync 适合持续同步

```bash
rsync -av ~/Projects/demo/ gpu-laptop:~/projects/demo/
```

常用选项：

```text
-a  递归并尽量保留属性
-v  显示过程
```

局域网传输已经压缩过的模型、图片和归档文件时，`-z` 不一定更快。

两端都需要可用的 rsync：

```bash
rsync --version
ssh gpu-laptop 'rsync --version'
```

---

## 4. 源路径尾部斜杠

```bash
rsync -av demo/ gpu-laptop:~/projects/demo/
```

表示复制 `demo` 里面的内容。

```bash
rsync -av demo gpu-laptop:~/projects/
```

表示复制 `demo` 目录本身。

可以记成：

```text
source/  → source 里面
source   → source 目录本身
```

正式同步前必须确认源、目标和尾部斜杠。

---

## 5. 先使用 `--dry-run`

```bash
rsync -av --dry-run \
  ~/Projects/demo/ \
  gpu-laptop:~/projects/demo/
```

确认计划后再去掉 `--dry-run`。

涉及大量文件、复杂排除规则或删除同步时，预演不是可选装饰。

---

## 6. 排除虚拟环境和产物

创建 `.rsyncignore`：

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

使用：

```bash
rsync -av --dry-run \
  --exclude-from='.rsyncignore' \
  ~/Projects/demo/ \
  gpu-laptop:~/projects/demo/
```

`.rsyncignore` 只是约定文件，rsync 不会自动读取，必须显式指定。

是否排除 `.git/` 取决于远程目录的 Git 管理方式。不要在自己不清楚的情况下覆盖另一端的 `.git`。

---

## 7. `--delete` 默认不要用

```bash
rsync -av --delete SOURCE/ DESTINATION/
```

它会删除目标端中源端不存在的文件。源和目标写反、源目录为空或排除规则错误，都可能造成批量删除。

必须使用时至少先执行：

```bash
rsync -av --delete --dry-run SOURCE/ DESTINATION/
```

并确认目标端将删除哪些内容。

---

## 8. 同步结果回 Mac

```bash
rsync -av --dry-run \
  gpu-laptop:~/runs/experiment-001/ \
  ~/ML-Runs/experiment-001/
```

确认后正式执行。

复杂 include/exclude 规则会受顺序影响，必须预演。大型 checkpoint 还可以生成校验值后再同步。

源码和结果推荐采用单向规则：

```text
源码：Mac → Ubuntu
结果：Ubuntu → Mac
```

不要让两端自动双向同步同一批源码。

---

## 9. 本地端口转发 `ssh -L`

Ubuntu 上让 Jupyter 只监听本机：

```bash
jupyter lab --no-browser --ip=127.0.0.1 --port=8888
```

Mac 建立隧道：

```bash
ssh -N -L 18888:127.0.0.1:8888 gpu-laptop
```

Mac 浏览器访问：

```text
http://127.0.0.1:18888
```

数据路径：

```text
Mac 127.0.0.1:18888
→ SSH 隧道
→ Ubuntu 127.0.0.1:8888
```

`-N` 表示不启动远程 Shell，只建立连接。按 `Ctrl + C` 结束隧道。

不要为了方便让无认证 Jupyter 直接监听公网地址。

---

## 10. 远程转发和动态转发

远程转发：

```bash
ssh -R 9000:127.0.0.1:3000 gpu-laptop
```

动态 SOCKS 转发：

```bash
ssh -D 1080 gpu-laptop
```

它们属于进阶功能，涉及监听地址、服务端配置和暴露范围。只需要 Mac 访问 Ubuntu 服务时，优先使用更容易理解的 `-L`。

---

## 11. AI CLI 的传输边界

```text
先只读检查源目录、目标目录、排除规则和预计传输大小。
rsync 必须先 --dry-run。
不要使用 --delete，除非我明确批准删除清单。
不要同步 .env、SSH 私钥、云凭据、虚拟环境或整个 HOME。
不要把无认证服务暴露到局域网或公网。
```

继续阅读：

- [项目同步与目录规范](../Part-11-GPU远程开发/02-项目同步与目录规范.md)
- [实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)
- [SSH 故障排查](04-SSH故障排查.md)
