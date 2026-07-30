#!/usr/bin/env python3
"""Scan the current tree and Git history for high-confidence secret patterns.

The script deliberately avoids broad "password=" style rules because this handbook
contains many configuration examples. Findings never print the complete matched
value; reports contain only the rule name, location, length and a short fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Finding:
    rule: str
    source: str
    location: str
    length: int
    fingerprint: str


RULES: tuple[Rule, ...] = (
    Rule(
        "private-key-block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"
        ),
    ),
    Rule("github-classic-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b")),
    Rule("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,255}\b")),
    Rule("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    Rule("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    Rule("anthropic-api-key", re.compile(r"\bsk-ant-[0-9A-Za-z_-]{20,255}\b")),
    Rule(
        "openai-style-api-key",
        re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-)?[0-9A-Za-z_-]{20,255}\b"),
    ),
    Rule("xai-api-key", re.compile(r"\bxai-[0-9A-Za-z_-]{20,255}\b")),
    Rule("huggingface-token", re.compile(r"\bhf_[0-9A-Za-z]{30,255}\b")),
    Rule("npm-token", re.compile(r"\bnpm_[0-9A-Za-z]{30,255}\b")),
    Rule("pypi-token", re.compile(r"\bpypi-[0-9A-Za-z_-]{40,255}\b")),
    Rule("slack-token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,255}\b")),
    Rule("stripe-live-key", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{20,255}\b")),
    Rule(
        "tailscale-key",
        re.compile(r"\btskey-(?:auth|client|api)-[0-9A-Za-z_-]{20,255}\b"),
    ),
    Rule(
        "long-bearer-token",
        re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+([0-9A-Za-z._~+/=-]{32,})"),
    ),
)

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

PLACEHOLDER_MARKERS = (
    "EXAMPLE",
    "PLACEHOLDER",
    "REDACTED",
    "REPLACE_ME",
    "REPLACE-ME",
    "YOUR_TOKEN",
    "YOUR_KEY",
    "DUMMY",
)

COMMIT_PREFIX = "__SECRET_SCAN_COMMIT__:"
MESSAGE_START = "__SECRET_SCAN_COMMIT_MESSAGE_START__"
MESSAGE_END = "__SECRET_SCAN_COMMIT_MESSAGE_END__"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="扫描当前目录与 Git 历史中的高置信度敏感信息特征。"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="扫描当前文件树的根目录，默认是当前目录。",
    )
    parser.add_argument(
        "--scope",
        choices=("tree", "history", "both"),
        default="both",
        help="扫描文件树、Git 历史或两者，默认 both。",
    )
    parser.add_argument(
        "--report",
        help="将完整脱敏报告写入指定文件。",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="发现任何未豁免匹配时返回非零状态。",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=5 * 1024 * 1024,
        help="单个文件的最大扫描字节数，默认 5 MiB。",
    )
    return parser.parse_args(argv)


def is_binary(data: bytes) -> bool:
    return b"\x00" in data[:8192]


def iter_text_files(root: Path, max_file_bytes: int) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def match_value(match: re.Match[str]) -> str:
    if match.lastindex:
        return match.group(match.lastindex)
    return match.group(0)


def is_placeholder(value: str, line: str) -> bool:
    upper_value = value.upper()
    upper_line = line.upper()
    if "SECRET-SCAN: ALLOW" in upper_line:
        return True
    if any(marker in upper_value for marker in PLACEHOLDER_MARKERS):
        return True
    compact = re.sub(r"[^A-Z0-9]", "", upper_value)
    if compact and len(set(compact)) <= 3 and len(compact) >= 12:
        return True
    return False


def fingerprint(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()
    return digest[:12]


def scan_line(line: str, source: str, location: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        for match in rule.pattern.finditer(line):
            value = match_value(match)
            if is_placeholder(value, line):
                continue
            findings.append(
                Finding(
                    rule=rule.name,
                    source=source,
                    location=location,
                    length=len(value),
                    fingerprint=fingerprint(value),
                )
            )
    return findings


def scan_lines(lines: Iterable[str], source: str, location_prefix: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(lines, start=1):
        findings.extend(scan_line(line, source, f"{location_prefix}:{line_number}"))
    return findings


def scan_tree(root: Path, max_file_bytes: int) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    scanned_files = 0
    skipped_binary = 0
    for path in iter_text_files(root, max_file_bytes):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_binary(data):
            skipped_binary += 1
            continue
        scanned_files += 1
        text = data.decode("utf-8", errors="replace")
        relative = path.relative_to(root).as_posix()
        findings.extend(scan_lines(text.splitlines(), "tree", relative))
    return findings, scanned_files, skipped_binary


def history_command(root: Path) -> list[str]:
    return [
        "git",
        "-C",
        str(root),
        "log",
        "--all",
        f"--format={COMMIT_PREFIX}%H%n{MESSAGE_START}%n%B%n{MESSAGE_END}",
        "--patch",
        "--no-color",
        "--no-ext-diff",
        "--unified=0",
    ]


def scan_history(root: Path) -> tuple[list[Finding], int, int]:
    if not (root / ".git").exists():
        raise RuntimeError("历史扫描要求 --root 指向 Git 仓库根目录。")

    process = subprocess.Popen(
        history_command(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    current_commit = "unknown"
    current_path = "unknown"
    in_message = False
    message_line = 0
    message_lines = 0
    added_lines = 0
    findings: list[Finding] = []

    for raw_line in process.stdout:
        line = raw_line.rstrip("\n")
        if in_message:
            if line == MESSAGE_END:
                in_message = False
                continue
            message_line += 1
            message_lines += 1
            findings.extend(
                scan_line(
                    line,
                    "history-message",
                    f"{current_commit}:commit-message:{message_line}",
                )
            )
            continue
        if line.startswith(COMMIT_PREFIX):
            current_commit = line.removeprefix(COMMIT_PREFIX)[:12]
            current_path = "unknown"
            message_line = 0
            continue
        if line == MESSAGE_START:
            in_message = True
            message_line = 0
            continue
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added_lines += 1
        content = line[1:]
        findings.extend(
            scan_line(
                content,
                "history-patch",
                f"{current_commit}:{current_path}:added-line-{added_lines}",
            )
        )

    stderr = ""
    if process.stderr is not None:
        stderr = process.stderr.read()
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"git log 扫描失败：{stderr.strip() or return_code}")
    return findings, added_lines, message_lines


def render_report(
    root: Path,
    scope: str,
    findings: Sequence[Finding],
    scanned_files: int,
    skipped_binary: int,
    history_added_lines: int,
    history_message_lines: int,
) -> str:
    lines = [
        "# 敏感信息扫描报告",
        "",
        f"- 根目录：`{root}`",
        f"- 扫描范围：`{scope}`",
        f"- 文本文件：{scanned_files}",
        f"- 跳过二进制文件：{skipped_binary}",
        f"- Git 历史补丁新增行：{history_added_lines}",
        f"- Git 历史提交说明行：{history_message_lines}",
        f"- 未豁免发现：{len(findings)}",
        "",
        "报告不会输出完整匹配值，只记录规则、位置、长度和 SHA-256 短指纹。",
        "",
    ]
    if not findings:
        lines.append("结果：未发现高置信度敏感信息特征。")
    else:
        lines.extend(
            [
                "## 发现",
                "",
                "| 规则 | 来源 | 位置 | 长度 | 指纹 |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        for item in findings:
            location = item.location.replace("|", "\\|")
            lines.append(
                f"| `{item.rule}` | `{item.source}` | `{location}` | "
                f"{item.length} | `{item.fingerprint}` |"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：扫描根目录不存在：{root}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    scanned_files = 0
    skipped_binary = 0
    history_added_lines = 0
    history_message_lines = 0

    try:
        if args.scope in {"tree", "both"}:
            tree_findings, scanned_files, skipped_binary = scan_tree(
                root, args.max_file_bytes
            )
            findings.extend(tree_findings)
        if args.scope in {"history", "both"}:
            history_findings, history_added_lines, history_message_lines = scan_history(root)
            findings.extend(history_findings)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    unique_findings = sorted(
        set(findings),
        key=lambda item: (item.source, item.location, item.rule, item.fingerprint),
    )
    report = render_report(
        root,
        args.scope,
        unique_findings,
        scanned_files,
        skipped_binary,
        history_added_lines,
        history_message_lines,
    )

    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
    print(report)

    if unique_findings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
