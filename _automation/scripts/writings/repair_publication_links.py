#!/usr/bin/env python3
"""Audit and repair external URLs in publication links.

For every EditMe/Writings/<slug>/index.md, walk the `links:` block:

  * Probe each external URL with HEAD->GET (10s timeout, follow redirects).
  * Classify each link as ok / redirected / broken / proxy / shortener.
  * Where we can do better than the current link, rewrite it:

      - shortener (tinyurl / bit.ly / j.mp / goo.gl) -> https://doi.org/<doi>
        if any DOI is available in the front matter or PDF, otherwise the
        final URL the shortener resolves to.
      - Harvard EZproxy (ezp-prod1.hul.harvard.edu) -> https://doi.org/<doi>
        if available, else strip the proxy prefix.
      - dx.doi.org / www.doi.org -> doi.org canonical form.
      - 4xx / 5xx / timeout -> https://doi.org/<doi> if available.
      - 301/302 to a different host -> the final URL.

Writes a JSON report to EditMe/Writings/Data/publication_link_repair_report.json.

Usage:
  python3 _automation/scripts/writings/repair_publication_links.py             # dry run
  python3 _automation/scripts/writings/repair_publication_links.py --apply
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import importlib.util

try:
    import certifi

    def _ssl_context() -> ssl.SSLContext:
        return ssl.create_default_context(cafile=certifi.where())
except ImportError:
    def _ssl_context() -> ssl.SSLContext:
        return ssl.create_default_context()


_HTTPS_OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=_ssl_context())
)
_HTTPS_OPENER.addheaders = [("User-Agent",
                             "Mozilla/5.0 (compatible; gking-site-link-audit;"
                             " +https://github.com/KatalinaToth/gking-site)")]

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parents[2]

_doi_spec = importlib.util.spec_from_file_location(
    "fill_publication_from_doi", THIS_DIR / "fill_publication_from_doi.py"
)
_doi_mod = importlib.util.module_from_spec(_doi_spec)
assert _doi_spec and _doi_spec.loader
_doi_spec.loader.exec_module(_doi_mod)

collect_dois = _doi_mod.collect_dois
collect_pdf_path = _doi_mod.collect_pdf_path
dois_in_pdf = _doi_mod.dois_in_pdf
first_crossref_doi = _doi_mod.first_crossref_doi
load_front_matter_block = _doi_mod.load_front_matter_block

import yaml  # noqa: E402

UA = "Mozilla/5.0 (compatible; gking-site-link-audit; +https://github.com/KatalinaToth/gking-site)"

SHORTENER_HOSTS = {"tinyurl.com", "bit.ly", "j.mp", "goo.gl", "ow.ly", "t.co", "rdcu.be"}

# Hosts whose article pages are gone (decommissioned, retired, or never
# resolve to the right article anymore). Always swap these to doi.org/<doi>
# when we have a DOI.
DEFUNCT_HOSTS = {
    "pan.oxfordjournals.org",
    "science.sciencemag.org",
    "www.sciencemag.org",
    "sciencemag.org",
    "ann.sagepub.com",
    "journals.cambridge.org",
}

# When the resolved URL has these substrings, the redirect went somewhere
# generic (homepage, error page, cookie wall) - DON'T follow.
JUNK_REDIRECT_FRAGMENTS = (
    "error=cookies_not_supported",
    "/author-access-redirect",
    "?cookieSet=",
)

EZPROXY_RE = re.compile(
    r"\.ezp[-]prod\d+\.hul\.harvard\.edu$|\.ezproxy\.harvard\.edu$", re.IGNORECASE
)
DOI_HOST_RE = re.compile(r"^(?:www\.)?doi\.org$|^dx\.doi\.org$", re.IGNORECASE)


def normalize_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def is_shortener(host: str) -> bool:
    return host.lower() in SHORTENER_HOSTS


def is_ezproxy(host: str) -> bool:
    return bool(EZPROXY_RE.search(host or ""))


def is_doi_host(host: str) -> bool:
    return bool(DOI_HOST_RE.match(host or ""))


def is_article_url(url: str) -> bool:
    """Heuristic: does the URL point at a specific article (not a journal homepage)?"""
    p = urllib.parse.urlparse(url)
    if not p.path or p.path in ("", "/"):
        return False
    parts = [seg for seg in p.path.split("/") if seg]
    if len(parts) < 2:
        return False
    if any(seg.lower() in ("article", "doi", "content", "abs", "full", "pdf",
                           "view", "papers") for seg in parts):
        return True
    if any(re.fullmatch(r"\d{3,}", seg) for seg in parts):
        return True
    if "10." in p.path:
        return True
    return False


def probe(url: str, timeout: float = 12.0) -> tuple[int | None, str | None, str | None]:
    """Return (status_code, final_url, error). HEAD with GET fallback."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with _HTTPS_OPENER.open(req, timeout=timeout) as resp:
                return resp.status, resp.geturl(), None
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            try:
                final_url = e.url  # type: ignore[attr-defined]
            except Exception:
                final_url = url
            return e.code, final_url or url, None
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
            if method == "HEAD":
                continue
            reason = getattr(e, "reason", e)
            return None, None, str(reason)[:120]
        except Exception as e:
            if method == "HEAD":
                continue
            return None, None, str(e)[:120]
    return None, None, "unreachable"


