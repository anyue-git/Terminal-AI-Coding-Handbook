# 01 Homebrew 与 PATH

Homebrew 是 macOS 常用的软件包管理器。它不仅负责下载软件，还决定软件安装到哪里、如何升级和卸载，以及当前 Shell 最终会运行哪个同名命令。本章不追求背诵大量 `brew` 子命令，而是用安装 `ripgrep` 贯穿一条完整流程：确认架构与前缀、检查 PATH、搜索和安装软件、验证命令来源，并理解 Formula、Cask 与 keg-only。

## 1. 先确认架构、前缀和现有安装

在 Mac 执行：

```bash
uname -m
arch
command -v brew
brew --version
brew --prefix
```

Apple Silicon 默认前缀通常是 `/opt/homebrew`，Intel Mac 通常是 `/usr/local`。这些路径与预编译包和命令链接有关，不应根据旧教程猜测，也不要为了“统一”两台不同架构的 Mac 手工移动 Homebrew。

若 `command -v brew` 没有输出，但怀疑已经安装过，可以检查默认位置：

```bash
ls -l /opt/homebrew/bin/brew 2>/dev/null
ls -l /usr/local/bin/brew 2>/dev/null
```

文件存在却找不到命令，通常是 PATH 或 Shell 初始化问题，不应立即重复运行安装脚本。Homebrew 官方安装命令和系统要求可能变化，本手册不复制长期固定的一键脚本；应从官方页面获取当前指令，确认 URL、脚本修改范围和安装器给出的 `Next steps`。缺少 Apple Command Line Tools 时，按官方提示使用 `xcode-select --install`。

## 2. `brew shellenv` 把 Homebrew 接入当前 Shell

Apple Silicon 常见初始化形式是：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

它会设置 Homebrew 所需环境变量，并把 `bin` 和 `sbin` 加入 PATH。先查看它准备输出什么：

```bash
/opt/homebrew/bin/brew shellenv
printf '%s\n' "$PATH" | tr ':' '\n'
```

zsh 登录环境常使用 `~/.zprofile`，交互式别名和提示符常放在 `~/.zshrc`，但实际加载方式取决于终端启动模式。安装器要求写入哪个文件，就按当前提示处理，不要同时向多个启动文件重复追加。

修改前检查并备份：

```bash
grep -n 'brew shellenv' ~/.zprofile ~/.zshrc 2>/dev/null
cp ~/.zprofile ~/.zprofile.backup
zsh -n ~/.zprofile
```

随后新开终端验证，通常比反复 `source` 一份有错误的配置更安全。

## 3. 安装成功不等于当前运行的是新版本

一台 Mac 可能同时存在系统工具、Homebrew、Python 虚拟环境、Node 全局命令和 Rosetta 下的另一套安装。使用：

```bash
type -a brew python3 git rg
command -v brew
command -v python3
command -v rg
```

`type -a` 显示别名、函数和所有 PATH 候选，`command -v` 显示当前解析结果。Apple Silicon 若同时出现 `/opt/homebrew/bin/brew` 和 `/usr/local/bin/brew`，可能存在 arm64 与 Intel/Rosetta 两套 Homebrew；继续检查：

```bash
arch
file "$(command -v brew)"
brew --prefix
```

不要直接删除 `/usr/local`，其中可能还有其他软件和历史数据。先记录两套安装的来源和内容，再按官方迁移方式处理。

## 4. Formula、Cask、prefix 与 keg-only

Formula 通常描述命令行工具、库或服务；Cask 安装上游提供的图形应用或大型预编译软件；prefix 是 Homebrew 根目录；keg 是某个 Formula 某个版本的实际目录；keg-only 表示软件已安装到 Cellar，但没有默认链接到通用前缀。

```bash
brew install ripgrep
brew install --cask visual-studio-code
brew info ripgrep
```

Finder 中是否有图标不能判断 Formula 是否成功，终端能否找到命令也不能完全代表 Cask 应用状态。`brew info` 会说明版本、依赖、安装位置和 keg-only 提示。

## 5. 完成一次搜索、安装和实际验证

先检查 `rg` 是否已经存在：

```bash
command -v rg
rg --version
```

不存在时搜索并查看信息：

