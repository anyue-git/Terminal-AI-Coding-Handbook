# 03 Headless、Worktree 与扩展系统

> 官方产品名：Grok Build
>
> 最近核对：2026-07-28

Grok CLI 不只有全屏 TUI。它还可以用于脚本和 CI，创建独立 Git Worktree，并加载 Skills、Plugins、Hooks、MCP 等扩展。

这些能力越强，越要分清：谁在执行、执行在哪个目录、能访问什么、结果怎样验证。

---

## 1. Headless 是什么

Headless 表示不进入全屏界面，直接提交任务并输出结果。当前常见形式是：

```bash
grok -p "只读解释当前项目架构"
```

适合：

- 脚本；
- CI；
- 批量只读检查；
- 固定格式输出；
- 无法使用 TUI 的环境。

不适合直接用于模糊重构、生产数据库、高权限系统配置、不可逆删除或无人复核的推送。

---

## 2. 输出格式怎么选

当前官方文档提供普通文本、JSON 和流式 JSON 等输出方式。示例：

```bash
grok -p "列出项目中的 TODO" --output-format json
```

自动化不能只判断输出中有没有 `success`。还要检查：

- 进程退出状态；
- Git diff；
- 测试结果；
- 生成文件；
- 是否超出允许范围。

结构化输出只是更方便程序读取，不是正确性证明。

---

## 3. 工作目录必须明确

```bash
cd PROJECT_PATH
pwd
git branch --show-current
git status --short
grok -p "只读检查当前项目"
```

当前版本支持时，也可以使用工作目录参数。具体形式以：

```bash
grok --help
```

为准。

自动化日志至少记录目录、分支、Git 状态和 Grok 版本。

---

## 4. Headless 会话仍然不是项目快照

Headless 可以创建和恢复会话，但会话只保存上下文。

恢复前先运行：

```bash
pwd
git status
git log -5 --oneline
```

然后要求 Agent 重新核对当前文件、分支、配置和测试状态，不要直接沿用旧假设。

---

## 5. Headless 中不要随便开启全自动批准

自动化环境没有人及时阅读每个命令，所以 Always-approve 的风险比交互模式更高。

更稳妥的设计：

```text
固定工作目录
→ 明确工具白名单
→ 限制网络
→ 设置最大轮数和超时
→ 只允许必要文件
→ 检查退出状态、测试和 diff
```

具体的 Allow、Deny、Sandbox 和最大轮数参数，以当前 `grok --help` 为准。

---

## 6. Worktree 是什么

Git Worktree 允许同一个仓库同时拥有多个独立工作目录：

```text
主工作区
→ 人工正在使用

任务 Worktree
→ Agent 在另一个目录修改
```

它比多个 Agent 共享同一个未提交工作区安全得多。

Grok 当前支持创建 Worktree 的入口，具体参数查看：

```bash
grok --help
grok worktree --help
```

不要只凭旧教程记住某个参数，因为 Worktree 命令和默认分支策略可能变化。

---

## 7. Worktree 不等于完整隔离

Worktree 只隔离 Git 工作目录，不自动隔离：

- 家目录；
- 环境变量；
- SSH 密钥；
- Docker Socket；
- 网络；
- 数据集与缓存；
- 系统服务。

可以把它理解成给两个 Agent 分了两张桌子，不是给它们各建了一栋楼。

移除 Worktree 前，先检查分支、未提交修改和仍需保留的提交。

---

## 8. 多个 AI CLI 怎样配合

不推荐：

```text
Claude Code + Codex CLI + Grok CLI
同时修改同一个工作区
```

更合理的是：

```text
Worktree A
→ Grok 实现方案 A

Worktree B
→ Codex 实现方案 B 或只读审查

主工作区
→ 人工比较和整合
```

最终比较：

```bash
git diff main...BRANCH_A
git diff main...BRANCH_B
```

测试结果也要分别对应各自分支。

---

## 9. Skill 是什么

Skill 是一组可复用的 Agent 指令和资源，可能包含：

- Markdown 指令；
- 脚本；
- 参考资料；
- 模板和资源文件。

它不是普通 Prompt。只要其中包含脚本或工具调用，就可能读取文件、访问网络和修改项目。

启用前检查来源、脚本内容、读写路径、环境变量、MCP 和 Git 操作。

---

## 10. Plugin 与 Marketplace

Plugin 可能组合：

- Skills；
- Agents；
- Hooks；
- MCP Servers；
- LSP Servers；
- 其他扩展资源。

Marketplace 只是插件来源列表，不代表每个插件都经过 xAI 安全审查。

安装前确认维护者、仓库、更新记录、自动脚本、Hooks 和 MCP。不要因为插件名字写着“效率提升”就默认给它全部权限。

---

## 11. Hooks 会自动执行

Hook 可以在工具调用或会话事件前后运行脚本，例如格式检查、测试和审计记录。

风险包括：

- 反复触发；
- 大范围格式化；
- 写入日志中的敏感信息；
- 调用网络；
- 自动提交或推送；
- 执行未审查的仓库脚本。

更稳妥的 Hook 应优先检查并报告，而不是自动完成高风险写操作。

---

## 12. MCP 连接外部工具和数据

MCP 可以接入文档、数据库、浏览器、GitHub 和内部服务。

启用前确认：

- 服务由谁维护；
- 能读取和写入什么；
- 凭据保存在哪里；
- 是否发送源码和日志；
- 返回内容是否可信；
- 是否符合组织政策。

MCP 返回的网页、Issue 或文档可能包含提示注入。它们只能作为数据，不能自动成为新的高优先级指令。

---

## 13. 扩展来源先用 `grok inspect` 核对

```bash
grok inspect
```

它可以帮助确认当前目录加载了哪些规则、Skills、Plugins、Hooks 和 MCP。

克隆陌生仓库后，先审查这些来源，再决定是否运行 Agent。仓库中的扩展配置也是代码供应链的一部分。

---

## 14. ACP 与编辑器集成

ACP 可以让 Grok 作为 Agent 接入编辑器或其他客户端。接入以后仍要确认：

- 工作目录；
- 权限模式；
- Sandbox；
- 客户端传入了哪些文件；
- 会话和日志保存在哪里；
- 是否存在额外网络与扩展。

换了界面，不代表权限边界自动变小。

---

## 15. 自动化结束时检查什么

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

同时记录：

```text
执行命令
退出状态
测试结果
生成文件
未验证内容
使用的模型和版本
加载的扩展
```

如果任务本来应该只读，任何 diff 都应先解释。

---

## 一份 Headless 任务模板

```text
目标：

工作目录：

允许工具：

允许修改：

禁止修改：

网络：

验证命令：

输出格式：

最大轮数与超时：

停止条件：
- 需要扩大范围；
- 需要更高权限；
- 测试结果矛盾；
- 连续失败；
- 无法找到足够证据。

不要执行 git add、commit 或 push。
```

延伸阅读：

- [权限、Sandbox 与项目配置](02-权限Sandbox与项目配置.md)
- [复杂任务拆分与独立复核](../Part-12-AI开发工作流/05-复杂任务拆分与独立复核.md)
- [三个 AI CLI 怎么选](../Part-12-AI开发工作流/06-Claude-Code-Codex-Grok对照与协作.md)

官方参考：

- [Grok headless scripting](https://docs.x.ai/build/cli/headless-scripting)
- [Grok CLI reference](https://docs.x.ai/build/cli/reference)
