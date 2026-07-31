# 04 TUI、斜杠命令与交互界面

> 官方产品名：Grok Build  
> 最近核对：2026-07-31

Grok Build 的界面不只是一个输入框。输入 `/` 后出现的菜单同时混合三类入口：由 Agent 后端处理的 Shell Builtin、由 TUI 前端处理的 Pager Builtin，以及声明为 `user-invocable: true` 的 Skill。它们看起来都像 `/command`，来源、稳定性和权限却可能完全不同。内置命令随客户端发布；Skill 可以来自 Grok 捆绑内容、用户目录、当前项目、Plugin 或兼容扫描。遇到陌生命令时，应先看菜单中的来源标签，再用 `/skills`、`/plugins` 和 `grok inspect` 核对，不能仅凭名称判断它是稳定核心功能。

官方在线文档与开源仓库内随包用户指南可能存在几天的同步差异。例如 2026-07-31 的在线 Modes and Commands 已列出 `/share`、`/transcript`、`/tasks` 和 `/queue`，而同日仓库内的 Slash Commands 文件尚未完整出现这些条目。正文会说明这种差异；本机真实能力始终以当前版本的 `/help`、斜杠菜单和 `grok --help` 为准。

## 1. 先学会识别命令来源

在 TUI 中输入 `/` 打开菜单，继续输入字符会模糊筛选。方向键用于选择，`Tab` 或回车用于补全或执行。每个条目通常会显示命令名、用途、参数提示和来源。

相同名称发生冲突时，内置命令优先。用户或项目 Skill 可以使用作用域前缀：

```text
/local:commit
/user:commit
```

因此，一个名为 `compact` 的项目 Skill 不会覆盖内置 `/compact`；需要显式使用 `/local:compact`。升级后先检查：

```bash
grok version
grok --help
grok inspect
```

进入界面后再查看：

```text
/help
/docs
/release-notes
```

`/docs`（别名可能包括 `/howto`、`/guides`）可以浏览内置指南、打开在线文档或按标题寻找具体指南；`/tutorial`（别名 `/tour`、`/onboarding`）提供交互式入门；`/release-notes`（别名 `/changelog`）用于确认当前版本新增或改变了什么。

## 2. 新建、恢复、切换、分叉和删除会话

`/new`（别名 `/clear`）建立新会话并清空当前对话；它不清理 Git 工作区，也不会撤销已经执行的命令。`/home`（别名 `/welcome`）返回欢迎页但保留会话，`/quit`（别名 `/exit`）退出程序。

会话入口包括：

```text
/resume
/sessions
/dashboard
/session-info
/rename NAME
/fork
/rewind
/delete
```

`/resume` 打开持久化到磁盘的会话选择器。在线 Modes and Commands 将 `/sessions` 描述为切换、重命名或关闭活动会话；当前上游随包指南进一步说明 `/sessions` 与 `/agents-dashboard` 是 `/dashboard` 的别名，三者进入当前 Pager 的实时会话与 Agent Dashboard，可以查看顶层会话、回复、派发任务、固定、重命名、停止或附着。它们不是 Shell 层 `grok sessions list/search/delete` 管理的磁盘会话，也不是 `/config-agents` 管理的 Agent 定义。

`/session-info`（别名 `/status`、`/info`）显示认证方式、模型、轮数和上下文占用。`/rename NAME`（别名 `/title`）重命名当前会话。`/fork` 从当前历史分出一个新 Agent，`/rewind`（别名 `/undo`）回到较早轮次并丢弃之后的对话。分叉和回退只处理会话历史及客户端能够维护的快照语义，不能替代 Git 分支，也不能保证数据库、网络请求、容器、服务或已经推送的提交被回滚。

`/delete` 删除当前会话并要求确认；删除其他持久化会话可以进入 `/resume` 后按当前界面提示操作。会话文件可能包含 Prompt、代码、路径和工具结果，清理前应确认是否还需要审计或复现。

