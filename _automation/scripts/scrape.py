#!/usr/bin/env python3
"""
Scraper for gking.harvard.edu
Extracts publications, bio, software, and downloads PDFs.

Site uses Harvard Web Publishing (HWP) Drupal theme with these key selectors:
  - .hwp-citation: individual publication entries on index pages
  - .hwp-citations-group: groups of publications by year/status
  - .hwp-biblio--abstract: abstract on individual pages
  - .hwp-biblio--content-area: main content area on individual pages
  - .bibcite-citation / .csl-entry: formatted citation text
  - .hwp-pager: pagination
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://gking.harvard.edu"


def _find_scraped_dir() -> Path:
    """Locate the scraped_data/ folder across common layouts.

    Tries the repo-internal location first, then the sibling-of-repo
    location (the original migration workspace). Falls back to the
    in-repo path so a fresh run creates it there if neither exists.
    """
    repo = Path(__file__).resolve().parents[2]
    for candidate in (repo / "scraped_data", repo.parent / "scraped_data"):
        if candidate.is_dir():
            return candidate
    return repo / "scraped_data"


SCRAPED_DIR = _find_scraped_dir()
FILES_DIR = SCRAPED_DIR / "files"
PAGES_DIR = SCRAPED_DIR / "pages"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (academic site migration tool)"
})

RATE_LIMIT = 0.3


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(RATE_LIMIT)
            resp = SESSION.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            print(f"  Attempt {attempt+1} failed for {url}: {e}")
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def fetch_soup(url):
    resp = fetch(url)
    if resp is None:
        return None
    return BeautifulSoup(resp.text, "lxml")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].rstrip('-')


def clean_text(text):
    """Remove material icon names and excessive whitespace."""
    text = re.sub(r'(picture_as_pdf|add_circle_outline|do_not_disturb_on|description|download_for_offline|chevron_\w+)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---------------------------------------------------------------------------
# Phase 1a: Scrape publications index (47 pages)
# ---------------------------------------------------------------------------

def scrape_publications_index():
    print("=" * 60)
    print("PHASE 1a: Scraping publications index...")
    print("=" * 60)

    publications = []
    seen_urls = set()

    for page_num in range(0, 50):
        url = f"{BASE_URL}/publications?page={page_num}"
        print(f"  Fetching page {page_num}: {url}")
        soup = fetch_soup(url)
        if soup is None:
            print(f"  Failed to fetch page {page_num}, stopping.")
            break

        citations = soup.select(".hwp-citation")
        if not citations:
            print(f"  No citations found on page {page_num}, done.")
            break

        current_group_type = "article-journal"
        for cite in citations:
            group = cite.find_parent(class_="hwp-citations-group")
            if group:
                group_title_el = group.select_one(".hwp-citations-group--title")
                if group_title_el:
                    current_group_type = map_group_title_to_type(group_title_el.get_text(strip=True))

            pub = parse_citation(cite, current_group_type)
            if pub and pub.get("url") and pub["url"] not in seen_urls:
                seen_urls.add(pub["url"])
                publications.append(pub)

        has_next = soup.select_one("a.hwp-pager__item--next, .hwp-pager__item--next a")
        if not has_next:
            print(f"  Last page reached at page {page_num}.")
            break

    print(f"\n  Total unique publications found: {len(publications)}")

    out_path = SCRAPED_DIR / "publications.json"
    with open(out_path, "w") as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {out_path}")
    return publications


def map_group_title_to_type(title):
    title_lower = title.lower().strip()
    if re.match(r'^\d{4}$', title_lower):
        return "article-journal"
    mapping = {
        "working paper": "working-paper",
        "forthcoming": "forthcoming",
        "book": "book",
        "journal article": "article-journal",
        "conference": "paper-conference",
        "patent": "patent",
        "software": "software",
        "presentation": "speech",
        "report": "report",
        "newspaper": "article-newspaper",
        "data": "dataset",
        "web article": "article",
        "miscellaneous": "misc",
        "unpublished": "manuscript",
        "book chapter": "chapter",
        "website": "webpage",
    }
    for key, val in mapping.items():
        if key in title_lower:
            return val
    return "article-journal"


def parse_citation(cite, group_type):
    """Parse a single .hwp-citation element from the publications index."""
    pub = {"publication_type": group_type}

    text_el = cite.select_one(".hwp-citation__text")
    if not text_el:
        return None

    title_link = text_el.select_one("a[href]")
    if title_link:
        pub["title"] = title_link.get_text(strip=True).strip('" ')
        pub["url"] = urljoin(BASE_URL, title_link.get("href", ""))
    else:
        pub["title"] = clean_text(text_el.get_text(strip=True))[:150]
        pub["url"] = ""

    raw = clean_text(text_el.get_text(" ", strip=True))
    pub["raw_citation"] = raw

    year_match = re.search(r'\b(19[7-9]\d|20[0-2]\d)\b', raw)
    pub["year"] = int(year_match.group(1)) if year_match else None

    pub["authors"] = parse_authors_from_citation(raw)

    journal_match = re.search(r'\.\s*(?:In\s+)?([A-Z][^.]+?)(?:,\s*\d|\s*Pp\.|\s*$)', raw)
    pub["journal"] = ""

    abstract_el = cite.select_one(".hwp-citation__full-body")
    pub["abstract"] = abstract_el.get_text(strip=True) if abstract_el else ""

    pub["pdf_url"] = ""
    pub["supplementary_url"] = ""
    pub["publisher_url"] = ""
    pub["links"] = []
    pub["attachments"] = []

    for a in cite.select(".hwp-citation__ctas a[href]"):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()
        full_href = urljoin(BASE_URL, href)

        if href.endswith(".pdf") or "/files/" in href:
            text_clean = re.sub(r'picture_as_pdf', '', text).strip()
            if "supp" in text_clean or "appendix" in text_clean:
                pub["supplementary_url"] = full_href
            elif "paper" in text_clean or "article" in text_clean or not pub["pdf_url"]:
                if not pub["pdf_url"]:
                    pub["pdf_url"] = full_href
                else:
                    pub["attachments"].append({"name": text_clean, "url": full_href})

        if "publisher" in text or "version" in text:
            pub["publisher_url"] = full_href

    return pub


def parse_authors_from_citation(raw):
    """Extract authors from a raw citation string like 'Gary King and John Doe. 2025. \"Title\"'"""
    year_match = re.search(r'\.\s*(19|20)\d{2}\s*\.', raw)
    if year_match:
        author_part = raw[:year_match.start()]
    else:
        quote_match = re.search(r'["""\u201c]', raw)
        if quote_match:
            author_part = raw[:quote_match.start()]
        else:
            author_part = raw[:200]

    author_part = author_part.strip(' ."')
    if not author_part or len(author_part) < 3:
        return []

    authors = re.split(r',\s+(?:and\s+)?|\s+and\s+', author_part)
    authors = [a.strip(' ."') for a in authors if a.strip() and len(a.strip()) > 2]
    authors = [a for a in authors if not re.match(r'^\d{4}$', a)]
    return authors


