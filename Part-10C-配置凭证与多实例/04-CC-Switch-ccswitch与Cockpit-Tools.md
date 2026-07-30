# 04 CC Switch、ccswitch 与 Cockpit Tools

> 最近核对：2026-07-30

本章讨论三款名称相近、实现不同的第三方管理工具。它们能减少手工编辑，也可能接触 OAuth 缓存、API Key、客户端配置、本地代理和完整请求内容。使用前需要确认对应仓库、版本、数据目录、网络监听、备份和恢复方式；账号必须由读者本人或所属组织合法持有，不能导入购买、借用或来源不明的凭证，也不能用多账号工具规避平台限制。

## 1. 分清项目与切换机制

**CC Switch 桌面应用**对应 `farion1231/cc-switch`。当前项目说明把它定位为跨平台 AI 编程工具管理器，覆盖 Claude Code、Claude Desktop、Codex、Gemini CLI、Grok Build 等客户端，并管理 Provider、MCP、Skills、模型与本地代理。它除了切换账号，还可能改写 live 配置、保存供应商信息并启动路由服务。

**ccswitch 命令行工具**对应 `vyshnavsdeepak/ccswitch`，聚焦 Claude Code 多账号切换。它保存已经通过官方流程建立的凭据快照，并把选中账号写回活动凭据；macOS 使用系统 Keychain，Linux/WSL 使用权限受限的本地文件。它还显式处理 `CLAUDE_CODE_OAUTH_TOKEN`：这个环境变量的优先级高于普通登录缓存，若没有清除，即使 Keychain 已切换，Claude Code 仍可能继续使用旧 Token。

**Cockpit Tools**对应 `jlcodes99/cockpit-tools`，当前项目说明把它定位为多种 AI IDE/CLI 的账号、配额和实例管理器。Codex 本地 API 由内置 CLIProxyAPI sidecar 驱动，Cockpit Tools 负责账号同步、配置投影、状态和用量统计；多开功能还涉及独立实例目录与启动参数。它更接近“账号与本地 Gateway 控制台”，窗口数量本身不能证明实例已经隔离。

三个项目分别可能采用三类机制：

```text
配置投影
工具保存多份 Provider 设置
→ 选择后写入客户端 live 配置
→ 客户端重启后读取新配置

凭证替换
工具保存多个已授权账号快照
→ 选择账号后更新 Keychain 或活动缓存
→ 客户端重启后读取新凭据

本地路由接管
客户端 Base URL 指向 127.0.0.1
→ 本地 Gateway 选择上游并可能转换协议
→ 请求继续发送到真实供应商或账号池
```

配置投影会覆盖活动文件，需要处理工具数据库、备份和用户手工编辑之间的冲突；凭证替换适合串行切号，已经启动的两个进程是否暂时保留不同旧 Token 只取决于进程缓存，不能当作可靠并行隔离；本地路由可以热切换和转换协议，但服务可能看到完整 Prompt、源码、工具调用和响应。客户端显示 localhost 只说明第一跳在本机，不表示数据不会离开机器。

## 2. 观察每个工具实际修改的层次

CC Switch 可能为不同客户端维护 Provider 卡片，再把活动项投影到 live 配置。Codex 侧可能涉及模型、`model_provider`、Base URL、Provider 凭据或本地路由；Claude Code 侧可能涉及 Base URL、认证环境、模型映射和代理；Grok Build 等客户端也有自己的状态与配置目录。工具界面显示“已切换”不代表所有环境变量、登录缓存和正在运行的会话已经同步改变。

`ccswitch` 的典型流程是：通过 Claude Code 官方流程登录账号 A 并执行 `ccswitch add`；退出后登录账号 B，再次保存；需要切换时运行 `ccswitch switch`，随后重启 Claude Code。项目 README 当前提供：

```bash
ccswitch add
ccswitch list
ccswitch status
ccswitch switch 2
ccswitch refresh 2
ccswitch remove 2
```

macOS 凭据写入 Keychain；Linux/WSL 使用 `~/.claude-switch-backup/credentials/`，文件权限为 `0600`、目录为 `0700`。Token 账号还会使用 `~/.ccswitchrc` 清除 `CLAUDE_CODE_OAUTH_TOKEN`，让 Claude Code 回到活动 Keychain/凭据文件。这个文件本身仍属于认证控制链，不能因为没有直接写出 Token 就忽略审查。

Cockpit Tools 的 Codex 账号页会显示计划与配额，并可启动本地 API 或不同实例。隔离是否成立，要检查状态目录、启动参数、凭据存储和 Keyring，而不能只相信“多开”标签。本地 API 使用时还要确认监听 `127.0.0.1` 还是 `0.0.0.0`、本地 API Key 的用途、OAuth 存储、请求日志、账号轮换和退出后的配置恢复。个人机器优先只监听回环地址；绑定所有接口可能让局域网其他设备接触服务。