## 3. 分享、查找、转录、复制和导出

官方在线文档当前列出：

```text
/share
/find
/transcript
/copy [N]
/export
```

`/share` 把当前会话生成可访问的分享 URL。它可能把会话内容上传到分享服务，使用前必须检查代码、内部路径、客户数据、凭据线索和组织策略；不能把“生成链接”误解为只在本地复制文本。如果本机菜单没有该命令，说明当前安装版本、账号或发布通道尚未提供。

`/find` 搜索当前会话的滚动内容。`/transcript` 使用 `$PAGER` 查看完整会话转录，适合长会话阅读和本地搜索；PAGER 程序、临时文件和终端历史也可能接触会话内容。`/history` 搜索本会话发过的 Prompt，空输入时按上方向键也可快速回忆。

复制最近回复使用：

```text
/copy
/copy 2
/copy out.txt
/copy 2 ~/exports/reply.md
```

Grok 还可能把复制内容备份到 `~/.grok/last-copy.txt`，或由 `GROK_COPY_FILE` 指定位置。SSH 中本地剪贴板通常不可达，写入文件更可靠。`/export` 把整段会话导出到文件或剪贴板；Shell 层还提供 `grok export SESSION_ID [OUTPUT]`。导出物可能包含敏感路径、代码、凭据线索和外部工具结果，公开前必须人工检查。

## 4. 上下文与压缩

长会话需要区分“模型上下文”和“磁盘会话”。`/context` 展示系统提示、消息、推理与开销、工具定义、Skill 清单、MCP 公告和剩余空间估算；`/compact [说明]` 把较长历史压缩为更短表示：

```text
/compact 保留认证实现、失败测试、未完成任务和验证命令
```

当前配置文档给出的默认自动压缩阈值是 85%，可通过以下字段调整：

```toml
[session]
auto_compact_threshold_percent = 85
```

压缩会改变模型接下来看到的历史表示，不等于完整保存。重要需求、决策、验证结果和待办应同时写入项目文档、Issue、PR 或 Git，而不是只依赖会话。

## 5. 模型、推理强度与三种工作模式

模型入口包括：

```text
/model MODEL
/model MODEL high
/effort low|medium|high|xhigh
```

`/model`（别名 `/m`）切换模型；`/effort` 只改变当前模型的推理强度。是否支持某个等级由模型和账号决定，通过 `grok models`、`/model` 和 `grok inspect` 核对。

Plan、Auto 和 Always-approve 解决不同问题：

```text
/plan [说明]
/view-plan
/auto
/always-approve
```

Plan 模式先规划，并限制普通文件编辑，只允许操作会话计划文件，直到用户批准；这道文件编辑门槛与 Ask、Auto、Always-approve 的工具批准模式相互独立。Auto 使用分类器批准被判断为安全的工具，危险动作仍可能询问。Always-approve 跳过工具批准提示，但 Deny、Hook 和 Sandbox 仍可能阻断。三者都不自动缩小文件、网络或系统访问范围。

在 TUI 中，`Shift+Tab` 可以循环 Normal、Plan、可用时的 Auto 和 Always-approve。具体循环顺序和 Auto 是否出现由当前版本与功能开关决定，以界面状态为准。

## 6. 队列、旁问、后台任务和定时循环

当前在线文档列出：

```text
/btw QUESTION
/queue
/tasks
/loop [INTERVAL] PROMPT
```

`/btw` 发送旁问，不中断当前主任务，旁问及回答不进入主轮次。它适合短小确认，不适合承载会改变实施范围的重要需求；关键决定应重新写回主对话或任务文件。

`/queue` 查看当前轮次后等待执行的 Prompt；`/tasks` 汇总后台任务、子 Agent 和定时任务。任务进行中，新输入可能进入队列，空输入框上的单独回车还可能强制发送队首消息。不同输入模式和终端会改变具体按键，应以当前界面提示为准。

