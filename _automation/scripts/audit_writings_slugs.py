#!/usr/bin/env python3
"""Audit publication folders for slug/URL mismatches.

Walks every EditMe/Writings/**/index.md bundle, computes the canonical
public URL slug from the title, and reports any folder whose name differs
from what Hugo would publish as the :slug.

Usage:
    python3 _automation/scripts/audit_writings_slugs.py            # table
    python3 _automation/scripts/audit_writings_slugs.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_automation" / "lib"))
from slug import public_slug  # noqa: E402


WRITINGS_DIR = ROOT / "EditMe" / "Writings"


def _extract_title(md_path: Path) -> str | None:
    """Extract the title from front matter (first 5000 bytes)."""
    text = md_path.read_text(encoding="utf-8")[:5000]
    m = re.search(r'^title:\s*"(.+?)"\s*$', text, re.M)
    if not m:
        m = re.search(r"^title:\s*'(.+?)'\s*$", text, re.M)
    if not m:
        m = re.search(r"^title:\s*(.+?)\s*$", text, re.M)
    return m.group(1).strip() if m else None


def _extract_explicit_slug(md_path: Path) -> str | None:
    """Extract explicit slug: field from front matter."""
    text = md_path.read_text(encoding="utf-8")[:5000]
    m = re.search(r'^slug:\s*"?([^"\n]+)"?\s*$', text, re.M)
    return m.group(1).strip() if m else None


def audit() -> list[dict]:
    """Return list of mismatches: {folder, path, title, expected_slug, explicit_slug}."""
    mismatches = []
    for md in sorted(WRITINGS_DIR.rglob("index.md")):
        if md.parent.name == "Data":
            continue
        folder = md.parent.name
        title = _extract_title(md)
        if not title:
            continue
        explicit = _extract_explicit_slug(md)
        expected = explicit if explicit else public_slug(title)
        if folder != expected:
            rel_path = md.parent.relative_to(ROOT)
            mismatches.append({
                "folder": folder,
                "path": str(rel_path),
                "title": title,
                "expected_slug": expected,
                "explicit_slug": explicit or "",
                "folder_len": len(folder),
            })
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    mismatches = audit()

    if args.json:
        print(json.dumps(mismatches, indent=2))
    else:
        print(f"Found {len(mismatches)} folder/slug mismatches:\n")
        truncated = sum(1 for m in mismatches if m["folder_len"] == 80)
        print(f"  ({truncated} are exactly 80 chars — truncated by intake)\n")
        print(f"{'FOLDER':<82} {'EXPECTED SLUG'}")
        print("-" * 160)
        for m in mismatches:
            print(f"{m['folder']:<82} {m['expected_slug']}")
        print(f"\nTotal: {len(mismatches)} mismatches")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
