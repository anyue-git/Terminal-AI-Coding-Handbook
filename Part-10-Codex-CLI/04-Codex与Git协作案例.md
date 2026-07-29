# 04 Codex CLI 与 Git 协作案例

> 最近核对：2026-07-29

Codex 与 Git 的合理分工不是“让 Agent 自动提交全部结果”，而是：

```text
Codex
→ 理解、修改、运行测试、解释差异

Git
→ 隔离任务、记录现场、比较方案、保存检查点、支持恢复

人
→ 确定范围、审查命令和 diff、决定提交与发布
```

本章建立一个完整练习项目，修复“只包含空格的登录标识仍被接受”的问题。整个过程包括基线、任务分支、失败测试、最小实现、精确暂存、独立 Review、Worktree 对照和 Pull Request 准备。

## 1. 创建练习项目

在 Mac 或 Ubuntu 本机终端运行：

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
- 只修改本次任务明确允许的文件。
- 不执行 `git add`、`git commit`、`git push`、`git reset`、`git clean` 或历史改写。
MD

python3 -m venv .venv
. .venv/bin/activate
python -m pip install pytest
python -m pytest -q
```

预期基线：

```text
3 passed
```

初始化 Git：

```bash
git init
git add validator.py test_validator.py AGENTS.md
git commit -m "chore: create login validator demo"
```

确认：

```bash
git status
git log --oneline --decorate -3
```

工作区应干净。`.venv` 如果显示为未跟踪，应创建 `.gitignore` 并提交，而不是把虚拟环境加入 Git：

```bash
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git add .gitignore
git commit -m "chore: ignore local Python files"
```

## 2. 把需求写成可验证行为

任务不是模糊的“优化登录校验”，而是：

```text
输入 "   " 时应抛出 ValueError("login is required")。
输入 "  alice  " 时应返回 "alice"。
现有 None、空字符串和普通登录行为必须继续通过。
```

这三个行为决定了测试和最小实现范围。

先创建 Issue 风格任务文件：

```bash
cat > task.md <<'EOF'
目标：登录标识在校验前应去除首尾空白。

预期行为：
- "   " 抛出 ValueError("login is required")；
- "  alice  " 返回 "alice"；
- None、空字符串和普通登录继续保持正确。

允许修改：
- validator.py
- test_validator.py

禁止：
- 新增依赖；
- 修改 AGENTS.md、.gitignore 或其他文件；
- 执行 Git 写操作。

验证：
python -m pytest -q

阶段要求：先只读分析；确认后先添加失败测试；再次确认后再改实现。
EOF
```

`task.md` 是否提交取决于团队习惯。本练习先保留为本地任务说明，不纳入最终功能提交。

## 3. 创建任务分支

由人在 Shell 中运行：

```bash
git status
git switch -c fix/trim-login
```

确认：

```bash
git branch --show-current
git status --short
```

已有未提交修改时，不要让 Codex 自动“清理干净”。先识别每项修改属于谁、是否需要保存，再开始新任务。

## 4. 第一轮只读调查

启动 Codex：

```bash
codex --sandbox read-only --ask-for-approval on-request
```

输入：

```text
读取 task.md、AGENTS.md、validator.py 和 test_validator.py。
当前阶段只读，不要修改文件、运行安装命令或执行 Git 写操作。

请输出：
1. 当前行为和真实测试基线；
2. Bug 的最小原因；
3. 应新增的两个测试；
4. 最小实现方案；
5. 计划运行的命令；
6. 已确认事实与推测。

每个结论引用文件。
```

理想计划应接近：

```text
先在 test_validator.py 增加空白输入和首尾空白测试
→ 运行测试并确认预期失败
→ 在 validator.py 中统一 strip 后校验
→ 运行完整测试
```

如果计划提出更换框架、增加第三方库或重构整个认证模块，应要求它缩小范围。

## 5. 先只增加失败测试

切换到可写权限时，不必重启会话，也可以通过 `/permissions` 调整；为清楚起见，本练习重新启动：

```bash
codex --sandbox workspace-write --ask-for-approval on-request
```

输入：

```text
现在只执行第一阶段。

只允许修改 test_validator.py。
新增两个最小测试：
- 只包含空格时抛出 login is required；
- 带首尾空格的普通登录返回去除空格后的值。

不要修改 validator.py 或其他文件。
运行 python -m pytest -q，并确认失败来自新需求尚未实现。
完成后停止，报告修改、命令、退出状态和失败原因。
```

Codex 停止后，在普通 Shell 中检查：

```bash
git status --short
git diff --name-status
git diff -- test_validator.py
```

应该只有：

```text
M test_validator.py
```

运行测试：

```bash
. .venv/bin/activate
python -m pytest -q
```

预期新测试失败。如果全部通过，说明测试没有真正覆盖问题；如果旧测试失败，说明测试修改可能破坏了基线。

## 6. 把失败测试保存成检查点

确认测试准确以后，由人精确暂存：

```bash
git add test_validator.py
git diff --cached --name-status
git diff --cached
```

创建提交：

```bash
git commit -m "test: reproduce whitespace login bug"
```

这个提交暂时是红色测试提交。在团队是否允许提交失败测试取决于工作流；也可以不推送，等实现完成后再整理。但把测试与实现分开有助于证明测试确实先失败。

检查：

```bash
git log --oneline --decorate -3
git status
```

## 7. 再执行最小实现

回到 Codex 会话或恢复最近会话：

```bash
codex resume --last
```

恢复后先要求重新检查现实：

```text
先不要修改。
重新检查当前分支、HEAD、Git 状态、现有失败测试和 AGENTS.md。
说明与旧会话上下文相比发生了什么。
```

确认后输入：

```text
现在只执行实现阶段。