`/loop` 按间隔重复执行 Prompt：

```text
/loop 30m 检查部署状态并报告变化
/loop check deploy status every hour
```

当前上游指南说明最小间隔为 60 秒，循环任务通常在 7 天后过期。循环不是生产级监控和自动修复系统；涉及生产环境时应默认只读，并明确报警条件、费用、停止边界和人工门槛。

## 7. 输入方式、渲染模式与命令可用范围

常见界面命令包括：

```text
/multiline
/compact-mode
/vim-mode
/timestamps
/theme
/minimal
/fullscreen
/edit-prompt
```

`/multiline`（别名 `/ml`）切换多行输入。启用后回车插入换行，`Shift+Enter` 或 `Alt+Enter` 发送。`/compact-mode` 减少界面留白；`/timestamps` 切换时间显示；`/theme`（别名 `/t`）选择主题；`/vim-mode` 控制滚动区的 Vim 风格导航，不等于 Prompt 输入器的 Vim 模式。Prompt 输入由 `[ui] simple_mode` 控制，滚动区由 `[ui] vim_mode` 控制。

`/minimal` 和 `/fullscreen`（别名 `/full`）在原生终端滚动模式与标准全屏 TUI 之间切换，只影响当前会话。默认模式由 `[ui] screen_mode` 或 `/settings` 决定。Minimal 模式中的 `/edit-prompt` 会调用 `$VISUAL`、`$EDITOR` 或 `vi` 编辑空草稿；要编辑已有草稿，应使用命令面板中的外部编辑入口，避免把文件引用、图片或其他富输入错误压平。

命令还受渲染模式限制。当前上游把 `/find`、`/jump`、`/timeline`、`/theme`、`/tutorial`、`/workflows` 和 `/dashboard` 列为 Fullscreen-only；`/expand` 与 `/edit-prompt` 仅在 Minimal 可用。`--no-alt-screen` 只是让 Fullscreen 界面留在终端主 Scrollback 中，在命令可用性上仍按 Fullscreen 处理。某个命令在菜单中消失时，先确认当前渲染模式，不要直接判断功能已被版本删除。

不要把开源仓库旧版本中出现过、但当前正式文档和本机菜单都找不到的命令当作稳定功能。命令是否存在应由 `/help` 和斜杠菜单确认，而不是根据旧截图推断。

## 8. 键盘不是附属功能，而是 TUI 的主要控制面

在 TUI 中按 `Ctrl+.` 可以打开当前上下文适用的完整快捷键面板；Windows 或不支持 Kitty Keyboard Protocol 的终端通常使用 `Ctrl+X`。不适用于当前焦点或模式的条目会变暗。`Ctrl+P` 或 `?` 打开命令面板，`F2` 或 `Ctrl+,` 打开设置。

最常用的基础操作如下：

| 按键 | 作用 |
| --- | --- |
| `Enter` | 发送 Prompt |
| `Tab` | 在 Prompt 和 Scrollback 之间切换焦点 |
| `Esc`、`Ctrl+C` | 取消正在运行的一轮 |
| `Esc Esc` | 清空当前输入；输入为空时打开 Rewind |
| `Shift+Tab` | 循环工作模式 |
| `Ctrl+Q`、`Ctrl+D` | 连按两次退出；具体终端可能只支持其中一个 |
| `Ctrl+N` | 连按两次新建会话 |
| `Ctrl+O` | 切换 Always-approve |
| `Ctrl+\` | 打开 Agent Dashboard |

任务正在运行时，`Ctrl+Enter` 或 `Ctrl+I` 可以插入一条 Interject，而不是等本轮完全结束；这与追加到队列不同。`Ctrl+B` 可以把当前运行命令转入后台，`Ctrl+;` 或 `Ctrl+'` 打开 Prompt Queue，`Ctrl+G` 打开 Tasks，`Ctrl+T` 打开 Todo Pane。中途插话、排队和转后台都会改变执行时序，使用后应重新查看当前任务、队列和真实工作区，不能假设 Agent 已经在原步骤安全停止。

