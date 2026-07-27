# 终端与 AI CLI 快速入门

> 适合第一次打开终端，或者隔了一段时间想快速找回手感的读者。
>
> 预计阅读和练习时间：20–30 分钟。

这篇只带你走一遍最短可用路线：知道命令在哪里执行，进入项目，用 Git 留好退路，启动一个 AI CLI，最后亲自检查它改了什么。

更短的版本在这里：

- [终端十五分钟上手](../00-快速开始/01-终端十五分钟上手.md)
- [AI CLI 快速上手](../00-快速开始/02-AI-CLI快速上手.md)

---

## 1. Terminal、Shell 和 CLI 到底是什么关系

可以先这样理解：

```text
Terminal
→ 显示文字、接收键盘输入的窗口

Shell
→ 理解并执行命令的程序，macOS 默认通常是 zsh

CLI
→ 通过命令行使用的具体工具
```

例如：

```bash
cd ~/Projects
```

通常由 zsh 解释；而下面这些命令会启动不同工具：

```bash
git status
claude
codex
grok
```

进入 Claude Code、Codex CLI 或 Grok CLI 后，你面对的不再只是普通 Shell，而是一个能读取文件、修改代码和执行命令的编程 Agent。

详细阅读：

- [Terminal 到底是什么](../Part-01-基础篇/02-Terminal到底是什么.md)
- [Shell 到底是什么](../Part-01-基础篇/03-Shell到底是什么.md)
- [zsh 到底是什么](../Part-01-基础篇/04-zsh到底是什么.md)

---

## 2. 每次动手前，先回答三个问题

```text
我在哪台机器？
我在哪个目录？
这条命令会读取或修改什么？
```

检查机器、用户和目录：

```bash
hostname
whoami
pwd
```

查看当前目录：

```bash
ls
ls -la
```

如果通过 SSH 登录 Ubuntu，窗口可能和 Mac 上长得差不多，但命令已经在远程机器执行。终端不会主动提醒你“现在踩的是别人家的地板”，所以 `hostname` 和 `pwd` 很值得多看一眼。

---

## 3. 怎样在目录之间移动

进入项目：

```bash
cd ~/Projects/my-project
```

回到上一级：

```bash
cd ..
```

返回家目录：

```bash
cd ~
```

回到刚才所在的目录：

```bash
cd -
```

目录名有空格时使用引号：

```bash
cd "My Project"
```

每次进入重要目录后，可以立即确认：

```bash
pwd
ls -la
```

详细阅读：

- [文件系统、目录与路径](../Part-01-基础篇/05-文件系统目录与路径.md)
- [pwd、ls 与 cd](../Part-02-终端命令/01-pwd-ls-cd.md)

---

## 4. 先记住几个真正高频的快捷键

在 macOS 默认 zsh 的常见 Emacs 键位中：

```text
Ctrl + A
→ 移到行首

Ctrl + E
→ 移到行尾

Ctrl + W
→ 删除光标左侧一个单词

Ctrl + U
→ 删除当前整行

Ctrl + C
→ 中断当前前台程序

Ctrl + R
→ 搜索历史命令

方向键上 / 下
→ 浏览历史命令
```

快捷键会受到 Vi 模式、插件、tmux 和 AI CLI 全屏界面的影响。想确认本机 zsh 的实际绑定，可以运行：

```bash
bindkey '^U'
bindkey '^W'
```

在 AI CLI 里按键可能由工具自己的界面处理，不一定继续遵循 zsh。

详细阅读：

- [命令行编辑核心快捷键](../Part-03-Shell快捷键/01-命令行编辑核心快捷键.md)
- [快捷键速查表](../Appendix/快捷键速查表.md)

---

## 5. 文件操作只需要先掌握这一组

创建空文件：

```bash
touch notes.md
```

创建目录：

```bash
mkdir practice
mkdir -p project/src
```

查看短文件：

```bash
cat notes.md
```

分页查看长文件：

```bash
less README.md
```

在 `less` 中：

```text
q       退出
/word   搜索 word
n       跳到下一个匹配
```

复制：

```bash
cp notes.md notes-backup.md
```

移动或重命名：

```bash
mv notes.md project-notes.md
```

按名称找文件：

```bash
find . -name 'README.md'
```

搜索项目文字：

```bash
rg "TODO"
```

没有安装 ripgrep 时，可以使用：

