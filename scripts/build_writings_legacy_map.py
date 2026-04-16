#!/usr/bin/env python3
"""Build hugo-site/data/writings_legacy_map.json from scraped Drupal HTML + publications.json.

Each bundle folder gets legacy tab ids matching gking.harvard.edu Writings filters:
  journal, presentation, patent, software, other

Run after updating scraped_data:  python3 hugo-site/scripts/build_writings_legacy_map.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRAPED = BASE.parent / "scraped_data"
PAGES = SCRAPED / "pages"
PUBS_JSON = SCRAPED / "publications.json"
OUT = BASE / "data" / "writings_legacy_map.json"
CONTENT = BASE / "content"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].rstrip("-")


def norm_title(t: str) -> str:
    t = (t or "").strip()
    for a, b in [
        ("\u2019", "'"),
        ("\u2018", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
        ("\u2013", "-"),
        ("\u2014", "-"),
    ]:
        t = t.replace(a, b)
    t = re.sub(r"\s+", " ", t)
    return t.lower()


# When HTML/GTM has no row, map scraped JSON publication_type -> Drupal bibcite type names
PUB_TYPE_TO_DRUPAL = {
    "article-journal": "journal_article",
    "speech": "presentation",
    "software": "software",
    "chapter": "book_chapter",
    "book": "book",
    "working-paper": "working_paper",
    "dataset": "data",
    "forthcoming": "journal_article",
    "paper-conference": "conference_paper",
    "patent": "patent",
    "article-newspaper": "newspaper_article",
    "misc": "miscellaneous",
    "manuscript": "unpublished",
    "report": "report",
    "article": "miscellaneous",
    "webpage": "website",
}


def drupal_to_tab(ct: str) -> str:
    if ct == "journal_article":
        return "journal"
    if ct == "presentation":
        return "presentation"
    if ct == "patent":
        return "patent"
    if ct == "software":
        return "software"
    return "other"


def extract_gtm_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Return (title_norm -> drupal content_type, html_stem -> drupal content_type).

    Only includes Gary King site pages (excludes stray mirrors without GTM).
    """
    by_title: dict[str, str] = {}
    by_stem: dict[str, str] = {}
    if not PAGES.is_dir():
        return by_title, by_stem
    for p in PAGES.glob("*.html"):
        text = p.read_text(encoding="utf-8", errors="replace")
        pos = 0
        while True:
            i = text.find("dataLayer.push(", pos)
            if i == -1:
                break
            brace = text.find("{", i)
            if brace == -1:
                break
            try:
                obj, end = json.JSONDecoder().raw_decode(text, brace)
            except json.JSONDecodeError:
                pos = i + 1
                continue
            pos = brace + end
            if obj.get("entityType") != "bibcite_reference":
                continue
            if obj.get("siteName") != "GARY KING":
                continue
            ct = obj.get("content_type")
            title = obj.get("content_title")
            if not ct or not title:
                continue
            nt = norm_title(title)
            by_title[nt] = ct
            by_stem[p.stem] = ct
    return by_title, by_stem


def yaml_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    fm = text[3:end]
    m = re.search(r"^title:\s*(.+)$", fm, re.M)
    if not m:
        return ""
    raw = m.group(1).strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"')
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    return raw


def hugo_publication_types(slug: str) -> list[str]:
    """Read publication_types from the Hugo bundle front matter (if present)."""
    out: list[str] = []
    for section in ("publication", "talk"):
        p = CONTENT / section / slug / "index.md"
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            return out
        end = text.find("\n---", 3)
        if end == -1:
            return out
        fm = text[3:end]
        m = re.search(r"^publication_types:\s*\n((?:\s*-\s*.+\n)+)", fm, re.M)
        if m:
            for line in m.group(1).strip().split("\n"):
                mm = re.match(r'\s*-\s*"(.+)"', line.strip())
                if mm:
                    out.append(mm.group(1))
        else:
            m2 = re.search(r"publication_types:\s*\[(.*?)\]", fm, re.S)
            if m2:
                out.extend(re.findall(r'"([^"]+)"', m2.group(1)))
        return out
    return out


