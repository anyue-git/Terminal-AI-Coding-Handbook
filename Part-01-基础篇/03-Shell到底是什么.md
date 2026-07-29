# 03 Shell 到底是什么

Terminal 是窗口，Shell 是在这个窗口中理解并执行命令的程序。macOS 现在通常使用 zsh；Linux 教程中经常出现 Bash。你在提示符后输入一行内容并按回车时，Shell 会先分析这行文字，再决定调用哪个程序、传入哪些参数，以及是否需要展开变量、通配符或重定向。

例如：

```bash
ls -la ~/Downloads
```

Shell 会把它拆成几部分：

```text
ls              命令
-la             选项
~/Downloads     参数，其中 ~ 会展开为当前用户主目录
```

完成处理后，Shell 找到 `ls` 程序并启动它，再把输出交给 Terminal 显示。理解这一层以后，很多“同一条命令为什么在两台机器上结果不同”的问题会更容易定位。

## 1. 先确认自己正在使用哪个 Shell

查看登录 Shell：

```bash
echo "$SHELL"
```

常见输出：

```text
/bin/zsh
```

查看当前 Shell 进程：

```bash
ps -p $$ -o pid,ppid,comm=
```

可能看到：

```text
  PID  PPID
48321 48290 zsh
```

登录 Shell 和当前进程通常一致，但并非永远如此。你可能从 zsh 中临时启动 Bash，也可能进入容器、远程机器或某个程序自己的交互界面。遇到语法、快捷键或配置差异时，先确认当前到底由谁处理输入。

## 2. Shell 内建命令和外部程序有什么区别

`cd` 通常是 Shell 内建命令，因为切换目录需要改变 Shell 自己维护的当前工作目录。如果 `cd` 只是启动一个独立程序，那个程序退出后，原来的 Shell 仍然会停在旧目录。

`ls`、`git`、`python3` 和 `codex` 通常是外部程序。可以使用 `type` 检查：

```bash
type cd
type ls
type git
type python3
```

输出可能类似：

```text
cd is a shell builtin
ls is /bin/ls
git is /usr/bin/git
python3 is /opt/homebrew/bin/python3
```

`type` 还能识别别名和函数，因此比只使用 `which` 更适合排查“我输入这个名字时到底会执行什么”。查看所有同名来源：

```bash
type -a python3
type -a claude
```

如果同一个工具出现多个路径，不要立刻继续安装。先弄清 PATH 顺序和每个版本的来源。

## 3. Shell 怎样通过 PATH 寻找程序

输入：

```bash
codex
```

