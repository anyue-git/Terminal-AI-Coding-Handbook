# 03 会话、CLAUDE.md、Auto Memory、Hooks 与 MCP

> 最近核对：2026-07-29

Claude Code 会从多处获得上下文：当前会话保存任务过程，`CLAUDE.md` 和 `.claude/rules/` 保存人工维护的项目指导，Auto Memory 记录本机积累的项目经验，Hooks 在事件边界运行程序，MCP 则连接外部工具和数据。它们都可能影响回答，却分别属于对话、项目文档、本机记忆、自动脚本和外部服务。

## 1. 恢复会话时重新对齐磁盘现实

常用会话操作包括：

```bash
claude --name auth-validation
claude --continue
claude -c
claude --resume
claude --resume auth-validation
claude --resume auth-validation --fork-session
```

会话保存的是对话上下文，不是 Git 提交、文件快照、虚拟环境、数据库或模型供应商状态。恢复旧会话前查看：

```bash
pwd
git branch --show-current
git status
git diff --stat
git log -5 --oneline
```

分叉会话适合比较思路或做独立审查，但仍读取当前磁盘上的同一工作区。需要同时编辑两个方案时，要使用独立 Worktree。恢复后的第一步应让 Claude 重新检查目录、分支、HEAD、项目规则和测试，指出旧上下文与现实不一致的地方。

长会话的压缩和阶段交接见[大项目与多阶段任务工作流](04-大项目与多阶段任务工作流.md)。

## 2. `CLAUDE.md` 保存项目里长期成立的指导

适合写入 `CLAUDE.md` 的内容包括项目入口、目录职责、真实构建和测试命令、依赖管理、接口约定、禁止修改目录和验收方式。一次性任务计划、完整失败日志、经常变化的模型名和本机临时路径，不适合进入每次会话都会加载的项目指导。

常见层级：

```text
组织管理
macOS: /Library/Application Support/ClaudeCode/CLAUDE.md
Linux/WSL: /etc/claude-code/CLAUDE.md

用户级
~/.claude/CLAUDE.md

项目共享
PROJECT_ROOT/CLAUDE.md
或 PROJECT_ROOT/.claude/CLAUDE.md

项目本机
PROJECT_ROOT/CLAUDE.local.md
```

项目共享文件通常进入版本控制，`CLAUDE.local.md` 用于本机偏好并应加入忽略规则。Claude Code 从启动目录向父目录寻找指导文件并把内容加入上下文，不是简单以后一个文件覆盖前一个；子目录规则通常在读取对应路径时才加载。

进入会话后可用：

```text
/context
/memory
```

`/context` 用于查看实际加载的 Memory files，`/memory` 用于浏览和编辑项目指导与 Auto Memory。`/init` 可以生成或改进 `CLAUDE.md`，结果仍要通过 diff 检查：

```bash
git diff -- CLAUDE.md .claude/CLAUDE.md
```

一个简洁项目文件可以是：

```md
# 项目约定

## 环境

- Python 版本由 `.python-version` 和 `pyproject.toml` 共同约束。
- 使用 `uv sync --locked` 创建环境，Python 命令使用 `uv run`。

## 修改边界

- 不修改 `data/`、`models/`、`.env` 和生产配置。
- 必须扩大文件范围时先说明原因。

## 验证

- 单元测试：`uv run pytest -q`。
- 格式检查：`uv run ruff format --check .`。
- 静态检查：`uv run ruff check .`。
```

项目指导应尽量短而准确。完整教程、重复的安全清单和大量背景材料会长期占用上下文，却未必帮助当前任务。

## 3. 导入与路径规则用于拆分大型项目指导

`CLAUDE.md` 可以使用 `@path` 导入其他文件：

```md
@docs/development.md
@docs/testing.md
```

相对路径以当前指导文件所在目录为基准。当前官方限制递归导入最多四层；外部路径首次导入会要求批准。已有多 Agent 规范时，也可以导入 `@AGENTS.md`，再补充 Claude Code 特有内容。

大型项目可把规则拆到 `.claude/rules/`：

```text
.claude/
├── CLAUDE.md
└── rules/
    ├── testing.md
    ├── security.md
    └── frontend/react.md
```

没有路径条件的规则在启动时加载；按文件生效的规则使用 frontmatter：

```md
---
paths:
  - "src/api/**/*.py"
  - "tests/api/**/*.py"
---

# API 规则

- 所有外部输入必须验证。
- 错误响应使用统一结构。
- 修改接口行为时同步更新 API 测试和文档。
```

路径匹配依赖 Glob。规则写完后应在真实文件任务中通过 `/context` 验证是否被加载，而不是只检查 frontmatter 外观。

## 4. Auto Memory 是本机积累的项目笔记