# Hugo Blox / CSL types in front matter -> Drupal bibcite type names (for tab mapping).
HUGO_CSL_TO_DRUPAL: dict[str, str] = {
    "patent": "patent",
    "software": "software",
    "speech": "presentation",
    "presentation": "presentation",
    "journal_article": "journal_article",
    "article-journal": "journal_article",
    "book": "book",
    "chapter": "book_chapter",
    "book_chapter": "book_chapter",
    "manuscript": "working_paper",
    "dataset": "data",
    "miscellaneous": "miscellaneous",
    "article": "miscellaneous",
    "report": "report",
    "unpublished": "unpublished",
    "newspaper_article": "newspaper_article",
    "article-newspaper": "newspaper_article",
    "webpage": "website",
    "website": "website",
    "paper-conference": "conference_paper",
    "conference_paper": "conference_paper",
    "conference_proceedings": "conference_proceedings",
}


def hugo_override_types(slug: str) -> str | None:
    """Map Hugo CSL types to Drupal bibcite names when GTM is missing."""
    types = hugo_publication_types(slug)
    for t in types:
        if t in HUGO_CSL_TO_DRUPAL:
            return HUGO_CSL_TO_DRUPAL[t]
    return None


def strip_year_suffix(slug: str) -> str:
    return re.sub(r"-(19|20)\d{2}(-\d+)?$", "", slug)


def resolve_slug_exact(slug: str, by_stem: dict[str, str]) -> str | None:
    if slug in by_stem:
        return by_stem[slug]
    s2 = strip_year_suffix(slug)
    if s2 != slug and s2 in by_stem:
        return by_stem[s2]
    return None


def main() -> int:
    by_title, by_stem = extract_gtm_maps()
    if not PUBS_JSON.is_file():
        print(f"Missing {PUBS_JSON}", file=sys.stderr)
        return 1
    pubs = json.loads(PUBS_JSON.read_text())
    seen_slugs: set[str] = set()

    # Expected slug -> (drupal_type, tab) from canonical import list
    from_json: dict[str, tuple[str, str]] = {}
    for pub in pubs:
        title = pub.get("title", "Untitled")
        slug = slugify(title)
        if slug in seen_slugs:
            year = pub.get("year", "")
            slug = f"{slug}-{year}" if year else f"{slug}-2"
        if slug in seen_slugs:
            slug = f"{slug}-{len(seen_slugs)}"
        seen_slugs.add(slug)

        nt = norm_title(title)
        raw_pt = pub.get("publication_type", "article-journal")
        ct = by_title.get(nt)
        if ct is None:
            ct = resolve_slug_exact(slug, by_stem)
        if ct is None:
            ct = hugo_override_types(slug)
        if ct is None and raw_pt == "software":
            ct = "software"
        if ct is None:
            ct = PUB_TYPE_TO_DRUPAL.get(raw_pt, "miscellaneous")
        tab = drupal_to_tab(ct)
        from_json[slug] = (ct, tab)

    entries: dict[str, dict[str, str]] = {}
    for slug, (ct, tab) in from_json.items():
        entries[slug] = {"tab": tab, "drupal": ct}

    # Merge any HTML stems not in JSON (rare)
    for stem, ct in by_stem.items():
        if stem in entries:
            continue
        tab = drupal_to_tab(ct)
        entries[stem] = {"tab": tab, "drupal": ct}

    # Ensure every Hugo bundle is present
    missing: list[str] = []
    for section in ("publication", "talk"):
        root = CONTENT / section
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            slug = d.name
            if slug in entries:
                continue
            ct = resolve_slug_exact(slug, by_stem)
            title = yaml_title(d / "index.md")
            if ct is None and title:
                ct = by_title.get(norm_title(title))
            if ct is None:
                ct = hugo_override_types(slug)
            if ct is None and section == "talk":
                ct = "presentation"
            elif ct is None:
                ct = "miscellaneous"
            tab = drupal_to_tab(ct)
            entries[slug] = {"tab": tab, "drupal": ct}
            missing.append(slug)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"entries": entries}, indent=0) + "\n", encoding="utf-8")

    # Summary
    from collections import Counter

    c = Counter(e["tab"] for e in entries.values())
    print(f"Wrote {OUT} ({len(entries)} slugs)")
    print("Tab counts:", dict(c))
    if missing:
        print(f"Filled {len(missing)} bundles not in publications.json (slug/title/stem fallback).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
