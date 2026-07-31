# 02 权限、Sandbox 与项目配置

> 官方产品名：Grok Build  
> 最近核对：2026-07-31

Grok Build 把交互批准、Allow/Ask/Deny Rule、Plan、Sandbox、项目配置和扩展系统放在同一个运行环境中。权限模式决定工具调用怎样获得批准；规则提前处理匹配项；Plan 为普通编辑工具增加计划审查；Sandbox 限制获准进程能接触的资源；`grok inspect` 则展示用户、项目和组织来源合并后的实际状态。任何一层都不能独自代表完整安全边界。

Shell、网络、凭据、Docker 和远程主机的共同风险统一见[权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)。

## 1. 先从最终加载状态理解权限模式

在项目根目录查看当前工作区和 Grok 实际读取的来源：

```bash
pwd
git status
grok inspect
grok inspect --json
```

重点核对工作目录、仓库根、用户与项目配置、模型、权限模式、Rule、Sandbox、`AGENTS.md`、Skills、Plugins、Agents、Hooks、MCP、LSP，以及 Claude Code 兼容发现。命令行参数、环境变量、组织 Requirements 和扩展都可能改变最终行为，只阅读 `~/.grok/config.toml` 或界面状态栏无法覆盖所有来源。

结构化结果可以保存作比较：

```bash
grok inspect --json > grok-inspect.json
```

文件中可能带有路径、服务地址和扩展信息，公开前需要检查。

### Ask

Ask 会对没有被 Rule 或既有授权预先处理的调用询问用户，适合陌生仓库和需要逐步确认的任务。已有 Allow Rule 可能直接放行，因此 Ask 不保证每条命令都弹窗。

### Auto

Auto 使用分类器批准被判断为安全的工具：

```text
/auto
```

危险调用仍可能询问，Deny 和 Hook 仍可阻断。分类器无法知道某个普通文件是否实际是生产配置，也不能代替组织策略和 Sandbox。

### Always-approve

Always-approve 跳过工具批准提示：

```text
/always-approve
```

命令行入口包括：

```bash
grok --always-approve
grok --yolo
```

它只改变批准方式，并没有缩小文件、网络或系统能力。Deny 和能够阻断的 PreToolUse Hook 仍可能拦截调用，但它们也不能替代完整 Sandbox。

用户级默认可写为：

```toml
[ui]
permission_mode = "ask"
```

当前正式值包括 `ask`、`auto` 和 `always-approve`。用户习惯不适合无差别覆盖 Mac、远程 Ubuntu、CI 和所有仓库。

## 2. Plan 是编辑门槛，不是完整只读模式

Plan 可以和 Ask、Auto 或 Always-approve 组合：

```text
/plan
/view-plan
```

Plan 阶段只允许普通 Edit 工具修改会话计划文件，计划完成后会进入独立预览和批准界面；Auto 和 Always-approve 不会跳过这次计划审查。

但 Plan 的边界必须写清：

```text
Edit 工具受到计划门槛
Bash、MCP 和其他工具继续遵守权限模式与 Sandbox
Bash 重定向仍可能写文件
子 Agent 不继承父会话的 Plan 编辑门槛
```

因此，`Plan + Always-approve` 仍可能让 Bash 或拥有写能力的 MCP 产生副作用；名称为“调查”的子 Agent 也不自动只读。高影响任务应继续使用 Ask、精确 Rule、有限 Sandbox 和明确的只读 Prompt，而不是把 Plan 当成文件系统隔离。

一种常见组合是在 `Plan + Ask` 中建立项目地图和文件级方案，批准后再按任务选择 Ask 或受控 Auto。通过 `Shift+Tab` 切换后，应查看界面状态重新确认。

## 3. Headless 还有面向自动化的权限模式

Headless 和 CI 无法持续处理交互式弹窗。官方 Enterprise 文档另外公开两种 `--permission-mode`：

```bash
grok -p "只读审查当前 diff" \
  --permission-mode dontAsk \
  --allow 'Bash(git *)' \
  --allow 'Read' \
  --allow 'Grep' \
  --deny 'Bash(rm -rf *)' \
  --sandbox strict
```

