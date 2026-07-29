# 04 SSH 故障排查

SSH 连接失败时，最有效的方法不是重装 OpenSSH、删除整个 `~/.ssh` 或反复修改防火墙，而是先确定失败发生在哪一层。一个错误通常已经排除了前面的若干层：看到 `Permission denied`，说明网络和端口大概率已经可达；看到 `Connection timed out`，此时还没有进入用户认证阶段。

本章仍以 Mac 连接 Ubuntu 游戏本为例。所有命令都标明运行位置，避免在错误机器上检查错误对象。

## 1. 先保存一份最小诊断记录

在 Mac 新建临时目录：

```bash
mkdir -p ~/terminal-practice/ssh-diagnosis
cd ~/terminal-practice/ssh-diagnosis
```

记录当前时间和客户端版本：

```bash
date
ssh -V
```

若使用 SSH 别名，查看最终配置：

```bash
ssh -G gpu-laptop-lan \
  | grep -E '^(hostname|user|port|identityfile|identitiesonly|proxyjump|localforward) '
```

再进行一次详细连接，并把完整输出保存在本地：

```bash
ssh -vvv gpu-laptop-lan 2> ssh-debug.log
```

连接完成或失败后检查日志末尾：

```bash
tail -n 80 ssh-debug.log
```

`-vvv` 会显示客户端如何解析地址、建立连接和尝试认证。日志可能包含真实用户名、主机名、IP、私钥路径和网络结构；发送给外部 AI 或公开到论坛前必须脱敏，但要保留原始错误和相邻上下文。

## 2. 第一步：确认 SSH 实际准备连接到哪里

SSH Config 中可能存在多个匹配规则。先在 Mac 执行：

```bash
ssh -G gpu-laptop-lan \
  | grep -E '^(hostname|user|port|identityfile|identitiesonly) '
```

期望看到类似：

```text
hostname 192.168.1.50
user student
port 22
identityfile ~/.ssh/id_ed25519_gpu_laptop
identitiesonly yes
```

如果 `hostname`、`user` 或 `port` 已经错误，后续网络和认证检查都会针对错误目标。先修改 `~/.ssh/config`，再运行 `ssh -G` 验证，不要继续猜测。

直接使用 IP 能连接，而别名不能连接时，问题通常在客户端 Config、名称解析或某个 `Host *` 规则，不在 Ubuntu 密钥本身。

## 3. `Could not resolve hostname`：名称没有解析成地址

典型错误：

```text
ssh: Could not resolve hostname gpu-laptop: nodename nor servname provided, or not known
```

这表示客户端连目标 IP 都还没有得到。先确认别名是否来自 SSH Config：

```bash
ssh -G gpu-laptop | grep '^hostname '
```

如果使用普通 DNS 或局域网主机名：

```bash
nslookup HOSTNAME
```

如果使用 Tailscale MagicDNS：

```bash
tailscale status
tailscale ping HOSTNAME
```

直接用可信 IP 测试：

```bash
ssh USERNAME@SERVER_IP
```

若 IP 可以连接，说明 SSH 服务和认证基本可用，应集中检查主机名、MagicDNS 和客户端配置。不要因为名称解析失败就重新生成密钥。

## 4. `Operation timed out`：请求没有得到回应

超时表示 Mac 发出的连接请求在规定时间内没有得到 TCP 响应。常见原因包括：

- Ubuntu 关机、休眠或掉线；
- 局域网地址已经变化；
- 两台设备不在可达网络；
- Tailscale 未连接或访问策略不允许；
- 防火墙丢弃连接；
- SSH 没有监听目标接口或端口；
- 路由器启用了访客网络隔离。

在 Mac 测试目标端口：

```bash
nc -vz HOST 22
```

在 Ubuntu 本机检查地址和服务：

```bash
hostname -I
ip route
systemctl is-active ssh
sudo ss -lntp | grep ':22'
```

若 Ubuntu 地址已变化，先更新 SSH Config 或路由器 DHCP 保留。若服务未运行，查看：

```bash
sudo systemctl status ssh
sudo journalctl -u ssh --no-pager -n 100
```

ping 使用不同协议。它只能提供辅助线索，不能替代 TCP 端口测试。

## 5. `Connection refused`：主机回应，但端口没有接受连接

典型错误：

```text
ssh: connect to host 192.168.1.50 port 22: Connection refused
```

这通常说明目标主机可达，但 TCP 22 没有程序监听，或者系统明确拒绝连接。

在 Ubuntu 本机执行：

```bash
systemctl status ssh
sudo ss -lntp | grep ':22'
sudo sshd -t
sudo journalctl -u ssh --no-pager -n 100
```

如果修改过端口，查看最终生效值：

```bash
sudo sshd -T | grep '^port '
```

同时在 Mac 检查客户端准备使用的端口：

```bash
ssh -G gpu-laptop-lan | grep '^port '
```

