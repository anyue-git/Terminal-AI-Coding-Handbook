# 06 Claude Code、Codex CLI 与 Grok CLI 怎么选

> 最近核对：2026-07-28
>
> 三个工具更新都很快。本文讲的是选择方法和协作思路；具体参数请同时查看本机 `--help` 和官方文档。

## 1. 别急着给三个工具排总榜

Claude Code、Codex CLI 和 Grok CLI 都能读代码、改文件、运行命令、执行测试和查看 Git 差异。它们的模型、界面和扩展能力不同，但对新手来说，真正影响使用体验的往往是下面几件事：

- 它会不会在执行命令前询问你；
- 它能访问哪些文件和网络；
- 能不能先只读分析，再开始修改；
- 会话中断后能不能继续；
- 能不能放进脚本或自动化流程；
- 多个任务能不能分开放，避免互相踩脚。

所以，“哪个最强”通常不是一个很好回答的问题。更实用的问法是：

> 这次任务要改多少文件、风险有多高、是否需要自动化，最后由谁复核？

就像选螺丝刀，不能只看哪把最长。要是螺丝很小，拿一把两米长的也未必显得专业。

## 2. 先看懂三个容易混淆的词

### 权限审批

权限审批决定：**某次操作要不要先问你。**

例如，Agent 想运行测试、修改文件或访问网络时，工具可能弹出确认，也可能按照既有规则自动允许。

### Sandbox

Sandbox 可以理解为“活动范围”。它决定：**已经获准的操作到底能碰到哪里。**

审批和 Sandbox 不是一回事。你可以批准一条命令，但 Sandbox 仍可能阻止它写到项目目录之外；反过来，即使 Sandbox 范围很大，工具也可能每次都先询问。

### Worktree

Git Worktree 是同一个仓库的另一个工作目录。它适合让两个任务分开修改代码。

可以把它理解成给两个 Agent 分了两个房间，但没有顺手给每个房间配独立保险柜。Worktree 能隔离 Git 工作目录，不能自动隔离：

- 家目录；
- 环境变量；
- SSH 密钥；
- Docker Socket；
- 网络；
- 系统服务；
- 数据集和共享缓存。

## 3. 三个工具放在一起看

| 你关心的事情 | Claude Code | Codex CLI | Grok CLI / Grok Build |
|---|---|---|---|
| 基础命令 | `claude` | `codex` | `grok` |
| 非交互使用 | 支持打印模式 | 支持 `codex exec` | 支持 Headless 运行 |
| 会话继续 | 支持继续和恢复会话 | 支持会话恢复 | 支持继续、恢复及会话管理 |
| 权限控制 | Permission Mode、Allow/Deny 等 | 审批策略与 Sandbox 分开配置 | Ask、Auto、Always-approve，并与 Sandbox 分开 |
| 项目规则 | 常见入口为 `CLAUDE.md` 和 Settings | 常见入口为 `AGENTS.md` 与配置文件 | 支持项目规则、Memory 等配置 |
| 扩展 | Hooks、MCP、子 Agent 等 | MCP、Skills、Hooks、Subagents 等 | MCP、Skills、Hooks、Subagents 等 |
| Worktree | 可配合 Git Worktree | 可用于 Worktree 工作流 | 提供较明确的 Worktree 会话支持 |
| 比较适合的新手起点 | 默认审批或 Plan | 受限 Sandbox，加按需审批 | Ask；复杂任务先 Plan |

这张表只能帮助你找方向，不能代替版本核对。不同版本、账号和平台可能不完全一致。

在自己电脑上先看：

```bash
claude --version
claude --help

codex --version
codex --help

grok version
grok --help
```

教程可能会旧，`--help` 也可能有版本差异，但它至少是在回答“你现在装的这一个工具会什么”。

## 4. 三个工具分别适合什么场景

### Claude Code：适合连续理解和推进大项目

