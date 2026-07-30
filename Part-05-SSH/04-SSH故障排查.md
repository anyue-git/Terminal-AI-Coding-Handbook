# 04 SSH 故障排查

SSH 连接失败时，最有效的方法不是重装 OpenSSH、删除整个 `~/.ssh` 或同时修改客户端、服务端和防火墙，而是先确定失败发生在哪一层。错误信息本身通常已经排除了前面的若干层：`Permission denied` 表示网络和端口大概率已通，`Connection timed out` 则说明还没有进入用户认证。

本章以 Mac 连接 Ubuntu 游戏本为例，按“客户端目标—名称解析—网络与端口—主机身份—用户认证—远程环境—传输与隧道”的顺序排查。命令运行位置必须分清，避免在错误机器上检查错误对象。

## 1. 先保存客户端配置和详细日志

在 Mac 建立临时诊断目录，记录时间、版本和最终配置：

```bash
mkdir -p ~/terminal-practice/ssh-diagnosis
cd ~/terminal-practice/ssh-diagnosis
date
ssh -V

ssh -G gpu-laptop-lan \
  | grep -E '^(hostname|user|port|identityfile|identitiesonly|proxyjump|localforward) '
```

再做一次详细连接并保存错误输出：

```bash
ssh -vvv gpu-laptop-lan 2> ssh-debug.log
tail -n 80 ssh-debug.log
```

日志会显示客户端如何解析地址、建立 TCP 连接和尝试认证，可能包含真实用户名、IP、私钥路径和网络结构。发给外部 AI 或论坛前必须脱敏，但应保留原始错误与相邻上下文。

若 `ssh -G` 已显示错误的主机、用户、端口或私钥，先修正 `~/.ssh/config`；直接 IP 能连而别名不能连时，问题通常在 Config、名称解析或宽泛的 `Host *` 规则，而不是 Ubuntu 密钥。

## 2. 名称解析与超时发生在认证之前

`Could not resolve hostname` 表示客户端没有得到目标 IP。先检查 SSH 别名：

```bash
ssh -G gpu-laptop | grep '^hostname '
```

普通 DNS/局域网名称可用 `nslookup HOSTNAME`，Tailscale MagicDNS 可用：

```bash
tailscale status
tailscale ping HOSTNAME
```

再用可信 IP 测试：

```bash
ssh USERNAME@SERVER_IP
```

IP 可连时，应集中检查名称解析和客户端配置，不需要重新生成密钥。

`Operation timed out` 表示 TCP 请求没有得到回应。Mac 先测试端口：

```bash
nc -vz HOST 22
```

Ubuntu 本机检查地址、路由、服务和监听：

```bash
hostname -I
ip route
systemctl is-active ssh
sudo ss -lntp | grep ':22'
```

常见原因包括 Ubuntu 关机或休眠、局域网地址变化、访客网络隔离、Tailscale 未连接、访问策略或防火墙丢弃，以及 sshd 没有监听目标接口。ping 只能辅助判断，不能替代 TCP 端口测试。

## 3. 拒绝连接说明主机已回应，但端口不接受

典型错误为 `Connection refused`。在 Ubuntu 本机查看：

```bash
systemctl status ssh
sudo ss -lntp | grep ':22'
sudo sshd -t
sudo journalctl -u ssh --no-pager -n 100
sudo sshd -T | grep '^port '
```

同时在 Mac 检查客户端端口：

```bash
ssh -G gpu-laptop-lan | grep '^port '
```

客户端连接 22 而服务端监听 2222，或反过来，都会失败。一次只修正一个已确认的不一致点，不要同时改 Config、sshd 和 UFW。

## 4. 主机身份警告不能按认证失败处理

`REMOTE HOST IDENTIFICATION HAS CHANGED` 表示 Mac 保存的服务器身份与本次收到的主机密钥不一致，不是用户密码错误。先从 Ubuntu 本机控制台核对：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认系统重装、密钥重建或地址仍属于预期设备后，在 Mac 只删除对应记录：

```bash
ssh-keygen -R HOSTNAME_OR_IP
```

