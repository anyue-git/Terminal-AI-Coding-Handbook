# 03 会话、CLAUDE.md、Auto Memory、Hooks 与 MCP

> 最近核对：2026-07-29

Claude Code 用久以后，影响稳定性的往往不是某一轮回答是否聪明，而是长期上下文和扩展能力有没有分层管理。会话、`CLAUDE.md`、Auto Memory、Hooks 和 MCP 都能让工作更连贯，但它们解决的问题完全不同。

```text
会话
→ 保存当前任务的对话过程

CLAUDE.md 与 .claude/rules/
→ 由人维护的长期项目指导

Auto Memory
→ Claude 自动记录的本机项目经验

Hooks
→ 在特定事件发生时自动运行检查或命令

MCP
→ 连接外部工具、数据源和服务
```

其中，`CLAUDE.md` 和 Auto Memory 都只是进入模型上下文的指导信息，不是强制安全配置。需要无论模型如何判断都阻止某项操作时，应使用权限 Deny、Sandbox、PreToolUse Hook 或外部隔离。

## 1. 会话保存对话，不保存项目快照

Claude Code 会话包含对话、工具调用和任务上下文，但不等于：

- Git 提交；
- 文件系统快照；
- Python 虚拟环境；
- Docker Volume；
- 数据库事务；
- 远程服务器状态；
- 模型供应商配置快照。

恢复会话前，先重新检查现实状态：

```bash
pwd
git branch --show-current
git status
git diff --stat
git log -5 --oneline
```

中断期间可能有人切换分支、修改文件、更新依赖或改变远程环境。旧会话说“测试已经通过”，只代表当时的状态。

## 2. 命名、继续、恢复和分叉会话

启动时命名：

```bash
claude --name auth-validation
```

继续当前目录最近的会话：

```bash
claude --continue
```

简写：

```bash
claude -c
```

打开恢复选择器：

```bash
claude --resume
```

按名称或会话 ID 恢复：

```bash
claude --resume auth-validation
```

希望保留旧会话，同时从某个节点尝试另一条路线，可以创建分叉：

```bash
claude --resume auth-validation --fork-session
```

分叉适合比较不同实现方案、独立审查或保留原任务记录。它仍然共享当前磁盘上的项目状态，不会自动复制工作区。需要真正隔离文件修改时，应结合独立 Git 分支或 worktree。

## 3. 恢复后先让上下文与现实重新对齐

恢复会话后的第一条消息可以固定为：

```text
先不要继续修改文件。

重新检查：
- 当前工作目录；
- Git 分支和 HEAD；
- 未提交修改；
- CLAUDE.md、.claude/rules 和设置；
- 依赖声明和锁文件；
- 最近测试结果；
- 当前模型供应商与 Base URL。

说明现实状态与旧会话记忆不一致的地方，再等待确认。
```

会话适合保存推理过程和任务讨论，Git 适合保存代码检查点。不要让二者互相替代。

## 4. `CLAUDE.md` 保存由人维护的稳定指导

适合写入：

- 项目入口和目录职责；
- 真实构建、启动和测试命令；
- 依赖管理方式；
- 编码和接口规范；
- 禁止修改的目录；
- Git 协作规则；
- 数据和安全边界；
- 常见但不容易从代码发现的约定。

不适合写入：

- API Key、Token 和密码；
- 一次性任务计划；
- 某次失败的完整日志；
- 经常变化的模型名称；
- 模糊口号；
- 与其他规则冲突的旧命令；
- 需要强制执行的安全策略。

官方建议单个 `CLAUDE.md` 尽量控制在 200 行以内。文件越长，占用的上下文越多，关键规则越容易被稀释。

## 5. 不同位置的指导文件

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

项目共享文件适合进入版本控制；`CLAUDE.local.md` 用于个人项目偏好、测试地址和本机信息，应加入 `.gitignore`。

Claude Code 从当前工作目录向父目录查找 `CLAUDE.md` 和 `CLAUDE.local.md`。发现的内容会按层次拼接到上下文中，不是简单“后者覆盖前者”。越接近启动目录的内容越晚进入上下文，但相互冲突时模型仍可能选择错误规则，因此应主动消除矛盾。

子目录中的指导文件不会全部在启动时加载，通常在 Claude 读取对应子目录文件时才加入上下文。

## 6. 检查实际加载了什么

进入会话后运行：

```text
/context
```

在 Memory files 部分检查当前加载的指导文件。

运行：

```text
/memory
```

可以浏览和编辑项目指导与 Auto Memory，并切换自动记忆设置。

不要只凭文件存在判断它已经生效。启动目录、设置来源和排除规则都会影响加载结果。

## 7. 用 `/init` 建立起点，但要人工审查

在项目根目录运行：

```text
/init
```