# ---------------------------------------------------------------------------
# Phase 1b: Scrape individual publication pages
# ---------------------------------------------------------------------------

def scrape_individual_pages(publications):
    print("\n" + "=" * 60)
    print("PHASE 1b: Scraping individual publication pages...")
    print("=" * 60)

    total = len(publications)
    for i, pub in enumerate(publications):
        url = pub.get("url", "")
        if not url or url == BASE_URL or url == BASE_URL + "/":
            continue

        print(f"  [{i+1}/{total}] {pub.get('title', 'untitled')[:60]}...")

        soup = fetch_soup(url)
        if soup is None:
            continue

        page_path = PAGES_DIR / f"{slugify(pub.get('title', 'untitled'))}.html"
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        enrich_publication(pub, soup, url)

    out_path = SCRAPED_DIR / "publications.json"
    with open(out_path, "w") as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)
    print(f"\n  Updated {out_path}")
    return publications


def enrich_publication(pub, soup, page_url):
    """Extract detailed info from an individual publication page."""
    # Abstract
    abstract_el = soup.select_one(".hwp-biblio--abstract")
    if abstract_el:
        text = abstract_el.get_text(strip=True)
        if text.lower().startswith("abstract"):
            text = text[8:].strip()
        if text and (not pub.get("abstract") or len(text) > len(pub.get("abstract", ""))):
            pub["abstract"] = text

    # Full citation from the page
    csl_el = soup.select_one(".csl-entry")
    if csl_el:
        pub["full_citation"] = clean_text(csl_el.get_text(strip=True))

    # Extract journal from citation if available
    citation_text = pub.get("full_citation", pub.get("raw_citation", ""))
    if citation_text:
        # Pattern: "Title." Journal Name, Vol(Issue), Pages.
        # or "Title." Journal Name Pp. X.
        journal_patterns = [
            r'"\s*\.\s*([A-Z][^,.\d]+?)(?:,\s*\d|\s*Pp\.)',
            r'"\s*\.\s*([A-Z][^,.\d]+?)\.\s*$',
        ]
        for pat in journal_patterns:
            m = re.search(pat, citation_text)
            if m:
                journal = m.group(1).strip()
                if len(journal) > 3 and len(journal) < 100:
                    pub["journal"] = journal
                    break

    # Publisher's version and other links from the page
    for a in soup.select(".publication-info__actions a[href], .hwp-biblio--see-also a[href], .hwp-biblio--content-area a[href]"):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()
        full_href = urljoin(page_url, href)

        text_clean = re.sub(r'(picture_as_pdf|description|download_for_offline)', '', text).strip()

        if "publisher" in text_clean or "version" in text_clean:
            pub["publisher_url"] = full_href

        if href.endswith(".pdf") or "/files/" in href:
            if "supp" in text_clean or "appendix" in text_clean:
                if not pub.get("supplementary_url"):
                    pub["supplementary_url"] = full_href
            elif not pub.get("pdf_url"):
                pub["pdf_url"] = full_href

        if "dataverse" in href or "replication" in text_clean:
            if not any(l.get("url") == full_href for l in pub.get("links", [])):
                pub.setdefault("links", []).append({
                    "name": "Replication Data",
                    "url": full_href
                })

    # Attachments
    for a in soup.select(".field--name-hwp-bibcite-file-upload a[href], .file a[href]"):
        href = a.get("href", "")
        if href:
            full_href = urljoin(page_url, href)
            filename = unquote(os.path.basename(urlparse(href).path))
            if not any(att.get("url") == full_href for att in pub.get("attachments", [])):
                pub.setdefault("attachments", []).append({
                    "name": filename,
                    "url": full_href
                })

    # Body content (for pages that have extra description beyond abstract)
    body_el = soup.select_one(".hwp-biblio--body, .field--name-body")
    if body_el:
        body_text = body_el.get_text(strip=True)
        if body_text and body_text != pub.get("abstract", ""):
            pub["body"] = body_text

    # See-also links
    see_also = soup.select(".hwp-biblio--see-also a[href]")
    if see_also:
        pub["see_also"] = [
            {"name": a.get_text(strip=True), "url": urljoin(page_url, a.get("href", ""))}
            for a in see_also
        ]

    # Improve publication type from page clues
    if pub.get("publication_type") == "article-journal":
        pub["publication_type"] = detect_type_from_page(pub, soup, page_url)