输入侧还有几组容易混淆的按键：

| 按键 | 作用 |
| --- | --- |
| `Shift+Enter` | 普通模式插入换行；Multiline 模式中发送，部分终端改用 `Alt+Enter` |
| `Ctrl+M` | Prompt 获得焦点时切换 Multiline；焦点不在 Prompt 时选择模型 |
| `Ctrl+R` | 搜索已发送的 Prompt 历史 |
| `!` | 仅在空 Prompt 上进入 Shell mode |
| `Ctrl+S` | 打开 Sessions |
| `Ctrl+L` | 打开 Extensions；部分集成终端会改作 Interject |

Shell mode 是本地终端操作入口，不是普通自然语言 Prompt。使用 `!` 后仍应按真实 Shell 命令判断影响范围，尤其注意删除、覆盖、Git 写入、远程主机和凭据；不能因为命令从 Grok 界面发出就认为它受 Agent 规划或自动恢复保护。

## 9. Scrollback 可以逐块检查，不必只靠鼠标滚动

先按 `Tab` 把焦点切到 Scrollback。方向键始终可用；`j`、`k`、`h`、`l`、`g`、`G`、`e`、`r`、`y`、`x` 等裸字母按键需要启用 `/vim-mode`，否则它们会把焦点送回 Prompt 并输入字符。

| 按键 | 作用 |
| --- | --- |
| `↓`、`↑` | 选择下一项或上一项 |
| `Shift+→`、`Shift+←` | 下一轮或上一轮 |
| `Shift+J`、`Shift+K` | 下一条或上一条回复 |
| `Page Down`、`Page Up` | 整页滚动 |
| `Ctrl+D`、`Ctrl+U` | 半页向下或向上滚动 |
| `←`、`→` | 折叠或展开当前块 |
| `e`、`Shift+E` | 展开/折叠当前块或全部块，需 Vim Scrollback |
| `Ctrl+E` | 切换全部 Thinking Block |
| `r` | 查看原始 Markdown，需 Vim Scrollback |
| `y`、`Shift+Y` | 复制内容，或复制命令/路径，需 Vim Scrollback |
| `Enter`、`Ctrl+F` | 在全屏 Viewer 中打开所选块 |
| `/` | 搜索 Scrollback，需 Vim Scrollback |
| `x` | 终止选中的后台任务，需 Vim Scrollback |

`x` 是实际任务控制，不只是关闭一块显示；执行前确认选中的确是要停止的后台任务。复制、Raw Markdown 和 Viewer 也可能暴露完整路径、命令与敏感输出，粘贴到外部渠道前仍需检查。

## 10. 文件引用与终端差异决定按键是否真的生效

官方入门示例支持在 Prompt 中使用 `@路径` 明确引用项目文件：

```text
@src/main.rs 解释这个入口的调用链
@tests/test_auth.py 检查这些测试是否覆盖失败分支
```

`@路径` 让本轮明确指向文件，但不会改变当前工作目录、Git 分支、权限或 Sandbox，也不能证明引用内容已经完整读入。路径解析异常时先确认：

```bash
pwd
git rev-parse --show-toplevel
ls -l src/main.rs
```

快捷键不是所有终端都完全一致。官方当前列出的主要差异包括：

- VS Code、Cursor、Windsurf、Zed 等集成终端只用 `Ctrl+D` 退出；Interject 改为 `Ctrl+L`，半页滚动改为 `Shift+D`，`Ctrl+L` 不再打开 Extensions，应使用 `/plugins`，换行通常使用 `Alt+Enter`。
- Apple Terminal 中，`Ctrl+O` 也可能触发 Interject，因此不能只凭这一按键判断是否切换了 Always-approve。
- WezTerm 需要启用 `enable_kitty_keyboard = true`，才能可靠区分 `Ctrl+Enter` 和 `Shift+Enter`。

