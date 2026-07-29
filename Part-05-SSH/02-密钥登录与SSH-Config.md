# 02 密钥登录与 SSH Config

密码可以完成首次连接，但长期从 Mac 使用 Ubuntu，更适合使用专用 SSH 密钥和清晰的客户端配置。密钥登录并不是把密码换成另一串秘密，而是让客户端使用私钥完成签名，服务端用已登记的公钥验证签名。私钥不应传到服务器，也不应交给 AI、网盘或代码仓库。

本章沿用上一章的环境：Mac 作为客户端，Ubuntu 游戏本作为服务端。假设你已经用密码成功登录过一次，并核对过 Ubuntu 的主机指纹。

## 1. 先分清三类容易混淆的文件

在 Mac 上查看：

```bash
ls -la ~/.ssh
```

常见内容包括：

```text
id_ed25519_gpu_laptop       客户端私钥
id_ed25519_gpu_laptop.pub   与私钥配对的公钥
known_hosts                 Mac 记录的服务器主机身份
config                      Mac 的 SSH 客户端连接配置
```

Ubuntu 服务端还拥有自己的主机密钥，例如：

```text
/etc/ssh/ssh_host_ed25519_key
/etc/ssh/ssh_host_ed25519_key.pub
```

它们负责证明“这台服务器是谁”，与用户登录密钥不是同一组文件。

需要牢牢记住：

- 没有 `.pub` 后缀的用户身份文件通常是私钥；
- 私钥只保存在可信客户端，不能发送给服务器；
- 公钥可以安装到目标用户的 `authorized_keys`；
- `known_hosts` 保存的是服务器身份，不是登录凭证；
- `~/.ssh/config` 只是连接配置，不应包含私钥正文。

## 2. 在 Mac 上生成一把专用密钥

不要为了省事让所有服务器共用同一把没有说明的默认密钥。为 Ubuntu 游戏本创建专用 Ed25519 密钥：

```bash
ssh-keygen -t ed25519 \
  -C "mac-to-gpu-laptop" \
  -f ~/.ssh/id_ed25519_gpu_laptop
```

命令会询问是否设置 passphrase。建议设置一个自己能够长期管理的口令。passphrase 用于保护磁盘上的私钥文件，即使文件被复制，攻击者仍然需要解锁它。

生成后检查文件名和权限：

```bash
ls -l ~/.ssh/id_ed25519_gpu_laptop*
```

可能看到：

```text
-rw-------  ... id_ed25519_gpu_laptop
-rw-r--r--  ... id_ed25519_gpu_laptop.pub
```

只查看公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub
```

公钥通常是一行，以 `ssh-ed25519` 开头。不要运行 `cat ~/.ssh/id_ed25519_gpu_laptop`，更不要把私钥内容复制进聊天、Issue、PR、日志或远程命令。

## 3. 把公钥安装到正确的 Ubuntu 用户

最容易理解的方法，是先通过密码登录 Ubuntu，再在远程用户目录中创建 `~/.ssh` 和 `authorized_keys`。

先在 Mac 打印公钥，复制整行：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub
```

然后通过原来的密码方式登录 Ubuntu：

```bash
ssh USERNAME@SERVER_IP
```

在 Ubuntu 远程 Shell 中执行：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
```

把公钥粘贴为单独一行，保存退出后设置权限：

```bash
chmod 600 ~/.ssh/authorized_keys
```

确认当前用户和目录：

```bash
whoami
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys
```

如果公钥被安装到错误用户的家目录，使用正确私钥也无法登录目标账号。

熟悉命令后，也可以在 Mac 使用管道安装公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub \
  | ssh USERNAME@SERVER_IP \
  'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
```

这条命令只传输以 `.pub` 结尾的公钥。执行前必须重新核对本地文件名、远程用户名和地址。不要把私钥路径替换进去。

## 4. 在新终端中测试密钥登录

保留现有 SSH 会话不要关闭，再在 Mac 打开第二个 Terminal：

```bash
ssh -i ~/.ssh/id_ed25519_gpu_laptop \
  -o IdentitiesOnly=yes \
  USERNAME@SERVER_IP
```

`IdentityFile` 指定要使用的私钥，`IdentitiesOnly=yes` 避免客户端同时尝试 ssh-agent 中大量其他密钥。

成功后执行：

```bash
hostname
whoami
pwd
```

确认登录到了正确主机和正确用户。若仍要求 Ubuntu 账号密码，说明公钥认证没有成功；不要立刻禁用密码登录，先查看后面的故障排查章节。

设置了私钥 passphrase 时，首次使用可能要求输入密钥口令。这不是 Ubuntu 用户密码。两种口令保护不同层次：Ubuntu 密码用于账号认证，私钥 passphrase 用于解锁本地私钥。

## 5. 用 SSH Config 把连接参数保存成别名

每次输入地址、用户和私钥路径容易出错。Mac 的客户端配置文件是：

```text
~/.ssh/config
```

先确保目录和文件权限合理：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

编辑文件：

```bash
nano ~/.ssh/config
```

