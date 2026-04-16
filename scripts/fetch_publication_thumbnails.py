#!/usr/bin/env python3
"""Download legacy Drupal thumbnails into publication bundles as featured.png."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

BASE = Path(__file__).resolve().parents[1]
PUB = BASE / "content" / "publication"
SCRAPED = BASE.parent / "scraped_data" / "pages"
LEGACY_BASE = "https://gking.harvard.edu"

# First thumbnail-style image in publication body (excludes header/footer logos).
IMG_RE = re.compile(
    r'<img[^>]+src="(/sites/g/files/omnuum7116/files/styles/hwp[^"]+/public/gking/files/[^"]+)"',
    re.IGNORECASE | re.DOTALL,
)


def has_featured(d: Path) -> bool:
    for f in os.listdir(d):
        if "featured" in f.lower() and f.lower().rsplit(".", 1)[-1] in (
            "png",
            "jpg",
            "jpeg",
            "webp",
            "gif",
        ):
            return True
    return False


def extract_img_url(html: str) -> str | None:
    m = IMG_RE.search(html)
    return m.group(1) if m else None


def main() -> int:
    if not SCRAPED.is_dir():
        print(f"Missing scraped pages dir: {SCRAPED}", file=sys.stderr)
        return 1

    dirs = sorted([p for p in PUB.iterdir() if p.is_dir() and not p.name.startswith(".")])
    ok = skip = fail = 0
    for d in dirs:
        if has_featured(d):
            skip += 1
            continue
        html_path = SCRAPED / f"{d.name}.html"
        if not html_path.is_file():
            fail += 1
            print(f"NO_HTML\t{d.name}")
            continue
        html = html_path.read_text(encoding="utf-8", errors="replace")
        rel = extract_img_url(html)
        if not rel:
            fail += 1
            print(f"NO_IMG\t{d.name}")
            continue
        url = urljoin(LEGACY_BASE, rel)
        out = d / "featured.png"
        try:
            subprocess.run(
                ["curl", "-fsSL", "-o", str(out), url],
                check=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            fail += 1
            print(f"CURL_FAIL\t{d.name}\t{url}\t{e}")
            continue
        # Verify looks like an image; rename to .jpg if needed
        probe = subprocess.run(["file", str(out)], capture_output=True, text=True)
        pl = probe.stdout.lower()
        if "jpeg" in pl or "jpg" in pl:
            jpg = d / "featured.jpg"
            out.rename(jpg)
            out = jpg
        elif "png" not in pl and "image" not in pl:
            out.unlink(missing_ok=True)
            fail += 1
            print(f"BAD_FILE\t{d.name}\t{probe.stdout.strip()}")
            continue
        ok += 1
        print(f"OK\t{d.name}")
        time.sleep(0.15)
    print(f"done: ok={ok} skipped_had_featured={skip} failed={fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
