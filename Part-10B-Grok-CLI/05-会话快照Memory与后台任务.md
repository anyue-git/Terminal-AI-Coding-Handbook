# 05 会话、Memory 与后台任务

> 官方产品名：Grok Build  
> 最近核对：2026-07-31

Grok Build 同时存在磁盘会话、当前模型上下文、跨会话 Memory、Prompt 队列、后台 Agent 和定时任务。它们都可能被用户笼统称为“恢复”“记住”或“继续”，实际保存对象完全不同。理解这些层次，才能判断一次恢复找回了什么，以及哪些现实状态必须重新检查。

## 1. 会话入口分为实时界面与磁盘管理两层

TUI 中常用：

```text
/resume
/sessions
/dashboard
/session-info
/fork
/rewind
/rename NAME
/delete
```

`/resume` 面向已经持久化到磁盘的会话记录。`/sessions` 与 `/dashboard` 面向当前 Pager 中的活动会话：在线 Modes and Commands 将 `/sessions` 描述为切换、重命名或关闭活动会话，上游随包指南则把它与 `/agents-dashboard` 列为 `/dashboard` 的别名。两份说明指向同一个实时会话与 Agent Dashboard，只是强调点不同。

Shell 中常用：

```bash
grok sessions list
grok sessions search KEYWORD
grok sessions delete SESSION_ID

grok --resume SESSION_ID
grok --continue
grok --session-id UUID
grok --resume SESSION_ID --fork-session
```

Shell 层的 `grok sessions list/search/delete` 管理磁盘会话，不等于 TUI 的实时 Dashboard。`--resume` 恢复指定会话；省略 ID 时，当前版本可能恢复最近会话。`--continue` 继续当前目录最近的会话，目录识别错误时可能找到与预期不同的记录。`--session-id` 为新会话指定 UUID，主要用于外部调度和可重复引用，不应拿同一个 ID 同时驱动多个写入进程。`--fork-session` 在恢复时创建新会话 ID，保留原历史作为分叉起点。

会话通常位于：

```text
~/.grok/sessions/
```

也可以通过 `GROK_HOME` 改变整个 Grok 状态目录。不要手工假设目录结构长期不变；列表、搜索和删除优先使用当前 CLI 子命令。

## 2. 恢复会话不等于恢复项目

会话恢复的是 Prompt、模型回复、工具记录以及客户端能够重建的会话状态，不等于恢复 Git、文件系统、数据库、容器、远程主机或系统进程。

恢复后第一件事不是继续输入“接着做”，而是重新核对现实现场：

```bash
hostname
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
grok version
grok inspect
```

如果原会话位于另一台机器、另一个 Worktree 或已经清理的临时目录，对话仍可能被恢复，但路径和文件已经不同。未提交修改也可能被人工、格式化工具或另一个 Agent 改变；外部服务状态更不会随会话回退。

`/fork` 和 `--fork-session` 只建立会话分支，不自动创建 Git 分支。需要并行实现时，应同时建立独立 Worktree，并在每条会话里记录真实目录、分支和 HEAD。

`/rewind`（别名 `/undo`）回退到较早轮次并丢弃之后的对话。它不能撤销已经写入项目外部的数据库、网络、云资源、容器或 Git Push。高影响操作仍要依靠 Git 提交、产品自身回滚、基础设施变更记录和备份。

## 3. Context、Compact、Transcript、Export 和 Share 不是一回事

`/context` 查看当前模型上下文怎样分配；`/compact` 把较长历史总结成更短表示；`/transcript` 使用 `$PAGER` 阅读完整转录；`/export` 和 `grok export` 导出会话；`/share` 则可能生成在线分享链接。

```text
/context
/compact 保留需求、已改文件、失败测试和下一步
/transcript
/export
/share
```

```bash
grok export SESSION_ID
grok export SESSION_ID ~/exports/session.md
```

Compact 不会自动删除磁盘会话，也不保证每个细节都被保留。Transcript 和 Export 主要用于本地阅读或导出，Share 可能把内容上传到分享服务。三类输出都可能包含 Prompt、代码、路径、工具输出和敏感线索，公开前必须检查。

自动压缩阈值可配置：

```toml
[session]
auto_compact_threshold_percent = 85
```

长期任务应把需求、决策、验证命令和未解决问题写进项目文档、Issue 或 PR，而不是只存在会话历史里。

## 4. Memory 是跨会话知识层

Memory 与普通会话历史不同。当前官方入口包括：

```text
/remember NOTE
/memory
/memory on
/memory off
/flush
/dream
```

`/remember` 立即保存一条明确事实，并且当前上游指南将它列为始终可用。例如：

```text
/remember 该项目正式测试命令是 python -m pytest tests -q
```

`/flush` 让模型把当前会话的重要知识总结进 Memory，适合在压缩或退出前主动固化；`/dream` 合并整理已有会话日志和记忆；`/memory`（别名 `/mem`）浏览、管理或开关 Memory。

除 `/remember` 外，Memory 功能通常需要显式启用：

```bash
grok --experimental-memory
```

或：

```bash
export GROK_MEMORY=1
```

配置还可以控制自动保存、文件监听、搜索和首次注入：

```toml
[memory]
enabled = true

[memory.session]
save_on_end = true

[memory.watcher]
enabled = true

[memory.search]
max_results = 6
min_score = 0.35

[memory.initial_injection]
enabled = true
min_score = 0.0
```

