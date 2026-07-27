# 04 zsh 到底是什么

zsh 是 macOS 默认常见的 Shell。它负责解释命令、显示提示符、保存历史、补全路径、读取配置文件，并通过 ZLE 提供命令行编辑能力。

很多看起来像“终端自带”的功能，其实来自 zsh：

- Tab 补全；
- 方向键历史；
- `Ctrl + R` 搜索历史；
- `Ctrl + U`、`Ctrl + W` 等编辑快捷键；
- 通配符展开；
- 别名和函数。

---

## 1. ZLE 是什么

ZLE 是 Zsh Line Editor，负责普通 zsh 提示符中的输入编辑。

查看当前按键绑定：

```bash
bindkey '^U'
bindkey '^W'
bindkey '^R'
```

不同插件、Vi 模式和终端配置可能改变结果，所以本机 `bindkey` 输出比通用速查表更可靠。

临时切换到常见 Emacs 键位：

```bash
bindkey -e
```

不要在不了解现有配置时，把网上整套键位设置直接追加到配置文件。

---

## 2. `.zshrc` 会影响什么

常见交互式配置文件：

```text
~/.zshrc
```

它可能包含：

- PATH；
- alias；
- 函数；
- 插件；
- Prompt；
- Python、Node 和 Homebrew 初始化；
- API 端点或环境变量。

修改前备份：

```bash
cp ~/.zshrc ~/.zshrc.backup
```

重新加载：

```bash
source ~/.zshrc
```

重新加载会立即执行其中内容。出现报错时，不要反复 `source`，先定位具体行：

```bash
zsh -n ~/.zshrc
```

这可以进行语法检查，但不能发现所有运行时逻辑问题。

---

## 3. `.zprofile` 和 `.zshrc` 不完全相同

macOS 中常见：

```text
~/.zprofile
→ 登录 Shell 初始化，常用于 PATH 和 Homebrew shellenv

~/.zshrc
→ 每个交互式 zsh 会话读取，常用于别名、提示符和插件
```

实际加载行为还受到终端设置和启动方式影响。遇到“一个终端能运行，另一个不能”时，检查不同配置文件是否重复或冲突。

不要同时在多个文件里无脑追加相同 PATH 初始化。

---

## 4. alias 适合简单替换

```bash
alias ll='ls -la'
```

查看：

```bash
alias
type ll
```

alias 适合短而透明的替换。不要把高风险命令隐藏成看不出含义的短名称，例如把递归删除包装成一个随手输入的别名。

复杂逻辑应使用函数或脚本，并明确参数和错误处理。

---

## 5. Tab 补全比死记路径更可靠

输入：

```bash
cd Dow
```

按 Tab，zsh 可能补全为：

```bash
cd Downloads/
```

补全不仅节省输入，也能帮助确认路径确实存在。匹配不唯一时，zsh 可能显示候选或等待继续输入。

不要把长路径完全靠手打。

---

## 6. 历史命令可能包含敏感信息

浏览上一条命令：

```text
方向键上
```

搜索历史：

```text
Ctrl + R
```

历史文件可能位于：

```text
~/.zsh_history
```

不要在命令行直接粘贴长期有效的 Token、密码或 Cookie。即使执行 `clear`，历史记录也可能仍然存在。

找到历史命令后先检查路径、地址和参数，再决定是否执行。

---

## 7. 通配符会在命令执行前展开

```text
*   任意数量字符
?   一个字符
[]  字符集合
```

例如：

```bash
ls *.py
```

查看很方便，但用于删除、移动、上传和改权限时会放大影响。

在 zsh 中，没有匹配结果时常见：

```text
zsh: no matches found
```

这通常是保护性行为，不要为了消除提示而随意修改全局通配符设置。

---

## 8. Oh My Zsh 不是必需品

Oh My Zsh 是配置框架，可以提供主题、插件、别名和补全增强，但不是使用 zsh 的前提。

新手一开始安装大量插件会增加排错层级：

```text
zsh
→ ZLE
→ 主题
→ 插件
→ PATH 初始化
→ 语言环境管理器
```

先掌握原生 zsh，再根据真实需求增加配置。

---

## 9. zsh 排错清单

```bash
echo "$SHELL"
ps -p $$
zsh --version
zsh -n ~/.zshrc
bindkey '^U'
type -a COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

遇到终端启动报错或命令消失时，优先检查最近修改的配置，而不是先重装终端或系统。

继续阅读：

- [命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
- [Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)
- [Python 解释器与 pip 定位](../Part-07-Python环境/01-Python解释器与pip定位.md)
