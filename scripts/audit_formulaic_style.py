#!/usr/bin/env python3
"""Locate formulaic prose candidates in the handbook.

This is a diagnostic report, not a quality gate. It deliberately ignores code
blocks, tables and list items, then reports cross-file duplicate sentences,
repeated paragraph openings, warning-heavy files and very long paragraphs for
human review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Sequence


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
TABLE_RULE_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])\s*|\n+")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
HTML_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)

SKIP_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "Private",
    "Drafts",
    "Internal",
}

MAINTENANCE_PATHS = {
    "CONTRIBUTING.md",
    "RELEASE_NOTES_V2.0.md",
    "RELEASE_NOTES_V3.0.md",
    "SUMMARY.md",
    "V3.0-ROADMAP.md",
    "Appendix/内容审查记录.md",
    "Appendix/更新记录.md",
    "Appendix/自动检查报告.md",
    "Appendix/版本化工具核对表.md",
}

FORMULAIC_PATTERNS: dict[str, re.Pattern[str]] = {
    "不是…而是…": re.compile(r"不是.{0,40}而是"),
    "先…再…": re.compile(r"先.{0,50}再"),
    "不等于": re.compile(r"不等于"),
    "真正": re.compile(r"真正"),
    "稳定做法": re.compile(r"稳定做法"),
    "更可靠": re.compile(r"更可靠"),
    "本章": re.compile(r"本章"),
    "最后": re.compile(r"最后"),
}

WARNING_RE = re.compile(r"不要|不能|不应|不得|严禁|不适合|避免")


@dataclass(frozen=True)
class Paragraph:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class Location:
    path: str
    line: int


@dataclass(frozen=True)
class DuplicateSentence:
    sentence: str
    files: int
    occurrences: int
    locations: list[Location]


@dataclass(frozen=True)
class RepeatedOpening:
    opening: str
    files: int
    occurrences: int
    locations: list[Location]


@dataclass(frozen=True)
class FileDensity:
    path: str
    sentences: int
    warning_sentences: int
    density: float


@dataclass(frozen=True)
class LongParagraph:
    path: str
    line: int
    characters: int
    preview: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="定位跨章重复句式、警告密度和超长段落候选。"
    )
    parser.add_argument("--root", default=".", help="Markdown 根目录。")
    parser.add_argument("--report", help="Markdown 报告输出路径。")
    parser.add_argument("--json", dest="json_path", help="JSON 报告输出路径。")
    parser.add_argument(
        "--include-maintenance",
        action="store_true",
        help="同时扫描路线图、发布说明和维护记录。",
    )
    parser.add_argument(
        "--duplicate-min-chars",
        type=int,
        default=30,
        help="重复句候选的最小可见字符数，默认 30。",
    )
    parser.add_argument(
        "--long-paragraph-chars",
        type=int,
        default=300,
        help="超长自然段候选阈值，默认 300。",
    )
    return parser.parse_args(argv)


def clean_inline(text: str) -> str:
    text = LINK_RE.sub(lambda match: match.group(1), text)
    text = INLINE_CODE_RE.sub(" CODE ", text)
    text = HTML_RE.sub(" ", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("~~", "").replace("*", "")
    return SPACE_RE.sub(" ", text).strip()


def visible_length(text: str) -> int:
    return len(NON_WORD_RE.sub("", text))


def normalize_sentence(text: str) -> str:
    text = clean_inline(text).casefold()
    return NON_WORD_RE.sub("", text)


def opener(text: str, length: int = 14) -> str:
    compact = NON_WORD_RE.sub("", clean_inline(text))
    return compact[:length]


def is_maintenance(relative: str) -> bool:
    if relative in MAINTENANCE_PATHS:
        return True
    return relative.startswith("Appendix/V3.0-")


def iter_markdown_files(root: Path, include_maintenance: bool) -> Iterator[Path]:
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in parts):
            continue
        relative = path.relative_to(root).as_posix()
        if not include_maintenance and is_maintenance(relative):
            continue
        yield path


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    if TABLE_RULE_RE.match(stripped):
        return True
    return stripped.startswith("|") and stripped.count("|") >= 2


def extract_paragraphs(path: Path, root: Path) -> list[Paragraph]:
    text = path.read_text(encoding="utf-8", errors="replace")
    relative = path.relative_to(root).as_posix()
    paragraphs: list[Paragraph] = []
    buffer: list[str] = []
    start_line = 0
    in_fence = False
    fence_char = ""
    fence_len = 0

    def flush() -> None:
        nonlocal buffer, start_line
        if not buffer:
            return
        content = clean_inline(" ".join(buffer))
        if visible_length(content) >= 12:
            paragraphs.append(Paragraph(relative, start_line, content))
        buffer = []
        start_line = 0

    for number, raw in enumerate(text.splitlines(), start=1):
        fence_match = FENCE_RE.match(raw)
        if fence_match:
            flush()
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
                fence_char = ""
                fence_len = 0
            continue
        if in_fence:
            continue

        stripped = raw.strip()
        if not stripped:
            flush()
            continue
        if HEADING_RE.match(raw) or LIST_RE.match(raw) or is_table_line(raw):
            flush()
            continue
        if stripped.startswith(">"):
            stripped = stripped.lstrip("> ")
            if not stripped:
                flush()
                continue
        if not buffer:
            start_line = number
        buffer.append(stripped)

    flush()
    return paragraphs


def split_sentences(paragraph: Paragraph) -> list[tuple[str, Location]]:
    results: list[tuple[str, Location]] = []
    for sentence in SENTENCE_SPLIT_RE.split(paragraph.text):
        sentence = sentence.strip()
        if visible_length(sentence) >= 8:
            results.append((sentence, Location(paragraph.path, paragraph.line)))
    return results


def limited_locations(locations: list[Location], limit: int = 6) -> list[Location]:
    unique: list[Location] = []
    seen: set[tuple[str, int]] = set()
    for item in locations:
        key = (item.path, item.line)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


def analyze(
    root: Path,
    include_maintenance: bool,
    duplicate_min_chars: int,
    long_paragraph_chars: int,
) -> dict[str, object]:
    paragraphs: list[Paragraph] = []
    files = list(iter_markdown_files(root, include_maintenance))
    for path in files:
        paragraphs.extend(extract_paragraphs(path, root))

    sentence_locations: dict[str, list[Location]] = defaultdict(list)
    sentence_display: dict[str, str] = {}
    opening_locations: dict[str, list[Location]] = defaultdict(list)
    file_sentence_count: Counter[str] = Counter()
    file_warning_count: Counter[str] = Counter()
    formulaic_by_file: dict[str, Counter[str]] = defaultdict(Counter)
    long_paragraphs: list[LongParagraph] = []

    for paragraph in paragraphs:
        paragraph_length = visible_length(paragraph.text)
        if paragraph_length >= long_paragraph_chars:
            preview = paragraph.text
            if len(preview) > 150:
                preview = preview[:147] + "..."
            long_paragraphs.append(
                LongParagraph(
                    paragraph.path,
                    paragraph.line,
                    paragraph_length,
                    preview,
                )
            )

        opening = opener(paragraph.text)
        if len(opening) >= 8:
            opening_locations[opening].append(Location(paragraph.path, paragraph.line))

        for sentence, location in split_sentences(paragraph):
            file_sentence_count[paragraph.path] += 1
            if WARNING_RE.search(sentence):
                file_warning_count[paragraph.path] += 1
            for label, pattern in FORMULAIC_PATTERNS.items():
                if pattern.search(sentence):
                    formulaic_by_file[paragraph.path][label] += 1

            normalized = normalize_sentence(sentence)
            if len(normalized) < duplicate_min_chars:
                continue
            sentence_locations[normalized].append(location)
            sentence_display.setdefault(normalized, sentence)

    duplicates: list[DuplicateSentence] = []
    for normalized, locations in sentence_locations.items():
        files_seen = {item.path for item in locations}
        if len(files_seen) < 2:
            continue
        duplicates.append(
            DuplicateSentence(
                sentence_display[normalized],
                len(files_seen),
                len(locations),
                limited_locations(locations),
            )
        )
    duplicates.sort(key=lambda item: (-item.files, -item.occurrences, item.sentence))

    openings: list[RepeatedOpening] = []
    for prefix, locations in opening_locations.items():
        files_seen = {item.path for item in locations}
        if len(files_seen) < 3 or len(locations) < 3:
            continue
        openings.append(
            RepeatedOpening(
                prefix,
                len(files_seen),
                len(locations),
                limited_locations(locations),
            )
        )
    openings.sort(key=lambda item: (-item.files, -item.occurrences, item.opening))

    densities: list[FileDensity] = []
    for path, sentence_count in file_sentence_count.items():
        warning_count = file_warning_count[path]
        if sentence_count < 8 or warning_count < 3:
            continue
        densities.append(
            FileDensity(
                path,
                sentence_count,
                warning_count,
                round(warning_count / sentence_count, 4),
            )
        )
    densities.sort(key=lambda item: (-item.density, -item.warning_sentences, item.path))

    formulaic_rows: list[dict[str, object]] = []
    for path, counts in formulaic_by_file.items():
        total = sum(counts.values())
        if total < 2:
            continue
        formulaic_rows.append(
            {
                "path": path,
                "total": total,
                "markers": dict(counts.most_common()),
            }
        )
    formulaic_rows.sort(key=lambda item: (-int(item["total"]), str(item["path"])))

    long_paragraphs.sort(key=lambda item: (-item.characters, item.path, item.line))

    return {
        "summary": {
            "markdown_files": len(files),
            "natural_paragraphs": len(paragraphs),
            "sentences": sum(file_sentence_count.values()),
            "duplicate_sentence_candidates": len(duplicates),
            "repeated_opening_candidates": len(openings),
            "warning_density_candidates": len(densities),
            "long_paragraph_candidates": len(long_paragraphs),
        },
        "duplicates": [asdict(item) for item in duplicates],
        "openings": [asdict(item) for item in openings],
        "warning_density": [asdict(item) for item in densities],
        "formulaic_markers": formulaic_rows,
        "long_paragraphs": [asdict(item) for item in long_paragraphs],
    }


def location_text(items: list[dict[str, object]]) -> str:
    return "<br>".join(f"`{item['path']}:{item['line']}`" for item in items)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_report(root: Path, result: dict[str, object]) -> str:
    summary = result["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# 公式化文风候选审计",
        "",
        "> 本报告只定位候选，不作为自动质量门。重复句可能是必要安全边界，列表和模板也可能具有真实用途，所有修改都需要回到章节职责与上下文人工判断。",
        "",
        f"- 根目录：`{root}`",
        f"- Markdown 文件：{summary['markdown_files']}",
        f"- 自然段：{summary['natural_paragraphs']}",
        f"- 句子：{summary['sentences']}",
        f"- 跨文件重复长句候选：{summary['duplicate_sentence_candidates']}",
        f"- 重复段落开头候选：{summary['repeated_opening_candidates']}",
        f"- 警告句密度候选文件：{summary['warning_density_candidates']}",
        f"- 超长段落候选：{summary['long_paragraph_candidates']}",
        "",
        "## 跨文件重复长句",
        "",
        "| 文件数 | 次数 | 句子 | 位置 |",
        "| ---: | ---: | --- | --- |",
    ]

    duplicates = result["duplicates"]
    assert isinstance(duplicates, list)
    for item in duplicates[:40]:
        assert isinstance(item, dict)
        lines.append(
            f"| {item['files']} | {item['occurrences']} | "
            f"{escape_cell(str(item['sentence']))} | "
            f"{location_text(item['locations'])} |"
        )
    if not duplicates:
        lines.append("| 0 | 0 | 无候选 | — |")

    lines.extend(
        [
            "",
            "## 重复段落开头",
            "",
            "| 文件数 | 次数 | 开头 | 位置 |",
            "| ---: | ---: | --- | --- |",
        ]
    )
    openings = result["openings"]
    assert isinstance(openings, list)
    for item in openings[:30]:
        assert isinstance(item, dict)
        lines.append(
            f"| {item['files']} | {item['occurrences']} | "
            f"`{escape_cell(str(item['opening']))}` | "
            f"{location_text(item['locations'])} |"
        )
    if not openings:
        lines.append("| 0 | 0 | 无候选 | — |")

    lines.extend(
        [
            "",
            "## 警告句密度较高的文件",
            "",
            "| 文件 | 警告句 | 总句数 | 占比 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    densities = result["warning_density"]
    assert isinstance(densities, list)
    for item in densities[:30]:
        assert isinstance(item, dict)
        lines.append(
            f"| `{item['path']}` | {item['warning_sentences']} | "
            f"{item['sentences']} | {float(item['density']):.1%} |"
        )
    if not densities:
        lines.append("| 无候选 | 0 | 0 | 0% |")

    lines.extend(
        [
            "",
            "## 公式化标记较集中的文件",
            "",
            "| 文件 | 总次数 | 标记 |",
            "| --- | ---: | --- |",
        ]
    )
    formulaic = result["formulaic_markers"]
    assert isinstance(formulaic, list)
    for item in formulaic[:30]:
        assert isinstance(item, dict)
        markers = item["markers"]
        assert isinstance(markers, dict)
        rendered = "、".join(f"{key}={value}" for key, value in markers.items())
        lines.append(f"| `{item['path']}` | {item['total']} | {rendered} |")
    if not formulaic:
        lines.append("| 无候选 | 0 | — |")

    lines.extend(
        [
            "",
            "## 超长自然段",
            "",
            "| 字符 | 位置 | 预览 |",
            "| ---: | --- | --- |",
        ]
    )
    long_items = result["long_paragraphs"]
    assert isinstance(long_items, list)
    for item in long_items[:40]:
        assert isinstance(item, dict)
        lines.append(
            f"| {item['characters']} | `{item['path']}:{item['line']}` | "
            f"{escape_cell(str(item['preview']))} |"
        )
    if not long_items:
        lines.append("| 0 | — | 无候选 |")

    lines.extend(
        [
            "",
            "## 人工使用方法",
            "",
            "优先查看同一句在多个产品专章重复出现、同一章节连续以相同句式开头、警告句超过正常解释密度，以及为了消除短段而形成的超长段落。保留必要的命令边界、错误恢复和模板结构；只有在章节职责确实重叠或措辞机械时才修改。",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：根目录不存在：{root}", file=sys.stderr)
        return 2
    if args.duplicate_min_chars < 12 or args.long_paragraph_chars < 80:
        print("错误：阈值过低。", file=sys.stderr)
        return 2

    result = analyze(
        root,
        args.include_maintenance,
        args.duplicate_min_chars,
        args.long_paragraph_chars,
    )
    report = render_report(root, result)
    print(report)

    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
    if args.json_path:
        json_path = Path(args.json_path).expanduser().resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
