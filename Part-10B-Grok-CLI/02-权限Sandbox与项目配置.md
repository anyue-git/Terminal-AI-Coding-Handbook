# 02 权限、Sandbox 与项目配置

> 官方产品名：Grok Build  
> 最近核对：2026-07-29

Grok Build 把交互批准、Allow/Deny、Sandbox、项目配置和扩展系统放在同一个运行环境中。Ask、Auto 与 Always-approve 决定工具调用怎样获得批准；Allow/Deny 处理规则匹配；Sandbox 限制获准进程能接触的资源；`grok inspect` 则展示用户配置、项目配置和扩展合并后的实际状态。Shell、网络、凭据、Docker 和远程主机的共同风险统一见[权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)。

## 1. 先从最终加载状态理解权限模式

在项目根目录查看当前工作区和 Grok 实际读取的来源：

```bash
pwd
git status
grok inspect
grok inspect --json
```

重点核对工作目录、仓库根、用户与项目配置、模型、批准模式、Allow/Deny、Sandbox、`AGENTS.md`、Skills、Plugins、Agents、Hooks、MCP、LSP，以及 Claude Code 兼容发现是否启用。命令行参数和扩展都会改变最终行为，只阅读 `~/.grok/config.toml` 或界面图标无法覆盖所有来源。结构化结果可以保存作比较：

```bash
grok inspect --json > grok-inspect.json
```

文件中可能带有路径、服务地址和扩展信息，公开前需要检查。

Ask 会对没有被规则预先处理的调用询问用户，适合陌生仓库和需要逐步确认的任务；已有 Allow 规则可能直接放行，因此它不保证每条命令都弹窗。Auto 使用分类器批准被判断为安全的调用：

```text
/auto
```

分类器并不知道某个看似普通的 JSON 是否实际是生产配置。Always-approve 则自动批准工具调用：

```text
/always-approve
```

命令行入口包括：

```bash
grok --always-approve
grok --yolo
```

Always-approve 只改变批准方式，并没有缩小文件、网络或系统能力。Deny 和能够阻断的 PreToolUse Hook 仍可能拦截调用，但它们也不能替代完整 Sandbox。

Plan 是任务阶段，可以和 Ask、Auto 或 Always-approve 组合：

```text
/plan
```

一种常见组合是在 `Plan + Ask` 中建立项目地图和文件级方案，确认后退出 Plan，再按任务选择 Ask 或受控 Auto。通过快捷键切换后，应查看界面或 `inspect` 重新确认。用户级默认可能写成：

```toml
[ui]
permission_mode = "ask"
```

字段和值以当前 Settings 为准；用户习惯不适合无差别覆盖 Mac、远程 Ubuntu 和所有仓库。

## 2. Allow/Deny 与 Sandbox 解决不同问题

规则可以通过命令行或配置定义：

```bash
grok --allow RULE --deny RULE
```

工具名和匹配语法以 `grok --help` 与 `grok inspect` 为准，核心关系是 Deny 高于 Allow。允许 `git status` 不会自然允许 `git clean`、`reset` 或 `push`；允许整个 Shell 则会显著扩大范围。弹窗里的“允许一次”“本次会话允许”和长期规则也属于不同作用域。

Sandbox 的入口包括：

```bash
grok --sandbox
```

项目还可能提供：

```text
.grok/sandbox.toml
```

Sandbox 处理的是调用获准以后能够访问哪些文件、网络、子进程和系统资源。字段和平台能力会随版本变化，配置后应在练习项目中验证一条预期允许和一条预期拒绝的操作。

这几层可以组合，但不能互相替代：Ask 配合宽 Sandbox 会保留人工询问，批准后的影响仍然很大；Always-approve 配合有限 Sandbox 可以减少弹窗，同时保留技术边界；Always-approve 且没有有效 Sandbox，则同时失去人工停顿和资源限制。判断风险时需要同时查看批准方式、规则与 Sandbox，而不是只看一个模式名称。

