# 01 SSH 基础与首次连接

SSH 用于从一台机器安全登录另一台机器、执行命令和传输文件。本手册的主要场景是 Mac 负责日常编辑和管理，Ubuntu 游戏本提供 Linux、Docker 与 NVIDIA GPU。第一次连接先在同一局域网内完成：在 Ubuntu 本机启用服务并确认地址，在 Mac 测试端口、核对主机指纹，再登录并确认远程环境。异网访问放到后面的安全组网章节处理。

一次连接可以理解为：Mac 上的 `ssh` 客户端通过网络和 TCP 端口找到 Ubuntu 的 `sshd`，先验证服务器身份，再验证用户身份，最后启动远程 Shell。最基本形式是：

```bash
ssh USERNAME@SERVER_IP
```

这里的用户名属于 Ubuntu，不是 Mac、GitHub 或路由器账号。连接成功后窗口仍显示在 Mac 屏幕上，但后续命令已经在 Ubuntu 执行。

## 1. 在 Ubuntu 本机准备 SSH 服务

首次配置应直接坐在 Ubuntu 游戏本前操作，不要在尚未建立的远程会话中想象执行。安装并启用服务：

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

随后从服务状态、监听端口和日志三个角度确认：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
sudo ss -lntp | grep ':22'
```

正常情况下前两条分别显示 `active` 和 `enabled`，端口检查能看到 `sshd` 监听 22。若服务没有正常启动，查看：

```bash
sudo journalctl -u ssh --no-pager -n 50
```

不要在没读日志前反复重启，也不要先关闭整个防火墙。服务未运行、配置语法错误和端口被占用属于不同问题。

仍在 Ubuntu 本机查找局域网地址：

```bash
hostname -I
ip route
```

输出可能同时包含 `192.168.1.50` 和 Docker 网桥的 `172.17.0.1`。结合默认路由所用接口，通常选择与路由器同网段的局域网地址。`127.0.0.1` 只表示当前机器自己；在 Mac 连接它，目标仍是 Mac。局域网地址可能随重启变化，长期使用可在路由器中设置 DHCP 保留，而不是随意写死可能冲突的静态地址。

## 2. 在 Mac 测试网络和端口

回到 Mac 新开终端，先确认客户端存在，再测试 Ubuntu 的 22 端口：

```bash
ssh -V
nc -vz 192.168.1.50 22
```

结果为 `succeeded`，说明网络路径和端口基本可达；`Connection refused` 通常表示主机回应但没有服务监听，应该回 Ubuntu 检查 `systemctl` 和 `ss`；`Operation timed out` 表示请求没有得到回应，可能是地址错误、设备休眠、网络隔离、防火墙丢弃或机器离线。`ping` 只能辅助判断在线状态，它与 SSH 使用的 TCP 端口不同，不能替代端口测试。

## 3. 第一次连接必须核对主机身份

在 Mac 执行：

```bash
ssh student@192.168.1.50
```

第一次通常会显示目标主机的 Ed25519 指纹，并询问是否继续。这不是普通的确认弹窗，而是在问你是否信任这台服务器。先到 Ubuntu 本机查看实际指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

两边一致后再输入 `yes`。记录会写入 Mac 的 `~/.ssh/known_hosts`。以后同一地址的主机密钥变化时，SSH 会发出强烈警告；不要通过关闭主机检查、自动接受所有主机或删除整个 `known_hosts` 来绕过。

主机身份确认后，输入 Ubuntu 用户密码。终端通常不会显示字符或星号，这是正常行为。这里需要的不是 Mac 密码、Wi-Fi 密码、GitHub 密码或路由器密码。密码登录适合首次验证和恢复入口；长期使用应配置专用 SSH 密钥，并在密钥登录稳定后再评估是否关闭密码认证。

## 4. 登录后立即确认远程环境

进入远程 Shell 后先运行：

```bash
hostname
whoami
pwd
uname -a
printf '%s\n' "$SHELL"
type -a python3 git docker
```

代表性结果可能是 Ubuntu 主机名、目标用户名、`/home/USERNAME` 和 Linux x86_64。之后执行的 Python、Git、Docker、AI CLI 和文件操作都使用 Ubuntu 的环境。Mac 与 Ubuntu 的 PATH、虚拟环境、软件安装和文件系统彼此独立；在 SSH 窗口创建的 `.venv` 位于 Ubuntu 磁盘，在这里删除文件也删除 Ubuntu 上的对象。

正常退出使用：

```bash
exit
```

网络卡死时，OpenSSH 客户端支持逃逸序列：先按回车进入新行，再依次输入 `~.`，即可终止当前客户端连接。断开 SSH 不保证远程前台任务继续，训练和长服务应放在 tmux、systemd、作业调度器或经过验证的后台容器中，并保存日志和 checkpoint。

## 5. 防火墙和服务端配置要保留备用入口

先查看 UFW 状态：

```bash
sudo ufw status verbose
```

若显示 `inactive`，问题不来自 UFW；若已启用且没有允许 SSH，应根据来源网络添加最小规则。远程修改防火墙时必须保留当前会话，并准备 Ubuntu 本机控制台，避免把自己锁在机器外。同一局域网首次连接不需要把 22 端口暴露到公网；更换端口也不能替代密钥认证、主机身份验证和最小暴露。

服务端配置主要来自 `/etc/ssh/sshd_config` 与 `/etc/ssh/sshd_config.d/*.conf`。修改前查看最终生效值，修改后先检查语法：

```bash
sudo sshd -T
sudo sshd -t
```

安全流程应是：保留旧会话和本机入口，写入最小配置，`sshd -t` 通过后 reload，在第二个 Mac 终端测试新连接，成功后才关闭旧会话。

```bash
sudo systemctl reload ssh
```

语法失败时不要 reload，也不要让 Agent 在没有备用入口的情况下自行改变认证方式、防火墙和监听端口。

## 6. 首次连接的完整验收

Ubuntu 本机确认服务、地址与监听：

```bash
systemctl is-active ssh
hostname -I
sudo ss -lntp | grep ':22'
```

Mac 确认端口并连接：

```bash
nc -vz SERVER_IP 22
ssh USERNAME@SERVER_IP
```

登录后确认：

```bash
hostname
whoami
pwd
```

这条链同时验证了服务端、网络地址、端口、服务器身份、用户认证和远程运行位置。下一章将在这个可用的密码入口上配置专用用户密钥和 SSH Config。

继续阅读：

- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [SSH 故障排查](04-SSH故障排查.md)
- [Mac 与 Ubuntu 游戏本的局域网部署](../Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md)
