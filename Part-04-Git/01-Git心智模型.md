# 01 Git 心智模型

Git 经常和 GitHub 一起出现，因此新手容易把它理解成“上传代码的工具”。实际上，Git 首先在本地工作：它记录文件变化，把一组经过选择的修改保存成提交，并允许你创建分支、比较历史和恢复已记录内容。即使电脑没有联网，绝大多数 Git 操作仍然可用。

本章通过一个小项目观察 Git 的三个本地层次：工作区、暂存区和提交历史。远程仓库与 Pull Request 放到后续章节。

## 1. 建立练习仓库

创建独立目录：

```bash
mkdir -p ~/terminal-practice/git-workflow-demo
cd ~/terminal-practice/git-workflow-demo
pwd
```

初始化 Git：

```bash
git init
```

可能看到：

```text
Initialized empty Git repository in /Users/NAME/terminal-practice/git-workflow-demo/.git/
```

`.git` 是 Git 保存提交对象、分支引用和仓库配置的隐藏目录。不要手工修改或删除其中内容。查看当前状态：

```bash
git status
```

空仓库通常显示当前分支还没有提交，并提示没有可提交内容。

如果第一次提交时 Git 提示缺少作者姓名和邮箱，请按提示配置自己的身份。身份会写进提交记录，不等同于 GitHub 登录密码，也不应使用别人的信息。

## 2. 工作区是你正在编辑的文件

创建两个文件：

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
```

运行测试：

```bash
python3 -m unittest -v
```

再查看状态：

```bash
git status --short
```

可能看到：

```text
?? calculator.py
?? test_calculator.py
```

`??` 表示未跟踪文件。文件已经存在于磁盘，也可以正常运行，但 Git 还没有把它们纳入任何提交。此时它们只属于工作区。

工作区就是当前检出的项目文件。编辑器、终端和 AI CLI 直接修改的都是工作区。Git 不会因为文件出现在项目目录里就自动记录它。

## 3. 暂存区决定下一次提交包含什么

把两个文件加入暂存区：

```bash
git add calculator.py test_calculator.py
```

查看状态：

```bash
git status
```

它们会出现在“Changes to be committed”下。查看暂存内容：

```bash
git diff --cached
```

这里显示的差异，就是下一次 `git commit` 准备记录的内容。

可以把暂存区理解成一次提交的候选清单，但它不只是文件名列表。Git 暂存的是文件当时的具体内容。如果暂存后又继续编辑同一文件，旧内容留在暂存区，新变化留在工作区。

做一个观察实验：

```bash
git add calculator.py
printf '%s\n' '' '# Supports basic integer addition.' >> calculator.py
git status
```

同一个文件可能同时出现在“已暂存”和“未暂存”区域。分别查看：

```bash
git diff --cached -- calculator.py
git diff -- calculator.py
```

第一条显示已放进下一次提交的版本，第二条显示暂存后又发生的变化。这是理解暂存区最直观的例子。

先把最新内容也加入暂存区：

```bash
git add calculator.py test_calculator.py
```

## 4. 提交把暂存区记录进本地历史

创建第一次提交：

```bash
git commit -m "feat: add basic calculator"
```

提交成功后查看：

```bash
git status
git log --oneline --decorate -5
```

可能看到：

```text
abc1234 (HEAD -> main) feat: add basic calculator
```

哈希值会因仓库而异。提交只发生在本机 `.git` 中，没有自动上传到 GitHub。

可以把本地流程写成：

```text
工作区
→ git add 选择具体内容
→ 暂存区
→ git commit 记录快照
→ 本地提交历史
```

`git status` 告诉你三个层次当前分别有什么内容，`git diff` 查看工作区与暂存区的差异，`git diff --cached` 查看暂存区与最近提交的差异。

## 5. 暂存区为什么不能省略

继续创建一份个人笔记，同时修改功能：

```bash
printf '%s\n' 'Remember to improve error messages.' > notes.txt
cat >> calculator.py <<'PY'


def subtract(left, right):
    return left - right
