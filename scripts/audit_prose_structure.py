#!/usr/bin/env python3
"""Audit fragmented prose patterns in tracked Markdown files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
HTML_RE = re.compile(r"^\s*</?[A-Za-z][^>]*>\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
SENTENCE_RE = re.compile(r"[。！？!?；;]+")
LEADIN_RE = re.compile(
    r"^(?:在[^。]{0,18}(?:执行|运行|输入)|"
    r"(?:现在|接着|然后|随后|再|最后)?"
    r"(?:执行|运行|输入|查看|检查|例如|可能看到|应看到|输出为|可以使用|可以运行))[:：]?$"
)

DEFAULT_EXCLUDES = {
    "SUMMARY.md",
    "RELEASE_NOTES_V2.0.md",
    "Appendix/自动检查报告.md",
    "Appendix/V3.0-叙事结构审计.md",
}


@dataclass
class FileMetrics:
    path: str
    prose_chars: int
    paragraphs: int
    micro_paragraphs: int
    short_paragraphs: int
    one_sentence_paragraphs: int
    longest_short_run: int
    headings: int
    list_items: int
    code_blocks: int
    thin_sections: int
    short_leadins_before_code: int
    average_paragraph_chars: float


@dataclass
class Aggregate:
    files: int
    prose_chars: int
    paragraphs: int
    micro_paragraphs: int
    short_paragraphs: int
    one_sentence_paragraphs: int
    headings: int
    list_items: int
    code_blocks: int
    thin_sections: int
    short_leadins_before_code: int
    micro_ratio: float
    short_ratio: float
    average_paragraph_chars: float


def git(root: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess:
    options = {
        "check": False,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if not binary:
        options.update(text=True, encoding="utf-8")
    return subprocess.run(["git", "-C", str(root), *args], **options)


def repo_root(start: Path) -> Path:
    result = git(start, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "当前目录不在 Git 仓库中。")
    return Path(result.stdout.strip()).resolve()


def markdown_paths(root: Path, ref: str | None) -> list[str]:
    if ref:
        result = git(root, "ls-tree", "-r", "-z", "--name-only", ref, binary=True)
    else:
        result = git(root, "ls-files", "-z", binary=True)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "无法读取 Git 文件列表。")
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if path.lower().endswith(".md"):
            paths.append(path)
    return sorted(paths)


def read_markdown(root: Path, path: str, ref: str | None) -> str:
    if not ref:
        return (root / path).read_text(encoding="utf-8")
    result = git(root, "show", f"{ref}:{path}")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"无法读取 {ref}:{path}")
    return result.stdout


def clean_text(text: str) -> str:
    text = INLINE_CODE_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = BLOCKQUOTE_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def sentence_count(text: str) -> int:
    return max(1, len(SENTENCE_RE.findall(text))) if text else 0


def analyze(path: str, text: str, micro_max: int, short_max: int, thin_max: int) -> FileMetrics:
    paragraphs: list[tuple[int, int, str]] = []
    section_chars: dict[str, int] = {"文档开头": 0}
    current_section = "文档开头"
    buffer: list[str] = []
    buffer_line = 0
    in_fence = False
    fence_char = ""
    fence_len = 0
    headings = 0
    lists = 0
    blocks = 0
    leadins = 0
    previous: tuple[int, int, str] | None = None

    def flush() -> None:
        nonlocal buffer, previous
        if not buffer:
            return
        cleaned = clean_text(" ".join(line.strip() for line in buffer))
        buffer = []
        if not cleaned:
            return
        item = (buffer_line, char_count(cleaned), cleaned)
        paragraphs.append(item)
        section_chars[current_section] = section_chars.get(current_section, 0) + item[1]
        previous = item

    for line_no, line in enumerate(text.splitlines(), start=1):
        fence = FENCE_RE.match(line)
        if fence:
            flush()
            token = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char, fence_len = token[0], len(token)
                blocks += 1
                if previous and previous[1] <= 24 and LEADIN_RE.match(previous[2]):
                    leadins += 1
            elif token[0] == fence_char and len(token) >= fence_len:
                in_fence = False
            continue
        if in_fence:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush()
            headings += 1
            level = len(heading.group(1))
            current_section = f"H{level} {clean_text(heading.group(2))}"
            section_chars.setdefault(current_section, 0)
            previous = None
            continue

        if LIST_RE.match(line):
            flush()
            lists += 1
            previous = None
            continue

        if TABLE_RE.match(line) or HR_RE.match(line) or HTML_RE.match(line):
            flush()
            previous = None
            continue

        if not line.strip():
            flush()
            continue

        if not buffer:
            buffer_line = line_no
        buffer.append(line)

    flush()
    lengths = [item[1] for item in paragraphs]
    micro = sum(length <= micro_max for length in lengths)
    short = sum(length <= short_max for length in lengths)
    one_sentence = sum(sentence_count(item[2]) == 1 for item in paragraphs)
    longest = run = 0
    for length in lengths:
        run = run + 1 if length <= short_max else 0
        longest = max(longest, run)
    thin = sum(
        1 for name, chars in section_chars.items()
        if name != "文档开头" and 0 < chars <= thin_max
    )
    prose_chars = sum(lengths)
    count = len(paragraphs)
    return FileMetrics(
        path=path,
        prose_chars=prose_chars,
        paragraphs=count,
        micro_paragraphs=micro,
        short_paragraphs=short,
        one_sentence_paragraphs=one_sentence,
        longest_short_run=longest,
        headings=headings,
        list_items=lists,
        code_blocks=blocks,
        thin_sections=thin,
        short_leadins_before_code=leadins,
        average_paragraph_chars=round(prose_chars / count, 1) if count else 0.0,
    )


def aggregate(items: list[FileMetrics]) -> Aggregate:
    paragraphs = sum(item.paragraphs for item in items)
    prose_chars = sum(item.prose_chars for item in items)
    micro = sum(item.micro_paragraphs for item in items)
    short = sum(item.short_paragraphs for item in items)
    return Aggregate(
        files=len(items),
        prose_chars=prose_chars,
        paragraphs=paragraphs,
        micro_paragraphs=micro,
        short_paragraphs=short,
        one_sentence_paragraphs=sum(item.one_sentence_paragraphs for item in items),
        headings=sum(item.headings for item in items),
        list_items=sum(item.list_items for item in items),
        code_blocks=sum(item.code_blocks for item in items),
        thin_sections=sum(item.thin_sections for item in items),
        short_leadins_before_code=sum(item.short_leadins_before_code for item in items),
        micro_ratio=round(micro / paragraphs, 4) if paragraphs else 0.0,
        short_ratio=round(short / paragraphs, 4) if paragraphs else 0.0,
        average_paragraph_chars=round(prose_chars / paragraphs, 1) if paragraphs else 0.0,
    )


def path_matches(path: str, prefixes: list[str] | set[str]) -> bool:
    normalized = PurePosixPath(path).as_posix()
    return any(
        normalized == prefix.rstrip("/")
        or normalized.startswith(prefix.rstrip("/") + "/")
        for prefix in prefixes
        if prefix
    )


def collect(root: Path, ref: str | None, args: argparse.Namespace) -> tuple[list[FileMetrics], Aggregate]:
    excludes = set(DEFAULT_EXCLUDES) | {value.strip("/") for value in args.exclude}
    selected = []
    for path in markdown_paths(root, ref):
        if path_matches(path, excludes):
            continue
        if args.include and not path_matches(path, args.include):
            continue
        selected.append(path)
    items = [
        analyze(
            path,
            read_markdown(root, path, ref),
            args.micro_max,
            args.short_max,
            args.thin_section_max,
        )
        for path in selected
    ]
    return items, aggregate(items)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def change(current: int | float, baseline: int | float) -> str:
    diff = current - baseline
    return f"{diff:+.1f}" if isinstance(diff, float) else f"{diff:+d}"


def report(
    ref: str | None,
    items: list[FileMetrics],
    total: Aggregate,
    baseline_ref: str | None,
    baseline: Aggregate | None,
    top: int,
) -> str:
    lines = [
        "# V3.0 叙事结构审计结果",
        "",
        f"> 当前分析对象：`{ref or '工作区'}`",
        "> 指标用于定位人工重写热点，不直接判断文章质量，也不应通过机械拼接段落来追求数字。",
        "",
        "## 全书指标",
        "",
        "| 指标 | 当前值 |",
        "| --- | ---: |",
        f"| 纳入分析的 Markdown 文件 | {total.files} |",
        f"| 正文字符 | {total.prose_chars} |",
        f"| 正文自然段 | {total.paragraphs} |",
        f"| 微型段落（不超过 20 字） | {total.micro_paragraphs}（{pct(total.micro_ratio)}） |",
        f"| 短段落（不超过 45 字） | {total.short_paragraphs}（{pct(total.short_ratio)}） |",
        f"| 平均段落长度 | {total.average_paragraph_chars} 字 |",
        f"| 标题 | {total.headings} |",
        f"| 列表项 | {total.list_items} |",
        f"| 代码块 | {total.code_blocks} |",
        f"| 正文偏薄的小节 | {total.thin_sections} |",
        f"| 代码块前的空引导短句 | {total.short_leadins_before_code} |",
        "",
    ]
    if baseline:
        rows = [
            ("正文字符", baseline.prose_chars, total.prose_chars),
            ("正文自然段", baseline.paragraphs, total.paragraphs),
            ("微型段落", baseline.micro_paragraphs, total.micro_paragraphs),
            ("短段落", baseline.short_paragraphs, total.short_paragraphs),
            ("平均段落长度", baseline.average_paragraph_chars, total.average_paragraph_chars),
            ("标题", baseline.headings, total.headings),
            ("列表项", baseline.list_items, total.list_items),
            ("正文偏薄的小节", baseline.thin_sections, total.thin_sections),
            ("空引导短句", baseline.short_leadins_before_code, total.short_leadins_before_code),
        ]
        lines += [
            f"## 与 `{baseline_ref}` 比较",
            "",
            "| 指标 | 基线 | 当前 | 变化 |",
            "| --- | ---: | ---: | ---: |",
            *[f"| {name} | {old} | {new} | {change(new, old)} |" for name, old, new in rows],
            "",
        ]

    ranked = sorted(
        items,
        key=lambda item: (
            item.short_paragraphs,
            item.short_leadins_before_code,
            item.thin_sections,
            item.longest_short_run,
        ),
        reverse=True,
    )[:top]
    lines += [
        "## 当前热点文件",
        "",
        "| 文件 | 段落 | 短段 | 最长连续短段 | 空引导 | 薄小节 | 平均段长 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in ranked:
        lines.append(
            f"| `{item.path}` | {item.paragraphs} | {item.short_paragraphs} | "
            f"{item.longest_short_run} | {item.short_leadins_before_code} | "
            f"{item.thin_sections} | {item.average_paragraph_chars} |"
        )
    lines += [
        "",
        "## 指标解释",
        "",
        "- 微型段落和短段落只统计普通正文，不统计标题、代码块、表格和列表项。",
        "- 正文偏薄的小节表示标题下普通正文不超过设定阈值；命令很多但解释很少的小节仍可能被标记。",
        "- 空引导短句用于识别“运行：”“查看：”“可能看到：”一类可与上下文合并的引导。",
        "- 列表和代码块本身不是问题；问题在于它们是否替代了本应连续展开的解释。",
        "- 数字改善不能替代内容覆盖检查，独特命令、错误恢复和安全边界仍需逐项保留或说明迁移位置。",
        "",
    ]
    return "\n".join(lines)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 Markdown 正文中的碎片化段落和模板化结构。")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ref", help="分析指定 Git ref；省略时分析当前工作区。")
    parser.add_argument("--baseline-ref", help="同时分析基线 Git ref。")
    parser.add_argument("--report", type=Path, help="写入 Markdown 报告。")
    parser.add_argument("--json", dest="json_path", type=Path, help="写入 JSON 结果。")
    parser.add_argument("--include", action="append", default=[], help="只分析指定文件或目录前缀。")
    parser.add_argument("--exclude", action="append", default=[], help="额外排除文件或目录前缀。")
    parser.add_argument("--micro-max", type=int, default=20)
    parser.add_argument("--short-max", type=int, default=45)
    parser.add_argument("--thin-section-max", type=int, default=80)
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        root = repo_root(args.root.resolve())
        items, total = collect(root, args.ref, args)
        baseline_items = baseline_total = None
        if args.baseline_ref:
            baseline_items, baseline_total = collect(root, args.baseline_ref, args)
    except (OSError, RuntimeError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    markdown = report(args.ref, items, total, args.baseline_ref, baseline_total, args.top)
    print(markdown)
    if args.report:
        target = args.report if args.report.is_absolute() else root / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown + "\n", encoding="utf-8")
    if args.json_path:
        target = args.json_path if args.json_path.is_absolute() else root / args.json_path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ref": args.ref or "WORKTREE",
            "aggregate": asdict(total),
            "files": [asdict(item) for item in items],
        }
        if baseline_total is not None and baseline_items is not None:
            payload.update(
                baseline_ref=args.baseline_ref,
                baseline_aggregate=asdict(baseline_total),
                baseline_files=[asdict(item) for item in baseline_items],
            )
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
