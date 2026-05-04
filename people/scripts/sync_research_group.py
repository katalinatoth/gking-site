#!/usr/bin/env python3
"""
Scrape https://gking.harvard.edu/people and sync
people/data/research_group.json plus people/content/profiles/<slug>/index.md
(role + research_group_category).

Requires: curl on PATH.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_OUT = ROOT / "people" / "data" / "research_group.json"
PEOPLE = ROOT / "people" / "content" / "profiles"
BASE = "https://gking.harvard.edu"

# Query value for f[0]= — must match original site facets
CATEGORIES = [
    ("current", "Current Research Associates", "hwp_c_vocabulary_175%3A1589"),
    ("alumni_students", "Alumni: Students", "hwp_c_vocabulary_175%3A1590"),
    ("alumni_postdocs", "Alumni: Post-Docs", "hwp_c_vocabulary_175%3A1591"),
    ("collaborators", "Collaborators", "hwp_c_vocabulary_175%3A1592"),
]


def curl_get(url: str) -> str:
    r = subprocess.run(
        ["curl", "-sL", "--fail", "-A", "Mozilla/5.0 (ResearchGroupSync)", url],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl failed {r.returncode}: {url}\n{r.stderr}")
    return r.stdout


def parse_cards(html: str) -> list[dict]:
    rows = []
    for m in re.finditer(
        r'<article[^>]*page-card--hwp-person[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE
    ):
        block = m.group(1)
        hm = re.search(
            r'href="/people/([^"/?#]+)"[^>]*>[\s\n]*<h3[^>]*>([^<]+)</h3>',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if not hm:
            continue
        slug = hm.group(1)
        name = re.sub(r"\s+", " ", hm.group(2)).strip()
        aff = ""
        am = re.search(
            r'field--name-field-hwp-person-prof-title[^>]*>.*?<div[^>]*>\s*([^<]+)\s*</div>',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if am:
            aff = re.sub(r"\s+", " ", am.group(1)).strip()
        rows.append({"name": name, "slug": slug, "affiliation": aff})
    return rows


def fetch_listing(url: str) -> list[dict]:
    html = curl_get(url)
    return parse_cards(html)


def fetch_all_pages(filter_param: str | None) -> list[dict]:
    """
    filter_param: None for full list, or the encoded f[0] value e.g.
    hwp_c_vocabulary_175%3A1589
    """
    out: list[dict] = []
    for page in range(0, 32):
        if filter_param is None:
            url = f"{BASE}/people?page={page}" if page else f"{BASE}/people"
        else:
            base_q = f"f%5B0%5D={filter_param}"
            url = f"{BASE}/people?{base_q}&page={page}" if page else f"{BASE}/people?{base_q}"
        batch = fetch_listing(url)
        if not batch:
            break
        out.extend(batch)
    return out


def main() -> int:
    print("Fetching unfiltered people (all pages)…")
    everyone = fetch_all_pages(None)
    by_slug: dict[str, dict] = {}
    for row in everyone:
        by_slug[row["slug"]] = row
    print(f"  Unique: {len(by_slug)}")

    slug_to_cat: dict[str, str] = {}
    for key, label, filt in CATEGORIES:
        print(f"Category: {label}…")
        rows = fetch_all_pages(filt)
        print(f"  … {len(rows)} rows")
        for row in rows:
            slug_to_cat[row["slug"]] = key

    records = []
    for slug in sorted(by_slug.keys(), key=lambda s: (by_slug[s]["name"].split()[-1].lower(), s)):
        row = by_slug[slug]
        cat = slug_to_cat.get(slug, "collaborators")
        records.append(
            {
                "slug": slug,
                "name": row["name"],
                "affiliation": row["affiliation"],
                "research_group_category": cat,
            }
        )

    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {DATA_OUT} ({len(records)} records)")

    for rec in records:
        update_person_md(rec)

    print(f"Updated people stubs: {len(records)}")
    return 0


def update_person_md(rec: dict) -> None:
    slug = rec["slug"]
    name = rec["name"]
    affiliation = rec["affiliation"]
    category_key = rec["research_group_category"]

    d = PEOPLE / slug
    d.mkdir(parents=True, exist_ok=True)
    path = d / "index.md"
    title_esc = name.replace('"', '\\"')
    role_json = json.dumps(affiliation, ensure_ascii=False)
    cat_json = json.dumps(category_key, ensure_ascii=False)
    text = f"""---
title: "{title_esc}"
type: "people"
role: {role_json}
research_group_category: {cat_json}
---

"""
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
