# 01 `pwd`、`ls` 与 `cd`

终端导航可以先记成三个问题：

```text
pwd    我现在在哪里
ls     这里有什么
cd     我要去哪里
```

它们看起来简单，却贯穿几乎所有后续操作。启动 AI CLI、删除文件、运行测试、使用 Docker 或连接远程机器时，只要当前目录判断错了，后面的命令即使语法完全正确，也可能作用在错误位置。

本章继续使用这个练习目录：

```bash
mkdir -p ~/terminal-practice/navigation-demo/src
mkdir -p ~/terminal-practice/navigation-demo/docs
cd ~/terminal-practice/navigation-demo
touch README.md src/app.py docs/notes.md
```

## 1. `pwd` 显示当前工作目录

运行：

```bash
pwd
```

可能输出：

```text
/Users/NAME/terminal-practice/navigation-demo
```

`pwd` 输出的是绝对路径。它不会猜测你“准备操作哪个项目”，只报告当前 Shell 实际所在的位置。

在执行下面这些操作前，值得再看一次 `pwd`：

- 删除、覆盖或批量移动文件；
- 启动 Claude Code、Codex CLI 或 Grok CLI；
- 运行训练脚本；
- 创建 Git 仓库；
- 使用 Docker Bind Mount；
- 通过 SSH 操作远程机器。

提示符有时会显示当前目录，但主题可能只显示最后一层名称，甚至完全隐藏路径。需要准确判断时，以 `pwd` 输出为准。

## 2. `ls` 查看目录内容

最简单的形式：

```bash
ls
```

在练习目录中可能看到：

```text
README.md  docs  src
```

查看详细信息：

```bash
ls -l
```

可能看到：

```text
-rw-r--r--  1 NAME  staff   0 Jul 29 10:00 README.md
drwxr-xr-x  3 NAME  staff  96 Jul 29 10:00 docs
drwxr-xr-x  3 NAME  staff  96 Jul 29 10:00 src
```

每行开头的第一个字符可以帮助判断对象类型：`-` 常表示普通文件，`d` 表示目录，`l` 表示符号链接。后面还会显示权限、所有者、大小和修改时间。

显示隐藏文件：

```bash
ls -a
```

详细显示并包含隐藏文件：

```bash
ls -la
```

文件大小使用更易读的单位：

```bash
ls -lh
ls -lah
```

`-l`、`-a` 和 `-h` 可以组合。不要只背组合形式，知道每个选项的作用后，遇到其他命令的选项也更容易理解。

## 3. 查看其他目录时不必先进入

可以直接查看一个路径：

```bash
ls -la src
ls -la ~/Downloads
```

这不会改变当前工作目录。运行后再执行：

```bash
pwd
```

你仍然位于原目录。

这种方式适合在切换前确认目标是否存在。例如准备进入某个项目：

```bash
ls -ld ~/Projects/my-project
```

`-d` 会显示目录对象本身，而不是列出目录内部内容。目标不存在时会直接报错，此时不要继续执行 `cd` 或其他写操作。

## 4. `cd` 改变当前工作目录

进入 `src`：

```bash
cd src
pwd
```

输出应类似：

```text
/Users/NAME/terminal-practice/navigation-demo/src
```

回到上一级：

```bash
cd ..
pwd
```

回到主目录：

```bash
cd ~
pwd
```

返回上一次所在目录：

```bash
cd -
```

`cd -` 通常会把新目录打印出来，适合在两个目录之间来回切换。

没有参数的 `cd` 通常也会回到主目录：

```bash
cd
```

为了让教程和脚本意图更清楚，本书通常写 `cd ~` 或使用完整目标路径。

## 5. 用 Tab 补全减少拼写错误

回到练习目录：

```bash
cd ~/terminal-practice/navigation-demo
```

输入：

```text
cd s
```

先不要回车，按 Tab。若只有 `src` 匹配，zsh 会补全为：

```text
cd src/
```

