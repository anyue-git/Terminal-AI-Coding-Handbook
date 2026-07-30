# 01 Mac 与 Ubuntu 游戏本的局域网部署

> 最近核对：2026-07-29
>
> 默认设备：一台日常使用的 Mac、一台安装 Windows 11 与 Ubuntu 24.04 双系统的 NVIDIA 游戏本，以及一个自己管理的路由器。训练节点使用 Ubuntu，Windows 分区不参与本章操作。

这套架构让 Mac 负责编辑、文档、Git 复核和轻量测试，Ubuntu 负责 Linux 依赖、NVIDIA GPU、数据集、模型与长时间训练。专属路由器只提供局域网连接，计算仍发生在 Ubuntu 本机。

```text
Mac
→ 主要源码、Git、文档与轻量测试

Ubuntu 24.04 游戏本
→ Linux、NVIDIA GPU、数据与长任务

专属路由器
→ SSH 控制和文件传输链路
```

本章完成后，Mac 应能通过固定别名连接 Ubuntu，并完成一次文件传输。CUDA、正式训练、tmux 和异网连接留给后续章节。

## 1. 确认 Ubuntu 的身份和局域网地址

Mac 与 Ubuntu 连接自己管理的同一路由器，游戏本条件允许时优先使用网线。以下命令在 **Ubuntu 游戏本本机终端**执行：

```bash
hostname
whoami
uname -a
cat /etc/os-release
ip -brief address
ip route
```

记录主机名、Linux 用户、实际联网网卡、局域网地址和默认网关。`127.0.0.1` 只代表当前机器自身，不能作为 Mac 的连接目标。常见私网地址位于 `192.168.x.x`、`10.x.x.x` 或 `172.16.x.x` 到 `172.31.x.x`；有线和无线同时出现时，以默认路由使用的网卡为准。

这条局域网可以承担 SSH、源码和配置同步、日志与 checkpoint 回传，以及 Jupyter、TensorBoard 等服务的 SSH 隧道。路由器不需要把 TCP 22 转发到公网；寝室外连接由[异网安全连接](06-异网安全连接.md)处理。

## 2. 启动 OpenSSH Server，并核对第一次连接

仍在 Ubuntu 本机安装服务：

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

检查启动状态和监听：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
sudo ss -lntp | grep ':22'
sudo journalctl -u ssh --no-pager -n 50
```

前两条通常分别返回 `active` 与 `enabled`。第一次部署先保持 Ubuntu 默认 SSH 配置；以后修改 `/etc/ssh/sshd_config` 或 `sshd_config.d/` 时，先运行：

```bash
sudo sshd -t
sudo systemctl reload ssh
```

`sshd -t` 没有输出通常表示语法检查通过。远程改登录配置时保留现有连接或本机控制台，避免同时失去修复入口。

主机指纹用于确认“服务器是谁”。在 Ubuntu 本机记录：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

假设用户名为 `YOUR_UBUNTU_USER`、地址为 `192.168.50.20`，在 **Mac 终端**连接：

```bash
ssh YOUR_UBUNTU_USER@192.168.50.20
```

Mac 首次显示的 Ed25519 指纹应与 Ubuntu 本机记录一致。接受并登录后检查：

```bash
hostname
whoami
pwd
ip route
```

确认目标机器和用户正确，再用 `exit` 返回 Mac。

## 3. 使用 Part 05 建立专用密钥和别名

密码连接成功后，按照[密钥登录与 SSH Config](../Part-05-SSH/02-密钥登录与SSH-Config.md)在 Mac 生成专用 Ed25519 密钥、把 `.pub` 公钥安装到 Ubuntu，并保留旧会话测试。完成后，Mac 的配置可以形成如下别名：

```sshconfig
Host gpu-laptop
  HostName 192.168.50.20
  User YOUR_UBUNTU_USER
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

验证最终解析和远程身份：

```bash
chmod 600 ~/.ssh/config
ssh -G gpu-laptop \
  | grep -E '^(hostname|user|identityfile|serveralive)'

ssh gpu-laptop 'hostname && whoami && pwd'
```