只允许修改 validator.py。
让 normalize_login 在校验前去除首尾空白，并满足现有测试。
不要修改测试、依赖或其他文件，不要执行 Git 写操作。
运行 python -m pytest -q。
完成后停止，报告实际代码变化、测试命令、退出状态和风险。
```

Shell 中核对：

```bash
git status --short
git diff --name-status
git diff -- validator.py
python -m pytest -q
```

合理实现类似：

```python
def normalize_login(value: str | None) -> str:
    if value is None:
        raise ValueError("login is required")
    normalized = value.strip()
    if normalized == "":
        raise ValueError("login is required")
    return normalized
```

不要只检查测试是否绿色，还要确认 `None` 不会在调用 `strip()` 时抛出错误类型不一致的异常。

## 8. 人工审查实际 diff

运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

重点检查：

- 是否只修改 `validator.py`；
- 是否出现无关格式化；
- 是否删除或弱化测试；
- 是否加入调试输出；
- 是否改变异常文本；
- 是否新增依赖或生成缓存；
- 是否把 `task.md`、`.venv` 或日志混入任务。

Codex 的最终总结不是审计依据。Git diff 才是当前工作区的事实。

## 9. 使用 `codex review` 做独立审查

Codex 提供独立审查入口。先查看当前版本：

```bash
codex review --help
```

审查未提交修改：

```bash
codex review --uncommitted \
  "重点检查输入边界、异常类型、测试缺口和无关修改"
```

也可以在交互界面使用：

```text
/review
```

Review 结果应按证据处理。每条问题都应回到文件、测试或 diff 验证，不要因为审查 Agent 没有发现问题就认为代码一定正确。

## 10. 用 `/fork` 比较另一种实现思路

在当前会话输入：

```text
/fork
```

在新会话中要求：

```text
只读审查当前实现，不要修改文件。
给出另一种最小实现，并比较：
- None 处理；
- 空白字符串；
- Unicode 空白；
- 可读性；
- 是否改变现有接口。
```

会话分叉不会自动创建 Git 分支。若两个会话都允许写同一工作区，仍可能互相覆盖。只读比较可以使用 `/fork`；并行实现应使用独立 Worktree。

## 11. 精确暂存实现

确认实现后：

```bash
git add validator.py
git diff --cached --name-status
git diff --cached
```

此时暂存区应只有实现文件，因为测试已经在上一个提交中。

提交：

```bash
git commit -m "fix: normalize whitespace in login identifier"
```

再次验证：

```bash
python -m pytest -q
git status
git log --oneline --decorate -5
git show --stat --oneline HEAD
```

如果团队希望测试与实现位于同一个提交，可以在人工理解 Git 历史后使用交互式 rebase 或 reset 重新组织。但新手不必为了“一个提交更漂亮”立即改写历史；清楚、可审查的两个提交同样合理。

## 12. 用 Worktree 隔离另一种方案

回到主工作区，查看仓库根：

```bash
git rev-parse --show-toplevel
```

创建另一个 Worktree：

```bash
git worktree add \
  ../codex-git-demo-alternative \
  -b experiment/login-normalization \
  main
```

进入：

```bash
cd ../codex-git-demo-alternative
git status
git branch --show-current
```

这里可以启动另一个 Codex 会话：

```bash
codex
```

要求它独立实现同一需求。两个 Worktree 有独立工作目录和分支，因此不会直接覆盖同一文件。

Worktree 不会隔离：

- `~/.codex` 与认证；
- 环境变量；
- SSH 密钥；
- Docker Socket；
- 网络；
- 数据库与系统服务；
- 全局缓存。

因此它是 Git 工作区隔离，不是完整安全沙箱。

## 13. 比较两个实现

在任一仓库工作区运行：

```bash
git diff main...fix/trim-login
git diff main...experiment/login-normalization
```

比较统计：

```bash
git diff --stat main...fix/trim-login
git diff --stat main...experiment/login-normalization
```

还应分别切换到各自 Worktree 运行测试，不能把 A 分支的测试结果当成 B 分支证据。

比较维度：

```text
需求覆盖
边界条件
代码复杂度
测试质量
无关修改
兼容性
可读性
```

选择方案以后，用正常 Git 合并、cherry-pick 或人工重写整合。不要复制粘贴文件后忘记保留对应测试与提交信息。

## 14. 安全移除 Worktree

先在替代 Worktree 中检查：

```bash
git status
git log --oneline --decorate -3
```

确认需要的修改已提交或明确放弃后，回到主工作区：

```bash
cd ~/terminal-practice/codex-git-demo
git worktree list
```

再移除：

```bash
git worktree remove ../codex-git-demo-alternative
```

不要在存在未提交修改时使用强制移除。Worktree 删除后，分支仍可能存在：

```bash
git branch --list
```

是否删除实验分支应由人根据保留需求决定。

## 15. 推送前进行分支级审查

比较目标分支：

```bash
git diff main...HEAD --name-status
git diff main...HEAD --stat
git diff main...HEAD
```

运行完整测试：

```bash
python -m pytest -q
```

再使用 Codex 只读审查：

```bash
codex review \
  --base main \
  "检查需求覆盖、边界条件、测试缺口、安全问题和无关修改；按严重程度排序"