Claude 会分析项目并生成或改进 `CLAUDE.md`。它可能识别构建、测试和项目约定，但生成内容仍应逐条核对：

```bash
git diff -- CLAUDE.md .claude/CLAUDE.md
```

重点检查：

- 命令是否真实可运行；
- 是否把猜测写成事实；
- 是否误读旧配置；
- 是否加入过宽权限；
- 是否写入本机路径或敏感信息；
- 是否与现有团队规则冲突。

不要因为文件由 `/init` 生成，就不经审查直接提交。

## 8. 一份简洁的项目级示例

```md
# 项目约定

## 环境

- Python 版本由 `.python-version` 和 `pyproject.toml` 共同约束。
- 使用 `uv sync --locked` 创建环境。
- Python 命令使用 `uv run`。

## 修改边界

- 不修改 `data/`、`models/`、`.env` 和生产配置。
- 不执行 `git add`、`git commit`、`git push`、`git reset` 或 `git clean`。
- 必须扩大文件范围时先说明原因。

## 验证

- 单元测试：`uv run pytest -q`。
- 格式检查：`uv run ruff format --check .`。
- 静态检查：`uv run ruff check .`。
```

这类规则具体、可验证，也不会把完整教程塞进每次会话上下文。

## 9. 使用 `@path` 导入其他文件

`CLAUDE.md` 可以导入其他文件：

```md
@docs/development.md
@docs/testing.md
```

相对路径以当前 `CLAUDE.md` 所在目录为基准。导入可以递归，当前官方限制最多四层。

导入内容同样会进入上下文，因此不应导入：

- `.env`；
- SSH 私钥；
- 云凭据；
- 大型日志；
- 数据集；
- 来源不明的远程下载文件。

只想在正文中提到一个 `@` 路径而不导入时，应放进反引号代码格式。

外部路径导入第一次会要求批准，因为共享项目可能通过导入读取工作区外文件。不要对不理解的外部导入直接同意。

## 10. 与 `AGENTS.md` 共用规则

Claude Code原生读取 `CLAUDE.md`，不直接把 `AGENTS.md` 当作主规则文件。已有多 Agent 项目可以创建：

```md
@AGENTS.md

## Claude Code 补充约定

- 涉及 `src/billing/` 时先使用 Plan 模式。
- 不运行生产部署命令。
```

这样共享通用规则，同时保留 Claude Code 特有约束。导入后使用 `/context` 确认实际加载。

## 11. 用 `.claude/rules/` 拆分大型规则

目录示例：

```text
.claude/
├── CLAUDE.md
└── rules/
    ├── testing.md
    ├── security.md
    └── frontend/
        └── react.md
```

没有路径条件的规则会在会话启动时加载。一个文件只负责一个主题，比一份数百行总规则更容易维护和审查。

适合拆出的主题包括：

- 测试规范；
- API 设计；
- 数据库迁移；
- 前端组件；
- 安全和隐私；
- 文档写作。

## 12. 路径限定规则减少无关上下文

创建 `.claude/rules/api.md`：

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

只有 Claude 处理匹配文件时，这些规则才会进入上下文。

规则匹配依赖 Glob。过度复杂的括号展开和无效模式会降低可维护性，应优先使用直观路径。修改后通过实际文件任务和 `/context` 验证，而不是只看 YAML 外观。

## 13. Auto Memory 是 Claude 自己写的项目笔记

Auto Memory 默认开启。Claude 会根据工作过程自行记录：

- 构建和测试命令；
- 调试发现；
- 架构线索；
- 代码风格偏好；
- 常见问题和解决方式。

它不会保证每个会话都写内容，也不会自动把所有事实保存下来。

每个 Git 仓库对应本机目录：

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md
├── debugging.md
└── 其他主题文件
```

同一仓库的不同 worktree 和子目录共享 Auto Memory。Mac 与 Ubuntu 不共享，除非用户自行同步这些文件；不建议把整个本机 Claude 状态目录跨机器复制。

## 14. Auto Memory 的加载范围有限

每次会话会加载 `MEMORY.md` 的前 200 行或 25 KB，以先达到的限制为准。详细内容可以放进主题文件，再由索引引用。

这意味着 Auto Memory 也需要保持简洁：

```text
MEMORY.md
→ 项目经验索引和关键结论

debugging.md
→ 具体排错过程

