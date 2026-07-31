# 07 扩展系统、MCP、ACP 与跨客户端兼容

> 官方产品名：Grok Build  
> 最近核对：2026-07-31

Grok Build 的扩展面包括 Skill、Plugin、Marketplace、Hook、Agent、Persona、MCP、LSP、代码索引、Workflow 与 ACP。它还会读取部分 Claude Code、Cursor 和 AGENTS.md 生态内容。扩展越多，不代表能力越可靠；每增加一层，都要重新核对来源、权限、凭据、日志、网络和恢复方式。

## 1. Skill 为什么会出现在 `/` 菜单

任何启用且在 `SKILL.md` 中声明 `user-invocable: true` 的 Skill 都可以成为 Slash Command。常见来源包括：

```text
Grok 捆绑 Skill
~/.grok/skills/ 用户 Skill
.grok/skills/ 项目 Skill
额外 [skills].paths
Plugin 提供的 Skill
兼容扫描发现的外部 Skill
```

例如用户目录存在 `~/.grok/skills/commit/SKILL.md` 时，可能出现：

```text
/commit 修正文档中的拼写错误
```

同名 Skill 可用作用域区分：

```text
/local:commit
/user:commit
```

内置命令优先于同名 Skill。看到 `/resume-codex`、`/resume-claude` 等命令时，不要先假设它是核心内置功能；应在 `/skills` 和 `grok inspect` 中查看来源，再阅读对应 `SKILL.md`、脚本和兼容配置。

用户配置可以增加、忽略或停用 Skill 路径：

```toml
[skills]
paths = ["~/my-team-skills"]
ignore = ["~/my-team-skills/wip"]
disabled = ["wip-skill"]
```

Skill 不只是 Prompt，也可能携带脚本、参考资料和资源文件。项目 Skill 会随仓库进入其他人的环境，应像源码一样审查。

## 2. Plugin 是扩展组合包

Plugin 可以同时携带 Skills、Agents、Hooks、MCP、LSP、Persona 和其他资源。TUI 入口包括：

```text
/plugins
/marketplace
/skills
/hooks
```

这些入口通常打开统一扩展面板的不同标签。Shell 层提供更细的管理命令：

```bash
grok plugin list
grok plugin install SOURCE
grok plugin uninstall NAME
grok plugin update
grok plugin enable NAME
grok plugin disable NAME
grok plugin details NAME
grok plugin validate PATH

grok plugin marketplace list
grok plugin marketplace add SOURCE
grok plugin marketplace remove NAME
grok plugin marketplace update
```

实际参数以 `grok plugin --help` 为准。Marketplace 只解决发现和安装，不代表扩展已经完成安全审计。

安装前至少检查：

```text
仓库、维护者、版本和最近更新
安装脚本与下载来源
文件、Shell、网络和凭据权限
携带的 Hook、MCP、Agent、LSP 与后台进程
日志、遥测和数据保留
禁用、卸载和恢复方式
```

## 3. Hook 既能阻断，也能扩大执行面

Hook 可以在工具调用前后、文件修改后或会话结束时运行脚本。来源包括：

```text
~/.grok/hooks/
额外的用户 Hook 路径
项目 .grok/hooks/
Plugin
Claude Code 或 Cursor 兼容来源
```

项目 Hook 通常需要显式信任。当前上游在 Shell 层还提供 `/hooks-list`、`/hooks-trust`、`/hooks-add`、`/hooks-remove` 和 `/hooks-untrust` 等入口，而 TUI 主要通过 `/hooks` 面板管理。

用于阻断危险操作的 PreToolUse Hook 必须在练习目录验证：

```text
预期允许的命令确实继续
预期拒绝的命令没有执行
Hook 报错时究竟阻断还是放行
日志没有泄露 Prompt、环境变量和凭据
```

不能照搬另一客户端的事件名、JSON 和退出码语义。即使 Grok 自动读取 Claude Hook，也应检查转换后的实际行为。

