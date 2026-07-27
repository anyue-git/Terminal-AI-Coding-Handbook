# 02 密钥登录与 SSH Config

长期连接 Ubuntu，推荐使用 SSH 密钥和清晰的客户端配置。

```text
Mac 私钥
→ 只保存在可信客户端

Ubuntu 公钥
→ 写入目标用户的 authorized_keys
```

私钥不会通过网络发送。服务端只验证客户端是否能够完成签名。

---

## 1. 先认识 `~/.ssh`

Mac：

```bash
ls -la ~/.ssh
```

常见文件：

```text
id_ed25519              私钥
id_ed25519.pub          公钥
known_hosts             已知主机身份
config                  客户端连接配置
```

规则：

- 没有 `.pub` 后缀的身份文件通常是私钥；
- 私钥不能提交 Git、上传网盘或发到聊天中；
- 不要把整个 `~/.ssh` 挂进容器或交给 AI；
- 公钥可以复制到服务器，但仍要确认目标账号和用途。

---

## 2. 生成专用 Ed25519 密钥

```bash
ssh-keygen -t ed25519 \
  -C "mac-to-gpu-laptop" \
  -f ~/.ssh/id_ed25519_gpu_laptop
```

建议设置 passphrase。

生成：

```text
~/.ssh/id_ed25519_gpu_laptop
~/.ssh/id_ed25519_gpu_laptop.pub
```

只查看公钥：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub
```

不要复制私钥内容。

---

## 3. 把公钥安装到 Ubuntu

已经验证密码登录和主机指纹后，可以执行：

```bash
cat ~/.ssh/id_ed25519_gpu_laptop.pub \
  | ssh USERNAME@SERVER_IP \
  'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
```

检查：

- 本地文件以 `.pub` 结尾；
- 用户名和主机正确；
- 远程目标是 `authorized_keys`；
- 没有传输私钥。

测试：

```bash
ssh -i ~/.ssh/id_ed25519_gpu_laptop USERNAME@SERVER_IP
```

Ubuntu 常见权限：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

不要递归修改整个家目录权限。

---

## 4. SSH Config 让连接可读

创建并保护：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/config
chmod 600 ~/.ssh/config
```

局域网配置：

```sshconfig
Host gpu-laptop-lan
  HostName 192.168.1.50
  User YOUR_UBUNTU_USERNAME
  Port 22
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
  IdentitiesOnly yes
```

连接：

```bash
ssh gpu-laptop-lan
```

查看最终解析：

```bash
ssh -G gpu-laptop-lan | sed -n '1,40p'
```

重点检查 `hostname`、`user`、`port`、`identityfile` 和 `proxyjump`。

---

## 5. 局域网和异网使用不同别名

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

这样局域网、Tailscale、rsync 和 VS Code Remote SSH 的问题更容易分层。

保活参数只能更快发现失效连接，不能防止 Mac 或 Ubuntu 休眠，也不能保证训练继续。

---

## 6. ssh-agent 与 Keychain

macOS 可使用 ssh-agent 缓存已解锁密钥。

当前系统支持时：

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_gpu_laptop
```

查看：

```bash
ssh-add -l
```

参数会随系统版本变化，使用前查看：

```bash
man ssh-add
```

不要默认启用：

```sshconfig
ForwardAgent yes
```

远程主机上的程序可能借用本地 Agent 发起签名。普通个人开发优先使用远程主机自己的受限凭据。

---

## 7. `Host *` 的配置顺序

OpenSSH 客户端通常采用先获得的值，所以专用配置应放在宽泛规则之前：

```sshconfig
Host gpu-laptop-remote
  HostName GPU_LAPTOP_MAGICDNS_NAME
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop

Host *
  AddKeysToAgent yes
  UseKeychain yes
```

不要在 `Host *` 中放某台机器专用的用户名、端口、私钥、ProxyJump 或端口转发。

---

## 8. 主机密钥变化不能直接忽略

出现：

```text
REMOTE HOST IDENTIFICATION HAS CHANGED
```

可能是系统重装、IP 被另一台设备使用、配置指向错误，也可能是攻击。

先在可信控制台核对：

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认无误后，只删除对应条目：

```bash
ssh-keygen -R HOSTNAME
```

不要删除整个 `known_hosts`，也不要关闭 `StrictHostKeyChecking`。

---

## 9. 禁用密码登录前的安全顺序

可以把自定义配置放入：

```text
/etc/ssh/sshd_config.d/99-local-hardening.conf
```

示意：

```text
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
```

安全流程：

```text
密钥登录已成功
→ 保留当前会话
→ 备份配置
→ 写入独立片段
→ sudo sshd -t
→ reload ssh
→ 第二终端测试
→ 成功后关闭旧会话
```

验证：

```bash
sudo sshd -t
sudo sshd -T | grep -E 'passwordauthentication|permitrootlogin|pubkeyauthentication'
sudo systemctl reload ssh
```

---

## 10. AI CLI 与 SSH 凭据

默认禁止 Agent 读取：

```text
~/.ssh/id_*
SSH Agent Socket
完整 known_hosts
```

排查时提供脱敏后的 Config 片段，不提供私钥、真实公网地址或设备授权链接。

继续阅读：

- [SSH 基础与首次连接](01-SSH基础与首次连接.md)
- [scp、rsync 与端口转发](03-scp-rsync与端口转发.md)
- [SSH 故障排查](04-SSH故障排查.md)
