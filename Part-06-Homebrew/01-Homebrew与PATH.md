# 01 Homebrew 与 PATH

Homebrew 是 macOS 常用的软件包管理器。它不仅负责下载软件，还管理安装位置、依赖、升级、卸载，以及命令如何进入 Shell 的搜索路径。

---

## 1. 先确认是否已经安装

```bash
brew --version
type -a brew
```

如果提示找不到命令，可能是：

- 尚未安装；
- 已安装但 PATH 未配置；
- Shell 配置尚未加载；
- 当前终端架构与安装环境不同。

不要因为找不到命令就反复运行安装脚本。

---

## 2. Apple Silicon 与 Intel 的常见前缀

```text
Apple Silicon：/opt/homebrew
Intel：         /usr/local
```

确认本机：

```bash
uname -m
brew --prefix
```

不要只根据旧教程猜路径。

---

## 3. `brew shellenv` 和 PATH

Homebrew 安装后，通常会要求在 Shell 配置中加入类似：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

具体路径以官方安装器提示和 `brew --prefix` 为准。

查看 PATH：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
```

Shell 会从前到后寻找命令。多个目录存在同名程序时，排在前面的通常优先。

查看所有来源：

```bash
type -a python3
type -a node
type -a codex
```

查看最终命令：

```bash
command -v python3
```

---

## 4. 不要重复追加 Shell 配置

检查：

```bash
grep -n 'brew shellenv' ~/.zprofile ~/.zshrc 2>/dev/null
```

修改前备份：

```bash
cp ~/.zprofile ~/.zprofile.backup
```

不要每次排错都向 `.zprofile` 和 `.zshrc` 重复追加同一行。PATH 越堆越长，问题通常不会因此更清楚。

---

## 5. Formula 与 Cask

Formula 通常是命令行工具、库和服务：

```bash
brew install ripgrep
brew install git
```

Cask 通常是图形应用：

```bash
brew install --cask visual-studio-code
```

查看信息：

```bash
brew info PACKAGE_NAME
```

---

## 6. 搜索、安装与验证

```bash
brew search ripgrep
brew install ripgrep
rg --version
command -v rg
```

查看已安装内容：

```bash
brew list --formula
brew list --cask
```

安装完成不代表当前 Shell 一定会优先找到它，仍要检查命令路径。

---

## 7. update、outdated 和 upgrade

更新 Homebrew 元数据：

```bash
brew update
```

查看可升级项目：

```bash
brew outdated
```

升级指定软件：

```bash
brew upgrade ripgrep
```

全量升级：

```bash
brew upgrade
```

不要在比赛、演示、训练或重要项目开始前无差别升级所有开发工具。Python、Node、数据库和编译器的主版本变化可能影响现有项目。

---

## 8. 卸载与清理

```bash
brew uninstall PACKAGE_NAME
```

预览清理：

```bash
brew cleanup -n
```

正式清理：

```bash
brew cleanup
```

不要手工批量删除 `/opt/homebrew` 或 `/usr/local` 中不认识的目录。

---

## 9. `brew doctor` 应怎样使用

```bash
brew doctor
```

Warning 不一定表示系统已损坏。正确流程：

1. 阅读完整提示；
2. 判断是否与当前问题相关；
3. 检查路径、权限和多版本来源；
4. 修改前备份；
5. 不复制网上的一键修复脚本。

---

## 10. 不要使用 `sudo brew`

不推荐：

```bash
sudo brew install PACKAGE
```

它可能产生 root 所有文件，让普通用户以后无法升级或卸载。

权限问题先检查：

```bash
brew doctor
brew --prefix
ls -ld "$(brew --prefix)"
```

再依据官方提示处理具体路径，不要扩大整个目录权限。

---

## 11. 网络安装脚本的边界

对任何：

```bash
curl URL | sh
```

都应确认：

- URL 来自官方网站；
- 命令是当前官方版本；
- 脚本会创建或修改什么；
- 没有从论坛复制被篡改的镜像；
- 不在命令中暴露密码、Token 或 Cookie。

官方常用远程脚本，不等于任意远程脚本都安全。

---

## 12. AI CLI 的 Homebrew 边界

```text
先检查命令是否已经存在，并显示版本和路径。
缺少依赖时，说明包名、用途和预计影响。
未经确认不要安装、全量升级、cleanup 或修改 Shell 配置。
不要使用 sudo brew。
```

排查 `command not found` 的顺序：

```text
确认是否安装
→ command -v 和 type -a
→ brew --prefix
→ 检查 PATH
→ 检查 Shell 配置
→ 新开终端验证
```

继续阅读：

- [服务、版本与常见故障](02-服务版本与常见故障.md)
- [Python 解释器与 pip 定位](../Part-07-Python环境/01-Python解释器与pip定位.md)

官方参考：

- [Homebrew Documentation](https://docs.brew.sh/)
- [Homebrew Installation](https://brew.sh/)