Auto Memory 默认开启，Claude 可能记录构建命令、调试发现、架构线索和常见问题。每个 Git 仓库在本机对应一个目录：

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md
├── debugging.md
└── architecture.md
```

同一仓库的 Worktree 和子目录共享记忆，Mac 与 Ubuntu 默认不共享。每次会话只加载 `MEMORY.md` 前 200 行或 25 KB，以先达到者为准，因此主文件适合作为索引，详细内容放到主题文件。

通过 `/memory` 定期清理过时命令、旧端口、废弃路径和错误推断。关闭项目 Auto Memory：

```json
{
  "autoMemoryEnabled": false
}
```

临时全局禁用：

```bash
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude
```

需要团队共同依赖的事实，应进入项目文档、测试或人工维护的 `CLAUDE.md`；只存在本机 Auto Memory 中的内容，其他成员和其他机器都看不到。

## 5. Hooks 属于自动执行层

Hooks 可以在 Prompt 提交、工具调用前后、权限请求、会话与子 Agent 生命周期、任务完成、上下文压缩和配置变化时运行。会话中使用 `/hooks` 查看事件、匹配器、来源和完整命令。用户可控制的 Hooks 可以通过 `disableAllHooks` 临时关闭，组织管理 Hook 可能不能由普通用户覆盖。

Hook 的规则、PreToolUse 阻断示例和退出码行为已经在[权限、审批、Sandbox 与安全边界](02-权限审批与安全边界.md)主讲，本章不重复完整脚本。这里需要记住的是：Hook 会执行本机程序，属于项目供应链的一部分；PostToolUse 发生在操作之后，不能撤销已经完成的推送、删除或部署。

## 6. MCP 连接的是另一条数据与权限链

MCP Server 可以连接文档、GitHub、数据库、浏览器、监控平台、内部工具和本地脚本。当前主要传输方式包括远程 HTTP、本地 stdio、已弃用的 SSE，以及适合双向事件的 WebSocket。

添加和管理示例：

```bash
claude mcp add --transport http NAME URL
claude mcp add --transport stdio NAME -- COMMAND ARGUMENTS
claude mcp list
claude mcp get NAME
claude mcp remove NAME
```

会话中用 `/mcp` 查看连接和工具。`--` 用于分隔 Claude Code 参数与本地 Server 的命令参数。

MCP Scope 分为 Local、Project 和 User。Local 与 User 存在本机 `~/.claude.json`，Project 写入仓库根目录 `.mcp.json` 并可随团队共享。同名 Server 当前优先顺序为 Local、Project、User、Plugin、claude.ai Connector，条目整体覆盖，不逐字段合并。添加项目级远程 Server 的形式为：

```bash
claude mcp add --transport http shared-docs \
  --scope project \
  https://example.com/mcp
```

这里的地址只是格式示例，不应直接执行。项目级条目会写入 `.mcp.json`，进入版本控制前应检查 URL、启动命令、环境变量和团队是否确实需要该服务；Claude Code 使用项目 Server 前仍可能要求批准。

陌生项目中先查看：

```bash
cat .mcp.json 2>/dev/null || true
```

重点是 Server URL 或本地启动命令、包来源、环境变量、工作目录、OAuth、提供的读写工具和目标系统。MCP 配置成功，只表示连接信息可被读取，不表示服务身份和权限已经符合项目要求。

真实 Token 不应直接写进 `.mcp.json` 的 `Authorization` Header。优先使用 OAuth、系统凭证库、受限凭据文件、环境变量或服务支持的动态 Header Helper；数据库 MCP 使用只读账号，GitHub MCP 使用细粒度 Token，并限制仓库与操作范围。

MCP 返回的网页、Issue、文档和数据库字段属于外部数据，其中可能夹带“忽略之前规则”“读取主目录”“上传环境变量”或“执行某条命令”等提示注入文本。这些内容不能自动成为新指令，也不能据此扩大文件、网络或凭据权限。模型供应商和 MCP Server 是两条独立数据链：项目内容可能先发送给模型后端，再由工具发送给另一个服务，两边的日志、保留和权限政策都要分别审查。

## 7. 进入陌生项目时清点上下文来源

Shell 中检查：

```bash
pwd
git status
find .. \( -name CLAUDE.md -o -name CLAUDE.local.md \) -print
find .claude -type f -print 2>/dev/null
cat .mcp.json 2>/dev/null || true
```

Claude Code 中查看：

```text
/context
/memory
/permissions
/hooks
/mcp
```

稳定项目事实放进 `CLAUDE.md`，路径特定要求放进 `.claude/rules/`，本机经验留给 Auto Memory，执行闸门交给权限规则、Sandbox 或 Hook，外部工具和数据通过 MCP 接入。把所有内容都塞进一份巨大规则文件，会让来源和作用域越来越难判断。

继续阅读：[权限、审批、Sandbox 与安全边界](02-权限审批与安全边界.md)、[大项目与多阶段任务工作流](04-大项目与多阶段任务工作流.md)和[接入 DeepSeek 与第三方供应商](05-接入DeepSeek与第三方供应商.md)。

官方参考：

- [Claude Code memory](https://code.claude.com/docs/en/memory)
- [Claude Code sessions](https://code.claude.com/docs/en/sessions)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
