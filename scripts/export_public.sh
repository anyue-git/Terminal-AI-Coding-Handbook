#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SOURCE_REPO="anyue-git/Terminal-AI-Coding-Handbook-Source"
EXPECTED_TARGET_REPO="anyue-git/Terminal-AI-Coding-Handbook"
DEFAULT_MAX_DELETE=25

usage() {
  cat <<'EOF'
用法：
  bash scripts/export_public.sh --dry-run --target <公开仓库本地目录>
  bash scripts/export_public.sh --apply --target <公开仓库本地目录> [删除确认选项]

模式：
  --dry-run              生成公开快照并展示差异，不写入目标仓库。
  --apply                在完成全部校验和差异预览后，同步到目标仓库工作区。

参数：
  --target PATH          已克隆的公开仓库本地目录。必须提供。
  --confirm-delete       当预览包含删除项时，明确授权执行这些删除。
  --max-delete N         普通同步允许的最大删除项数量，默认 25。
  --allow-large-delete   当删除项超过 --max-delete 时，额外授权大批量删除。
  -h, --help             显示本帮助。

安全边界：
  1. --dry-run 永远不会写入目标仓库。
  2. --apply 只允许从私有源仓库 main 分支发布到公开仓库的非 main/master 分支。
  3. 目标仓库必须无未提交修改，且 origin 必须指向指定公开仓库。
  4. 目标仓库的 .git 始终排除在同步和删除范围之外。
  5. 任何删除都需要 --confirm-delete；超过阈值还需要 --allow-large-delete。
EOF
}

die() {
  printf '错误：%s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "缺少必要命令：$1"
}

canonical_dir() {
  local input=$1
  [[ -d "$input" ]] || return 1
  (cd "$input" && pwd -P)
}

remote_matches_repo() {
  local url=$1
  local repo=$2

  case "$url" in
    "https://github.com/${repo}" | \
    "https://github.com/${repo}.git" | \
    "git@github.com:${repo}" | \
    "git@github.com:${repo}.git" | \
    "ssh://git@github.com/${repo}" | \
    "ssh://git@github.com/${repo}.git")
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

MODE=""
TARGET_INPUT=""
CONFIRM_DELETE=0
ALLOW_LARGE_DELETE=0
MAX_DELETE=$DEFAULT_MAX_DELETE

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      [[ -z "$MODE" ]] || die "--dry-run 与 --apply 只能选择一个。"
      MODE="dry-run"
      shift
      ;;
    --apply)
      [[ -z "$MODE" ]] || die "--dry-run 与 --apply 只能选择一个。"
      MODE="apply"
      shift
      ;;
    --target)
      [[ $# -ge 2 ]] || die "--target 后必须提供目录。"
      TARGET_INPUT=$2
      shift 2
      ;;
    --confirm-delete)
      CONFIRM_DELETE=1
      shift
      ;;
    --max-delete)
      [[ $# -ge 2 ]] || die "--max-delete 后必须提供整数。"
      MAX_DELETE=$2
      shift 2
      ;;
    --allow-large-delete)
      ALLOW_LARGE_DELETE=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die "未知参数：$1"
      ;;
  esac
done

[[ -n "$MODE" ]] || die "必须指定 --dry-run 或 --apply。"
[[ -n "$TARGET_INPUT" ]] || die "必须通过 --target 指定公开仓库本地目录。"
case "$MAX_DELETE" in
  '' | *[!0-9]*) die "--max-delete 必须是非负整数。" ;;
esac

require_command git
require_command rsync
require_command mktemp
require_command grep
require_command tee

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
SOURCE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd -P)
TARGET_ROOT=$(canonical_dir "$TARGET_INPUT") || die "目标目录不存在：$TARGET_INPUT"

[[ "$SOURCE_ROOT" != "$TARGET_ROOT" ]] || die "源仓库和目标仓库不能是同一个目录。"
[[ -e "$SOURCE_ROOT/.git" ]] || die "脚本所在目录不是 Git 仓库根目录：$SOURCE_ROOT"
[[ -e "$TARGET_ROOT/.git" ]] || die "目标目录不是 Git 仓库根目录：$TARGET_ROOT"

