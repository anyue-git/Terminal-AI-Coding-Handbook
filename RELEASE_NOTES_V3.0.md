# V3.0 发布说明（草案）

> 当前状态：尚未发布。本文件用于 V3.0 合并、公开导出和创建 GitHub Release 前的最终核对。

《终端与 AI 编程手册》V3.0 不是继续扩充章节数量，而是针对 V2.0 普遍存在的碎片化叙事进行全书重构。原版本已经覆盖终端、Git、SSH、Python、Docker、三套 AI CLI、配置凭证和 GPU 远程开发，但大量页面采用“一句引导—代码块—一句解释—列表—下一个标题”的卡片式节奏，导致页面很长、连续理解困难，也让相同安全提醒在多个章节重复出现。

V3.0 将重构单位从单个知识点改为完整意思、真实任务和可验证决策：一个自然段围绕同一问题展开，一个小节解决真正不同的问题，一章形成从场景、操作、结果判断到恢复方法的连续过程。独特命令、配置键、代表性输出、故障场景、安全边界和恢复路径继续保留；删除或迁移的主要是空泛过渡、重复模板和只承载一条命令的标题。

## 主要变化

### 全书叙事结构、公式化文风与内容覆盖审查

V3.0 先建立叙事审计脚本、写作规范和内容覆盖制度，再完成三篇代表性样章、四个正文批次和第二轮公式化文风审查。README、Quickstart、快速开始、Part 01–12 和主要附录均经过人工重新设计，没有使用脚本自动拼接段落。

当前全量审计包含 81 篇文件，V2 基线只有 73 篇。为了避免新增路线图、覆盖记录、审查记录和发布说明影响比较，下表只统计 V2 中原有、V3 当前仍存在的同一批 73 个文档。数据来自 Source Release Audit #187，对应正文头 `5ebae1a1f468347711df851467d497ccbc831ebf`：

| 指标 | V2.0 基线 | V3.0 #187 | 变化 |
| --- | ---: | ---: | ---: |
| 普通正文字符 | 137786 | 122367 | -11.2% |
| 自然段 | 4526 | 2066 | -54.4% |
| 微型段落 | 2311 | 536 | -76.8% |
| 短段落 | 3355 | 952 | -71.6% |
| 一句段落 | 3304 | 1095 | -66.9% |
| 平均段长 | 30.4 字 | 59.2 字 | +28.8 字 |
| 标题 | 1433 | 522 | -63.6% |
| 列表项 | 2446 | 276 | -88.7% |
| 代码块 | 2467 | 1048 | -57.5% |
| 正文偏薄的小节 | 544 | 20 | -96.3% |
| 空引导短句 | 151 | 15 | -90.1% |
| 短段占比 | 74.1% | 46.1% | -28.0 个百分点 |

此前曾误把当前 81 篇的字符总量与 V2 的 73 篇基线比较，得出“正文略高于 V2”的错误结论；该口径已经在路线图、审查记录、静态审计和 Draft PR 中纠正。

普通正文减少 11.2% 不能单独说明内容是否完整。术语表和维护清单改为表格后，表格单元格不计入普通正文；重复 Prompt、重复 Git 流程和跨章安全提醒也已合并或迁移。但结构指标同样不能证明无损，因此 V3 又加入 V2 主分支反查：从缩减较大的章节中逐项寻找被删除的独特命令、故障场景和恢复方法，确认由其他主讲章节承接，或直接补回。

### 代码示例转义回归

本轮直接回读正文时发现，《Shell 到底是什么》和《查看文本文件与日志》中少量 `printf '%s\n'` 示例曾在写入过程中变成单引号跨物理行。Markdown 围栏仍然闭合，Shell 也可能把它继续解释为多行字符串，因此普通 Markdown 与语法检查没有报警，但读者复制时看到的形式已经不正确。

相关示例已经恢复为显式 `\n`。`scripts/test_audit_tools.py` 新增了针对 Bash、sh、Shell 和 zsh 围栏的回归扫描：正常的单行格式参数通过，`printf` 的格式参数引号跨越物理行时，两套 GitHub Actions 会直接失败。该规则刻意保持窄范围，不把一般代码块、普通多行字符串或正文段落纳入判断。

### 入口与终端基础

README 改为读者路线和内容地图；两个短版快速开始形成终端与 AI CLI 的最小闭环，完整 Quickstart 继续提供可脱离真实项目运行的独立项目练习。Terminal、Shell、zsh、路径、文件生命周期和进程生命周期重新划分职责，快捷键章节继续保持查表结构。

