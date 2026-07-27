#!/usr/bin/env python3
"""检查仓库中的 Markdown 结构和本地链接。

脚本只使用 Python 标准库，适合在全新 macOS 或 Ubuntu 环境中直接运行。
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data", "ftp"}


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    message: str


def find_repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError("当前目录不在 Git 仓库中。请在仓库内运行。")
    return Path(result.stdout.strip()).resolve()


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "无法读取 Git 跟踪文件。")
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def normalize_heading(text: str) -> str:
    text = re.sub(r"\s+#+\s*$", "", text).strip()
    return re.sub(r"\s+", " ", text)


def parse_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]

    match = re.match(r"^(\S+)(?:\s+[\"'].*[\"'])?$", target)
    return match.group(1) if match else target


def lexical_repo_path(source: str, target: str) -> str:
    source_parent = PurePosixPath(source).parent
    combined = source_parent / PurePosixPath(target)
    normalized = os.path.normpath(combined.as_posix()).replace("\\", "/")
    return normalized.removeprefix("./")


def directory_has_tracked_content(directory: str, all_tracked: set[str]) -> bool:
    """判断仓库目录下是否至少包含一个 Git 跟踪文件。"""
    prefix = directory.rstrip("/") + "/"
    return any(path.startswith(prefix) for path in all_tracked)


def inspect_markdown(
    root: Path,
    rel_path: str,
    min_chars: int,
    min_nonempty: int,
) -> tuple[list[Finding], list[tuple[str, int, str]]]:
    findings: list[Finding] = []
    links: list[tuple[str, int, str]] = []
    path = root / rel_path

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [Finding("ERROR", rel_path, exc.start, "文件不是有效 UTF-8。")], links

    lines = text.splitlines()
    nonempty = [line for line in lines if line.strip()]
    content_chars = len("".join(nonempty))
    if content_chars < min_chars and len(nonempty) < min_nonempty:
        findings.append(
            Finding(
                "WARN",
                rel_path,
                1,
                f"正文可能异常短：{content_chars} 个非空字符，{len(nonempty)} 个非空行。",
            )
        )

    headings: list[tuple[int, int, str]] = []
    open_fence: tuple[str, int, int] | None = None

    for line_no, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            token = fence_match.group(1)
            char = token[0]
            length = len(token)
            if open_fence is None:
                open_fence = (char, length, line_no)
            elif char == open_fence[0] and length >= open_fence[1]:
                open_fence = None
            continue

        if open_fence is not None:
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = normalize_heading(heading_match.group(2))
            headings.append((level, line_no, title))

        scan_line = INLINE_CODE_RE.sub("", line)
        for link_match in LINK_RE.finditer(scan_line):
            links.append((rel_path, line_no, parse_link_target(link_match.group(1))))

    if open_fence is not None:
        findings.append(
            Finding(
                "ERROR",
                rel_path,
                open_fence[2],
                f"围栏代码块未闭合：以 {open_fence[0] * open_fence[1]} 开始。",
            )
        )

    h1s = [(line_no, title) for level, line_no, title in headings if level == 1]
    if not h1s:
        findings.append(Finding("ERROR", rel_path, 1, "缺少一级标题。"))
    elif len(h1s) > 1:
        lines_text = ", ".join(str(line_no) for line_no, _ in h1s)
        findings.append(
            Finding("ERROR", rel_path, h1s[1][0], f"存在多个一级标题，行号：{lines_text}。")
        )

    h2_groups: dict[str, list[int]] = collections.defaultdict(list)
    for level, line_no, title in headings:
        if level == 2:
            h2_groups[title].append(line_no)
    for title, line_numbers in sorted(h2_groups.items()):
        if title and len(line_numbers) > 1:
            findings.append(
                Finding(
                    "WARN",
                    rel_path,
                    line_numbers[1],
                    f"重复二级标题“{title}”，行号：{', '.join(map(str, line_numbers))}。",
                )
            )

    return findings, links


def inspect_links(
    root: Path,
    links: list[tuple[str, int, str]],
    all_tracked: set[str],
) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    referenced_markdown: set[str] = set()

    for source, line_no, raw_target in links:
        target = raw_target.strip()
        if not target or target.startswith("#") or target.startswith("//"):
            continue

        split = urlsplit(target)
        if split.scheme.lower() in EXTERNAL_SCHEMES:
            continue
        if split.scheme and len(split.scheme) > 1:
            continue

        path_part = unquote(split.path)
        if not path_part:
            continue
        if "\\" in path_part:
            findings.append(Finding("WARN", source, line_no, f"本地链接使用反斜杠：{target}"))
            path_part = path_part.replace("\\", "/")

        repo_target = lexical_repo_path(source, path_part)
        if repo_target.startswith("../") or repo_target == "..":
            findings.append(Finding("ERROR", source, line_no, f"本地链接越出仓库：{target}"))
            continue

        disk_path = root / repo_target
        if repo_target in all_tracked:
            if repo_target.lower().endswith(".md"):
                referenced_markdown.add(repo_target)
            continue

        if disk_path.is_dir():
            if directory_has_tracked_content(repo_target, all_tracked):
                continue
            findings.append(
                Finding("WARN", source, line_no, f"链接目录存在但不包含 Git 跟踪文件：{repo_target}")
            )
            continue

        if disk_path.exists():
            findings.append(
                Finding("WARN", source, line_no, f"链接目标存在但未被 Git 跟踪：{repo_target}")
            )
        else:
            findings.append(Finding("ERROR", source, line_no, f"本地链接目标不存在：{repo_target}"))

    return findings, referenced_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="检查仓库中的 Markdown 结构和本地链接。")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库中的任意目录。")
    parser.add_argument("--summary", default="SUMMARY.md", help="目录文件路径。")
    parser.add_argument("--min-content-chars", type=int, default=500)
    parser.add_argument("--min-nonempty-lines", type=int, default=12)
    parser.add_argument("--strict-warnings", action="store_true", help="警告也返回非零状态。")
    args = parser.parse_args()

    try:
        root = find_repo_root(args.root.resolve())
        tracked = tracked_paths(root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    tracked_set = set(tracked)
    markdown_files = sorted(path for path in tracked if path.lower().endswith(".md"))
    findings: list[Finding] = []
    all_links: list[tuple[str, int, str]] = []

    for rel_path in markdown_files:
        file_findings, links = inspect_markdown(
            root,
            rel_path,
            min_chars=args.min_content_chars,
            min_nonempty=args.min_nonempty_lines,
        )
        findings.extend(file_findings)
        all_links.extend(links)

    link_findings, _ = inspect_links(root, all_links, tracked_set)
    findings.extend(link_findings)

    summary_path = args.summary.replace("\\", "/")
    if summary_path not in tracked_set:
        findings.append(Finding("ERROR", summary_path, 1, "目录文件不存在或未被 Git 跟踪。"))
    else:
        summary_links = [link for link in all_links if link[0] == summary_path]
        _, summary_targets = inspect_links(root, summary_links, tracked_set)
        exempt = {summary_path}
        orphaned = [path for path in markdown_files if path not in summary_targets and path not in exempt]
        for path in orphaned:
            findings.append(Finding("WARN", path, 1, f"Markdown 文件未被 {summary_path} 引用。"))

    severity_order = {"ERROR": 0, "WARN": 1}
    findings.sort(key=lambda item: (severity_order[item.severity], item.path, item.line, item.message))

    for finding in findings:
        print(f"{finding.severity}: {finding.path}:{finding.line}: {finding.message}")

    error_count = sum(item.severity == "ERROR" for item in findings)
    warning_count = sum(item.severity == "WARN" for item in findings)
    print(
        f"检查完成：{len(markdown_files)} 个 Markdown 文件，"
        f"{error_count} 个错误，{warning_count} 个警告。"
    )

    if error_count:
        return 1
    if warning_count and args.strict_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
