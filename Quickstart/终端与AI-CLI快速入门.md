# 终端与 AI CLI 完整快速入门

> 适合第一次完整练习“终端 + Git + AI 编程工具”的读者。
>
> 预计时间：30–45 分钟。练习只使用 Python 标准库，不需要安装第三方依赖。

这篇教程会在主目录下创建一个很小的 Python 项目。你先亲自建立代码、运行测试并提交基线，再让 Claude Code、Codex CLI 或 Grok CLI 完成一个范围明确的修改，最后阅读 Git diff、重新运行测试并决定是否提交。整个过程不接触真实项目、账号配置或远程服务器，因此适合第一次练习。

## 1. 准备工具和独立项目

在 Mac 终端确认 Python、Git 和至少一个 AI CLI 可用：

```bash
python3 --version
git --version
type -a claude
type -a codex
type -a grok
```

不要求三个 Agent 都安装，本练习只选择其中一个。若 Python 或 Git 显示 `command not found`，先处理安装或 PATH；AI CLI 的安装、登录、供应商和凭证配置见 [Part 10C](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)。

接着确认当前机器和目录，并建立独立练习项目：

```bash
hostname
whoami
pwd
mkdir -p ~/terminal-practice
cd ~/terminal-practice
mkdir ai-cli-demo
cd ai-cli-demo
pwd
```

最终路径应类似 `/Users/YOUR_NAME/terminal-practice/ai-cli-demo`。若 `ai-cli-demo` 已存在，不要覆盖旧练习，改用 `ai-cli-demo-2` 等新名称。后面的所有文件都应位于这个目录；路径不符合预期时先停下来检查。

现在创建一个最小函数和测试：

```bash
cat > greeting.py <<'PY'
def greet(name: str) -> str:
    """Return a short greeting for the supplied name."""
    return f"Hello, {name}!"
PY

cat > test_greeting.py <<'PY'
import unittest

from greeting import greet


class GreetingTests(unittest.TestCase):
    def test_normal_name(self) -> None:
        self.assertEqual(greet("Alice"), "Hello, Alice!")


if __name__ == "__main__":
    unittest.main()
PY

ls -la
cat greeting.py
cat test_greeting.py
python3 -m unittest -v
```

正常情况下会看到一个测试通过。这个结果是修改前基线；以后测试失败时，只有知道项目原本能够运行，才能判断失败是否由本次任务引入。

## 2. 用 Git 保存基线并创建任务分支

初始化仓库，只暂存刚创建的两个文件，并在提交前检查暂存区：

```bash
git init
git status --short
git add greeting.py test_greeting.py
git diff --cached --name-status
git diff --cached
git commit -m "建立问候函数练习基线"
git status
git log --oneline -1
```

如果 Git 提示缺少用户名或邮箱，按提示配置自己的提交身份后重试。不要复制别人的邮箱，也不要把 API 账号邮箱误当成必须使用的 Git 身份。提交成功后，工作区应当干净。

这次任务是去掉姓名两侧空格，并拒绝空姓名。创建专用分支并确认起点：

```bash
git switch -c fix/normalize-name
git branch --show-current
git status --short
git rev-parse --short HEAD
```

分支让后面的修改与基线保持可比较状态，但不会替你恢复数据库、项目外文件或未提交数据。这里的练习只涉及两个受 Git 跟踪的文本文件，因此边界清楚。

## 3. 先让 Agent 调查，再限定任务

从当前项目目录启动一个工具：

```bash
claude
```

或者运行 `codex`、`grok`。进入 Agent 界面后，第一轮只读：

```text
当前阶段只读，不要修改文件、安装依赖、访问外部服务或执行 Git 写操作。

请检查当前目录、Git 状态、greeting.py 和 test_greeting.py，并回答：
1. 当前函数做什么；
2. 现有测试覆盖什么；
3. 项目怎样运行测试；
4. 当前工作区是否干净；
5. 如果要处理姓名两侧空格和空姓名，需要修改哪些文件。

结论附上文件路径，不要开始修改。
```

Agent 应找到两个文件并识别 `python3 -m unittest -v` 或等价测试方式。若它开始讨论不存在的框架、数据库或依赖，说明调查方向不对，应先纠正而不是授权修改。

调查结果正确后，再给出任务和验收方式：