文件创建、复制、移动与删除章从十二个小节合并为五段文件生命周期，但仍保留覆盖确认、目录体积预演、空格与连字符文件名、变量路径、待清理区和 Git 恢复边界。日志章仍保留 `file`、`cat`、`less`、`head`、`tail -f`、`tee`、`pipefail`、二进制判断、敏感信息和逐层定位；本轮只修复示例转义，没有为了增加篇幅恢复旧版卡片。

### Git、SSH、Homebrew、Python 与 Docker

Git 按心智模型、日常提交、分层恢复和 Pull Request 协作组织；SSH 分别处理首次连接、密钥与客户端配置、传输与隧道、分层故障排查；Homebrew 聚焦命令来源和完整服务生命周期；Python 区分解释器、环境选择与依赖复现；Docker 区分对象生命周期、Mac/Ubuntu 运行结构、Compose 与 GPU 分层验证。

覆盖反查补回了以下独特内容：

- Git 日常流程：工作区与暂存区的 `git diff --check`，以及 `git status --ignored --short` 对忽略规则的实际验证；
- Pull Request：远程分支是否自动清理由仓库设置决定，Worktree 不能消除接口和数据格式的语义冲突；
- Homebrew 与 PATH：`sudo brew` 的权限污染风险、前缀所有者检查、最小恢复边界和官方参考；
- Homebrew 服务：`brew services info`、`brew services list --debug`、废弃服务登记清理，以及 `/opt/homebrew` 与 `/usr/local` 两套 Homebrew 服务视图；
- Python 依赖：`sys_platform` 环境标记、extras/dependency groups、包来源与私有索引、按 uv/pip/Conda 分层诊断；
- Docker 核心：构建上下文与 `.dockerignore`、自定义网络中的容器名通信、Volume/Inspect、故障链和容器安全边界；
- Docker Compose：变量插值、`.env.example`、多文件合并顺序、显式项目名和服务网络诊断；
- GPU 容器：独立 GPU Compose 覆盖文件、镜像 digest、不可信镜像/模型自定义代码风险和 UID/GID 验证；
- Docker Desktop/Ubuntu Engine：Mac 通过命名 SSH Context 显式操作 Ubuntu daemon，并说明远程 Bind Mount 的源路径必须在 Ubuntu 上存在。

Homebrew 服务章补回后正文为 1987 字，接近 V2 的 2188 字，但自然段从 76 降到 35、标题从 16 降到 5、薄小节从 1 降到 0。Python 依赖章普通正文已经高于 V2，但自然段从 81 降到 35、标题从 18 降到 8、最长连续短段从 10 降到 3。这表明内容覆盖与结构收紧可以同时成立。

### Claude Code、Codex CLI 与 Grok Build

三套客户端只在各自章节主讲产品特有的安装、认证、权限、会话、自动化与扩展能力。共同的模型、Provider、Base URL、配置、凭证、Profile、状态目录、独立实例和本地网关集中到 Part 10C。

Codex 安装、认证、设备码、Enterprise Access Token、granular 审批和 beta Permission Profiles 已按 2026-07-30 官方资料核对。Claude Code 大任务章只保留命名 Plan 会话、上下文管理、独立 Review、Worktree、`.worktreeinclude` 和子 Agent；三工具协作章只处理稳定差异、主实施者选择和单一写入者/只读复核者分工。

AI 客户端覆盖反查补回 Claude Code MCP 的项目 Scope、凭据边界、提示注入和双数据链，以及 Grok Headless 的工具白名单、Allow/Deny、JSONL 前向兼容和模型/推理强度记录。Claude Code 配置/网关与 Codex TOML/凭证两章逐项对照后，设置作用域、认证优先级、Profile、Provider、Token、Keyring、Helper、Gateway、多开和恢复入口均有承接。

Codex 自动化章本轮继续对照 V2，确认 TUI/`exec`、工作目录、Git 检查、非交互权限、会话恢复、JSONL、Schema、只读审计脚本、修改型任务、退出状态、超时、CI 凭据与 Git 写操作边界仍完整。旧版完整任务合同已经迁移到 Prompt 模板库，因此没有恢复二十个小节。

CC Switch、`ccswitch` 与 Cockpit Tools 分别依据其项目 README 核对；配置投影、凭证替换和本地路由被明确区分，第三方项目声明的技术能力不被视为上游平台授权。

### Mac、Ubuntu 与 GPU 远程开发

