# 01 Mac 与 Ubuntu 游戏本的局域网部署

> 最近核对：2026-07-29
>
> 本章默认设备组合为：一台日常使用的 Mac、一台安装 Windows 11 与 Ubuntu 24.04 双系统的 NVIDIA 游戏本，以及一个自己管理的路由器。训练节点使用 Ubuntu；Windows 分区不参与本章操作，也不会因为配置 Ubuntu SSH 而被修改。

你的目标不是把两台电脑强行变成完全相同的开发环境，而是建立一条清楚、可验证的链路：

```text
Mac
→ 写代码、看文档、做 Git 复核和轻量测试

Ubuntu 24.04 游戏本
→ Linux 依赖、NVIDIA GPU、数据集、模型和长时间训练

专属路由器
→ 提供稳定的同一局域网
```

完成本章后，Mac 应能通过一个固定别名连接 Ubuntu，并完成一次小文件传输。这里不安装 CUDA，不启动正式训练，也不开放公网端口；先把基础网络和 SSH 做对，后面的 GPU、tmux、rsync 和 VS Code 才有可靠地基。

## 1. 先确认物理和网络结构

推荐结构：

```text
互联网
  │
专属路由器
  ├── Mac：Wi-Fi 或网线
  └── Ubuntu 游戏本：优先网线，也可以 Wi-Fi
```

Ubuntu 能接网线时通常更稳定。训练计算发生在 Ubuntu 本机，局域网主要承担：

- SSH 控制；
- 源码和配置同步；
- 日志、图表和 checkpoint 回传；
- VS Code Remote SSH；
- Jupyter、TensorBoard 等服务的 SSH 隧道。

不要在路由器中配置公网端口转发。寝室外访问将在 [异网安全连接](06-异网安全连接.md) 中通过加密组网实现。

## 2. 在 Ubuntu 本机建立基础信息记录

这一节所有命令都在 **Ubuntu 游戏本本机终端** 执行，不是在 Mac 上执行。

```bash
hostname
whoami
uname -a
cat /etc/os-release
ip -brief address
ip route
```

重点记录：

```text
Ubuntu 主机名
Ubuntu 用户名
实际联网网卡
局域网 IPv4 地址
默认网关
```

`127.0.0.1` 只表示当前机器自身，不能作为 Mac 的连接目标。常见局域网地址可能是：

```text
192.168.x.x
10.x.x.x
172.16.x.x 到 172.31.x.x
```

如果 `hostname -I` 或 `ip -brief address` 显示多个地址，使用 `ip route` 查看哪张网卡负责默认路由。游戏本的有线网卡和无线网卡拥有不同的 IP 与 MAC 地址，后面做 DHCP 地址保留时不能混淆。

## 3. 安装并启动 OpenSSH Server

仍在 **Ubuntu 本机终端** 执行：

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

检查服务状态：

```bash
systemctl is-active ssh
systemctl is-enabled ssh
sudo ss -lntp | grep ':22'
```

正常情况下前两条分别显示：

```text
active
enabled
```

查看最近日志：

```bash
sudo journalctl -u ssh --no-pager -n 50
```

Ubuntu 支持在 `/etc/ssh/sshd_config.d/` 中保存配置片段。现在先使用系统默认配置，不要一开始就照抄“关闭密码、改端口、禁止所有用户”等硬化模板。以后确实需要修改时，固定采用：

```bash
sudo sshd -t
sudo systemctl reload ssh
```

`sshd -t` 没有输出通常表示语法检查通过。远程修改 SSH 配置时，要保留一个已连接会话或可用的本机控制台，避免把自己锁在外面。

## 4. 在 Ubuntu 核对主机指纹

第一次连接时，Mac 会显示主机指纹。先在 **Ubuntu 本机** 查看 Ed25519 主机密钥指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

记录输出中的 SHA256 指纹。以后 Mac 第一次连接时，应与这里核对，而不是看到提示就直接输入 `yes`。

主机指纹代表“这台 SSH 服务器是谁”。它和用户登录私钥不是同一把密钥。

## 5. 从 Mac 做第一次密码连接

假设 Ubuntu 信息为：

```text
用户名：YOUR_UBUNTU_USER
地址：192.168.50.20
```

