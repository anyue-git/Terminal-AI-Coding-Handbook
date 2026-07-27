# 04 SSH 故障排查

SSH 失败时，按层定位比“重装一遍”有效得多。

```text
机器是否在线
→ 名称和地址是否正确
→ 网络路径是否可达
→ 端口是否监听
→ 主机身份是否可信
→ 用户认证是否成功
→ 登录后环境是否正确
```

---

## 1. 先收集客户端信息

查看最终配置：

```bash
ssh -G gpu-laptop | sed -n '1,50p'
```

重点看：

```text
hostname
user
port
identityfile
identitiesonly
proxyjump
localforward
```

查看连接过程：

```bash
ssh -vvv gpu-laptop
```

公开日志前脱敏真实用户名、主机名、地址和本机路径，但保留关键错误行。

---

## 2. 名称解析失败

错误：

```text
Could not resolve hostname
```

检查：

```bash
ssh -G gpu-laptop | grep '^hostname '
nslookup HOSTNAME
```

Tailscale 环境：

```bash
tailscale status
tailscale ping HOSTNAME
```

如果直接使用 IP 可以连接，问题通常在 DNS、MagicDNS 或 SSH Config，而不是认证。

---

## 3. `Connection timed out`

请求没有得到响应。检查：

1. Ubuntu 是否开机、联网且未休眠；
2. 地址是否变化；
3. 两台设备是否在可达网络；
4. Tailscale 是否在线；
5. 防火墙或 policy 是否丢弃；
6. SSH 是否监听目标接口和端口。

```bash
nc -vz HOST 22
```

ping 成功不代表 TCP 22 一定可达。

---

## 4. `Connection refused`

主机通常可达，但端口没有服务监听或被明确拒绝。

Ubuntu：

```bash
systemctl status ssh
sudo ss -lntp | grep ':22'
sudo sshd -t
sudo journalctl -u ssh --no-pager -n 100
```

不要反复 restart 而不看日志。

---

## 5. `Permission denied`

网络和服务通常已经可达，失败位于认证层。

客户端精确指定密钥：

```bash
ssh -vv \
  -o IdentitiesOnly=yes \
  -i ~/.ssh/id_ed25519_gpu_laptop \
  USER@HOST
```

检查：

- 用户名；
- 私钥路径；
- 服务端 `authorized_keys`；
- `.ssh` 所有权和权限；
- 公钥认证是否启用；
- Agent 是否提交了错误密钥。

Ubuntu：

```bash
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys
sudo journalctl -u ssh --no-pager -n 100
```

---

## 6. `Too many authentication failures`

通常是 Agent 尝试了过多密钥。

Config：

```sshconfig
Host gpu-laptop
  IdentitiesOnly yes
  IdentityFile ~/.ssh/id_ed25519_gpu_laptop
```

不要删除所有密钥来解决。

---

## 7. 主机身份变化

错误：

```text
REMOTE HOST IDENTIFICATION HAS CHANGED
```

先在可信控制台核对：

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

确认目标正确后，只删除对应记录：

```bash
ssh-keygen -R HOSTNAME
```

不要关闭主机密钥检查，也不要删除整个 `known_hosts`。

---

## 8. Tailscale 在线但 SSH 不通

先检查网络层：

```bash
tailscale status
tailscale ping GPU_HOSTNAME
tailscale netcheck
nc -vz GPU_HOSTNAME 22
```

普通 OpenSSH 运行在 Tailscale 网络上时，还要检查：

- tailnet policy 是否允许 TCP 22；
- Ubuntu SSH 服务是否监听；
- UFW 是否允许该来源。

启用了 Tailscale SSH 时，还要检查 SSH policy、目标本地用户和重新认证要求。

不要为了追求 `direct` 而开放公网 22。经 DERP 仍是加密连接，只是性能可能较低。

---

## 9. SSH 能登录但命令不对

```bash
hostname
whoami
pwd
echo "$SHELL"
printf '%s\n' "$PATH"
type -a python claude codex grok
```

常见原因：

- 登录到错误用户；
- 交互与非交互 Shell 加载不同配置；
- Python 环境未激活；
- 工具安装在另一用户目录；
- VS Code Remote SSH 使用远程环境；
- PATH 顺序与本地不同。

不要因为命令找不到就再次安装，先确定机器、用户和 PATH。

---

## 10. scp 或 rsync 失败

先验证非交互 SSH：

```bash
ssh gpu-laptop 'hostname && whoami'
```

验证目标目录：

```bash
ssh gpu-laptop 'ls -ld ~/projects'
```

检查两端 rsync：

```bash
rsync --version
ssh gpu-laptop 'rsync --version'
```

再预演：

```bash
rsync -av --dry-run SOURCE/ gpu-laptop:DESTINATION/
```

---

## 11. 修改服务端配置前

配置来源：

```text
/etc/ssh/sshd_config
/etc/ssh/sshd_config.d/*.conf
```

查看生效值：

```bash
sudo sshd -T
```

修改流程：

```text
保留旧会话
→ sudo sshd -t
→ reload ssh
→ 第二终端测试
→ 成功后关闭旧会话
```

---

## 12. 固定排错清单

Mac：

```bash
ssh -G gpu-laptop | sed -n '1,50p'
nc -vz HOST 22
ssh -vvv gpu-laptop
```

Tailscale 场景再加：

```bash
tailscale status
tailscale ping HOST
tailscale netcheck
```

Ubuntu：

```bash
hostname
ip addr
systemctl status ssh
sudo ss -lntp | grep ':22'
sudo sshd -t
sudo sshd -T
sudo journalctl -u ssh --no-pager -n 100
```

给 AI 排错时要求它按 DNS、网络、端口、主机身份、认证和远程环境分层分析，不要建议关闭验证、开放公网 22 或删除整个 `~/.ssh`。

继续阅读：

- [SSH 基础与首次连接](01-SSH基础与首次连接.md)
- [密钥登录与 SSH Config](02-密钥登录与SSH-Config.md)
- [异网安全连接](../Part-11-GPU远程开发/06-异网安全连接.md)
