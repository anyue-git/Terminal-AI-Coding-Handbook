# 04 CC Switch、ccswitch 与 Cockpit Tools

> 最近核对：2026-07-29

这一章讨论第三方配置管理工具。它们可以减少手工编辑配置的工作量，也可能接触 OAuth 登录缓存、API Key、本地代理和客户端状态。使用前要确认项目来源、版本、备份机制和数据流向。第三方项目的 README 能说明开发者设计了什么功能，但不能证明 OpenAI 或 Anthropic 对所有用法提供支持。

本章涉及的账号应当由读者本人或所属组织合法持有。不要导入购买、借用或来源不明的账号凭证，也不要把多账号工具用于规避平台限制。

---

## 1. 先解决名称混淆

目前至少有两个常被简称为“CC Switch”的项目。

### CC Switch 桌面应用

仓库为 `farion1231/cc-switch`。它是跨平台图形化工具，支持管理 Claude Code、Claude Desktop、Codex、Gemini CLI 等多种客户端的供应商配置、MCP、Skills 和本地路由。它不仅做账号切换，还可能改写客户端配置、管理模型目录或启动本地代理。

### ccswitch 命令行工具

仓库为 `vyshnavsdeepak/ccswitch`。它更专注于 Claude Code 多账号切换，主要保存不同账号的凭证快照，再将选中的账号恢复为活动凭证。在 macOS 上，它使用系统 Keychain；Linux 和 WSL 上则维护权限受限的本地凭证文件。

这两个项目不是同一个软件，安装命令、存储方式和风险边界都不同。搜索教程时应先核对仓库作者和项目地址。

### Cockpit Tools

仓库为 `jlcodes99/cockpit-tools`。它围绕 Codex 等工具提供账号管理、多开实例和本地 API 服务。当前版本还包含面向 Codex `/v1/responses` 和模型列表的本地兼容处理。它更接近“账号与本地网关控制台”，不能简单理解为配置文件编辑器。

---

## 2. 三种工具模式

理解按钮之前，先判断工具采用哪种模式。

### 配置投影

工具内部保存多份供应商设置，当前选中哪一份，就把哪一份写入客户端实际读取的配置文件。

```text
工具数据库中的供应商 A
→ 写入 ~/.codex/config.toml
→ Codex 重启后读取供应商 A
```

这种方式容易理解，但切换时会覆盖活动文件。工具需要维护备份，也要处理用户手工修改与工具内部数据不一致的问题。

### 凭证替换

工具保存多个账号的认证快照，切换时替换 Keychain 或凭证文件。

```text
账号 A 凭证
账号 B 凭证
→ 选择账号 B
→ 更新活动凭证
→ 重启 Claude Code
```

这适合串行切号。两个已经启动的客户端是否能继续分别使用旧账号，取决于它们是否已经把 Token 缓存在内存中，不能把这种偶然状态当作可靠并行方案。

### 本地路由接管

工具启动本地服务，把 Codex 或 Claude Code 的 Base URL 指向 `127.0.0.1`。客户端只与本地服务通信，工具再选择上游账号或供应商。

```text
Codex CLI
→ http://127.0.0.1:PORT/v1
→ 本地网关
→ 账号池或第三方供应商
```

本地路由可以完成协议转换、用量统计和热切换，但也扩大了工具的权限：它可能看到完整 Prompt、源码片段、工具调用和返回内容。

---

## 3. CC Switch 桌面应用通常改什么

CC Switch 会为不同客户端维护供应商卡片，并将活动供应商写入客户端的 live 配置。以 Codex 为例，可能涉及：

- `config.toml` 中的模型、Provider、Base URL 和模型目录；
- `auth.json` 或 Provider 范围的认证字段；
- 本地路由接管时的代理地址；
- 工具自身数据库中的供应商、模型和用量设置。

