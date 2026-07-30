# 01 `pwd`、`ls` 与 `cd`

终端导航可以记成三个问题：`pwd` 回答“我现在在哪里”，`ls` 回答“这里有什么”，`cd` 回答“我要去哪里”。它们贯穿启动 AI CLI、删除文件、运行测试、使用 Docker 和连接远程机器等所有后续操作；当前目录判断错了，命令语法即使完全正确，也可能作用在错误位置。

本章使用一个独立练习目录：

```bash
mkdir -p ~/terminal-practice/navigation-demo/src
mkdir -p ~/terminal-practice/navigation-demo/docs
cd ~/terminal-practice/navigation-demo
touch README.md src/app.py docs/notes.md
```

## 1. 用 `pwd` 和 `ls` 建立当前现场

运行：

```bash
pwd
ls
ls -la
```

`pwd` 会输出类似 `/Users/NAME/terminal-practice/navigation-demo` 的绝对路径。`ls` 可能显示 `README.md`、`docs` 和 `src`，`ls -la` 还包含隐藏对象与详细信息。长格式每行开头的 `-` 常表示普通文件，`d` 表示目录，`l` 表示符号链接；后面还包括权限、所有者、大小和修改时间。

常见选项可以组合：`-l` 显示详情，`-a` 包含隐藏文件，`-h` 使用较易读的大小单位。提示符有时只显示最后一层目录，甚至完全隐藏路径，需要准确判断时以 `pwd` 为准。

查看其他目录不必先进入：

```bash
ls -la src
ls -la ~/Downloads
ls -ld ~/Projects/my-project
```

这些命令不会改变当前目录。`ls -ld` 显示目录对象本身，适合在切换前确认目标是否存在；运行后再次执行 `pwd`，仍会看到原来的位置。

## 2. 用 `cd` 在目录树中移动，并让补全验证目标

在练习目录中依次尝试：

```bash
cd src
pwd
cd ..
pwd
cd ~
pwd
cd -
pwd
```

`cd src` 进入子目录，`cd ..` 返回上一级，`cd ~` 或不带参数的 `cd` 回到主目录，`cd -` 切换到上一次所在目录并通常打印新路径。相对路径从当前目录计算，绝对路径明确指定固定位置；在项目内部移动常用相对路径，跨较远目录或希望意图清楚时可以使用 `$HOME` 或完整路径。

回到练习根目录，输入 `cd s` 但不按回车，再按 Tab。如果只有 `src` 匹配，zsh 会补全为 `cd src/`；存在多个候选时，继续输入到目标唯一。补全不仅减少键入，也在确认当前目录中确实存在目标。

## 3. 空格、对象类型和路径错误都要回到现实目录判断

创建并进入一个含空格的目录：

```bash
cd ~/terminal-practice/navigation-demo
mkdir "My Project"
cd "My Project"
```

写成 `cd My Project` 时，Shell 会把它拆成多个参数。也可以写 `cd My\ Project`，实际操作时优先依赖 Tab 补全。

`cd` 只能进入目录。运行：

```bash
cd README.md
```

会得到类似 `not a directory` 的错误，因为文件存在但不是目录。使用下面两条命令确认对象类型：

```bash
ls -ld README.md
file README.md
```

查看文件内容应使用 `cat`、`less` 或编辑器，而不是 `cd`。

再故意运行：

```bash
cd missing-folder
```

看到 `no such file or directory` 后，当前目录通常没有变化。检查现场：

```bash
pwd
ls -la
ls -ld missing-folder
```

常见原因包括拼写或大小写错误、当前目录与预期不同、路径中空格未加引号、目标已移动，或者目标位于另一台机器或容器。确认事实以后再修正命令；连续猜测相似路径只会增加混乱，`sudo` 也不能修复路径不存在或对象类型错误。

## 4. 进入真实项目时把导航与启动动作分开

假设项目位于 `~/Projects/my-project`，查看目标、进入目录并建立现场：

```bash
ls -ld ~/Projects/my-project
cd ~/Projects/my-project
hostname
pwd
ls -la
git status
```

`git status` 显示正常分支和工作区后，再启动 `claude`、`codex` 或其他 Agent。第一次操作时把 `cd` 和启动工具分开执行，每一步都能观察结果，比一条自己无法解释的复合命令更容易发现目录错误。

通过 SSH 登录 Ubuntu 后，同样的 `pwd`、`ls` 和 `cd` 全部作用于远程机器。若输出是 `gpu-laptop` 和 `/home/NAME/projects/demo`，终端窗口虽然还在 Mac 桌面，文件操作已经发生在 Ubuntu。退出远程 Shell 使用 `exit`，随后运行 `hostname` 确认回到本机。

最后完成一轮导航练习：

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

练习阶段每次切换后都运行 `pwd`。熟悉以后可以减少次数，但在删除、远程和 AI Agent 场景中仍应主动确认机器和目录。

继续阅读：[文件系统、目录与路径](../Part-01-基础篇/05-文件系统目录与路径.md)、[创建、复制、移动与删除](02-创建复制移动与删除.md)和[命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)。