def detect_type_from_page(pub, soup, page_url):
    """Detect publication type from URL patterns, page content, and citation text."""
    url_lower = page_url.lower()

    if "/presentations/" in url_lower or "/presentation/" in url_lower:
        return "speech"
    if "/software/" in url_lower:
        return "software"

    citation = pub.get("full_citation", pub.get("raw_citation", "")).lower()
    title = pub.get("title", "").lower()

    type_signals = {
        "patent": ["patent"],
        "book": ["princeton university press", "cambridge university press",
                  "oxford university press", "university of michigan press",
                  "university press", "ed. ", "eds. "],
        "chapter": ["in ", "chapter in"],
        "speech": ["talk at", "presentation at", "lecture at", "(talk at"],
        "software": ["software", "r package", "program for"],
        "article-newspaper": ["new york times", "washington post", "wall street journal",
                              "the guardian", "the crimson"],
        "dataset": ["data for", "dataset", "replication data"],
    }

    for pub_type, signals in type_signals.items():
        for signal in signals:
            if signal in citation or signal in title:
                return pub_type

    # Check if it has slides (usually a presentation)
    for a in soup.select("a[href]"):
        text = a.get_text(strip=True).lower()
        if "slides" in text:
            return "speech"

    return "article-journal"


# ---------------------------------------------------------------------------
# Phase 1c: Scrape standalone pages
# ---------------------------------------------------------------------------

