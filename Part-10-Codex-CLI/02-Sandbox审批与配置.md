# 02 权限、Sandbox 与配置

> 最近核对：2026-07-30  
> Codex 的 beta Permission Profiles 仍在快速变化。实际配置前同时检查 `/permissions`、`/status`、本机版本和官方文档。

Codex 把“什么时候停下来问人”和“获准进程实际能访问什么”分成两条轴：审批策略处理人工停顿，Sandbox 处理文件与网络边界。beta Permission Profiles 进一步把文件系统与网络规则组合成命名配置，但它不能与旧 `sandbox_mode` 机制叠加。本章只讲 Codex 的实现差异；Shell、凭据、Docker、远程主机和高影响命令的共同判断见[权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)。

## 1. 先读取最终状态，再解释 Sandbox 与审批组合

进入 Codex 后运行：

```text
/status
/permissions
```

重点确认工作目录与工作区根、认证方式、活动配置 Profile、Sandbox 或 Permission Profile、审批策略与审批者、网络状态，以及 Rules、MCP、Skills、Plugins 和 Hooks。命令行参数、用户配置、受信任项目配置、组织要求和启动目录都会参与最终结果，不能只根据一行 TOML 或界面图标判断当前边界。

旧机制的 Sandbox 模式主要是：

```text
read-only
workspace-write
danger-full-access
```

常见审批策略是：

```text
untrusted
on-request
never
```

`read-only` 适合陌生项目调查和代码审查：

```bash
codex --sandbox read-only --ask-for-approval on-request
```

非交互只读任务可以让越界动作直接失败：

```bash
codex exec \
  --sandbox read-only \
  --ask-for-approval never \
  "只读总结当前项目，不修改文件"
```

这里的 `never` 表示不弹出审批，超出只读 Sandbox 的动作仍应失败。`workspace-write` 是常见本地开发组合：

```bash
codex --sandbox workspace-write --ask-for-approval on-request
```

它允许写入实际 writable roots；工作区不等于整个硬盘，也不必然包含父目录、HOME 或其他数据盘，最终根目录仍以 `/status` 为准。

`danger-full-access` 移除本地 Sandbox 约束：

```bash
codex --sandbox danger-full-access
```

与 `--ask-for-approval never` 组合后，Codex 会在当前系统用户权限下获得很宽的文件和网络能力。`--dangerously-bypass-approvals-and-sandbox`（别名 `--yolo`）同时跳过审批和 Sandbox，只适合外层已经隔离、凭据已移除且环境可销毁的执行器。

`untrusted` 只自动放行被认为安全的读取操作；`on-request` 允许 Codex 在边界内工作，遇到需要确认的动作时请求审批；`never` 适合无人值守但边界明确的自动化。当前版本还支持 granular 审批策略，分别控制 Sandbox 升级、Rules、MCP elicitation、权限请求和 Skill 脚本等提示是否允许出现。它适合精细自动化，但不应在不了解每个分类时直接复制复杂配置。风险由审批与 Sandbox 的组合决定，`workspace-write + on-request` 和 `danger-full-access + never` 的含义完全不同。

## 2. 审批者可以自动化，权限边界不会因此扩大

默认审批者是用户：

```toml
approvals_reviewer = "user"
```

符合条件的审批请求也可以交给自动审查 Agent：

```toml
approval_policy = "on-request"
approvals_reviewer = "auto_review"
```

`auto_review` 只审核原本需要审批的动作，不改变 Sandbox，也不会撤销已经在 Sandbox 内允许的行为；它还会产生额外模型调用。自动审查拒绝的动作需要人重新判断，不能把这个模式理解为“比人工更安全”的总开关。

修改审批设置时，一次只改变一个变量：保留相同 Sandbox，比较 `user` 与 `auto_review`；需要 granular 策略时，再分别验证哪些提示能够出现、哪些会自动拒绝。直接同时修改 Sandbox、审批策略、审批者、网络和 Rules，即使结果异常，也很难判断是哪一层造成的。

## 3. beta Permission Profiles 把文件与网络边界放进一个命名策略

