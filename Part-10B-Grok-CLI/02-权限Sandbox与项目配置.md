# 02 权限、Sandbox 与项目配置

> 官方产品名：Grok Build
>
> 最近核对：2026-07-29

Grok Build 的安全边界至少分成六层：

```text
任务范围
→ Prompt 与规则说应该做什么

权限模式
→ 工具调用是否需要用户批准

Allow / Deny
→ 哪些工具或命令被预先允许或拒绝

Sandbox
→ 已获准操作实际能访问哪些路径、网络和进程

Hooks 与扩展
→ 工具调用前后是否自动执行其他动作

操作系统账户
→ 当前用户本身能控制哪些本机或远程资源
```

任何一层都不能替代其他层。Prompt 里写“不要访问网络”不等于网络已经关闭；Sandbox 限制工作区，也不等于所有工作区内修改都合理。

## 1. 启动前先检查真实加载状态

在项目根目录运行：

```bash
pwd
git status
grok inspect
```

需要机器可读信息时：

```bash
grok inspect --json
```

重点确认：

- 当前工作目录与仓库根；
- 用户和项目配置来源；
- 当前模型；
- 权限规则；
- Sandbox 配置；
- Rules 与 `AGENTS.md`；
- Skills、Plugins、Agents 与 Hooks；
- MCP Servers；
- Claude Code 兼容配置是否启用。

不要凭“上次是 Ask”判断当前状态。命令行参数、用户配置和项目配置都可能改变最终行为。

## 2. Ask、Auto 与 Always-approve

### 2.1 Ask

Ask 是最适合陌生项目和新手的模式。未被明确允许的工具调用会向用户请求批准。

适合：

- 刚克隆的仓库；
- 远程 Ubuntu 游戏本；
- 工作区有未提交修改；
- 涉及数据库、Docker 或网络；
- 还不能快速判断 Shell 命令风险。

Ask 不等于每条命令都会询问。已经被 Allow 规则放行的动作可能直接执行，因此仍要检查已有规则。

### 2.2 Auto

Auto 使用分类器自动批准被判断为安全的操作，其余操作仍可能询问。

在 TUI 中可以使用：

```text
/auto
```

命令行参数和配置名称以当前帮助为准。

Auto 可以减少重复确认，但分类器不知道所有业务背景。例如，修改一个普通 JSON 文件在技术上风险较低，但该文件可能是生产部署清单。

### 2.3 Always-approve

Always-approve 自动批准工具调用：

```text
/always-approve
```

命令行入口当前包括：

```bash
grok --always-approve
```

别名可能包括：

```bash
grok --yolo
```

不要把它写成日常 Shell 别名。Always-approve 只是减少审批，不会自动缩小文件、网络或系统权限。

即使开启 Always-approve，Deny 规则和能够阻断的 PreToolUse Hook 仍然应生效。但它们不能保证覆盖所有风险。

## 3. Plan 是任务阶段，不是权限模式

进入 Plan：

```text
/plan
```

它可以和 Ask、Auto 或 Always-approve 组合。推荐流程：

```text
Plan + Ask
→ 只读建立项目地图
→ 输出文件级计划与测试方法
→ 人工确认
→ 退出 Plan
→ Ask 或受控 Auto 分阶段执行
```

Plan 的目标是先理解和设计，不代表后续命令受到更强操作系统隔离。

复杂任务还可以显式禁用 Plan 能力：

```bash
grok --no-plan
```

但普通开发没有必要为了减少步骤而默认关闭。

## 4. 在 TUI 中切换模式

当前版本可以通过斜杠命令切换，并可能支持 `Shift+Tab` 循环权限模式。具体按键以 `/help` 为准。

切换后应再次确认界面状态，不要只根据按键次数猜当前模式。

用户级默认值可以写入：

```toml
[ui]
permission_mode = "ask"
```

也可能使用 `auto` 或 `always_approve` 等当前支持值。不要把 Always-approve 设置成全局默认，尤其是同时在 Mac、远程 Ubuntu 和多个项目中使用同一用户配置时。

## 5. Allow 与 Deny 的核心优先级

Grok Build 支持通过命令行和配置预先允许或拒绝工具规则：

```bash
grok --allow RULE --deny RULE
```

具体规则语法和工具名称使用前查看：

