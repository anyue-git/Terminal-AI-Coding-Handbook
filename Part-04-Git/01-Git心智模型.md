# 01 Git 心智模型

Git 经常和 GitHub 一起出现，因此新手容易把它理解成“上传代码的工具”。实际上，Git 首先在本地工作：它记录文件变化，把一组经过选择的修改保存成提交，并允许你创建分支、比较历史和恢复已经记录的内容。即使电脑没有联网，绝大多数 Git 操作仍然可用。

本章通过一个小项目观察工作区、暂存区和提交历史之间的关系，再说明分支、远程仓库和 AI CLI 应该处在什么边界。后续章节会继续使用本章留下的练习状态。

## 1. 建立仓库并观察工作区

在 Mac 终端创建独立练习目录并初始化 Git：

```bash
mkdir -p ~/terminal-practice/git-workflow-demo
cd ~/terminal-practice/git-workflow-demo
pwd
git init
```

初始化成功时可能看到：

```text
Initialized empty Git repository in /Users/NAME/terminal-practice/git-workflow-demo/.git/
```

`.git` 是 Git 保存提交对象、分支引用和仓库配置的隐藏目录，不要手工修改或删除。此时运行 `git status`，空仓库通常会提示当前分支还没有提交，也没有可提交内容。如果第一次提交时 Git 要求设置作者姓名和邮箱，应按提示配置自己的身份；这些信息会写进提交记录，但不等同于 GitHub 密码。

接着创建一个最小计算器和测试文件，并先确认程序可以运行：

```bash
cat > calculator.py <<'PY'
def add(left, right):
    return left + right
PY

cat > test_calculator.py <<'PY'
import unittest

from calculator import add


class CalculatorTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
PY

python3 -m unittest -v
git status --short
```

状态可能显示：

```text
?? calculator.py
?? test_calculator.py
```

`??` 表示未跟踪文件。它们已经存在于磁盘，也可以被 Python 正常读取，但 Git 还没有把这些内容纳入任何提交。当前检出的项目文件构成工作区，编辑器、终端和 AI CLI 直接修改的都是这一层；文件出现在项目目录里，并不意味着 Git 已经自动保存它。

## 2. 暂存区选择下一次提交的具体内容

把两个文件加入暂存区，再查看状态和暂存差异：

```bash
git add calculator.py test_calculator.py
git status
git diff --cached
```

它们会出现在 `Changes to be committed` 下，而 `git diff --cached` 展示下一次 `git commit` 准备记录的内容。暂存区可以理解成提交候选清单，但它保存的不只是文件名，而是文件在执行 `git add` 时的具体版本。

可以通过一次小实验观察这一点。文件已经暂存后，再向 `calculator.py` 追加一行注释：

```bash
printf '%s\n' '' '# Supports basic integer addition.' >> calculator.py
git status
git diff --cached -- calculator.py
git diff -- calculator.py
```

同一个文件现在可能同时出现在“已暂存”和“未暂存”区域。第一条 diff 展示已经进入暂存区的旧版本，第二条 diff 展示暂存后又产生的新变化。把最新内容也加入暂存区后，两层才重新一致：

```bash
git add calculator.py test_calculator.py
git status
git diff --cached
```

这就是工作区和暂存区最重要的区别：工作区反映你正在编辑的现场，暂存区反映你准备放进下一次提交的内容。`git status` 告诉你各层当前有什么，`git diff` 比较工作区与暂存区，`git diff --cached` 比较暂存区与最近一次提交。

## 3. 提交把暂存内容写入本地历史

确认暂存差异符合预期后，创建第一次提交：

```bash
git commit -m "feat: add basic calculator"
git status
git log --oneline --decorate -5
```

提交记录可能类似：

```text
abc1234 (HEAD -> main) feat: add basic calculator
```

哈希值会因仓库而异。这个提交只写入本机的 `.git`，并没有自动上传到 GitHub。到这里，本地流程可以概括为：

```text
工作区
→ git add 选择具体内容
→ 暂存区
→ git commit 记录快照
→ 本地提交历史
```

提交不是对整个目录做一次盲目备份，而是记录当时暂存区中的快照。没有暂存的修改和未跟踪文件不会自动进入提交，因此在执行 `git commit` 前阅读 `git status` 和 `git diff --cached`，比记住某个固定命令顺序更重要。

## 4. 用精确暂存和分支隔离下一项工作

现在同时创建一份个人笔记，并给计算器增加减法函数：