重新连接时再次核对指纹。不要删除整个 `known_hosts` 或关闭 `StrictHostKeyChecking`，否则其他服务器的身份记录和真正的地址冲突都会被掩盖。

## 5. `Permission denied` 表示进入了用户认证层

明确指定用户与私钥进行测试：

```bash
ssh -vv \
  -o IdentitiesOnly=yes \
  -i ~/.ssh/id_ed25519_gpu_laptop \
  USERNAME@HOST
```

检查目标用户是否真实存在，指定的是私钥而非 `.pub`，对应公钥是否在该用户的 `~/.ssh/authorized_keys`，目录和文件是否属于目标用户，以及服务端是否允许该认证方式。Ubuntu 本机或旧会话中执行：

```bash
whoami
ls -ld ~ ~/.ssh
ls -l ~/.ssh/authorized_keys
sudo sshd -T \
  | grep -E 'pubkeyauthentication|passwordauthentication|authorizedkeysfile'
sudo journalctl -u ssh --no-pager -n 100
```

常见权限为 `.ssh` 目录 `700`、`authorized_keys` `600`，但所有权同样重要。不要递归放宽整个家目录，也不要把授权文件设为所有人可写。

`Too many authentication failures` 常由 ssh-agent 中密钥过多导致。使用 `IdentitiesOnly=yes` 和明确 `IdentityFile`，并通过 `ssh-add -l` 查看 agent；不要为此删除所有本地密钥。

连接过程中还可能依次出现主机指纹确认、私钥 passphrase 和 Ubuntu 用户密码。三者分别验证服务器身份、解锁 Mac 私钥和认证远程账号，终端不显示输入字符属于正常保护。

## 6. 能登录但命令找不到，问题已转到远程环境

登录后出现 `python`、`codex` 等命令不存在，说明网络和密钥已经不是主要问题。先在远程执行：

```bash
hostname
whoami
pwd
printf '%s\n' "$SHELL"
printf '%s\n' "$PATH" | tr ':' '\n'
type -a python python3 git claude codex grok
```

常见原因是登录了错误用户、工具只安装在 Mac、虚拟环境未激活、工具属于另一个 Ubuntu 用户、交互式与非交互式 Shell 加载不同配置，或 PATH 顺序不同。

```bash
ssh gpu-laptop-lan 'codex --version'
```

这种非交互命令不一定读取与普通交互 Shell 完全相同的启动文件。不要因为一种启动方式找不到命令就重复安装，先比较可执行文件位置和 PATH。

## 7. scp、rsync 和隧道失败时先拆回普通 SSH

先验证非交互连接和目标目录：

```bash
ssh gpu-laptop-lan 'hostname && whoami'
ssh gpu-laptop-lan 'mkdir -p ~/projects && ls -ld ~/projects'
```

rsync 还要检查两端版本：

```bash
rsync --version
ssh gpu-laptop-lan 'rsync --version'
```

传输报错时核对冒号、源/目标方向、目录权限、末尾斜杠和远端磁盘空间。端口转发失败时，分别确认 SSH 本身可连、Ubuntu 目标服务确实监听、Mac 本地端口未被占用，以及 `-L` 中目标地址是从 Ubuntu 视角解释的。

```bash
lsof -nP -iTCP:LOCAL_PORT -sTCP:LISTEN
ssh gpu-laptop-lan 'ss -lntp | grep REMOTE_PORT'
```

## 8. 一条固定的诊断链

```text
ssh -G 确认客户端目标
→ 名称是否能解析为地址
→ nc 测试 TCP 端口
→ Ubuntu 检查地址、sshd 与监听
→ 核对主机指纹
→ 明确用户、私钥与 authorized_keys
→ 登录后检查远程 PATH 和解释器
→ 最后再排查 scp、rsync、VS Code 或端口转发
```

每次只改变一个已确认的问题点，并保留可工作的旧会话和本机控制台。让 AI 协助时，应提供脱敏错误与层次化证据，并明确禁止它自动删除 `known_hosts`、重建密钥、放宽权限、关闭防火墙或修改 sshd 后直接断开旧会话。

继续阅读：

- [SSH 基础与首次连接](01-SSH基础与首次连接.md)
- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