Permission Profiles 使用 `default_permissions` 和 `[permissions]`，内置名称包括：

```text
:read-only
:workspace
:danger-full-access
```

它与旧机制必须二选一：

```text
default_permissions + [permissions]
```

或：

```text
sandbox_mode + [sandbox_workspace_write]
```

如果任何已加载配置、命令行 `--sandbox` 或所选配置 Profile 中出现 `sandbox_mode`，Codex 会使用旧机制，而不是把两套规则相加。企业管理的 `allowed_permission_profiles` 是明确要求使用新 Profile 的例外；混合版本部署还要考虑旧客户端兼容。为了“多一层保护”同时复制两套配置，通常只会让实际生效机制更难判断。

一个关闭网络的项目编辑 Profile 可以从内置 `:workspace` 继承：

```toml
default_permissions = "project-edit"

[permissions.project-edit]
extends = ":workspace"
description = "Write the current project without network"

[permissions.project-edit.filesystem.":workspace_roots"]
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = false
```

需要显式控制工作区内容时，可以定义更完整的文件规则：

```toml
default_permissions = "project-edit"

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
".devcontainer" = "read"
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = true

[permissions.project-edit.network.domains]
"api.openai.com" = "allow"
"objects.githubusercontent.com" = "allow"
"*.github.com" = "allow"
```

更具体的 `deny` 会压过附近较宽的读写规则。Profile 还可以通过 `[permissions.NAME.workspace_roots]` 加入额外工作区根；这与文件系统表中的 `:workspace_roots` 规则不是同一个概念。Profile 仍处于 beta，配置后要在无重要数据的练习项目中分别验证允许读取、允许写入、敏感文件拒绝、允许域名和其他网络拒绝，不能只确认 Codex 能启动。

## 4. 配置、项目指令和真实 Sandbox 测试各自承担一层

用户级 `~/.codex/config.toml` 保存模型、推理强度、Sandbox、审批、Permission Profiles、网络、MCP、配置 Profile 和功能开关。`AGENTS.md` 与 `AGENTS.override.md` 描述项目结构、测试、编码约定、禁止修改范围和验收要求，它们影响模型行为，却不形成文件系统强制隔离。完整指令发现链已在[安装、认证与第一次启动](01-安装登录与启动.md)说明，本章不再重复。

旧教程中的 `codex exec --full-auto` 现在属于弃用兼容入口，新脚本应显式写出 Sandbox、审批、网络和工作目录。Codex 提供稳定的 Sandbox Helper，可用当前平台的实现直接运行测试命令：

```bash
codex sandbox --help

# macOS：参数以本机帮助为准
codex sandbox macos -- COMMAND

# Linux：参数以本机帮助为准
codex sandbox linux -- COMMAND
```

测试 Permission Profile 时，可以使用当前帮助支持的 `--permission-profile`，先运行 `pwd`、`ls`、`cat README.md` 等无副作用命令，再在练习目录创建可丢弃文件，验证预期允许和拒绝。真实删除、生产网络或秘密文件不适合作为规则探针。

修改 `config.toml` 前保存本地备份：

```bash
mkdir -p ~/.codex/backups
cp ~/.codex/config.toml \
  ~/.codex/backups/config.toml.$(date +%Y%m%d-%H%M%S)
```

一个可解释的调整顺序是：用 `/status` 和 `/permissions` 记录当前状态；决定采用旧 Sandbox 还是 beta Permission Profiles；在练习目录验证文件和网络边界；再调整审批策略或审批者；最后分别加入 Rules、MCP、Skills、Plugins 或 Hooks。整份复制陌生配置可能同时带入第三方 Provider、未知扩展和过时字段，不利于判断实际变化。

延伸阅读：[安装、认证与第一次启动](01-安装登录与启动.md)、[交互模式与自动化](03-交互模式与自动化.md)和[Codex 的 TOML、Profile 与凭证](../Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)。

官方参考：

- [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
- [Codex configuration](https://developers.openai.com/codex/config-reference/)
- [Codex permissions](https://developers.openai.com/codex/permissions/)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
