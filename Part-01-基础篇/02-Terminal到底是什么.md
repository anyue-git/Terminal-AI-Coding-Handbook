# 02 Terminal 到底是什么

打开 Mac 上的 Terminal.app 后，你会看到一个可以输入文字的窗口。很多人第一次接触终端时，会把这个窗口、里面运行的 zsh、输入的命令和操作系统统称为“终端”。日常交流这样说问题不大，但遇到快捷键失效、命令找不到或远程连接时，分清它们各自负责什么会更容易排错。

Terminal 是承载文字交互的界面。它负责接收键盘输入、显示程序输出，并把输入交给当前正在运行的程序。刚打开窗口时，这个程序通常是 Shell；在 macOS 上，默认 Shell 通常是 zsh。你在 Shell 中输入 `git status` 后，zsh 会寻找并启动 Git，Git 再读取当前目录中的仓库状态。

可以先把它们的关系记成：

```text
你按下键盘
→ Terminal 接收输入
→ 当前程序处理输入
→ 程序调用系统资源
→ Terminal 显示结果
```

“当前程序”不一定始终是 zsh。启动 `less`、Vim、Claude Code 或 Codex 后，Terminal 窗口没有变，但键盘输入已经先交给了这些程序。这是理解终端行为的关键。

---

## 1. 同样像终端的窗口，里面可能完全不同

macOS Terminal、iTerm2、Warp、VS Code 集成终端和 JetBrains Terminal 都可以提供终端界面。它们的字体、标签页、快捷键和复制方式可能不同，但里面可以运行同一个 zsh。反过来，同一个 Terminal.app 里也可以启动 Bash、Fish、Python 交互解释器或 SSH 会话。

先做一个小检查。在 Mac 终端执行：

```bash
printf 'Terminal program: %s\n' "$TERM_PROGRAM"
printf 'Shell setting: %s\n' "$SHELL"
printf 'Current process: '
ps -p $$ -o comm=
```

可能看到：

```text
Terminal program: Apple_Terminal
Shell setting: /bin/zsh
Current process: -zsh
```

第一行表示当前终端应用，第二行是登录 Shell 设置，第三行是当前 Shell 进程。不同设备上的输出可能不同，例如 VS Code 中的 `TERM_PROGRAM` 可能显示 `vscode`。

如果一条命令在两个“终端窗口”中表现不同，不要只比较窗口软件。还要检查当前机器、Shell、用户、目录、PATH 和环境变量。很多差异来自里面的运行环境，而不是窗口外观。

---

## 2. 提示符是输入位置，不是命令的一部分

刚打开终端时，可能看到类似内容：

```text
username@MacBook ~ %
```

最后的 `%` 表示 Shell 正在等待输入。前面的内容由主题和配置决定，常见信息包括用户名、计算机名称和当前目录。这里的 `~` 表示当前用户的主目录，例如：

```text
/Users/username
```

执行：

```bash
pwd
```

可能得到：

```text
/Users/username
```

很多网上教程会写：

```text
$ pwd
```

其中 `$` 通常只是提示符，用来表示“在普通用户的 Shell 中输入”。实际复制时只输入 `pwd`。如果把 `$` 也复制进去，zsh 可能提示：

```text
zsh: command not found: $
```

看到这种报错时，不需要重新安装任何软件。删掉提示符，只保留命令即可。

---

## 3. 怎样判断输入现在交给谁

最容易判断的状态是普通 Shell。你会看到提示符，输入一行命令后按回车，命令执行结束，提示符再次出现：

```text
username@MacBook demo % pwd
/Users/username/demo
username@MacBook demo %
```

在文档中，为了避免把提示符误当成命令，通常会把输入和输出分开写：

```bash
pwd
```

可能输出：

```text
/Users/username/demo
```

启动交互程序后，界面会发生变化。例如执行：

```bash
less README.md
```

此时按字母 `q` 会退出 `less`，而不是把 `q` 当作 zsh 命令。执行：

```bash
claude
```

或：

```bash
codex
```

之后，输入内容通常会被当成 Prompt、斜杠命令或选项。Shell 中的部分编辑快捷键可能被程序接管。

当你不确定自己在哪一层时，可以先观察：

- 是否还能看到熟悉的 Shell 提示符；
- 界面底部是否显示快捷键提示；
- 按 `q`、`Esc` 或 `Ctrl + C` 是否有程序自己的说明；
- 上一步是否刚启动了 `less`、Vim、Python、SSH 或 AI CLI。

不要在不确定的界面里连续按回车。权限审批界面可能把回车解释为接受默认选项，Shell 则会执行当前输入行。

---

## 4. 回车为什么有时执行命令，有时只是发送消息

在普通 zsh 中，回车会把当前整行交给 Shell 解析。下面这行包含程序名和参数：

```bash
ls -la
```

zsh 找到 `ls`，把 `-la` 作为参数传给它，然后 Terminal 显示结果。

在 Claude Code 或 Codex 中，回车通常用于提交 Prompt或确认界面选项。程序可能根据 Prompt 再决定是否调用 Shell、读取文件或申请权限。此时你输入的文字不是直接由 zsh 执行。

可以通过一个简单对比理解：

