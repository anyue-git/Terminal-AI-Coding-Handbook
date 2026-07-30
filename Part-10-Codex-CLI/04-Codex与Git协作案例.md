# 04 Codex CLI 与 Git 协作案例

> 最近核对：2026-07-29

Codex 能读取项目、修改文件、执行测试和审查差异，Git 则保存基线、隔离任务并记录人工确认后的版本。两者协作时，关键不是让 Codex 顺便完成所有 Git 操作，而是让每一次模型判断都能回到真实工作区、测试输出和分支差异。本章用一个小型登录校验器串起 Codex 的只读 Sandbox、可写 Sandbox、`AGENTS.md`、会话恢复、`codex review`、`/fork` 和 Worktree；暂存、提交、推送与 PR 的完整规则仍由 Part 04 主讲。

## 1. 建立可重复的基线

在独立目录创建实现、测试和项目规则：

```bash
mkdir -p ~/terminal-practice/codex-git-demo
cd ~/terminal-practice/codex-git-demo

cat > validator.py <<'PY'
def normalize_login(value: str | None) -> str:
    if value is None or value == "":
        raise ValueError("login is required")
    return value
PY

cat > test_validator.py <<'PY'
import pytest

from validator import normalize_login


def test_accepts_normal_login():
    assert normalize_login("alice") == "alice"


def test_rejects_empty_login():
    with pytest.raises(ValueError, match="login is required"):
        normalize_login("")


def test_rejects_none_login():
    with pytest.raises(ValueError, match="login is required"):
        normalize_login(None)
PY

cat > AGENTS.md <<'MD'
# 项目约定

- Python 命令使用项目 `.venv`。
- 修改后运行 `python -m pytest -q`。
- 不新增依赖。
- 只修改任务允许的文件。
- Git 暂存、提交、推送和历史修改由人处理。
MD

printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pytest
python -m pytest -q
```

基线应为三个测试通过。将初始文件提交后建立任务分支：

```bash
git init
git add validator.py test_validator.py AGENTS.md .gitignore
git commit -m "chore: create login validator demo"
git switch -c fix/trim-login
git status
```

需求是：只包含空格的登录标识仍应被拒绝，带首尾空格的普通名称应返回清理后的值，原有 `None`、空字符串和正常名称行为保持不变；允许修改的文件只有 `validator.py` 与 `test_validator.py`。这个边界同时写进 Prompt 和 `AGENTS.md`，但最终仍要通过 Git diff 判断是否遵守。

## 2. 从只读调查推进到两批实施

在项目根目录启动只读会话：

```bash
codex --sandbox read-only --ask-for-approval on-request
```

```text
读取 AGENTS.md、validator.py 和 test_validator.py，当前阶段只读。

任务：登录标识在校验前去除首尾空白；清理后为空仍抛出
ValueError("login is required")；其他现有行为保持不变。

请说明当前实现为什么不满足需求、需要新增哪些测试、最小实现会改哪几行，
以及准备运行的测试命令。已确认事实与推测分开写，并引用文件。
```

合格调查会指出现有函数只检查原始空字符串，没有对非空字符串调用 `strip()`，测试也缺少纯空格与首尾空格场景。如果分析开始讨论数据库、Web 框架或新依赖，说明它已经越过练习范围。

需要写入时重新启动可写会话：

```bash
codex --sandbox workspace-write --ask-for-approval on-request
```

第一批只增加能够证明需求的测试：

```text
只修改 test_validator.py。
新增两个测试：纯空格输入应抛出 login is required；
"  alice  " 应返回 "alice"。
运行 python -m pytest -q，并解释失败是否来自需求尚未实现。
完成后停止。
```

回到普通 Shell 检查工作区和失败原因：

```bash
git status --short
git diff -- test_validator.py
python -m pytest -q
```

目标测试应因尚未清理空白而失败，原有测试继续通过。导入错误、环境问题或拼写错误不构成需求复现。确认失败准确后恢复最近会话：

```bash
codex resume --last
```

