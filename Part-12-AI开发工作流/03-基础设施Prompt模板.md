# 03 基础设施与远程开发 Prompt 模板

> 最近核对：2026-07-30

基础设施任务与普通代码修改最大的区别，是许多影响不会完整出现在 Git diff 中。SSH、防火墙、系统服务、驱动、Docker Volume、远程数据和训练状态一旦改错，可能导致断连、数据丢失或环境不可用，因此应始终采用：

```text
观察
→ 判断问题层级
→ 设计最小方案
→ 预演或备份
→ 人工确认
→ 单步执行
→ 验证
→ 检查恢复路径
```

本章的模板不是让 Agent 自动管理机器，而是把高影响任务改写成可审查的诊断和变更卡片。

## 1. 所有基础设施任务先使用同一诊断合同

```text
当前阶段只做诊断。不要修改文件、安装软件、重启服务、使用 sudo、删除数据或改变网络规则。

请先说明：
1. 问题可能位于哪一层；
2. 需要查看哪些只读信息；
3. 每条命令在哪台机器和哪个目录执行；
4. 每条命令会读取什么；
5. 不同输出分别意味着什么；
6. 哪一步之后才需要讨论修改；
7. 修改前需要什么备份、dry run 或备用连接。

涉及凭据、远程连接、系统服务、磁盘、Docker Volume、驱动或数据删除时单独标明风险。
```

诊断结束后不要一次串联多个高影响步骤。每个执行批次先输出：

```text
准备执行：
- 主机：
- 用户：
- 目录：
- 完整命令：
- 读取内容：
- 修改内容：
- 是否需要 sudo：
- 是否会断连或重启：
- 预演或备份：
- 成功判断：
- 失败恢复：
```

人工确认后只执行这一批，并立即验证。

## 2. 网络、SSH、Tailscale 与端口隧道

SSH 失败时不要先改配置、删除 `known_hosts`、重建密钥或开放公网端口，而是沿名称解析、网络、TCP、sshd、主机身份和用户认证逐层检查：

```text
请分析下面的 SSH 错误和已脱敏调试输出：
[ERROR]

客户端：[Mac / Ubuntu]
目标主机：[SSH_ALIAS_OR_ADDRESS]

当前阶段不要修改 SSH 配置、删除 known_hosts、重建密钥、调整防火墙、重启服务或开放公网端口。

请按层判断：
1. 主机名解析；
2. 网络可达性；
3. TCP 端口；
4. sshd 是否监听；
5. 主机指纹；
6. 用户名和密钥认证；
7. 登录后的 Shell 环境。

每次只给一组最小检查，标明在客户端还是服务端执行，并解释不同结果如何决定下一步。
```

审查 SSH Config 时只提供脱敏配置，不包含私钥正文：

```text
只读审查下面的 SSH Config，不要修改原文件：
[REDACTED_CONFIG]

请检查 Host 与通配规则顺序、HostName、User、Port、IdentityFile、IdentitiesOnly、ProxyJump、ServerAlive 设置和不存在的路径。

输出：
1. 每个别名最终解析结果；
2. 可能互相覆盖的规则；
3. 最小修改建议；
4. 修改前备份命令；
5. 使用 ssh -G 和第二个会话验证的方法；
6. 恢复原配置的方法。
```

Tailscale 异网问题必须把组网可达性与普通 OpenSSH 登录分开：

```text
只读诊断 Tailscale 与普通 OpenSSH 的异网连接，不修改 ACL、Grants、路由、设备密钥或 SSH 配置。

请按顺序检查：
1. 两台设备是否在线；
2. tailscale ping；
3. direct 或 DERP；
4. MagicDNS；
5. Grants 是否允许目标端口；
6. TCP 22；
7. 普通 OpenSSH 主机指纹与用户认证。

不要建议为解决 Tailscale 问题开放公网 22。
```

Jupyter、TensorBoard 或开发服务应只监听远端回环地址，再通过 SSH 隧道访问：

