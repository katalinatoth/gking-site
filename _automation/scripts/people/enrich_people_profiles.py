#!/usr/bin/env python3
"""
Fetch https://gking.harvard.edu/people/<slug> for each member and set:
  - front matter: email, website (+ label), avatar (optional)
  - markdown body: bio text from field-hwp-body (falls back to generic one-liner)

Website and email are read from .hwp-person-card (same as the original site).

Requires: beautifulsoup4, curl on PATH.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "EditMe" / "People" / "Data" / "research_group.json"
PEOPLE = ROOT / "EditMe" / "People" / "Profiles"
BASE = "https://gking.harvard.edu"


def curl_get(url: str) -> str:
    r = subprocess.run(
        ["curl", "-sL", "--fail", "-A", "Mozilla/5.0 (PeopleProfileEnricher)", url],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl {r.returncode}: {url}")
    return r.stdout


def parse_profile(html: str) -> dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup

    card = soup.select_one(".hwp-person-card")

    email = ""
    website = ""
    website_label = "Website"
    if card:
        for a in card.find_all("a", href=True):
            h = a.get("href", "").strip()
            if h.startswith("mailto:"):
                if not email:
                    email = h.split(":", 1)[1].strip()
            elif h.startswith(("http://", "https://")):
                if not website:
                    website = h
                    website_label = (a.get_text(strip=True) or "Website")[:80]
            elif h.startswith("//"):
                if not website:
                    website = "https:" + h
                    website_label = (a.get_text(strip=True) or "Website")[:80]
            elif h.startswith("/") and not h.startswith("//"):
                if not website:
                    website = urljoin(BASE, h)
                    website_label = (a.get_text(strip=True) or "Website")[:80]
    if not email:
        for a in main.find_all("a", href=True):
            if a["href"].startswith("mailto:"):
                email = a["href"].split(":", 1)[1].strip()
                break

    bio = ""
    body_el = soup.select_one(".field--name-field-hwp-body")
    if body_el:
        parts = [p.get_text(" ", strip=True) for p in body_el.find_all("p")]
        if parts:
            bio = "\n\n".join(parts)
        else:
            # Lists, divs, or plain text nodes
            bio = body_el.get_text("\n", strip=True)
            bio = re.sub(r"\n{3,}", "\n\n", bio).strip()

    avatar = ""
    if card:
        im = card.find("img", src=True)
        if im:
            src = im["src"].strip()
            if src and "header-logo" not in src and "footer-logo" not in src and "svg" not in src.lower():
                avatar = urljoin(BASE, src)

    prof_title = ""
    pt = soup.select_one(".hwp-page-title .field--name-field-hwp-person-prof-title div")
    if not pt:
        pt = soup.select_one(".field--name-field-hwp-person-prof-title div")
    if pt:
        prof_title = pt.get_text(" ", strip=True)

    return {
        "email": email,
        "website": website,
        "website_label": website_label,
        "bio": bio,
        "avatar": avatar,
        "prof_title": prof_title,
    }


def write_person_md(
    path: Path,
    *,
    title: str,
    role: str,
    category: str,
    email: str,
    website: str,
    website_label: str,
    avatar: str,
    body: str,
) -> None:
    lines = [
        "---",
        f'title: {json.dumps(title)}',
        'type: "people"',
        f"role: {json.dumps(role)}",
        f"research_group_category: {json.dumps(category)}",
    ]
    if email:
        lines.append(f"email: {json.dumps(email)}")
    if website:
        lines.append(f"website: {json.dumps(website)}")
        if website_label and website_label != "Website":
            lines.append(f"website_label: {json.dumps(website_label)}")
    if avatar:
        lines.append(f"avatar: {json.dumps(avatar)}")
    lines.append("---")
    lines.append("")
    lines.append(body if body.strip() else "")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        from bs4 import BeautifulSoup  # noqa: F401
    except ImportError:
        print("Install: pip install beautifulsoup4", file=sys.stderr)
        return 1

    rows = json.loads(DATA.read_text(encoding="utf-8"))
    ok = fail = 0
    for i, row in enumerate(rows):
        slug = row["slug"]
        url = f"{BASE}/people/{slug}"
        try:
            html = curl_get(url)
            parsed = parse_profile(html)
        except Exception as e:
            print(f"FAIL {slug}: {e}")
            fail += 1
            continue

        path = PEOPLE / slug / "index.md"
        if not path.exists():
            print(f"SKIP missing: {slug}")
            fail += 1
            continue

        role = (row.get("affiliation") or "").strip() or (parsed.get("prof_title") or "").strip()
        body = parsed["bio"] if parsed["bio"] else ""
        write_person_md(
            path,
            title=row["name"],
            role=role,
            category=row["research_group_category"],
            email=parsed["email"],
            website=parsed.get("website") or "",
            website_label=parsed.get("website_label") or "Website",
            avatar=parsed["avatar"],
            body=body,
        )
        ok += 1
        if (i + 1) % 30 == 0:
            print(f"  … {i + 1}/{len(rows)}")
        time.sleep(0.18)

    print(f"Done. Updated {ok}, failed {fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
