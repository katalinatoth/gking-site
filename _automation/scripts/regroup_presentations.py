#!/usr/bin/env python3
"""Cluster talks in EditMe/Writings/Presentations/Unsorted/ into
<title-slug>/<venue-slug>/ folders.

Title-slug comes from each talk's frontmatter `title:` field, slugified
(lowercase, ASCII-only, dashes between words). Venue-slug is the talk's
original folder name. After running, every talk lives at
EditMe/Writings/Presentations/<title-slug>/<venue-slug>/index.md.

Talks whose title slugifies identically end up sharing one title folder
even if their original folder slugs differ; that's the desired
clustering behaviour.
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITME = ROOT / "EditMe"
PRES = EDITME / "Writings" / "Presentations"
UNSORTED = PRES / "Unsorted"


def slugify(value: str) -> str:
    """Convert *value* into a lowercase ASCII-only kebab-case slug."""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or "untitled"


def extract_title(index_md: Path) -> str | None:
    text = index_md.read_text(errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fm = text[3:end]
    m = re.search(r"""^\s*title\s*:\s*['"]?(.+?)['"]?\s*$""", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "mv", str(src), str(dst)], check=True, cwd=ROOT)


def main() -> int:
    if not UNSORTED.exists():
        print("nothing to do — Unsorted/ doesn't exist", file=sys.stderr)
        return 0

    moves: list[tuple[Path, Path]] = []
    skipped: list[str] = []
    title_to_count: dict[str, int] = {}

    for slug_dir in sorted(UNSORTED.iterdir()):
        if not slug_dir.is_dir():
            continue
        index_md = slug_dir / "index.md"
        if not index_md.exists():
            skipped.append(slug_dir.name)
            continue
        title = extract_title(index_md)
        if not title:
            skipped.append(slug_dir.name)
            continue
        title_slug = slugify(title)
        venue_slug = slug_dir.name
        title_to_count[title_slug] = title_to_count.get(title_slug, 0) + 1
        dst = PRES / title_slug / venue_slug
        moves.append((slug_dir, dst))

    for src, dst in moves:
        if dst.exists():
            continue
        git_mv(src, dst)

    # Move the section _index.md up to Presentations/_index.md so /talk/ keeps
    # its list page.
    pres_index = UNSORTED / "_index.md"
    if pres_index.exists() and not (PRES / "_index.md").exists():
        git_mv(pres_index, PRES / "_index.md")

    # Remove Unsorted/ if empty
    if UNSORTED.exists() and not any(UNSORTED.iterdir()):
        UNSORTED.rmdir()

    multi_venue = sum(1 for c in title_to_count.values() if c > 1)
    print("\n--- regroup_presentations.py summary ---")
    print(f"  total talks moved : {len(moves)}")
    print(f"  unique titles     : {len(title_to_count)}")
    print(f"  multi-venue titles: {multi_venue}")
    print(f"  skipped           : {len(skipped)}")
    for s in skipped[:5]:
        print(f"    {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