SOURCE_TOP=$(git -C "$SOURCE_ROOT" rev-parse --show-toplevel 2>/dev/null || true)
TARGET_TOP=$(git -C "$TARGET_ROOT" rev-parse --show-toplevel 2>/dev/null || true)
[[ "$SOURCE_TOP" == "$SOURCE_ROOT" ]] || die "请从私有源仓库根目录使用本脚本。"
[[ "$TARGET_TOP" == "$TARGET_ROOT" ]] || die "--target 必须直接指向公开仓库根目录。"

SOURCE_ORIGIN=$(git -C "$SOURCE_ROOT" remote get-url origin 2>/dev/null || true)
TARGET_ORIGIN=$(git -C "$TARGET_ROOT" remote get-url origin 2>/dev/null || true)
remote_matches_repo "$SOURCE_ORIGIN" "$EXPECTED_SOURCE_REPO" || \
  die "源仓库 origin 不匹配。期望：$EXPECTED_SOURCE_REPO；实际：${SOURCE_ORIGIN:-未配置}"
remote_matches_repo "$TARGET_ORIGIN" "$EXPECTED_TARGET_REPO" || \
  die "目标仓库 origin 不匹配。期望：$EXPECTED_TARGET_REPO；实际：${TARGET_ORIGIN:-未配置}"

[[ -z "$(git -C "$SOURCE_ROOT" status --porcelain --untracked-files=all)" ]] || \
  die "私有源仓库存在未提交修改。请先提交或清理后再发布。"
[[ -z "$(git -C "$TARGET_ROOT" status --porcelain --untracked-files=all)" ]] || \
  die "公开目标仓库存在未提交修改。为避免覆盖，请先提交、暂存到其他分支或清理。"

SOURCE_BRANCH=$(git -C "$SOURCE_ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
TARGET_BRANCH=$(git -C "$TARGET_ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
[[ -n "$SOURCE_BRANCH" ]] || die "私有源仓库处于 detached HEAD 状态。"
[[ -n "$TARGET_BRANCH" ]] || die "公开目标仓库处于 detached HEAD 状态。"

if [[ "$MODE" == "apply" ]]; then
  [[ "$SOURCE_BRANCH" == "main" ]] || \
    die "正式发布只能从私有源仓库 main 分支执行；当前分支：$SOURCE_BRANCH"
  case "$TARGET_BRANCH" in
    main | master)
      die "禁止直接写入公开仓库 $TARGET_BRANCH 分支。请先创建发布分支。"
      ;;
  esac
fi

IGNORE_FILE="$SOURCE_ROOT/.publishignore"
[[ -f "$IGNORE_FILE" ]] || die "缺少公开发布规则：$IGNORE_FILE"

REQUIRED_PUBLIC_PATHS=(
  "LICENSE"
  "README.md"
  "SUMMARY.md"
  ".github/workflows/markdown-check.yml"
  "scripts/check_markdown.py"
)

for rel_path in "${REQUIRED_PUBLIC_PATHS[@]}"; do
  [[ -e "$SOURCE_ROOT/$rel_path" ]] || die "源仓库缺少必须公开的文件：$rel_path"
done

SOURCE_HEAD=$(git -C "$SOURCE_ROOT" rev-parse HEAD)
TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse HEAD)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/terminal-ai-public-export.XXXXXX")
STAGING_ROOT="$TMP_ROOT/snapshot"
PREVIEW_FILE="$TMP_ROOT/preview.txt"
mkdir -p "$STAGING_ROOT"
trap 'rm -rf "$TMP_ROOT"' EXIT

printf '源仓库：%s\n' "$SOURCE_ROOT"
printf '源提交：%s\n' "$SOURCE_HEAD"
printf '目标仓库：%s\n' "$TARGET_ROOT"
printf '目标分支：%s\n' "$TARGET_BRANCH"
printf '目标提交：%s\n' "$TARGET_HEAD"
printf '模式：%s\n\n' "$MODE"