项目近期版本增加了“保留 Codex 官方认证”的可选设置。启用后，第三方供应商凭证可以写入 Provider 范围配置，而官方 ChatGPT/Codex OAuth 登录继续留在 `auth.json`。该功能当前默认不是强制开启，因此升级或换机后不能假设行为完全相同。

对 Claude Code，CC Switch 可能管理 Base URL、认证环境、模型映射和本地代理。Claude Code 的部分 Provider 数据支持热切换，但这不代表所有环境变量、登录缓存和正在运行的会话都能即时更新。

第一次使用时，先在工具中找到备份、恢复官方配置、数据目录和本地代理开关。没有确认这些功能之前，不要一次导入多个真实账号。

---

## 4. ccswitch 命令行工具如何切 Claude 账号

`vyshnavsdeepak/ccswitch` 的主要逻辑是保存当前 Claude Code 账号凭证，然后在需要时切换活动账号。macOS 上凭证存入系统 Keychain，工具还会处理 `CLAUDE_CODE_OAUTH_TOKEN` 可能覆盖 Keychain 凭证的问题。

典型流程是：

```text
用 Claude Code 登录账号 A
→ ccswitch 保存当前凭证
→ 在 Claude Code 中退出并登录账号 B
→ ccswitch 保存账号 B
→ 以后通过 ccswitch 选择活动账号
→ 重启 Claude Code
```

不要把这理解为“复制一个邮箱地址就能登录”。工具保存的是已经通过官方流程建立的凭证状态。它也不能替代账号本身的授权。

如果 Shell 中一直设置着：

```text
CLAUDE_CODE_OAUTH_TOKEN
```

这个环境变量会按照 Claude Code 的认证优先级覆盖 Keychain 中的订阅登录。此时即使 ccswitch 替换了 Keychain，Claude Code 仍可能继续使用环境变量。排错时应先确认变量是否存在，而不是反复添加账号。

---

## 5. Cockpit Tools 的多开与本地 API

Cockpit Tools 可以管理多个 Codex 账号，并为不同账号启动独立窗口或本地实例。是否真正隔离，需要检查它分别管理了哪些目录、启动参数和凭证，而不是只看界面中出现了两个窗口。

它的本地 Codex API 服务采用另一种模式：客户端向本地 `/v1/responses` 和 `/v1/models` 发送请求，Cockpit 再使用其管理的 OAuth 账号向上游转发。近期发行说明显示，该项目针对 Codex 客户端的请求形状、模型列表和 localhost 代理干扰进行了兼容处理。

这种结构带来便利，也需要额外判断：

- 本地服务监听 `127.0.0.1` 还是所有网络接口；
- 客户端使用的本地 API Key 是什么用途；
- 工具把 OAuth 凭证保存在哪里；
- 请求日志是否包含 Prompt 或源码；
- 账号选择、轮换和失败重试依据什么规则；
- 退出软件后是否恢复原始 Codex 配置。

如果本地服务错误绑定到 `0.0.0.0`，同一局域网中的其他设备可能访问它。新手应优先只监听回环地址，不要为了“远程调用方便”直接开放端口。

---

## 6. 一个不暴露密钥的观察实验

下面的实验用于了解管理工具切换前后修改了什么。不要把输出发到公开群组，也不要对凭证文件执行 `cat`。

### 第一步：记录文件元数据和安全摘要

在 Mac 终端执行：

```bash
mkdir -p ~/switch-observation
chmod 700 ~/switch-observation

for file in \
  ~/.codex/config.toml \
  ~/.codex/auth.json \
  ~/.claude/settings.json \
  ~/.claude.json
do
  if [ -f "$file" ]; then
    stat -f '%N | size=%z | modified=%Sm' "$file"
    shasum -a 256 "$file"
  fi
done > ~/switch-observation/before.txt
```

SHA-256 只用于判断内容是否变化，不能告诉你具体修改了什么，也不能证明文件安全。

### 第二步：只切换一个设置