```text
任务目标：改进 greet(name) 的输入处理。

要求：
1. 去掉 name 两侧的空白字符；
2. 去除空白后如果姓名为空，抛出 ValueError；
3. 正常姓名仍返回 "Hello, NAME!"；
4. 为两侧空格和空姓名补充测试。

允许修改：
- greeting.py
- test_greeting.py

禁止：
- 修改其他文件；
- 安装依赖；
- 删除文件；
- 访问项目外目录或网络；
- 执行 git add、commit 或 push。

先给出一个简短计划，不要立即修改。计划说明准备增加哪些测试、如何修改函数，以及最终运行什么命令验收。
```

计划应围绕两个文件和两类新测试展开。若 Agent 建议引入外部库、重构项目结构或修改无关内容，要求它缩小范围。

## 4. 分两步实施并检查失败证据

第一步只补测试：

```text
现在只修改 test_greeting.py：
- 增加一个姓名两侧有空格的测试；
- 增加一个空字符串或纯空白姓名应抛出 ValueError 的测试。

不要修改 greeting.py。完成后运行测试，报告实际命令、退出状态和失败原因，然后停止。
```

测试此时应该失败，因为实现尚未改变。关键不是“有失败”，而是失败原因确实对应新要求；导入错误、语法错误或运行了错误解释器都不能证明目标问题得到复现。

确认测试有效后，再授权最小实现：

```text
现在允许修改 greeting.py，只实现刚才测试要求的行为，不做其他重构。
完成后重新运行全部 unittest，报告命令、测试数量、退出状态和未验证内容。
不要提交或推送。
```

Agent 完成后，暂停或退出工具，回到普通 Shell。不要因为它给出“任务完成”的总结就直接进入提交阶段。

## 5. 用 diff 和测试亲自验收

先查看工作区真实状态：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

正常情况下只应看到 `greeting.py` 和 `test_greeting.py`。阅读 diff 时确认测试覆盖两侧空格和空姓名，`ValueError` 只在清理后为空时触发，正常姓名行为仍然保留，同时没有调试输出、无关格式化或额外文件。一个合理实现可能使用 `strip()`，但熟悉的写法不能代替测试证据。

亲自运行测试和一次手工验证：

```bash
python3 -m unittest -v

python3 - <<'PY'
from greeting import greet

print(greet("  Alice  "))
try:
    greet("   ")
except ValueError as exc:
    print(type(exc).__name__, str(exc))
PY
```

测试应全部通过，手工输出应包含 `Hello, Alice!` 和 `ValueError`。异常消息的具体文字可以不同，但异常类型和触发条件必须符合任务要求。

## 6. 人工决定是否提交

确认 diff 和验证结果后，只暂存目标文件并再次阅读暂存区：

```bash
git add greeting.py test_greeting.py
git diff --cached --name-status
git diff --cached
git commit -m "规范化问候函数的姓名输入"
git status
git log --oneline --decorate -3
```

现在仓库应有一个基线提交和一个任务提交。你已经完整走过一次：建立项目、运行基线、创建分支、让 Agent 调查、限定任务、分步修改、查看 diff、运行测试和人工提交。是否 push 或创建 PR 是新的影响范围，本练习不要求执行。

## 7. 常见偏差怎样处理

Agent 修改了范围外文件时，先不要暂存。使用 `git status --short` 和 `git diff --name-status` 确认现场，再让它解释原因或人工恢复明确不需要的变化；不要用一次丢弃全部工作区修改的命令省事。

测试在修改前就失败时，回到基线检查 Python 版本、运行命令和环境。没有可靠基线，很难证明新失败来自本次任务。Agent 宣称测试通过却没有命令、退出状态或输出时，自己重新运行；总结中的“已验证”不能代替真实证据。

本练习不需要读取主目录、OAuth 缓存、API Key 或其他凭证。遇到此类权限请求应拒绝，并重新限定项目目录。第一次练习也只使用一个 Agent；多个 Agent 需要独立分支、Worktree 或隔离实例，不能通过简单打开多个窗口获得可靠隔离。

完成后可继续阅读 [Terminal 到底是什么](../Part-01-基础篇/02-Terminal到底是什么.md)、[`pwd`、`ls` 与 `cd`](../Part-02-终端命令/01-pwd-ls-cd.md)、[Git 心智模型](../Part-04-Git/01-Git心智模型.md)、[通用 AI 编程闭环](../Part-12-AI开发工作流/01-通用AI编程闭环.md)以及配置与凭证章节。保留 `~/terminal-practice/ai-cli-demo`，后续可以继续练习分支、恢复、Pull Request 和不同 AI CLI 的行为差异。