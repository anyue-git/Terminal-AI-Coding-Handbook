# 02 Sandbox、审批与配置

> 最近核对：2026-07-28

Codex CLI 的安全要分成三层：

```text
任务范围
→ 你允许它做什么

审批策略
→ 哪些操作要先问你

Sandbox
→ 已获准的操作实际上能碰到哪里
```

三者不能互相代替。Prompt 写了“不要访问网络”，不等于网络已经被技术上关闭；Sandbox 很严格，也不代表每次修改都合理。

---

## 1. 先看当前状态

进入 Codex 后先查看：

```text
/status
/permissions
```

开始任务前确认：

- 当前模型；
- Sandbox；
- 审批策略；
- 网络状态；
- 工作目录；
- 是否加载项目配置与 MCP。

不要凭“上次好像是只读”判断当前会话。

---

## 2. Sandbox 的三个常见级别

### `read-only`

适合项目体检、代码审查、架构分析和计划生成。它不应修改工作区。

### `workspace-write`

允许在工作区内写入，适合修改源码、测试和文档。仍要确认工作区边界、网络和项目外路径。

### `danger-full-access`

显著扩大访问范围，不应作为普通开发默认值。它只适合明确、短时、可验证并且已有额外隔离的任务。

Sandbox 不是完整虚拟机。当前用户能访问 Docker、远程服务器或高权限工具时，Codex 也可能通过命令扩大影响范围。

---

## 3. 审批策略决定什么时候问你

当前常见策略包括：

```text
untrusted
on-request
never
```

`untrusted` 适合陌生项目和新手；`on-request` 适合已限定范围的日常开发；`never` 不会临时向用户请求批准，适合受控自动化，但不能和过宽 Sandbox 随意组合。

旧版配置中可能看到 `on-failure`。新配置应优先依据当前官方参考，不要从旧博客继续照搬。

---

## 4. 推荐组合

只读分析：

```text
Sandbox：read-only
审批：untrusted 或 on-request
```

普通本地修改：

```text
Sandbox：workspace-write
审批：on-request
```

高权限维护：

```text
Sandbox：danger-full-access
审批：严格人工控制
```

不要把最高权限长期写成全局默认值。

---

## 5. 配置文件与项目规则不是一回事

用户级配置通常位于：

```text
~/.codex/config.toml
```

它适合保存模型、推理强度、Sandbox、审批、网络、MCP 和功能开关。

`AGENTS.md` 更适合保存：

- 项目结构；
- 测试命令；
- 编码规范；
- 禁止修改的目录；
- Git 工作流；
- 项目特定风险。

不要把 API Key 写进会被提交的项目文件。

---

## 6. 不要整份复制陌生人的配置

一份看起来很方便的 `config.toml` 可能同时启用：

- 自动批准；
- 高权限 Sandbox；
- 未知 MCP；
- 宽泛网络访问；
- 过时配置项；
- 第三方代理。

更稳妥的方式是：先备份，每次只加一个配置项，再用 `/status` 和 `/permissions` 验证。

---

## 7. 网络与外部服务

允许网络后，Codex 可能下载依赖、查询文档、调用 API、连接 MCP 或访问远程仓库。

私有项目中要确认：

- 哪些内容会离开本机；
- 外部服务由谁维护；
- 是否记录源码和日志；
- 凭据保存在哪里；
- 是否符合学校、团队或公司要求。

“只查官方文档”也应该通过明确工具与域名实现，而不是开放不受限制的网络。

---

## 8. 审批命令时看什么

至少检查：

```text
当前目录
完整命令和参数
目标路径
是否递归或含通配符
是否覆盖或删除
是否访问网络
是否修改依赖或 Git 历史
是否触及项目外路径
失败后能否恢复
```

看不懂时直接拒绝，并要求：

```text
不要执行。
请逐段解释命令、参数、目标路径、影响范围、失败后果和更保守的替代方案。
```

---

## 9. 项目信任不是装饰

刚下载的陌生仓库、来源不明的压缩包、共享目录和包含未知脚本的示例项目，不应轻易标记为可信。

先审查：

- README；
- 构建脚本；
- 包管理器生命周期脚本；
- Dockerfile；
- `AGENTS.md`；
- MCP 与项目配置。

仓库里的说明和脚本都可能成为提示注入与供应链风险来源。

---

## 10. `codex exec` 的权限边界

非交互任务没有人实时判断弹窗，因此必须显式控制：

- 工作目录；
- Sandbox；
- 审批策略；
- 网络；
- 输出格式；
- 超时与最大重试；
- 允许修改的文件。

不要把 `danger-full-access` 与 `never` 当作普通自动化组合。

---

## 11. Git 仍然是必要检查线

开始前：

```bash
git status
git switch -c task/codex-change
```

结束后：

```bash
git status --short
git diff --name-status
git diff --stat
git diff
```

Git 能恢复很多已跟踪文件修改，但不能撤回已上传的数据、数据库写入、项目外覆盖、Docker Volume 变化或远程主机操作。

---

## 12. 新手可以照着走的流程

```text
进入项目根目录
→ git status
→ 阅读 AGENTS.md 和配置
→ /status 与 /permissions
→ read-only 调查
→ 明确文件和测试范围
→ workspace-write 执行
→ 按需审批
→ 运行测试
→ git diff
→ 人工决定是否提交
```

延伸阅读：

- [安装、登录与启动](01-安装登录与启动.md)
- [交互模式与自动化](03-交互模式与自动化.md)
- [权限与安全边界总览](../Part-12-AI开发工作流/04-权限与安全边界总览.md)

官方参考：

- [Codex security](https://developers.openai.com/codex/security/)
- [Codex configuration](https://developers.openai.com/codex/config-reference/)
