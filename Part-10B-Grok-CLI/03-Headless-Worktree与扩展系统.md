# 03 Headless、Worktree 与扩展系统

> 官方产品名：Grok Build
>
> 最近核对：2026-07-29

Grok Build 不只提供全屏 TUI。它还能以 Headless 方式运行脚本和 CI，在独立 Git Worktree 中执行任务，并通过 Skills、Plugins、Agents、Hooks、MCP、LSP 与 ACP 接入更多能力。

这些能力可以组合，但每增加一层，都要重新回答：

```text
谁在执行
在哪个目录执行
使用哪个会话和模型
能读取与修改什么
能访问哪些外部服务
最终结果怎样验证
```

## 1. Headless 是什么

最小 Headless 命令：

```bash
grok -p "只读解释当前项目架构"
```

当前长参数可能是：

```bash
grok --single "只读解释当前项目架构"
```

它不会进入全屏 TUI，而是执行单次任务并把结果写到标准输出。

适合：

- Shell 脚本；
- CI；
- 批量只读检查；
- 固定格式报告；
- 远程无交互环境；
- 编辑器或其他 Agent 编排系统。

不适合直接无人复核执行：

- 生产数据库修改；
- 不可逆删除；
- 系统权限和网络配置；
- 模糊的大规模重构；
- 自动强制推送；
- 没有测试和回滚方案的依赖升级。

## 2. 固定工作目录

不要依赖脚本启动位置：

```bash
PROJECT="$HOME/Projects/my-project"
cd "$PROJECT"

pwd
git branch --show-current
git status --short
grok -p "只读检查当前项目"
```

也可以显式指定：

```bash
grok \
  --cwd "$HOME/Projects/my-project" \
  -p "只读检查当前项目"
```

自动化日志至少记录：

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

否则失败后可能无法判断它在本机还是远程、在哪个分支、加载了什么扩展。

## 3. Headless Prompt 要写成执行工单

不要只写：

```text
帮我修一下。
```

完整任务示例：

```text
目标：修复 CSV 解析器忽略尾部空字段的问题。

允许读取：src/csv_parser.py、tests/test_csv_parser.py、pyproject.toml。
允许修改：src/csv_parser.py、tests/test_csv_parser.py。
禁止修改：依赖、锁文件、CI、配置和其他目录。

验证：python -m pytest tests/test_csv_parser.py -q。
网络：不允许。
Git：不要执行 add、commit、push、reset、clean 或 rebase。

停止条件：
- 需要扩大文件范围；
- 需要安装依赖；
- 现有行为与任务描述冲突；
- 测试失败原因不是本次修改；
- 达到最大轮数仍无法通过。

最终输出：修改文件、执行命令、测试退出状态、未验证内容和风险。
```

## 4. 输出格式

普通文本：

```bash
grok -p "列出项目入口和测试命令"
```

JSON：

```bash
grok \
  -p "只读检查当前项目" \
  --output-format json
```

流式 JSON：

```bash
grok \
  -p "只读检查当前项目" \
  --output-format streaming-json
```

当前支持值通常包括：

```text
plain
json
streaming-json
```

使用前检查：

```bash
grok --help
```

结构化输出方便程序读取，但不能证明测试真的执行、没有越界修改或命令没有副作用。

## 5. JSON 与流式 JSON 的处理方式不同

普通 JSON 可能在任务结束后输出一个完整对象；Streaming JSON 会逐行发送事件或增量数据。

保存流式结果：

```bash
grok \
  -p "只读检查当前项目" \
  --output-format streaming-json \
  > grok-events.jsonl
```

验证每行 JSON：

```bash
python - <<'PY'
import json
from pathlib import Path

for line_number, line in enumerate(
    Path("grok-events.jsonl").read_text().splitlines(),
    start=1,
):
    json.loads(line)
print("valid json lines")
PY
```

不要把 JSONL 当成一个大型 JSON 对象。事件字段可能随版本变化，解析器应忽略未知字段并处理错误事件。

日志中可能包含 Prompt、路径、代码片段和外部工具结果，不应默认作为公共 CI Artifact 上传。

## 6. 限制最大轮数

Headless 自动化应限制 Agent 能连续推进多少轮：

```bash
grok \
  -p "读取 task.md 并执行任务" \
  --max-turns 12
```

数字应根据任务复杂度设置，不是越大越好。达到上限时应停止并报告，而不是外层无限重新运行。