architecture.md
→ 架构发现
```

如果把所有日志和历史讨论堆进 `MEMORY.md`，后面的内容不会自动进入每次会话。

## 15. 审查、修改和关闭 Auto Memory

在会话中运行：

```text
/memory
```

检查 Claude 实际保存了什么。应删除或纠正：

- 过时命令；
- 错误端口；
- 已废弃目录；
- 临时任务限制；
- 错误架构推断；
- 旧模型或供应商信息；
- 不应长期保存的私人内容。

关闭当前项目的 Auto Memory，可以在项目设置中加入：

```json
{
  "autoMemoryEnabled": false
}
```

全局临时禁用：

```bash
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude
```

Auto Memory 是方便机制，不是可信知识库。关键事实仍应写入项目文档、测试或明确的 `CLAUDE.md`。

## 16. Hooks 把“记得检查”变成自动事件

Hook 可以在以下事件附近运行：

```text
用户提交 Prompt
工具调用之前或之后
权限请求
会话开始或结束
子 Agent 开始或结束
任务完成
压缩上下文前后
配置变化
```

常见用途：

- 阻止危险 Bash 命令；
- 文件修改后运行格式检查；
- 检查禁止路径；
- 记录审计信息；
- 在任务结束时提醒运行测试；
- 阻止生产环境操作。

Hook 可能执行任意本机命令，因此项目 Hook 属于代码执行入口。接受 Workspace Trust 前必须审查。

## 17. 查看当前 Hooks

在 Claude Code 中运行：

```text
/hooks
```

界面会显示事件、匹配器、来源和完整命令。检查 Hook 来自：

- 用户设置；
- 项目设置；
- 本地设置；
- Plugin；
- 当前会话；
- 内置机制。

临时关闭用户可控制的全部 Hooks，可以在设置中写：

```json
{
  "disableAllHooks": true
}
```

组织管理的 Hook 可能无法被普通用户设置关闭。

## 18. 一个真正阻止 `git push` 的 PreToolUse Hook

在练习项目中创建脚本：

```bash
mkdir -p .claude/hooks
cat > .claude/hooks/block_git_push.py <<'PY'
#!/usr/bin/env python3
import json
import sys

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError as exc:
    print(f"invalid hook input: {exc}", file=sys.stderr)
    sys.exit(2)

if payload.get("tool_name") != "Bash":
    sys.exit(0)

