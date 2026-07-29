# 01 Homebrew 与 PATH

Homebrew 是 macOS 常用的软件包管理器。它不仅负责下载软件，还决定软件安装到哪里、怎样升级和卸载，以及命令是否能被当前 Shell 找到。本章不追求记住很多 `brew` 子命令，而是通过安装 `ripgrep` 完成一条完整流程：确认架构和 Homebrew 前缀、检查 PATH、搜索软件、安装、验证命令来源，并理解 Formula、Cask 和 keg-only。

## 1. 先确认本机架构与现有安装

在 Mac 终端执行：

```bash
uname -m
arch
command -v brew
brew --version
brew --prefix
```

Apple Silicon Mac 通常看到：

```text
arm64
arm64
/opt/homebrew/bin/brew
Homebrew ...
/opt/homebrew
```

Intel Mac 的默认前缀通常是：

```text
/usr/local
```

Homebrew 官方支持的默认位置之所以重要，是因为大量预编译包会按照这些前缀构建。不要只根据旧教程猜测路径，也不要为了“统一”两台不同架构的 Mac，把 Homebrew 手工移动到同一个目录。

如果 `command -v brew` 没有输出，但你怀疑已经安装过，可以检查默认位置：

```bash
ls -l /opt/homebrew/bin/brew 2>/dev/null
ls -l /usr/local/bin/brew 2>/dev/null
```

发现文件存在时，问题可能是 PATH，而不是没有安装。不要连续重复运行安装脚本，否则可能把一个简单的 Shell 配置问题变成多套安装并存。

## 2. 安装前理解官方脚本会做什么

Homebrew 官方安装方式会使用远程脚本。运行任何类似：

```bash
curl URL | sh
```

的命令前，都应确认 URL 属于官方来源、当前页面仍在维护，并阅读脚本将修改的路径。Homebrew 官方安装器会显示计划并要求确认，但这不意味着从论坛、网盘或镜像站复制的任意一键命令都同样可信。

安装 Homebrew 还需要受支持的 macOS 环境和 Apple Command Line Tools。缺少工具时，可按官方提示安装：

```bash
xcode-select --install
```

本手册不复制一个可能随时间变化的完整安装命令。应从 Homebrew 官网获取当前指令，并在执行后保存安装器输出中的 “Next steps”。

## 3. `brew shellenv` 为什么重要

Homebrew 安装结束后，通常会要求把一条 `shellenv` 初始化写入 Shell 配置。例如 Apple Silicon 常见：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

这条命令会输出并应用 Homebrew 需要的环境变量，其中最关键的是让 Homebrew 的 `bin` 和 `sbin` 进入 PATH。

查看它准备设置什么：

```bash
/opt/homebrew/bin/brew shellenv
```

查看当前 PATH 的每一项：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
```

Shell 从前到后搜索命令。若多个目录中存在同名程序，排在前面的版本通常先被运行。

macOS zsh 常把登录环境初始化放在：

```text
~/.zprofile
```

交互式别名和提示符通常放在：

```text
~/.zshrc
```

实际加载方式仍取决于终端启动模式。安装器给出哪个文件，就先按当前官方提示处理，不要同时向 `.zprofile`、`.zshrc` 和其他文件重复追加同一行。

检查是否已经写过：

```bash
grep -n 'brew shellenv' ~/.zprofile ~/.zshrc 2>/dev/null
```

修改前备份：

```bash
cp ~/.zprofile ~/.zprofile.backup
```

语法检查：

```bash
zsh -n ~/.zprofile
```

然后新开一个终端验证，通常比反复 `source` 一份有错误的配置更容易判断启动过程。

## 4. 用 `type` 和 `command -v` 判断实际命令来源

一台 Mac 上可能同时存在系统工具、Homebrew 工具、Python 虚拟环境和 Node 全局命令。检查所有候选：

```bash
type -a brew
type -a python3
type -a git
type -a rg
```

查看当前真正会运行哪一个：

```bash
command -v brew
command -v python3
command -v rg
```

`type -a` 能显示别名、函数、内建命令和所有 PATH 候选；`command -v` 适合确认当前解析结果。仅仅看到“安装成功”不能证明你运行的就是刚安装的版本。

Apple Silicon 上如果同时看到：

```text
/opt/homebrew/bin/brew
/usr/local/bin/brew
```

可能存在原生 arm64 与 Intel/Rosetta 两套 Homebrew。继续检查：

```bash
arch
file "$(command -v brew)"
brew --prefix
```

不要直接删除 `/usr/local`。其中可能包含其他软件和历史数据，应先记录两套安装内容并按官方迁移方式处理。

## 5. Formula、Cask、keg 和 prefix

Homebrew 常见术语可以这样理解：

```text
Formula
→ 命令行工具、库或可由 Homebrew 管理的服务

