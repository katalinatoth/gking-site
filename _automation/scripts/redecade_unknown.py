#!/usr/bin/env python3
"""Re-process the unknown-decade buckets for typed Writings folders.

The first run of regroup_writings.py used a regex that missed dates
written with single quotes (date: '1994-01-01'). This script re-scans
unknown-decade/ in each typed bucket and moves slugs to the right
decade folder when a parseable date can now be found.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITME = ROOT / "EditMe"
TYPED = ["Books", "Reports", "Patents", "CourtBriefs", "SoftwareNotes"]


def get_decade(index_md: Path) -> str:
    text = index_md.read_text(errors="replace")
    if not text.startswith("---"):
        return "unknown-decade"
    end = text.find("\n---", 3)
    if end < 0:
        return "unknown-decade"
    fm = text[3:end]
    m = re.search(r"""^\s*date\s*:\s*['"]?(\d{4})""", fm, re.MULTILINE)
    if not m:
        return "unknown-decade"
    year = int(m.group(1))
    return f"{(year // 10) * 10}s"


def main() -> int:
    moved = 0
    still_unknown = []
    for typed in TYPED:
        unknown_dir = EDITME / "Writings" / typed / "unknown-decade"
        if not unknown_dir.exists():
            continue
        for slug_dir in sorted(unknown_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            index_md = slug_dir / "index.md"
            if not index_md.exists():
                still_unknown.append(slug_dir)
                continue
            decade = get_decade(index_md)
            if decade == "unknown-decade":
                still_unknown.append(slug_dir)
                continue
            dst = EDITME / "Writings" / typed / decade / slug_dir.name
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "mv", str(slug_dir), str(dst)], check=True, cwd=ROOT)
            moved += 1
    # Remove empty unknown-decade dirs
    for typed in TYPED:
        unknown_dir = EDITME / "Writings" / typed / "unknown-decade"
        if unknown_dir.exists() and not any(unknown_dir.iterdir()):
            unknown_dir.rmdir()
    print(f"moved {moved}; still unknown: {len(still_unknown)}")
    for d in still_unknown[:10]:
        print(f"  {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
