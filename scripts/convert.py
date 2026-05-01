#!/usr/bin/env python3
"""
Convert scraped data from gking.harvard.edu into Hugo content files
for the Hugo Blox academic theme.

One-time migration script kept for reference. The scraped_data/
folder it consumes (~1 GB of crawled HTML, JSON, and PDFs) is not
committed to the repo; copy it next to the gking-site checkout
or pass an explicit path if you ever need to re-run this.
"""

import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote

HUGO_DIR = Path(__file__).resolve().parents[1]  # the gking-site checkout root


def _find_scraped_dir() -> Path:
    """Locate the scraped_data/ folder across common layouts.

    Tries (in order):
      * <repo>/scraped_data/         — copied into the checkout
      * <repo>/../scraped_data/      — sibling of the checkout (the
                                       layout used during the original
                                       migration)
    Returns the in-repo candidate as a fallback so error messages
    point somewhere predictable.
    """
    candidates = [
        HUGO_DIR / "scraped_data",
        HUGO_DIR.parent / "scraped_data",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


SCRAPED_DIR = _find_scraped_dir()
CONTENT_DIR = HUGO_DIR / "content"
STATIC_DIR = HUGO_DIR / "static"


def load_json(filename):
    path = SCRAPED_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].rstrip('-')


def yaml_string(s):
    """Escape a string for YAML front matter."""
    if not s:
        return '""'
    escaped = s.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def map_publication_type(pub_type):
    """Map our scraped types to Hugo Blox CSL types."""
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


def local_pdf_path(url, pdf_mapping):
    """Get local path for a PDF URL using the mapping."""
    if not url:
        return ""
    if url in pdf_mapping:
        return pdf_mapping[url]
    parsed = urlparse(url)
    original_name = unquote(os.path.basename(parsed.path))
    local_name = re.sub(r'[^\w.\-]', '_', original_name)
    return f"/files/{local_name}"


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

def convert_publications(pdf_mapping):
    print("Converting publications...")
    pubs = load_json("publications.json")
    if not pubs:
        print("  No publications found!")
        return

    seen_slugs = set()
    talks_count = 0
    pubs_count = 0

    for pub in pubs:
        title = pub.get("title", "Untitled")
        slug = slugify(title)

        if slug in seen_slugs:
            year = pub.get("year", "")
            slug = f"{slug}-{year}" if year else f"{slug}-2"
        if slug in seen_slugs:
            slug = f"{slug}-{len(seen_slugs)}"
        seen_slugs.add(slug)

        pub_type = map_publication_type(pub.get("publication_type", "article-journal"))

        if pub_type == "speech":
            section = "talk"
            talks_count += 1
        else:
            section = "publication"
            pubs_count += 1

        pub_dir = CONTENT_DIR / section / slug
        os.makedirs(pub_dir, exist_ok=True)

        year = pub.get("year", 2025)
        date = f"{year}-01-01" if year else "2025-01-01"

        pdf_local = local_pdf_path(pub.get("pdf_url", ""), pdf_mapping)
        supp_local = local_pdf_path(pub.get("supplementary_url", ""), pdf_mapping)

        authors = pub.get("authors", [])
        if not authors:
            authors = ["Gary King"]

        lines = ["---"]
        lines.append(f"title: {yaml_string(title)}")
        lines.append(f"date: {yaml_string(date)}")

        lines.append("authors:")
        for author in authors:
            lines.append(f"  - {yaml_string(author)}")

        lines.append("publication_types:")
        lines.append(f'  - "{pub_type}"')

        if pub.get("journal"):
            lines.append(f"publication: {yaml_string(pub['journal'])}")

        abstract = pub.get("abstract", "")
        if abstract:
            lines.append(f"abstract: {yaml_string(abstract.replace(chr(10), ' '))}")

        all_links = []

        if pdf_local:
            all_links.append({"type": "pdf", "url": pdf_local})
        elif pub.get("pdf_url"):
            all_links.append({"type": "pdf", "url": pub["pdf_url"]})

        if pub.get("publisher_url"):
            all_links.append({"type": "source", "url": pub["publisher_url"]})

        if supp_local:
            all_links.append({"name": "Supplementary Material", "url": supp_local})
        elif pub.get("supplementary_url"):
            all_links.append({"name": "Supplementary Material", "url": pub["supplementary_url"]})

        for link in pub.get("links", []):
            if link.get("url"):
                all_links.append({"name": link.get("name", "Link"), "url": link["url"]})

        if all_links:
            lines.append("links:")
            for link in all_links:
                if link.get("type"):
                    lines.append(f"  - type: {link['type']}")
                else:
                    lines.append(f"  - name: {yaml_string(link['name'])}")
                lines.append(f"    url: {yaml_string(link['url'])}")

        lines.append("---")
        lines.append("")

        body = pub.get("body", "")
        if body:
            lines.append(body)

        content = "\n".join(lines)
        index_path = pub_dir / "index.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"  Created {pubs_count} publications and {talks_count} talks")


# ---------------------------------------------------------------------------
# Software
# ---------------------------------------------------------------------------

