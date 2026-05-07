#!/usr/bin/env python3
"""Post-build rewrite: serve target-page content at short URL paths.

Run this AFTER `hugo build` (and after Pagefind indexing, to avoid
duplicating search entries).  It scans every index.html in public/ for
meta-refresh redirects.  When the target is an internal page that also
exists in public/, the redirect stub is overwritten with a copy of the
target page's fully rendered HTML.  The result: GitHub Pages serves the
real content at the short URL — no client-side redirect.

External targets (https://…) are left untouched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

# Matches <meta http-equiv="refresh" content="0; url=TARGET">
# Handles both absolute and relative URLs, with or without quotes.
_REFRESH_RE = re.compile(
    r'<meta\s+http-equiv=["\']?refresh["\']?\s+'
    r'content=["\']?\d+;\s*url=([^"\'>\s]+)',
    re.IGNORECASE,
)


def _base_url() -> str:
    """Read baseURL from hugo.yaml so we can strip it from absolute targets."""
    for name in ("hugo.yaml", "hugo.toml", "config.yaml", "config.toml"):
        p = ROOT / name
        if p.exists():
            text = p.read_text()
            m = re.search(r'baseURL:\s*["\']?(https?://[^"\'>\s]+)', text)
            if m:
                return m.group(1).rstrip("/")
    return ""


def _to_relative(url: str, base: str) -> str | None:
    """Convert an internal URL to a root-relative path, or None if external."""
    url = url.strip()
    if url.startswith("/"):
        return url
    if base and url.startswith(base):
        return url[len(base):] or "/"
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        return None  # external
    return "/" + url  # bare relative path


def _resolve_src(rel_path: str) -> Path | None:
    """Find the rendered index.html for a root-relative URL path."""
    cleaned = rel_path.strip("/")
    if not cleaned:
        candidate = PUBLIC / "index.html"
    else:
        candidate = PUBLIC / cleaned / "index.html"
    return candidate if candidate.exists() else None


def main() -> int:
    if not PUBLIC.exists():
        print("[apply_rewrites] public/ not found — run `hugo` first.")
        return 1

    base = _base_url()
    applied = skipped_ext = skipped_miss = 0

    for html_file in sorted(PUBLIC.rglob("index.html")):
        try:
            head = html_file.read_text(encoding="utf-8", errors="replace")[:4096]
        except OSError:
            continue

        m = _REFRESH_RE.search(head)
        if not m:
            continue

        raw_target = m.group(1)
        rel_target = _to_relative(raw_target, base)
        if rel_target is None:
            skipped_ext += 1
            continue

        src = _resolve_src(rel_target)
        if src is None:
            rel_from = str(html_file.parent.relative_to(PUBLIC))
            print(
                f"  SKIP /{rel_from}/ → {rel_target} "
                f"(target not found in public/)"
            )
            skipped_miss += 1
            continue

        if src.resolve() == html_file.resolve():
            continue

        html_file.write_bytes(src.read_bytes())
        applied += 1

    print(
        f"[apply_rewrites] {applied} page(s) rewritten, "
        f"{skipped_ext} external skipped, "
        f"{skipped_miss} target(s) not found."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