还应在调度系统中设置：

- 最大执行时间；
- 最大重试次数；
- 最大用量或费用；
- 允许文件范围；
- 测试失败停止条件；
- 人工介入点。

## 7. 禁用不需要的能力

根据任务，可以显式关闭：

```bash
grok --no-plan
grok --no-subagents
grok --no-memory
grok --disable-web-search
```

这些选项分别减少 Plan、子 Agent、记忆或 Web Search 的使用。但：

```text
--disable-web-search
≠ 禁止所有网络
```

Shell、包管理器、Git、MCP、Plugin 和 Hook 仍可能联网。真正的网络限制还需要 Sandbox 或外部隔离。

## 8. 工具白名单与拒绝列表

当前 CLI 支持指定允许工具集合和拒绝工具：

```bash
grok --tools TOOL_LIST
grok --disallowed-tools TOOL_LIST
```

以及权限规则：

```bash
grok --allow RULE --deny RULE
```

具体格式以当前帮助为准。

Headless 中没有人实时阅读弹窗，因此应遵循：

```text
默认较少工具
→ 按任务添加必需能力
→ 明确 Deny 高风险操作
→ 仍使用 Sandbox
```

不要为了避免工具缺失错误直接启用全部 Shell、网络和扩展。

## 9. Always-approve 在 Headless 中风险更高

自动批准入口：

```bash
grok --always-approve -p "TASK"
```

或别名：

```bash
grok --yolo -p "TASK"
```

Headless 环境无人逐条观察命令，风险高于交互 TUI。只有在以下条件同时成立时才考虑：

- 独立临时工作区；
- 有限 Sandbox；
- 无真实凭据；
- 无生产数据；
- 固定工具和网络范围；
- 有退出状态、测试和 diff 检查；
- 环境可整体销毁重建。

普通个人电脑和唯一 GPU 主机不满足这些条件。

## 10. 自动更新应在脚本中关闭

Headless、CI 和 ACP 需要可复现版本。运行时可以使用：

```bash
grok --no-auto-update -p "TASK"
```

或者用户配置：

```toml
[cli]
auto_update = false
```

然后由明确的维护流程升级并重新验证参数与输出格式。

## 11. 一个完整的只读审计脚本

在独立练习仓库中创建：

```bash
cat > run-grok-audit.sh <<'SH'
#!/bin/sh
set -eu

project=${1:?usage: run-grok-audit.sh PROJECT_PATH}
output=${2:-/tmp/grok-audit-output}

cd "$project"
mkdir -p "$output"

{
  printf 'hostname: '
  hostname
  printf 'pwd: '
  pwd
  printf 'branch: '
  git branch --show-current
  printf 'head: '
  git rev-parse HEAD
  printf 'grok: '
  grok version
} > "$output/environment.txt"

git status --short > "$output/status-before.txt"

set +e
grok \
  --no-auto-update \
  --no-memory \
  --disable-web-search \
  --max-turns 8 \
  -p "只读审查当前项目。不要修改文件、安装依赖、联网或执行 Git 写操作。输出入口、测试方式、明显风险和人工待确认项。" \
  --output-format streaming-json \
  > "$output/events.jsonl" \
  2> "$output/stderr.txt"
status=$?
set -e

printf '%s\n' "$status" > "$output/exit-status.txt"
git status --short > "$output/status-after.txt"

if [ "$status" -ne 0 ]; then
  printf 'Grok failed with status %s\n' "$status" >&2
  exit "$status"
fi

if ! cmp -s "$output/status-before.txt" "$output/status-after.txt"; then
  printf 'Working tree status changed during read-only audit\n' >&2
  exit 2
fi

if ! git diff --exit-code > "$output/diff.txt"; then
  printf 'Tracked files changed during read-only audit\n' >&2
  exit 3
fi

printf 'Audit completed; inspect %s\n' "$output"
SH

chmod +x run-grok-audit.sh
```

运行：

```bash
./run-grok-audit.sh "$PWD"
```

输出放在 `/tmp`，避免只读检查自身生成未跟踪项目文件。正式 CI 应使用平台的临时目录，并控制日志保留与访问权限。

## 12. 会话与 Headless 恢复

Headless 任务也会使用本地会话系统。会话通常保存在：

```text
~/.grok/sessions/
```

继续最近会话：

```bash
grok --continue -p "重新检查现实状态后继续下一阶段"
```

恢复指定会话：

