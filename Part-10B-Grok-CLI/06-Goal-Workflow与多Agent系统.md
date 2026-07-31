# 06 Goal、Workflow 与多 Agent 系统

> 官方产品名：Grok Build  
> 最近核对：2026-07-31

Grok Build 的 Goal、Deep Research、Workflow、子 Agent 和 Agent Dashboard 组成了一套比普通单会话更复杂的执行系统。它们可以把任务拆成多轮、多角色和可观察的后台流程，但不会自动解决需求错误、权限过宽、证据不足或外部副作用。使用这些能力前，应先掌握单会话、Git diff、测试、Worktree 和恢复方法。

## 1. 先分清 Goal、Workflow、Subagent 与 Dashboard

```text
Goal        自主目标与完成验证
Workflow    由 Host 驱动的可保存 Rhai 脚本
Subagent    独立子会话，承担调查、实现或验证
Dashboard   当前 Pager 进程中的实时会话管理界面
```

它们可以组合，但不是同一种东西。Goal 可能调用后台 Workflow；Workflow 可以启动多个子 Agent；Dashboard 只用于观察和管理当前进程中的会话。Persona 和 Agent Definition 又属于“如何工作”的配置层，不是运行状态。

## 2. `/goal` 有两套驱动

`/goal` 设置、查看、暂停、恢复或清除自主目标：

```text
/goal 将认证模块迁移到新 API
/goal status
/goal pause
/goal resume
/goal clear
```

目标还可以带 Token 预算：

```text
/goal 将认证模块迁移到新 API --budget 120000
```

当前配置文档说明，Goal 的运行方式取决于 Background Workflows：

```text
Background Workflows 开启
→ Host-owned Workflow Engine 驱动每轮并验证完成候选

Background Workflows 关闭
→ 回退到模型可见的旧式 update_goal 工具
```

是否显示 `/goal` 本身还受独立的 Goal Feature 开关控制。因此，“关闭 Workflow”不一定让 `/goal` 完全消失，也不代表 Goal 仍以相同机制运行。

Goal 会跨多个模型轮次工作，并在声称完成前进行独立证据复核。如果复核无法重现结果、缺少可用证据或发现覆盖缺口，目标应保持活动或暂停，并报告具体缺口。这里的 `--budget` 是 Goal Token Budget，不等于 Workflow 的 Agent Budget、外部 API 费用或运行时间。

自主目标仍需明确：

```text
目标与完成条件
允许修改的文件
验证命令
禁止操作
外部资源和费用边界
人工停止点
```

目标系统可以检查证据是否支持完成声明，但不能替用户决定业务需求是否正确，也不能证明生产环境安全。

## 3. Background Workflows 当前默认开启

当前官方配置说明把后台 Workflow 标为默认开启，覆盖：

```text
workflow 工具
.grok/workflows/*.rhai
~/.grok/workflows/*.rhai
/deep-research
/workflow
Goal 的 Host-owned 驱动
```

可以通过用户配置或环境变量关闭：

```toml
[workflows]
enabled = false
```

```bash
export GROK_WORKFLOWS=0
```

关闭后不仅影响 `/workflow` 和 `/deep-research`，还会改变 `/goal` 使用的驱动。排查时不能只问“命令是否存在”，还要确认最终配置和当前驱动。

## 4. `/deep-research` 是有界后台研究 Workflow

使用：

```text
/deep-research 比较 PostgreSQL 17 与 MySQL 9 的迁移风险
```

当前上游描述的流程包括：规划有限问题、收集带来源的结构化主张、使用独立验证分片交叉检查，并只渲染通过验证的主张。失败分片、被丢弃的主张和研究不确定性会作为覆盖限制保留；存在缺口时报告可能标记为 Partial。

命令通常立即返回，进度通过 `/workflows` 查看，完成后的报告自动进入会话。它不等于无限联网搜索，也不保证来源都权威。应明确时间范围、首选来源、排除对象和输出格式；法律、医疗、财务和安全决策仍需专业复核。

## 5. Workflow 是 Rhai 脚本，不是普通 Prompt

项目 Workflow 位于：

```text
<repo-root>/.grok/workflows/*.rhai
```

用户 Workflow 位于：

```text
~/.grok/workflows/*.rhai
```

发现和调用依赖脚本的 `meta.name`，文件名最好与它一致。当前优先级为：

```text
内置 Workflow
> 项目 Workflow
> 用户 Workflow
```

名称冲突时，高优先级定义胜出，因此不同作用域应使用唯一名称。

启动和管理入口包括：

```text
/workflow review-changes {"target":"origin/main...HEAD"}
/workflow pause review-changes
/workflow resume review-changes
/workflow stop review-changes-2
/workflow save review-changes
/workflows
```

同一 Workflow 多次启动会得到会话内唯一显示名，例如 `review-changes`、`review-changes-2`。管理命令使用这个显示名，不需要内部 Run ID。带编号的显示名不是可重复使用的定义名；保存前应选择新的唯一 `meta.name`。

