# 01 Mac 与 Ubuntu 游戏本的局域网部署

你的设备条件可以采用一套很直接的架构：

```text
Mac
→ 日常编辑、Git、文档和轻量测试

Ubuntu 24 游戏本
→ NVIDIA GPU、Linux 环境和长时间训练

专属路由器
→ 让两台设备在同一局域网内稳定通信
```

目标不是把 Ubuntu 变成第二台日常电脑，而是把它当作一台可以从 Mac 安全控制的计算节点。

---

## 1. 先决定网络结构

推荐：

```text
专属路由器
├── Mac
└── Ubuntu 游戏本
```

Ubuntu 如果能接网线，通常比两台设备都使用 Wi-Fi 更稳定。训练本身在 Ubuntu 本地执行，网络主要影响：

- 源码和数据同步；
- 模型下载；
- checkpoint 回传；
- VS Code Remote SSH；
- Jupyter 和日志查看。

局域网阶段不要配置公网端口转发。异网访问将在 [异网安全连接](06-异网安全连接.md) 中通过安全组网处理。

---

## 2. 在 Ubuntu 安装 OpenSSH Server

先在 Ubuntu 本机终端执行：

```bash
sudo apt update
sudo apt install openssh-server
```

启动并设置开机启动：

```bash
sudo systemctl enable --now ssh
```

检查：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
```

理想结果是：

```text
active
enabled
```

查看服务日志：

```bash
sudo journalctl -u ssh --no-pager -n 50
```

如果未来修改 SSH 服务配置，先运行：

```bash
sudo sshd -t
```

只有语法检查通过，才考虑重新加载服务。远程操作时应保留第二个已登录会话或本机控制台，避免把自己锁在外面。

---

## 3. 找到 Ubuntu 用户名和局域网地址

用户名：

```bash
whoami
```

局域网地址：

```bash
hostname -I
ip route
```

常见私有地址范围包括：

```text
192.168.x.x
10.x.x.x
172.16.x.x ～ 172.31.x.x
```

不要使用：

```text
127.0.0.1
```

它只代表当前机器自身。

如果 `hostname -I` 返回多个地址，结合 `ip route` 判断实际连接专属路由器的网卡。Wi-Fi 和有线网卡通常拥有不同地址和不同 MAC 地址。

---

## 4. 第一次从 Mac 连接

假设：

```text
Ubuntu 用户名：YOUR_UBUNTU_USER
Ubuntu 地址：192.168.50.20
```

在 Mac 执行：

```bash
ssh YOUR_UBUNTU_USER@192.168.50.20
```

首次连接会询问主机指纹。不要不看内容就输入确认。可以在 Ubuntu 本机查看 Ed25519 主机密钥指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

核对一致后再接受。

登录后立即确认没有连错机器：

```bash
hostname
whoami
pwd
```

---

## 5. 配置密钥登录

在 Mac 生成一把专用于游戏本的密钥：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_gpu_laptop
```

建议设置口令，并通过 `ssh-agent` 管理。私钥文件是：

```text
~/.ssh/id_ed25519_gpu_laptop
```

不要上传、粘贴或同步它。

把公钥安装到 Ubuntu：

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_gpu_laptop.pub \
  YOUR_UBUNTU_USER@192.168.50.20
```

如果系统没有 `ssh-copy-id`，可以手工把 `.pub` 公钥内容追加到 Ubuntu 用户的：

```text
~/.ssh/authorized_keys
```

只传公钥，不传私钥。

---

## 6. 在 Mac 创建 SSH 别名

编辑：

```text
~/.ssh/config
```

加入：

```sshconfig
Host gpu-laptop
  HostName 192.168.50.20
  User YOUR_UBUNTU_USER
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

设置权限：

```bash
chmod 600 ~/.ssh/config
```

检查最终解析结果：

```bash
ssh -G gpu-laptop | sed -n '1,30p'
```

以后连接：

```bash
ssh gpu-laptop
```

SSH Config 中写的是私钥路径，不是私钥正文。

---

## 7. 让 Ubuntu 获得稳定局域网地址

Ubuntu 的 DHCP 地址可能在路由器或机器重启后变化。优先在路由器后台设置：

```text
DHCP Reservation
静态租约
地址保留
IP 与 MAC 绑定
```

原理是让指定网卡每次获得同一个局域网地址。

查看当前网卡信息：

```bash
ip link
```

找到实际使用网卡的 `link/ether` 地址。不要把 Wi-Fi 网卡的 MAC 绑定到有线网卡地址，反之亦然。