当快捷键与文档不一致时，优先打开 `Ctrl+.`/`Ctrl+X` 的当前快捷键面板，再运行 `/terminal-setup` 或 `/doctor` 检查终端能力。不要连续试按可能产生副作用的 `Ctrl+O`、`Ctrl+B`、`Ctrl+N` 或 `x`。

## 11. 扩展、设置、诊断、账号和隐私

`/hooks`、`/plugins`、`/marketplace`、`/skills` 和 `/mcps` 会打开扩展管理界面的对应标签或管理面板。面板可以查看和管理启用状态，但不代表陌生项目已经获得信任，也不能替代阅读 Skill、Plugin、Hook、MCP 和脚本的真实内容。

`/settings`（别名 `/config`、`/preferences`、`/prefs`）打开交互设置。运行时修改可能写回 `~/.grok/config.toml`。`/doctor` 检查终端、剪贴板、颜色、输入、通知和 Sandbox，`/doctor fix` 列出可自动修复项；当前上游还保留 `/terminal-setup`、`/terminal-check` 和 `/terminal-info` 等别名。官方在线简表可能只展示 `/terminal-setup`，完整上游指南则使用 `/doctor` 作为主入口。

账号与数据入口包括：

```text
/login
/logout
/usage
/privacy
/feedback
```

`/usage`（别名 `/cost`）查看额度或进入计费管理；消费者订阅和 xAI API 计费不是同一主体。`/privacy` 管理编码数据、保留和训练设置，不会自动改变产品遥测、Session Trace 上传或外部 OpenTelemetry 配置。团队账号中的设置可能由管理员管理。

## 12. 媒体、Claude 导入、Agent 与 Persona

当前文档还列出：

```text
/imagine PROMPT
/imagine-video PROMPT
/import-claude
/config-agents
/personas
```

媒体生成可能消耗独立额度，也可能把文字、附件或截图发送到对应服务，不应直接提交客户数据、内部页面或凭据画面。

`/import-claude` 打开 Claude 设置导入面板，用于迁移 `~/.claude` 中可识别的权限、环境变量、MCP、Hook 和路径配置。它不是 Claude 会话恢复。Shell 层的 `grok import [targets...]` 则用于显式导入 Claude Code 会话，两者必须分开理解。

`/config-agents`（别名 `/agents`）管理 Agent 定义和默认 Agent；`/personas` 管理角色指令。它们与查看实时运行会话的 `/dashboard` 是不同层次，Persona 也不形成权限隔离。

## 13. Skill 命令不会形成永久封闭清单

任何启用且声明 `user-invocable: true` 的 Skill 都可以进入 `/` 菜单，Plugin 中的 Skill 也一样。遇到 `/resume-codex`、`/commit` 或其他不在核心清单中的命令，应进入 `/skills` 查看来源，再阅读实际 `SKILL.md` 和脚本。

因此，“完整命令清单”只能描述某一版本的内置功能；用户环境中的最终菜单还取决于安装版本、功能开关、账号、Plugin、Skill、项目配置和兼容扫描。终端层完整入口见[终端子命令与完整功能索引](09-终端子命令与完整功能索引.md)，扩展与跨客户端边界见[扩展系统、MCP、ACP 与跨客户端兼容](07-扩展系统MCP-ACP与跨客户端兼容.md)。

官方参考：

- [Grok Build Modes and Commands](https://docs.x.ai/build/modes-and-commands)
- [Grok Build Keyboard Shortcuts](https://docs.x.ai/build/keyboard-shortcuts)
- [Grok Build Overview](https://docs.x.ai/build/overview)
- [Grok Build Slash Commands](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/04-slash-commands.md)
- [Grok Build Configuration](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/05-configuration.md)