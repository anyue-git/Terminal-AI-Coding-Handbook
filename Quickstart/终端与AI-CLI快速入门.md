# 终端与 AI CLI 完整快速入门

> 适合第一次完整练习“终端 + Git + AI 编程工具”的读者。
>
> 预计时间：30–45 分钟。练习只使用 Python 标准库，不需要安装第三方依赖。

这篇教程会在主目录下创建一个很小的 Python 项目，先由你运行和提交基线，再让 Claude Code、Codex CLI 或 Grok CLI 完成一个范围明确的修改。最后，你会亲自运行测试并查看 Git diff。整个过程不接触真实项目、账号配置或远程服务器，因此适合第一次练习。

## 1. 开始前检查工具

在 Mac 终端执行：

```bash
python3 --version
git --version
```

你应看到 Python 和 Git 的版本信息。如果出现 `command not found`，先处理对应工具的安装或 PATH，不要继续复制后面的命令。

再检查至少一个 AI CLI 是否可用：

```bash
type -a claude
type -a codex
type -a grok
```

不要求三个都安装。这次只选择其中一个。Claude Code、Codex CLI 和 Grok CLI 的安装、登录与模型接入方式不同，本练习假设你已经能正常启动其中一个；配置、凭证和供应商切换见 [Part 10C](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)。

## 2. 创建独立练习项目

先确认当前机器和目录：

```bash
hostname
whoami
pwd
```

建立练习目录：

```bash
mkdir -p ~/terminal-practice
cd ~/terminal-practice
mkdir ai-cli-demo
cd ai-cli-demo
pwd
```

如果 `mkdir ai-cli-demo` 提示目录已经存在，不要覆盖旧练习。改用另一个名称，例如：

```bash
mkdir ai-cli-demo-2
cd ai-cli-demo-2
```

最终的 `pwd` 应类似：

```text
/Users/YOUR_NAME/terminal-practice/ai-cli-demo
```

后面的文件都应该出现在这个目录中。路径不符合预期时，先停下来检查，不要继续创建文件。

## 3. 手工建立一个最小 Python 项目

创建 `greeting.py`：

```bash
cat > greeting.py <<'PY'
def greet(name: str) -> str:
    """Return a short greeting for the supplied name."""
    return f"Hello, {name}!"
PY
```

创建测试文件：

```bash
cat > test_greeting.py <<'PY'
import unittest

from greeting import greet


class GreetingTests(unittest.TestCase):
    def test_normal_name(self) -> None:
        self.assertEqual(greet("Alice"), "Hello, Alice!")


if __name__ == "__main__":
    unittest.main()
PY
```

检查目录和文件正文：

```bash
ls -la
cat greeting.py
cat test_greeting.py
```

运行测试：

```bash
python3 -m unittest -v
```

正常结果类似：

```text
test_normal_name (test_greeting.GreetingTests.test_normal_name) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

这一步很重要。后面如果测试失败，你需要知道问题是 AI 修改造成的，还是项目在修改前就无法运行。

## 4. 用 Git 保存修改前的基线

初始化仓库：

```bash
git init
git status
```

Git 会显示两个未跟踪文件。只暂存这两个文件：

```bash
git add greeting.py test_greeting.py
git diff --cached --name-status
git diff --cached
```

确认暂存区只有刚创建的代码和测试，再提交：

```bash
git commit -m "建立问候函数练习基线"
```

如果 Git 提示没有设置用户名或邮箱，按照提示配置自己的提交身份后重新提交。不要随便复制别人的邮箱，也不要把 API 账号邮箱误当成必须使用的 Git 身份。

提交后检查：

```bash
git status
git log --oneline -1
```

工作区应当干净，并显示刚才的基线提交。

## 5. 建立任务分支

这次要让 Agent 完成的任务是：去掉姓名两侧的空格，并拒绝空姓名。创建分支：

```bash
git switch -c fix/normalize-name
```

确认状态：

```bash
git branch --show-current
git status
```

你现在拥有一个清楚的起点。即使后面的修改不满意，也可以通过 Git 看出它与基线的差异。

## 6. 启动一个 AI CLI

在当前项目目录中运行一个工具：

```bash
claude
```

或：

```bash
codex
```

或：

```bash
grok
```

进入 Agent 界面后，先只做调查。输入：

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

Agent 应当找到两个文件，并识别 `python3 -m unittest -v` 或等价测试方式。如果它开始讨论不存在的框架、数据库或依赖，说明调查方向不对，应先纠正。

## 7. 给出明确任务和验收方式

调查正确后，输入：

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

计划应当围绕两个文件和两类新测试展开。若 Agent 建议引入外部库、重构项目结构或修改与任务无关的内容，可以直接要求它缩小范围。

## 8. 让 Agent 分两步完成修改

先让它只补测试：

```text
现在只修改 test_greeting.py：
- 增加一个姓名两侧有空格的测试；
- 增加一个空字符串或纯空白姓名应抛出 ValueError 的测试。