def repair_url(orig: str, status: int | None, final: str | None, doi_url: str | None) -> str | None:
    """Decide on a replacement URL, or None to keep the original.

    Conservative rules - we replace only when we're sure the result is
    better than the original. doi.org URLs are always preferred when a
    DOI is available; otherwise we leave working links alone.
    """
    parsed = urllib.parse.urlparse(orig)
    host = (parsed.netloc or "").lower()

    if is_shortener(host):
        if doi_url:
            return doi_url
        if final and final != orig and is_article_url(final):
            return final
        return None

    if is_ezproxy(host):
        if doi_url:
            return doi_url
        return None

    if host in {"dx.doi.org", "www.doi.org"}:
        path = parsed.path.lstrip("/")
        if path.lower().startswith("10."):
            return f"https://doi.org/{path}"
        return None

    if host == "doi.org":
        if parsed.scheme != "https":
            return "https://" + orig.split("://", 1)[1]
        return None

    if host in DEFUNCT_HOSTS and doi_url:
        return doi_url

    if status is not None and status == 404 and doi_url:
        return doi_url

    if status is None and doi_url:
        return doi_url

    return None


def url_replace_in_yml(yml: str, old: str, new: str) -> tuple[str, bool]:
    """Replace `url: <old>` (with optional quoting) with `url: <new>` in YAML, once."""
    pat = re.compile(
        r"^(\s*url:\s*)(['\"]?)" + re.escape(old) + r"(['\"]?)\s*$",
        re.MULTILINE,
    )
    new_yml, n = pat.subn(rf"\g<1>\g<2>{new}\g<3>", yml, count=1)
    return new_yml, n > 0


def load_index(md: Path) -> tuple[str, str, dict[str, Any] | None]:
    block = load_front_matter_block(md)
    if not block:
        return "", "", None
    yml_raw, body = block
    try:
        fm = yaml.safe_load(yml_raw) or {}
    except yaml.YAMLError:
        fm = None
    return yml_raw, body, fm


def write_index(md: Path, yml: str, body: str) -> None:
    md.write_text("---\n" + yml + "---\n" + body, encoding="utf-8")


