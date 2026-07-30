#!/usr/bin/env python3
"""Offline regression tests for the release-audit helper scripts."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_external_links as links  # noqa: E402
from scripts import audit_sensitive_patterns as secrets  # noqa: E402


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
PRINTF_FORMAT_RE = re.compile(r"^\s*printf(?:\s+--)?\s+(['\"])")
SHELL_FENCE_LANGUAGES = {"bash", "sh", "shell", "zsh"}


def printf_format_crosses_physical_line(line: str) -> bool:
    """Return True when printf's quoted format does not close on this line.

    Handbook examples should express output newlines as ``\n`` inside the
    format argument. A format quote crossing a physical Markdown line is a
    strong signal that an escaped newline was accidentally converted into a
    literal newline while content was written through an API.
    """

    match = PRINTF_FORMAT_RE.match(line)
    if match is None:
        return False

    quote = match.group(1)
    escaped = False
    for char in line[match.end() :]:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == quote:
            return False
    return True


def split_printf_locations(path: Path) -> list[int]:
    """Find suspicious printf format lines inside labelled shell fences."""

    lines = path.read_text(encoding="utf-8").splitlines()
    open_fence: tuple[str, int, bool] | None = None
    findings: list[int] = []

    for line_number, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            token = fence_match.group(1)
            char = token[0]
            length = len(token)
            if open_fence is None:
                info = fence_match.group(2).strip()
                language = info.split(None, 1)[0].lower() if info else ""
                open_fence = (char, length, language in SHELL_FENCE_LANGUAGES)
            elif char == open_fence[0] and length >= open_fence[1]:
                open_fence = None
            continue

        if open_fence is None or not open_fence[2]:
            continue
        if printf_format_crosses_physical_line(line):
            findings.append(line_number)

    return findings


class ExternalLinkAuditTests(unittest.TestCase):
    def test_placeholder_host_is_skipped(self) -> None:
        self.assertIsNone(links.normalize_url("https://example.com/private/path"))

    def test_fragment_is_removed_but_query_is_preserved(self) -> None:
        normalized = links.normalize_url(
            "HTTPS://docs.github.com/en/actions?tab=readme#workflow-syntax"
        )
        self.assertEqual(
            normalized,
            "https://docs.github.com/en/actions?tab=readme",
        )

    def test_embedded_credentials_are_redacted_and_blocked(self) -> None:
        raw = (
            "https://"
            + "alice"
            + ":"
            + "not-a-real-password"
            + "@docs.github.com/en/actions"
        )
        normalized = links.normalize_url(raw)
        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertNotIn("not-a-real-password", normalized)
        self.assertIn("redacted-credentials@", normalized)
        with self.assertRaises(links.UnsafeTargetError):
            links.ensure_public_target(normalized)

    def test_non_public_literal_addresses_are_blocked(self) -> None:
        unsafe_urls = (
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
        )
        for url in unsafe_urls:
            with self.subTest(url=url):
                with self.assertRaises(links.UnsafeTargetError):
                    links.ensure_public_target(url)

    def test_non_public_hostname_suffix_is_blocked_without_dns(self) -> None:
        with self.assertRaises(links.UnsafeTargetError):
            links.ensure_public_target("https://service.internal/status")

    def test_public_literal_address_is_allowed(self) -> None:
        links.ensure_public_target("https://1.1.1.1/")


class SensitivePatternAuditTests(unittest.TestCase):
    @staticmethod
    def fake_github_token() -> str:
        return "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"

    def test_finding_report_never_echoes_complete_secret(self) -> None:
        token = self.fake_github_token()
        findings = secrets.scan_lines([f"token={token}"], "test", "fixture")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule, "github-classic-token")

        report = secrets.render_report(
            ROOT,
            "tree",
            findings,
            scanned_files=1,
            skipped_binary=0,
            history_added_lines=0,
            history_message_lines=0,
        )
        self.assertNotIn(token, report)
        self.assertIn(findings[0].fingerprint, report)

    def test_placeholder_marker_is_ignored(self) -> None:
        token = "ghp_" + "EXAMPLE" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        findings = secrets.scan_lines([f"token={token}"], "test", "fixture")
        self.assertEqual(findings, [])

    def test_private_key_header_is_detected_without_storing_key_body(self) -> None:
        marker = "-----BEGIN " + "OPENSSH " + "PRIVATE KEY-----"
        findings = secrets.scan_lines([marker], "test", "fixture")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule, "private-key-block")

    def test_history_message_source_is_supported(self) -> None:
        token = self.fake_github_token()
        findings = secrets.scan_line(
            f"temporary credential {token}",
            "history-message",
            "deadbeef0000:commit-message:1",
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].source, "history-message")


class ShellExampleRegressionTests(unittest.TestCase):
    def test_normal_printf_formats_close_on_same_line(self) -> None:
        valid_examples = (
            r"printf '%s\n' \"$PATH\" | tr ':' '\n'",
            r"printf 'hello\n' > message.txt",
            r'printf "value=%s\n" "$value"',
            r"printf -- '%s\n' item",
        )
        for example in valid_examples:
            with self.subTest(example=example):
                self.assertFalse(printf_format_crosses_physical_line(example))

    def test_split_printf_format_is_detected(self) -> None:
        self.assertTrue(printf_format_crosses_physical_line("printf '%s"))
        self.assertTrue(printf_format_crosses_physical_line('printf "value=%s'))
        self.assertFalse(printf_format_crosses_physical_line("echo '%s"))

    def test_repository_has_no_split_printf_formats(self) -> None:
        findings: list[str] = []
        for path in sorted(ROOT.rglob("*.md")):
            if ".git" in path.parts:
                continue
            for line_number in split_printf_locations(path):
                findings.append(f"{path.relative_to(ROOT)}:{line_number}")

        self.assertEqual(
            findings,
            [],
            "Shell 代码块中的 printf 格式参数跨越物理行；"
            "若要输出换行，请在同一行格式字符串中写 \\n。\n"
            + "\n".join(findings),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
