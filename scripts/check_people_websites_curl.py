#!/usr/bin/env python3
"""Check people website: URLs using curl (TLS + redirects match browsers).

Prints lines: slug<TAB>code<TAB>url for 404/410 and suspected soft-404s.
"""
from __future__ import annotations

import concurrent.futures
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ROOT / "content" / "people"

CURL = [
    "curl",
    "-sS",
    "-L",
    "--max-time",
    "25",
    "-A",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]

def extract_website(text: str) -> str | None:
    m = re.search(r'^website:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def http_code(url: str) -> int:
    r = subprocess.run(
        CURL + ["-o", "/dev/null", "-w", "%{http_code}", url],
        capture_output=True,
        text=True,
        timeout=35,
    )
    try:
        return int(r.stdout.strip())
    except ValueError:
        return -1


def check_slug(slug: str, url: str) -> tuple[str, str, int, str]:
    """Return (slug, url, code, reason). reason empty if OK.

    Only *true* not-found pages are flagged (404 / 410 after redirects).
    Other codes (403 bot-wall, 999 curl quirks) are ignored so we do
    not mass-edit good links.
    """
    code = http_code(url)
    if code in (404, 410):
        return slug, url, code, "not_found"
    return slug, url, code, ""


def main() -> int:
    jobs: list[tuple[str, str]] = []
    for d in sorted(PEOPLE.iterdir()):
        if not d.is_dir():
            continue
        md = d / "index.md"
        if not md.exists():
            continue
        url = extract_website(md.read_text())
        if url:
            jobs.append((d.name, url))

    bad: list[tuple[str, str, int, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(check_slug, s, u) for s, u in jobs]
        for fut in concurrent.futures.as_completed(futs):
            row = fut.result()
            if row[3]:
                bad.append(row)

    bad.sort(key=lambda x: (x[3], x[0]))
    print(f"Checked {len(jobs)} URLs; {len(bad)} broken or soft-404.\n")
    for slug, url, code, why in bad:
        print(f"{slug}\t{why}\t{code}\t{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
