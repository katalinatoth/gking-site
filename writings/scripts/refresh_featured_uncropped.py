#!/usr/bin/env python3
"""Replace cropped Drupal-styled publication thumbnails with their uncropped originals.

Pipeline per writings/content/<slug>/:

  1. Find scraped_data/pages/<slug>.html (using the same slug-stripping
     heuristics as fetch_publication_thumbnails.py). Extract the original
     image URL from <meta property="og:image"> or <link rel="image_src">,
     stripping any /styles/<style>/public/ segment so we get the uncropped
     path. Download and install as featured.<ext>.

  2. Fallback when no scraped HTML / no usable URL / download fails: open
     the linked PDF in _site/static/files/<name>.pdf, enumerate every
     embedded raster image with PyMuPDF, perceptual-hash compare each
     against the CURRENT cropped featured.png, and save the closest
     match (within a Hamming-distance threshold) as featured.<ext>.

By default only files whose intrinsic dimensions match a known Drupal
hwp_* style box (480x600, 800x800, 960x1200, ...) are touched. Use --force
to also rewrite anything that already has a non-fingerprint size.

Usage:
  python3 writings/scripts/refresh_featured_uncropped.py             # dry run
  python3 writings/scripts/refresh_featured_uncropped.py --apply     # do it
  python3 writings/scripts/refresh_featured_uncropped.py --only foo  # one slug
  python3 writings/scripts/refresh_featured_uncropped.py --apply --force

Requires:
  pip install -r _automation/scripts/requirements-featured.txt
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parents[1]

_spec = importlib.util.spec_from_file_location(
    "fetch_publication_thumbnails", THIS_DIR / "fetch_publication_thumbnails.py"
)
_fpt = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_fpt)

LEGACY_BASE: str = _fpt.LEGACY_BASE
SCRAPED: Path = _fpt.SCRAPED
PUB: Path = _fpt.PUB
resolve_scraped_html = _fpt.resolve_scraped_html
should_skip_url = _fpt.should_skip_url
normalize_url_for_curl = _fpt.normalize_url_for_curl

DRUPAL_CROP_SIZES = {
    (180, 180),
    (200, 250),
    (240, 300),
    (480, 600),
    (800, 800),
    (960, 1200),
    (1600, 1600),
}

_OG_IMAGE_PATTERNS = [
    re.compile(
        r'<meta\s[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta\s[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<link\s[^>]*rel=["\']image_src["\'][^>]*href=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<link\s[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']image_src["\']',
        re.IGNORECASE,
    ),
]

_STYLED_URL_RE = re.compile(
    r'(["\'])(/sites/g/files/[^"\']*?)/styles/[^/"\']+/public/([^"\']+)\1',
    re.IGNORECASE,
)

_STRIP_STYLES_RE = re.compile(
    r"/sites/g/files/([^/]+)/files/styles/[^/]+/public/", re.IGNORECASE
)

_PDF_URL_RE = re.compile(
    r"url:\s*[\"']?files/([^\"'\s]+\.pdf)", re.IGNORECASE
)


def existing_featured(d: Path) -> Path | None:
    for cand in sorted(d.glob("featured.*")):
        if cand.is_file() and cand.suffix.lower() in (
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"
        ):
            return cand
    return None


def image_dimensions(p: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(p) as im:
            return im.size
    except Exception:
        return None


def is_drupal_styled_crop(p: Path) -> bool:
    dims = image_dimensions(p)
    return bool(dims and dims in DRUPAL_CROP_SIZES)


def _strip_query_token(url: str) -> str:
    if "?" in url and ("itok=" in url or "h=" in url):
        return url.split("?", 1)[0]
    return url


def find_uncropped_url(html: str) -> str | None:
    """Return the best uncropped legacy image URL from a scraped page, or None."""
    for pat in _OG_IMAGE_PATTERNS:
        m = pat.search(html)
        if not m:
            continue
        u = m.group(1).strip()
        if not u or should_skip_url(u):
            continue
        if "/styles/" in u:
            stripped = _STRIP_STYLES_RE.sub(r"/sites/g/files/\1/files/", u)
            stripped = _strip_query_token(stripped)
            if not should_skip_url(stripped):
                return stripped
            continue
        return _strip_query_token(u)

    m2 = _STYLED_URL_RE.search(html)
    if m2:
        prefix = m2.group(2)
        tail = m2.group(3).split("?", 1)[0]
        rel = f"{prefix}/{tail}"
        return urljoin(LEGACY_BASE, rel)
    return None


def find_pdf_path(d: Path) -> Path | None:
    idx = d / "index.md"
    if not idx.is_file():
        return None
    text = idx.read_text(encoding="utf-8", errors="replace")
    m = _PDF_URL_RE.search(text)
    if not m:
        return None
    pdf = ROOT / "_site" / "static" / "files" / m.group(1)
    return pdf if pdf.is_file() else None


def _file_ext(p: Path) -> str | None:
    probe = subprocess.run(
        ["file", str(p)], capture_output=True, text=True, errors="replace"
    )
    pl = probe.stdout.lower()
    if "html" in pl or "ascii text" in pl or "empty" in pl or "svg" in pl:
        return None
    if "jpeg" in pl or " jpg" in pl:
        return "jpg"
    if "png" in pl:
        return "png"
    if "gif" in pl:
        return "gif"
    if "webp" in pl:
        return "webp"
    if "avif" in pl:
        return "avif"
    return None


def _download(url: str, dest: Path, timeout: int = 90) -> bool:
    try:
        subprocess.run(
            [
                "curl",
                "-fsSL",
                "-L",
                "-A",
                "Mozilla/5.0 (compatible; gking-site-migration)",
                "-o",
                str(dest),
                normalize_url_for_curl(url),
            ],
            check=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return dest.is_file() and dest.stat().st_size > 0


def install_as_featured(d: Path, src: Path, ext: str) -> Path | None:
    """Atomically replace any existing featured.* with src under the right ext."""
    ext = ext.lower().lstrip(".")
    if ext == "jpeg":
        ext = "jpg"
    if ext in ("webp", "avif"):
        png_tmp = d / ".featured.convert.png"
        r = subprocess.run(
            ["sips", "-s", "format", "png", str(src), "--out", str(png_tmp)],
            capture_output=True,
            timeout=60,
        )
        if r.returncode != 0 or not png_tmp.is_file():
            png_tmp.unlink(missing_ok=True)
            return None
        src.unlink(missing_ok=True)
        src = png_tmp
        ext = "png"
    new_path = d / f"featured.{ext}"
    for old in list(d.glob("featured.*")):
        if old != src and old != new_path:
            old.unlink(missing_ok=True)
    if src != new_path:
        if new_path.exists():
            new_path.unlink()
        src.rename(new_path)
    return new_path


def fetch_legacy(d: Path, url: str) -> Path | None:
    tmp = d / ".featured.download.tmp"
    tmp.unlink(missing_ok=True)
    if not _download(url, tmp):
        tmp.unlink(missing_ok=True)
        return None
    ext = _file_ext(tmp)
    if not ext:
        tmp.unlink(missing_ok=True)
        return None
    return install_as_featured(d, tmp, ext)


def extract_pdf_images(pdf: Path) -> list[tuple[bytes, str, int, int]]:
    import fitz

    out: list[tuple[bytes, str, int, int]] = []
    seen: set[int] = set()
    doc = fitz.open(pdf)
    try:
        for page in doc:
            for info in page.get_images(full=True):
                xref = info[0]
                if xref in seen:
                    continue
                seen.add(xref)
                try:
                    img = doc.extract_image(xref)
                except Exception:
                    continue
                w = int(img.get("width") or 0)
                h = int(img.get("height") or 0)
                if w * h < 64 * 64:
                    continue
                out.append((img["image"], img.get("ext", "png"), w, h))
    finally:
        doc.close()
    return out


def best_pdf_match(
    current: Path, pdf: Path, max_hash_dist: int = 18
) -> tuple[bytes, str] | None:
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(current) as im:
            target = imagehash.phash(im)
    except Exception:
        return None
    best: tuple[int, bytes, str] | None = None
    for raw, ext, _w, _h in extract_pdf_images(pdf):
        try:
            with Image.open(io.BytesIO(raw)) as im:
                cand = imagehash.phash(im)
        except Exception:
            continue
        dist = target - cand
        if best is None or dist < best[0]:
            best = (dist, raw, ext)
    if best is None or best[0] > max_hash_dist:
        return None
    return best[1], best[2]


def install_pdf_match(d: Path, raw: bytes, ext: str) -> Path | None:
    tmp = d / ".featured.frompdf.tmp"
    tmp.write_bytes(raw)
    real_ext = _file_ext(tmp) or ext
    return install_as_featured(d, tmp, real_ext)


def process(d: Path, args: argparse.Namespace) -> tuple[str, str]:
    cur = existing_featured(d)
    if cur is None:
        return "skipped", "no current featured.* on disk"

    dims = image_dimensions(cur) or (0, 0)
    is_styled = dims in DRUPAL_CROP_SIZES
    if not is_styled and not args.force:
        return "skipped", f"non-fingerprint dims {dims[0]}x{dims[1]} (use --force)"

    html_path = resolve_scraped_html(d.name)
    html = (
        html_path.read_text(encoding="utf-8", errors="replace")
        if html_path else ""
    )

    legacy_url = find_uncropped_url(html) if html else None
    if legacy_url and not legacy_url.startswith("http"):
        legacy_url = urljoin(LEGACY_BASE, legacy_url)

    pdf = find_pdf_path(d)

    if legacy_url:
        if args.dry_run:
            return "legacy", f"would fetch {legacy_url} (was {dims[0]}x{dims[1]})"
        new = fetch_legacy(d, legacy_url)
        if new is not None:
            return "legacy", f"saved {new.name} from {legacy_url}"
        if pdf is None:
            return "failed", f"legacy fetch failed and no PDF: {legacy_url}"
        match = best_pdf_match(cur, pdf) if cur.is_file() else None
        if match is None:
            return "failed", (
                f"legacy fetch failed; no PDF figure match in {pdf.name} "
                f"(url={legacy_url})"
            )
        raw, ext = match
        new = install_pdf_match(d, raw, ext)
        if new is None:
            return "failed", f"PDF match install failed for {pdf.name}"
        return "pdf", f"saved {new.name} from {pdf.name} (legacy fetch failed)"

    if pdf:
        if args.dry_run:
            return "pdf", (
                f"would PDF-extract from {pdf.name} (was {dims[0]}x{dims[1]})"
            )
        match = best_pdf_match(cur, pdf) if cur.is_file() else None
        if match is None:
            return "failed", f"no PDF figure match in {pdf.name}"
        raw, ext = match
        new = install_pdf_match(d, raw, ext)
        if new is None:
            return "failed", f"PDF match install failed for {pdf.name}"
        return "pdf", f"saved {new.name} from {pdf.name}"

    return "failed", "no legacy URL and no PDF available"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Replace cropped publication thumbnails with uncropped originals."
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Perform writes (default is dry run).",
    )
    ap.add_argument(
        "--force", action="store_true",
        help="Also rewrite featured files whose dimensions don't match a "
             "known Drupal styled-crop fingerprint.",
    )
    ap.add_argument(
        "--only", action="append", default=[], metavar="SLUG",
        help="Only process this slug (repeatable).",
    )
    args = ap.parse_args()
    args.dry_run = not args.apply

    if not PUB.is_dir():
        print(f"Missing publication dir: {PUB}", file=sys.stderr)
        return 1

    dirs = sorted(
        p for p in PUB.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    if args.only:
        sel = set(args.only)
        dirs = [d for d in dirs if d.name in sel]
        if not dirs:
            print(f"--only matched no slugs: {sorted(sel)}", file=sys.stderr)
            return 1

    counts = {"legacy": 0, "pdf": 0, "skipped": 0, "failed": 0}
    width = len(str(len(dirs)))
    for i, d in enumerate(dirs, 1):
        action, detail = process(d, args)
        counts[action] = counts.get(action, 0) + 1
        tag = action.upper().rjust(7)
        print(f"[{i:>{width}}/{len(dirs)}] {tag}  {d.name}: {detail}", flush=True)
        if args.apply and action in ("legacy",):
            time.sleep(0.2)

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(
        f"--- {mode}: legacy={counts['legacy']} pdf={counts['pdf']} "
        f"skipped={counts['skipped']} failed={counts['failed']}",
        flush=True,
    )
    return 0 if counts["failed"] == 0 or args.dry_run else 0


if __name__ == "__main__":
    raise SystemExit(main())
