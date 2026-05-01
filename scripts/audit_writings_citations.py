#!/usr/bin/env python3
"""
Cross-reference each Hugo publication (writings) front matter with Crossref
using any DOI found in links, dataverse_url, or abstract.

Outputs JSON + a short text summary. Requires: PyYAML (yaml).

Usage (from the root of the gking-site checkout):
  python3 scripts/audit_writings_citations.py
  python3 scripts/audit_writings_citations.py --writings-only

  --writings-only: only slugs listed in data/writings_legacy_map.json
"""
from __future__ import annotations

import argparse
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

# --- DOI extraction ---
DOI_IN_TEXT = re.compile(
    r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)

# Skip Dataverse and other non-journal / non-Crossref DOI prefixes
CROSSREF_SKIPPED_PREFIXES = (
    "10.7910/",
    "10.5281/",
    "10.3886/",  # ICPSR
    "10.17605/",  # OSF
)


def clean_doi(d: str) -> str:
    """Strip trailing path segments often mistaken for part of a DOI (e.g. /full)."""
    d = d.rstrip(").,;]}\"'")
    d = d.split("?", 1)[0]
    for suf in ("/full", "/html", "/abstract", "/v1", "/v2", "/version"):
        if d.lower().endswith(suf):
            d = d[: -len(suf)]
    return d


def load_front_matter(path: Path) -> dict[str, Any] | None:
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
    yaml_raw = rest[: m.start()]
    try:
        return yaml.safe_load(yaml_raw) or {}
    except yaml.YAMLError:
        return None


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
    """Prefer journal-article style DOIs over book/ISBN-style (e.g. 10.3389/978-...)."""
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
            "User-Agent": "gking-site-citation-audit/1.0 (https://github.com/KatalinaToth/gking-site)",
        },
    )
    try:
        with urllib.request.urlopen(
            req, timeout=30, context=_ssl_context()
        ) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        return (None, str(e)[:400])
    if not isinstance(data, dict) or "message" not in data:
        return (None, "invalid JSON")
    return (data["message"], None)


def year_from_message(msg: dict[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "issued"):
        d = msg.get(key)
        if not d or "date-parts" not in d:
            continue
        parts = d["date-parts"]
        if parts and len(parts[0]) > 0:
            return str(parts[0][0])
    return None


def build_crossref_cite_line(msg: dict[str, Any]) -> str:
    cont = (msg.get("container-title") or [""])[0]
    vol = str(msg.get("volume") or "")
    iss = str(msg.get("issue") or "")
    page = str(msg.get("page") or "")
    parts: list[str] = []
    if cont:
        parts.append(cont)
    if vol or iss:
        if iss and vol:
            parts.append(f"{vol}({iss})")
        elif vol:
            parts.append(vol)
    if page and page not in (None, "None"):
        parts.append(page)
    y = year_from_message(msg)
    if y:
        parts.append(f"({y})")
    return ", ".join(parts)


def norm_cite(s: str) -> str:
    s = s.lower()
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\bppp?\b", "pp", s)
    s = re.sub(r"[^\w\s-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def score_overlap(local: str, cr: str) -> float:
    a = set(norm_cite(local).split())
    b = set(norm_cite(cr).split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def list_pdf_paths(
    hugo_root: Path, links: list[dict] | None, slug: str
) -> list[str]:
    out: list[str] = []
    if not links:
        return out
    for item in links:
        if not isinstance(item, dict):
            continue
        t = (item.get("type") or "").lower()
        u = item.get("url", "")
        if t != "pdf" or not isinstance(u, str) or ".." in u:
            continue
        p = (hugo_root / "static" / "publication" / slug / u).resolve()
        if p.is_file():
            out.append(str(p))
    return out


def run_audit(
    hugo_root: Path,
    writings_slugs: set[str] | None,
    delay: float,
) -> dict[str, Any]:
    pub_dir = hugo_root / "content" / "publication"
    results: list[dict[str, Any]] = []
    for index_md in sorted(pub_dir.glob("*/index.md")):
        slug = index_md.parent.name
        if writings_slugs is not None and slug not in writings_slugs:
            continue
        fm = load_front_matter(index_md) or {}
        local_pub = fm.get("publication")
        if not isinstance(local_pub, str):
            local_pub = None
        title = fm.get("title")
        if not isinstance(title, str):
            title = str(title or "")

        dois = collect_dois(fm)
        cr_doi = first_crossref_doi(dois)
        pdfs = list_pdf_paths(
            hugo_root, fm.get("links") if isinstance(fm.get("links"), list) else None, slug
        )

        entry: dict[str, Any] = {
            "slug": slug,
            "title": title,
            "local_publication": local_pub,
            "dois_found": dois,
            "pdfs": pdfs,
        }

        if not cr_doi:
            entry["status"] = "NO_DOI"
            entry["note"] = (
                "No non-dataverse DOI; verify via publisher or local PDF if present."
            )
            results.append(entry)
            continue

        entry["crossref_doi"] = cr_doi
        msg, cr_err = crossref_fetch(cr_doi)
        time.sleep(delay)
        if not msg:
            entry["status"] = "CROSSREF_ERROR"
            entry["crossref_error"] = cr_err
            results.append(entry)
            continue

        cr_title = (msg.get("title") or [""])[0]
        cr_cite = build_crossref_cite_line(msg)
        entry["crossref_title"] = cr_title
        entry["crossref_cite"] = cr_cite
        entry["crossref_type"] = msg.get("type")

        if local_pub:
            ov = score_overlap(local_pub, cr_cite)
            nloc = norm_cite(local_pub)
            big_toks = {tok for tok in norm_cite(cr_cite).split() if len(tok) > 3}
            if ov >= 0.25 or any(tok in nloc for tok in big_toks):
                entry["status"] = "LIKELY_OK" if ov >= 0.2 else "REVIEW"
            else:
                entry["status"] = "MISMATCH"
        else:
            entry["status"] = "NO_LOCAL_VENUE"

        results.append(entry)

    summary: dict[str, int] = {}
    for e in results:
        summary[e["status"]] = summary.get(e["status"], 0) + 1

    return {
        "hugo_root": str(hugo_root),
        "summary": summary,
        "count": len(results),
        "results": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--hugo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    ap.add_argument(
        "--writings-only",
        action="store_true",
        help="Only publication slugs in data/writings_legacy_map.json",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=0.12,
        help="Seconds between Crossref requests (etiquette).",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        help="JSON output path (default: data/citation_audit_report.json).",
    )
    args = ap.parse_args()
    hugo_root: Path = args.hugo_root

    writings_slugs: set[str] | None = None
    if args.writings_only:
        mpath = hugo_root / "data" / "writings_legacy_map.json"
        data = json.loads(mpath.read_text(encoding="utf-8"))
        entries = data.get("entries") or {}
        writings_slugs = set(entries.keys())

    report = run_audit(hugo_root, writings_slugs, args.delay)

    out_path = args.output
    if out_path is None:
        out_path = hugo_root / "data" / "citation_audit_report.json"

    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Wrote", out_path)
    print("Summary:", report["summary"])
    review = [
        r
        for r in report["results"]
        if r["status"]
        in ("MISMATCH", "REVIEW", "NO_DOI", "NO_LOCAL_VENUE", "CROSSREF_ERROR")
    ]
    print("Items needing follow-up:", len(review))
    for r in review[:40]:
        lp = (r.get("local_publication") or "")[:55]
        print(f"  {r['status']:16} {r['slug'][:50]:50} {lp}")
    if len(review) > 40:
        print(f"  ... and {len(review) - 40} more (see JSON)")


if __name__ == "__main__":
    main()