```bash
grok --help
grok inspect
```

最重要的原则：

```text
Deny 始终优先于 Allow
```

例如可以允许只读 Git 命令，同时拒绝推送与清理。规则应针对明确命令，而不是笼统允许全部 Shell。

```text
git status
≠ git clean
≠ git reset
≠ git push
```

显式 CLI 或配置 Allow 可能批准原本被分类为危险的命令。不要认为“系统仍然会二次判断”。放宽规则前必须理解匹配范围。

## 6. 临时批准与持久规则不同

权限弹窗中可能出现：

```text
允许一次
本次会话允许
长期允许
```

影响范围不同。写入长期配置前检查：

- 是否只针对低风险只读命令；
- 是否会误匹配删除、覆盖或远程操作；
- 是否适用于所有仓库；
- 是否应该是项目规则而非用户全局规则；
- 团队成员是否会继承该规则；
- 配置能否被 Git 提交。

方便完成一次任务，不等于适合成为永久默认。

## 7. Sandbox 是独立的技术边界

Grok Build 可以通过 Sandbox 限制工具执行环境。入口包括：

```bash
grok --sandbox
```

项目还可能包含：

```text
.grok/sandbox.toml
```

具体字段和平台能力以当前官方文档与开源仓库为准。

Sandbox 通常用于限制：

- 文件系统读写；
- 工作区外路径；
- 网络；
- 子进程；
- 系统资源。

它不是完整虚拟机。如果当前用户能通过 SSH、Docker、sudo、数据库客户端或云 CLI 控制其他资源，允许相应命令后仍可能扩大影响范围。

## 8. Sandbox 与权限模式如何配合

可以把关系理解为：

```text
权限模式
→ 这次调用要不要先问

Sandbox
→ 调用获准以后能碰到哪里
```

例如：

```text
Ask + 宽 Sandbox
→ 每次可能问，但批准后影响范围大

Always-approve + 窄 Sandbox
→ 不询问，但技术范围相对有限

Always-approve + 无 Sandbox
→ 无询问且范围宽，风险最高
```

新手优先：

```text
Ask
+
项目级有限 Sandbox
+
Git 任务分支
```

## 9. 用户配置目录结构

Grok Build 的用户状态通常位于：

```text
~/.grok/
```

常见内容包括：

```text
~/.grok/config.toml
→ 用户级主配置

~/.grok/pager.toml
→ Pager / TUI 相关配置

~/.grok/auth.json
→ 主账户认证

~/.grok/mcp_credentials.json
→ MCP OAuth 凭据

~/.grok/sessions/
→ 会话

~/.grok/memory/
→ 记忆

~/.grok/skills/
~/.grok/plugins/
~/.grok/agents/
→ 用户级扩展
```

这些文件的敏感程度不同。不要为了迁移一个 UI 设置而复制整个 `~/.grok`。

## 10. 项目 `.grok` 目录

项目可以包含：

```text
PROJECT_ROOT/.grok/config.toml
PROJECT_ROOT/.grok/skills/
PROJECT_ROOT/.grok/plugins/
PROJECT_ROOT/.grok/agents/
PROJECT_ROOT/.grok/hooks/
PROJECT_ROOT/.grok/lsp.json
PROJECT_ROOT/.grok/sandbox.toml
PROJECT_ROOT/AGENTS.md
```

项目扩展可能随 Git 仓库进入团队环境。因此克隆陌生仓库后，它们应像代码一样接受审查。

## 11. 项目配置不能覆盖全部用户设置

这是非常容易误解的地方。项目级：

```text
.grok/config.toml
```

当前主要参与：

- MCP Server 定义；
- Plugins；
- Permission Rules；
- MCP 输出大小限制等项目范围设置。

很多其他设置仍然只从用户配置读取，例如默认模型、UI 权限模式和部分全局行为。

因此，不要在项目 `.grok/config.toml` 中写一个默认模型后，看到没有生效就不断复制配置。先查看官方 Settings 文档和：

```bash
grok inspect
```

项目配置同样不应包含个人 API Key、登录 Session 或 OAuth 凭据。

## 12. 配置合并与同名 MCP

用户级和项目级配置会按功能进行合并。项目 MCP Server 与全局 MCP 同名时，项目定义可能完整替换全局定义，而不是逐字段拼接。

