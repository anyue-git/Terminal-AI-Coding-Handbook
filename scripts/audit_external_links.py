#!/usr/bin/env python3
"""Audit external HTTP(S) links in Markdown files.

The checker ignores fenced code blocks and placeholder hosts. It treats confirmed
404/410 responses, malformed URLs and unsafe non-public targets as blocking
findings. Authentication, bot protection, rate limiting and transient network
failures are reported separately because they do not prove that a link is broken.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import ipaddress
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

PLACEHOLDER_HOSTS = {
    "example.com",
    "example.org",
    "example.net",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}

NON_PUBLIC_SUFFIXES = (
    ".internal",
    ".intranet",
    ".lan",
    ".local",
    ".localhost",
)

PASS_CODES = set(range(200, 400))
RESTRICTED_CODES = {401, 403, 407, 418, 429, 451}
BROKEN_CODES = {404, 410}
RETRYABLE_HEAD_CODES = {400, 405, 406, 409, 415, 500, 501, 502, 503, 504}


class UnsafeTargetError(ValueError):
    """Raised when a URL could reach credentials or a non-public network target."""


@dataclass(frozen=True)
class LinkResult:
    url: str
    category: str
    status: str
    detail: str


@dataclass(frozen=True)
class SourceRef:
    path: str
    line: int


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查 Markdown 中的外部 HTTP(S) 链接。"
    )
    parser.add_argument("--root", default=".", help="Markdown 根目录，默认当前目录。")
    parser.add_argument("--report", help="将 Markdown 报告写入指定文件。")
    parser.add_argument("--strict", action="store_true", help="发现确认死链或不安全目标时返回非零状态。")
    parser.add_argument("--timeout", type=float, default=12.0, help="单次请求超时秒数。")
    parser.add_argument("--workers", type=int, default=8, help="并发检查数量。")
    parser.add_argument("--retries", type=int, default=1, help="网络错误重试次数。")
    return parser.parse_args(argv)


def iter_markdown_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in parts):
            continue
        yield path


def trim_url(raw: str) -> str:
    url = raw.rstrip(".,;:!?，。；：！？")
    pairs = {")": "(", "]": "[", "}": "{"}
    changed = True
    while changed and url:
        changed = False
        closing = url[-1]
        opening = pairs.get(closing)
        if opening and url.count(closing) > url.count(opening):
            url = url[:-1]
            changed = True
    return url


def bracket_host(host: str) -> str:
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def normalize_url(raw: str) -> str | None:
    cleaned = trim_url(raw)
    parsed = urllib.parse.urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower().rstrip(".")
    if host in PLACEHOLDER_HOSTS or host.endswith(".example"):
        return None

    safe_host = bracket_host(host)
    try:
        port = parsed.port
    except ValueError:
        # Preserve a safe, non-secret representation that will be rejected later.
        netloc = f"invalid-authority@{safe_host}"
    else:
        port_suffix = f":{port}" if port is not None else ""
        if parsed.username is not None or parsed.password is not None:
            # Never copy embedded credentials into reports or Actions logs.
            netloc = f"redacted-credentials@{safe_host}{port_suffix}"
        else:
            netloc = f"{safe_host}{port_suffix}"

    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            netloc,
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def extract_links(root: Path) -> tuple[dict[str, list[SourceRef]], int]:
    sources: dict[str, list[SourceRef]] = defaultdict(list)
    files = 0
    for path in iter_markdown_files(root):
        files += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        in_fence = False
        fence_char = ""
        fence_len = 0
        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            fence_match = FENCE_RE.match(line)
            if fence_match:
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
            searchable = INLINE_CODE_RE.sub("", line)
            for match in URL_RE.finditer(searchable):
                url = normalize_url(match.group(0))
                if url is not None:
                    sources[url].append(SourceRef(relative, line_number))
    return dict(sources), files


def ensure_public_target(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise UnsafeTargetError("URL must use HTTP(S) and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeTargetError("embedded credentials or invalid authority are not allowed")

    host = parsed.hostname.lower().rstrip(".")
    if host in PLACEHOLDER_HOSTS or host.endswith(NON_PUBLIC_SUFFIXES):
        raise UnsafeTargetError(f"non-public hostname is not allowed: {host}")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeTargetError(f"invalid port: {exc}") from exc
    if port is not None and not 1 <= port <= 65535:
        raise UnsafeTargetError(f"invalid port: {port}")

    addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    try:
        addresses.add(ipaddress.ip_address(host))
    except ValueError:
        service_port = port or (443 if parsed.scheme.lower() == "https" else 80)
        infos = socket.getaddrinfo(
            host,
            service_port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
        for info in infos:
            address_text = info[4][0].split("%", 1)[0]
            addresses.add(ipaddress.ip_address(address_text))

    if not addresses:
        raise socket.gaierror(f"hostname did not resolve: {host}")
    unsafe = sorted(str(address) for address in addresses if not address.is_global)
    if unsafe:
        raise UnsafeTargetError(
            f"hostname resolves to non-public address(es): {', '.join(unsafe)}"
        )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects that leave the public HTTP(S) address space."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> urllib.request.Request | None:
        ensure_public_target(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request_once(url: str, method: str, timeout: float) -> int:
    ensure_public_target(url)
    headers = {
        "User-Agent": "Terminal-AI-Coding-Handbook-Link-Audit/1.0 (+GitHub Actions)",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }
    if method == "GET":
        headers["Range"] = "bytes=0-2047"
    request = urllib.request.Request(url, headers=headers, method=method)
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context),
        SafeRedirectHandler(),
    )
    with opener.open(request, timeout=timeout) as response:
        return int(response.getcode() or 200)


def classify_code(url: str, code: int, method: str) -> LinkResult:
    if code in PASS_CODES:
        return LinkResult(url, "ok", str(code), method)
    if code in RESTRICTED_CODES:
        return LinkResult(url, "restricted", str(code), f"{method}; authentication/bot/rate limit")
    if code in BROKEN_CODES:
        return LinkResult(url, "broken", str(code), f"{method}; confirmed not found")
    return LinkResult(url, "warning", str(code), f"{method}; unexpected HTTP status")


def check_url(url: str, timeout: float, retries: int) -> LinkResult:
    last_error = ""
    for attempt in range(retries + 1):
        try:
            code = request_once(url, "HEAD", timeout)
            result = classify_code(url, code, "HEAD")
            if result.category == "warning" and code in RETRYABLE_HEAD_CODES:
                code = request_once(url, "GET", timeout)
                return classify_code(url, code, "GET")
            return result
        except UnsafeTargetError as exc:
            return LinkResult(url, "broken", "unsafe-target", str(exc))
        except urllib.error.HTTPError as exc:
            code = int(exc.code)
            if code in RETRYABLE_HEAD_CODES or code in BROKEN_CODES:
                try:
                    get_code = request_once(url, "GET", timeout)
                    return classify_code(url, get_code, "GET")
                except UnsafeTargetError as get_exc:
                    return LinkResult(url, "broken", "unsafe-target", str(get_exc))
                except urllib.error.HTTPError as get_exc:
                    return classify_code(url, int(get_exc.code), "GET")
                except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as get_exc:
                    last_error = f"GET after HTTP {code}: {type(get_exc).__name__}: {get_exc}"
            else:
                return classify_code(url, code, "HEAD")
        except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        except ValueError as exc:
            return LinkResult(url, "broken", "malformed", str(exc))
        if attempt < retries:
            time.sleep(0.5 * (attempt + 1))
    return LinkResult(url, "network", "unreachable", last_error or "network error")


def render_sources(items: Iterable[SourceRef], limit: int = 4) -> str:
    refs = list(items)
    shown = [f"`{item.path}:{item.line}`" for item in refs[:limit]]
    if len(refs) > limit:
        shown.append(f"另 {len(refs) - limit} 处")
    return "<br>".join(shown)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_report(
    root: Path,
    markdown_files: int,
    sources: dict[str, list[SourceRef]],
    results: Sequence[LinkResult],
) -> str:
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        counts[result.category] += 1
    lines = [
        "# 外部链接审计报告",
        "",
        f"- 根目录：`{root}`",
        f"- Markdown 文件：{markdown_files}",
        f"- 去重后的外部链接：{len(results)}",
        f"- 正常：{counts['ok']}",
        f"- 受认证、反爬或限流限制：{counts['restricted']}",
        f"- 网络状态无法确认：{counts['network']}",
        f"- 其他警告：{counts['warning']}",
        f"- 确认死链或不安全目标：{counts['broken']}",
        "",
        "404、410、格式错误、内嵌凭据和非公网目标被视为阻断问题；401、403、429、连接超时等单独记录，不自动判定页面不存在。代码块和占位域名不参与检查，重定向也必须保持在公网 HTTP(S) 地址空间。",
        "",
        "| 结果 | 状态 | URL | 出现位置 | 说明 |",
        "| --- | --- | --- | --- | --- |",
    ]
    order = {"broken": 0, "warning": 1, "network": 2, "restricted": 3, "ok": 4}
    for result in sorted(results, key=lambda item: (order.get(item.category, 9), item.url)):
        lines.append(
            "| {category} | `{status}` | <{url}> | {sources} | {detail} |".format(
                category=result.category,
                status=escape_cell(result.status),
                url=escape_cell(result.url),
                sources=render_sources(sources[result.url]),
                detail=escape_cell(result.detail),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：根目录不存在：{root}", file=sys.stderr)
        return 2
    if args.workers < 1 or args.retries < 0 or args.timeout <= 0:
        print("错误：workers、retries 和 timeout 参数无效。", file=sys.stderr)
        return 2

    try:
        sources, markdown_files = extract_links(root)
    except OSError as exc:
        print(f"错误：读取 Markdown 失败：{exc}", file=sys.stderr)
        return 2

    urls = sorted(sources)
    results: list[LinkResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(check_url, url, args.timeout, args.retries): url for url in urls
        }
        for future in concurrent.futures.as_completed(future_map):
            url = future_map[future]
            try:
                results.append(future.result())
            except Exception as exc:  # Defensive boundary for one URL.
                results.append(LinkResult(url, "network", "exception", repr(exc)))

    report = render_report(root, markdown_files, sources, results)
    print(report)
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    broken = [item for item in results if item.category == "broken"]
    return 1 if args.strict and broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
