# 02 权限、Sandbox 与项目配置

> 官方产品名：Grok Build
>
> 最近核对：2026-07-28

Grok CLI 的安全边界至少分三层：

```text
权限模式
→ 某个工具调用是否需要你批准

Sandbox
→ 已获准的操作实际能访问什么

配置作用域
→ 规则来自用户、项目还是组织管理
```

权限允许了某条命令，不代表它可以突破 Sandbox；Sandbox 很严格，也不代表可以盲目批准自己看不懂的操作。

---

## 1. Ask、Auto 和 Always-approve

### Ask

默认且最适合新手。没有被明确允许的工具调用会询问用户。

适合陌生项目、远程 Ubuntu、有未提交修改或涉及真实数据的环境。

### Auto

由分类器自动批准被判断为安全的操作，其他操作仍可能询问。

Auto 不是“绝对安全”。分类器未必知道当前路径、业务影响和用户原有修改。

### Always-approve

自动批准工具调用。它减少询问，不会自动让操作变安全。

不要把它用于：

- 主分支；
- 唯一远程连接；
- 包含凭据和真实数据的目录；
- 可控制 Docker Socket 的环境；
- 未审查的仓库、Skills、Hooks 或 MCP。

---

## 2. Plan 不是权限模式

Plan 用来先分析和制定方案：

```text
/plan
```

它可以和 Ask、Auto 或 Always-approve 组合。新手推荐：

```text
Plan
→ 审查范围和测试
→ 切回 Ask
→ 分阶段执行
```

不要把 Plan 理解成后续操作都会自动安全。

---

## 3. Allow 与 Deny 规则

Grok CLI 支持工具级允许与拒绝规则。核心原则是：

```text
Deny 优先于 Allow
```

只允许明确、低风险的操作，比允许全部 Shell 命令更安全。

例如，允许 `git status` 和 `git diff`，不等于应该允许所有 Git 命令。`git push`、`git clean` 和历史改写的风险完全不同。

规则格式与工具名称可能变化，使用前检查：

```bash
grok --help
grok inspect
```

---

## 4. 临时授权和持久配置不是一回事

界面中的一次允许、本次会话允许和写入配置的长期 Allow，影响范围不同。

修改持久规则前先问：

- 是否只针对只读命令；
- 匹配模式是否过宽；
- 是否可能误匹配删除、覆盖或推送；
- 是否适用于所有项目；
- 是否应该放到项目级而不是用户级。

---

## 5. Sandbox 是独立边界

Grok CLI 当前支持通过 Sandbox Profile 限制：

- 文件读写范围；
- 网络访问；
- 子进程；
- 系统资源；
- 工作区外路径。

具体 Profile 名称和默认行为应查看：

```bash
grok --help
grok inspect
```

Sandbox 不是完整虚拟机。如果当前用户能控制远程主机、Docker 或高权限工具，Agent 获得对应命令能力后，影响范围仍会扩大。

---

## 6. Sandbox 不能代替 Git

即使只允许写工作区，Agent 仍可能覆盖源码、删除未跟踪文件、修改锁文件或生成大量无关内容。

开始前：

```bash
git status
git switch -c task/grok-change
```

结束后：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Git 也无法撤回已经发送到网络的数据、数据库写入、Docker Volume 变化或远程系统操作。

---

## 7. 配置作用域

### 用户配置

通常位于：

```text
~/.grok/config.toml
```

或设置 `GROK_HOME` 后的对应目录。

适合默认模型、UI 偏好、用户级权限和扩展设置。

### 项目配置

通常位于：

```text
PROJECT_ROOT/.grok/config.toml
```

适合共享项目级 MCP、插件和权限规则。项目配置不应包含个人 API Key。

### Managed 与 Requirements

组织环境可能提供管理配置和强制要求。个人设备通常不需要主动创建这些文件。

---

## 8. 使用 `grok inspect` 看真实状态

```bash
grok inspect
```

它可以帮助查看当前目录发现的：

- 配置来源；
- Rules；
- Skills；
- Plugins；
- Hooks；
- MCP Servers；
- 兼容规则文件。

排查“为什么自动批准”“为什么加载了某个 MCP”时，先看真实加载结果，不要只翻自己记得的配置文件。

---

## 9. 克隆陌生仓库后先审查项目配置

```bash
find . -type d -name .grok -print
git status
grok inspect
```

这里不使用 GNU `find` 的 `-maxdepth`，因此可以直接在默认的 macOS BSD `find` 中运行。仓库很大时，也可以先用 `find . -type d -name .grok -print` 只定位配置目录，再逐个查看内容。

重点检查：

- 第三方 MCP；
- 插件来源；
- 宽泛 Allow；
- 自动执行的 Hooks；
- 是否读取兼容的 Claude Code 或 AGENTS.md 规则；
- 是否可能把环境变量和源码发送到外部服务。

仓库里的规则、Skills、Hooks 和 MCP 都属于潜在供应链与提示注入入口。

---

## 10. 网络访问要单独批准

Grok CLI 可能使用 Web Search、Web Fetch、依赖下载、MCP 和远程仓库。

私有项目中应明确：

- 哪些内容可以离开本机；
- 哪些域名允许访问；
- 是否真的需要联网；
- 外部服务由谁维护；
- 日志是否保存源码；
- 是否符合组织要求。

不要因为任务只说“查文档”，就默认开放所有网络能力。

---

## 11. Hooks、Skills、Plugins 与 MCP 都会扩大权限面

启用前确认：

- 来源和维护者；
- 是否运行脚本；
- 读取与写入哪些路径；
- 是否访问网络；
- 是否读取环境变量；
- 是否自动调用其他工具；
- 是否会把内容发送给第三方。

扩展能提高效率，也可能把一次普通工具调用变成一串自动动作。

---

## 12. 审批命令时看什么

```text
当前目录
完整命令和参数
目标路径
是否递归或含通配符
是否覆盖或删除
是否访问网络
是否修改依赖或 Git 历史
是否触及项目外路径
失败后怎样恢复
```

看不懂时先拒绝：

```text
不要执行。
请逐段解释命令、参数、目标路径、影响范围、失败后果和更保守的替代方案。
```

---

## 13. 新手推荐流程

```text
进入项目根目录
→ git status
→ grok inspect
→ Plan + Ask
→ 明确文件与测试范围
→ 分阶段修改
→ 逐条审批命令
→ 运行测试
→ git diff
→ 人工决定是否提交
```

延伸阅读：

- [安装、登录与基础使用](01-安装登录与基础使用.md)
- [Headless、Worktree 与扩展系统](03-Headless-Worktree与扩展系统.md)
- [权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)

官方参考：

- [Grok permissions](https://docs.x.ai/build/features/permissions)
- [Grok modes and commands](https://docs.x.ai/build/modes-and-commands)