Cask
→ 预编译并由上游签名的 macOS 应用或大型二进制软件

prefix
→ Homebrew 的安装根目录，例如 /opt/homebrew

keg
→ 某个 Formula 某个版本的实际安装目录

keg-only
→ 已安装到 Cellar，但没有默认链接进通用前缀
```

安装命令行工具通常使用：

```bash
brew install ripgrep
```

安装图形应用常见：

```bash
brew install --cask visual-studio-code
```

“是否在 Finder 中出现图标”不是判断 Formula 是否安装成功的方法；“终端中能否找到命令”也不能完全代表 Cask 应用是否正常。

查看软件信息：

```bash
brew info ripgrep
```

输出会说明版本、依赖、安装位置、是否 keg-only，以及可能需要额外添加到 PATH 的提示。

## 6. 完成一次搜索、安装和验证

先确认 `rg` 是否已经存在：

```bash
command -v rg
rg --version
```

若命令不存在，搜索 Homebrew 中的包：

```bash
brew search ripgrep
```

查看信息：

```bash
brew info ripgrep
```

确认包名和来源后安装：

```bash
brew install ripgrep
```

安装完成后不要只看最后一行，继续验证：

```bash
rg --version
command -v rg
type -a rg
brew list --versions ripgrep
brew --prefix ripgrep
```

在 Apple Silicon 上，命令通常来自：

```text
/opt/homebrew/bin/rg
```

接着做一个实际测试：

```bash
mkdir -p ~/terminal-practice/brew-demo
cd ~/terminal-practice/brew-demo
printf '%s\n' 'TODO: write tests' 'done' > notes.txt
rg -n 'TODO' .
```

应看到 `notes.txt` 中匹配行。这样才完成了“包已安装、Shell 能找到、程序能运行、实际功能符合预期”的验证闭环。

## 7. 已安装但命令找不到时怎么查

假设 `brew list --versions ripgrep` 显示已安装，但 `rg` 提示找不到。按顺序检查：

```bash
brew --prefix
brew --prefix ripgrep
brew list ripgrep
command -v rg
type -a rg
printf '%s\n' "$PATH" | tr ':' '\n'
```

可能原因包括：

- Homebrew 的 `bin` 没进入 PATH；
- 当前终端没有重新加载登录配置；
- 使用了另一套架构的 Shell；
- Formula 是 keg-only；
- 命令名与 Formula 名不同；
- 运行环境位于 IDE、服务或非交互 Shell，加载的配置不同。

不要为了让命令出现，随意在 `/usr/local/bin` 或 `/opt/homebrew/bin` 手工创建软链接。先阅读：

```bash
brew info FORMULA
```

如果 Formula 是 keg-only，官方信息通常会给出适合当前版本的 PATH 或编译环境设置。

## 8. 更新元数据与升级软件是两件事

更新 Homebrew 自身和包元数据：

```bash
brew update
```

查看可升级项目：

```bash
brew outdated
```

升级一个明确的软件：

```bash
brew upgrade ripgrep
```

无参数的：

```bash
brew upgrade
```

可能升级大量 Formula 和 Cask。它不适合在比赛、演示、提交截止前或重要训练开始前随手运行。Python、Node、数据库、编译器和 AI CLI 运行时的版本变化，都可能影响项目。

更稳妥的流程是：

```text
brew update
→ brew outdated
→ 识别与当前项目有关的软件
→ 阅读主版本变化
→ 升级一个明确目标
→ 验证命令路径与版本
→ 运行项目测试
```

Homebrew 命令成功，只能说明包管理操作完成，不代表所有项目都兼容新版本。

## 9. 卸载与清理先预览影响

卸载一个明确的 Formula：

```bash
brew uninstall FORMULA
```

执行前查看谁依赖它：

```bash
brew uses --installed FORMULA
brew deps FORMULA
```

清理旧下载和旧版本前先预览：

```bash
brew cleanup -n
```

确认后才考虑：

```bash
brew cleanup
```

不要手工批量删除 `/opt/homebrew/Cellar`、`/opt/homebrew/opt` 或 `/usr/local` 中不认识的目录。Homebrew 的链接和依赖关系应尽量由 Homebrew 自己维护。

Cask 的 `--zap` 可能删除应用相关的配置和数据，有些文件还可能被其他应用共享。它不是普通卸载的默认选项。

## 10. `brew doctor` 是诊断工具，不是自动修复按钮

运行：

```bash
brew doctor
```

它可能报告旧 Command Line Tools、非默认前缀、意外头文件、多套 Homebrew 或 PATH 问题。Warning 不一定与当前问题有关，也不代表整个系统已经损坏。

处理顺序：

1. 阅读完整信息；
2. 判断它是否能解释当前故障；
3. 用 `brew config`、`brew --prefix`、`arch` 和 `type -a` 补充证据；
4. 查阅 Homebrew 官方文档；
5. 修改前备份配置和包清单；
6. 一次只处理一个确认的问题。

不要把论坛中的 `sudo chown -R`、全局删除目录或批量创建软链接当成通用修复。

## 11. 为什么不要使用 `sudo brew`

不应执行：

```bash
sudo brew install PACKAGE
```

Homebrew 的默认前缀设计为安装后由普通用户管理。使用 sudo 可能生成 root 所有文件，导致后续安装、升级和卸载继续要求管理员权限，并污染目录所有权。

遇到权限错误时先检查：

```bash
brew --prefix
ls -ld "$(brew --prefix)"
brew doctor
```

然后根据官方诊断处理具体异常。不要递归放宽整个 Homebrew 目录权限，也不要把目录改成所有用户可写。

## 12. AI CLI 的 Homebrew 操作边界

可以给 Agent 明确约束：

```text
先检查命令是否已存在，输出 command -v、type -a、版本、brew 前缀和架构。
缺少依赖时，说明 Formula/Cask 名称、用途、来源和预计影响。
未经确认不要安装、全量升级、cleanup、link、unlink、卸载或修改 Shell 配置。
不要使用 sudo brew，不要递归修改 Homebrew 目录权限。
完成后验证实际命令路径、版本和项目测试。
```

对于 `command not found`，推荐排查顺序是：

```text
命令是否已经存在
→ 当前 Shell 实际解析到哪里
→ Formula 是否已安装
→ Homebrew 前缀和架构是否正确
→ PATH 是否包含正确目录
→ Shell 配置是否被加载
→ 是否为 keg-only 或命令名不同
```

继续阅读：

- [服务、版本与常见故障](02-服务版本与常见故障.md)
- [Python 解释器与 pip 定位](../Part-07-Python环境/01-Python解释器与pip定位.md)

官方参考：

- [Homebrew Installation](https://docs.brew.sh/Installation)
- [Homebrew Manual](https://docs.brew.sh/Manpage)
- [Homebrew Common Issues](https://docs.brew.sh/Common-Issues)