```text
现在只修改 validator.py，让已经确认的测试通过。
不要改测试、依赖或项目规则，也不要执行 Git 写操作。
运行 python -m pytest -q，完成后报告代码变化和实际测试结果。
```

一个直接实现是：

```python
def normalize_login(value: str | None) -> str:
    if value is None:
        raise ValueError("login is required")
    normalized = value.strip()
    if normalized == "":
        raise ValueError("login is required")
    return normalized
```

实施结束后只相信真实命令输出：

```bash
python -m pytest -q
git status --short
git diff --name-status
git diff
```

检查允许文件之外是否出现变化，异常类型和文本是否保持兼容，测试有没有通过删除或放宽断言来适配实现。Codex 的总结是解释材料，工作区和测试结果才是交接证据。

## 3. 用 Review 和 `/fork` 获得不同阅读角度

Codex 提供独立 Review 入口。审查未提交修改前查看当前帮助，再让 Review 聚焦本任务：

```bash
codex review --help
codex review --uncommitted \
  "重点检查输入边界、异常类型、测试缺口和无关修改"
```

交互会话中也可以使用 `/review`。Review 会重新读取差异，但它不是批准按钮；每条意见都应落到具体文件、行为或测试，“没有发现问题”只表示这次阅读没有提出问题。

`/fork` 从当前上下文分出另一个会话，适合比较方案或进行只读复核。它复制会话上下文，不复制磁盘目录；两个可写分支会话仍然操作同一工作区。只想获得第二种解释可以用 `/fork`，真正并行修改则需要 Worktree。

## 4. 用 Worktree 隔离替代方案

主方案形成清楚提交后，可以从 `main` 建立另一个目录：

```bash
git worktree add \
  ../codex-git-demo-alternative \
  -b experiment/login-normalization \
  main

cd ../codex-git-demo-alternative
git status
git branch --show-current
codex
```

Worktree 隔离工作目录与分支，不隔离 `~/.codex`、认证、环境变量、SSH、Docker Socket、网络或数据库。两边分别运行测试，再比较完整分支差异：

```bash
git diff main...fix/trim-login
git diff main...experiment/login-normalization
git diff --stat main...fix/trim-login
git diff --stat main...experiment/login-normalization
```

比较需求覆盖、边界、复杂度、测试质量和兼容性。选择方案后通过正常的 merge、cherry-pick 或人工整合处理；只复制实现文件容易漏掉测试与提交语义。清理前查看 Worktree 的状态和最近提交：

```bash
cd ~/terminal-practice/codex-git-demo
git worktree list
git -C ../codex-git-demo-alternative status
git -C ../codex-git-demo-alternative log -3 --oneline
git worktree remove ../codex-git-demo-alternative
```

有未提交内容时，`git worktree remove` 会拒绝普通删除；不要绕过检查直接在 Finder 中移除目录。

## 5. 把结果交给 Git，而不是让 Agent 隐藏发布步骤

准备交接时，当前分支应能同时回答“改了什么、测试了什么、还有什么没有验证”：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
python -m pytest -q

codex review \
  --base main \
  "检查需求覆盖、边界条件、测试缺口、安全问题和无关修改；按严重程度排序"
```

只有人工读过最终差异、确认测试与当前 HEAD/工作区一致，才进入精确暂存、提交、推送和 PR。那些步骤见[日常提交与复核流程](../Part-04-Git/02-日常提交与复核流程.md)和[Pull Request 与多人协作](../Part-04-Git/04-Pull-Request与多人协作.md)；恢复、分支与 Worktree 的通用边界见[分支、合并与安全恢复](../Part-04-Git/03-分支合并与安全恢复.md)。项目规则可以禁止 Codex 自动写 Git，但不应把 push、历史改写或远程发布藏在普通开发任务里。

Codex 的非交互使用见[交互模式与自动化](03-交互模式与自动化.md)。

官方参考：

- [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
- [Codex review](https://developers.openai.com/codex/cli/reference/#codex-review)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