```bash
grep -R "TODO" .
```

查看某个命令最终从哪里运行：

```bash
type -a python
type -a git
type -a claude
```

详细阅读：

- [创建、复制、移动与删除](../Part-02-终端命令/02-创建复制移动与删除.md)
- [查看文本文件与日志](../Part-02-终端命令/03-查看文本文件与日志.md)
- [搜索文件与文本](../Part-02-终端命令/04-搜索文件与文本.md)

---

## 6. 删除和程序中断要分清

删除文件：

```bash
rm FILE_NAME
```

删除前先确认当前目录和目标：

```bash
pwd
ls -la TARGET
```

递归删除、通配符、管理员权限和项目外路径都需要额外小心。不要在没看懂路径时复制一条气势很足的删除命令；终端不会因为你是新手就自动把文件放回回收站。

程序卡住时，先按：

```text
Ctrl + C
```

不小心按了 `Ctrl + Z` 时，程序通常只是暂停。查看任务：

```bash
jobs
```

恢复到前台：

```bash
fg
```

详细阅读：

- [危险命令清单](../Appendix/危险命令清单.md)
- [进程、前台、后台与任务控制](../Part-02-终端命令/06-进程前台后台与任务控制.md)

---

## 7. 让 Git 记录项目发生了什么

进入项目后先运行：

```bash
git status
git branch --show-current
```

为任务创建分支：

```bash
git switch -c task/fix-parser
```

分支名尽量写任务，不要只写 `ai-test-final-2`。未来的你看到后者，通常只能推断当时已经有点急了。

AI 修改后检查：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

其中：

- `git status` 告诉你哪些文件变了；
- `git diff --stat` 显示改动规模；
- `git diff` 显示具体内容。

只暂存确认过的文件：

```bash
git add src/example.py tests/test_example.py
```

检查暂存区：

```bash
git diff --cached --name-status
git diff --cached
```

不推荐新手默认使用：

```bash
git add .
```

它可能把缓存、日志和无关修改一起放进提交。

详细阅读：

- [Git 心智模型](../Part-04-Git/01-Git心智模型.md)
- [日常提交与复核流程](../Part-04-Git/02-日常提交与复核流程.md)

---

## 8. 启动 AI CLI 前的固定动作

进入项目：

```bash
cd PROJECT_PATH
```

确认环境：

```bash
hostname
pwd
git status
git branch --show-current
```

确认工具路径：

```bash
type -a claude
type -a codex
type -a grok
```

不要从家目录、下载目录、云盘根目录或同时包含多个仓库的父目录启动 Agent。启动目录会直接影响它能看到什么。

---

## 9. Claude Code 不只有官方订阅这一种接入方式

启动命令是：

```bash
claude
```

Claude Code 是客户端。真正处理请求的模型后端，可以根据条件选择：

- Anthropic 官方账户或官方 API；
- DeepSeek 官方提供的 Anthropic 兼容接口；
- 团队部署的 LLM Gateway；
- 通过 CC Switch 管理的正规第三方供应商。

部分读者无法或不打算使用 Anthropic 官方订阅，这并不代表 Claude Code 客户端完全不能用。DeepSeek 官方文档提供了接入 Claude Code 的环境变量配置；CC Switch 则适合管理多个供应商，但它只是配置切换工具，不替任何中转商担保。

无论选择哪种后端，都要知道：项目内容、Prompt 和终端输出可能发送给实际供应商。直连模型厂商和使用 API 中转商，不是同一层信任关系。

先阅读：

- [Claude Code：安装、登录与启动](../Part-09-Claude-Code/01-安装登录与启动.md)
- [Claude Code：接入 DeepSeek 与第三方供应商](../Part-09-Claude-Code/05-接入DeepSeek与第三方供应商.md)

接入完成后，第一条任务先只读：

```text
先不要修改文件、安装依赖或执行 Git 写操作。

请检查当前目录、Git 状态、README、项目规则、依赖文件和测试入口。
说明：
1. 项目入口；
2. 任务可能涉及的文件；
3. 测试方式；
4. 当前未提交修改；
5. 仍然不确定的地方。

重要结论给出文件路径。
```

---

## 10. Codex CLI 和 Grok CLI 怎样快速开始

Codex CLI：

```bash
codex
```

Grok CLI：

```bash
grok
```

