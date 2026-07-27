# 05 Claude Code 接入 DeepSeek 与第三方供应商

> 最近核对：2026-07-28
>
> Claude Code、DeepSeek API、第三方供应商和 CC Switch 都可能持续更新。实际配置前，请同时查看当前官方文档和本机版本。

Claude Code 是终端编程客户端。它负责项目读取、文件修改、工具调用、权限询问和会话管理；真正完成推理和生成代码的模型，则由后端供应商提供。

因此可以把整个链路分成四层：

```text
Claude Code 客户端
→ 负责终端交互和工具执行

接口协议
→ 客户端与模型后端通信的格式

模型供应商
→ 提供接口、计费和数据处理

具体模型
→ 实际完成推理和代码生成
```

理解这四层后，就能更容易判断问题出在客户端、配置、网络、模型映射还是供应商接口。

---

## 1. 常见接入方式

Claude Code 可以通过多种方式获得模型能力。

### Anthropic 官方账户或 API

适合希望直接使用 Claude 模型和 Claude Code 完整兼容能力的用户。

常见形式包括：

- Claude App 账户；
- Anthropic Console API；
- 组织统一配置的认证方式。

### Amazon Bedrock 或 Google Vertex AI

企业环境可以通过受支持的云平台接入，由组织统一管理身份、费用和审计。

### DeepSeek 官方 Anthropic 兼容接口

DeepSeek 官方提供 Claude Code 接入说明和 Anthropic 兼容接口。终端中仍然运行 `claude`，但实际模型请求发送到 DeepSeek。

这条路线适合：

- 主要使用 DeepSeek 模型；
- 希望继续使用 Claude Code 客户端；
- 能够自行管理 API Key、端点和模型映射；
- 接受按照 DeepSeek API 规则计费和处理数据。

### 企业或自建 LLM Gateway

团队可以通过企业网关统一处理：

- 身份认证；
- 模型路由；
- 费用统计；
- 日志审计；
- 限流和故障转移。

### CC Switch

需要管理多套供应商配置时，也可以使用 CC Switch。它可以帮助切换 Claude Code、Codex 等工具使用的供应商、端点和模型配置。

CC Switch 的界面、配置格式和支持范围可能随版本变化，本书不重复维护完整操作教程。具体安装、添加供应商和切换方法，请查看：

