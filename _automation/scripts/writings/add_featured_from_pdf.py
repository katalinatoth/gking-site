#!/usr/bin/env python3
"""
For each EditMe/Writings/*/ missing featured.{png,jpg,...}, if index.md
links to _site/static/files/<name>.pdf, render the first page to
featured.png.
Requires: pip install pymupdf
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install pymupdf: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

RE_FILES_PDF = re.compile(
    r"url:\s*[\"']?files/([^\"'\s]+\.pdf)",
    re.IGNORECASE,
)


def first_pdf_in_front_matter(text: str) -> str | None:
    m = RE_FILES_PDF.search(text)
    return m.group(1) if m else None


def has_featured(pub_dir: Path) -> bool:
    return any(pub_dir.glob("featured.*"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--page",
        type=int,
        default=0,
        help="0-based PDF page index (default: first page)",
    )
    ap.add_argument(
        "--scale",
        type=float,
        default=2.5,
        help="Render scale for get_pixmap matrix",
    )
    args = ap.parse_args()
    root: Path = args.root
    pub_root = root / "EditMe" / "Writings"
    static_files = root / "_site" / "static" / "files"
    n_ok = 0
    n_skip = 0
    for d in sorted(pub_root.iterdir()):
        if not d.is_dir():
            continue
        if has_featured(d):
            n_skip += 1
            continue
        index = d / "index.md"
        if not index.is_file():
            continue
        text = index.read_text(encoding="utf-8", errors="replace")
        rel = first_pdf_in_front_matter(text)
        if not rel:
            continue
        pdf = static_files / rel
        if not pdf.is_file():
            print(f"skip (no file): {d.name} -> {rel}")
            continue
        out = d / "featured.png"
        if not args.apply:
            print(f"would add: {d.name} <- {rel} p.{args.page + 1}")
            n_ok += 1
            continue
        doc = fitz.open(pdf)
        if args.page < 0 or args.page >= doc.page_count:
            print(f"skip (bad page): {d.name} page {args.page}", file=sys.stderr)
            continue
        page = doc.load_page(args.page)
        mat = fitz.Matrix(args.scale, args.scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out))
        doc.close()
        print(f"ok: {d.name} -> featured.png ({pix.width}x{pix.height})")
        n_ok += 1
    print(
        f"Done. created={n_ok} skipped_already_had_featured={n_skip} "
        f"({'apply' if args.apply else 'dry run'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