```

也可以审查具体提交：

```bash
codex review --commit HEAD
```

参数以当前 `codex review --help` 为准。

## 16. Push 由人决定

推送前检查：

```bash
git status
git branch --show-current
git log --oneline --decorate -5
git diff main...HEAD --stat
```

确认：

- 分支名称正确；
- 工作区干净；
- 没有凭据、日志或大型生成物；
- 测试已经在当前 HEAD 上运行；
- 提交历史能够解释；
- 没有无关文件。

然后由人执行：

```bash
git push -u origin fix/trim-login
```

不要把 `git push` 写入项目级 `AGENTS.md`、Hook 或普通 Codex 任务模板。

## 17. Pull Request 描述应基于证据

```md
## 变更内容

- 登录标识校验前去除首尾空白
- 拒绝只包含空白的输入
- 增加空白输入和标准化回归测试

## 原因

旧实现只拒绝 `None` 和空字符串，没有处理空白字符串，也没有返回标准化结果。

## 验证

- `python -m pytest -q`
- 结果：5 passed

## 风险

- 调用方现在会收到去除首尾空白后的登录标识
- 依赖保留首尾空白的异常调用方可能受到影响

## 未处理

- Unicode 用户名规范化
- 大小写策略
- 登录限流
```

测试数字必须来自当前提交的真实运行结果，不要照抄示例。

## 18. Codex 可以执行哪些 Git 命令

只读命令通常适合由 Codex运行：

```bash
git status
git diff
git log
git show
git branch --show-current
```

写操作需要更严格控制：

```text
git add
→ 改变暂存区

git commit
→ 创建历史

git switch / checkout
→ 改变工作区与分支

git reset / clean
→ 可能丢失修改

git rebase
→ 改写历史

git push
→ 修改远程仓库
```

推荐 Prompt：

```text
不要执行 Git 写操作。
完成后只列出：
- 建议暂存的文件；
- 不应暂存的文件；
- 建议提交信息；
- 推送前检查项。
```

## 19. 恢复错误修改时先分类

未暂存的已跟踪文件修改可以先查看：

```bash
git diff
```

只撤销一个确认不需要的文件：

```bash
git restore path/to/file
```

已暂存但尚未提交：

```bash
git diff --cached
git restore --staged path/to/file
```

已提交并准备保留历史：

```bash
git revert COMMIT_SHA
```

不要让 Codex 在不理解现有修改归属时运行：

```text
git reset --hard
git clean -fd
git push --force
```

Git 也无法恢复已经上传到网络的数据、数据库写入、Docker Volume 变化或项目外删除。

## 20. 多 Agent 协作的安全结构

不推荐：

```text
Codex 会话 A
+
Codex 会话 B
+
Claude Code
+
Grok Build
→ 同时修改同一个未提交工作区
```

更合理：

```text
主工作区
→ 人工集成与最终测试

Worktree A
→ Codex 实现

Worktree B
→ Grok 或另一 Codex 实现

独立只读会话
→ Review
```

每个工作区都要分别记录分支、HEAD、测试和 diff。最终合并后还要在集成分支重新运行测试。

## 21. 完成任务的检查清单

开始前：

```bash
git status
git branch --show-current
git log -1 --oneline
```

实施中：

```text
只读调查
→ 失败测试
→ 最小实现
→ 每阶段停止
```

结束后：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
git diff --cached
python -m pytest -q
```

提交后：

```bash
git show --stat
git diff main...HEAD
git status
```

最后由人决定是否 Push 和创建 PR。

## 延伸阅读

- [Git 心智模型](../Part-04-Git/01-Git心智模型.md)
- [日常提交与复核流程](../Part-04-Git/02-日常提交与复核流程.md)
- [分支、合并与安全恢复](../Part-04-Git/03-分支合并与安全恢复.md)
- [Pull Request 与多人协作](../Part-04-Git/04-Pull-Request与多人协作.md)
- [交互模式与自动化](03-交互模式与自动化.md)

官方参考：

- [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
- [Codex review](https://developers.openai.com/codex/cli/reference/#codex-review)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
