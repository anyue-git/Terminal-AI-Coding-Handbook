# 04 zsh 到底是什么

zsh 是 macOS 当前常见的默认 Shell。它负责解释命令、显示提示符、保存历史、补全路径、展开通配符，并通过自己的行编辑器处理 `Ctrl + A`、`Ctrl + U`、`Ctrl + R` 等快捷键。

很多人会把这些能力统称为“终端功能”，但它们实际上来自不同层：Terminal 负责窗口和键盘输入，zsh 负责命令解析和行编辑，主题与插件再在 zsh 之上改变提示符、补全和快捷键。分清这些层以后，遇到快捷键失效、命令找不到或终端启动报错时，排查会更有方向。

## 1. 先确认当前真的是 zsh

查看登录 Shell：

```bash
echo "$SHELL"
```

查看当前进程：

```bash
ps -p $$ -o pid,ppid,comm=
```

再查看版本：

```bash
zsh --version
```

典型输出类似：

```text
zsh 5.9 (arm64-apple-darwin...)
```

如果你在容器、远程 Ubuntu、脚本或某个 IDE 中，当前进程可能不是 zsh。不要只根据 Mac 默认值推断，先看实际输出。

## 2. ZLE 负责普通提示符中的输入编辑

ZLE 是 Zsh Line Editor。你在普通 zsh 提示符中移动光标、删除单词、搜索历史时，通常就是 ZLE 在工作。

查看常见按键绑定：

```bash
bindkey '^A'
bindkey '^E'
bindkey '^U'
bindkey '^W'
bindkey '^R'
```

可能看到：

```text
"^A" beginning-of-line
"^E" end-of-line
"^U" kill-whole-line
"^W" backward-kill-word
"^R" history-incremental-search-backward
```

插件、Vi 模式和个人配置都可能改变结果，因此本机 `bindkey` 输出比网上的通用速查表更可靠。

临时切换到常见 Emacs 键位：

```bash
bindkey -e
```

这只影响当前 Shell 会话。确认符合预期后，再决定是否写入配置文件。不要为了修一个快捷键，把网上整套配置不加检查地追加到 `.zshrc`。

## 3. `.zshrc` 不是普通文本备忘录

交互式 zsh 常读取：

```text
~/.zshrc
```

里面可能包含 PATH、别名、函数、补全、提示符、插件、Python/Node 初始化和 API 相关环境变量。每次打开新的交互式 zsh，这些内容都可能被执行。

修改前先查看文件是否存在：

```bash
ls -l ~/.zshrc
```

建立本地备份：

```bash
cp ~/.zshrc ~/.zshrc.backup-before-edit
```

如果文件不存在，`cp` 会报错；这不代表系统异常，只说明还没有用户级 `.zshrc`。

编辑后先做语法检查：

```bash
zsh -n ~/.zshrc
```

没有输出通常表示没有发现语法错误。它不能保证每个命令在运行时都成功，但能发现未闭合引号、括号等基础问题。

重新加载当前会话：

```bash
source ~/.zshrc
```

`source` 会立即执行文件中的内容。出现报错后不要连续重复执行，先看报错行号并修复。更稳妥的验证方式是打开一个新的终端窗口；这样当前可用的 Shell 仍然保留，出问题时更容易恢复。

## 4. `.zprofile`、`.zshrc` 和其他启动文件有什么区别

macOS 上常见的两个文件是：

```text
~/.zprofile    登录 Shell 初始化，常用于 PATH 和 Homebrew shellenv
~/.zshrc       每个交互式 zsh 会话读取，常用于提示符、别名、插件和快捷键
```

zsh 还支持 `.zshenv`、`.zlogin`、`.zlogout` 等文件，但新手不需要一开始就把配置分散到所有位置。很多“Terminal 能运行，VS Code 集成终端不能运行”的问题，就是不同启动方式读取了不同文件，或者同一段 PATH 初始化在多个文件中重复执行。

检查文件中是否重复设置某个工具：

```bash
grep -n 'homebrew\|pyenv\|nvm\|ANTHROPIC\|OPENAI' \
  ~/.zprofile ~/.zshrc 2>/dev/null
```

输出中的行号可以帮助你定位来源。涉及 API Key 时不要把完整配置文件发到公开聊天或 Issue；先隐藏变量值，只说明变量名称和所在文件。

## 5. Tab 补全既省输入，也能验证路径

在主目录中输入：

```text
cd Dow
```

先不要回车，按 Tab。若存在 `Downloads`，zsh 可能补全为：

```text
cd Downloads/
```

如果有多个匹配项，它可能显示候选或等待你继续输入。补全不仅减少拼写错误，也是在确认目标真实存在。

路径含空格时，补全通常会自动处理转义。例如目录 `My Project` 可能显示为：

```text
My\ Project/
```

或者在引号中补全。不要因为看到反斜杠就手工删除；它用于告诉 Shell 空格属于文件名的一部分。

## 6. 历史记录很方便，也可能保存秘密