`/workflows` 打开运行面板，显示阶段、Agent 名单、进度和结果。它是运行视图，不是保存脚本的目录浏览器。

## 6. Pause、Resume 与 Restart 的边界

同一进程内暂停再恢复，会继续原始不可变脚本、原始参数、原始 Agent Budget，以及已经提交的 Host 调用结果。要修改脚本或参数，应保存副本、编辑后重新启动，而不是期待普通 Resume 改变原运行定义。

进程重启后，当前上游明确不恢复被中断的 Workflow，因为外部副作用没有稳定的跨进程身份。即使在同一进程内，Resume 也不保证 exactly-once：如果一个外部操作已经执行，但其结果尚未提交到 Workflow 状态就发生暂停，该操作可能再次执行。

因此 Workflow 不适合直接承载没有幂等设计的付款、删除、生产发布、权限变更或数据库迁移。高影响步骤应由人工门槛、幂等键、事务或外部编排系统保护。

## 7. Agent Budget 与 Token Budget 完全不同

Workflow 可以设置 `agent_budget`，限制累计逻辑子 Agent 调用次数。当前上游给出的规则是：

```text
默认值：128
显式范围：1–1024
每次 agent()：消耗 1
parallel() 中每个子项：各消耗 1
Schema 修正重试：不消耗新的逻辑 Agent 名额
```

如果一个并行面板会超过剩余额度，系统会在任何子 Agent 启动前拒绝整个面板。`budget()` 可以返回：

```text
total
spent
reserved
remaining
```

当前文档说明 `reserved` 固定为 0。

普通 `/workflow resume NAME` 不能提高预算。因预算耗尽而暂停的运行，只能由模型或工具发出带更高 `agent_budget` 的恢复请求，而且新上限必须高于已经接纳的 Agent 数量。

必须分别记录：

```text
Goal Token Budget
Workflow Agent Budget
模型/API 费用
运行时间与外层超时
```

## 8. 子 Agent、Agent Definition 与 Persona

子 Agent 默认可以启用，也可以在单次会话中关闭：

```bash
grok --no-subagents
```

或通过环境与配置控制：

```bash
export GROK_SUBAGENTS=0
```

```toml
[subagents]
enabled = true

[subagents.toggle]
explore = true
plan = false

[subagents.models]
explore = "grok-build"
```

`/config-agents`（别名 `/agents`）管理 Agent Definition、默认 Agent 和当前选择；`/personas` 创建、编辑和删除 Persona。Agent Definition 可以指定模型、工具和行为，Persona 主要塑造角色指令。它们都不构成权限隔离。

名称为 `reviewer` 的 Agent 如果仍拥有 Shell、Edit 或 MCP 写入能力，依然可以修改文件和外部系统。实际继承关系必须通过 Agent 定义、Workflow 脚本、权限配置和 `grok inspect` 判断。

## 9. 多 Agent 应保持唯一写入者

更稳妥的职责关系是：

```text
调查 Agent：只读定位入口、测试和风险
实施 Agent：唯一写入者，在独立分支或 Worktree 修改
验证 Agent：运行测试并核对结果
复核 Agent：只读检查 diff、范围和证据
人：处理冲突并决定提交、合并和发布
```

不要让多个 Agent 同时写入同一未提交工作区。需要比较两个实现时，为每个实现建立独立 Worktree：

```bash
grok --worktree implementation-a --ref main
grok --worktree implementation-b --ref main

git worktree list
git diff main...implementation-a
git diff main...implementation-b
```

Worktree 只隔离 Git 目录与分支，不隔离 `~/.grok`、认证、环境变量、SSH、网络、数据库、Docker、GPU、显存和项目外文件。并行训练或服务测试还要显式分配端口、数据库、缓存目录和 GPU。

## 10. 后台系统必须记录完整现场

每个 Goal、Workflow 或多 Agent 任务应记录：

```text
机器、目录、分支与 HEAD
Grok 版本、模型和推理强度
Goal 与 Workflow 的实际驱动
权限模式、Allow/Deny 与 Sandbox
Skill、Plugin、Hook、MCP 和 Agent
目标、预算、最大轮数与停止条件
修改范围、测试、退出状态与未验证内容
外部资源、费用、幂等性和副作用
```

在生产环境、云资源、数据库迁移和发布流程中，后台系统默认只做只读调查和生成方案；写操作应经过人工门槛。所谓“自主完成”只表示系统达到了自身完成条件，不代表用户已经批准提交、部署、合并或发布。

官方参考：

- [Grok Build Slash Commands](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/04-slash-commands.md)
- [Grok Build Configuration](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/05-configuration.md)
- [Grok Build Worktrees](https://docs.x.ai/build/features/worktrees)
- [Grok Build Agent Dashboard](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/23-dashboard.md)