# 先在临时目录中生成完整的公开快照。这样，新增到 .publishignore 的旧公开文件
# 会在第二阶段被识别为删除项，同时目标仓库的 .git 不会进入快照。
rsync -a \
  --exclude='/.git' \
  --exclude='/.git/' \
  --exclude-from="$IGNORE_FILE" \
  "$SOURCE_ROOT/" "$STAGING_ROOT/"

for rel_path in "${REQUIRED_PUBLIC_PATHS[@]}"; do
  [[ -e "$STAGING_ROOT/$rel_path" ]] || \
    die ".publishignore 错误排除了必须公开的文件：$rel_path"
done

printf '%s\n' '即将产生的公开仓库差异：'
rsync -a \
  --delete-after \
  --itemize-changes \
  --exclude='/.git' \
  --exclude='/.git/' \
  --dry-run \
  "$STAGING_ROOT/" "$TARGET_ROOT/" | tee "$PREVIEW_FILE"

CHANGE_COUNT=$(grep -cve '^[[:space:]]*$' "$PREVIEW_FILE" || true)
DELETE_COUNT=$(grep -c '^\*deleting' "$PREVIEW_FILE" || true)
printf '\n差异项：%s；删除项：%s。\n' "$CHANGE_COUNT" "$DELETE_COUNT"

if [[ "$MODE" == "dry-run" ]]; then
  printf '%s\n' '预演完成：目标仓库未被写入。'
  exit 0
fi

[[ "$CHANGE_COUNT" -gt 0 ]] || {
  printf '%s\n' '没有需要同步的差异。'
  exit 0
}

if [[ "$DELETE_COUNT" -gt 0 ]]; then
  [[ "$CONFIRM_DELETE" -eq 1 ]] || \
    die "预览包含 $DELETE_COUNT 个删除项。核对列表后，使用 --confirm-delete 重新执行 --apply。"

  if [[ "$DELETE_COUNT" -gt "$MAX_DELETE" && "$ALLOW_LARGE_DELETE" -ne 1 ]]; then
    die "删除项数量 $DELETE_COUNT 超过安全阈值 $MAX_DELETE。确认范围后，再增加 --allow-large-delete。"
  fi
fi

[[ "$(git -C "$SOURCE_ROOT" rev-parse HEAD)" == "$SOURCE_HEAD" ]] || \
  die "预演后源仓库 HEAD 已变化，已停止同步。"
[[ "$(git -C "$TARGET_ROOT" rev-parse HEAD)" == "$TARGET_HEAD" ]] || \
  die "预演后目标仓库 HEAD 已变化，已停止同步。"
[[ -z "$(git -C "$TARGET_ROOT" status --porcelain --untracked-files=all)" ]] || \
  die "预演后目标仓库工作区发生变化，已停止同步。"

printf '\n%s\n' '开始正式同步：'
rsync -a \
  --delete-after \
  --itemize-changes \
  --exclude='/.git' \
  --exclude='/.git/' \
  "$STAGING_ROOT/" "$TARGET_ROOT/"

[[ -e "$TARGET_ROOT/.git" ]] || die "严重错误：同步后目标仓库 .git 不存在。"
TARGET_ORIGIN_AFTER=$(git -C "$TARGET_ROOT" remote get-url origin 2>/dev/null || true)
remote_matches_repo "$TARGET_ORIGIN_AFTER" "$EXPECTED_TARGET_REPO" || \
  die "同步后目标仓库 origin 校验失败。"

for rel_path in "${REQUIRED_PUBLIC_PATHS[@]}"; do
  [[ -e "$TARGET_ROOT/$rel_path" ]] || die "同步后缺少必须公开的文件：$rel_path"
done

printf '\n%s\n' '同步完成。请在公开仓库中复核以下 Git 差异，再提交并创建 Pull Request：'
git -C "$TARGET_ROOT" status --short