如果存在多个以 `s` 开头的目录，zsh 可能显示候选。继续输入直到目标唯一，再按 Tab。

补全的价值不只是少打几个字符。它还能帮助验证路径是否真实存在。一个完全无法补全的路径，应该先检查当前位置和拼写，而不是继续凭记忆输入。

## 6. 路径中有空格时要加引号

在练习目录中创建：

```bash
mkdir "My Project"
```

错误写法：

```bash
cd My Project
```

Shell 会把它理解为两个参数，通常显示：

```text
cd: string not in pwd: My
```

或其他参数错误。正确写法：

```bash
cd "My Project"
```

也可以使用反斜杠：

```bash
cd My\ Project
```

实际使用时优先依赖 Tab 补全，它会帮助处理空格和特殊字符。

## 7. `no such file or directory` 时不要连续猜路径

故意运行：

```bash
cd missing-folder
```

会看到类似：

```text
cd: no such file or directory: missing-folder
```

目录切换失败后，当前目录通常没有变化。按下面顺序检查：

```bash
pwd
ls -la
ls -ld missing-folder
```

常见原因包括：

- 路径拼错；
- 当前目录不是你以为的位置；
- 文件名大小写不同；
- 路径有空格但没有加引号；
- 目标已被移动或删除；
- 目标位于另一台机器或容器中。

先确认事实，再改命令。反复输入相似路径通常只会增加混乱。

## 8. `not a directory` 表示目标可能是文件

在项目根目录运行：

```bash
cd README.md
```

会得到类似：

```text
cd: not a directory: README.md
```

`README.md` 存在，但它是文件，不是目录。检查对象类型：

```bash
ls -ld README.md
file README.md
```

如果想查看文件内容，使用 `cat`、`less` 或编辑器，而不是 `cd`。

## 9. 相对路径和绝对路径怎样配合

当前位于：

```text
/Users/NAME/terminal-practice/navigation-demo/docs
```

进入同级的 `src` 可以写：

```bash
cd ../src
```

也可以使用绝对路径：

```bash
cd ~/terminal-practice/navigation-demo/src
```

相对路径适合在项目内部移动，绝对路径适合明确指定固定位置。命令需要发给别人或跨机器使用时，要注意绝对路径中的用户名和主目录位置可能不同。

## 10. 一套进入项目的固定流程

假设项目位于：

```text
~/Projects/my-project
```

先检查目标：

```bash
ls -ld ~/Projects/my-project
```

再进入并确认：

```bash
cd ~/Projects/my-project
hostname
pwd
ls -la
git status
```

如果 `git status` 显示正常分支和工作区状态，再启动：

```bash
claude
```

或：

```bash
codex
```

不要把 `cd` 和启动 Agent 写成一条自己看不懂的复杂命令。第一次操作时分开执行，每一步都能看见结果，更容易发现目录错误。

## 11. 远程终端中的相同命令影响另一台机器

通过 SSH 登录 Ubuntu 后，同样可以运行：

```bash
hostname
pwd
ls -la
```

但输出可能是：

```text
gpu-laptop
/home/NAME/projects/demo
```

此时 `cd`、`ls` 和后续文件操作全部发生在远程 Ubuntu。终端窗口仍在 Mac 桌面上，不表示命令仍在 Mac 执行。

从远程返回本地通常使用：

```bash
exit
```

退出后再次运行 `hostname`，确认自己已经回到本机。

## 12. 导航练习

从任意位置开始：

```bash
cd ~/terminal-practice/navigation-demo
pwd
ls -la
cd docs
pwd
ls -la
cd ../src
pwd
ls -la
cd -
pwd
```

练习时每次切换后都运行 `pwd`。熟悉以后可以减少次数，但在删除、远程和 AI Agent 场景中，仍应主动确认。

继续阅读：

- [文件系统、目录与路径](../Part-01-基础篇/05-文件系统目录与路径.md)
- [创建、复制、移动与删除](02-创建复制移动与删除.md)
- [命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