在管理工具中只做一次操作，例如从官方 Codex 配置切到一个自己拥有 API Key 的测试供应商。不要同时打开本地路由、切账号、改模型和导入 MCP，否则无法判断每项变化来自哪里。

关闭并重新打开对应客户端，确认切换是否生效。

### 第三步：再次记录

```bash
for file in \
  ~/.codex/config.toml \
  ~/.codex/auth.json \
  ~/.claude/settings.json \
  ~/.claude.json
do
  if [ -f "$file" ]; then
    stat -f '%N | size=%z | modified=%Sm' "$file"
    shasum -a 256 "$file"
  fi
done > ~/switch-observation/after.txt

diff -u ~/switch-observation/before.txt \
  ~/switch-observation/after.txt
```

如果 `config.toml` 摘要变化而 `auth.json` 不变，工具可能只切换了 Provider。若 `auth.json` 也变化，说明认证状态可能被改写。若两个文件都不变但客户端地址变成 localhost，则还要检查环境变量、启动参数或工具自己的本地代理状态。

### 第四步：只比较非敏感字段

对于 Codex，可以手工打开 `config.toml`，但先搜索明显的 Token 字段。确认没有秘密后，再比较模型、Provider 和 Base URL。对于 `auth.json`、`.claude.json` 和 Keychain，不建议通过复制正文来观察。

---

## 7. 切换后怎样确认真实路径

### Codex

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
grep -E '^(model|model_provider|openai_base_url)' \
  "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null
```

如果 Base URL 是 localhost，检查工具界面中的本地路由状态和端口。仅凭模型名称不能判断最终上游。

### Claude Code

启动 Claude Code 后运行：

```text
/status
```

查看活动认证和设置来源。在 Shell 中只检查变量是否存在：

```bash
env | grep -E '^(ANTHROPIC_BASE_URL|ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|CLAUDE_CODE_OAUTH_TOKEN)=' \
  | sed 's/=.*$/=<已隐藏>/'
```

如果工具宣称已经切换，但 `/status` 和环境变量仍指向旧配置，应关闭旧进程再测试。

---

## 8. 恢复官方配置

优先使用工具提供的“切换到官方供应商”“退出本地路由”或“恢复备份”。不要在工具仍运行和监控配置文件时，同时手工覆盖 live 文件，否则工具可能立刻再次写回。

恢复后检查：

1. 本地代理是否停止；
2. Base URL 是否不再指向 localhost 或第三方地址；
3. 官方登录是否仍然有效；
4. Shell 启动文件中是否残留环境变量；
5. Codex 或 Claude Code 重启后 `/status` 是否符合预期。

如果工具的备份不可用，再使用自己在修改前保存的配置备份。含凭证文件的恢复应在本机完成，不通过聊天传输。

---

## 9. 风险边界

第三方管理工具可能拥有读取和写入凭证、修改客户端配置、启动本地网络服务以及查看请求内容的能力。安装前至少检查：

- 仓库是否为真正的官方项目地址；
- 最近版本和 Issue 是否显示仍在维护；
- 安装包是否有签名或校验方式；
- 数据目录和备份能否找到；
- 是否默认上传遥测或日志；
- 是否包含赞助中转站预设，以及这些预设是否经过独立验证；
- OAuth 复用是否符合上游平台当前条款。

Anthropic 当前明确区分个人订阅 OAuth 与第三方产品调用场景，并限制第三方代表用户路由 Free、Pro 或 Max 凭证。涉及“把订阅 OAuth 转成其他客户端 API”的功能时，应阅读当前条款和项目风险提示，不能只看技术上能否连通。

### 核对来源

- [CC Switch 项目](https://github.com/farion1231/cc-switch)
- [CC Switch 用户手册](https://github.com/farion1231/cc-switch/blob/main/docs/user-manual/en/README.md)
- [ccswitch 多账号工具](https://github.com/vyshnavsdeepak/ccswitch)
- [Cockpit Tools 项目](https://github.com/jlcodes99/cockpit-tools)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