```bash
grok --resume SESSION_ID -p "重新检查后继续"
```

从旧会话创建新分支上下文：

```bash
grok \
  --resume SESSION_ID \
  --fork-session \
  -p "只读评估另一种方案"
```

恢复前先运行：

```bash
pwd
git branch --show-current
git status
git log -5 --oneline
```

会话上下文不是工作区快照。

## 13. Worktree 的作用

Git Worktree 允许同一仓库同时拥有多个工作目录：

```text
主工作区
→ 人工集成和最终测试

Worktree A
→ Grok 实现方案 A

Worktree B
→ Codex 或另一个 Grok 实现方案 B
```

它避免多个 Agent 同时修改同一个未提交工作区。

Grok Build 当前提供直接创建 Worktree 的入口：

```bash
grok --worktree
```

简写：

```bash
grok -w
```

指定名称：

```bash
grok --worktree parser-fix
```

指定起点：

```bash
grok \
  --worktree parser-fix \
  --ref main
```

具体分支命名和目录位置以当前版本输出为准。

## 14. 使用 Worktree 完成独立实现

在干净仓库根目录运行：

```bash
git status
grok --worktree whitespace-fix
```

进入创建的会话后先确认：

```text
当前工作目录是什么？
当前 Git 分支和 HEAD 是什么？
是否存在未提交修改？
只报告，不要修改。
```

Shell 中也应检查实际 Worktree：

```bash
git worktree list
```

让 Agent 执行任务时仍要明确：

```text
只修改指定文件。
不要操作主工作区。
不要执行 commit 或 push。
完成后运行测试并停止。
```

## 15. Worktree 管理命令

当前 Grok CLI 提供：

```bash
grok worktree list
grok worktree show NAME
grok worktree rm NAME
grok worktree gc
```

具体参数查看：

```bash
grok worktree --help
```

移除前检查：

- Worktree 路径；
- 分支名称；
- 未提交修改；
- 尚未推送的提交；
- 是否仍有运行中的终端或进程。

不要为了清理列表强制删除包含未保存工作的 Worktree。

## 16. Worktree 不等于完整隔离

Worktree 只隔离 Git 工作目录，不隔离：

- `~/.grok`；
- 认证与 API Key；
- 环境变量；
- SSH 密钥；
- Docker Socket；
- 网络；
- 数据库；
- 系统服务；
- GPU 和显存；
- 用户级缓存与记忆。

多个 Worktree 同时训练模型，仍可能争用同一块 GPU。两个 Agent 也可能通过共享数据库或远程 API 互相影响。

## 17. 多 CLI 协作案例

不推荐：

```text
Claude Code
+
Codex CLI
+
Grok Build
→ 同时修改主工作区
```

推荐：

```text
Worktree grok-implementation
→ Grok Build 实现

Worktree codex-review
→ Codex 做独立审查或替代实现

主工作区
→ 人工比较、选择、整合和最终测试
```

比较：

```bash
git diff main...grok-implementation
git diff main...codex-review
```

每个分支分别运行测试。合并后还要在集成分支重新测试。

## 18. Skill 的结构与边界

Grok Skill 是可复用的指令与资源包，可能包含：

```text
SKILL.md
scripts/
references/
assets/
```

常见位置：

```text
~/.grok/skills/
PROJECT_ROOT/.grok/skills/
```

Skill 不是普通 Prompt。如果包含脚本，它可能：

- 读取项目文件；
- 执行命令；
- 访问网络；
- 写入输出；
- 调用 MCP 或其他工具。

安装或复制 Skill 前，应审查全部脚本和引用，不要只看 `SKILL.md` 的简介。

## 19. Plugin 与 Marketplace

Plugin 可以组合：

- Skills；
- Agents；
- Hooks；
- MCP；
- LSP；
- 模板和其他资源。

用户与项目位置可能是：

```text
~/.grok/plugins/
PROJECT_ROOT/.grok/plugins/
```

Marketplace 只帮助发现插件，不代表每个插件已经由 xAI 完整安全审查。

安装前确认：

```text
维护者
源码仓库
版本与更新记录
自动脚本
Hook
MCP
网络与凭据
卸载和回滚方式
```

## 20. 自定义 Agent

自定义 Agent 可以保存特定角色的 Prompt、工具和工作方式。常见位置：

```text
~/.grok/agents/
PROJECT_ROOT/.grok/agents/
```