```bash
brew search ripgrep
brew info ripgrep
brew install ripgrep
```

安装后验证路径、版本、包记录和实际功能：

```bash
rg --version
command -v rg
type -a rg
brew list --versions ripgrep
brew --prefix ripgrep

mkdir -p ~/terminal-practice/brew-demo
cd ~/terminal-practice/brew-demo
printf '%s\n' 'TODO: write tests' 'done' > notes.txt
rg -n 'TODO' .
```

这才完成“包已安装、Shell 能找到、当前运行的是预期程序、功能可用”的闭环。

## 6. 已安装但命令找不到时按层调查

```bash
brew --prefix
brew --prefix FORMULA
brew list FORMULA
command -v COMMAND
type -a COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
brew info FORMULA
```

常见原因包括 Homebrew 的 bin 不在 PATH、当前终端未加载新配置、使用另一架构 Shell、Formula 为 keg-only、命令名与包名不同，或 IDE/服务/非交互 Shell 加载了不同环境。不要为让命令出现而随意在 `/usr/local/bin` 或 `/opt/homebrew/bin` 手工创建软链接；keg-only 软件应按 `brew info` 给出的当前版本提示设置 PATH 或构建变量。

## 7. 更新、升级、权限修复和清理要拆开决策

```bash
brew update
brew outdated
brew upgrade ripgrep
```

`brew update` 更新 Homebrew 与元数据，`brew outdated` 只列出可升级项目，指定 Formula 的 `brew upgrade` 才执行目标升级。无参数升级可能同时改变 Python、Node、数据库、编译器和 AI CLI 运行时，不适合在比赛、演示、截止前或重要训练开始前随手执行。稳妥流程是识别目标、阅读主版本变化、只升级明确软件、重新确认命令路径与版本，再运行项目测试。

Homebrew 的默认前缀在安装完成后应由普通用户管理，不要用下面的方式绕过权限错误：

```bash
sudo brew install PACKAGE
```

`sudo` 可能在 Homebrew 目录中生成 root 所有文件，让后续安装、升级和卸载继续要求管理员权限。遇到 `Permission denied` 时先确认实际前缀、目录所有者和诊断结果：

```bash
brew --prefix
ls -ld "$(brew --prefix)"
brew doctor
```

只修复能够确认的异常，不递归放宽整个 Homebrew 前缀，也不要把目录改成所有用户可写。论坛中的 `sudo chown -R`、全局删除目录或批量创建软链接都不应作为通用恢复步骤。

卸载前查看依赖关系：

```bash
brew uses --installed FORMULA
brew deps FORMULA
brew uninstall FORMULA
```

清理旧版本和下载先预演：

```bash
brew cleanup -n
```

不要手工批量删除 Cellar、opt 或 `/usr/local` 中不认识的目录。Cask 的 `--zap` 可能删除配置和数据，也不是普通卸载的默认选项。

## 8. `brew doctor` 用于诊断，不是自动修复

```bash
brew doctor
```

它可能报告旧工具链、非默认前缀、多套安装、意外头文件和 PATH 问题。警告不一定都与当前故障有关，应阅读上下文并逐项判断；不要让 Agent 将所有建议自动执行。需要提交排障信息时，可使用 `brew config`、`brew doctor` 和目标包的 `brew info`，但先检查输出是否含用户名、内部路径或代理信息。

## 9. 一条稳定的 Homebrew 工作流

```text
确认 Mac 架构和 brew 前缀
→ 查看 shellenv 与 PATH
→ 用 type/command -v 确认实际命令来源
→ 搜索和阅读 Formula/Cask 信息
→ 安装一个明确目标
→ 验证路径、版本和实际功能
→ 升级、权限修复、卸载和清理分别评估影响
```

继续阅读：

- [服务、版本与常见故障](02-服务版本与常见故障.md)
- [Shell 到底是什么](../Part-01-基础篇/03-Shell到底是什么.md)
- [Python 解释器与 pip 定位](../Part-07-Python环境/01-Python解释器与pip定位.md)

官方参考：

- [Homebrew Installation](https://docs.brew.sh/Installation)
- [Homebrew Manual](https://docs.brew.sh/Manpage)
- [Homebrew Common Issues](https://docs.brew.sh/Common-Issues)