| 模式 | 行为 | 典型用途 |
| --- | --- | --- |
| `dontAsk` | 没有显式 Allow 的操作静默拒绝 | CI、只读审计、无人值守任务 |
| `acceptEdits` | 自动批准文件编辑，Shell 等其他工具仍按规则处理 | 半自动实施 |

这些模式不等于 TUI 中的 Ask/Auto 简单改名。`dontAsk` 如果缺少必要 Allow，会让任务安全地失败或无法完成；`acceptEdits` 也不是“所有写入都安全”，因为编辑范围仍取决于工作目录、Prompt、Rule 和 Sandbox。

官方企业策略还使用 `bypassPermissions` 表示跳过批准的路线。普通用户应优先使用 `--always-approve` 这一公开入口；企业可以在 root 所有的 `/etc/grok/requirements.toml` 中设置：

```toml
[ui]
disable_bypass_permissions_mode = true
```

该锁会阻止 `--yolo`、Always-approve 切换和宽泛 Catch-all Allow 重新开启绕过模式。为了防止用户自行解除，官方当前只在 root-owned 系统策略层信任这类锁，不把用户可写的 `~/.grok/requirements.toml` 当作同等级防篡改边界。

## 4. Allow/Ask/Deny Rule 与 Sandbox 解决不同问题

Rule 可以通过命令行或配置定义：

```bash
grok --allow RULE --deny RULE
```

当前规则支持 Bash、Edit、Read、Grep、MCP Tool、Web Fetch 和 Web Search 等过滤对象。核心关系是：

```text
deny > ask > allow
```

允许 `git status` 不会自然允许 `git clean`、`reset` 或 `push`；允许整个 Bash 则会显著扩大范围。弹窗里的“允许一次”“长期允许具体命令”和全局 Always-approve 也属于不同作用域。

当前内置 Sandbox Profile 包括：

```text
off
workspace
devbox
read-only
strict
```

命令行示例：

```bash
grok --sandbox workspace
grok --sandbox read-only
grok --sandbox strict
```

项目还可能提供：

```text
.grok/sandbox.toml
```

Sandbox 处理的是调用获准以后能够访问哪些文件、网络、子进程和系统资源。字段和平台能力会随版本变化，配置后应在练习项目中验证一条预期允许和一条预期拒绝的操作。

这些层可以组合，但不能互相替代：Ask 配合宽 Sandbox 会保留人工询问，批准后的影响仍然很大；Always-approve 配合有限 Sandbox 可以减少弹窗，同时保留技术边界；Always-approve 且没有有效 Sandbox，则同时失去人工停顿和资源限制。判断风险时必须同时查看权限模式、Rule、Plan、Sandbox 和 Hook。

## 5. 记住的批准与显式 Rule 强度不同

用户在审批菜单里选择的长期授权，通常只针对某个命令、工具、域或当前编辑关系；它不等于在配置中写入 Catch-all Allow。当前官方还会让部分被记住的危险命令继续询问，例如 `rm` 或 `git push`。

显式配置或 CLI Allow Rule 强度更高，匹配后可以直接批准危险模式。因此下面两种行为不能混为一谈：

```text
审批弹窗中记住一次具体授权
配置中显式 allow Bash(git *)
```

`[ui] default_selected_permission` 只决定批准菜单第一次打开时默认高亮哪一行，并不自动执行；但误按回车仍可能形成宽授权。更保守的个人默认可以写成：

```toml
[ui]
default_selected_permission = "allow_once"
remember_tool_approvals = false
```

## 6. 用户状态、项目配置与扩展按功能合并

Grok Build 用户状态通常位于 `~/.grok/`：

```text
config.toml              用户主配置
pager.toml               TUI/Pager 设置
auth.json                主账户认证
mcp_credentials.json     MCP OAuth 凭据
sessions/                会话
memory/                  记忆
skills/ plugins/ agents/ 用户级扩展
```

这些文件的敏感程度不同。迁移 UI 设置或模型别名时不应复制整个目录，更不能把认证文件和会话日志一起放进 Git。

项目可以包含：

```text
.grok/config.toml
.grok/sandbox.toml
.grok/skills/
.grok/plugins/
.grok/agents/
.grok/hooks/
.grok/lsp.json
.grok/workflows/
AGENTS.md
```