Claude Code 常见的优势场景是：

- 需要连续阅读较大的代码库；
- 一个任务要分多个阶段推进；
- 项目已经维护 `CLAUDE.md` 或分层规则；
- 需要使用 Hooks、MCP 或子 Agent；
- 希望先在 Plan 中调查，再开始动手。

基础启动：

```bash
claude
```

只做非交互分析时，可以使用当前版本提供的打印模式。常见形式是：

```bash
claude -p "分析测试入口，不要修改文件"
```

会话继续、恢复和权限模式的参数可能调整，使用前查看：

```bash
claude --help
```

Claude Code 的危险点并不神秘：额外目录会扩大访问范围，Hooks 可以执行本地代码，MCP 可能连接外部工具，而跳过权限确认的选项会让人失去最后一道刹车。

### Codex CLI：适合强调隔离和自动化的流程

Codex CLI 比较适合：

- 明确区分 Sandbox 和人工审批；
- 交互使用与 `codex exec` 脚本化结合；
- 需要结构化输出；
- 希望把检查任务放进 CI 或脚本；
- 项目已经使用 `AGENTS.md` 或 Codex 配置。

基础启动：

```bash
codex
```

只读审查可以从类似下面的任务开始：

```bash
codex exec "检查当前 Git 差异是否存在明显回归，不要修改文件"
```

Codex 的审批策略和 Sandbox 是两个不同旋钮。一个控制“问不问”，另一个控制“能去哪”。不要只看到没有弹窗，就以为操作一定安全。

具体策略名、Profile 和临时配置方式请以当前文档和本机帮助为准：

```bash
codex --help
```

### Grok CLI：适合明确切换权限和使用 Worktree

Grok Build 的终端命令是：

```bash
grok
```

它比较适合：

- 需要在 Ask、Auto、Always-approve 之间切换；
- 希望把 Plan 与执行权限分开理解；
- 经常使用 Worktree 做并行试验；
- 需要 Headless 运行；
- 需要会话导入、导出或分叉；
- 使用 Skills、Hooks、MCP、Memory 或 Subagents。

这里最容易误解的是：

> Always-approve 只是减少询问，不等于没有访问边界，也不等于操作自动变安全。

Worktree 会话、权限规则和 Headless 参数变化较快，实际使用前检查：

```bash
grok --help
```

## 5. 新手到底该选哪个

没有必要把三个工具同时设为主力。先选一个最熟悉的负责修改，另一个只负责复核，通常更省心。

### 任务很大，需要连续理解

可以先考虑 Claude Code，或者选择团队已经维护完整项目规则的工具。这里的重点不是某个模型永远更聪明，而是长会话和项目规则是否顺手。

### 想把文件和命令范围管得更清楚

可以先考虑 Codex CLI，并认真检查 Sandbox 与审批策略的组合。

### 经常做并行实验

可以考虑 Grok CLI 的 Worktree 工作流，也可以让其他工具配合 Git Worktree 使用。

无论选哪个，都不要让多个 Agent 同时编辑同一个未提交工作区。三个 Agent 同时改一份代码，通常不会产生“三倍效率”，更可能产生一份谁也说不清来历的 `git diff`。

### 需要放进脚本

不要只看“支持非交互”。还要确认：

- 输出格式是否稳定；
- 失败时退出状态是否可靠；
- 能否限制执行轮次；
- 是否会访问网络；
- 日志保存在哪里；
- 重试会不会重复写入；
- 是否可能修改项目目录之外。

## 6. 最实用的双 Agent 分工

比较稳妥的做法是：一个 Agent 修改，另一个 Agent 只读审查。

实施者只拿到明确范围：

```text
你负责实现，不负责提交。

先检查项目规则、Git 状态和相关测试。
只允许修改：
- FILE_A
- FILE_B

禁止：
- 修改其他文件；
- git add、commit、push；
- 安装依赖；
- 访问外部服务；
- 删除数据或生成物。

完成后运行 TEST_COMMAND，并汇报：
1. 修改了哪些文件；
2. 执行了哪些命令；
3. 测试结果；
4. 尚未验证的部分；
5. 已知风险。
```