## 4. MCP 把外部数据和操作带入会话

`/mcps` 打开 MCP 管理界面。Shell 层包括：

```bash
grok mcp list
grok mcp add ...
grok mcp remove NAME
grok mcp doctor
```

MCP Server 可以通过本地 stdio、HTTP 或其他受支持传输提供文档、数据库、浏览器、GitHub、云平台或内部服务工具。需要核对：

```text
Server 命令或 URL
传输方式和 TLS
读写工具与资源范围
OAuth、API Key 和环境变量
启动与调用超时
工作目录、输出上限和日志
服务端数据保留与审计
```

主账户认证与 MCP OAuth 凭据分离，`grok logout` 不一定撤销外部 MCP 授权。删除 Server 后还要检查 `~/.grok/mcp_credentials.json`、服务端授权和相关环境变量。

MCP 返回内容属于不可信输入。外部文档要求读取 HOME、上传环境变量或关闭 Sandbox 时，不应自动执行。MCP 工具仍受权限模式、Allow/Deny、Hook 和 Sandbox 约束。

## 5. 用户与项目配置的作用域不同

项目 `.grok/config.toml` 当前主要贡献：

```text
[mcp_servers]
[plugins]
[permission]
[mcp] max_output_bytes
```

其余大多数主配置只从用户 `~/.grok/config.toml` 读取。MCP 与 Plugin 的优先级通常为：

```text
当前目录 .grok/config.toml
> 仓库根 .grok/config.toml
> 用户 ~/.grok/config.toml
```

同名 MCP 是整体替换，不是逐字段合并。Permission Rule 则跨来源合并，并遵守 `deny > ask > allow`。只看一份配置文件无法判断最终结果，应使用 `grok inspect`。

## 6. LSP 与代码索引

LSP 配置来源包括：

```text
~/.grok/lsp.json
项目 .grok/lsp.json
Plugin 的 .lsp.json 或 plugin.json 内联定义
```

当前优先级为项目、用户、Plugin。项目或用户定义会替换低优先级同名 Server；Plugin 只补充尚未定义的名称，并且只有受信任的 Plugin 才加载 LSP。

LSP 会启动额外进程、扫描代码并产生缓存或日志。需要确认安装来源、启动命令、工作目录、排除范围和下载行为。`[features] lsp_tools` 控制是否向 Agent 暴露 LSP 工具；被动诊断与 Agent 可调用工具不应混为一谈。

代码索引可能由 `[features] codebase_indexing` 控制。它可以改善符号关系检索，但不保证理解正确，也可能增加启动时间、磁盘占用和隐私范围。大型私有仓库应核对索引范围、缓存位置和清理方式。

## 7. ACP 把 Grok 交给其他宿主驱动

ACP 入口为：

```bash
grok agent stdio
```

编辑器或其他客户端通过标准输入输出驱动 Grok。此时工作目录、自动附加文件、审批界面、Sandbox、额外工具和日志可能同时受到宿主与 Grok 两侧控制。换成图形界面不会自动缩小权限。

ACP 故障应同时记录：

```text
宿主版本与 Grok 版本
启动命令和参数
工作目录
传入规则与附件
权限和 Sandbox
stdout/stderr 与日志
```

终端中直接运行正常，不能证明 ACP 中上下文、工具和权限完全相同。

## 8. Claude 兼容发现是自动的，但不代表语义完全相同

当前官方 Skills、Plugins & Marketplaces 文档把 Claude Code 兼容描述为无需额外配置，并列出 Grok 会自动读取：

```text
Claude Marketplace
Plugin
Skill
MCP
Agent
Hook
CLAUDE.md、Claude.md、CLAUDE.local.md
.claude/rules/
```

Grok 也读取从当前目录到仓库根的 AGENTS.md 家族，并可发现 `~/.agents/skills/` 与 `~/.agents/commands/`。

