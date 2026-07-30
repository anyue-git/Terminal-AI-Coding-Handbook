# 03 Headless、Worktree 与扩展系统

> 官方产品名：Grok Build  
> 最近核对：2026-07-29

Grok Build 除了全屏 TUI，还可以在脚本和 CI 中以 Headless 方式运行，在独立 Git Worktree 中执行任务，并通过 Skills、Plugins、Agents、Hooks、MCP、LSP 和 ACP 接入外部能力。三者解决不同问题：Headless 负责无交互执行，Worktree 隔离仓库目录，扩展系统增加工具和上下文。把它们同时打开并不会自动提高可靠性；任务拆分、测试、Git diff 和人工复核的共同方法仍见[复杂任务拆分与独立复核](../Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)。

## 1. Headless 任务要固定现场、范围和停止条件

最小命令是：

```bash
grok -p "只读解释当前项目架构"
```

当前版本也可能提供较长入口：

```bash
grok --single "只读解释当前项目架构"
```

它不会进入 TUI，而是执行一次任务并把结果写到标准输出，适合脚本、CI、远程无交互终端和固定格式报告。运行前先固定目录和 Git 现场：

```bash
PROJECT="$HOME/Projects/my-project"
cd "$PROJECT"

hostname
pwd
git branch --show-current
git rev-parse HEAD
git status --short
grok version
grok inspect
```

也可以使用当前版本支持的 `--cwd`：

```bash
grok \
  --cwd "$HOME/Projects/my-project" \
  -p "只读检查当前项目"
```

失败日志若没有机器、目录、分支、HEAD 与 Grok 版本，通常只能说明“某次任务失败”，无法重建运行现场。

无交互任务也没有人持续处理确认弹窗，Prompt 需要明确目标、允许文件、验证命令和停止位置：

```text
目标：修复 CSV 解析器忽略尾部空字段的问题。
允许修改：src/csv_parser.py、tests/test_csv_parser.py。
验证：python -m pytest tests/test_csv_parser.py -q。
不修改依赖、锁文件、CI 和其他目录，不执行 Git 写操作。

如果需要扩大文件范围、安装依赖，或测试失败原因与目标问题无关，停止并说明。
最终报告修改文件、执行命令、退出状态和未验证内容。
```

轮数可以在命令层限制：

```bash
grok \
  -p "读取 task.md 并执行任务" \
  --max-turns 12
```

外层调度还应控制总超时、重试和用量。达到轮数后退出，比在错误方向上无限重试更容易排查。

当前版本提供若干按需关闭能力的选项：

```bash
grok --no-plan
grok --no-subagents
grok --no-memory
grok --disable-web-search
```

每个选项只关闭对应能力。`--disable-web-search` 不会阻止 Shell、包管理器、Git、MCP、Plugin 或 Hook 联网。工具集合与拒绝项还可以通过当前版本支持的入口缩小：

```bash
grok --tools TOOL_LIST
grok --disallowed-tools TOOL_LIST
grok --allow RULE --deny RULE
```

具体工具名和规则格式以 `grok --help` 为准。Headless 没有人持续阅读审批弹窗，默认只启用任务需要的工具，比为了避免缺少能力而一次开放全部 Shell、网络和扩展更容易审计；这些参数也不能替代 Sandbox。

在自动化中使用 `--always-approve` 或 `--yolo` 会明显扩大影响范围，不能把“没有弹窗”理解成“没有风险”。脚本环境更适合关闭自动更新，由独立维护流程升级并重新验证命令：

```bash
grok --no-auto-update -p "TASK"
```

对应配置在当前版本中可能写为：

```toml
[cli]
auto_update = false
```

## 2. 输出格式与只读审计要服务下游证据

普通文本适合人读：

```bash
grok -p "列出项目入口和测试命令"
```

需要单个结构化结果时使用 JSON：

```bash
grok \
  -p "只读检查当前项目" \
  --output-format json
```

长任务或事件流可以输出 JSONL：

```bash
grok \
  -p "只读检查当前项目" \
  --output-format streaming-json \
  > grok-events.jsonl
```

当前常见值为 `plain`、`json` 和 `streaming-json`，实际名称以本机帮助为准。`streaming-json` 每行是独立事件，不能把整个文件当成单个 JSON 对象。下面的脚本只验证每行语法：

```bash
python - <<'PY'
import json
from pathlib import Path

for number, line in enumerate(Path("grok-events.jsonl").read_text().splitlines(), 1):
    try:
        json.loads(line)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"line {number}: {exc}")
print("valid json lines")
PY
```

真实下游解析器还应忽略不认识的新字段，并显式处理错误事件，不能因为事件结构随版本增加字段就让整条流水线崩溃。结构化输出只是格式，不是执行证明；事件中仍可能出现 Prompt、路径、代码和外部工具结果，保存和上传时要按真实内容判断。

下面的只读审计脚本把输出放在项目外的临时目录，记录前后状态，并在已跟踪文件发生变化时失败：