```text
请设计通过 SSH 隧道访问 [JUPYTER/TENSORBOARD/DEV_SERVER] 的方案。

要求：
- 服务只监听目标主机 127.0.0.1；
- 不开放公网端口；
- 明确服务端和客户端命令；
- 使用非冲突本地端口；
- 说明认证要求；
- 给出端口占用、隧道断开和日志排查；
- 异网时通过已验证的 Tailscale + OpenSSH 别名。
```

## 3. 文件同步、磁盘与数据删除

设计 rsync 时必须明确源、目标、方向和目标端是否有独立生成内容：

```text
请为下面的同步生成方案：

源主机与目录：[SOURCE]
目标主机与目录：[TARGET]
方向：[Mac 到 Ubuntu / Ubuntu 到 Mac]
需要排除：[LIST]
目标端是否有独立生成数据：[YES_OR_NO]

要求：
1. 第一条命令必须使用 --dry-run；
2. 默认不要使用 --delete；
3. 解释源路径末尾 / 的影响；
4. 不同步 .git、虚拟环境、.env、缓存、数据集、模型和运行结果，除非明确要求；
5. 给出执行前后验证；
6. 说明中断后如何安全重试；
7. 如果可能覆盖远端修改，停止并给出 Git 回收方案。
```

磁盘清理阶段只盘点，不生成通配符批量删除命令：

```text
当前阶段只盘点，不删除任何内容。

目标目录：[PATH]

请输出：
1. 总体磁盘使用；
2. 最大目录与文件；
3. 哪些属于源码、环境、缓存、数据、模型、运行结果和 checkpoint；
4. 哪些内容有 Git、远程副本、校验值或备份；
5. 候选删除项及影响；
6. 删除前同步和恢复方法。

未经人工逐项确认，不执行 rm、find -delete、docker prune 或清理工具。
```

数据目录、Docker Volume、模型和 checkpoint 往往不受 Git 保护，候选删除项必须说明备份位置、校验方式和恢复成本。

## 4. Python、Homebrew、Docker 与 GPU 运行栈

Python 环境问题先确认解释器、pip、依赖声明和同名文件遮蔽，不安装或升级：

```text
请只读诊断 Python 环境，不要安装、升级或卸载包，也不要修改系统 Python。

主机：[HOST]
项目目录：[PATH]
错误：[ERROR]
目标包：[PACKAGE]

请检查：
- pwd；
- type -a python python3 pip pip3；
- python --version；
- python -c 'import sys; print(sys.executable, sys.prefix, sys.base_prefix)'；
- python -m pip --version；
- python -m pip show [PACKAGE]；
- 是否有同名文件遮蔽包；
- 项目依赖声明和锁文件。

区分解释器选错、环境未激活、包未安装、版本冲突、平台不兼容和项目导入问题，再给出最小修复与验证命令。不要建议 sudo pip install。
```

Mac 与 Ubuntu 必须分别创建环境，不能复制 `.venv`。Homebrew 与 PATH 问题也先只读：

```text
请只读诊断 Homebrew 与 PATH，不要 install、uninstall、upgrade、cleanup、link、unlink 或重启服务。

目标命令：[COMMAND]
现象：[ERROR]

请检查 uname -m、brew --prefix、type -a [COMMAND]、command -v [COMMAND]、当前 PATH、brew info [FORMULA]、Shell 启动文件，以及是否混用 Apple Silicon 与 Rosetta。

给出最小修改、备份、验证和回滚方法。不要连续向 .zshrc 追加未经确认的 PATH。
```

Docker 或 Compose 失败时，禁止默认执行清理：

```text
请只读分析下面的 Docker 问题：
[REDACTED_ERROR_AND_CONFIG]

不要执行 system prune，不要删除容器、镜像、Volume、Bind Mount 数据或网络。

请分层检查：
- docker version；
- docker context show；
- docker ps -a；
- docker compose config；
- docker compose ps；
- 相关日志；
- 应用监听地址与端口映射；
- Volume、Bind Mount 与权限；
- 环境变量；
- healthcheck；
- 依赖服务是否就绪。

每个根因假设给出证据和最小验证。任何涉及持久数据的修改必须单独说明影响、备份和恢复方法，并等待人工确认。
```