## 3. 用户状态、项目配置与扩展按功能合并

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
AGENTS.md
```

项目扩展会随仓库进入其他人的环境，应像源码一样审查。当前项目配置主要参与 MCP、Plugins、Permission Rules 和项目范围行为，默认模型、UI 权限模式等许多设置仍来自用户层。配置没有生效时查看 `grok inspect`，不要把同一字段复制到更多文件。

用户与项目配置按功能合并；同名 MCP 可能由项目条目整体替换用户条目，而不是逐字段叠加。排查时应看最终 Server 命令或 URL、环境变量、工作目录、OAuth、输出上限和读写工具。用户配置还可以定义模型别名和供应商：

```toml
[model.my-model]
model = "CURRENT_MODEL_ID"
base_url = "https://api.example.com"
env_key = "PROVIDER_API_KEY"

[models]
default = "my-model"
```

字段以当前版本为准。模型别名、供应商、API Key 和浏览器登录账号是不同对象；跨客户端的 Provider、凭据和实例概念由 Part 10C 集中解释。Grok 侧通过 `grok models`、`grok inspect` 和临时 `grok -m MODEL_NAME` 核对最终选择。

`AGENTS.md` 适合描述项目结构、构建测试、编码约定和验收要求，但不会形成强制文件隔离。Grok Build 还能发现部分 Claude Code 规则、Hooks 和 MCP 配置；兼容发现只表示能够读取某些来源，不说明两个客户端拥有相同权限、Hook JSON 或退出码语义。克隆陌生仓库后定位可能加载的项目内容：

```bash
find . -type d -name .grok -print
find . -name AGENTS.md -print
git status
grok inspect
```

这里的 `find` 写法可在 macOS 默认 BSD `find` 中运行。需要审查的是 `.grok/config.toml`、Sandbox、Hooks、Plugins、Skills、Agents、MCP、LSP 和兼容来源分别提供了什么能力。Skill 可能包含指令、脚本、参考资料和资源；Plugin 可以组合 Skills、Agents、Hooks、MCP 与 LSP；自定义 Agent 也可以带有模型和工具配置。Marketplace 或仓库列表只帮助发现扩展，不代表已经完成源码与权限审计。

PreToolUse Hook 用于阻断时，应在练习目录验证允许命令能否继续、拒绝命令是否确实没有执行，以及 Hook 自己报错时系统是阻断还是放行。不能直接套用 Claude Code 或 Codex 的退出码和 JSON 结构。

## 4. 修改时只改变一层，并用 `inspect` 比较

修改用户配置前确认文件并建立本地备份：

```bash
test -f ~/.grok/config.toml && echo "config exists"
mkdir -p ~/.grok/backups
cp ~/.grok/config.toml \
  ~/.grok/backups/config.toml.$(date +%Y%m%d-%H%M%S)
```

一次实验只处理一个来源：先改权限模式并用 `inspect` 验证，再加入一条 Allow/Deny 检查匹配，然后启用 Sandbox 测试允许与拒绝，最后才分别添加 Plugin、Hook 或 MCP。多层配置同时变化时，即使行为异常，也难以判断由哪一层引起。

整份复制陌生配置还可能带入第三方 Base URL、宽权限和自动脚本。更稳妥的流程是理解自己需要的字段，把它加入现有配置，再比较 `grok inspect --json` 前后变化。高影响命令是否值得批准、凭据与远程资源怎样处理，继续由[权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)承担。

延伸阅读：[安装、登录与基础使用](01-安装登录与基础使用.md)、[Headless、Worktree 与扩展系统](03-Headless-Worktree与扩展系统.md)和[配置、凭证与多实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)。

官方参考：

- [Grok CLI reference](https://docs.x.ai/build/cli/reference)
- [Grok settings](https://docs.x.ai/build/settings)
- [Grok sandboxing](https://docs.x.ai/build/features/sandbox)
- [Grok Build 官方开源仓库](https://github.com/xai-org/grok-build)
