# 04 zsh 到底是什么

zsh 是 macOS 当前常见的默认 Shell。它解释命令、显示提示符、保存历史、补全路径、展开通配符，并通过 ZLE（Zsh Line Editor）处理普通提示符中的光标移动和删除快捷键。很多人把这些能力都称为“终端功能”，实际上 Terminal 负责窗口与键盘输入，zsh 负责命令解析和行编辑，主题、插件和个人配置再改变提示符、补全与按键。分清这些层以后，遇到快捷键失效、命令找不到或终端启动报错时，排查会更有方向。

## 1. 确认当前 zsh 和真实按键绑定

不要只根据“Mac 默认使用 zsh”推断当前环境。运行：

```bash
echo "$SHELL"
ps -p $$ -o pid,ppid,comm=
zsh --version
```

在容器、远程 Ubuntu、脚本或 IDE 中，当前进程可能不是 zsh。登录 Shell 与当前进程也可能不同，因此语法和快捷键异常时应看实际输出。

普通 zsh 提示符中的输入编辑通常由 ZLE 负责。可以查看高频按键的真实绑定：

```bash
bindkey '^A'
bindkey '^E'
bindkey '^U'
bindkey '^W'
bindkey '^R'
```

常见 Emacs 键位会把它们绑定到行首、行尾、清理输入、删除左侧单词和反向搜索历史，但插件、Vi 模式和个人配置都可能改变结果。本机 `bindkey` 输出比网上的通用速查表更可靠。临时切换到常见 Emacs 键位可以运行 `bindkey -e`，它只影响当前会话；确认符合预期后，再决定是否写入永久配置。

## 2. `.zshrc` 会在每个交互式会话中执行

交互式 zsh 常读取 `~/.zshrc`。文件中可能包含 PATH、别名、函数、补全、提示符、插件、Python/Node 初始化和 API 相关环境变量。它不是普通备忘录，每次打开新的交互式 Shell，其中的命令都可能执行。

修改前先确认文件并建立本地备份：

```bash
ls -l ~/.zshrc
cp ~/.zshrc ~/.zshrc.backup-before-edit
```

如果文件不存在，`cp` 报错只表示还没有用户级 `.zshrc`。编辑后先做语法检查：

```bash
zsh -n ~/.zshrc
```

没有输出通常表示没有发现未闭合引号、括号等基础语法错误，但不能保证文件中的每个程序运行时都成功。`source ~/.zshrc` 会立即在当前会话执行配置，出现报错后不要连续重复；更稳妥的验证方式是保留当前可用窗口，再打开一个新终端测试。

macOS 上还常见 `~/.zprofile`，它通常用于登录 Shell 初始化和 Homebrew `shellenv`；`.zshrc` 更常用于交互式提示符、别名、插件和快捷键。zsh 还支持其他启动文件，但新手不需要把配置分散到每一层。很多“Terminal 能运行、VS Code 集成终端不能运行”的问题，来自不同启动方式读取了不同文件，或同一段 PATH 初始化被重复写入。

检查常见初始化来源：

```bash
grep -n 'homebrew\|pyenv\|nvm\|ANTHROPIC\|OPENAI' \
  ~/.zprofile ~/.zshrc 2>/dev/null
```

涉及 API Key 时不要把完整配置文件粘贴到公开聊天或 Issue，只说明变量名和所在文件，并隐藏值。

## 3. 补全和历史既提高效率，也需要复核

在主目录输入 `cd Dow` 后按 Tab，如果存在 `Downloads`，zsh 会补全目录；有多个候选时，它会显示选项或等待继续输入。补全不仅减少拼写错误，也是在确认目标真实存在。路径含空格时可能显示 `My\ Project/`，反斜杠用于告诉 Shell 空格属于文件名，不要手工删除。

方向键可以浏览最近命令，`Ctrl + R` 可以按关键词搜索较早历史。找到命令后先检查路径、服务器地址、分支名和输出目录，再决定是否执行；历史记录保存的是过去的现场，不保证现在仍然安全。zsh 历史文件常位于 `~/.zsh_history`，查看元数据即可：