PY
```

查看：

```bash
git status --short
```

可能得到：

```text
 M calculator.py
?? notes.txt
```

假设这次提交只想记录减法功能，个人笔记不应进入历史。可以只暂存源码：

```bash
git add calculator.py
git diff --cached
git status
```

`notes.txt` 仍留在工作区，下一次提交不包含它。暂存区让一个混杂的工作目录仍然可以形成主题明确的提交。

这也是为什么新手不应把 `git add .` 当作永远正确的默认动作。它会把当前目录下所有符合条件的变化一起加入，包括日志、缓存、临时文件、无关格式化和意外出现的敏感配置。精确指定文件更容易审查。

暂存错了但想保留工作区修改时：

```bash
git restore --staged calculator.py
```

这只把文件移出暂存区，不会删除刚写的代码。

## 6. Commit、分支和 HEAD

Git 的提交形成有父子关系的历史。第一次提交可以记作 A，第二次提交会指向 A：

```text
A ← B
```

分支是一个会随着提交向前移动的名字，`HEAD` 表示当前检出位置，通常指向当前分支：

```text
A ← B
    ↑
   main
    ↑
   HEAD
```

查看当前分支和提交：

```bash
git branch --show-current
git rev-parse --short HEAD
git log --oneline --decorate --graph -10
```

创建任务分支：

```bash
git switch -c feature/subtraction
```

分支并不是复制一份完整项目目录，而是建立一个新的提交指针，因此创建很快。后续提交会让 `feature/subtraction` 向前移动，而 `main` 仍停在原来的提交。

当前工作区还有未提交修改，先不要提交；下一章会从这里继续完整的日常流程。

## 7. Git、GitHub 和远程仓库的区别

Git 是本地版本控制系统。GitHub、GitLab 和其他平台可以托管 Git 仓库，并提供账号权限、Pull Request、Issue 和自动化检查。

本地无需联网即可执行：

```bash
git status
git diff
git add
git commit
git branch
git log
```

与远程通信的操作包括：

```bash
git fetch
git pull
git push
```

查看当前仓库是否配置远程：

```bash
git remote -v
```

本练习仓库还没有远程，所以没有输出是正常的。`origin` 只是远程名称的常见约定，不是 GitHub 专属关键字。

## 8. Git 能恢复什么，不能恢复什么

Git 擅长恢复已经跟踪并进入提交历史的文件，也能帮助找回部分仍有引用记录的提交。但它不能自动恢复从未提交过的未跟踪文件，也不能撤销已经发送到网络的数据、数据库写入、云资源操作、Docker Volume 或项目目录之外的变化。

例如当前的 `notes.txt` 尚未跟踪。如果直接从磁盘删除，Git 通常没有任何副本可以恢复。这说明“项目使用 Git”并不等于所有操作都有撤销按钮。

提交前可以问：

```text
这个文件是否已被 Git 跟踪？
当前修改是否已暂存？
是否已经形成提交？
提交是否已经共享到远程？
```

问题所处层次不同，恢复方法也不同。

## 9. AI CLI 参与项目时的最低边界

Agent 开始工作前，人工先运行：

```bash
git status
git branch --show-current
```

再给出明确限制：

```text
只修改当前任务需要的工作区文件。
不要执行 git add、commit、push、merge、rebase、reset 或 clean。
完成后列出全部变更文件、测试命令和未验证内容。
```

结束后人工检查：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Agent 的总结只能说明它认为自己做了什么，Git 差异才是工作区实际发生的变化。

## 10. 本章练习状态

此时仓库应处于 `feature/subtraction` 分支，`calculator.py` 有尚未提交的减法函数，`notes.txt` 是未跟踪文件。检查：

```bash
git branch --show-current
git status --short
git diff
```

下一章会在这个状态上补测试、精确暂存、创建提交并复核结果。

继续阅读：

- [日常提交与复核流程](02-日常提交与复核流程.md)
- [分支、合并与安全恢复](03-分支合并与安全恢复.md)
- [Pull Request 与多人协作](04-Pull-Request与多人协作.md)