客户端连接 22，而服务端实际监听 2222，或相反，都会失败。不要在不了解现有配置时同时修改客户端、服务端和防火墙；一次只修正一个已确认的不一致点。

## 6. 主机身份警告：先确认服务器是谁

典型警告：

```text
REMOTE HOST IDENTIFICATION HAS CHANGED
```

这不是用户密码错误。Mac 在 `known_hosts` 中保存的服务器身份与本次收到的主机密钥不一致。

先通过 Ubuntu 本机控制台查看当前指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认系统确实重装过、主机密钥确实重建过，或者该地址现在仍属于预期设备后，在 Mac 只删除对应记录：

```bash
ssh-keygen -R HOSTNAME_OR_IP
```

重新连接时再次核对指纹。不要删除整个 `known_hosts`，也不要关闭 `StrictHostKeyChecking`。那会丢失其他服务器的身份记录，并把真正的地址冲突或攻击迹象一起掩盖。

## 7. `Permission denied`：网络已通，问题在用户认证

常见形式：

```text
Permission denied (publickey,password)
```

这通常说明 Mac 已经连接到 SSH 服务，但服务端不接受当前认证方式。先在 Mac 明确指定目标用户和私钥：

```bash
ssh -vv \
  -o IdentitiesOnly=yes \
  -i ~/.ssh/id_ed25519_gpu_laptop \
  USERNAME@HOST
```

检查以下内容：

1. `USERNAME` 是否是 Ubuntu 中真实存在的用户；
2. 指定的是私钥，而不是 `.pub` 文件；
3. 对应公钥是否位于该 Ubuntu 用户的 `~/.ssh/authorized_keys`；
4. Ubuntu 用户是否拥有自己的 `.ssh` 目录和文件；
5. 服务端是否允许公钥认证；
6. 私钥是否损坏或使用了错误的一把。

在 Ubuntu 本机或仍然可用的旧会话中执行：

```bash
whoami
ls -ld ~ ~/.ssh
ls -l ~/.ssh/authorized_keys
sudo sshd -T | grep -E 'pubkeyauthentication|passwordauthentication|authorizedkeysfile'
sudo journalctl -u ssh --no-pager -n 100
```

常见权限应类似：

```text
~/.ssh                  700
~/.ssh/authorized_keys  600
```

目录和文件还要属于目标用户。不要递归修改整个家目录权限，也不要把 `authorized_keys` 设置成所有人可写。

## 8. `Too many authentication failures`：客户端尝试了太多密钥

即使正确密钥存在，ssh-agent 中加载了很多其他密钥时，服务器可能在轮到正确密钥之前就停止尝试。

临时测试：

```bash
ssh \
  -o IdentitiesOnly=yes \
  -i ~/.ssh/id_ed25519_gpu_laptop \
  USERNAME@HOST
```

长期配置：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
```

查看 agent 中的密钥：

```bash
ssh-add -l
```

不要为了解决这个错误删除所有本地密钥。把目标主机限定到正确身份文件即可。

## 9. 密钥口令、账号密码和主机指纹要分开判断

连接过程中可能依次遇到三种提示：

```text
主机指纹确认
→ 验证服务器身份

Enter passphrase for key ...
→ 解锁 Mac 本地私钥

