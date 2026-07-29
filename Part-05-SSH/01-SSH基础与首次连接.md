# 01 SSH 基础与首次连接

SSH 用于从一台机器安全地登录另一台机器、执行命令和传输文件。本手册的主要场景是：Mac 负责日常编辑和管理，Ubuntu 游戏本提供 Linux、Docker 与 NVIDIA GPU。第一次连接应先在同一局域网内完成，异网访问放到后面的安全组网章节处理。

本章会完整走一遍：确认 Ubuntu 的 SSH 服务、找到局域网地址、从 Mac 测试端口、核对主机指纹、登录并确认远程环境。

## 1. 连接过程中有哪些角色

一次普通连接包含五个环节：

```text
Mac 上的 ssh 客户端
→ 局域网地址与 TCP 端口
→ Ubuntu 上的 sshd 服务
→ 主机身份验证
→ 用户认证与远程 Shell
```

最基本的连接形式是：

```bash
ssh USERNAME@SERVER_IP
```

例如 Ubuntu 用户名是 `student`，局域网地址是 `192.168.1.50`：

```bash
ssh student@192.168.1.50
```

命令中的用户名是 Ubuntu 用户，不是 Mac 用户、GitHub 用户或路由器账号。连接成功后，当前终端仍显示在 Mac 屏幕上，但键盘输入已经交给 Ubuntu 上的远程 Shell。

## 2. 在 Ubuntu 本机安装并检查服务

首次配置时，应坐在 Ubuntu 游戏本前，直接打开它的终端。不要在尚未建立的 SSH 会话中尝试完成这一步。

安装服务端：

```bash
sudo apt update
sudo apt install openssh-server
```

安装完成后启用并立即启动服务：

```bash
sudo systemctl enable --now ssh
```

检查状态：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
```

正常情况下会分别看到：

```text
active
enabled
```

再确认是否监听默认端口 22：

```bash
sudo ss -lntp | grep ':22'
```

代表性输出类似：

```text
LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=1234,fd=3))
LISTEN 0 128    [::]:22    [::]:* users:(("sshd",pid=1234,fd=4))
```

服务没有正常启动时，先查看日志：

```bash
sudo journalctl -u ssh --no-pager -n 50
```

不要在没有阅读日志前反复重启服务，也不要先把防火墙全部关闭。服务未运行、配置语法错误和端口被占用，都应分别处理。

## 3. 找到 Ubuntu 的局域网地址

仍然在 Ubuntu 本机执行：

```bash
hostname -I
ip route
```

`hostname -I` 可能输出多个地址，例如：

```text
192.168.1.50 172.17.0.1
```

`192.168.1.50` 可能是 Wi-Fi 或有线局域网地址，`172.17.0.1` 常见于 Docker 网桥。结合 `ip route` 查看默认路由使用哪个接口：

```text
default via 192.168.1.1 dev wlp4s0
```

这说明当前主要网络接口是 `wlp4s0`，通常应选择与默认路由同网段的 `192.168.1.50`。

不要使用：

```text
127.0.0.1
```

它只表示“当前这台机器自己”。在 Mac 上连接 `127.0.0.1`，目标会是 Mac，而不是 Ubuntu。

局域网地址可能在重启或重新联网后变化。长期使用时，可以在路由器中为 Ubuntu 设置 DHCP 地址保留，或者配置一个稳定的 SSH 别名；不要随意给网卡写死一个可能冲突的静态地址。

## 4. 在 Mac 上先测试端口

回到 Mac，打开新的 Terminal。先确认本机 SSH 客户端可用：

```bash
ssh -V
```

然后测试 Ubuntu 的 TCP 22 端口：

```bash
nc -vz 192.168.1.50 22
```

常见结果有三类：

```text
succeeded
```

表示网络路径和端口基本可达，可以继续登录。

```text
Connection refused
```

表示主机通常可达，但该端口没有服务监听，或者连接被明确拒绝。应回到 Ubuntu 检查 `systemctl status ssh` 和 `ss`。

```text
Operation timed out
```

表示请求没有得到响应，可能是地址错误、两台机器不在同一可达网络、Ubuntu 休眠、防火墙丢弃连接或设备离线。

`ping` 可以辅助判断设备是否在线，但它使用的协议与 SSH 不同。ping 失败不能单独证明 TCP 22 不通，ping 成功也不能证明 SSH 服务正常。

## 5. 第一次连接先核对主机指纹

在 Mac 执行：

```bash
ssh student@192.168.1.50
```

第一次连接通常会看到类似提示：

```text
The authenticity of host '192.168.1.50' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

这不是普通的“是否继续”弹窗，而是在询问你是否信任目标机器的主机密钥。先到 Ubuntu 本机查看 Ed25519 主机指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认 Ubuntu 显示的指纹与 Mac 提示一致，再输入：

```text
yes
```