“自动读取”只表示发现和兼容层生效，不表示权限规则、Hook JSON、退出码、MCP 凭据、Agent 工具或执行顺序完全等同。进入陌生仓库后仍要查看：

```bash
find . -name AGENTS.md -print
find . -type d -name .grok -print
find . -type d -name .claude -print
grok inspect
```

## 9. 三种 Claude 导入必须分开

### `/import-claude`

这是 TUI 设置导入面板，读取 `~/.claude` 中可识别的权限、环境变量、MCP、Hook 和路径配置。它是一次配置迁移，不是会话恢复，也不是两套客户端永久同步。

### `grok import [targets...]`

这是正式 CLI 子命令，当前官方 CLI Reference 将它描述为从 Claude Code 导入会话。它与 `/import-claude` 的设置迁移不同。执行前查看：

```bash
grok import --help
```

导入后的会话仍不包含原 Claude 进程、外部服务状态、环境变量快照或 Git 恢复点。

### `resume-claude` Skill 与兼容 Session Cell

这是另一条实验性兼容路径。上游配置说明 Session Cell 仍处于 staged 状态，直到 Foreign-session Scanner 消费它；同时还需要匹配的 `resume-claude` Skill。缺少 Skill 时不会读取对应外部会话目录。

三者不能用同一个“导入 Claude”概括。

## 10. Codex 与 Cursor 会话兼容仍是 staged

当前上游配置包括：

```toml
[compat.cursor]
sessions = true

[compat.claude]
sessions = true

[compat.codex]
sessions = true
```

但文档同时明确标注这些 Session Cell 仍是 staged、尚无 Scanner Consumer；每个工具还需要对应的 `resume-cursor`、`resume-claude` 或 `resume-codex` Skill。没有匹配 Skill，就不会发生外部会话文件系统读取。

Codex 的 `skills`、`rules`、`agents`、`mcps` 和 `hooks` 兼容单元目前只是保留字段，并不会启用 `.codex` 发现。因此，看到 `/resume-codex` 只能证明当前环境有一个可调用 Skill，不能直接证明稳定的 Codex Session Scanner 已经接通。

即使未来扫描成功，通常也只是把历史、摘要或记录转换为 Grok 上下文，不会继承：

```text
原 Codex 或 Cursor 进程
原 Sandbox 和审批策略
原 Provider 与账号
原环境变量
原工作区和外部系统状态
```

恢复后仍要重新检查：

```bash
hostname
pwd
git branch --show-current
git rev-parse HEAD
git status --short
grok inspect
```

## 11. Persona 与 Agent Definition 不是隔离机制

`/config-agents` 管理 Agent Definition，`/personas` 管理角色指令。Agent Definition 可以指定模型、工具和行为，Persona 主要塑造工作方式。名称为 `reviewer` 的 Agent 如果拥有 Shell、Edit 或写入型 MCP，依然可以改变文件与外部系统。

项目级 Agent、Persona、Skill 和 Workflow 应像源码一样审查，不能把真实凭据、个人绝对路径或宽权限默认写进公开仓库。

## 12. 用 `inspect` 收束全部来源

扩展与兼容配置分散时，最终判断回到：

```bash
grok inspect
grok inspect --json > grok-inspect.json
```

重点确认：

```text
用户、项目与组织配置
AGENTS.md 与 Claude 规则来源
Permission 与 Sandbox
Skills、Plugins、Agents、Personas
Hooks、MCP、LSP、Workflow
兼容 Cell 的解析状态
```

JSON 可能包含路径、服务地址和扩展元数据，公开前先检查。

官方参考：

- [Skills, Plugins & Marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- [Grok CLI Reference](https://docs.x.ai/build/cli/reference)
- [Grok Build Skills](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/08-skills.md)
- [Grok Build Configuration](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/05-configuration.md)
- [Grok Build Hooks](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md)