排查时不要只看一份文件：

```bash
grok inspect --json > grok-inspect.json
```

然后确认最终使用的：

- Server 命令或 URL；
- 环境变量名；
- 工作目录；
- OAuth 状态；
- 输出上限；
- 读写能力。

## 13. 模型配置与供应商配置

用户配置可以定义模型：

```toml
[model.my-model]
model = "CURRENT_MODEL_ID"
base_url = "https://api.example.com"
env_key = "PROVIDER_API_KEY"

[models]
default = "my-model"
```

字段和支持能力随版本变化，使用前查看 Settings 文档。

注意：

```text
模型别名
≠ 模型供应商
≠ API Key
≠ 当前登录账户
```

第三方 Base URL 会改变项目代码与 Prompt 发送到哪里。不要从论坛复制未知端点，也不要把真实 Key 直接写进 TOML。

查看最终模型：

```bash
grok models
grok inspect
```

临时指定：

```bash
grok -m MODEL_NAME
```

## 14. `AGENTS.md` 与兼容规则

Grok Build 支持项目规则，并可读取 `AGENTS.md`。规则适合保存：

- 项目结构；
- 构建与测试命令；
- 编码规范；
- 禁止修改的目录；
- Git 边界；
- 验收标准。

它不是强制安全配置。Prompt 或规则写“不要读 `.env`”，不能代替 Sandbox、文件权限和 Deny。

Grok 还提供与 Claude Code 部分规则、Hooks 和 MCP 配置兼容的发现机制。是否扫描这些来源取决于当前设置。

不要因为“兼容 Claude”就假设两个客户端的权限、匹配语法和 Hook 行为完全一致。用：

```bash
grok inspect
```

确认实际加载结果。

当前 `.codex` 兼容发现中的部分 Skills 或 Rules 位置可能仍是预留能力，不能仅凭目录存在就认为已经生效。

## 15. 克隆陌生仓库后的审查流程

先定位 Grok 项目配置：

```bash
find . -type d -name .grok -print
find . -name AGENTS.md -print
```

这里不依赖 GNU `find -maxdepth`，macOS 默认 BSD `find` 也能运行。

然后查看：

```bash
git status
grok inspect
```

重点检查：

- `.grok/config.toml`；
- `.grok/sandbox.toml`；
- `.grok/hooks/`；
- `.grok/plugins/`；
- `.grok/skills/`；
- `.grok/agents/`；
- MCP Server；
- `AGENTS.md`；
- 兼容的 `.claude` 配置。

未知扩展、Hook 和 MCP 都属于供应链与提示注入入口。

## 16. Skills、Plugins、Agents、Hooks 与 MCP 都扩大执行面

### Skill

Skill 可以包含：

- 指令；
- 脚本；
- 参考资料；
- 模板和资源文件。

### Plugin

Plugin 可能组合：

- Skills；
- Agents；
- Hooks；
- MCP；
- LSP；
- 其他扩展。

### Agent

自定义 Agent 可能获得特定工具、Prompt 与模型配置。

### Hook

Hook 会在工具调用或会话事件前后自动执行程序。

### MCP

MCP 连接外部文档、数据库、浏览器、GitHub 或内部系统。

启用任何扩展前检查：

```text
来源与维护者
执行哪些脚本
读写哪些路径
是否访问网络
读取哪些环境变量
使用什么凭据
是否能写外部系统
失败时怎样处理
```

Marketplace 或仓库列表只是发现入口，不等于 xAI 已对每个扩展完成安全审计。

## 17. Hook 可以继续执行，也可以阻断

PreToolUse Hook 可以在工具执行前检查请求。用于安全阻断时，必须按照 Grok Build 当前 Hook 协议返回明确的阻断结果或退出语义。

不要假设 Claude Code、Codex 和 Grok 的 Hook JSON 与退出码完全一样。移植 Hook 时应查看当前 Grok 文档与开源实现，并在练习目录中测试：

```text
允许命令
→ 确认能够继续

拒绝命令
→ 确认工具确实没有执行

Hook 自身报错
→ 确认系统是阻断还是放行
```

不要让 Hook 自动执行：

- `git commit` 或 `git push`；
- 删除未跟踪文件；
- 全量升级依赖；
- 修改系统配置；
- 上传源码和环境变量；
- 操作生产数据库。