复核者不要先看实施者的“自我表扬”。只给它原始需求、当前 diff、测试结果和必要文件：

```text
你只负责独立审查，不要修改文件。

根据原始需求、当前 diff 和测试结果检查：
1. 是否满足需求；
2. 是否修改了范围外内容；
3. 是否遗漏边界条件、错误处理或安全问题；
4. 测试是否足够；
5. 是否存在更小的修复方案。

把结论分成：
- 已确认问题；
- 可能问题；
- 无法验证；
- 建议补充的测试。
```

这样做的原因很简单：实施者已经沿着自己的思路走了一遍，容易对同一套假设产生“熟悉感”。换一个会话或工具，至少能多一双没被带节奏的眼睛。

## 7. 多个 Agent 并行时怎么放

错误做法是让 Claude Code、Codex CLI 和 Grok CLI 同时编辑同一个目录。

需要并行时，使用不同分支或不同 Worktree，例如：

```text
~/Projects/my-project/
→ 主工作区，只做人工整合

~/Projects/my-project-feature-a/
→ Agent A 实现

~/Projects/my-project-review/
→ Agent B 只读复核
```

开始前分别检查：

```bash
pwd
git status
git branch --show-current
```

Worktree 解决的是代码互相覆盖的问题，不是完整的安全隔离。涉及 SSH 密钥、Docker Socket、系统服务和网络时，仍要单独控制权限。

## 8. Mac 与 Ubuntu GPU 怎么分工

对本手册的典型环境，可以把 Mac 作为主编辑端，把 Ubuntu 游戏本作为运行端。

Mac 适合：

- 阅读和修改源码；
- 管理 Git 分支；
- 运行不依赖 CUDA 的测试；
- 检查 diff；
- 准备训练配置。

Ubuntu 适合：

- 验证 CUDA 和 PyTorch 环境；
- 运行 GPU 测试；
- 在 tmux 中启动训练；
- 保存日志、指标和 checkpoint；
- 分析运行期错误。

不要默认允许 Ubuntu 上的 Agent 修改 SSH、防火墙、NVIDIA 驱动，或者清空数据集和 checkpoint。这些操作影响的是整台机器，不只是当前项目。

完整流程见：

- [Mac 到 Ubuntu GPU 的端到端案例](07-Mac到Ubuntu-GPU端到端案例.md)

## 9. 最后仍然要由人检查

Agent 说“测试通过”时，先别急着鼓掌。至少看一下它到底运行了什么。

提交前运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

然后确认：

- 修改文件是否在允许范围内；
- 是否新增依赖或锁文件；
- 是否出现大文件；
- 是否改测试来绕过失败；
- 是否包含 Token、私钥或个人路径；
- 是否有未经解释的删除；
- 测试结果是否来自当前这份代码。

适合新手的组合不是“三个工具全部自动批准”，而是：

> 一个工具负责修改，一个工具负责只读复核；Git 记录差异，测试提供证据，最后由人决定是否提交。

## 版本核对入口

### Claude Code

```bash
claude --version
claude --help
```

- [Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage)
- [Claude Code security](https://docs.anthropic.com/en/docs/claude-code/security)

### Codex CLI

```bash
codex --version
codex --help
```

- [Codex CLI reference](https://developers.openai.com/codex/cli/reference)
- [Codex configuration reference](https://developers.openai.com/codex/config-reference)
- [Codex security](https://developers.openai.com/codex/security)

### Grok CLI / Grok Build

```bash
grok version
grok --help
```

- [Grok CLI reference](https://docs.x.ai/build/cli/reference)
- [Grok permissions](https://docs.x.ai/build/features/permissions)