三个工具都应从同一原则起步：先只读调查，再限制文件范围。具体权限名称、登录方式和自动化参数变化较快，应查看当前版本：

```bash
codex --help
grok --help
```

详细阅读：

- [Codex CLI：安装、登录与启动](../Part-10-Codex-CLI/01-安装登录与启动.md)
- [Codex CLI：Sandbox、审批与配置](../Part-10-Codex-CLI/02-Sandbox审批与配置.md)
- [Grok CLI：安装、登录与基础使用](../Part-10B-Grok-CLI/01-安装登录与基础使用.md)
- [Grok CLI：权限、Sandbox 与配置](../Part-10B-Grok-CLI/02-权限Sandbox与项目配置.md)

一次只让一个 Agent 修改同一工作区。多个工具同时改代码，很容易把协作现场变成多人抢同一支笔。

---

## 11. 一份三个工具都能用的任务模板

```text
目标：
[写清楚要解决的问题]

当前阶段：
先只读调查，不要修改文件。

请检查：
- 当前目录和 Git 状态；
- 项目规则与 README；
- 与任务相关的实现；
- 测试入口。

计划中写明：
- 允许修改的文件；
- 每个文件为什么要改；
- 验证命令；
- 风险；
- 停止条件。

禁止：
- 修改范围外文件；
- 安装依赖；
- 读取凭据；
- 删除数据或未跟踪文件；
- 执行 git add、commit 或 push。

确认计划后，只完成一个可验证步骤。
完成后汇报修改文件、执行命令、测试结果、未验证内容和风险。
```

Prompt 不需要写成法律合同，但目标、范围和验证方式不能全靠 Agent 猜。

---

## 12. AI 说“完成”以后该做什么

暂停或退出 Agent，然后运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

检查：

- 是否修改范围外文件；
- 是否出现意外删除；
- 是否改动依赖或锁文件；
- 是否生成日志、缓存或大型文件；
- 是否加入密码、Token、私钥或真实内部地址；
- 测试是否被削弱；
- 是否存在大范围无关格式化。

再运行项目的真实测试，例如：

```bash
python -m pytest
```

实际命令应以项目 README 和配置文件为准。

测试记录至少写明：

```text
执行命令：
退出状态：
通过与失败数量：
未运行部分：
环境限制：
```

Agent 的总结是说明，测试和 diff 才是证据。

---

## 13. Mac 连接 Ubuntu GPU 机器

已经配置局域网或安全组网后：

```bash
ssh gpu-laptop
```

先确认远程机器：

```bash
hostname
whoami
pwd
git status
```

长时间训练使用 tmux：

```bash
tmux new -s train
```

检查 GPU：

```bash
nvidia-smi
```

`nvidia-smi` 正常不等于当前 Python 环境一定能使用 GPU。还需要检查 PyTorch 或其他框架。

tmux 可以防止 SSH 断开直接结束训练，但机器关机、进程崩溃和磁盘写满仍会终止任务。恢复训练需要 checkpoint，不是靠 tmux 施魔法。

详细阅读：

- [SSH 基础与首次连接](../Part-05-SSH/01-SSH基础与首次连接.md)
- [Mac 与 Ubuntu 局域网部署](../Part-11-GPU远程开发/01-Mac与Ubuntu局域网部署.md)
- [Mac 到 Ubuntu GPU 的端到端案例](../Part-12-AI开发工作流/07-Mac到Ubuntu-GPU端到端案例.md)

---

## 14. 最短记忆卡片

```text
看机器：hostname
看位置：pwd
看文件：ls -la
进目录：cd PATH
回上级：cd ..
看长文件：less FILE
找文字：rg TEXT
中断程序：Ctrl + C
看 Git：git status
看修改：git diff
连远程：ssh HOST
保持任务：tmux
Claude Code：claude
Codex CLI：codex
Grok CLI：grok
```

使用 AI CLI：

```text
先调查
→ 定范围
→ 改一小步
→ 跑测试
→ 看 diff
→ 人工决定是否提交
```

---

## 下一步阅读

- [全书目录](../SUMMARY.md)
- [危险命令清单](../Appendix/危险命令清单.md)
- [通用 AI 编程闭环](../Part-12-AI开发工作流/01-通用AI编程闭环.md)
- [权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)
- [Claude Code、Codex CLI 与 Grok CLI 怎么选](../Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)