## 18. 网络访问必须单独设计

Grok Build 可能通过以下路径联网：

```text
Web Search
Web Fetch
Shell 命令
包管理器
Git
MCP
Plugin
Hook
项目测试脚本
```

可以使用：

```bash
grok --disable-web-search
```

但这只关闭相关 Web Search 能力，不等于所有网络路径都被操作系统阻断。

私有项目应明确：

- 是否需要联网；
- 允许访问哪些服务；
- 是否可以发送源码；
- 外部服务保存哪些日志；
- API Key 和 OAuth 凭据放在哪里；
- 是否符合学校、团队或公司要求。

## 19. 审批命令时要阅读完整命令

至少检查：

```text
当前目录
完整命令与参数
输入重定向和管道
目标路径
是否递归或含通配符
是否覆盖或删除
是否联网
是否安装依赖
是否修改 Git 历史
是否访问 Docker、SSH、数据库或云 CLI
失败后如何恢复
```

看不懂时先拒绝：

```text
不要执行。
请逐段解释当前目录、命令、参数、目标路径、网络访问、影响范围、失败后果和更保守的替代方案。
```

## 20. Docker、SSH 与远程 GPU 的额外风险

在 Ubuntu 游戏本中，Agent 可能接触：

- NVIDIA GPU；
- Docker daemon；
- 数据集与模型；
- SSH 配置；
- tmux 中的训练进程；
- 局域网或异网主机。

启动前运行：

```bash
hostname
whoami
pwd
git status
docker context show 2>/dev/null || true
nvidia-smi 2>/dev/null || true
```

不要组合：

```text
Always-approve
+ 宽 Sandbox
+ Docker Socket
+ 整个 HOME
+ SSH 私钥
+ 真实云凭据
```

Worktree 和 Git 分支无法撤销远程主机、数据库和 Docker Volume 的副作用。

## 21. 配置修改采用单变量实验

修改用户配置前备份：

```bash
mkdir -p ~/.grok/backups
cp ~/.grok/config.toml \
  ~/.grok/backups/config.toml.$(date +%Y%m%d-%H%M%S)
```

文件不存在时先检查：

```bash
test -f ~/.grok/config.toml && echo "config exists"
```

每次只改一项：

```text
先改权限模式
→ 新开会话检查

再加一条 Allow 或 Deny
→ 验证匹配

再启用 Sandbox
→ 测试允许与拒绝

最后添加 Plugin、Hook 或 MCP
→ 分别核对
```

不要整份复制陌生人的配置。里面可能同时存在第三方 Base URL、宽权限、未知 MCP 和自动 Hook。

## 22. Git 是必要检查线

开始前：

```bash
git status
git switch -c task/grok-permission-demo
```

结束后：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Git 能恢复许多已跟踪文件修改，但不能撤回：

- 已发送到网络的数据；
- 数据库写入；
- Docker Volume 变化；
- 项目外文件覆盖；
- SSH 远程操作；
- 未备份的未跟踪文件删除。

## 23. 新手推荐工作流

```text
进入项目根目录
→ git status
→ grok inspect
→ 审查 .grok 与 AGENTS.md
→ Plan + Ask
→ 明确允许文件和测试命令
→ 分阶段执行
→ 逐条审批越界操作
→ 运行测试
→ git diff
→ 人工决定是否提交
```

推荐 Prompt：

```text
先不要修改文件。
请列出当前目录、实际加载的规则、权限模式、Sandbox、Hooks、Plugins、Skills 和 MCP。

输出准备读取与修改的文件、计划执行的命令、网络访问、风险和验证方式。
任何删除、覆盖、安装、联网、Git 写操作、项目外访问、Docker、SSH 或高权限操作都必须先说明。
完成后不要提交或推送。
```

## 延伸阅读

- [安装、认证与第一次使用](01-安装登录与基础使用.md)
- [Headless、Worktree 与扩展系统](03-Headless-Worktree与扩展系统.md)
- [权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)

官方参考：

- [Grok permissions](https://docs.x.ai/build/features/permissions)
- [Grok settings](https://docs.x.ai/build/settings)
- [Grok modes and commands](https://docs.x.ai/build/modes-and-commands)
- [Grok Build 官方开源仓库](https://github.com/xai-org/grok-build)