方向键上、下可以浏览最近命令，`Ctrl + R` 可以按关键词反向搜索。搜索到历史命令后，先检查路径、地址和参数，再决定是否执行；旧命令可能指向已经变化的服务器、目录或分支。

zsh 历史文件常见位置：

```text
~/.zsh_history
```

查看文件元数据即可：

```bash
ls -l ~/.zsh_history
```

不要在命令行直接粘贴长期有效的 API Key、Cookie、Session 或 Refresh Token。即使执行 `clear`，历史文件仍可能保留命令文字。更安全的方式是使用系统凭证库、密码管理器、工具官方登录流程或不回显输入的临时变量。

如果已经误把秘密输入终端，不要只删除一条历史记录就认为问题结束。凭证可能同时出现在终端滚动区、日志、同步工具和截图中，应当按供应商流程撤销或轮换。

## 7. alias 适合透明的短替换

定义一个临时别名：

```bash
alias ll='ls -la'
```

查看来源：

```bash
type ll
```

输出可能是：

```text
ll is an alias for ls -la
```

alias 适合短、清楚、没有复杂参数处理的替换。不要把高风险命令包装成含义模糊的短名称，也不要让别名悄悄加入管理员权限或强制参数。

需要参数、条件和错误处理时，函数或独立脚本更合适。例如，一个只负责进入固定项目并检查状态的函数可以写得很清楚：

```bash
cddemo() {
  cd "$HOME/Projects/demo" || return
  pwd
  git status
}
```

写入 `.zshrc` 前先在当前终端临时定义并测试，确认目录和输出符合预期。

## 8. 通配符会在命令运行前展开

zsh 常见通配符：

```text
*      匹配任意数量字符
?      匹配一个字符
[]     匹配字符集合
```

例如：

```bash
printf '%s\n' *.py
```

会把当前目录中的 Python 文件逐行打印出来。没有匹配时，zsh 通常显示：

```text
zsh: no matches found: *.py
```

这与 Bash 的默认行为可能不同。通配符用于查看文件很方便，但用于删除、移动、上传、同步和修改权限时会扩大影响范围。先用 `printf`、`ls` 或工具的 dry run 查看展开结果，再执行写操作。

## 9. PATH 修改应当可解释、可检查

很多安装教程要求把目录加入 PATH。例如：

```bash
export PATH="$HOME/bin:$PATH"
```

这表示优先在 `~/bin` 中寻找程序，然后再搜索原有 PATH。修改后检查：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
type -a COMMAND
```

不要反复把同一目录追加到 `.zprofile`、`.zshrc` 和工具自动生成的脚本中。PATH 重复通常不会立刻报错，但会让命令来源更难判断。

使用 Homebrew、pyenv、Conda、nvm 或其他环境管理器时，先确认它们各自修改了哪些路径和启动文件。出现版本混乱时，`type -a python3`、`type -a node` 和 `type -a codex` 比继续安装新副本更有用。

## 10. AI 工具的环境变量可能来自 zsh 配置

Claude Code、Codex 和第三方管理工具可能通过环境变量设置 Base URL、API Key、Token 或状态目录。变量写入 `.zshrc` 后，每个新终端都会自动继承。

只查看相关变量名称，不显示秘密正文：

```bash
env | grep -E '^(CODEX_HOME|OPENAI_|ANTHROPIC_|CLAUDE_CODE_)' \
  | sed 's/=.*$/=<已设置>/'
```

如果你已经切回官方登录，但客户端仍然访问旧网关，检查 `.zshrc`、`.zprofile` 和管理工具生成的启动脚本中是否还保留 `ANTHROPIC_BASE_URL`、认证变量或自定义 `CODEX_HOME`。

这也是配置管理工具必须单独学习的原因：界面中的一次切换，背后可能改写 TOML、JSON、环境变量或系统凭证库。

## 11. zsh 启动报错时怎样恢复

假设新开终端后看到：

```text
/Users/NAME/.zshrc:42: unmatched "
```

先不要重装 Terminal。错误已经指出 `.zshrc` 第 42 行附近存在未闭合引号。可以查看附近内容：

```bash
nl -ba ~/.zshrc | sed -n '35,48p'
```

修复后运行：

```bash
zsh -n ~/.zshrc
```

如果当前终端因为配置错误无法正常使用，可以启动一个不读取普通用户启动文件的 zsh：

```bash
zsh -f
```

在这个临时 Shell 中修复文件，或将之前的备份恢复为另一个名称后再比较。恢复整个配置前先确认备份时间，避免覆盖后来仍然需要的正常修改。

## 12. 一套实用排查命令

```bash
echo "$SHELL"
ps -p $$ -o comm=
zsh --version
zsh -n ~/.zshrc
bindkey '^U'
type -a COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

这些命令分别检查 Shell、语法、按键和命令路径。遇到终端启动报错、快捷键变化或命令突然消失时，先确定是哪一层发生变化，再决定是否修改配置。

继续阅读：

- [命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
- [Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)
- [配置、凭证、供应商与实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)
