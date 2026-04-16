#!/usr/bin/env python3
"""Download publication thumbnails into bundles as featured.png / featured.jpg.

Sources (in order):
1. Scraped legacy HTML: Drupal /sites/g/files/.../styles/hwp.../public/... (any subpath under public/)
2. og:image / twitter:image on same page
3. Scored <img> (figures, screenshots) with base URL from og:image or canonical
4. Live fetch https://gking.harvard.edu/publication/<slug>/ when no scraped file matches
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, urlunparse

BASE = Path(__file__).resolve().parents[1]
PUB = BASE / "content" / "publication"
SCRAPED = BASE.parent / "scraped_data" / "pages"
LEGACY_BASE = "https://gking.harvard.edu"

# Drupal image styles: public/ may be gking/files/... OR 2025-09/... etc.
DRUPAL_STYLED = re.compile(
    r'["\'](/sites/g/files/omnuum7116/files/styles/hwp[^"\']+/public/[^"\']+\.(?:png|jpg|jpeg|webp|gif)(?:\?[^"\']*)?)["\']',
    re.IGNORECASE,
)

SKIP_SUBSTR = (
    "header-logo",
    "footer-logo",
    "favicon",
    "/files/css/",
    "googletagmanager",
    "img.shields.io",
    "shields.io",
    "gravatar.com",
    "opengraph.githubassets.com",
    "avatars.githubusercontent.com",
    "/akam/",
    "pixel_",
)
IMG_TAG_SRC = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
META_CONTENT = re.compile(r'content=["\']([^"\']+)["\']', re.IGNORECASE)
def canonical_href(html: str) -> str | None:
    """Drupal often uses href= before rel=canonical."""
    for pat in (
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']',
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    ):
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def has_featured(d: Path) -> bool:
    for f in os.listdir(d):
        low = f.lower()
        if "featured" not in low:
            continue
        ext = low.rsplit(".", 1)[-1]
        if ext in ("png", "jpg", "jpeg", "webp", "gif"):
            return True
    return False


def resolve_scraped_html(slug: str) -> Path | None:
    """Match content/<slug>/ to scraped_data/<name>.html (exact or strip -2007, -2015-215, etc.)."""
    parts = slug.split("-")
    for end in range(len(parts), 0, -1):
        cand = "-".join(parts[:end])
        p = SCRAPED / f"{cand}.html"
        if p.is_file():
            return p
    return None


def should_skip_url(url: str) -> bool:
    u = url.lower()
    if u.endswith((".svg", ".ico")):
        return True
    for s in SKIP_SUBSTR:
        if s in u:
            return True
    return False


def page_base_url(html: str) -> str | None:
    ch = canonical_href(html)
    if ch:
        return urljoin(ch, "/")
    for prop in ('property="og:image"', "property='og:image'", 'name="twitter:image"'):
        idx = html.lower().find(prop.lower())
        if idx == -1:
            continue
        chunk = html[idx : idx + 400]
        mc = META_CONTENT.search(chunk)
        if mc:
            u = mc.group(1).strip()
            if u.startswith("http"):
                return urljoin(u, "/")
    return None


def score_img_url(raw: str) -> int:
    u = raw.lower()
    if "/sites/g/files" in u and "/styles/hwp" in u:
        return 100
    if any(x in u for x in ("figure", "unnamed", "screenshot", "plot", "weighted", "/public/")):
        return 75
    if "logo" in u and "figure" not in u:
        return 15
    if "badge" in u or "shield" in u:
        return -1
    return 40


def meta_social_image_urls(html: str) -> list[str]:
    """og:image / twitter:image (attribute order varies)."""
    found: list[str] = []
    for pat in (
        r'<meta\s[^>]*(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta\s[^>]*content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:image|twitter:image)["\']',
    ):
        for m in re.finditer(pat, html, re.I):
            found.append(m.group(1).strip())
    return found


def extract_prioritized_urls(html: str) -> list[tuple[int, str]]:
    """Return [(score, url), ...] best first, deduped."""
    scored: list[tuple[int, str]] = []

    for m in DRUPAL_STYLED.finditer(html):
        u = m.group(1)
        if not should_skip_url(u):
            scored.append((100, u))

    for u in meta_social_image_urls(html):
        if not u.startswith("http") or should_skip_url(u):
            continue
        bonus = 5 if "gking.harvard.edu" in u else 0
        scored.append((38 + bonus, u))

    base = page_base_url(html)
    for m in IMG_TAG_SRC.finditer(html):
        raw = m.group(1).strip()
        if not raw or should_skip_url(raw):
            continue
        if raw.startswith("//"):
            raw = "https:" + raw
        if raw.startswith("http"):
            s = score_img_url(raw)
            if s >= 0:
                scored.append((s, raw))
        elif raw.startswith("/") and not raw.endswith(".svg"):
            s = score_img_url(raw)
            if s >= 0:
                scored.append((s, raw))
        elif base and not raw.startswith("data:"):
            joined = urljoin(base, raw)
            s = score_img_url(joined)
            if s >= 0:
                scored.append((s, joined))

    seen: set[str] = set()
    ordered: list[tuple[int, str]] = []
    for s, u in sorted(scored, key=lambda t: -t[0]):
        if u in seen:
            continue
        seen.add(u)
        ordered.append((s, u))
    return ordered


def download_url(url: str, out: Path) -> bool:
    try:
        subprocess.run(
            [
                "curl",
                "-fsSL",
                "-L",
                "-A",
                "Mozilla/5.0 (compatible; gking-site-migration)",
                "-o",
                str(out),
                normalize_url_for_curl(url),
            ],
            check=True,
            timeout=90,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    probe = subprocess.run(
        ["file", str(out)], capture_output=True, text=True, errors="replace"
    )
    pl = probe.stdout.lower()
    if not pl.strip() or "empty" in pl:
        out.unlink(missing_ok=True)
        return False
    if "svg" in pl or "html" in pl or "ascii text" in pl:
        out.unlink(missing_ok=True)
        return False
    if "jpeg" in pl or "jpg" in pl:
        jpg = out.parent / "featured.jpg"
        out.rename(jpg)
        return True
    if "avif" in pl:
        avif = out.parent / "featured.avif"
        out.rename(avif)
        png = out.parent / "featured.png"
        subprocess.run(
            ["sips", "-s", "format", "png", str(avif), "--out", str(png)],
            capture_output=True,
            timeout=60,
        )
        avif.unlink(missing_ok=True)
        return png.is_file()
    # WebP is often saved as featured.png; Hugo image.Fill expects real PNG/JPEG.
    if "webp" in pl or "web/p" in pl:
        tmp = out.with_suffix(".webp")
        out.rename(tmp)
        png = out.parent / "featured.png"
        subprocess.run(
            ["sips", "-s", "format", "png", str(tmp), "--out", str(png)],
            capture_output=True,
            timeout=60,
        )
        tmp.unlink(missing_ok=True)
        return png.is_file()
    if "png" in pl or "gif" in pl or "image" in pl:
        return True
    out.unlink(missing_ok=True)
    return False


def normalize_url_for_curl(url: str) -> str:
    """Percent-encode paths (e.g. ψ, spaces) so curl accepts them."""
    url = url.strip()
    if url.startswith("/"):
        url = urljoin(LEGACY_BASE, url)
    parts = urlparse(url)
    if not parts.scheme:
        return url
    path = quote(parts.path, safe="/%")
    return urlunparse(
        (parts.scheme, parts.netloc, path, parts.params, parts.query, parts.fragment)
    )


def live_url_for_slug(slug: str, scraped_path: Path | None) -> str:
    """Prefer <link rel=canonical> from scrape; Drupal paths are often not /publication/<slug>/."""
    if scraped_path and scraped_path.is_file():
        html = scraped_path.read_text(encoding="utf-8", errors="replace")
        href = canonical_href(html)
        if href:
            if href.startswith("http"):
                return href
            return urljoin(LEGACY_BASE, href)
    return f"{LEGACY_BASE}/publication/{slug}/"


def fetch_live_html(slug: str, scraped_path: Path | None = None) -> str | None:
    url = normalize_url_for_curl(live_url_for_slug(slug, scraped_path))
    try:
        p = subprocess.run(
            [
                "curl",
                "-fsSL",
                "-L",
                "-A",
                "Mozilla/5.0 (compatible; gking-site-migration)",
                "--max-time",
                "45",
                url,
            ],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=50,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    if p.returncode != 0 or not p.stdout:
        return None
    return p.stdout


def process_bundle(d: Path, html: str, source: str) -> tuple[bool, str]:
    candidates = extract_prioritized_urls(html)
    if not candidates:
        return False, "NO_IMG"
    out = d / "featured.png"
    for score, rel in candidates:
        if rel.startswith("http"):
            url = rel
        else:
            url = urljoin(LEGACY_BASE, rel)
        sys.stdout.flush()
        if download_url(url, out):
            return True, f"OK({source},score={score})"
    return False, f"CURL_FAIL tried {len(candidates)} urls (last {url})"


def main() -> int:
    if not SCRAPED.is_dir():
        print(f"Missing scraped pages dir: {SCRAPED}", file=sys.stderr)
        return 1

    dirs = sorted(p for p in PUB.iterdir() if p.is_dir() and not p.name.startswith("."))
    need = [d for d in dirs if not has_featured(d)]
    had_featured = len(dirs) - len(need)
    ok = fail = 0
    print(
        f"Publications needing images: {len(need)} (already have featured: {had_featured})",
        flush=True,
    )

    for i, d in enumerate(need, 1):
        slug = d.name
        print(f"[{i}/{len(need)}] {slug} …", flush=True)

        html_path = resolve_scraped_html(slug)
        html: str | None = None
        src = ""
        if html_path:
            html = html_path.read_text(encoding="utf-8", errors="replace")
            src = str(html_path.name)
        else:
            print(f"  no scraped HTML — trying live gking URL …", flush=True)
            html = fetch_live_html(slug, None)
            src = "LIVE"

        if not html:
            fail += 1
            print("  FAIL: NO_HTML", flush=True)
            time.sleep(0.2)
            continue

        success, msg = process_bundle(d, html, src)
        # Stale scrape may lack og:image; live Drupal page may have it.
        if not success and html_path and msg == "NO_IMG":
            print("  no image in scrape — trying live gking (canonical URL) …", flush=True)
            live = fetch_live_html(slug, html_path)
            if live:
                success, msg = process_bundle(d, live, "LIVE_RETRY")
            else:
                print("  (live fetch empty)", flush=True)

        if success:
            ok += 1
            print(f"  {msg}", flush=True)
        else:
            fail += 1
            print(f"  FAIL: {msg}", flush=True)

        time.sleep(0.2)

    print(
        f"done: new_ok={ok} skipped_had_featured={had_featured} failed={fail}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
