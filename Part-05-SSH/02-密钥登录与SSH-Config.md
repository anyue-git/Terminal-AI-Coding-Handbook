# 02 密钥登录与 SSH Config

密码可以完成首次连接，但长期从 Mac 使用 Ubuntu，更适合专用 SSH 密钥和清晰的客户端配置。密钥登录不是把账号密码换成另一串文本，而是由 Mac 私钥完成签名，Ubuntu 使用已登记的公钥验证；私钥始终留在可信客户端，不应上传服务器、仓库、网盘或交给 AI。

本章假设你已经通过密码成功登录 Ubuntu，并核对过主机指纹。整个过程遵循“在 Mac 生成身份、只把公钥安装到正确用户、保留旧会话测试、最后再简化连接”的顺序。

## 1. 先分清用户密钥、主机密钥和客户端记录

Mac 的 `~/.ssh` 中可能包含：

```text
id_ed25519_gpu_laptop       用户私钥
id_ed25519_gpu_laptop.pub   配对公钥
known_hosts                 已核对的服务器身份
config                      客户端连接规则
```

Ubuntu 还拥有 `/etc/ssh/ssh_host_ed25519_key` 等主机密钥，用来证明“服务器是谁”，与用户登录密钥不是同一组。没有 `.pub` 后缀的身份文件通常是私钥；公钥可加入目标用户的 `authorized_keys`；`known_hosts` 记录服务器身份；`~/.ssh/config` 只保存连接参数，不应包含任何私钥正文。

## 2. 在 Mac 创建并保护专用密钥

为游戏本生成一把用途明确的 Ed25519 密钥：

```bash
ssh-keygen -t ed25519 \
  -C "mac-to-gpu-laptop" \
  -f ~/.ssh/id_ed25519_gpu_laptop
```

建议设置自己能长期管理的 passphrase，它用于保护磁盘上的私钥文件，不是 Ubuntu 用户密码。生成后检查文件名和权限：

```bash
ls -l ~/.ssh/id_ed25519_gpu_laptop*
```

私钥通常为 `600`，公钥可读范围更宽。只查看公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub
```

不要 `cat` 私钥，也不要把它复制进聊天、Issue、PR、日志或远程命令。为不同重要目标使用有说明的专用密钥，比所有服务器共用一把无名称默认密钥更容易撤销和审计。

## 3. 将公钥安装到正确的 Ubuntu 用户

先通过密码登录 Ubuntu，在远程用户自己的主目录中建立授权文件：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
```

将 Mac 上 `.pub` 文件的完整一行粘贴进去，保存后执行：

```bash
chmod 600 ~/.ssh/authorized_keys
whoami
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys
```

公钥安装到错误用户的家目录时，正确私钥也无法登录目标账号。熟悉后也可以从 Mac 通过管道追加公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub \
  | ssh USERNAME@SERVER_IP \
  'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
```

执行前必须重新核对本地文件确实以 `.pub` 结尾、远程用户名和地址正确。绝不能把私钥路径替换进去。

## 4. 保留旧会话，在新终端测试身份

不要立即关闭仍可使用的密码会话。在 Mac 第二个终端中明确指定私钥：

```bash
ssh -i ~/.ssh/id_ed25519_gpu_laptop \
  -o IdentitiesOnly=yes \
  USERNAME@SERVER_IP
```

成功后检查：

```bash
hostname
whoami
pwd
```

`IdentitiesOnly=yes` 避免客户端先尝试 agent 中大量其他密钥。若仍要求 Ubuntu 账号密码，说明公钥认证没有成功；不要此时禁用密码登录。设置了密钥 passphrase 时，客户端可能要求解锁本地私钥，它与远程账号密码保护的是不同层次。

## 5. 用 SSH Config 保存可检查的连接别名

Mac 客户端配置位于 `~/.ssh/config`。先确保权限：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

加入一个局域网别名：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  Port 22
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
```

随后可直接连接：

```bash
ssh gpu-laptop-lan
```

`Host` 是本地别名，`HostName` 才是真实地址。scp、rsync、VS Code Remote SSH 和端口转发都能复用同一别名。局域网和 Tailscale 等异网入口应使用不同名称，明确地址来源：

```sshconfig
Host gpu-laptop-remote
  HostName GPU_LAPTOP_MAGICDNS_NAME
  User YOUR_UBUNTU_USERNAME
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

保活参数只能更快发现失效连接，不能阻止设备休眠，也不能保证前台训练在断线后继续。

## 6. 用 `ssh -G` 检查最终生效配置

客户端配置可能由命令行、具体 Host、`Host *`、系统文件和环境共同决定。不要只读文件正文，直接查看最终解析：

```bash
ssh -G gpu-laptop-lan \
  | grep -E '^(hostname|user|port|identityfile|identitiesonly|proxyjump|localforward) '
```

OpenSSH 通常采用先获得的参数值，因此具体主机规则应放在宽泛规则之前：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User student
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes

Host *
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

不要在 `Host *` 中写某台机器专用的用户名、私钥、端口或转发规则，否则其他连接也可能继承。

## 7. ssh-agent、Keychain 与转发边界

设置 passphrase 后，可以让 ssh-agent 在当前登录会话缓存解锁状态：

```bash
ssh-add -l
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_gpu_laptop
```

macOS/OpenSSH 参数会变化，使用前查看 `man ssh-add` 和 `man ssh_config`。按系统支持情况，可在具体 Host 中设置 `AddKeysToAgent yes` 与 `UseKeychain yes`；若当前版本不支持，客户端会直接报告配置错误，应以本机帮助为准。

不要把 `ForwardAgent yes` 作为默认值。转发不会复制私钥文件，但远程进程可能借用本地 agent 发起签名，扩大凭证使用范围。更稳妥的做法是 Mac 使用自己的密钥登录 Ubuntu，Ubuntu 访问 GitHub 时使用自己的受限凭证或部署密钥，不复制整个 `~/.ssh`，也不把 agent socket 挂入不可信容器。

## 8. 主机身份变化与认证失败的安全处理

看到 `REMOTE HOST IDENTIFICATION HAS CHANGED` 时，先从 Ubuntu 本机控制台核对当前主机指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认系统重装、密钥重建或地址归属变化合理后，只删除对应记录：

```bash
ssh-keygen -R HOSTNAME_OR_IP
```

不要删除整个 `known_hosts` 或关闭检查。密钥登录失败时，保留密码入口，使用 `ssh -vv`、`IdentitiesOnly=yes` 和明确的 `-i` 路径调查；服务端则检查目标用户、`~/.ssh` 所有权、`authorized_keys` 权限和 sshd 日志。不要通过放宽整个家目录权限或把授权文件设为所有人可写来“修复”。

## 9. 配置完成后的验收

```bash
ssh -G gpu-laptop-lan \
  | grep -E '^(hostname|user|port|identityfile|identitiesonly) '

ssh gpu-laptop-lan 'hostname && whoami && pwd'
```

这两步分别验证客户端最终配置和非交互远程执行。只有新终端中密钥登录稳定、目标机器与用户正确，才应考虑收紧密码认证；调整服务端认证时仍要保留旧会话和本机备用入口。

继续阅读：

- [scp、rsync 与端口转发](03-scp-rsync与端口转发.md)
- [SSH 故障排查](04-SSH故障排查.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
