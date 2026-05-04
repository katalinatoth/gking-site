#!/usr/bin/env python3
"""Compare scraped publications.json to Hugo writings/content + talks/content.

Uses the same slugify + duplicate-resolution rules as
_automation/scripts/convert.py. Run from the root of the gking-site
checkout:
  python3 writings/scripts/verify_writings_parity.py

Exit 1 if a JSON entry is missing a matching bundle or index title.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SCRAPED = BASE.parent / "scraped_data" / "publications.json"
PUBS_CONTENT = BASE / "writings" / "content"
TALKS_CONTENT = BASE / "talks" / "content"

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].rstrip("-")


def map_publication_type(pub_type: str) -> str:
    mapping = {
        "article-journal": "article-journal",
        "book": "book",
        "chapter": "chapter",
        "paper-conference": "paper-conference",
        "patent": "patent",
        "speech": "speech",
        "software": "software",
        "working-paper": "manuscript",
        "forthcoming": "article-journal",
        "dataset": "dataset",
        "article-newspaper": "article-newspaper",
        "misc": "article",
        "manuscript": "manuscript",
        "report": "report",
        "article": "article",
        "webpage": "webpage",
    }
    return mapping.get(pub_type, "article")


def norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def index_titles(root: Path) -> dict[str, str]:
    """normalized title -> folder slug"""
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for d in root.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        idx = d / "index.md"
        if not idx.is_file():
            continue
        text = idx.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.M)
        if m:
            out[norm_title(m.group(1))] = d.name
    return out


def main() -> int:
    if not SCRAPED.is_file():
        print(f"Missing {SCRAPED}", file=sys.stderr)
        return 1
    pubs = json.loads(SCRAPED.read_text())
    seen_slugs: set[str] = set()
    expected: list[tuple[str, str, str]] = []  # slug, section, title

    for pub in pubs:
        title = pub.get("title", "Untitled")
        slug = slugify(title)
        if slug in seen_slugs:
            year = pub.get("year", "")
            slug = f"{slug}-{year}" if year else f"{slug}-2"
        if slug in seen_slugs:
            slug = f"{slug}-{len(seen_slugs)}"
        seen_slugs.add(slug)
        pt = map_publication_type(pub.get("publication_type", "article-journal"))
        section = "talk" if pt == "speech" else "publication"
        expected.append((slug, section, title))

    actual_pub = {d.name for d in PUBS_CONTENT.iterdir() if d.is_dir()}
    actual_talk = {d.name for d in TALKS_CONTENT.iterdir() if d.is_dir()}

    missing: list[str] = []
    for slug, section, title in expected:
        pool = actual_talk if section == "talk" else actual_pub
        if slug not in pool:
            missing.append(f"{section}/{slug} ({title[:55]})")

    titles_pub = index_titles(PUBS_CONTENT)
    titles_talk = index_titles(TALKS_CONTENT)
    all_titles = {**titles_pub, **titles_talk}

    title_miss: list[str] = []
    for pub in pubs:
        nt = norm_title(pub.get("title", ""))
        if nt in all_titles:
            continue
        title_miss.append(pub.get("title", "")[:90])

    extra_pub = sorted(actual_pub - {e[0] for e in expected if e[1] == "publication"})
    expected_talk_slugs = {e[0] for e in expected if e[1] == "talk"}
    extra_talk = sorted(actual_talk - expected_talk_slugs)

    print(f"publications.json entries: {len(pubs)}")
    print(f"Missing bundle dirs: {len(missing)}")
    for m in missing:
        print(f"  {m}")
    print(f"Missing title matches: {len(title_miss)}")
    for m in title_miss:
        print(f"  {m}")
    print(f"Extra publication dirs (not from JSON slug list): {extra_pub}")
    print(f"Extra talk dirs: {extra_talk}")

    if missing or title_miss:
        print("\nFAIL", file=sys.stderr)
        return 1
    print("\nOK: publications.json matches Hugo publication + talk bundles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