```bash
cat > run-grok-audit.sh <<'SH'
#!/bin/sh
set -eu

project=${1:?usage: run-grok-audit.sh PROJECT_PATH}
output=${2:-/tmp/grok-audit-output}

cd "$project"
mkdir -p "$output"

{
  hostname
  pwd
  git branch --show-current
  git rev-parse HEAD
  grok version
} > "$output/environment.txt"

git status --short > "$output/status-before.txt"

set +e
grok \
  --no-auto-update \
  --no-memory \
  --disable-web-search \
  --max-turns 8 \
  -p "只读审查当前项目。输出入口、测试方式、明显风险和待确认项。" \
  --output-format streaming-json \
  > "$output/events.jsonl" \
  2> "$output/stderr.txt"
status=$?
set -e

printf '%s\n' "$status" > "$output/exit-status.txt"
git status --short > "$output/status-after.txt"

[ "$status" -eq 0 ] || exit "$status"
cmp -s "$output/status-before.txt" "$output/status-after.txt" || exit 2
git diff --exit-code > "$output/diff.txt" || exit 3

printf 'Audit completed; inspect %s\n' "$output"
SH

chmod +x run-grok-audit.sh
./run-grok-audit.sh "$PWD"
```

这组检查能够证明 Git 状态和已跟踪 diff 没有变化，却无法观察数据库写入、网络请求、项目外文件或其他外部副作用；审计边界仍取决于实际启用的工具。

Headless 任务也可以继续或分叉本地会话：

```bash
grok --continue -p "重新检查现实状态后继续下一阶段"
grok --resume SESSION_ID -p "重新检查后继续"
grok \
  --resume SESSION_ID \
  --fork-session \
  -p "只读评估另一种方案"
```

会话保存上下文，不保存文件系统快照。恢复后重新确认目录、分支、HEAD 和工作区。

## 3. Worktree 隔离仓库目录，不隔离外部资源

Grok Build 当前提供 Worktree 入口：

```bash
grok --worktree
grok -w
grok --worktree parser-fix
grok --worktree parser-fix --ref main
```

运行后用 Shell 核对真实目录和分支：

```bash
git worktree list
git status
git branch --show-current
git rev-parse HEAD
```

管理命令包括：

```bash
grok worktree list
grok worktree show NAME
grok worktree rm NAME
grok worktree gc
grok worktree --help
```

Worktree 只隔离仓库目录与分支。`~/.grok`、认证、环境变量、SSH、Docker Socket、网络、数据库、系统服务、GPU、显存、缓存和记忆仍然可能共享。多个 Worktree 同时训练会争用同一块 GPU，多个 Agent 也可能通过同一数据库或外部服务相互影响。

多 CLI 协作时，可以让不同实现各占一个 Worktree，主工作区只负责比较和整合：

```bash
git diff main...grok-implementation
git diff main...codex-implementation
```

每个分支分别运行测试，整合后再在集成分支验证。移除 Worktree 前确认其中没有未提交修改、未推送提交或仍在运行的进程。

## 4. 扩展系统增加新的执行面，最终状态仍由 `inspect` 核对

Grok Skill 可能包含 `SKILL.md`、scripts、references 和 assets，并不只是一个 Prompt。Plugin 可以组合 Skills、Agents、Hooks、MCP、LSP 与其他资源；Marketplace 解决发现问题，不负责替用户审计脚本和权限。

项目 Hook 常位于 `.grok/hooks/`。它可以在命令前阻断操作、在修改后检查文件或在结束时运行测试，也可能形成递归、全仓格式化、敏感日志、自动联网或自动提交。用于阻断的 Hook 应先在练习目录验证，确认拒绝后目标命令确实没有执行。

MCP 把文档、数据库、浏览器、GitHub 或内部服务接入会话。需要检查传输地址、读写工具、认证方式、日志和数据保留；外部返回内容属于不可信输入，不能因为它要求读取 HOME 或上传环境变量就自动扩大权限。

项目可通过 `.grok/lsp.json` 启动语言服务。LSP 会增加进程并扫描项目，安装来源、下载行为、工作目录、排除范围和日志位置都应可解释。ACP 的入口为：

```bash
grok agent stdio
```

编辑器或其他客户端会通过标准输入输出驱动 Grok。接入后，工作目录、自动附加文件、权限模式、Sandbox、额外工具和双方日志都可能由宿主客户端改变；换成图形界面不会自然缩小权限。

进入陌生项目或任务结束后，使用 `inspect` 核对最终规则与扩展：

```bash
pwd
git status
grok inspect
grok inspect --json > grok-inspect.json
```

再读取真实工作区：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

一份可追踪的 Headless 结果应关联机器、目录、Grok 版本、模型与推理强度、会话、权限与 Sandbox、关键扩展、命令退出状态、测试和未验证内容。自动化的目标是让失败能够定位、任务能够停止、结果能够复核，而不是让模型在无人监督下持续运行。

延伸阅读：[权限、Sandbox 与项目配置](02-权限Sandbox与项目配置.md)、[复杂任务拆分与独立复核](../Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)和[三个 AI CLI 怎么选](../Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)。

官方参考：

- [Grok CLI reference](https://docs.x.ai/build/cli/reference)
- [Grok settings](https://docs.x.ai/build/settings)
- [Grok worktrees](https://docs.x.ai/build/features/worktrees)
- [Grok Build 官方开源仓库](https://github.com/xai-org/grok-build)