加入：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  Port 22
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
```

保存后连接：

```bash
ssh gpu-laptop-lan
```

`Host` 是本地别名，可以自己命名；`HostName` 才是真实地址。以后 `scp`、`rsync`、VS Code Remote SSH 和端口转发都可以复用同一个别名。

## 6. 检查 SSH 最终如何解释配置

客户端配置可能来自命令行、`~/.ssh/config`、系统配置和宽泛的 `Host *` 规则。不要只看文件正文，使用：

```bash
ssh -G gpu-laptop-lan | sed -n '1,60p'
```

重点检查：

```text
hostname
user
port
identityfile
identitiesonly
proxyjump
localforward
```

例如：

```bash
ssh -G gpu-laptop-lan | grep -E '^(hostname|user|port|identityfile|identitiesonly) '
```

如果解析结果中的用户、地址或私钥不符合预期，应先修正客户端配置，再继续排查认证。

OpenSSH 配置会按匹配规则合并，通常采用先获得的值。因此，具体主机规则应放在宽泛规则之前：

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

不要在 `Host *` 中填写某台机器专用的用户名、私钥、端口或转发规则，否则其他连接也可能继承它们。

## 7. 局域网和异网使用不同别名

如果后续使用 Tailscale 等安全组网，可以保留两套入口：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes

Host gpu-laptop-remote
  HostName GPU_LAPTOP_MAGICDNS_NAME
  User YOUR_UBUNTU_USERNAME
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

这样可以清楚区分：

```text
ssh gpu-laptop-lan
→ 局域网地址

ssh gpu-laptop-remote
→ 安全组网地址
```

保活参数只能帮助客户端更快发现失效连接，不会阻止 Mac 或 Ubuntu 休眠，也不能让前台训练在 SSH 断线后自动继续。

## 8. ssh-agent 和 macOS Keychain

如果私钥设置了 passphrase，可以让 ssh-agent 在当前登录会话中缓存解锁后的密钥。先查看当前列表：

```bash
ssh-add -l
```

macOS 当前 OpenSSH 支持时，可以执行：

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_gpu_laptop
```

不同 macOS 版本的参数可能变化，使用前查看：

```bash
man ssh-add
```

在 `~/.ssh/config` 中也可以按系统支持情况配置：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes
```

如果某个选项在当前 OpenSSH 中不受支持，连接会报配置错误。以本机 `man ssh_config` 和 `ssh -G` 为准，不要盲目复制旧教程。

## 9. 不要默认开启 Agent Forwarding

下面的设置不应作为普通个人开发默认值：

```sshconfig
ForwardAgent yes
```

Agent Forwarding 不会复制私钥文件，但远程主机上的进程可能借用本地 agent 发起签名。若远程主机或远程进程不可信，这会扩大凭证使用范围。

更稳妥的选择是：

- Mac 使用自己的 SSH 私钥登录 Ubuntu；
- Ubuntu 访问 GitHub 时使用 Ubuntu 自己的受限凭证或部署密钥；
- 不把 Mac 的整个 `~/.ssh` 复制到 Ubuntu；
- 不把 SSH agent socket 挂载进不可信容器。

## 10. 主机密钥变化时不要直接忽略

看到：

```text
REMOTE HOST IDENTIFICATION HAS CHANGED
```

常见原因包括 Ubuntu 重装、SSH 主机密钥重建、局域网地址被另一台设备占用、Config 指向错误，或者网络中存在攻击风险。

先通过 Ubuntu 本机控制台核对当前主机指纹：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认变化合理后，在 Mac 只删除对应地址或主机名的旧记录：

```bash
ssh-keygen -R HOSTNAME_OR_IP
```

再重新连接并核对新指纹。不要删除整个 `known_hosts`，也不要把 `StrictHostKeyChecking` 关闭为全局规则。

## 11. 禁用密码登录前的安全顺序

只有在密钥登录已经从第二个终端成功验证，并且你有 Ubuntu 本机控制台或其他恢复入口时，才考虑关闭密码认证。

可以在 Ubuntu 建立独立配置片段：

```text
/etc/ssh/sshd_config.d/99-local-hardening.conf
```

内容示意：

```text
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin no
```

修改后：

```bash
sudo sshd -t
sudo sshd -T | grep -E 'pubkeyauthentication|passwordauthentication|permitrootlogin'
sudo systemctl reload ssh
```

保留旧连接，在新的 Mac 终端再次运行：

```bash
ssh gpu-laptop-lan
```

只有新连接成功后，才关闭旧会话。远程认证配置一旦写错，已有会话往往是最后的修复入口。

## 12. AI CLI 与 SSH 凭证的边界

默认不要授权 Agent 读取：

```text
~/.ssh/id_*
SSH_AUTH_SOCK
整个 ~/.ssh 目录
完整 known_hosts
```

排查连接时，通常只需要提供：

- 脱敏后的 `~/.ssh/config` 相关片段；
- `ssh -G ALIAS` 中的非秘密字段；
- `ssh -vvv` 的关键错误行；
- 公钥指纹，而不是私钥内容；
- 经过脱敏的主机名、用户名和地址。

即使私钥设置了 passphrase，也不能把文件交给模型。passphrase 是额外保护，不是分享许可。

继续阅读：

- [SSH 基础与首次连接](01-SSH基础与首次连接.md)
- [scp、rsync 与端口转发](03-scp-rsync与端口转发.md)
- [SSH 故障排查](04-SSH故障排查.md)
