# 02 权限、Sandbox 与配置

> 最近核对：2026-07-29
>
> Codex 的 beta Permission Profiles 正在快速变化。实际配置前同时检查 `/permissions`、`/status`、本机版本和官方文档。

Codex 能否执行一项操作，不是由一个“自动模式”开关决定的。至少要分清五层：

```text
任务范围
→ Prompt 和 AGENTS.md 说应该做什么

审批策略
→ 什么时候暂停并向用户请求批准

Sandbox 或 Permission Profile
→ 已获准的命令实际上能读写哪些路径、访问哪些网络

Rules、MCP、Skills 与 Plugins
→ 哪些额外命令和外部工具可用

操作系统与账户权限
→ 当前用户本来就能控制哪些主机资源
```

Prompt 中写“不要联网”不是网络隔离；没有出现审批弹窗，也不代表操作风险很低。

## 1. 每次会话先看真实状态

进入 Codex 后运行：

```text
/status
/permissions
```

至少确认：

- 当前工作目录和工作区根；
- 当前模型与推理强度；
- 当前认证方式；
- 当前 Sandbox 或 Permission Profile；
- 审批策略和审批者；
- 网络是否可用；
- 是否加载了 Profile、Rules、MCP、Skills 或 Plugins。

不要凭“上次是只读”判断当前会话。命令行参数、配置文件、组织要求和启动目录都可能改变最终状态。

## 2. 稳定机制：Sandbox 与审批策略

当前常见 Sandbox 模式是：

```text
read-only
workspace-write
danger-full-access
```

审批策略常见为：

```text
untrusted
on-request
never
```

它们是两个维度。Sandbox 决定技术边界，审批策略决定什么时候询问。

### 2.1 `read-only`

适合陌生项目调查、架构分析、代码审查和生成计划。Codex 可以读取工作区，但编辑文件、运行部分命令或联网可能需要审批。

显式启动：

```bash
codex --sandbox read-only --ask-for-approval on-request
```

非交互只读任务可以使用：

```bash
codex exec \
  --sandbox read-only \
  --ask-for-approval never \
  "只读总结当前项目，不要修改文件"
```

这里的 `never` 不是“允许一切”，而是“不弹出审批”。无法在只读 Sandbox 内完成的动作应失败，而不是获得额外权限。

### 2.2 `workspace-write`

这是本地开发的低摩擦模式。Codex 可以读取文件、修改工作区，并在边界内运行常规命令：

```bash
codex --sandbox workspace-write --ask-for-approval on-request
```

它通常在尝试访问工作区外路径或网络时请求批准。

工作区并不等于整块硬盘。使用 `/status` 查看实际 writable roots，不要假设当前仓库父目录、家目录或另一块数据盘也属于工作区。

在默认 `workspace-write` 机制中，工作区内的 `.git`、`.codex` 和部分受保护目录仍可能保持只读，以防 Agent 直接改写 Git 元数据或自身配置。

### 2.3 `danger-full-access`

这一模式移除本地 Sandbox 约束：

```bash
codex --sandbox danger-full-access
```

如果再配合：

```bash
--ask-for-approval never
```

Codex 将在当前用户权限下获得广泛读写和网络能力。它不应成为个人电脑、唯一远程 GPU 主机或普通项目的默认配置。

官方还提供：

```bash
codex --dangerously-bypass-approvals-and-sandbox
```

别名可能包括 `--yolo`。这个参数同时跳过审批与 Sandbox，只适合已经存在强外部隔离、数据可丢弃、凭据已移除的一次性环境。本书不把它写进别名、脚本或长期配置。

## 3. 三种审批策略如何理解

### 3.1 `untrusted`

Codex 只自动运行已知安全的读取操作。可能修改状态、触发外部执行路径或包含危险 Git 参数的命令会请求批准。

适合：

- 初次接触项目；
- 远程 Ubuntu；
- 工作区已有个人未提交修改；
- 对命令行风险还不熟悉的读者。

示例：

```bash
codex --sandbox workspace-write --ask-for-approval untrusted
```

### 3.2 `on-request`

Codex 在 Sandbox 内自行工作，需要突破边界时再请求批准。这是日常本地开发的常见组合：

```text
workspace-write
+
on-request
```

它不表示“危险命令一定会问”。一个命令只要在现有边界内能够执行，就可能无需额外确认。因此仍要用 Git、Rules 和任务范围限制行为。

### 3.3 `never`

Codex 不会停下来请求批准：

```bash
codex --ask-for-approval never
```

这在无人值守自动化中很重要，因为脚本无法点击弹窗。但它必须和有限 Sandbox 配合。