适合把“只读安全审查”“文档检查”“测试失败分类”等稳定任务封装起来。

不要让项目中来源不明的 Agent 默认获得全部 Shell、网络和凭据访问。自定义 Agent 的描述文件同样属于可执行工作流的一部分。

## 21. Hooks 的自动执行风险

项目 Hooks 常见位置：

```text
PROJECT_ROOT/.grok/hooks/
```

Hook 可在工具调用或会话事件前后执行命令，例如：

- 阻止危险 Shell；
- 修改后运行格式化；
- 记录审计日志；
- 结束时运行测试。

风险包括：

- 无限递归触发；
- 对整个仓库格式化；
- 把源码和环境变量写入日志；
- 自动联网；
- 自动提交或推送；
- 执行未审查的项目脚本。

安全 Hook 应优先检查与报告。用于阻断时，应在练习目录验证“拒绝后命令确实没有执行”。

## 22. MCP 连接外部数据和写操作

MCP 可以连接：

- 文档；
- 数据库；
- 浏览器；
- GitHub；
- 项目管理系统；
- 内部服务。

启用前检查：

```text
服务维护者
传输协议与地址
读取和写入能力
OAuth 或 API Key
凭据存储
日志和数据保留
返回内容是否可信
```

外部网页、Issue、文档和数据库字段可能包含提示注入。它们只能作为不可信数据，不能自动要求 Agent 读取主目录、上传环境变量或扩大权限。

## 23. LSP 与代码理解

项目可以通过：

```text
.grok/lsp.json
```

配置语言服务。LSP 能提高符号、定义和诊断能力，但也可能启动额外进程、扫描大型目录和读取编辑器相关配置。

启用前确认：

- LSP 二进制来自哪里；
- 是否需要下载；
- 工作目录；
- 扫描范围；
- 是否读取生成目录、数据集和凭据文件；
- 日志位置。

## 24. ACP 与编辑器集成

Grok Build 可以作为 ACP Agent 通过标准输入输出运行：

```bash
grok agent stdio
```

这允许编辑器或其他客户端驱动 Grok。接入后要重新确认：

- 客户端传入哪个工作目录；
- 哪些文件被自动附加；
- 权限模式与 Sandbox；
- 会话保存位置；
- 客户端是否额外提供网络或工具；
- 日志由哪一端保存。

换成编辑器界面不会自动缩小权限。ACP 模式同样应固定版本，并避免交互时自动更新改变协议行为。

## 25. 扩展来源用 `grok inspect` 核对

进入陌生项目后：

```bash
pwd
git status
grok inspect
grok inspect --json > grok-inspect.json
```

要求核对：

- Rules；
- Skills；
- Plugins；
- Agents；
- Hooks；
- MCP；
- LSP；
- Sandbox；
- Claude Code 兼容来源；
- 用户与项目配置冲突。

不要只检查 `.grok/config.toml`。扩展可能分散在多个目录和兼容配置中。

## 26. 自动化结束后的证据

Shell 中记录：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

任务报告应包含：

```text
执行机器与工作目录
Grok 版本
模型和推理强度
会话 ID
权限模式与 Sandbox
加载的关键扩展
执行命令与退出状态
测试结果
生成文件
未验证内容
风险
```

如果任务原本应该只读，任何 diff、未跟踪文件或外部写操作都要先解释。

## 27. Headless 任务模板

```text
目标：

现实状态：
- 主机：
- 工作目录：
- 分支：
- HEAD：
- 工作区状态：

允许工具：

允许修改：

禁止修改：

网络：

模型与最大轮数：

验证命令：

输出格式：

Git 边界：
- 不要 add、commit、push、reset、clean 或 rebase。

停止条件：
- 需要扩大文件或工具范围；
- 需要更高权限；
- 需要安装依赖；
- 测试结果与任务描述矛盾；
- 连续失败；
- 达到最大轮数；
- 无法找到足够证据。
```

## 延伸阅读

- [权限、Sandbox 与项目配置](02-权限Sandbox与项目配置.md)
- [复杂任务拆分与独立复核](../Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)
- [三个 AI CLI 怎么选](../Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)

官方参考：

- [Grok headless scripting](https://docs.x.ai/build/cli/headless-scripting)
- [Grok CLI reference](https://docs.x.ai/build/cli/reference)
- [Grok settings](https://docs.x.ai/build/settings)
- [Grok Build 官方开源仓库](https://github.com/xai-org/grok-build)