相比直接在 Ubuntu 手工配置静态 IP，路由器地址保留通常更容易维护，也更不容易产生地址冲突。

---

## 8. 防火墙只在确认现状后修改

查看 UFW：

```bash
sudo ufw status verbose
```

如果 UFW 没有启用，不需要为了“看起来更专业”立刻开启。先保证 SSH 正常，并理解现有网络。

如果 UFW 已经启用，应只允许可信局域网访问 SSH。概念形式是：

```text
允许专属局域网网段
→ 访问 Ubuntu 的 TCP 22
```

具体网段必须根据自己的路由器确认，不要照抄示例地址。修改规则后保留当前 SSH 会话，再从第二个终端测试新连接。

不要把“允许 22 端口”理解成“必须把公网 22 暴露出去”。局域网主机防火墙和路由器公网转发是两件事。

---

## 9. 按层排查连接问题

从 Mac 依次检查：

### Ubuntu 是否在线

```bash
ping 192.168.50.20
```

有些设备会屏蔽 ICMP，所以 ping 失败不能单独证明 SSH 失败。

### TCP 22 是否可达

```bash
nc -vz 192.168.50.20 22
```

### SSH 连接过程

```bash
ssh -v gpu-laptop
```

Ubuntu 端检查：

```bash
systemctl is-active ssh
sudo ss -lntp | grep ':22'
sudo journalctl -u ssh --no-pager -n 50
```

常见错误的大致方向：

```text
Connection timed out
→ 网络、地址、防火墙或设备离线

Connection refused
→ 主机可达，但 SSH 服务没有监听

Permission denied
→ 用户名、密钥或认证配置

Host key verification failed
→ 主机身份记录发生变化，需要先核实原因
```

不要把删除 `known_hosts` 当成通用修复。主机指纹变化也可能意味着连到了另一台机器。

---

## 10. 防止训练被休眠打断

Ubuntu 游戏本进入睡眠后，SSH 和训练通常都会中断。

桌面设置中检查：

```text
Settings
→ Power
→ Automatic Suspend
```

接通电源时可以关闭自动睡眠，但游戏本长时间训练还要考虑：

- 保持机盖打开；
- 不遮挡进风和出风口；
- 使用稳定电源；
- 监控温度和显存；
- 不把机器塞进封闭空间。

合盖不休眠属于系统级电源策略修改。不要在不了解散热和备用访问方式时直接改配置。

---

## 11. 建立清晰目录

Ubuntu：

```text
~/projects/    源码
~/datasets/    数据集
~/models/      模型权重
~/runs/        实验输出
```

Mac：

```text
~/Projects/    日常项目
~/ML-Runs/     拉回的实验结果
```

源码、数据、模型和训练输出分开后，Git、rsync、编辑器和 AI CLI 都更不容易扫描或搬运无关大文件。

---

## 12. 完成第一次端到端测试

Ubuntu：

```bash
mkdir -p ~/projects/connection-test
printf 'hello from ubuntu\n' > ~/projects/connection-test/hello.txt
```

Mac 读取：

```bash
ssh gpu-laptop 'cat ~/projects/connection-test/hello.txt'
```

Mac 创建测试文件：

```bash
mkdir -p ~/terminal-practice/gpu-test
printf 'hello from mac\n' > ~/terminal-practice/gpu-test/mac.txt
```

先预演同步：

```bash
rsync -av --dry-run \
  ~/terminal-practice/gpu-test/ \
  gpu-laptop:~/projects/connection-test/
```

确认源目录、目标目录和文件列表后，再去掉 `--dry-run`。最后检查：

```bash
ssh gpu-laptop \
  'find ~/projects/connection-test -maxdepth 2 -type f -print'
```

到这里，局域网计算节点的基础链路已经完成：

```text
Mac
→ SSH 控制 Ubuntu
→ rsync 传输文件
→ Ubuntu 本地使用 GPU
```

继续阅读：

- [项目同步与目录规范](02-项目同步与目录规范.md)
- [tmux 与断线后继续训练](03-tmux与断线续跑.md)
- [异网安全连接](06-异网安全连接.md)
- [Mac 到 Ubuntu GPU 的端到端案例](../Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)

官方参考：

- [Ubuntu：OpenSSH server](https://ubuntu.com/server/docs/how-to/security/openssh-server/)
- [Ubuntu：Firewall](https://documentation.ubuntu.com/server/how-to/security/firewalls/)