Part 11 按局域网链路、源码同步、tmux、NVIDIA/PyTorch、跨平台环境、Tailscale、VS Code/AI CLI 协作和实验恢复重新组织。Mac 负责主要编辑、Git 与复核，Ubuntu 负责 Linux/CUDA/训练；源码、环境、数据、模型与 runs 分目录，日志、退出状态、代码快照、最终配置、指标、checkpoint 和恢复演练组成完整证据链。

### AI 开发工作流

Part 12 将 Prompt、安全边界、复杂任务、多 Agent 和端到端案例组织为可执行流程：

```text
定义完成标准
→ 建立现实基线
→ 只读调查
→ 选择方案
→ 小批实施
→ 证据验证
→ 独立复核与人工提交
```

同一工作区同时只保留一个实施者；其他 Agent 使用只读职责或独立 Worktree。审批、Sandbox、操作系统权限和恢复能力继续作为不同层级处理。可复制表单留在 Prompt 模板库，概念章和产品章不再分别重复整套模板。

复杂任务章在覆盖反查后补回每个批次的测试证据格式：命令、运行环境、退出状态、通过/失败/跳过、关键警告、覆盖行为和未覆盖内容；最终验收也明确检查凭据、大型生成物和范围外修改。

### 附录与维护体系

术语表从大量单句小节改为领域索引表；危险命令按文件与权限、Git/同步、安装与系统、网络与进程、Docker、AI/凭据等风险域组织；版本化工具核对表改为维护矩阵；总路线图恢复为阅读顺序和章节依赖。快捷键速查表继续保留查表结构，不为追求长段落而强行改写。

## 新增自动审计

V3.0 新增并接入 GitHub Actions：

- `scripts/audit_prose_structure.py`：统计微型段、短段、连续短段、薄小节和空引导；
- `scripts/audit_formulaic_style.py`：定位跨章重复长句、固定段首、警告密度、公式化转折和超长段落候选；
- `scripts/audit_sensitive_patterns.py`：扫描当前树、提交说明和完整 Git 补丁历史中的高置信度凭据特征，报告不输出完整匹配值；
- `scripts/audit_external_links.py`：忽略代码块和占位域名，检查公开快照外链和非公网目标；
- `scripts/test_audit_tools.py`：回归外链与敏感规则，并扫描 Shell `printf` 格式参数转义；
- `.github/workflows/source-release-audit.yml`：克隆当前公共仓库，真实执行 `export_public.sh --dry-run`，验证目标 clone 未变化，构建隔离公开快照并重新运行 Markdown、敏感信息与外链检查。

源仓库专用发布审计工作流由 `.publishignore` 排除，不进入公共快照。

## 当前验证结果

Source Release Audit #187 已验证最终头 `3e4eb1ebb278438fbc019ecfba8d9c15eb4bbdec`：

- 审计辅助测试全部通过，包括全仓库 Shell `printf` 示例回归扫描；
- 85 个公开快照 Markdown 文件通过严格检查，0 个错误、0 个警告；
- 60 个去重外部链接全部正常；
- 当前树、104516 行 Git 历史新增内容、782 行提交说明和公开快照均未发现高置信度敏感信息；
- 公开导出预演包含 117 个差异项、0 个删除项；
- 预演没有改变公共仓库 clone；公共仓库未被写入；
- V3.0 仍位于私有源仓库 Draft PR。

上述结果是一份可追溯的审计快照。每次正文、脚本或维护文档变化都会重新触发 Markdown Check 与 Source Release Audit；最终发布时仍以拟合并头提交对应的最新成功运行及其产物为准。自动检查通过只能证明所覆盖的规则和预演通过，不能证明所有命令已经在作者真实 Mac、Ubuntu、NVIDIA GPU、账号和网络环境中执行，也不能保证外部服务未来不会变化。

## 发布前剩余条件

V3.0 公开发布前仍需完成：

1. 在真实 Mac 与 Ubuntu 环境抽样执行关键 zsh、Git、SSH、rsync、Docker、Python、CUDA 和 checkpoint 恢复命令；
2. 对快速变化的 AI CLI、第三方 Provider 和平台策略做最后一次官方事实抽检；
3. 核对最终合并提交、公开导出差异、README、许可证、标签名称和 GitHub Release 文案；
4. 在最终批准提交重新运行 Markdown Check 与 Source Release Audit；
5. 从私有源仓库 `main` 导出到公共仓库发布分支，人工复核 diff 后再提交、创建 PR、合并并打标签。

## 许可证

本项目采用双许可证：正文、解释、表格、练习和其他非代码教学内容使用 CC BY-NC-SA 4.0；脚本、GitHub Actions、Shell 命令、配置示例和围栏代码使用 MIT License。第三方商标、引用、截图和链接材料仍受各自权利人条款约束。