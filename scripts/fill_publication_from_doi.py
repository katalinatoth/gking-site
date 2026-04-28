#!/usr/bin/env python3
"""
Set `publication:` from Crossref metadata using the first suitable DOI in
front matter (links, abstract; Dataverse DOIs are skipped). Only journal and
proceedings articles with a container title and at least volume, issue, or
pages in Crossref are updated.

Usage (from hugo-site/):
  python3 scripts/fill_publication_from_doi.py
  python3 scripts/fill_publication_from_doi.py --apply
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import certifi

    def _ssl_context() -> ssl.SSLContext:
        return ssl.create_default_context(cafile=certifi.where())
except ImportError:
    def _ssl_context() -> ssl.SSLContext:
        return ssl.create_default_context()

try:
    import yaml
except ImportError as e:
    print("Install PyYAML: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1) from e

try:
    import fitz  # PyMuPDF, optional: PDF DOI extraction.
except ImportError:
    fitz = None  # type: ignore[assignment]

DOI_IN_TEXT = re.compile(
    r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)
CROSSREF_SKIPPED_PREFIXES = (
    "10.7910/",
    "10.5281/",
    "10.3886/",
    "10.17605/",
)


def clean_doi(d: str) -> str:
    d = d.rstrip(").,;]}\"'")
    d = d.split("?", 1)[0]
    for suf in ("/full", "/html", "/abstract", "/v1", "/v2", "/version"):
        if d.lower().endswith(suf):
            d = d[: -len(suf)]
    return d


def collect_pdf_path(fm: dict[str, Any], static_files: Path) -> Path | None:
    """Return the local PDF in static/files/ that the front-matter links to, if any."""
    links = fm.get("links")
    if not isinstance(links, list):
        return None
    for item in links:
        if not isinstance(item, dict):
            continue
        t = (item.get("type") or "").lower()
        u = item.get("url") or ""
        if t == "pdf" and isinstance(u, str) and u.startswith("files/"):
            cand = static_files / u[len("files/") :]
            if cand.is_file():
                return cand
    return None


def dois_in_pdf(pdf: Path, max_pages: int = 3) -> list[str]:
    """Extract DOIs from the first few pages of a PDF.

    Most journals print the canonical DOI in the masthead/footer of the
    first 1-2 pages. Scanning the first three pages catches outliers
    (long mastheads, papers that print the DOI on page 2) without
    pulling in DOIs that the article merely cites.
    """
    if fitz is None:
        return []
    found: set[str] = set()
    try:
        doc = fitz.open(pdf)
    except Exception:
        return []
    try:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            text = page.get_text() or ""
            for m in DOI_IN_TEXT.finditer(text):
                found.add(clean_doi(m.group(0)))
    finally:
        doc.close()
    return sorted(found)


def collect_dois(fm: dict[str, Any]) -> list[str]:
    found: set[str] = set()
    dv = fm.get("dataverse_url")
    if isinstance(dv, str):
        for d in DOI_IN_TEXT.findall(dv):
            found.add(clean_doi(d))
    links = fm.get("links")
    if isinstance(links, list):
        for item in links:
            if not isinstance(item, dict):
                continue
            u = item.get("url", "")
            if isinstance(u, str):
                for d in DOI_IN_TEXT.findall(u):
                    found.add(clean_doi(d))
    for key in ("doi", "publication_doi", "citation_doi"):
        v = fm.get(key)
        if isinstance(v, str):
            for d in DOI_IN_TEXT.findall(v):
                found.add(clean_doi(d))
    abs_ = fm.get("abstract")
    if isinstance(abs_, str):
        for d in DOI_IN_TEXT.findall(abs_):
            found.add(clean_doi(d))
    hb = fm.get("hugoblox")
    if isinstance(hb, dict):
        ids_ = hb.get("ids")
        if isinstance(ids_, dict):
            d = ids_.get("doi")
            if isinstance(d, str) and d.strip():
                found.add(clean_doi(d.strip()))
    return sorted(
        found,
        key=lambda x: (x.lower().startswith("10.7910"), -len(x)),
    )


def first_crossref_doi(dois: list[str]) -> str | None:
    preferred: list[str] = []
    fallback: list[str] = []
    for d in dois:
        if any(d.startswith(p) for p in CROSSREF_SKIPPED_PREFIXES):
            continue
        tail = d.split("/", 1)[-1] if "/" in d else d
        if re.match(r"^978-?\d", tail) or d.startswith("10.3389/978"):
            fallback.append(d)
        else:
            preferred.append(d)
    for d in preferred + fallback:
        return d
    return None


def crossref_fetch(doi: str) -> tuple[dict[str, Any] | None, str | None]:
    enc = urllib.parse.quote(doi)
    url = f"https://api.crossref.org/works/{enc}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gking-site-pubfill/1.0 (https://github.com/KatalinaToth/gking-site)",
        },
    )
    try:
        with urllib.request.urlopen(
            req, timeout=45, context=_ssl_context()
        ) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        return (None, str(e)[:400])
    if not isinstance(data, dict) or "message" not in data:
        return (None, "invalid response")
    return (data["message"], None)


def _normalize_title(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s.lower())).strip()


def crossref_search_by_title(
    title: str, authors: list[str], year: str | None
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """Search Crossref by title+author; return (doi, message, error).

    Accepts a candidate only if its normalized title equals the query
    title and at least one author surname appears in the candidate's
    author list. This is the fallback path for papers whose PDF prints
    no DOI string (older BMC and similar journals)."""
    if not title:
        return (None, None, "no title")
    surnames = [a.split()[-1] for a in authors if a]
    params = {
        "query.title": title,
        "rows": "5",
    }
    if surnames:
        params["query.author"] = " ".join(surnames)
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gking-site-pubfill/1.0 (https://github.com/KatalinaToth/gking-site)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        return (None, None, str(e)[:400])
    items = (data.get("message") or {}).get("items") or []
    qt = _normalize_title(title)
    qsurnames = {s.lower() for s in surnames}
    for it in items:
        if it.get("type") not in TYPES_OK:
            continue
        cand_titles = it.get("title") or []
        if not any(_normalize_title(t) == qt for t in cand_titles):
            continue
        if year:
            issued = (it.get("issued") or {}).get("date-parts") or [[None]]
            cy = str((issued[0] or [None])[0] or "")
            if cy and abs(int(cy or 0) - int(year)) > 1:
                continue
        if qsurnames:
            cand_authors = it.get("author") or []
            cand_surnames = {(a.get("family") or "").lower() for a in cand_authors}
            if not (qsurnames & cand_surnames):
                continue
        return (it.get("DOI"), it, None)
    return (None, None, "no match")


def normalize_page_field(page: str) -> str:
    s = page.strip().replace("–", "-").replace("—", "-")
    s = re.sub(r"(\d)\s*-\s*(\d)", r"\1–\2", s)
    return s


TYPES_OK = frozenset({"journal-article", "proceedings-article"})

# Do not overwrite manually curated citation lines (Crossref journal title may differ).
SKIP_SLUGS = frozenset(
    {
        "cem-coarsened-exact-matching-in-stata",
        "cem-software-for-coarsened-exact-matching",
        "cem-coarsened-exact-matching-software",
        "clarify-software-for-interpreting-and-presenting-statistical-results",
    }
)


def merge_old_pages(new: str, old: str | None) -> str:
    """If Crossref omitted pages but the prior `publication:` line had them,
    append the old `Pp. ...` so we never strip page info from a working entry."""
    if not old or "Pp. " in new or "Pp. " not in old:
        return new
    m = re.search(r"Pp\.\s+\S+", old)
    if not m:
        return new
    return new + ", " + m.group(0)


def format_publication_line(msg: dict[str, Any]) -> str | None:
    mtype = msg.get("type") or ""
    if mtype and mtype not in TYPES_OK:
        return None
    cont = msg.get("container-title")
    if not cont or not isinstance(cont, list) or not (cont[0] or "").strip():
        return None
    journal = html.unescape(str(cont[0]).strip())
    vol = (msg.get("volume") or "").strip()
    iss = (msg.get("issue") or "").strip()
    page = (msg.get("page") or "").strip()
    article = (msg.get("article-number") or "").strip()
    if not vol and not iss and not page and not article:
        return None
    parts: list[str] = [journal]
    if vol:
        parts.append(vol)
    if iss:
        parts.append(iss)
    if page:
        parts.append("Pp. " + normalize_page_field(page))
    elif article:
        parts.append("Pp. " + article)
    return ", ".join(parts)


def load_front_matter_block(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None
    if text.startswith("---\r\n"):
        end = 5
    else:
        end = 4
    rest = text[end:]
    m = re.search(r"^---\s*$", rest, re.MULTILINE)
    if not m:
        return None
    yml = rest[: m.start()]
    body = rest[m.end() :]
    return (yml, body)


def write_front_matter(path: Path, yml: str, body: str) -> None:
    path.write_text("---\n" + yml + "---\n" + body, encoding="utf-8")


def set_publication_in_yml(yml: str, new_publication: str) -> str:
    inner = new_publication.replace("\\", "\\\\").replace('"', '\\"')
    line = f'publication: "{inner}"\n'
    if re.search(r"^publication:\s", yml, re.MULTILINE):
        return re.sub(
            r"^publication:\s*.*\n",
            line,
            yml,
            count=1,
            flags=re.MULTILINE,
        )
    yml = yml.rstrip() + "\n" + line
    return yml + ("\n" if not yml.endswith("\n") else "")


def collect_dois_raw(text: str) -> list[str]:
    """Extract DOI strings from raw file text when YAML cannot be parsed."""
    found: set[str] = set()
    for m in DOI_IN_TEXT.finditer(text):
        found.add(clean_doi(m.group(0)))
    return sorted(
        found,
        key=lambda x: (x.lower().startswith("10.7910"), -len(x)),
    )


def extract_old_publication(yml_raw: str) -> str | None:
    m = re.search(r'(?m)^publication:\s*"(.*)"\s*$', yml_raw)
    if m:
        return m.group(1).replace('\\"', '"')
    m = re.search(r"(?m)^publication:\s*(.+)\s*$", yml_raw)
    if m:
        return m.group(1).strip()
    return None


def run(pub_dir: Path, apply: bool, delay: float) -> None:
    rows: list[dict[str, Any]] = []
    static_files = pub_dir.parent.parent / "static" / "files"
    pdf_lookups = 0
    for index_md in sorted(pub_dir.glob("*/index.md")):
        slug = index_md.parent.name
        if slug in SKIP_SLUGS:
            rows.append({"slug": slug, "status": "skip_excluded"})
            continue
        block = load_front_matter_block(index_md)
        if not block:
            rows.append({"slug": slug, "status": "no_front_matter"})
            continue
        yml_raw, body = block
        full_text = f"---\n{yml_raw}---\n{body}"
        fm: dict[str, Any] | None
        try:
            fm = yaml.safe_load(yml_raw) or {}
        except yaml.YAMLError:
            fm = None
        if fm is not None:
            dois = collect_dois(fm)
        else:
            dois = collect_dois_raw(full_text)
        doi_source = "front_matter" if dois else None
        if not first_crossref_doi(dois) and fm is not None:
            pdf = collect_pdf_path(fm, static_files)
            if pdf is not None:
                pdf_dois = dois_in_pdf(pdf)
                if pdf_dois:
                    pdf_lookups += 1
                    seen = set(dois)
                    for d in pdf_dois:
                        if d not in seen:
                            dois.append(d)
                            seen.add(d)
                    if not doi_source:
                        doi_source = "pdf"
        title_search_result: dict[str, Any] | None = None
        if not first_crossref_doi(dois) and fm is not None:
            old_pub_for_check = fm.get("publication")
            old_pub_str = old_pub_for_check if isinstance(old_pub_for_check, str) else ""
            pub_types_fm = [t for t in (fm.get("publication_types") or []) if isinstance(t, str)]
            allowed_types = {"journal_article", "proceedings_article"}
            type_ok = bool(set(pub_types_fm) & allowed_types) or not pub_types_fm
            empty_pub = not old_pub_str.strip()
            if type_ok and empty_pub:
                title = (fm.get("title") or "").strip()
                authors_fm = [a for a in (fm.get("authors") or []) if isinstance(a, str)]
                year = ""
                d_ = fm.get("date")
                if isinstance(d_, str) and len(d_) >= 4:
                    year = d_[:4]
                if title:
                    doi_t, msg_t, _ = crossref_search_by_title(title, authors_fm, year)
                    time.sleep(delay)
                    if doi_t and msg_t:
                        dois.append(doi_t)
                        title_search_result = msg_t
                        doi_source = "title_search"
        old_s: str | None
        if fm is not None:
            old_pub = fm.get("publication")
            old_s = old_pub if isinstance(old_pub, str) else None
        else:
            old_s = extract_old_publication(yml_raw)
        doi = first_crossref_doi(dois)
        if not doi:
            rows.append({"slug": slug, "status": "no_doi"})
            continue
        if title_search_result is not None and clean_doi(title_search_result.get("DOI") or "") == doi:
            msg, err = title_search_result, None
        else:
            msg, err = crossref_fetch(doi)
            time.sleep(delay)
        if not msg:
            rows.append(
                {
                    "slug": slug,
                    "status": "crossref_error",
                    "doi": doi,
                    "error": err,
                }
            )
            continue
        new_pub = format_publication_line(msg)
        if new_pub:
            new_pub = merge_old_pages(new_pub, old_s)
        if not new_pub:
            rows.append(
                {
                    "slug": slug,
                    "status": "skip_type",
                    "doi": doi,
                    "cr_type": msg.get("type"),
                }
            )
            continue
        rows.append(
            {
                "slug": slug,
                "status": "ok",
                "doi": doi,
                "doi_source": doi_source or "front_matter",
                "old": old_s,
                "new": new_pub,
            }
        )
        if apply and new_pub != old_s:
            new_yml = set_publication_in_yml(yml_raw, new_pub)
            write_front_matter(index_md, new_yml, body)

    out_path = pub_dir.parent.parent / "data" / "publication_doi_fill_report.json"
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    changed = [r for r in rows if r.get("status") == "ok" and r.get("new") != r.get("old")]
    print("Wrote", out_path)
    for k, label in [
        ("ok", "resolved"),
        ("no_doi", "no usable doi"),
        ("crossref_error", "crossref error"),
        ("skip_type", "skipped (type / missing fields)"),
        ("skip_excluded", "skipped (slug allowlist)"),
        ("no_front_matter", "no fm"),
    ]:
        n = len([r for r in rows if r.get("status") == k])
        if n:
            print(f"  {label}: {n}")
    print(f"publication line updated (or would be): {len(changed)}")
    if pdf_lookups:
        from_pdf = [r for r in rows if r.get("doi_source") == "pdf"]
        print(f"  DOIs found via PDF (no DOI in front matter): {len(from_pdf)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--hugo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--delay", type=float, default=0.12)
    args = ap.parse_args()
    pub = args.hugo_root / "content" / "publication"
    if not args.apply:
        print("DRY RUN — no files written. Use --apply to update.\n")
    run(pub, apply=args.apply, delay=args.delay)


if __name__ == "__main__":
    main()
