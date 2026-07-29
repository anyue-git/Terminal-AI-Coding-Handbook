# 06 Claude Code、Codex CLI 与 Grok Build 对照协作

> 最近核对：2026-07-30
>
> 三个工具迭代都很快。本章只比较稳定的工作方式；安装、参数、认证和权限细节以各自专章、本机 `--help` 与官方文档为准。

Claude Code、Codex CLI 和 Grok Build 都能读取项目、修改文件、运行命令和查看 Git 差异。真正影响选择的，不是抽象的“谁最聪明”，而是：

```text
任务是否需要长时间交互
是否要非交互自动化
项目规则放在哪里
权限与 Sandbox 怎样限制
会话能否恢复或分叉
是否需要 Worktree
输出是否适合脚本处理
由谁独立复核
```

## 1. 不要让三个工具同时编辑同一个目录

最危险的协作方式：

```text
Claude Code
Codex CLI
Grok Build
→ 同时修改同一个未提交工作区
```

这会导致：

- 文件互相覆盖；
- 测试结果对应不上具体版本；
- Agent 读取到对方的中间状态；
- 很难判断某行是谁改的；
- 一个工具回滚时破坏另一个工具的修改。

更稳定的原则：

```text
一个工作区
→ 同一时刻只有一个实施者

其他工具
→ 只读调查、独立复核或在独立 Worktree 工作
```

## 2. 三个工具的稳定定位

| 维度 | Claude Code | Codex CLI | Grok Build |
|---|---|---|---|
| 交互入口 | `claude` | `codex` | `grok` |
| 非交互 | 打印模式等 | `codex exec` | Headless / single prompt |
| 项目规则 | `CLAUDE.md`、Settings 等 | `AGENTS.md`、Codex 配置 | 项目规则、Memory、配置等 |
| 权限思路 | Permission Mode、Allow/Deny、Sandbox | 审批策略与 Sandbox 分开；另有 Permission Profiles | Ask、Auto、Always-approve 与 Sandbox 分开 |
| 会话 | 继续、恢复、分叉等 | 恢复、分叉等 | 列表、恢复、继续、分叉等 |
| 扩展 | Hooks、MCP、子 Agent | MCP、Skills、Hooks、Subagents | Skills、Plugins、Agents、Hooks、MCP、LSP、ACP |
| Worktree | 可配合 Git Worktree | 可配合 Worktree 工作流 | 提供较直接的 Worktree 会话支持 |
| 结构化自动化 | 依当前打印输出能力 | JSONL、Schema、最后消息文件 | JSON、streaming JSON 等 |

表格只帮助判断方向，不能替代版本核对：

```bash
claude --version
claude --help

codex --version
codex --help

grok version
grok --help
```

## 3. Claude Code 适合什么任务

常见适用场景：

- 持续阅读较大代码库；
- 多阶段交互任务；
- 项目已经维护 `CLAUDE.md`；
- 需要 Hooks、MCP 或子 Agent；
- 希望先 Plan，再分批实施；
- 需要在一个会话中持续追踪上下文。

启动：

```bash
claude
```

只读非交互分析可使用当前版本支持的打印模式，例如：

```bash
claude -p "只读分析测试入口，不要修改文件"
```

风险重点：

- 额外目录会扩大读取范围；
- Hooks 能执行本地命令；
- MCP 会连接外部服务；
- 高权限模式会减少人工刹车；
- 长会话可能保留旧假设。

## 4. Codex CLI 适合什么任务

常见适用场景：

- 需要清楚区分审批与 Sandbox；
- 交互开发与 `codex exec` 自动化结合；
- 希望输出 JSONL 或受 Schema 约束的结果；
- 做只读审查、CI 检查或批处理；
- 项目使用 `AGENTS.md`；
- 需要 `codex review`、恢复或分叉。

启动：

```bash
codex
```

只读自动化示例：

```bash
codex exec --ephemeral \
  "只读审查当前 Git diff，不要修改文件"
```

风险重点：

- 不要混用稳定 Sandbox 配置与 beta Permission Profiles；
- `danger-full-access` 与低审批不能作为日常默认；
- 自动化必须设置外部超时和输出契约；
- `--add-dir` 会扩大访问范围；
- ChatGPT 登录与 Platform API Key 的计费路径不同。

## 5. Grok Build 适合什么任务

常见适用场景：

- 需要明确切换 Ask、Auto 和 Always-approve；
- 使用独立 Plan；
- 频繁使用 Worktree 并行试验；
- 需要 Headless、JSON 或 streaming JSON；
- 使用 Skills、Plugins、Agents、Hooks、MCP 或 LSP；
- 需要会话列表、恢复、继续和分叉。

启动：

```bash
grok
```

风险重点：

- Always-approve 只减少询问，不自动缩小访问范围；
- 项目配置不能覆盖所有用户设置；
- Worktree 不是完整安全沙箱；
- 插件、Hook 和 MCP 会扩大能力链；
- 浏览器 OAuth、设备码和 API Key 有明确认证优先级。

## 6. 怎样选择主实施者

### 任务需要长会话和连续理解

选择自己最熟悉、项目规则最完整的交互工具。常见情况下可以让 Claude Code 主实施，但这不是固定结论；项目规则、模型可用性和团队习惯更重要。