USERNAME@HOST's password:
→ 输入 Ubuntu 用户密码
```

它们不是同一件事。若你以为在输入 Ubuntu 密码，实际提示的是私钥 passphrase，就会不断得到错误。仔细阅读完整提示，而不是只看到“password”就尝试所有常用密码。

终端输入密码或 passphrase 时通常不显示字符，这是正常保护，不代表键盘失效。

## 10. SSH 能登录，但远程命令找不到

登录成功后出现：

```text
command not found: python
command not found: codex
```

问题已经不在网络或密钥层，而在远程 Ubuntu 环境。先执行：

```bash
hostname
whoami
pwd
printf '%s\n' "$SHELL"
printf '%s\n' "$PATH" | tr ':' '\n'
type -a python python3 git claude codex grok
```

常见原因包括：

- 登录到了错误用户；
- 工具只安装在 Mac，没有安装在 Ubuntu；
- Python 虚拟环境没有激活；
- 工具安装在另一个 Ubuntu 用户目录；
- 交互式 Shell 与非交互式命令加载的配置不同；
- VS Code Remote SSH 选择的是远程解释器；
- PATH 顺序与本地不同。

例如：

```bash
ssh gpu-laptop-lan 'codex --version'
```

这是非交互式远程命令，它不一定加载与普通交互式 zsh/bash 完全相同的配置。不要因为一个执行方式找不到命令，就重复安装工具；先比较 `PATH` 和命令位置。

## 11. scp 或 rsync 失败时先拆开验证

首先验证普通非交互 SSH：

```bash
ssh gpu-laptop-lan 'hostname && whoami'
```

验证远程目标目录：

```bash
ssh gpu-laptop-lan 'mkdir -p ~/projects && ls -ld ~/projects'
```

检查两端 rsync：

```bash
rsync --version
ssh gpu-laptop-lan 'rsync --version'
```

然后只做预演：

```bash
rsync -av --dry-run SOURCE/ gpu-laptop-lan:DESTINATION/
```

常见问题包括：目标目录不存在、远程用户没有写权限、源路径尾部斜杠不符合预期、某一端缺少 rsync，以及排除文件路径相对于错误目录。

## 12. 本地端口转发打不开页面

假设隧道是：

```bash
ssh -N -L 18888:127.0.0.1:8888 gpu-laptop-lan
```

按三段分别检查。

在 Ubuntu 确认服务监听：

```bash
ss -lntp | grep ':8888'
curl http://127.0.0.1:8888
```

在 Mac 确认本地端口由 SSH 监听：

```bash
lsof -nP -iTCP:18888 -sTCP:LISTEN
curl http://127.0.0.1:18888
```

如果 Ubuntu 自己都无法访问 127.0.0.1:8888，问题在远程服务，不在隧道。如果本地端口已被其他程序占用，SSH 会在建立隧道时提示绑定失败。不要只看 SSH 进程还在运行就假设转发成功。

## 13. 修改服务端配置后无法新建连接

如果旧连接仍在，保持它不要退出。在 Ubuntu 运行：

```bash
sudo sshd -t
sudo sshd -T | sed -n '1,120p'
sudo systemctl status ssh
sudo journalctl -u ssh --no-pager -n 100
```

检查最近添加的 `/etc/ssh/sshd_config.d/*.conf` 片段。修正后：

```bash
sudo sshd -t
sudo systemctl reload ssh
```

再从 Mac 第二个终端测试。只有新连接成功后才关闭旧会话。

如果所有远程会话都已断开，就需要使用 Ubuntu 本机键盘屏幕或其他已准备的管理入口。没有控制台的远程机器更应避免一次修改多项认证和防火墙设置。

## 14. Tailscale 在线但普通 OpenSSH 不通

如果通过 Tailscale 网络运行普通 OpenSSH，依次检查：

```bash
tailscale status
tailscale ping GPU_HOSTNAME
nc -vz GPU_HOSTNAME 22
ssh -vvv gpu-laptop-remote
```

还需要确认：

- 目标 Ubuntu 上的 OpenSSH 服务正在监听；
- tailnet 访问策略允许该来源访问目标 TCP 22；
- Ubuntu 防火墙没有拒绝 Tailscale 接口流量；
- SSH Config 的 `HostName` 是正确的 MagicDNS 名称或 Tailscale IP；
- 没有把普通 OpenSSH 与 Tailscale SSH 的认证机制混为一谈。

经 DERP 中继仍然是加密连接，通常只是路径和性能不同。不要为了显示 `direct` 而把路由器公网端口 22 暴露出去。

## 15. 一份可以交给他人或 AI 的脱敏报告

排查复杂问题时，可以整理：

```text
客户端系统：macOS 版本与 CPU 架构
服务端系统：Ubuntu 版本
连接方式：局域网 / Tailscale
目标别名：已脱敏
错误发生时间：
完整错误原文：

ssh -G 的关键字段：
- hostname: 脱敏
- user: 脱敏
- port:
- identityfile: 只保留文件名
- identitiesonly:

Mac 端：
- nc -vz 结果
- ssh -vvv 最后 30～80 行（已脱敏）

Ubuntu 端：
- systemctl is-active ssh
- ss 监听结果
- sshd -t 结果
- journalctl 相关错误行（已脱敏）

最近改动：
- SSH Config
- sshd_config.d
- UFW
- Tailscale policy
- 系统重装或地址变化
```

不要提供私钥正文、账号密码、Cookie、设备授权链接或完整内部网络信息。诊断需要的是结构和错误证据，不是把所有秘密交出去。

## 16. 固定排查顺序

在 Mac：

```bash
ssh -G ALIAS | grep -E '^(hostname|user|port|identityfile|identitiesonly) '
nc -vz HOST PORT
ssh -vvv ALIAS
```

在 Ubuntu：

```bash
hostname
hostname -I
systemctl is-active ssh
sudo ss -lntp | grep ':22'
sudo sshd -t
sudo sshd -T
sudo journalctl -u ssh --no-pager -n 100
```

按下面顺序判断：

```text
目标名称与客户端配置
→ 设备和网络是否可达
→ TCP 端口是否监听
→ 服务器主机身份是否可信
→ 用户与密钥认证是否成功
→ 登录后的远程 PATH 和项目环境是否正确
```

每一层确认后再进入下一层。这样不仅更快，也能避免为了修一个用户名错误而重装服务、重生成密钥或开放防火墙。

继续阅读：

- [SSH 基础与首次连接](01-SSH基础与首次连接.md)
- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