def convert_software():
    print("Converting software projects...")
    software = load_json("software.json")
    if not software:
        print("  No software entries found!")
        return

    seen_slugs = set()
    count = 0

    for sw in software:
        title = sw.get("title", "Untitled")
        slug = slugify(title)
        if slug in seen_slugs:
            slug = f"{slug}-2"
        seen_slugs.add(slug)

        sw_dir = CONTENT_DIR / "software" / slug
        os.makedirs(sw_dir, exist_ok=True)

        year = sw.get("year", 2020)
        date = f"{year}-01-01" if year else "2020-01-01"

        authors = sw.get("authors", [])
        if not authors:
            authors = ["Gary King"]

        lines = ["---"]
        lines.append(f"title: {yaml_string(title)}")
        lines.append(f"date: {yaml_string(date)}")

        lines.append("authors:")
        for author in authors:
            lines.append(f"  - {yaml_string(author)}")

        if sw.get("url"):
            lines.append("links:")
            lines.append("  - type: site")
            lines.append(f"    url: {yaml_string(sw['url'])}")

        abstract = sw.get("abstract", "")
        if abstract:
            lines.append(f"summary: {yaml_string(abstract.replace(chr(10), ' '))}")

        lines.append("---")
        lines.append("")

        if sw.get("abstract"):
            lines.append(sw["abstract"])

        content = "\n".join(lines)
        with open(sw_dir / "index.md", "w", encoding="utf-8") as f:
            f.write(content)
        count += 1

    print(f"  Created {count} software entries")


# ---------------------------------------------------------------------------
# Bio page
# ---------------------------------------------------------------------------

def convert_bio():
    print("Converting bio page...")
    bio = load_json("bio.json")
    if not bio:
        print("  No bio data found!")
        return

    bio_dir = CONTENT_DIR / "bio"
    os.makedirs(bio_dir, exist_ok=True)

    lines = ["---"]
    lines.append('title: "Gary King"')
    lines.append('type: "page"')
    lines.append('---')
    lines.append('')

    text = bio.get("content_text", "")
    if text:
        paragraphs = text.split("\n")
        for p in paragraphs:
            p = p.strip()
            if p:
                lines.append(p)
                lines.append("")

    content = "\n".join(lines)
    with open(bio_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("  Created bio page")


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

def convert_home(pdf_mapping):
    print("Converting home page...")
    home = load_json("home.json")
    bio = load_json("bio.json")

    os.makedirs(CONTENT_DIR, exist_ok=True)

    bio_text = ""
    if bio:
        full = bio.get("content_text", "")
        first_para = full.split("\n")[0] if full else ""
        bio_text = first_para

    lines = ['---']
    lines.append('title: "Gary King"')
    lines.append('type: landing')
    lines.append('')
    lines.append('sections:')

    # Hero / bio section
    lines.append('  - block: hero')
    lines.append('    content:')
    lines.append('      title: "Gary King"')
    lines.append(f'      text: {yaml_string(bio_text)}')
    lines.append('      primary_action:')
    lines.append('        text: Bio & CV')
    lines.append('        url: /bio/')
    lines.append('')

    # Recent publications
    lines.append('  - block: collection')
    lines.append('    content:')
    lines.append('      title: Recent Publications')
    lines.append('      count: 10')
    lines.append('      filters:')
    lines.append('        folders:')
    lines.append('          - publication')
    lines.append('    design:')
    lines.append('      view: citation')

    # Recent talks
    lines.append('  - block: collection')
    lines.append('    content:')
    lines.append('      title: Recent Presentations')
    lines.append('      count: 5')
    lines.append('      filters:')
    lines.append('        folders:')
    lines.append('          - talk')
    lines.append('    design:')
    lines.append('      view: date-title-summary')

    # Software
    lines.append('  - block: collection')
    lines.append('    content:')
    lines.append('      title: Software')
    lines.append('      count: 10')
    lines.append('      filters:')
    lines.append('        folders:')
    lines.append('          - software')
    lines.append('    design:')
    lines.append('      view: card')

    lines.append('---')

    content = "\n".join(lines)
    with open(CONTENT_DIR / "_index.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("  Created home page")


# ---------------------------------------------------------------------------
# Copy PDFs to static directory
# ---------------------------------------------------------------------------

def copy_pdfs():
    print("Copying PDFs to Hugo static directory...")
    src_dir = SCRAPED_DIR / "files"
    dst_dir = STATIC_DIR / "files"
    os.makedirs(dst_dir, exist_ok=True)

    count = 0
    for f in src_dir.iterdir():
        if f.is_file():
            dst = dst_dir / f.name
            if not dst.exists():
                shutil.copy2(f, dst)
            count += 1

    print(f"  Copied {count} files to static/files/")


# ---------------------------------------------------------------------------
# Create author page for Gary King
# ---------------------------------------------------------------------------

def create_author_page():
    print("Creating author page...")
    author_dir = CONTENT_DIR / "authors" / "gary-king"
    os.makedirs(author_dir, exist_ok=True)

    bio = load_json("bio.json")
    bio_text = bio.get("content_text", "") if bio else ""
    first_para = bio_text.split("\n")[0] if bio_text else ""

    lines = ["---"]
    lines.append('title: "Gary King"')
    lines.append('role: "Weatherhead University Professor"')
    lines.append("organizations:")
    lines.append("  - name: Harvard University")
    lines.append("    url: https://www.harvard.edu/")
    lines.append(f'bio: {yaml_string(first_para[:200])}')
    lines.append("social:")
    lines.append("  - icon: globe")
    lines.append("    icon_pack: fas")
    lines.append("    link: https://gking.harvard.edu/")
    lines.append("superuser: true")
    lines.append("---")
    lines.append("")
    lines.append(first_para)

    content = "\n".join(lines)
    with open(author_dir / "_index.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("  Created Gary King author page")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pdf_mapping = load_json("pdf_mapping.json")
    if isinstance(pdf_mapping, list):
        pdf_mapping = {}

    convert_publications(pdf_mapping)
    convert_software()
    convert_bio()
    convert_home(pdf_mapping)
    copy_pdfs()
    create_author_page()

    print("\n" + "=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