在 **Mac 终端**执行：

```bash
ssh YOUR_UBUNTU_USER@192.168.50.20
```

第一次连接会显示类似：

```text
The authenticity of host ... can't be established.
ED25519 key fingerprint is SHA256:...
```

与 Ubuntu 本机记录的指纹一致后再接受。登录成功后立即执行：

```bash
hostname
whoami
pwd
ip route
```

这样可以确认自己连接的是正确机器、正确用户，而不是另一个使用相似地址的设备。

退出：

```bash
exit
```

如果第一次连接失败，先跳到本章第 11 节按层排查，不要同时修改防火墙、重装 SSH 和删除主机记录。

## 6. 在 Mac 创建专用登录密钥

以下命令在 **Mac 终端**执行：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_gpu_laptop
```

建议为私钥设置口令。生成后：

```text
~/.ssh/id_ed25519_gpu_laptop
→ 私钥，只留在 Mac

~/.ssh/id_ed25519_gpu_laptop.pub
→ 公钥，可以安装到 Ubuntu
```

不要把私钥粘贴到聊天、GitHub、网盘或项目目录中。

把公钥安装到 Ubuntu：

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_gpu_laptop.pub \
  YOUR_UBUNTU_USER@192.168.50.20
```

macOS 环境中如果没有 `ssh-copy-id`，可以先显示公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub
```

然后在 Ubuntu 本机把这一整行追加到：

```text
~/.ssh/authorized_keys
```

Ubuntu 上目录和文件权限应为：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

再次从 Mac 测试：

```bash
ssh -i ~/.ssh/id_ed25519_gpu_laptop \
  YOUR_UBUNTU_USER@192.168.50.20
```

## 7. 在 Mac 建立稳定 SSH 别名

编辑 Mac 的：

```text
~/.ssh/config
```

可以使用：

```bash
nano ~/.ssh/config
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

查看 OpenSSH 最终解析结果：

```bash
ssh -G gpu-laptop | grep -E '^(hostname|user|identityfile|serveralive)'
```

以后连接只需要：

```bash
ssh gpu-laptop
```

`ServerAliveInterval` 可以帮助更快发现网络中断，但不会让 Ubuntu 在关机、睡眠或系统崩溃后继续在线，也不能代替 tmux 和 checkpoint。

## 8. 在路由器中保留 Ubuntu 地址

DHCP 地址可能在重启后变化。优先在自己的路由器后台寻找：

```text
DHCP Reservation
静态租约
地址保留
IP 与 MAC 绑定
```

在 Ubuntu 查看当前网卡和 MAC：

```bash
ip -brief link
ip link show
```

只绑定实际用于连接路由器的那张网卡。绑定完成后重启网络或设备，再确认：

```bash
ip -brief address
ip route
```

然后从 Mac 验证：

```bash
ssh gpu-laptop
```

对个人局域网来说，路由器地址保留通常比在 Ubuntu 中手写静态地址更容易维护，也更不容易产生地址冲突。

## 9. 防火墙不要在未知状态下盲目修改

在 **Ubuntu 本机**检查：

```bash
sudo ufw status verbose
```

如果显示 `inactive`，不需要为了完成 SSH 教程立刻启用 UFW。先把网络和 SSH 跑通，再决定自己的防火墙策略。

如果 UFW 已启用，规则应只覆盖你确认的可信局域网。修改前：

1. 保留当前已登录 SSH 会话；
2. 确认专属路由器的真实网段；
3. 增加规则；
4. 从 Mac 新开第二个终端测试；
5. 第二个连接成功后再关闭旧会话。

“Ubuntu 允许局域网访问 TCP 22”和“路由器把公网端口转发到 Ubuntu”是完全不同的两件事。本手册不建议新手公开公网 SSH。

## 10. 防止睡眠和散热问题中断任务

游戏本进入睡眠后，SSH 和训练都会中断。Ubuntu 桌面中检查：

```text
Settings
→ Power
→ Automatic Suspend
```

接通电源时可以关闭自动睡眠，但还要确认：

- 机盖状态不会触发睡眠；
- 进风口和出风口不被遮挡；
- 使用稳定电源；
- 长时间训练时监控温度、功耗和显存；
- Windows 快速启动或双系统切换不会让你误以为 Ubuntu 仍在线。

