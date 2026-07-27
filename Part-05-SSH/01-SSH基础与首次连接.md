# 01 SSH 基础与首次连接

SSH（Secure Shell）用于安全地远程登录、执行命令和传输数据。

本手册的典型场景：

```text
Mac
→ SSH
→ Ubuntu 游戏本
→ Linux、GPU、Docker、数据和训练任务
```

本章先完成同一局域网中的普通 OpenSSH 连接。异网访问通过 Tailscale 等安全组网处理，不把公网端口转发作为新手默认方案。

---

## 1. SSH 连接包含哪些环节

```text
Mac 上的 SSH 客户端
→ 网络地址和端口
→ Ubuntu 上的 SSH 服务
→ 主机身份验证
→ 用户认证
→ 远程 Shell
```

基本命令：

```bash
ssh USERNAME@SERVER_IP
```

例如：

```bash
ssh ubuntu@192.168.1.50
```

修改端口并不会自动提高安全性。真正重要的是密钥、主机身份验证、访问控制和最小网络暴露。

---

## 2. Ubuntu 端安装并检查服务

Mac 通常已有客户端：

```bash
ssh -V
```

Ubuntu 安装服务端：

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

检查：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
sudo ss -lntp | grep ':22'
```

查看日志：

```bash
sudo journalctl -u ssh --no-pager -n 50
```

服务没有监听时，先查服务和配置，不要先乱改防火墙。

---

## 3. 找到正确的局域网地址

Ubuntu：

```bash
hostname -I
ip route
```

局域网地址通常是：

```text
192.168.x.x
10.x.x.x
172.16.x.x ～ 172.31.x.x
```

不要使用：

```text
127.0.0.1
```

它只代表当前机器。

如果出现多个地址，排除 Docker、VPN 和当前不用的虚拟接口，选择与 Mac 同网段的地址。

---

## 4. 先测端口，再登录

Mac：

```bash
nc -vz SERVER_IP 22
```

常见结果：

```text
succeeded
→ TCP 端口可达

Connection refused
→ 主机可达，但没有服务监听或被明确拒绝

timed out
→ 地址、路由、防火墙、休眠或设备离线
```

然后连接：

```bash
ssh USERNAME@SERVER_IP
```

`ping` 可以辅助判断设备是否在线，但 ICMP 可能被屏蔽，因此 ping 失败不能单独证明 SSH 不通。

---

## 5. 第一次连接必须核对主机指纹

首次连接会询问是否信任目标主机。

在 Ubuntu 本机查看 Ed25519 主机指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

与 Mac 显示内容核对后再接受。记录会写入：

```text
~/.ssh/known_hosts
```

不要通过关闭主机密钥检查、自动接受所有主机或删除整个 `known_hosts` 来绕过警告。

---

## 6. 密码登录只用于首次验证或恢复

首次登录可能要求 Ubuntu 用户密码。输入时终端不显示星号是正常现象。

这个密码不是 Mac、Wi-Fi、路由器或 GitHub 密码。

长期使用应配置 SSH 密钥。密钥稳定工作后，再评估是否禁用密码认证。

---

## 7. 登录后确认自己在哪台机器

```bash
hostname
whoami
pwd
uname -a
```

远程会话中执行的命令使用 Ubuntu 的文件系统、PATH、Python、Docker、GPU 和权限。

在 SSH 窗口中删除文件，删除的是远程机器上的文件。

---

## 8. 正常退出和卡死断开

正常退出：

```bash
exit
```

SSH 卡死时，可以使用 OpenSSH 逃逸序列：

```text
按 Enter
然后输入 ~.
```

它只断开客户端连接，不保证远程前台任务继续运行。

长任务应使用 tmux、systemd、任务调度器或经过验证的后台容器。

---

## 9. 修改 SSH 服务配置时的安全流程

主要配置位置：

```text
/etc/ssh/sshd_config
/etc/ssh/sshd_config.d/*.conf
```

查看最终生效配置：

```bash
sudo sshd -T
```

修改后先检查语法：

```bash
sudo sshd -t
```

远程修改时：

```text
保留当前会话
→ 准备本机控制台或备用入口
→ 检查配置语法
→ reload 服务
→ 第二个终端测试新连接
→ 成功后再关闭旧会话
```

---

## 10. 公网边界

新手阶段不推荐：

```text
公网地址
→ 路由器端口转发
→ Ubuntu TCP 22
```

个人 Mac + Ubuntu 游戏本优先使用安全组网，再在其上运行普通 OpenSSH。

更改端口、隐藏主机名或依赖弱密码都不能替代真正的访问控制。

---

## 11. 最小首次连接流程

Ubuntu：

```bash
systemctl is-active ssh
hostname -I
sudo ss -lntp | grep ':22'
```

Mac：

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

继续阅读：

- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [scp、rsync 与端口转发](03-scp-rsync与端口转发.md)
- [SSH 故障排查](04-SSH故障排查.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