### 任务需要受控自动化和结构化输出

Codex `exec` 更适合需要 JSONL、Schema、外层超时和脚本验收的流程。

### 任务需要多个隔离试验

Grok Worktree 工作流较直接；其他工具也能配合普通 Git Worktree。

### 任务主要是只读审查

三个工具都可以。优先选择：

- 与实施者不同的新会话；
- 只读权限；
- 能获取原始需求、diff 和测试证据；
- 不继承实施者总结。

## 7. 最实用的双 Agent 分工

实施者 Prompt：

```text
你负责实施，不负责提交。

先检查项目规则、Git 状态和相关测试。
只允许修改：
- FILE_A
- FILE_B

禁止：
- 修改其他文件；
- 安装依赖；
- 访问外部服务；
- 删除数据；
- git add、commit 或 push。

完成后运行 TEST_COMMAND，并汇报：
- 修改文件；
- 命令和退出状态；
- 测试结果；
- 未验证部分；
- 风险。
```

复核者 Prompt：

```text
你没有参与实现，只负责只读审查。不要修改文件。

根据原始需求、当前 diff 和测试结果检查：
1. 是否满足需求；
2. 是否存在范围外修改；
3. 逻辑、兼容性、错误处理和安全问题；
4. 测试是否足够；
5. 是否存在更小修复；
6. 哪些内容无法验证。

分类为已确认问题、可能问题、无法验证和可选改进。
```

## 8. 三 Agent 分工不等于三人同时写代码

更合理的分工：

```text
Agent A：调查
→ 只读找入口、测试和风险

Agent B：实施
→ 在任务分支或 Worktree 修改

Agent C：复核
→ 只读检查 diff 与测试
```

人负责：

- 确认需求；
- 选择方案；
- 批准高风险命令；
- 分类复核意见；
- 暂存、提交和推送。

## 9. 使用 Worktree 做方案对照

在主工作区执行：

```bash
git status --short
git worktree add ../project-option-a -b experiment/option-a
git worktree add ../project-option-b -b experiment/option-b
```

目录：

```text
project/
→ 人工整合

project-option-a/
→ Agent A 实施最小方案

project-option-b/
→ Agent B 实施另一方案
```

每个 Worktree 开始前检查：

```bash
pwd
git branch --show-current
git status --short
```

比较时使用相同测试和输入，不要只比较两个 Agent 的文字总结。

Worktree 仍共享主目录、凭据、网络、Docker、数据集和部分 Git 元数据。

## 10. 不要让复核者自动修复所有发现

复核输出先由人分类：

```text
必须修复
需要确认
可选改进
误报
```

选定问题后，再交给实施者做一个新的小批次。不要直接说“把审查报告全部修好”。

## 11. 非交互任务的共同要求

无论 Claude、Codex 还是 Grok，脚本化时都应考虑：

- 明确工作目录；
- 使用临时或隔离会话；
- 限制最大轮数；
- 设置外层超时；
- 固定输出格式；
- 保留退出状态；
- 记录执行命令；
- 过滤凭据；
- 防止重试重复写入；
- 任务后检查 Git diff。

自动化成功不能只看模型输出文字，还要看：

```text
进程退出状态
输出文件
测试结果
Git diff
未验证部分
```

## 12. Mac 与 Ubuntu 上不要自动共享 Agent 状态

Mac 和 Ubuntu 是两台独立机器。下面内容不会因为 SSH 或 rsync 自动同步：

- CLI 安装；
- 登录缓存；
- TOML 或 settings；
- CC Switch/Cockpit Tools 状态；
- MCP、Hook、Plugin 和 Skill；
- Shell 环境变量；
- 凭据库。

源码可以同步，认证目录和 Agent 状态不应整目录复制。两台机器分别配置并核对真实 Provider、Base URL 和认证来源。

## 13. 推荐的日常组合

### 简单任务

```text
主力 Agent 实施
→ 人工检查 diff
→ 同一工具新会话只读复核
```

### 中型任务

```text
Claude Code 或熟悉工具调查与实施
→ Codex/Grok 新会话只读复核
→ 人工整合
```

### 自动化审查

```text
Codex exec 或 Grok Headless
→ 结构化只读报告
→ 人工决定是否进入修改任务
```

### 两种方案比较

```text
两个 Worktree
→ 两个独立实施者
→ 相同测试和基准
→ 第三个只读复核
→ 人工选择
```

工具组合不是越多越好。每增加一个 Agent，都增加一份配置、权限、上下文和结果整合成本。

## 14. 最终判断标准

不论使用哪个工具，可靠结果都应包含：

- 明确需求；
- 真实项目证据；
- 限定修改范围；
- 可查看 Git diff；
- 测试命令和退出状态；
- 未验证部分；
- 独立复核；
- 人工提交决定。

工具负责提高调查和修改速度，闭环负责让结果可相信。

## 延伸阅读

- [Claude Code](../Part-09-Claude-Code/01-安装登录与启动.md)
- [Codex CLI](../Part-10-Codex-CLI/01-安装登录与启动.md)
- [Grok Build](../Part-10B-Grok-CLI/01-安装登录与基础使用.md)
- [配置、凭证与多实例](../Part-10C-配置凭证与多实例/01-先分清配置凭证供应商与实例.md)
