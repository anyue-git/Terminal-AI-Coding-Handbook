# 03 Shell 到底是什么

Shell 是负责解析并执行命令的程序。

输入：

```bash
ls -la ~/Downloads
```

Shell 会识别：

- 命令：`ls`；
- 选项：`-la`；
- 参数：`~/Downloads`；
- `~` 需要展开为当前用户主目录。

然后它查找并启动对应程序，把结果交回终端显示。

---

## 1. Shell 不只有一种

常见 Shell：

- zsh；
- bash；
- fish；
- sh；
- PowerShell。

macOS 默认通常是 zsh，Linux 教程中经常出现 bash。两者基础语法相近，但配置文件、插件和部分高级行为不同。

查看登录 Shell：

```bash
echo "$SHELL"
```

查看当前进程：

```bash
ps -p $$
```

---

## 2. 内建命令和外部程序

`cd` 通常是 Shell 内建命令，因为改变当前目录需要修改 Shell 自身状态。

`ls`、`git`、`python` 等通常是外部程序。

检查：

```bash
type cd
type ls
type git
```

`type` 比单独使用 `which` 更完整，因为它还能识别别名、函数和内建命令。

---

## 3. Shell 怎样寻找命令

输入：

```bash
codex
```

Shell 通常会按照 `PATH` 中的目录顺序查找。

查看 PATH：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
```

查看会运行哪个程序：

```bash
command -v codex
type -a codex
```

出现 `command not found` 时，常见原因是：

- 工具没有安装；
- 安装目录不在 PATH；
- Shell 尚未重新加载配置；
- 命令名错误；
- 工具安装在另一个 Python、Node 或用户环境中。

不要在没有定位路径前重复安装。

---

## 4. Shell 会先处理特殊字符

```bash
ls *.md
```

通常是 Shell 先把 `*.md` 展开成多个文件名，再交给 `ls`。

这也是通配符删除危险的原因：

```bash
rm *.md
```

执行前应先预览：

```bash
ls -l *.md
```

变量、通配符、引号、重定向、管道和命令替换都可能在程序启动前由 Shell 处理。

---

## 5. 引号为什么重要

双引号允许变量展开：

```bash
printf '%s\n' "$HOME"
```

单引号通常按原样保留：

```bash
printf '%s\n' '$HOME'
```

路径有空格时：

```bash
cd "My Project"
```

变量表示路径时通常应加双引号：

```bash
cp "$SOURCE_FILE" "$BACKUP_DIR/"
```

否则空格和通配符可能被再次拆分或展开。

---

## 6. Shell 可以组合命令

管道：

```bash
rg 'ERROR' app.log | less
```

成功后继续：

```bash
python -m pytest && git status
```

保存输出：

```bash
python app.py 2>&1 | tee app.log
```

这些能力让小工具组成可重复流程。复杂逻辑仍然更适合写成有测试的 Python 程序或维护良好的脚本。

---

## 7. Shell 与 AI CLI 的关系

运行：

```bash
claude
```

Shell 负责找到并启动 Claude Code。进入工具后，Claude Code 接管交互；当它运行 `python -m pytest` 时，又会调用当前系统环境中的程序。

所以 AI CLI 的实际能力仍受以下因素限制：

- 当前目录；
- PATH；
- 当前用户；
- 环境变量；
- 文件权限；
- 网络；
- Sandbox 和审批规则。

AI Agent 不是绕过操作系统的更高权限层。

---

## 8. 命令问题的排查顺序

```text
当前是否在普通 Shell
→ 命令类型是什么
→ PATH 指向哪里
→ 参数和引号是否正确
→ 通配符或变量怎样展开
→ 当前用户是否有权限
```

常用检查：

```bash
pwd
type -a COMMAND
command -v COMMAND
printf '%s\n' "$PATH" | tr ':' '\n'
```

继续阅读：

- [zsh 到底是什么](04-zsh到底是什么.md)
- [Homebrew 与 PATH](../Part-06-Homebrew/01-Homebrew与PATH.md)
- [管道、重定向与命令组合](../Part-02-终端命令/05-管道重定向与命令组合.md)
