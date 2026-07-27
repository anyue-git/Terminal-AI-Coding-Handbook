# 04 Codex CLI 与 Git 协作案例

> 最近核对：2026-07-28

Codex 与 Git 的合理分工是：Codex 负责理解、修改和验证；Git 负责隔离、比较、记录和恢复；人负责范围、审批和最终判断。

本章用一个小任务贯穿：修复登录输入为空时仍被接受的问题，并补充回归测试。

---

## 1. 从干净起点开始

```bash
git status
git switch -c fix/login-validation
```

确认：

```bash
git branch --show-current
git status
```

已有未提交修改时，先判断它们是否属于当前任务。不要让 Codex 自动整理、覆盖或混入提交。

---

## 2. 第一轮只读调查

```text
当前阶段只读，不要修改文件或执行 Git 写操作。

请读取登录验证相关的实现、测试和文档，并输出：
1. 当前行为；
2. 真实调用链；
3. Bug 可能原因；
4. 最小修改范围；
5. 建议补充的测试；
6. 仍然不确定的地方。

重要结论给出文件路径。
```

如果 Codex 找错入口、漏掉调用方或提出无关重构，先纠正计划。

---

## 3. 先补失败测试

```text
现在只修改 tests/test_validator.py。
增加一个能够稳定复现空白登录标识问题的最小测试。
不要修改生产代码。
运行该测试，并报告命令、退出状态和失败原因。
```

测试在修改前失败，说明它确实覆盖了问题。失败原因不一致时，停止继续实施。

---

## 4. 再允许最小实现修改

```text
现在允许修改：
- src/auth/validator.py
- tests/test_validator.py

只修复刚才测试覆盖的问题，不重构其他登录逻辑。
运行目标测试和现有认证测试。
不要执行 git add、commit 或 push。
```

一次只改一个可验证的小范围，比“顺便优化整个认证模块”容易审查得多。

---

## 5. 人工检查实际差异

退出或暂停 Codex 后运行：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

重点看：

- 是否修改允许范围外文件；
- 是否出现无关格式化；
- 是否改动依赖或锁文件；
- 是否删除文件；
- 是否留下日志和缓存；
- 测试是否被削弱；
- 是否加入敏感信息。

Codex 的总结是它对修改的描述，Git diff 才是现场记录。

---

## 6. 精确暂存

```bash
git add src/auth/validator.py tests/test_validator.py
```

检查暂存区：

```bash
git diff --cached --name-status
git diff --cached
```

同一文件中混有无关修改时，可以使用：

```bash
git add -p
```

但交互暂存属于进阶操作，每一块都要能说明为什么属于本次任务。

不要默认使用：

```bash
git add .
```

---

## 7. 创建小而清楚的提交

```bash
git commit -m "fix: reject blank login identifier"
```

好的提交应该：

- 只有一个目的；
- 测试和实现配套；
- 不包含无关文件；
- 提交信息描述行为变化。

不要为了追求“只有一个提交”而盲目改写历史。发现遗漏时继续创建清晰提交，通常比新手直接折腾 rebase 安全。

---

## 8. 提交后再次验证

```bash
git status
git log -1 --stat
git show --stat
```

再运行相关测试，例如：

```bash
python -m pytest tests/auth
```

实际命令以项目配置为准。

---

## 9. 用新会话做独立审查

```text
只读审查当前分支相对于 main 的差异，不要修改文件。

重点检查：
- 是否真正修复任务；
- 边界条件；
- 回归风险；
- 安全与性能问题；
- 测试缺口；
- 无关修改。

按严重程度排序，并引用文件和位置。
```

人工再对照：

```bash
git diff main...HEAD
```

AI 审查是第二意见，不是自动合并许可。

---

## 10. 推送前检查

```bash
git status
git log --oneline --decorate -5
git diff main...HEAD --stat
```

确认：

- 当前分支正确；
- 工作区干净；
- 没有凭据或内部文件；
- 没有大型生成物；
- 测试已运行；
- 提交历史能看懂。

然后由人决定是否运行：

```bash
git push -u origin fix/login-validation
```

---

## 11. Pull Request 描述模板

```text
## 变更内容
- 拒绝空白登录标识
- 添加回归测试

## 原因
旧逻辑只处理 null，没有处理空白字符串。

## 验证
- python -m pytest tests/auth

## 风险
- 输入规则更严格，依赖旧行为的调用方可能需要调整

## 未处理
- 登录限流
- 用户名国际化规则
```

PR 描述要帮助审查者理解行为变化，而不是只写“已修复”。

---

## 12. 哪些 Git 操作可以让 Codex直接做

只读操作通常风险较低：

```bash
git status
git diff
git log
git show
```

写操作需要更谨慎：

- 暂存全部文件；
- 创建提交；
- 切换或删除分支；
- 丢弃工作区修改；
- 改写历史；
- 推送和强制推送。

更合适的 Prompt 是：

```text
不要执行 Git 写操作。
结束时只给出建议暂存的文件和建议提交信息。
```

---

## 13. 多个 Agent 不要共享一个未提交工作区

并行任务使用独立 clone、分支或 Git Worktree。Worktree 能隔离工作目录，但不会自动隔离家目录、环境变量、SSH 密钥、Docker Socket 或网络。

最终仍要分别测试并比较：

```bash
git diff main...BRANCH_A
git diff main...BRANCH_B
```

---

## 最后记住三条命令

```bash
git status
git diff
git diff --cached
```

它们分别回答：现在有什么变化、工作区具体改了什么、准备提交的到底是什么。

延伸阅读：

- [Sandbox、审批与配置](02-Sandbox审批与配置.md)
- [交互模式与自动化](03-交互模式与自动化.md)
- [通用 AI 编程闭环](../Part-12-AI开发工作流/01-通用AI编程闭环.md)