私钥只留在 Mac。`ServerAliveInterval` 帮助发现连接中断，无法让休眠、关机或崩溃后的 Ubuntu 保持在线，也不能替代 tmux 与 checkpoint。

## 4. 稳定地址、电源和防火墙

DHCP 地址可能在重启后变化。个人局域网优先在路由器后台设置 DHCP Reservation、静态租约或 IP/MAC 绑定。先在 Ubuntu 确认联网网卡和 MAC：

```bash
ip -brief link
ip link show
```

完成绑定并重新联网后检查：

```bash
ip -brief address
ip route
ssh gpu-laptop
```

防火墙先看现状：

```bash
sudo ufw status verbose
```

UFW 未启用时，无需为了 SSH 教程立刻改变整机防火墙。已经启用时，确认可信局域网网段，保留旧会话，添加必要规则后用 Mac 的第二个终端测试。局域网允许 TCP 22 与路由器公网端口转发是两种完全不同的影响范围。

游戏本进入睡眠后，SSH 和训练都会中断。Ubuntu 桌面中检查 `Settings → Power → Automatic Suspend`，接通电源时按需要调整自动睡眠，并确认合盖行为、稳定供电和散热条件。系统级电源配置修改应保留本机恢复方式。

## 5. 连接失败时先定位哪一层

从 Mac 检查设备、TCP 和 SSH 过程：

```bash
ping 192.168.50.20
nc -vz 192.168.50.20 22
ssh -vv gpu-laptop
```

`ping` 可能被设备屏蔽，不能单独判断主机离线。必要时回到 Ubuntu 本机：

```bash
systemctl is-active ssh
sudo ss -lntp | grep ':22'
sudo journalctl -u ssh --no-pager -n 80
```

```text
Connection timed out
→ 地址、网络、路由、防火墙或设备离线

Connection refused
→ 主机可达，但目标端口没有服务监听

Permission denied
→ 用户名、密钥、文件权限或认证策略

Host key verification failed
→ 主机身份记录变化，需要核实原因
```

系统重装或主机密钥确实重建后，精准删除对应记录并重新核对指纹：

```bash
ssh-keygen -R 192.168.50.20
```

更完整的分层排查见[SSH 故障排查](../Part-05-SSH/04-SSH故障排查.md)。

## 6. 建立目录并完成端到端验证

Ubuntu 建立运行侧目录：

```bash
mkdir -p ~/projects ~/datasets ~/models ~/runs
```

Mac 建立源码和结果目录：

```bash
mkdir -p ~/Projects ~/ML-Runs
```

约定 Ubuntu 的 `projects` 存放运行副本，`datasets`、`models` 和 `runs` 分别保存数据、权重缓存和实验输出；Mac 的 `Projects` 保存主要源码，`ML-Runs` 接收回传结果。

在 Ubuntu 创建测试文件：

```bash
mkdir -p ~/projects/connection-test
printf 'hello from ubuntu\n' \
  > ~/projects/connection-test/from-ubuntu.txt
```

Mac 读取它：

```bash
ssh gpu-laptop \
  'cat ~/projects/connection-test/from-ubuntu.txt'
```

再从 Mac 预演并同步一个文件：

```bash
mkdir -p ~/terminal-practice/gpu-connection-test
printf 'hello from mac\n' \
  > ~/terminal-practice/gpu-connection-test/from-mac.txt

rsync -av --dry-run \
  ~/terminal-practice/gpu-connection-test/ \
  gpu-laptop:~/projects/connection-test/

rsync -av \
  ~/terminal-practice/gpu-connection-test/ \
  gpu-laptop:~/projects/connection-test/

ssh gpu-laptop \
  'find ~/projects/connection-test -type f -print -exec cat {} \;'
```

到这里，Mac 已能通过专用密钥控制 Ubuntu，并完成文件传输。下一章决定两台机器谁是源码主副本，以及 Git 与 rsync 怎样分工。

继续阅读：[项目同步与目录规范](02-项目同步与目录规范.md)、[tmux 与断线后继续训练](03-tmux与断线续跑.md)和[异网安全连接](06-异网安全连接.md)。

官方参考：[Ubuntu Server：OpenSSH server](https://documentation.ubuntu.com/server/how-to/security/openssh-server/)。