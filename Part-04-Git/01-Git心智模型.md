# 01 Git 心智模型

Git 不是“把代码上传到 GitHub”的工具。它首先是本地版本控制系统，用来记录项目状态、比较差异、创建分支和恢复历史。

最重要的结构是：

```text
工作区 Working Tree
→ git add
暂存区 Staging Area
→ git commit
本地提交历史 Repository
→ git push
远程仓库 Remote
```

理解这四层后，大多数 Git 命令都不再像魔法。

---

## 1. 工作区、暂存区和提交

工作区是你和编辑器、AI CLI 直接修改的文件。

查看整体状态：

```bash
git status
```

查看尚未暂存的差异：

```bash
git diff
```

把明确文件加入下一次提交候选：

```bash
git add src/app.py tests/test_app.py
```

查看暂存区：

```bash
git diff --cached
```

创建提交：

```bash
git commit -m "fix: validate login input"
```

提交不是上传。它只是把暂存区内容记录到本地历史。

---

## 2. 暂存区为什么有价值

假设同时修改了：

```text
src/auth.py
README.md
notes.txt
```

这次只想提交登录修复：

```bash
git add src/auth.py
git diff --cached
git commit -m "fix: validate login input"
```

README 和个人笔记仍可留在工作区。

所以不推荐新手默认使用：

```bash
git add .
```

它可能加入日志、缓存、无关格式化和敏感文件。

---

## 3. Commit、HEAD 和分支

提交组成一条有父子关系的历史：

```text
A ← B ← C
```

`HEAD` 表示当前检出位置，通常指向当前分支：

```text
A ← B ← C
        ↑
       main
        ↑
       HEAD
```

查看：

```bash
git branch --show-current
git rev-parse --short HEAD
git log --oneline --decorate --graph -10
```

创建分支：

```bash
git switch -c feature/login-validation
```

分支本质上是可移动的提交指针，不是复制整个项目目录。因此创建分支很快，也适合隔离 AI 修改。

---

## 4. Remote、fetch、pull 和 push

查看远程：

```bash
git remote -v
```

`origin` 只是常见名称，不是 GitHub 专属关键字。

获取远程更新但不自动改当前工作区：

```bash
git fetch origin
```

把本地提交发送到远程：

```bash
git push
```

`git pull` 通常会先 fetch，再 merge 或 rebase。它不是无副作用的“刷新按钮”。执行前先检查：

```bash
git status
git branch --show-current
```

---

## 5. Git 与 GitHub 的区别

```text
Git
→ 本地版本控制

GitHub
→ 托管 Git 仓库并提供 PR、Issue、Actions 和权限管理
```

没有网络也能运行：

```bash
git add
git commit
git branch
git log
```

只有 push、fetch、pull 等操作需要远程连接。

---

## 6. `git status` 是最重要的安全命令

它会告诉你：

- 当前分支；
- 已修改文件；
- 已暂存内容；
- 未跟踪文件；
- 是否正在合并或变基；
- 与远程的关系。

形成固定习惯：

```bash
git status
git diff
git diff --cached
```

分别回答：

```text
整体发生了什么
→ 工作区还改了什么
→ 下一次提交会包含什么
```

---

## 7. Git 能恢复什么，不能恢复什么

Git 擅长恢复：

- 已跟踪文件的历史；
- 已提交版本；
- 分支和提交引用。

Git 不能自动恢复：

- 从未提交过的未跟踪文件；
- 已发送到网络的数据；
- 数据库和云服务写入；
- 项目外文件变化；
- Docker Volume 中的数据。

所以“有 Git”不等于可以随意执行任何命令。

---

## 8. AI CLI 中的最低 Git 边界

开始任务前：

```bash
git status
git switch -c agent/short-description
```

给 Agent 的规则：

```text
只修改当前分支的工作区文件。
不要执行 git add、commit、push、merge、rebase、reset 或 clean。
完成后列出所有变更文件、测试结果和风险。
```

结束后人工检查：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Agent 的总结是陈述，Git 差异才是证据。

---

## 9. 一次最小练习

```bash
mkdir -p ~/terminal-practice/git-model
cd ~/terminal-practice/git-model
git init
printf '# Git Practice\n' > README.md
git status
git add README.md
git diff --cached
git commit -m "docs: add initial README"
printf 'Learn Working Tree and Staging Area.\n' >> README.md
git status
git diff
```

最后一行修改只存在于工作区，还没有进入暂存区或新提交。

继续阅读：

- [日常提交与复核流程](02-日常提交与复核流程.md)
- [分支、合并与安全恢复](03-分支合并与安全恢复.md)
- [Pull Request 与多人协作](04-Pull-Request与多人协作.md)
