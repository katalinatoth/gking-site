#!/usr/bin/env python3
"""One-off helper: split EditMe/Writings/Articles/Unsorted/ into typed
sub-folders (Books/, Reports/, Patents/, CourtBriefs/, SoftwareNotes/)
using writings_legacy_map.json. Articles (tab="journal") are left in
Articles/Unsorted/ for phase 5 to topic+decade them.

Within each non-Article bucket, slugs are nested by decade.

This script is idempotent: running it twice has no effect once the moves
are done.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITME = ROOT / "EditMe"
ARTICLES_UNSORTED = EDITME / "Writings" / "Articles" / "Unsorted"
WRITINGS = EDITME / "Writings"
LEGACY_MAP = EDITME / "Writings" / "Data" / "writings_legacy_map.json"

# Each tab maps to (target folder name under EditMe/Writings/, decade-nested?)
TAB_TO_FOLDER = {
    "book":       ("Books", True),
    "other":      ("Reports", True),
    "patent":     ("Patents", True),
    "courtbrief": ("CourtBriefs", True),
    "software":   ("SoftwareNotes", True),
    "journal":    None,  # leave in Articles/Unsorted/ for phase 5
    "presentation": None,  # already in Presentations/Unsorted/
}


def get_decade_from_frontmatter(index_md: Path) -> str:
    """Pull the `date:` field from frontmatter and return e.g. '2010s'."""
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
    decade_start = (year // 10) * 10
    return f"{decade_start}s"


def git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "mv", str(src), str(dst)], check=True, cwd=ROOT)


def main() -> int:
    if not LEGACY_MAP.exists():
        print(f"Missing {LEGACY_MAP}", file=sys.stderr)
        return 1
    with open(LEGACY_MAP) as f:
        entries = json.load(f)["entries"]

    moved = {tab: 0 for tab in TAB_TO_FOLDER}
    skipped_no_index: list[str] = []
    missing_in_map: list[str] = []
    missing_folder: list[str] = []

    for slug_dir in sorted(ARTICLES_UNSORTED.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        index_md = slug_dir / "index.md"
        if not index_md.exists():
            skipped_no_index.append(slug)
            continue

        entry = entries.get(slug)
        if not entry:
            # No legacy-map entry — leave in Unsorted as journal-like default.
            missing_in_map.append(slug)
            continue

        tab = entry.get("tab", "journal")
        target = TAB_TO_FOLDER.get(tab)
        if target is None:
            # journal or presentation — leave alone
            moved.setdefault(tab, 0)
            moved[tab] += 1
            continue
        folder_name, decade_nested = target
        decade = get_decade_from_frontmatter(index_md) if decade_nested else None
        dst_root = WRITINGS / folder_name
        dst = dst_root / decade / slug if decade else dst_root / slug
        if dst.exists():
            continue  # idempotent
        git_mv(slug_dir, dst)
        moved[tab] += 1

    print("\n--- regroup_writings.py summary ---")
    for tab, count in moved.items():
        print(f"  tab={tab!r:<14} count={count}")
    if skipped_no_index:
        print(f"  skipped (no index.md): {len(skipped_no_index)}")
        for s in skipped_no_index[:5]:
            print(f"    {s}")
    if missing_in_map:
        print(f"  missing from legacy_map (left in Unsorted): {len(missing_in_map)}")
        for s in missing_in_map[:5]:
            print(f"    {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