项目扩展会随仓库进入其他人的环境，应像源码一样审查。当前项目 `.grok/config.toml` 主要参与 MCP、Plugins、Permission Rules 和 MCP 输出上限；默认模型、UI 权限模式和多数用户设置不能简单下放到项目配置。配置没有生效时查看 `grok inspect`，不要把同一字段复制到更多文件。

用户与项目配置按功能合并；同名 MCP 可能由当前目录或仓库根的项目条目整体替换用户条目，而不是逐字段叠加。排查时应看最终 Server 命令或 URL、环境变量、工作目录、OAuth、输出上限和读写工具。

用户配置还可以定义模型别名和供应商：

```toml
[model.my-model]
model = "CURRENT_MODEL_ID"
base_url = "https://api.example.com"
env_key = "PROVIDER_API_KEY"

[models]
default = "my-model"
```

模型别名、Provider、API Key 和浏览器登录账号是不同对象；跨客户端的 Provider、凭据和实例概念由 Part 10C 集中解释。Grok 侧通过 `grok models`、`grok inspect` 和临时 `grok -m MODEL_NAME` 核对最终选择。

## 7. 项目规则和扩展需要按源码审查

`AGENTS.md` 适合描述项目结构、构建测试、编码约定和验收要求，但不会形成强制文件隔离。Grok Build 还能发现部分 Claude Code 规则、Hooks、MCP、Plugin、Skill 和 Agent；兼容发现只表示能够读取某些来源，不说明两个客户端拥有相同权限、Hook JSON 或退出码语义。

克隆陌生仓库后定位可能加载的项目内容：

```bash
find . -type d -name .grok -print
find . -type d -name .claude -print
find . -name AGENTS.md -print
git status
grok inspect
```

这里的 `find` 写法可在 macOS 默认 BSD `find` 中运行。需要审查的是 `.grok/config.toml`、Sandbox、Hooks、Plugins、Skills、Agents、MCP、LSP、Workflow 和兼容来源分别提供了什么能力。Skill 可能包含指令、脚本、参考资料和资源；Plugin 可以组合 Skills、Agents、Hooks、MCP 与 LSP；自定义 Agent 也可以带有模型和工具配置。Marketplace 或仓库列表只帮助发现扩展，不代表已经完成源码与权限审计。

PreToolUse Hook 用于阻断时，应在练习目录验证允许命令能否继续、拒绝命令是否确实没有执行，以及 Hook 自己报错时系统是阻断还是放行。不能直接套用 Claude Code 或 Codex 的退出码和 JSON 结构。

## 8. 修改时只改变一层，并用 `inspect` 比较

修改用户配置前确认文件并建立本地备份：

```bash
test -f ~/.grok/config.toml && echo "config exists"
mkdir -p ~/.grok/backups
cp ~/.grok/config.toml \
  ~/.grok/backups/config.toml.$(date +%Y%m%d-%H%M%S)
```

一次实验只处理一个来源：先改权限模式并用 `inspect` 验证，再加入一条 Allow/Deny 检查匹配，然后启用 Sandbox 测试允许与拒绝，最后才分别添加 Plugin、Hook 或 MCP。多层配置同时变化时，即使行为异常，也难以判断由哪一层引起。

整份复制陌生配置还可能带入第三方 Base URL、宽权限和自动脚本。更稳妥的流程是理解自己需要的字段，把它加入现有配置，再比较 `grok inspect --json` 前后变化。高影响命令是否值得批准、凭据与远程资源怎样处理，继续由[权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)承担。

延伸阅读：[安装、登录与基础使用](01-安装登录与基础使用.md)、[Headless、Worktree 与扩展系统](03-Headless-Worktree与扩展系统.md)、[TUI、斜杠命令与交互界面](04-TUI斜杠命令与交互界面.md)和[配置、模型、诊断与功能核对](08-配置模型诊断与功能核对.md)。

官方参考：

- [Grok Build Permissions](https://docs.x.ai/build/features/permissions)
- [Grok Build Plan Mode](https://docs.x.ai/build/features/plan-mode)
- [Grok Build Sandbox](https://docs.x.ai/build/features/sandbox)
- [Grok Build Settings](https://docs.x.ai/build/settings)
- [Grok Build Enterprise Deployments](https://docs.x.ai/build/enterprise)
- [Grok CLI Reference](https://docs.x.ai/build/cli/reference)