第一次使用任何工具时，不要同时导入多个真实账号、开启代理、改模型和同步 MCP。找到数据目录、备份、恢复、代理开关和官方配置入口后，只做一个可撤销动作。

## 3. 用元数据和客户端状态验证切换结果

下面的实验不读取凭据正文，只记录文件大小、修改时间与 SHA-256。输出仍可能暴露路径和使用痕迹，应保留在本机：

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

在管理工具中只执行一个动作，例如从官方 Codex 配置切换到自己拥有 API Key 的测试 Provider。重启对应客户端后再次记录：

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

`config.toml` 变化而 `auth.json` 不变，可能只是 Provider 投影；两者都变，认证也可能被改写；文件都不变但客户端指向 localhost，则继续检查环境变量、启动参数、Keychain 和本地代理。摘要只能证明内容发生变化，不能说明具体字段、安全性或请求最终去向。`auth.json`、`.claude.json` 和 Keychain 不应通过复制正文观察。

Codex 切换后确认状态目录和非敏感字段：

```bash
printf 'CODEX_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}"
grep -E '^(model|model_provider|openai_base_url)' \
  "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null
codex login status
```

Base URL 为 localhost 时，还要确认本地进程、监听端口、当前路由与真实上游。Claude Code 中使用 `/status` 查看活动认证与 Setting sources，并在 Shell 中只检查变量是否存在：

```bash
env | grep -E '^(ANTHROPIC_BASE_URL|ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|CLAUDE_CODE_OAUTH_TOKEN)=' \
  | sed 's/=.*$/=<已隐藏>/'
```

工具界面与客户端状态不一致时，关闭旧进程后重新测试。有效验证还应包含一个不含秘密的最小请求、一次工具调用，以及用量实际归属；只看卡片中的模型名或账号标签，无法证明请求路线。

## 4. 恢复官方配置时只保留一个写入控制面

优先使用工具提供的“官方 Provider”“退出本地路由”“恢复备份”或删除受管实例功能。工具仍在后台监控 live 文件时，不要同时手工覆盖，否则它可能立即写回。

恢复后逐层检查：本地代理是否停止，Base URL 是否离开 localhost 或第三方地址，官方登录是否有效，Shell 启动文件是否残留环境变量，客户端重启后的 `/status` 或 `codex login status` 是否符合预期。工具备份不可用时，再使用修改前保存的非敏感配置备份；包含凭据的恢复只在本机进行，不通过聊天或网盘传输。

配置、凭据、环境变量和路由应分层恢复。一次同时修改四层，即使最终能连接，也无法确认哪项变化生效，下一次故障也难以回退。

## 5. 安装前审查权限、维护状态和上游认证条款

第三方管理工具可能读写凭据、修改客户端配置、启动网络服务、安装 sidecar，并看到请求正文。安装前至少确认项目仓库、Release 与 Issue 状态、安装包签名或校验、数据目录、备份、遥测、日志、预置中转站、监听地址、OAuth 复用方式和卸载回滚。项目 README 只能说明项目自身设计，不能代表 OpenAI、Anthropic、xAI 或其他供应商批准所有用法。

Anthropic 当前明确区分原生 Claude Code/Anthropic 应用的订阅 OAuth 与第三方产品调用：第三方开发者构建产品或服务时应使用 API Key 或受支持的云平台认证，不能代表用户路由 Free、Pro 或 Max 订阅凭据。`ccswitch` 在本机为同一用户切换官方登录快照，与把订阅 OAuth 包装成第三方 API 服务是不同场景；具体使用仍必须符合账号所属计划、组织策略和当前条款。Codex、Grok 和其他上游同样需要按各自官方认证与使用政策核对，技术可连通不等于政策允许。

选择工具时，账号数量不是核心。使用者应能清楚回答：工具修改什么，凭据存在哪里，请求经过哪里，实例隔离到哪一层，用量怎样验证，失败后如何恢复。无法回答这些问题时，先使用官方客户端与官方认证，不急于增加额外控制层。

核对来源：

- [CC Switch 项目](https://github.com/farion1231/cc-switch)
- [CC Switch 用户手册](https://github.com/farion1231/cc-switch/blob/main/docs/user-manual/en/README.md)
- [ccswitch 多账号工具](https://github.com/vyshnavsdeepak/ccswitch)
- [Cockpit Tools 项目](https://github.com/jlcodes99/cockpit-tools)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