记录会写入 Mac 的：

```text
~/.ssh/known_hosts
```

以后同一地址的主机密钥发生变化，SSH 会发出醒目警告。不要通过关闭主机密钥检查、自动接受所有主机或删除整个 `known_hosts` 来绕过它。

## 6. 使用 Ubuntu 用户密码完成首次验证

主机身份确认后，SSH 会要求输入 Ubuntu 用户密码。输入时终端通常不显示字符和星号，这是正常行为。输入完成后按回车即可。

这里需要的是 Ubuntu 本地用户密码，不是：

- Mac 登录密码；
- Wi-Fi 密码；
- GitHub 密码；
- 路由器管理密码；
- 磁盘加密恢复密钥。

密码登录适合首次验证和恢复入口。长期使用应配置专用 SSH 密钥，确认密钥登录稳定后，再考虑是否关闭密码认证。

## 7. 登录后立即确认远程环境

连接成功后执行：

```bash
hostname
whoami
pwd
uname -a
```

可能看到：

```text
gpu-laptop
student
/home/student
Linux gpu-laptop ... x86_64 GNU/Linux
```

这四条输出分别确认远程主机、用户、当前目录和操作系统。之后运行的 `python`、`git`、`docker`、`claude`、`codex` 和文件操作，都使用 Ubuntu 的环境。

可以进一步查看：

```bash
printf '%s\n' "$SHELL"
printf '%s\n' "$PATH" | tr ':' '\n'
type -a python3 git docker
```

Mac 和 Ubuntu 的软件、PATH、虚拟环境和文件系统彼此独立。在 SSH 窗口中删除文件，删除的是 Ubuntu 文件；在这里创建 Python 虚拟环境，环境也位于 Ubuntu 磁盘。

## 8. 正常退出与连接卡死

正常退出远程 Shell：

```bash
exit
```

也可以按 `Ctrl + D`，但新手更适合明确输入 `exit`，避免在其他程序中误触 EOF。

网络中断后终端可能没有立即返回提示符。OpenSSH 客户端支持逃逸序列：先按一次回车，让光标位于新行开头，然后依次输入：

```text
~.
```

这会终止当前 SSH 客户端连接。波浪号必须出现在新行开头，且不需要再按 Ctrl。

断开 SSH 不保证远程前台任务继续。训练、下载或长时间服务应放在 tmux、systemd、作业调度器或经过验证的后台容器中，并保存日志和 checkpoint。

## 9. 防火墙只在确认需要时处理

Ubuntu 可能没有启用 UFW，也可能已有团队或个人规则。先检查：

```bash
sudo ufw status verbose
```

如果状态是 `inactive`，连接问题不来自 UFW。若状态为 `active` 且没有允许 SSH，应先确认当前连接来源和网络边界，再添加最小规则。远程修改防火墙时要保留现有会话，并准备本机控制台，避免把自己锁在机器外。

同一局域网首次连接不需要把 TCP 22 暴露到公网。更换端口也不会自动提供安全性；密钥认证、主机身份验证、最小暴露和正确访问控制更加重要。

## 10. 修改服务端配置的安全流程

Ubuntu 的 OpenSSH 服务端配置主要来自：

```text
/etc/ssh/sshd_config
/etc/ssh/sshd_config.d/*.conf
```

Ubuntu 默认配置通常会包含 `sshd_config.d` 下的片段。添加本地规则时，使用单独文件通常比直接大改主配置更容易检查和恢复。

修改前查看最终生效值：

```bash
sudo sshd -T
```

修改后先检查语法：

```bash
sudo sshd -t
```

远程修改时应遵循：

```text
保留当前 SSH 会话
→ 准备 Ubuntu 本机控制台或备用入口
→ 写入最小配置变更
→ sudo sshd -t
→ reload ssh
→ 在第二个 Mac 终端测试新连接
→ 成功后才关闭旧会话
```

重载服务：

```bash
sudo systemctl reload ssh
```

语法检查失败时不要 reload，先修正配置。不要让 AI CLI 在没有备用入口的情况下自行改认证方式、防火墙和监听端口。

## 11. 本章完成后的检查

在 Ubuntu 本机：

```bash
systemctl is-active ssh
hostname -I
sudo ss -lntp | grep ':22'
```

在 Mac：

```bash
nc -vz SERVER_IP 22
ssh USERNAME@SERVER_IP
```

登录后：

```bash
hostname
whoami
pwd
```

这套流程确认了服务端运行、网络地址正确、端口可达、主机身份已核对、用户认证成功，以及登录后的机器和账号符合预期。

继续阅读：

- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [scp、rsync 与端口转发](03-scp-rsync与端口转发.md)
- [SSH 故障排查](04-SSH故障排查.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)

官方参考：

- [Ubuntu Server：OpenSSH server](https://documentation.ubuntu.com/server/how-to/security/openssh-server/)