```bash
printf '%s\n' 'Remember to improve error messages.' > notes.txt
cat >> calculator.py <<'PY'


def subtract(left, right):
    return left - right
PY

git status --short
```

可能得到：

```text
 M calculator.py
?? notes.txt
```

假设下一次提交只想记录减法功能，个人笔记不应进入历史，可以只暂存源码并检查候选内容：

```bash
git add calculator.py
git diff --cached
git status
```

`notes.txt` 仍然留在工作区，下一次提交不会包含它。暂存区的价值就在这里：即使工作目录中同时存在不同目的的修改，也可以精确选择某次提交应记录的内容。这也是为什么不应把 `git add .` 当作永远正确的默认动作；它可能把日志、缓存、临时文件、无关格式化和意外出现的敏感配置一起加入。

为了观察取消暂存的效果，执行：

```bash
git restore --staged calculator.py
git status --short
```

这条命令只把 `calculator.py` 移出暂存区，不会删除刚写的减法函数。当前修改仍在工作区，接着创建任务分支：

```bash
git switch -c feature/subtraction
git branch --show-current
git status --short
```

分支是一个随着提交向前移动的名字，`HEAD` 表示当前检出位置，通常指向当前分支。创建分支并不会复制一整份项目目录，因此速度很快；未提交修改也不会因为切换分支而自动隔离，它们仍然跟随当前工作区。查看分支、提交和图形历史可以使用：

```bash
git rev-parse --short HEAD
git log --oneline --decorate --graph -10
```

第一次提交可以记作 A，后续提交 B 会指向 A；分支名和 `HEAD` 则指向当前所在的提交：

```text
A ← B
    ↑
feature/subtraction
    ↑
   HEAD
```

本章先不提交减法功能。下一章会从 `feature/subtraction` 分支、已修改的 `calculator.py` 和未跟踪的 `notes.txt` 继续，完成测试、精确暂存和提交复核。

## 5. 区分 Git、GitHub 与恢复边界

Git 是本地版本控制系统，GitHub、GitLab 等平台负责托管 Git 仓库，并提供账号权限、Pull Request、Issue 和自动化检查。本地无需联网即可执行 `status`、`diff`、`add`、`commit`、`branch` 和 `log`；`fetch`、`pull`、`push` 才会与远程通信。

```bash
git status
git diff
git add
git commit
git branch
git log

git fetch
git pull
git push
```

用 `git remote -v` 可以查看当前仓库是否配置远程。本练习仓库还没有远程，因此没有输出是正常的；`origin` 只是远程名称的常见约定，并不是 GitHub 专属关键字。

Git 擅长恢复已经跟踪并进入提交历史的文件，也能帮助找回部分仍有引用记录的提交，但它不是整个计算机的撤销系统。数据库写入、云资源操作、Docker Volume、项目目录之外的文件、已经发送到网络的数据，以及从未提交过的未跟踪文件，都不能因为项目使用 Git 就自动恢复。

当前的 `notes.txt` 仍未跟踪。如果直接从磁盘删除，Git 通常没有副本可以找回。决定恢复方式前，先判断文件是否已被跟踪、修改是否已暂存、是否已经形成提交，以及提交是否已经共享到远程；问题所处层次不同，安全做法也不同。

## 6. AI CLI 参与时仍由人工控制 Git 历史

Agent 开始工作前，人工先确认当前分支和工作区：

```bash
git status
git branch --show-current
```

任务说明应明确限制修改范围，并禁止未经授权的 Git 写操作：

```text
只修改当前任务需要的工作区文件。
不要执行 git add、commit、push、merge、rebase、reset 或 clean。
完成后列出全部变更文件、测试命令和未验证内容。
```

Agent 完成后，人工用 Git 查看真实现场：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Agent 的总结只能说明它认为自己做了什么，Git 差异才是工作区实际发生的变化。确认需求、测试和 diff 相互对应后，再由人决定暂存、提交和推送；如果工具在没有授权时改写 Git 历史，应立即停止并检查影响范围。

本章结束时，仓库应位于 `feature/subtraction` 分支，`calculator.py` 包含尚未提交的减法函数，`notes.txt` 是未跟踪文件。可以用下面三条命令确认，然后进入下一章：

```bash
git branch --show-current
git status --short
git diff
```

继续阅读：

- [日常提交与复核流程](02-日常提交与复核流程.md)
- [分支、合并与安全恢复](03-分支合并与安全恢复.md)
- [Pull Request 与多人协作](04-Pull-Request与多人协作.md)