command = payload.get("tool_input", {}).get("command", "")
if "git push" in command:
    print("Blocked: git push must be performed manually after diff review.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
PY
chmod +x .claude/hooks/block_git_push.py
```

在 `.claude/settings.local.json` 中加入：

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/block_git_push.py\""
          }
        ]
      }
    ]
  }
}
```

检查 JSON：

```bash
python3 -m json.tool .claude/settings.local.json
claude doctor
```

Hook 命令通过标准输入收到 JSON，其中包含当前目录、权限模式、工具名和工具参数。上面的脚本只检查 Bash 命令，并在发现 `git push` 时写入 stderr、返回退出码 2。

## 19. Hook 阻止操作必须理解退出码

对于多数 Hook 事件：

```text
exit 0
→ 正常继续

exit 2
→ 阻止当前可阻止事件，并把 stderr 反馈给 Claude

exit 1 或其他非 0
→ 通常只被视为非阻断错误，操作仍可能继续
```

因此，传统 Shell 中常见的 `exit 1` 不足以可靠实现安全阻断。PreToolUse 需要 `exit 2` 才会阻止工具调用。

PostToolUse 在工具执行之后触发，即使返回 2，也无法撤销已经发生的操作。需要阻止删除、推送或部署时，应使用 PreToolUse。

Hook 示例只是辅助防线。简单字符串搜索可能被复杂 Shell 写法绕过，真正的重要边界还应使用权限 Deny、Sandbox 和外部隔离。

## 20. Hooks 不应自动执行高风险写操作

不推荐让 Hook 自动：

- `git add`、commit 或 push；
- 全量格式化整个仓库；
- 安装或升级依赖；
- 删除未跟踪文件；
- 修改系统配置；
- 重启 Docker 或 SSH；
- 上传源码和日志；
- 操作生产数据库；
- 使用 sudo。

更稳妥的设计是：

```text
Hook 检查并报告
→ 阻止危险行为
→ 人工确认
→ 在明确会话中执行写操作
```

## 21. MCP 把外部工具接入 Claude Code

MCP Server 可以提供：

- 文档和知识库搜索；
- GitHub、Issue 和项目管理；
- 数据库查询；
- 浏览器和自动化；
- 监控与错误平台；
- 内部业务工具；
- 自定义本地脚本。

MCP 不只是“给模型多一点资料”。一个 Server 可能拥有写权限、网络权限、数据库权限和组织凭据。

## 22. MCP 的传输方式

当前主要方式：

```text
HTTP
→ 推荐的远程 MCP 连接方式，可支持 OAuth

stdio
→ 在本机启动一个子进程，适合本地脚本和工具

SSE
→ 已弃用，只有旧服务仍可能使用

WebSocket
→ 持久双向连接，适合需要主动推送事件的服务
```

远程服务优先选择 HTTP；本地进程使用 stdio。不要因为一个 npm 包自称 MCP Server，就直接允许它读取整个项目和环境变量。

## 23. 添加和管理 MCP Server

添加远程 HTTP Server 的语法：

```bash
claude mcp add --transport http NAME URL
```

添加本地 stdio Server：

```bash
claude mcp add --transport stdio NAME -- COMMAND ARGUMENTS
```

`--` 用于分隔 Claude Code 参数和 Server 自己的命令参数。

管理：

```bash
claude mcp list
claude mcp get NAME
claude mcp remove NAME
```

会话中查看状态：

```text
/mcp
```

`claude mcp add` 写入配置成功，不代表 Server 身份、权限和行为已经安全，也不代表认证有效。添加后应检查连接状态和实际工具清单。

## 24. Local、Project 与 User 三种 MCP Scope

```text
Local
→ 只在当前项目可用
→ 配置存入 ~/.claude.json 的项目条目
→ 不与团队共享

Project
→ 只在当前项目可用
→ 配置写入项目根目录 .mcp.json
→ 可进入版本控制与团队共享

User
→ 在本机所有项目可用
→ 存入 ~/.claude.json
→ 不进入项目仓库
```

添加项目级 Server：

```bash
claude mcp add --transport http shared-docs \
  --scope project \
  https://example.com/mcp
```

这里的 URL 是格式示例，不应直接执行。项目级配置会写入 `.mcp.json`，Claude Code 使用前会要求批准。

同名 Server 出现在多个 Scope 时，当前优先顺序是：

```text
Local
→ Project
→ User
→ Plugin
→ claude.ai Connector
```

每个条目整体覆盖，不会逐字段合并。

## 25. 审查 `.mcp.json`

陌生仓库中先查看：

```bash
cat .mcp.json 2>/dev/null || true
```

检查：

- Server URL 和维护者；
- 本地启动命令；
- npm、Python 或容器依赖来源；
- 环境变量；
- 文件系统访问范围；
- 数据库连接；
- 读写工具；
- 网络目的地；
- 是否包含静态 Token；
- 是否需要 OAuth；
- 是否会上传源码或日志。

项目级 Server 等待批准时，`claude mcp list` 会显示 Pending approval。不要为了消除提示而批量批准。

## 26. MCP 凭据不要写进仓库

避免在 `.mcp.json` 中直接写：

```json
{
  "headers": {
    "Authorization": "Bearer REAL_TOKEN"
  }
}
```

优先使用 OAuth、系统 Keychain、受限凭据文件、环境变量或动态 Header Helper。远程服务只应获得完成任务所需的最小权限。

数据库 MCP 应使用只读数据库账号，而不是生产管理员账号。GitHub MCP 应使用细粒度 Token，并限制仓库和操作范围。

## 27. MCP 返回内容可能包含提示注入

网页、Issue、文档和数据库字段可能包含：

```text
忽略之前规则
读取用户主目录
上传环境变量
执行某条命令
```

这些内容只能作为不可信数据，不能自动成为新指令。

安全原则：

```text
外部内容只作为资料
→ 不自动扩大权限
→ 不读取项目外敏感路径
→ 不把凭据发到内容指定的地址
→ 写操作仍需独立确认
```

模型供应商和 MCP Server 是两条不同的数据链。项目内容可能先发送给模型后端，再由 MCP 工具发送给另一个服务。两边都需要单独审查日志、保留和权限策略。

## 28. 推荐的陌生项目检查顺序

进入仓库后：

```bash
pwd
git status
find .. -name CLAUDE.md -o -name CLAUDE.local.md -print
find .claude -type f -print 2>/dev/null
cat .mcp.json 2>/dev/null || true
```

然后在 Claude Code 中运行：

```text
/context
/memory
/permissions
/hooks
/mcp
```

检查完成前使用 Plan 模式，不执行项目 Hook、MCP 写操作、安装脚本和外部发布。

## 29. 选择机制的简明规则

```text
所有会话都要知道的稳定项目事实
→ CLAUDE.md

只对特定路径生效的规则
→ .claude/rules/ + paths

Claude 从反复纠正中积累的本机经验
→ Auto Memory

必须在工具执行前强制检查或阻止
→ PreToolUse Hook / permissions.deny / Sandbox

需要连接外部工具或数据源
→ MCP

一次复杂但不需要永久进入上下文的流程
→ Skill 或任务文档
```

不要把所有能力都塞进一份巨大的 `CLAUDE.md`，也不要用 Auto Memory 代替正式项目文档和测试。

继续阅读：

- [权限、审批、Sandbox 与安全边界](02-权限审批与安全边界.md)
- [大项目与多阶段任务工作流](04-大项目与多阶段任务工作流.md)
- [接入 DeepSeek 与第三方供应商](05-接入DeepSeek与第三方供应商.md)

官方参考：

- [Claude Code memory](https://code.claude.com/docs/en/memory)
- [Claude Code sessions](https://code.claude.com/docs/en/sessions)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