修改合盖行为属于系统级电源配置。先保留本机控制能力并确认散热，再处理 `/etc/systemd/logind.conf` 等高级设置，不要只为了合盖训练直接照抄配置。

## 11. 按层排查连接失败

### 第一层：Ubuntu 是否在线

Mac：

```bash
ping 192.168.50.20
```

有些设备会屏蔽 ICMP，因此 ping 失败不能单独证明 SSH 失败。

### 第二层：TCP 22 是否可达

Mac：

```bash
nc -vz 192.168.50.20 22
```

### 第三层：SSH 详细过程

Mac：

```bash
ssh -vv gpu-laptop
```

### 第四层：Ubuntu 服务状态

Ubuntu 本机：

```bash
systemctl is-active ssh
sudo ss -lntp | grep ':22'
sudo journalctl -u ssh --no-pager -n 80
```

常见错误方向：

```text
Connection timed out
→ 地址、网络、路由、防火墙或设备离线

Connection refused
→ 主机可达，但目标端口没有服务监听

Permission denied
→ 用户名、密钥、文件权限或认证策略

Host key verification failed
→ 主机身份记录发生变化，必须先核实原因
```

不要把删除整个 `~/.ssh/known_hosts` 当成通用修复。确定只是该设备重装系统或重新生成主机密钥后，可以精准处理：

```bash
ssh-keygen -R 192.168.50.20
```

然后重新在 Ubuntu 本机核对指纹。

## 12. 建立分离的工作目录

在 **Ubuntu** 创建：

```bash
mkdir -p ~/projects ~/datasets ~/models ~/runs
```

在 **Mac** 创建：

```bash
mkdir -p ~/Projects ~/ML-Runs
```

职责约定：

```text
Ubuntu ~/projects
→ 源码工作区

Ubuntu ~/datasets
→ 数据集

Ubuntu ~/models
→ 模型权重与缓存

Ubuntu ~/runs
→ 每次训练的日志、指标和 checkpoint

Mac ~/Projects
→ 本地主源码

Mac ~/ML-Runs
→ 从 Ubuntu 拉回的结果
```

把大数据、模型和实验结果放在源码目录外，可以减少 Git、rsync、VS Code、语言服务器和 AI CLI 的误扫描。

## 13. 完成第一次端到端练习

### Ubuntu：创建测试目标

```bash
mkdir -p ~/projects/connection-test
printf 'hello from ubuntu\n' > ~/projects/connection-test/from-ubuntu.txt
```

### Mac：远程读取

```bash
ssh gpu-laptop 'cat ~/projects/connection-test/from-ubuntu.txt'
```

预期看到：

```text
hello from ubuntu
```

### Mac：创建本地文件

```bash
mkdir -p ~/terminal-practice/gpu-connection-test
printf 'hello from mac\n' \
  > ~/terminal-practice/gpu-connection-test/from-mac.txt
```

先预演：

```bash
rsync -av --dry-run \
  ~/terminal-practice/gpu-connection-test/ \
  gpu-laptop:~/projects/connection-test/
```

检查目标路径和文件列表后，正式同步：

```bash
rsync -av \
  ~/terminal-practice/gpu-connection-test/ \
  gpu-laptop:~/projects/connection-test/
```

最后从 Mac 验证：

```bash
ssh gpu-laptop \
  'find ~/projects/connection-test -type f -print -exec cat {} \;'
```

完成后，你已经建立了最小链路：

```text
Mac
→ 使用密钥通过 SSH 控制 Ubuntu
→ 使用 rsync 传输文件
→ Ubuntu 保持独立 Linux 与 GPU 环境
```

下一章会解决更容易出错的问题：两台机器谁是源码主副本、Git 与 rsync 各负责什么，以及怎样避免把 `.venv`、数据集和 checkpoint 互相覆盖。

## 继续阅读

- [项目同步与目录规范](02-项目同步与目录规范.md)
- [tmux 与断线后继续训练](03-tmux与断线续跑.md)
- [异网安全连接](06-异网安全连接.md)

官方参考：

- [Ubuntu Server：OpenSSH server](https://documentation.ubuntu.com/server/how-to/security/openssh-server/)