def scrape_bio():
    print("\n" + "=" * 60)
    print("PHASE 1c-1: Scraping bio page...")
    print("=" * 60)

    soup = fetch_soup(f"{BASE_URL}/biocv")
    if soup is None:
        return {}

    content = soup.select_one(".hwp-biblio--content-area, .layout-content, .region-content")

    bio = {
        "title": "Gary King's Bio",
        "content_html": str(content) if content else "",
        "content_text": content.get_text("\n", strip=True) if content else "",
    }

    for a in (soup.select("a[href]") if soup else []):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()
        if "cv" in text or "vitae" in href:
            bio["cv_url"] = urljoin(BASE_URL, href)
            break

    page_path = PAGES_DIR / "biocv.html"
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    out_path = SCRAPED_DIR / "bio.json"
    with open(out_path, "w") as f:
        json.dump(bio, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {out_path}")
    return bio


def scrape_home():
    print("\n" + "=" * 60)
    print("PHASE 1c-2: Scraping home page...")
    print("=" * 60)

    soup = fetch_soup(BASE_URL)
    if soup is None:
        return {}

    page_path = PAGES_DIR / "home.html"
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    home = {"sections": []}
    content = soup.select_one(".layout-content, main")
    if content:
        for heading in content.select("h2"):
            text = heading.get_text(strip=True)
            content_parts = []
            sibling = heading.find_next_sibling()
            while sibling and sibling.name not in ["h2"]:
                content_parts.append(str(sibling))
                sibling = sibling.find_next_sibling()

            home["sections"].append({
                "heading": text,
                "content_html": "\n".join(content_parts),
                "content_text": BeautifulSoup("\n".join(content_parts), "lxml").get_text("\n", strip=True),
            })

    out_path = SCRAPED_DIR / "home.json"
    with open(out_path, "w") as f:
        json.dump(home, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {out_path}")
    return home


def scrape_software():
    print("\n" + "=" * 60)
    print("PHASE 1c-3: Scraping software page...")
    print("=" * 60)

    soup = fetch_soup(f"{BASE_URL}/software")
    if soup is None:
        return []

    page_path = PAGES_DIR / "software.html"
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    software = []
    seen = set()

    for cite in soup.select(".hwp-citation"):
        sw = {}
        text_el = cite.select_one(".hwp-citation__text")
        if not text_el:
            continue

        title_link = text_el.select_one("a[href]")
        if title_link:
            sw["title"] = title_link.get_text(strip=True).strip('" ')
            sw["url"] = urljoin(BASE_URL, title_link.get("href", ""))
        else:
            continue

        if sw["url"] in seen:
            continue
        seen.add(sw["url"])

        raw = clean_text(text_el.get_text(" ", strip=True))
        sw["raw_citation"] = raw
        sw["authors"] = parse_authors_from_citation(raw)

        year_match = re.search(r'\b(19[7-9]\d|20[0-2]\d)\b', raw)
        sw["year"] = int(year_match.group(1)) if year_match else None

        abstract_el = cite.select_one(".hwp-citation__full-body")
        sw["abstract"] = abstract_el.get_text(strip=True) if abstract_el else ""

        software.append(sw)

    out_path = SCRAPED_DIR / "software.json"
    with open(out_path, "w") as f:
        json.dump(software, f, indent=2, ensure_ascii=False)
    print(f"  Found {len(software)} software entries. Saved to {out_path}")
    return software


# ---------------------------------------------------------------------------
# Phase 1d: Download PDFs
# ---------------------------------------------------------------------------

def download_pdfs(publications):
    print("\n" + "=" * 60)
    print("PHASE 1d: Downloading PDFs...")
    print("=" * 60)

    pdf_mapping = {}
    downloaded = 0
    skipped = 0
    failed = 0

    all_urls = set()
    for pub in publications:
        for key in ["pdf_url", "supplementary_url"]:
            if pub.get(key):
                all_urls.add(pub[key])
        for att in pub.get("attachments", []):
            if att.get("url"):
                all_urls.add(att["url"])

    print(f"  Found {len(all_urls)} unique file URLs to download")

    for url in sorted(all_urls):
        parsed = urlparse(url)
        original_name = unquote(os.path.basename(parsed.path))
        if not original_name or '.' not in original_name:
            continue

        local_name = re.sub(r'[^\w.\-]', '_', original_name)
        local_path = FILES_DIR / local_name

        if local_path.exists():
            skipped += 1
            pdf_mapping[url] = f"/files/{local_name}"
            continue

        print(f"  [{downloaded + skipped + failed + 1}/{len(all_urls)}] {original_name[:60]}...")
        resp = fetch(url)
        if resp and resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            pdf_mapping[url] = f"/files/{local_name}"
            downloaded += 1
        else:
            print(f"    FAILED: {url}")
            failed += 1

    mapping_path = SCRAPED_DIR / "pdf_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(pdf_mapping, f, indent=2)

    print(f"\n  Downloaded: {downloaded}, Skipped (exists): {skipped}, Failed: {failed}")
    print(f"  Mapping saved to {mapping_path}")
    return pdf_mapping


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(SCRAPED_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(PAGES_DIR, exist_ok=True)

    phases = sys.argv[1:] if len(sys.argv) > 1 else ["all"]

    if "index" in phases or "all" in phases:
        pubs = scrape_publications_index()
    else:
        pub_path = SCRAPED_DIR / "publications.json"
        if pub_path.exists():
            with open(pub_path) as f:
                pubs = json.load(f)
        else:
            pubs = []

    if "individual" in phases or "all" in phases:
        pubs = scrape_individual_pages(pubs)

    if "bio" in phases or "other" in phases or "all" in phases:
        scrape_bio()

    if "home" in phases or "other" in phases or "all" in phases:
        scrape_home()

    if "software" in phases or "other" in phases or "all" in phases:
        scrape_software()

    if "pdfs" in phases or "all" in phases:
        download_pdfs(pubs)

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