`/memory` 还需要可用的 Memory Backend。实际后端、嵌入模型和存储位置通过当前配置与 `grok inspect` 确认。Memory 文件通常位于 `~/.grok/memory/`，Shell 层提供清理入口：

```bash
grok memory clear --workspace
grok memory clear --global
grok memory clear --all
```

清理操作不可仅凭名称判断影响范围，执行前先用 `grok memory clear --help` 核对当前版本的定义和确认机制。

Memory 适合保存稳定偏好、项目约定和长期事实，不适合保存 API Key、Cookie、验证码、私人数据或未经验证的推测。错误记忆会跨会话传播，因此重要内容应能追溯到项目文件、官方文档或真实命令结果；发现错误后应在 Memory 中修正或删除。

## 5. Prompt 队列和任务面板是当前核心功能

当前官方在线文档明确列出：

```text
/queue
/tasks
```

`/queue` 查看当前运行轮次之后等待处理的 Prompt。任务进行中输入的新消息可能进入队列；空输入框上的单独回车还可能强制发送队首消息。使用队列追加需求时，后续消息可能基于当前轮次尚未完成的假设，重要范围变化最好先停止或等待当前步骤结束。

`/tasks` 汇总后台任务、子 Agent 和定时任务。它解决“有哪些后台工作”的查看问题，不等于磁盘会话管理，也不等于 Agent 定义管理。任务结束后仍要回到真实文件、Git diff、测试和外部系统核对结果。

## 6. `/sessions` 与 Agent Dashboard 管理当前 Pager 的运行会话

使用：

```text
/sessions
/dashboard
```

或 Shell：

```bash
grok dashboard
```

在线文档强调 `/sessions` 可以切换、重命名或关闭活动会话；随包指南把 `/sessions` 和 `/agents-dashboard` 作为 `/dashboard` 的别名。这个实时面板显示当前 Pager 进程中的顶层会话或 Agent，可以查看状态、附着、回复、派发、固定、重命名和停止。

它不是 `~/.grok/sessions/` 的磁盘记录浏览器，也不是 `/config-agents` 管理的 Agent 定义。Dashboard 可以通过功能开关关闭，例如当前上游指南提到 `GROK_AGENT_DASHBOARD=0` 或 `[dashboard].enabled = false`；字段仍应以本机帮助和配置为准。

程序退出后，能恢复的是已经持久化的会话记录，不是原进程、外部连接或正在执行的命令。后台 Agent 还可能共享 `~/.grok`、认证、环境变量、Docker Socket、网络、数据库、GPU 和项目外缓存。即使使用不同 Worktree，也可能争用同一服务或显存。

## 7. `/btw` 是旁问，不是第二条主任务

`/btw` 发送一个旁问，不中断主任务，问答不进入主轮次：

```text
/btw 这个失败测试是否与当前修改有关
```

它适合短小确认，不适合修改需求或追加必须执行的工作。如果旁问产生关键决定，应把结论重新写进主对话、任务文档或 Issue，否则主 Agent 后续不一定把它当作约束。

## 8. `/loop` 创建有限期定时任务

`/loop` 按间隔重复运行 Prompt：

```text
/loop 30m 检查部署状态并报告变化
/loop check deploy status every hour
```

当前上游指南支持秒、分钟、小时和天的表达，最小间隔为 60 秒；小于一分钟会提高到最低值。循环任务通常在 7 天后过期，创建后返回任务 ID，可通过调度工具删除。

循环不是持续监控守护进程，也不保证上一次上下文仍然准确。每次运行都应重新读取现实状态。涉及生产系统时，Prompt 应明确只读范围、报警条件、费用和停止边界，不要让定时任务自动部署、删除、转账、修改权限或无限修复。

## 9. 各种“继续”能力的边界

| 能力 | 保存或操作什么 | 不保证什么 |
| --- | --- | --- |
| `/resume`、`--resume` | Grok 磁盘会话 | 当前 Git、进程、数据库和外部服务一致 |
| `--continue` | 当前目录最近会话 | 一定命中用户心里那条会话 |
| `/fork`、`--fork-session` | 从历史创建新会话 | 自动创建 Git 分支或资源隔离 |
| `/rewind` | 回退会话轮次 | 撤销外部副作用 |
| `/compact` | 压缩当前模型上下文 | 永久保存所有细节 |
| `/transcript` | 使用 Pager 阅读完整转录 | 自动脱敏或安全公开 |
| `/export` | 导出会话 | 外部状态和项目环境快照 |
| `/share` | 生成分享入口 | 内容仍只保存在本机 |
| `/remember` | 写入一条长期记忆 | 内容真实、永不过期或适合公开 |
| `/flush` | 总结当前会话到 Memory | 完整无损保存历史 |
| `/dream` | 整理合并 Memory | 自动纠正错误事实 |
| `/sessions`、`/dashboard` | 管理当前进程的活动会话或 Agent | 重启后恢复所有运行状态 |
| `/loop` | 按间隔重新执行 Prompt | 高频实时监控和自动安全处置 |

跨 Codex、Claude Code 或 Cursor 的会话导入不属于普通 `/resume`。`grok import`、兼容扫描器和 `resume-*` Skill 的区别见[扩展系统、MCP、ACP 与跨客户端兼容](07-扩展系统MCP-ACP与跨客户端兼容.md)。

官方参考：

- [Grok Build Modes and Commands](https://docs.x.ai/build/modes-and-commands)
- [Grok Build Slash Commands](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/04-slash-commands.md)
- [Grok CLI Reference](https://docs.x.ai/build/cli/reference)
- [Grok Build Configuration](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/05-configuration.md)