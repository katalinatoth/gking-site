#!/usr/bin/env python3
"""
Fetch each https://gking.harvard.edu/people/<slug> and extract:
  - research_group_categories (may be multiple — matches Drupal facet counts)
  - last_name_range (e.g. A-C) from /researchers-last-name/ link text

Rewrites people/data/research_group.json with:
  research_group_categories: [ ... ]
  last_name_range: "A-C"

Requires: curl on PATH.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "people" / "data" / "research_group.json"
BASE = "https://gking.harvard.edu/people"

PATH_TO_KEY = {
    "current-research-associates": "current",
    "alumni-students": "alumni_students",
    "alumni-post-docs": "alumni_postdocs",
    "collaborators": "collaborators",
}


def curl_get(url: str) -> str:
    r = subprocess.run(
        ["curl", "-sL", "--fail", "-A", "Mozilla/5.0 (RGSync)", "--max-time", "90", url],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl {r.returncode}: {url}")
    return r.stdout


def parse_profile(html: str) -> tuple[list[str], str]:
    cats: list[str] = []
    seen: set[str] = set()
    for path, _label in re.findall(
        r'href="/category/research-group/([^"]+)"[^>]*>([^<]+)</a>', html
    ):
        key = PATH_TO_KEY.get(path)
        if key and key not in seen:
            seen.add(key)
            cats.append(key)
    rng_m = re.search(
        r'href="/researchers-last-name/[^"]+"[^>]*>([^<]+)</a>', html
    )
    range_norm = ""
    if rng_m:
        t = rng_m.group(1).strip()
        range_norm = re.sub(r"\s*-\s*", "-", t)
    return cats, range_norm


def fallback_range_from_title(title: str) -> str:
    """Last-resort bucket if profile omits Researchers-by-Last-Name card."""
    parts = title.strip().split()
    if not parts:
        return "A-C"
    c = parts[-1][0].upper() if parts[-1] else "A"
    if "A" <= c <= "C":
        return "A-C"
    if "D" <= c <= "G":
        return "D-G"
    if "H" <= c <= "J":
        return "H-J"
    if "K" <= c <= "L":
        return "K-L"
    if "M" <= c <= "P":
        return "M-P"
    if "Q" <= c <= "S":
        return "Q-S"
    if "T" <= c <= "V":
        return "T-V"
    return "W-Z"


def main() -> int:
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    out: list[dict] = []
    fail = 0
    for i, row in enumerate(rows):
        slug = row["slug"]
        url = f"{BASE}/{slug}"
        try:
            html = curl_get(url)
            cats, rng = parse_profile(html)
            if not cats:
                cats = [row.get("research_group_category") or "collaborators"]
            if not rng:
                rng = row.get("last_name_range") or fallback_range_from_title(
                    row.get("name") or ""
                )
            new_row = {
                "slug": slug,
                "name": row.get("name") or "",
                "affiliation": row.get("affiliation") or "",
                "research_group_categories": cats,
                "last_name_range": rng,
            }
            out.append(new_row)
        except Exception as e:
            print(f"FAIL {slug}: {e}", file=sys.stderr)
            fail += 1
            out.append(
                {
                    **row,
                    "research_group_categories": [
                        row.get("research_group_category") or "collaborators"
                    ],
                    "last_name_range": row.get("last_name_range", ""),
                }
            )
        if (i + 1) % 40 == 0:
            print(f"  … {i + 1}/{len(rows)}")
        time.sleep(0.12)

    DATA.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cat_totals: dict[str, int] = {k: 0 for k in PATH_TO_KEY.values()}
    rng_totals: dict[str, int] = {}
    for row in out:
        for c in row.get("research_group_categories") or []:
            cat_totals[c] = cat_totals.get(c, 0) + 1
        r = row.get("last_name_range") or "?"
        rng_totals[r] = rng_totals.get(r, 0) + 1

    print("Category facet counts (sum > 190 if people have multiple tags):", cat_totals)
    print("Letter ranges:", dict(sorted(rng_totals.items())))
    print(f"Wrote {len(out)} rows, failures {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