GPU 问题按硬件、驱动、解释器、框架构建、真实运算、项目代码和 Toolkit 分层：

```text
请分层分析 GPU 问题，不要先重装驱动、CUDA Toolkit 或整个 Python 环境。

系统：[UBUNTU_VERSION]
Python：[INTERPRETER_OR_ENV]
框架：[PYTORCH_OR_OTHER]
错误：[ERROR]

依次检查：
1. PCI 和系统是否识别 GPU；
2. NVIDIA 驱动与 nvidia-smi；
3. 当前 Python 解释器；
4. 框架版本及其 CUDA 构建；
5. 框架能否执行最小 GPU 运算；
6. 模型和数据设备是否一致；
7. 容器是否获得 GPU；
8. 只有编译扩展时才检查 nvcc 和 Toolkit。

每层给出命令、判断标准和下一步。不要把 nvidia-smi 中的 CUDA Version 当作已安装 Toolkit 版本。
```

驱动确实需要变更时，先只制定计划：

```text
当前阶段只制定驱动变更计划，不执行安装、卸载、重启或 Secure Boot 修改。

请先读取 Ubuntu 版本、GPU 型号、当前驱动、ubuntu-drivers devices、Secure Boot 状态、nvidia-smi 错误，以及是否有正在运行的 GPU 任务。

方案必须说明：
1. 为什么确认问题在驱动层；
2. 推荐来源；
3. 预计安装或移除的包；
4. 是否需要重启和 MOK；
5. 如何保留本机控制台；
6. 失败后的恢复路径；
7. 安装后验证命令。
```

## 5. 远程训练与系统服务变更

正式训练前让 Agent 只读审查运行现场，而不是直接启动：

```text
只读审查下面的远程训练方案，不要启动训练，也不要修改系统配置。

主机：[HOST]
项目：[PATH]
命令：[COMMAND]
配置：[CONFIG]
输出目录：[RUN_DIR]

请检查：
- hostname、pwd、Git 分支和 HEAD；
- 工作区是否有未记录修改；
- Python 解释器；
- GPU 最小运算；
- 数据、模型和输出路径；
- 磁盘空间；
- tmux 会话名；
- 日志和退出状态；
- checkpoint 周期、latest/best 和恢复参数；
- 是否会覆盖旧实验；
- 是否含凭据或私人路径。

输出启动前清单，以及失败后从哪个 checkpoint 恢复。不要把完整环境变量写入日志。
```

系统服务变更同样先建立证据和恢复路径：

```text
当前阶段只制定 [SERVICE] 变更计划，不执行 sudo、restart、enable、disable 或文件覆盖。

请先给出：
- 当前状态和日志；
- 配置来源；
- 语法或 dry-run 检查；
- 影响的端口、用户、目录和依赖；
- 当前连接是否会中断；
- 备份命令；
- reload 与 restart 的区别；
- 第二会话或本机控制台验证；
- 回滚命令。
```

SSH、网络和远程服务变更必须保留备用会话或本机控制台；重启、驱动和防火墙操作不能与其他高影响变化合并成一条命令。

## 6. 用完成报告封闭证据链

基础设施任务完成报告应说明：

```text
问题层级：

执行环境：

变更前证据：

实际执行命令：

实际修改：

验证结果：

未验证部分：

备份或 checkpoint：

回滚方式：

后续观察：
```

只有“服务恢复正常”还不够；必须能解释改了什么、在哪台机器执行、怎样验证、哪些副作用不受 Git 保护，以及失败时怎样恢复。

## 延伸阅读

- [SSH 故障排查](../Part-05-SSH/04-SSH故障排查.md)
- [Docker GPU 与权限边界](../Part-08-Docker/04-GPU容器与权限边界.md)
- [GPU 远程开发](../Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md)
- [实验日志与 Checkpoint 管理](../Part-11-GPU远程开发/08-实验日志与Checkpoint管理.md)