```text
Shell 中输入：pwd
→ Shell 直接运行 pwd

AI CLI 中输入：请告诉我当前目录
→ AI CLI 先理解请求
→ 可能调用 pwd 或读取环境
→ 再组织回答
```

两种方式最后都可能显示目录，但中间过程和权限边界不同。AI CLI 给出的文字也不能替代你亲自执行 `pwd` 后看到的真实输出。

---

## 5. 一个窗口里可以进入远程机器

执行 SSH 后，Terminal 窗口仍在 Mac 上，但 Shell 已经运行在远程机器中。例如：

```bash
ssh YOUR_USERNAME@SERVER_IP
```

登录成功后，提示符可能从：

```text
username@MacBook ~ %
```

变成：

```text
username@ubuntu:~$
```

外观变化可能很明显，也可能几乎看不出来。远程登录后应立即执行：

```bash
hostname
whoami
pwd
```

可能看到：

```text
ubuntu-gpu
username
/home/username
```

这表示接下来的删除文件、安装软件和运行 Python 都发生在 `ubuntu-gpu` 上。Terminal 只是把远程输出显示在 Mac 屏幕上。

如果你原本以为自己还在 Mac，却看到 `/home/username` 而不是 `/Users/username`，先停止后续操作并重新确认连接状态。退出远程 Shell 可以执行：

```bash
exit
```

退出后再次运行 `hostname`，确认已经回到 Mac。

---

## 6. 关闭窗口会不会停止程序

在普通终端会话中直接运行：

```bash
python train.py
```

这个程序通常与当前 Shell 和终端会话相连。关闭窗口、退出 Shell 或断开 SSH 后，程序可能收到挂断信号并终止。是否终止还取决于程序、Shell 和启动方式，不能仅凭“窗口关了”判断任务仍在运行。

远程长任务常用 tmux。一个基本过程是：

```bash
tmux new -s train
python train.py
```

需要暂时离开时，按 `Ctrl + b`，松开后再按小写 `d`。这会让 tmux 会话继续运行并返回普通 Shell。重新连接后执行：

```bash
tmux attach -t train
```

tmux 能应对终端关闭和 SSH 断线，但不能抵抗远程机器关机、断电、内核崩溃或训练程序自身退出。重要任务仍需保存日志和 checkpoint。

---

## 7. 清屏只是改变显示

执行：

```bash
clear
```

或者在普通 zsh 中按 `Ctrl + L`，会把当前显示区域整理干净。它不会撤销已经执行的命令，也不会删除文件、停止程序或清空 Shell 历史。

可以做一个安全实验：

```bash
printf 'terminal practice\n' > /tmp/terminal-practice.txt
clear
cat /tmp/terminal-practice.txt
```

清屏后仍然会看到：

```text
terminal practice
```

文件一直存在，只是之前的屏幕内容被移出了当前视图。

如果曾经把 API Key 或密码直接输入 Shell，`clear` 不能消除泄露风险。命令可能进入 `~/.zsh_history`，终端软件也可能保存滚动记录。此时应根据凭证类型考虑撤销或轮换，而不是只清屏。

---

## 8. 集成终端没有改变命令运行位置

VS Code 集成终端只是把终端界面嵌入编辑器。直接在本地打开项目时，命令通常仍在 Mac 上执行；通过 VS Code Remote SSH 连接 Ubuntu 后，集成终端中的命令会在远程 Ubuntu 执行。

可以在每次打开新终端后运行：

```bash
hostname
whoami
pwd
printf 'shell=%s\n' "$SHELL"
```

这四项分别确认机器、用户、目录和 Shell。准备执行删除、安装、训练或修改权限的命令时，再检查一次并不多余。

如果 VS Code 左下角显示远程连接，但 `hostname` 输出仍是 Mac 名称，可能是你新建了本地终端而不是远程终端。以命令输出为准，不要只凭编辑器界面判断。

---

## 9. 输入或快捷键异常时的检查顺序

遇到“按键失效”“输入不显示”或“命令行为和教程不同”时，可以按下面的顺序检查：

1. 当前焦点是否真的在终端输入区域；
2. 当前程序是 Shell、分页器、编辑器还是 AI CLI；
3. `hostname` 显示的是哪台机器；
4. `pwd` 显示的当前目录是什么；
5. 当前 Shell 和终端应用分别是什么；
6. tmux、Vim 模式或程序快捷键是否接管了按键。

在普通 Shell 中可以运行：

```bash
printf 'terminal=%s\n' "$TERM_PROGRAM"
printf 'shell=%s\n' "$SHELL"
hostname
pwd
```

如果当前程序没有返回提示符，先使用该程序自己的退出方式。例如 `less` 使用 `q`，Vim 通常使用 `:q`，前台命令常用 `Ctrl + C` 请求中断。不要在不了解状态时直接关闭窗口，因为窗口中可能还有未保存内容或正在运行的任务。

---

## 10. 读完这一章应该记住什么

Terminal 是显示和输入文字的界面，Shell 是解释命令的程序，`git`、`python` 和 `ssh` 是由 Shell 启动的具体程序。启动交互程序或登录远程机器后，窗口本身没有决定命令在哪里执行；真正重要的是当前程序、当前机器和当前目录。

继续阅读：

- [Shell 到底是什么](03-Shell到底是什么.md)
- [zsh 到底是什么](04-zsh到底是什么.md)
- [命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