Shell 会按照 `PATH` 中目录的先后顺序寻找名为 `codex` 的可执行文件。将 PATH 分行查看：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
```

输出可能包含：

```text
/opt/homebrew/bin
/usr/local/bin
/usr/bin
/bin
```

越靠前的目录通常越先被搜索。查看当前会使用哪个程序：

```bash
command -v codex
type -a codex
```

出现：

```text
zsh: command not found: codex
```

常见原因包括工具尚未安装、安装目录不在 PATH、当前终端尚未重新加载配置、命令名拼错，或工具被安装在另一套 Node/Python/用户环境中。重复安装可能制造更多副本，应先定位路径问题。

## 4. Shell 会在程序启动前处理特殊字符

运行：

```bash
ls *.md
```

通常不是 `ls` 自己去理解 `*.md`。zsh 会先在当前目录中寻找匹配的文件，把通配符展开成多个真实文件名，再交给 `ls`。

假设目录中有：

```text
README.md
notes.md
app.py
```

Shell 实际交给 `ls` 的内容接近：

```text
ls README.md notes.md
```

这解释了为什么通配符用于删除、移动或修改权限时需要格外谨慎。先用只读命令查看匹配对象：

```bash
printf '%s\n' *.md
```

zsh 在没有匹配结果时常显示：

```text
zsh: no matches found: *.md
```

它说明通配符没有展开成功，不是文件系统损坏。不要为了消除这条提示随意关闭全局保护行为。

## 5. 引号决定哪些内容由 Shell 展开

双引号通常允许变量展开：

```bash
printf '%s\n' "$HOME"
```

可能输出：

```text
/Users/NAME
```

单引号会尽量保留文字本身：

```bash
printf '%s\n' '$HOME'
```

输出：

```text
$HOME
```

路径中有空格时需要引号：

```bash
cd "My Project"
```

变量保存路径时通常也应使用双引号：

```bash
SOURCE_FILE="$HOME/My Project/notes.md"
BACKUP_DIR="$HOME/Backups"
cp "$SOURCE_FILE" "$BACKUP_DIR/"
```

如果写成：

```bash
cp $SOURCE_FILE $BACKUP_DIR/
```

Shell 可能按空格拆分变量内容，甚至再次展开其中的通配符。对于路径变量，“加双引号”应当成为默认习惯，除非你明确需要字段拆分。

## 6. 重定向和管道也由 Shell 组织

把文字写入文件：

```bash
printf 'hello\n' > message.txt
```

`>` 会创建或覆盖目标文件。追加内容使用：

```bash
printf 'second line\n' >> message.txt
```

查看结果：

```bash
cat message.txt
```

可能看到：

```text
hello
second line
```

管道 `|` 会把前一个程序的标准输出交给后一个程序。例如：

```bash
printf 'pear\napple\nbanana\n' | sort
```

输出：

```text
apple
banana
pear
```

这些符号由 Shell 建立进程和数据通道。命令越来越复杂时，建议先分别运行每一步并检查中间结果；复杂业务逻辑更适合写成有错误处理和测试的脚本或程序。

## 7. `&&`、`;` 和换行不是同一种连接方式

运行：

```bash
python3 -m unittest && git status
```

只有前一个命令成功退出时，Shell 才会执行 `git status`。这适合表达“测试通过后再查看或进行下一步”。

分号会无论前一条是否成功都继续：

```bash
python3 -m unittest; git status
```

两条命令分行输入也通常各自独立执行。不要只因为一串命令写在同一行，就认为它们具有自动回滚或事务保证。

## 8. 环境变量会传给子程序

在当前 Shell 中定义普通变量：

```bash
PROJECT_NAME="demo"
```

它默认只属于当前 Shell。使用 `export` 后，后续启动的子程序通常可以读取：

```bash
export PROJECT_NAME
python3 -c 'import os; print(os.environ.get("PROJECT_NAME"))'
```

输出：

```text
demo
```

API Key、Base URL、`CODEX_HOME` 等配置经常通过环境变量传递。环境变量可能覆盖配置文件中的设置，因此出现“明明改了 TOML/JSON 却没生效”时，需要检查当前 Shell 中是否存在更高优先级的变量。

检查变量是否存在时不要打印秘密正文。可以只显示名称：

```bash
env | grep -E '^(CODEX_HOME|OPENAI_|ANTHROPIC_)' | sed 's/=.*$/=<已设置>/'
```

## 9. Shell 与 AI CLI 是两层程序

在普通提示符中运行：

```bash
claude
```

Shell 负责根据 PATH 找到并启动 Claude Code。启动以后，Claude Code 的交互界面接管键盘输入；你输入的文字不再直接作为 zsh 命令执行。当 Agent 需要运行 `python3 -m unittest` 时，它又会在当前系统和权限环境中启动相应程序。

因此，AI CLI 的行为仍然受到当前目录、PATH、用户权限、环境变量、网络、Sandbox 和审批规则影响。Agent 不是绕过操作系统的更高权限层。

退出 AI CLI 回到普通 Shell 后，提示符和快捷键控制权才重新交给 zsh。判断“现在是谁在接收我的按键”，是理解终端交互的关键。

## 10. 命令异常时按层检查

遇到命令无法运行，可以按照下面的顺序调查：

```text
当前焦点是否在普通 Shell
→ 当前 Shell 是什么
→ 这个名称是内建、别名、函数还是外部程序
→ PATH 会选择哪个文件
→ 参数、引号和通配符怎样展开
→ 当前目录和用户权限是否正确
```

常用检查命令：

```bash
pwd
ps -p $$ -o comm=
type -a COMMAND
command -v COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

先把问题定位到具体层，再决定是修改配置、调整路径、修正参数还是重新安装。这样比一遇到报错就把所有工具重装一遍更可靠。

继续阅读：

- [zsh 到底是什么](04-zsh到底是什么.md)
- [Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)
- [管道、重定向与命令组合](../Part-02-终端命令/05-管道重定向与命令组合.md)
