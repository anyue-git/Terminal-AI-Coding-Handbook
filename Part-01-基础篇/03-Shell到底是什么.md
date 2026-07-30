# 03 Shell 到底是什么

Terminal 是窗口，Shell 是在这个窗口中理解并执行命令的程序。macOS 现在通常使用 zsh，Linux 教程中经常出现 Bash。你在提示符后输入一行内容并按回车时，Shell 会分析文字，决定调用哪个程序、传入哪些参数，以及怎样展开变量、通配符、管道和重定向。

例如：

```bash
ls -la ~/Downloads
```

Shell 会把它理解为 `ls` 命令、`-la` 选项和 `~/Downloads` 参数，并把 `~` 展开成当前用户主目录。处理完成后，它找到 `ls` 程序并启动，把输出交给 Terminal 显示。理解这一层，很多“同一条命令为什么在两台机器上结果不同”的问题就更容易定位。

## 1. 确认当前 Shell 和命令来源

查看登录 Shell 与当前进程：

```bash
echo "$SHELL"
ps -p $$ -o pid,ppid,comm=
```

`$SHELL` 常显示 `/bin/zsh`，当前进程通常也是 zsh，但两者不一定永远一致。你可能从 zsh 临时启动 Bash，也可能进入容器、远程机器或某个程序的交互界面。遇到语法、快捷键或配置差异时，实际输出比提示符外观更可信。

Shell 既有内建命令，也会启动外部程序。`cd` 通常是内建命令，因为切换目录必须改变 Shell 自己维护的工作目录；`ls`、`git`、`python3` 和 `codex` 通常是外部程序。使用 `type` 可以同时识别内建、别名、函数和外部文件：

```bash
type cd
type ls
type git
type -a python3
type -a claude
```

同一个工具出现多个路径时，先弄清 PATH 顺序、别名或函数，以及每个版本来自哪里。继续安装新的副本往往只会让来源更难判断。

## 2. PATH 决定 Shell 找到哪个程序

输入 `codex` 时，Shell 会依次搜索 `PATH` 中的目录。可以把 PATH 分行查看：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
```

越靠前的目录通常越先被搜索。检查当前会使用哪个文件：

```bash
command -v codex
type -a codex
```

出现 `zsh: command not found: codex`，常见原因是工具尚未安装、安装目录不在 PATH、当前终端没有重新加载配置、命令名拼错，或工具安装在另一套 Node/Python/用户环境中。调查命令来源和搜索路径，通常比重复安装更容易找到根因。

PATH 修改也应当可解释。例如：

```bash
export PATH="$HOME/bin:$PATH"
```

表示优先搜索 `~/bin`，然后保留原有路径。不要在 `.zprofile`、`.zshrc` 和工具初始化脚本里反复追加同一目录；短期可能仍能运行，长期会让版本来源难以判断。

## 3. Shell 会在程序启动前展开特殊字符

运行：

```bash
ls *.md
```

通常是 zsh 把 `*.md` 展开为当前目录中的真实文件名，再交给 `ls`，并非 `ls` 自己搜索 Markdown 文件。删除、移动、上传或修改权限时，通配符会放大影响范围，可以先用只读命令预览：

```bash
printf '%s\n' *.md
```

zsh 没有匹配时常显示 `zsh: no matches found: *.md`。它说明模式没有展开，不代表文件系统损坏，也不需要为了消除提示而随意关闭保护行为。

引号决定哪些内容由 Shell 展开。双引号允许变量展开：

```bash
printf '%s\n' "$HOME"
```

单引号尽量保留文字本身：

```bash
printf '%s\n' '$HOME'
```

路径含空格时需要引号，路径变量也通常要使用双引号：

```bash
SOURCE_FILE="$HOME/My Project/notes.md"
BACKUP_DIR="$HOME/Backups"
cp "$SOURCE_FILE" "$BACKUP_DIR/"
```

省略引号后，Shell 可能按空格拆分变量，甚至再次展开其中的通配符。除非明确需要字段拆分，否则路径变量加双引号应成为默认习惯。

## 4. 管道和重定向由 Shell 组织数据流

Shell 可以把输出写入文件或交给另一个程序。下面的 `>` 会创建或覆盖 `message.txt`，`>>` 则追加：

```bash
printf 'hello\n' > message.txt
printf 'second line\n' >> message.txt
cat message.txt
```

管道 `|` 把左侧程序的标准输出作为右侧程序的标准输入：

```bash
printf 'pear\napple\nbanana\n' | sort
```

命令越来越复杂时，可以分别运行各部分并观察中间结果。条件、错误处理和复用较多时，独立脚本或程序通常比一条超长命令更容易阅读和验证。

命令连接符也表达不同逻辑：

```bash
python3 -m unittest && git status
python3 -m unittest; git status
```

`&&` 只有在测试成功退出时才执行下一条，`;` 则无论前一条是否成功都会继续。写在同一行不代表这些操作具有事务或自动回滚能力。

## 5. 环境变量会影响子程序和 AI 客户端

普通 Shell 变量只属于当前 Shell；使用 `export` 后，后续启动的子程序通常可以读取：

```bash
PROJECT_NAME="demo"
export PROJECT_NAME
python3 -c 'import os; print(os.environ.get("PROJECT_NAME"))'
```

API Key、Base URL、`CODEX_HOME` 等配置经常通过环境变量传递，而且可能覆盖 TOML 或 JSON 中的设置。出现“配置文件已经改了，客户端却仍连接旧端点”时，需要检查当前 Shell 中是否存在更高优先级的变量。

检查时不要打印秘密正文，可以只显示名称和“已设置”状态：

```bash
env | grep -E '^(CODEX_HOME|OPENAI_|ANTHROPIC_|CLAUDE_CODE_)' \
  | sed 's/=.*$/=<已设置>/'
```

环境变量会被子进程继承，也可能进入日志、调试输出和进程环境。长期凭证更适合官方登录流程、系统凭证库或专门的 Secret 管理方式，而不是反复写入 Shell 历史和公开脚本。

## 6. Shell 与 AI CLI 是嵌套的两层程序

在普通提示符中运行 `claude` 或 `codex` 时，Shell 根据 PATH 找到并启动客户端。客户端启动后接管键盘输入，Prompt 不会被 zsh 直接执行；当 Agent 需要运行测试时，它又会在当前系统、目录和权限环境中启动 Shell 命令。

因此，AI CLI 仍受当前目录、PATH、用户权限、环境变量、网络、Sandbox 和审批规则影响。Agent 没有脱离操作系统获得更高权限。退出客户端回到普通提示符后，按键和命令解释权才重新交给 zsh。

## 7. 命令异常时按层定位

命令无法运行时，可以依次确认：当前焦点是否在普通 Shell，当前 Shell 是什么，这个名称是内建、别名、函数还是外部程序，PATH 会选择哪个文件，参数、引号和通配符如何展开，以及当前目录与权限是否合适。

常用只读命令包括：

```bash
pwd
ps -p $$ -o comm=
type -a COMMAND
command -v COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

定位到具体层以后，再决定修改配置、调整 PATH、修正参数或重新安装。这样处理，比一遇到报错就重装所有工具更容易保留清楚的现场。

继续阅读：[zsh 到底是什么](04-zsh到底是什么.md)、[Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)和[管道、重定向与命令组合](../Part-02-终端命令/05-管道重定向与命令组合.md)。