较稳妥的只读 CI 组合：

```text
read-only
+
never
```

高风险组合：

```text
danger-full-access
+
never
```

后者意味着没有审批也没有 Sandbox，不应在普通工作站上使用。

## 4. 审批者：用户与 Auto-review

默认审批请求交给用户：

```toml
approvals_reviewer = "user"
```

当前 Codex 还支持把符合条件的审批请求交给自动审查 Agent：

```toml
approval_policy = "on-request"
approvals_reviewer = "auto_review"
```

它只审查原本需要批准的动作，不会替代 Sandbox。自动审查会增加模型调用和用量，也不能替代组织政策与人工判断。

适合先在低风险练习目录中验证，不要在生产数据库、远程系统维护或密钥操作中盲目启用。

## 5. beta Permission Profiles 是另一套机制

Codex 当前提供 beta Permission Profiles，把文件系统规则与网络规则组合成命名 Profile。内置 Profile 包括：

```text
:read-only
:workspace
:danger-full-access
```

关键限制是：

```text
Permission Profiles
不能与旧 sandbox_mode 机制叠加
```

配置时二选一：

```text
default_permissions + [permissions]
```

或者：

```text
sandbox_mode + [sandbox_workspace_write]
```

只要任何已加载配置、命令行 `--sandbox` 或选中 Profile 中出现 `sandbox_mode`，Codex 会使用旧 Sandbox 设置，而不是 `default_permissions`。

因此不要为了“更安全”同时把两套配置全部复制进去。结果通常不是两层叠加，而是其中一套被覆盖。

## 6. 最小 Permission Profile 示例

下面的示例允许写当前工作区，但禁止网络：

```toml
default_permissions = "project-edit"

[permissions.project-edit]
extends = ":workspace"
description = "Write the current project without network"

[permissions.project-edit.network]
enabled = false
```

更细的 Profile 可以限制工作区内的环境文件：

```toml
default_permissions = "project-edit"

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = false
```

允许联网时最好使用域名 Allowlist，而不是直接开放全部网络：

```toml
[permissions.docs-only.network]
enabled = true

[permissions.docs-only.network.domains]
"developers.openai.com" = "allow"
"docs.python.org" = "allow"
```

Permission Profiles 仍是 beta。首次配置后应在练习项目中验证读、写、网络和拒绝行为，而不是直接用于重要项目。

## 7. 不要把配置文件与项目规则混为一谈

用户级配置通常位于：

```text
~/.codex/config.toml
```

它适合保存模型、推理强度、Sandbox、审批、Permission Profiles、网络、MCP、Profile 和功能开关。

项目规则通常放在：

```text
AGENTS.md
AGENTS.override.md
```

它适合说明：

- 项目结构；
- 测试命令；
- 编码规范；
- 不应修改的目录；
- Git 工作流；
- 任务验收要求。

`AGENTS.md` 是模型指导，不是强制技术边界。真正不允许读取 `.env` 时，应同时使用文件系统权限、Permission Profile、Sandbox 或项目外隔离。

配置与凭证的完整优先级见 Part 10C。

## 8. AGENTS 指令的加载顺序

Codex 会先检查全局目录：

```text
$CODEX_HOME/AGENTS.override.md
$CODEX_HOME/AGENTS.md
```

同一级只使用第一个非空文件。

项目中则从仓库根目录向当前工作目录逐层检查。每一级目录的顺序通常是：

```text
AGENTS.override.md
→ AGENTS.md
→ 配置的 fallback 文件名
```

同一目录只加载一个。嵌套目录中的规则更接近当前任务，优先级更高。

排查异常规则时运行：

```bash
pwd
git rev-parse --show-toplevel
find .. -name AGENTS.md -o -name AGENTS.override.md
```

然后要求 Codex：

```text
只读列出本次会话实际加载的所有指令文件及其作用域。
不要修改任何文件。
```

## 9. 网络能力不只来自 Web Search

即使关闭 Web Search，Shell、包管理器、Git、MCP、Plugins 和项目脚本仍可能访问网络。

例如：

```text
pip install
npm install
git fetch
curl
Docker build
MCP Tool
```

私有项目中需要明确：

- 是否允许代码或日志离开本机；
- 允许访问哪些域名；
- 是否需要下载依赖；
- 外部 MCP 或 Plugin 由谁维护；
- 使用的是 ChatGPT 工作区策略还是 API 组织策略。

网络返回的网页、Issue、README 和包元数据都可能包含提示注入。外部内容只能作为不可信数据，不能自动变成高优先级指令。

