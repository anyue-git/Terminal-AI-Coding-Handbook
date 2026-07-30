# 02 Terminal 到底是什么

打开 Mac 上的 Terminal.app 后，你会看到一个可以输入文字的窗口。日常交流里，人们常把窗口、里面运行的 zsh、输入的命令和操作系统统称为“终端”；遇到快捷键失效、命令找不到、远程连接或 AI CLI 接管输入时，分清这些层会更容易排错。

Terminal 是承载文字交互的界面，负责接收键盘输入、显示程序输出，并把输入交给当前正在运行的程序。刚打开窗口时，这个程序通常是 Shell；macOS 默认常见的是 zsh。你在 Shell 中输入 `git status` 后，zsh 会寻找并启动 Git，Git 读取当前目录的仓库状态，Terminal 再把结果显示出来。关系可以先记成：

```text
键盘输入
→ Terminal 接收
→ 当前程序处理
→ 程序调用系统资源
→ Terminal 显示结果
```

“当前程序”不一定始终是 zsh。启动 `less`、Vim、Claude Code、Codex 或 SSH 会话后，窗口没有变，但输入已经先交给新的程序。

## 1. 窗口软件、Shell 和当前程序是三件事

macOS Terminal、iTerm2、Warp、VS Code 集成终端和 JetBrains Terminal 都可以提供终端界面。它们的字体、标签页和复制方式可能不同，但里面可以运行同一个 zsh；同一个 Terminal.app 里也可以启动 Bash、Fish、Python 解释器或远程 Shell。

在 Mac 终端运行下面的只读检查，可以看到当前终端应用、登录 Shell 设置和当前 Shell 进程：

```bash
printf 'Terminal program: %s\n' "$TERM_PROGRAM"
printf 'Shell setting: %s\n' "$SHELL"
printf 'Current process: '
ps -p $$ -o comm=
```

输出可能类似：

```text
Terminal program: Apple_Terminal
Shell setting: /bin/zsh
Current process: -zsh
```

在 VS Code 中，`TERM_PROGRAM` 可能显示 `vscode`；进入容器或临时启动 Bash 后，当前进程也可能与 `$SHELL` 不同。如果一条命令在两个“终端窗口”中表现不同，不要只比较窗口软件，还要检查机器、用户、目录、Shell、PATH 和环境变量。

## 2. 提示符只是等待输入的界面

刚打开终端时可能看到：

```text
username@MacBook ~ %
```

末尾的 `%` 表示 Shell 正在等待输入，前面的用户名、计算机名和目录由主题与配置决定。`~` 表示当前用户主目录；运行：

```bash
pwd
```

可能得到 `/Users/username`。网上教程常写 `$ pwd`，其中 `$` 通常只是“普通用户 Shell”的提示符，实际只输入 `pwd`。把 `$` 一起复制后出现 `zsh: command not found: $`，删掉提示符即可，不需要重新安装软件。

普通 Shell 中，输入一行命令并按回车，程序结束后提示符会再次出现。文档通常把输入和输出分开写，正是为了避免提示符和输出被误当成命令。

## 3. 怎样判断现在是谁在接收按键

执行：

```bash
less README.md
```

以后，`q` 会退出 `less`，而不是作为 zsh 命令执行。启动 `claude`、`codex` 或其他 TUI 后，输入会被当成 Prompt、斜杠命令或界面选项，Shell 的部分快捷键也可能被重新定义。回车在 zsh 中会提交命令，在 AI CLI 中通常提交 Prompt 或确认选项；两者最后都可能运行 `pwd`，但中间的解释和权限边界不同。

不确定自己在哪一层时，先观察熟悉的 Shell 提示符是否存在、界面底部是否显示程序自己的快捷键，以及上一步是否启动了分页器、编辑器、Python、SSH 或 AI CLI。不要在不确定的界面里连续按回车，权限界面可能把它解释为接受默认选项。

## 4. 同一个窗口可以进入远程机器或容器

执行：

```bash
ssh YOUR_USERNAME@SERVER_IP
```

登录成功后，Terminal 窗口仍在 Mac 上，但 Shell 已经运行在远程机器中。提示符可能从 `username@MacBook ~ %` 变成 `username@ubuntu:~$`，也可能变化很小，因此连接后应立即执行：

```bash
hostname
whoami
pwd
```

若输出是远程主机名和 `/home/username`，接下来的安装、删除、Python 和 Git 操作都发生在远程 Linux。原本以为仍在 Mac，却看到 `/home/...` 而不是 `/Users/...` 时，应停止后续操作。退出远程 Shell 使用 `exit`，随后再次运行 `hostname` 确认已回到本机。

VS Code 集成终端遵循同一原则：本地打开项目时，命令通常在 Mac 执行；通过 Remote SSH 连接 Ubuntu 后，新建的远程终端在 Ubuntu 执行。如果编辑器左下角显示远程连接，但 `hostname` 仍是 Mac 名称，可能新建的是本地终端。以命令输出为准，不只看界面装饰。

## 5. 关闭窗口、清屏和停止程序并不相同

直接在终端运行：

```bash
python train.py
```

程序通常与当前 Shell 和终端会话相连。关闭窗口、退出 Shell 或断开 SSH 后，它可能收到挂断信号并终止；具体行为取决于程序和启动方式，不能仅凭“窗口关了”判断任务仍在运行。远程长任务常使用 tmux：

```bash
tmux new -s train
python train.py
```

需要暂时离开时按 `Ctrl + b`，松开后再按小写 `d`；重新连接后运行 `tmux attach -t train`。tmux 能应对终端关闭和 SSH 断线，但不能抵抗远程机器关机、断电、内核崩溃或程序自身退出，重要任务仍需日志和 checkpoint。

`clear` 或普通 zsh 中的 `Ctrl + L` 只整理显示区域，不会撤销命令、删除文件、停止进程或清空历史。可以安全验证：

```bash
printf 'terminal practice\n' > /tmp/terminal-practice.txt
clear
cat /tmp/terminal-practice.txt
```

清屏后文件仍然存在。若把 API Key 或密码直接输入 Shell，`clear` 也不能消除泄露风险，命令可能仍在 `~/.zsh_history`、滚动记录、日志或截图中，需要按凭证类型撤销或轮换。

## 6. 输入或快捷键异常时按层检查

遇到“按键失效”“输入不显示”或“命令和教程不同”，先确认焦点是否在终端输入区，以及当前程序是 Shell、分页器、编辑器、AI CLI 还是 tmux 中的程序。回到普通 Shell 后可以运行：

```bash
hostname
whoami
pwd
printf 'terminal=%s\n' "$TERM_PROGRAM"
printf 'shell=%s\n' "$SHELL"
ps -p $$ -o comm=
```

这组信息能区分机器、用户、目录、终端应用、登录 Shell 和当前进程。再检查 Vim 模式、插件、tmux 或具体 TUI 是否接管按键。不要为了修复某个程序中的快捷键，直接重写整个 `.zshrc` 或终端键盘设置。

继续阅读：[Shell 到底是什么](03-Shell到底是什么.md)、[zsh 到底是什么](04-zsh到底是什么.md)、[命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)和[SSH 基础与首次连接](../Part-05-SSH/01-SSH基础与首次连接.md)。