```bash
ls -l ~/.zsh_history
```

不要在命令行粘贴长期有效的 API Key、Cookie、Session 或 Refresh Token。`clear` 不能删除历史文件，误输入秘密后也不能只删一条历史记录就认为风险消失；凭证可能同时出现在滚动区、日志、同步工具和截图中，应按供应商流程撤销或轮换。

## 4. alias、函数和 PATH 都应保持透明

临时别名可以写成：

```bash
alias ll='ls -la'
type ll
```

alias 适合短、清楚、没有复杂参数处理的替换，不应把高风险命令包装成含义模糊的短名称，也不要偷偷加入管理员权限或强制参数。需要参数、条件和错误处理时，函数或独立脚本更合适。例如：

```bash
cddemo() {
  cd "$HOME/Projects/demo" || return
  pwd
  git status
}
```

写入 `.zshrc` 前，先在当前终端临时定义并测试。

安装工具时常需要修改 PATH：

```bash
export PATH="$HOME/bin:$PATH"
```

这表示优先从 `~/bin` 寻找程序。修改后检查：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
type -a COMMAND
```

不要把同一目录重复追加到 `.zprofile`、`.zshrc` 和工具生成的脚本。使用 Homebrew、pyenv、Conda、nvm 或其他环境管理器时，先确认它们修改了哪些启动文件；出现版本混乱时，`type -a python3`、`type -a node` 和 `type -a codex` 比继续安装新副本更有用。

## 5. 通配符和环境变量会在程序启动前生效

zsh 的 `*`、`?` 和 `[]` 会在命令运行前展开。只读预览 Python 文件可以使用：

```bash
printf '%s\n' *.py
```

没有匹配时，zsh 通常显示 `no matches found`，这与 Bash 的默认行为可能不同。通配符用于查看很方便，但用于删除、移动、上传、同步和改权限时会扩大影响范围，应先用 `printf`、`ls` 或工具的 dry run 检查展开结果。

Claude Code、Codex 和第三方管理工具还可能通过环境变量设置 Base URL、API Key、Token 或状态目录。变量写入 `.zshrc` 后，每个新终端都会继承。只查看相关变量名称，不显示正文：

```bash
env | grep -E '^(CODEX_HOME|OPENAI_|ANTHROPIC_|CLAUDE_CODE_)' \
  | sed 's/=.*$/=<已设置>/'
```

如果已经切回官方登录，客户端却仍访问旧网关，应检查 `.zshrc`、`.zprofile` 和管理工具启动脚本中是否残留自定义 Base URL、认证变量或 `CODEX_HOME`。界面中的一次“切换”可能改写 TOML、JSON、环境变量或系统凭证库，不能把所有变化都理解成换模型。

## 6. 启动报错时保留一个可恢复入口

假设新终端显示：

```text
/Users/NAME/.zshrc:42: unmatched "
```

错误已经指出第 42 行附近存在未闭合引号。查看上下文并做语法检查：

```bash
nl -ba ~/.zshrc | sed -n '35,48p'
zsh -n ~/.zshrc
```

当前 Shell 因配置错误无法正常使用时，可以启动不读取普通用户启动文件的 zsh：

```bash
zsh -f
```

在这个临时环境中修复文件，或比较之前的备份。恢复整个配置前先确认备份时间，避免覆盖后来仍需要的正常修改。不要因为 `.zshrc` 一行错误就重装 Terminal，窗口程序通常不是问题来源。

## 7. 一套实用的自检命令

```bash
echo "$SHELL"
ps -p $$ -o comm=
zsh --version
zsh -n ~/.zshrc
bindkey '^U'
type -a COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

这些命令分别检查 Shell、配置语法、按键和命令路径。遇到终端启动报错、快捷键变化或命令突然消失时，先确定是哪一层发生变化，再决定是否修改配置。

继续阅读：[命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)、[Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)和[配置、凭证、供应商与实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)。