## 10. 审批命令时具体看什么

不要只看命令开头。至少检查：

```text
当前目录
完整命令和所有参数
目标路径
是否递归
是否含通配符
是否覆盖或删除
是否访问网络
是否安装或升级依赖
是否修改 Git 历史
是否操作远程主机、数据库或 Docker
失败后能否恢复
```

看不懂时直接拒绝：

```text
不要执行。
请逐段解释命令、参数、当前工作目录、目标路径、影响范围、失败后果和更保守的替代方案。
```

“这是测试命令”不是充分解释。测试脚本本身也可能运行安装、数据库迁移或外部服务。

## 11. Docker、SSH 与 GPU 会扩大影响范围

Sandbox 不是完整虚拟机。如果当前用户可以：

- 控制 `/var/run/docker.sock`；
- 使用 SSH 登录其他机器；
- 访问云凭据；
- 修改系统服务；
- 操作数据库；
- 使用 `sudo`；

那么 Agent 一旦获得对应命令能力，影响范围可能突破当前项目目录。

不要组合：

```text
高权限 Sandbox
+ never
+ Docker Socket
+ 整个 HOME
+ SSH 私钥
+ 真实云凭据
```

在 Ubuntu GPU 游戏本上运行前先确认：

```bash
hostname
whoami
pwd
git status
docker context show 2>/dev/null || true
```

## 12. `--full-auto` 已是兼容路径

旧教程经常使用：

```bash
codex exec --full-auto
```

当前官方文档将其保留为弃用兼容路径，并建议明确写出：

```bash
codex exec --sandbox workspace-write "TASK"
```

自动化时还应显式考虑审批策略、网络和工作目录。不要因为参数名叫 full-auto，就把它理解成推荐的最高效率模式。

## 13. 用 `codex sandbox` 测试边界

Codex 提供平台相关 Sandbox 测试入口：

```bash
# macOS
codex sandbox macos COMMAND

# Linux
codex sandbox linux COMMAND
```

Permission Profile 模式下可以查看当前版本支持的参数：

```bash
codex sandbox --help
codex sandbox macos --help
codex sandbox linux --help
```

先用无副作用命令测试：

```bash
pwd
ls
cat README.md
```

再测试预期应该失败的工作区外读取或写入。不要使用真实删除命令来证明 Sandbox 有效。

## 14. 配置修改采用单变量实验

修改前备份：

```bash
mkdir -p ~/.codex/backups
cp ~/.codex/config.toml \
  ~/.codex/backups/config.toml.$(date +%Y%m%d-%H%M%S)
```

每次只修改一个维度：

```text
先修改 Sandbox
→ 新开会话验证

再修改审批策略
→ 新开会话验证

最后添加网络、MCP 或 Profile
→ 分别验证
```

不要整份复制陌生人的 `config.toml`。其中可能同时包含高权限、第三方模型代理、未知 MCP 和过时参数。

## 15. Git 是检查线，但不是完整撤销

开始前：

```bash
git status
git switch -c task/codex-permission-demo
```

结束后：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Git 可以恢复许多已跟踪文件修改，但不能撤回：

- 已经发送到网络的数据；
- 数据库写入；
- Docker Volume 变化；
- 项目外文件覆盖；
- 远程主机操作；
- 未备份的未跟踪文件删除。

## 16. 新手推荐流程

```text
进入项目根目录
→ git status
→ 检查 AGENTS 与配置
→ /status
→ /permissions
→ read-only 调查
→ 明确文件和测试范围
→ workspace-write + on-request 执行
→ 逐条审查越界请求
→ 运行测试
→ git diff
→ 人工决定是否提交
```

推荐任务约束：

```text
先不要修改文件。
请列出当前工作目录、加载的项目规则、权限模式、可能执行的命令、网络访问和验证方式。

允许修改的文件必须明确列出。
任何删除、覆盖、安装、联网、Git 写操作、项目外访问、Docker、SSH 或高权限操作都必须先说明。
完成后不要提交或推送。
```

## 延伸阅读

- [安装、认证与第一次启动](01-安装登录与启动.md)
- [交互模式与自动化](03-交互模式与自动化.md)
- [权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)
- [Codex TOML、Profile 与凭证](../Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)

官方参考：

- [Codex permissions](https://developers.openai.com/codex/security/)
- [Codex sandboxing](https://learn.chatgpt.com/codex/sandboxing)
- [Agent approvals and security](https://learn.chatgpt.com/codex/agent-approvals-security)
- [Configuration reference](https://developers.openai.com/codex/config-reference/)