不要修改 greeting.py。完成后运行测试，报告实际命令和失败原因，然后停止。
```

此时测试应该失败，因为实现尚未改变。失败并不代表 Agent 做错了；关键是失败原因是否正好对应新要求。

确认测试有效后，再输入：

```text
现在允许修改 greeting.py，只实现刚才测试要求的行为，不做其他重构。
完成后重新运行全部 unittest，报告命令、测试数量、退出状态和未验证内容。
不要提交或推送。
```

Agent 完成后，先不要直接接受“任务完成”的总结。退出或暂停 Agent，回到普通 Shell 检查真实文件。

## 9. 查看实际改动

运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

正常情况下，只应看到：

```text
greeting.py
test_greeting.py
```

阅读 diff 时检查：

- 是否确实只改了两个允许文件；
- 测试是否覆盖空格和空姓名；
- `ValueError` 是否只在清理后姓名为空时触发；
- 正常姓名的原行为是否保留；
- 有没有调试输出、无关格式化或额外文件。

一个合理实现可能使用 `strip()` 清理输入，但不要只因为看见熟悉的方法就跳过测试。代码阅读和运行结果是两种不同证据。

## 10. 亲自运行验收

执行：

```bash
python3 -m unittest -v
```

你应看到三个或更多测试通过，具体名称取决于 Agent 如何命名。还可以手工验证：

```bash
python3 - <<'PY'
from greeting import greet

print(greet("  Alice  "))
try:
    greet("   ")
except ValueError as exc:
    print(type(exc).__name__, str(exc))
PY
```

输出应包含：

```text
Hello, Alice!
ValueError ...
```

错误消息的具体文字可以不同，但异常类型应符合要求。

## 11. 决定是否提交

确认 diff 和测试结果后，只暂存目标文件：

```bash
git add greeting.py test_greeting.py
git diff --cached --name-status
git diff --cached
```

暂存区正确后提交：

```bash
git commit -m "规范化问候函数的姓名输入"
```

最后查看：

```bash
git status
git log --oneline --decorate -3
```

现在仓库中应当有一个基线提交和一个任务提交。你已经完整走过一次：建立项目、运行基线、创建分支、让 Agent 调查、限定任务、分步修改、查看 diff、运行测试和人工提交。

## 12. 练习中最常见的偏差

### Agent 修改了范围外文件

先不要暂存。运行：

```bash
git status --short
git diff --name-status
```

让 Agent 解释为什么修改这些文件，或在确认不需要保留后人工恢复。不要使用会一次丢弃全部工作区变化的命令来省事。

### 测试在修改前就失败

回到基线提交查看测试环境，确认 Python 版本和运行命令。没有可用基线时，很难证明新失败来自本次修改。

### Agent 宣称测试通过，但没有命令或结果

自己运行测试。总结中的“已验证”不能代替真实命令、退出状态和输出。

### AI CLI 请求访问主目录或凭证

本练习不需要这些权限。拒绝请求并重新限定项目目录。配置文件、OAuth 缓存和 API Key 不属于代码任务的默认阅读范围。

### 想同时启动多个 Agent

同一工作区中的多个 Agent 会共享文件状态。第一次练习只使用一个；需要并行工作时，应先学习 Git worktree、独立分支或隔离实例，而不是简单打开多个窗口。

## 13. 下一步怎么学

完成练习后，可以按需要继续阅读：

- [Terminal 到底是什么](../Part-01-基础篇/02-Terminal到底是什么.md)
- [`pwd`、`ls` 与 `cd`](../Part-02-终端命令/01-pwd-ls-cd.md)
- [Git 心智模型](../Part-04-Git/01-Git心智模型.md)
- [通用 AI 编程闭环](../Part-12-AI开发工作流/01-通用AI编程闭环.md)
- [Codex 的 TOML、Profile 与凭证](../Part-10C-配置凭证与多实例/02-Codex-TOML配置与凭证.md)
- [Claude Code 的配置、凭证与网关](../Part-10C-配置凭证与多实例/03-Claude-Code配置凭证与网关.md)

不要急着删除 `~/terminal-practice/ai-cli-demo`。保留这个小仓库，后面可以继续练习分支、恢复、Pull Request、不同 AI CLI 的行为差异和配置切换。