def collect_dois_for(fm: dict[str, Any], static_files: Path) -> list[str]:
    dois = collect_dois(fm)
    if not first_crossref_doi(dois):
        pdf = collect_pdf_path(fm, static_files)
        if pdf:
            for d in dois_in_pdf(pdf):
                if d not in dois:
                    dois.append(d)
    return dois


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    pub_dir = ROOT / "EditMe" / "Writings"
    static_files = ROOT / "_site" / "static" / "files"
    md_files = sorted(pub_dir.glob("*/index.md"))

    targets: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}
    placeholders: list[dict[str, Any]] = []
    for md in md_files:
        slug = md.parent.name
        yml, body, fm = load_index(md)
        if fm is None:
            continue
        links = fm.get("links")
        if not isinstance(links, list):
            continue
        dois = collect_dois_for(fm, static_files)
        doi = first_crossref_doi(dois)
        doi_url = normalize_doi_url(doi) if doi else None
        for it in links:
            if not isinstance(it, dict):
                continue
            u = it.get("url") or ""
            t = (it.get("type") or "").lower()
            if isinstance(u, str) and u.strip() in {"#", ""}:
                placeholders.append({"slug": slug, "type": t, "url": u})
                continue
            if not isinstance(u, str) or not u.startswith("http"):
                continue
            cache.setdefault(u, {"url": u})
            targets.append(
                {
                    "slug": slug,
                    "type": t,
                    "url": u,
                    "doi_url": doi_url,
                    "md": md,
                }
            )

    print(f"{len(targets)} external links across {len(md_files)} publications "
          f"({len(cache)} unique URLs).", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(probe, u): u for u in cache}
        done = 0
        for f in as_completed(futs):
            u = futs[f]
            try:
                s, final, err = f.result()
            except Exception as e:
                s, final, err = None, None, str(e)[:120]
            cache[u]["status"] = s
            cache[u]["final"] = final
            cache[u]["error"] = err
            done += 1
            if done % 25 == 0:
                print(f"  probed {done}/{len(cache)}", flush=True)

    rows: list[dict[str, Any]] = []
    edits_per_md: dict[Path, list[tuple[str, str]]] = {}
    for t in targets:
        info = cache[t["url"]]
        new = repair_url(t["url"], info.get("status"), info.get("final"), t.get("doi_url"))
        rows.append(
            {
                "slug": t["slug"],
                "type": t["type"],
                "old": t["url"],
                "status": info.get("status"),
                "final": info.get("final"),
                "error": info.get("error"),
                "new": new,
                "doi_url": t["doi_url"],
            }
        )
        if new and new != t["url"]:
            edits_per_md.setdefault(t["md"], []).append((t["url"], new))

    out = ROOT / "EditMe" / "Writings" / "Data" / "publication_link_repair_report.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print("Wrote", out, flush=True)

    n_changed = sum(1 for r in rows if r.get("new"))
    n_broken = sum(1 for r in rows if (r.get("status") or 0) >= 400 or r.get("error"))
    n_short = sum(1 for r in rows if urllib.parse.urlparse(r["old"]).netloc.lower() in SHORTENER_HOSTS)
    n_ezp = sum(1 for r in rows if is_ezproxy(urllib.parse.urlparse(r["old"]).netloc))
    print(f"  broken / errored: {n_broken}")
    print(f"  shorteners      : {n_short}")
    print(f"  Harvard ezproxy : {n_ezp}")
    print(f"  would change    : {n_changed} (in {len(edits_per_md)} files)")
    if placeholders:
        print(f"  placeholder url: {len(placeholders)} (manual review):")
        for p in placeholders:
            print(f"    {p['slug']} ({p['type']}): {p['url']!r}")

    if not args.apply:
        print("\nDry run; pass --apply to write changes.", flush=True)
        return 0

    for md, swaps in edits_per_md.items():
        yml, body, _ = load_index(md)
        if not yml:
            continue
        changed = 0
        for old, new in swaps:
            yml, ok = url_replace_in_yml(yml, old, new)
            if ok:
                changed += 1
        if changed:
            write_index(md, yml, body)
            print(f"  wrote {changed} swap(s) -> {md.relative_to(ROOT)}", flush=True)

    print("done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