- [CC Switch 官方 GitHub 仓库](https://github.com/farion1231/cc-switch)
- [CC Switch 官方使用文档](https://github.com/farion1231/cc-switch/tree/main/docs)

---

## 2. 使用 DeepSeek 官方接口

### 2.1 先安装并确认 Claude Code

如果尚未安装，可以根据 Claude Code 当前官方文档选择安装方式。

使用 npm 时，常见命令为：

```bash
npm install -g @anthropic-ai/claude-code
```

安装后检查：

```bash
type -a claude
claude --version
claude doctor
```

如果 `type -a` 显示多个路径，应先确认当前 Shell 实际调用哪一个版本，不要继续重复安装。

---

### 2.2 配置 DeepSeek 端点和模型

截至 2026-07-28，DeepSeek 官方文档给出的 macOS / Linux 配置方式使用 Anthropic 相关环境变量。

示例结构如下：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="YOUR_DEEPSEEK_API_KEY"
export ANTHROPIC_MODEL="CURRENT_DEEPSEEK_MODEL"
```

某些版本还可能需要为 Opus、Sonnet、Haiku 或子 Agent 设置模型映射。模型名称和变量应以 DeepSeek 当前官方文档为准，不要长期复制旧博客中的固定值。

`YOUR_DEEPSEEK_API_KEY` 和 `CURRENT_DEEPSEEK_MODEL` 都是占位符，必须替换为当前真实配置。

不要把 API Key：

- 写进 Git 仓库；
- 放进教程截图；
- 粘贴到公开聊天；
- 直接提交到 `.env`；
- 保存在多人可读的脚本中。

---

### 2.3 验证环境变量

可以显示端点和模型，但不要打印 Token：

```bash
printf '%s\n' "$ANTHROPIC_BASE_URL"
printf '%s\n' "$ANTHROPIC_MODEL"
test -n "$ANTHROPIC_AUTH_TOKEN" && echo "API Key 已设置"
```

然后进入一个 Git 项目：

```bash
cd ~/Projects/my-project
pwd
git status
claude
```

第一次验证应使用只读任务：

```text
只读分析当前项目的入口文件和测试方式。
不要修改文件，不要执行 Git 写操作。
```

确认文本响应、文件读取和基础工具调用正常后，再开始修改代码。

---

### 2.4 环境变量会保留多久

在终端中直接运行 `export`，通常只影响当前 Shell 以及从它启动的程序。关闭窗口后，新终端未必继续保留。

需要长期使用时，可以选择：

- 系统密码管理工具；
- 专用密钥管理器；
- 可信的本地供应商配置工具；
- 权限受限且不会进入 Git 的本地配置文件。

不要因为 `.zshrc` 是隐藏文件，就把它当作加密保险柜。写入真实 Key 前，应先理解本机同步、备份和文件权限情况。

---

## 3. 更换后端后可能出现的差异

Anthropic 兼容接口不代表所有行为都与 Claude 模型完全相同。

可能存在差异的地方包括：

- 工具调用格式和成功率；
- 长上下文支持；
- 子 Agent 模型映射；
- Prompt 缓存；
- Web Search；
- 推理模式；
- 流式输出；
- 新版 Claude Code 功能的适配速度。

排错时至少记录：

```text
Claude Code 版本
实际 Base URL
实际模型名称或映射
供应商返回的错误信息
任务是否涉及工具调用
```

不要只写“Claude Code 报错了”。客户端能够启动，不代表后端接口完整支持当前任务；普通聊天正常，也不代表文件修改、工具调用和子 Agent 一定正常。

---

## 4. 常见故障

### 仍然要求登录 Anthropic

可能原因：

- 当前终端没有加载供应商配置；
- 环境变量没有传给 Claude Code 进程；
- Base URL 或认证变量写错；
- CC Switch 中的配置没有启用；
- 本地代理或网关没有运行。

检查：

```bash
printf '%s\n' "$ANTHROPIC_BASE_URL"
test -n "$ANTHROPIC_AUTH_TOKEN" && echo "Token 已设置"
type -a claude
claude --version
```

不要把 Token 本身打印到截图中。

### 返回 401 或认证失败

检查：

- API Key 是否属于当前供应商；
- Base URL 是否与 Key 匹配；
- Key 是否已停用；
- 账户是否有可用额度；
- 当前接口要求使用哪个认证变量；
- 企业网关是否要求额外请求头。

### 模型名称错误

不要凭记忆猜模型 ID。查看供应商当前文档，并检查主模型和角色模型映射。

### 普通聊天正常，但工具调用失败

可以逐步缩小测试：

1. 纯文本只读问答；
2. 读取一个项目文件；
3. 执行无副作用的只读命令；
4. 修改一个测试文件；
5. 测试子 Agent 或复杂工具调用。

这样更容易定位是基础接口、工具协议、权限还是模型映射问题。

### 新终端中配置消失

手工 `export` 默认只属于当前 Shell。需要长期配置时，应采用安全的持久化方式，而不是每次把 API Key 复制进命令历史。

---

## 5. 选择接入路线时看什么

### 直接使用 Anthropic

适合希望获得 Claude 模型和 Claude Code 新功能完整兼容的用户。

### 直接使用 DeepSeek

适合主要使用 DeepSeek，并希望保持较短请求链路的用户。

### 使用 CC Switch

适合需要管理和切换多套供应商配置的用户。具体能力和操作以 CC Switch 官方文档为准。

### 使用企业网关

适合需要统一认证、审计、成本控制和模型路由的团队。

无论使用哪种后端，Claude Code 对文件、Shell 命令、网络和扩展系统的权限边界都不会自动消失。修改后仍应运行测试并检查：

```bash
git status --short
git diff --stat
git diff
```

---

## 官方与项目参考

- [DeepSeek：接入 Claude Code](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code/)
- [DeepSeek：Anthropic API](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api)
- [Anthropic：LLM Gateway configuration](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)
- [CC Switch 官方 GitHub 仓库](https://github.com/farion1231/cc-switch)
