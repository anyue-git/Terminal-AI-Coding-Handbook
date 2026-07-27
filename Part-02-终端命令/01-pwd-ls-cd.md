# 01 `pwd`、`ls` 与 `cd`

这三个命令构成终端导航的基础：

```text
pwd   我在哪里
ls    这里有什么
cd    去另一个目录
```

---

## 1. `pwd`：确认当前目录

```bash
pwd
```

它输出当前工作目录的绝对路径。

进入项目后常用：

```bash
pwd
ls -la
git status
```

在启动 AI CLI、删除文件、运行训练或使用 Docker 前，先确认目录可以避免大量低级错误。

---

## 2. `ls`：查看目录内容

```bash
ls
```

常用组合：

```bash
ls -l
ls -a
ls -la
ls -lh
ls -lah
```

含义：

- `-l`：详细列表；
- `-a`：显示隐藏文件；
- `-h`：更易读的文件大小。

查看其他目录：

```bash
ls -la ~/Downloads
```

预览通配符匹配：

```bash
ls -l *.log
```

这比直接执行批量删除安全得多。

---

## 3. `cd`：切换目录

进入目录：

```bash
cd ~/Projects
```

回上一级：

```bash
cd ..
```

回主目录：

```bash
cd ~
```

回到刚才目录：

```bash
cd -
```

路径有空格：

```bash
cd "My Project"
```

Tab 补全可以减少路径拼写错误。

---

## 4. 一套固定导航流程

```bash
cd ~/Projects/my-project
pwd
ls -la
git status
```

确认无误后再运行：

```bash
claude
```

或：

```bash
codex
grok
```

---

## 5. 常见错误

### `no such file or directory`

检查：

```bash
pwd
ls -la
```

可能是路径拼错、大小写不同、空格未加引号，或目标已经移动。

### `not a directory`

说明目标可能是文件。检查：

```bash
file TARGET
ls -ld TARGET
```

### 切换后不知道去了哪里

```bash
pwd
```

不要只依赖提示符，因为主题可能隐藏或缩短路径。

继续阅读：

- [文件系统、目录与路径](../Part-01-基础篇/05-文件系统目录与路径.md)
- [创建、复制、移动与删除](02-创建复制移动与删除.md)
