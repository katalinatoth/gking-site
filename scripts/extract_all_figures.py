#!/usr/bin/env python3
"""Render every numbered figure in a PDF as a PNG thumbnail.

Used by the intake workflows to give the maintainer a visual picker for
the page's featured image. Reuses the caption-detection trick we used
to pull Figure 3 out of the survey-instability paper:

1. Walk every page; find every `Figure N:` (or `Figure N.`) caption.
2. The figure itself is the rectangle directly above the caption,
   bounded above by either the previous caption on the same page or
   the page's top margin.
3. Inside that vertical band, the figure's bbox is the union of:
     - every vector drawing rect from `page.get_drawings()`
     - every embedded image rect from `page.get_image_rects()`
     - every text-span bbox (so labels inside boxes / axis ticks /
       legend entries are included too)
4. Render that bbox at 5x zoom (~360 DPI) and save as
   `figure-<N>.png` in the output directory, alongside a
   `figures.json` manifest the PR-body builder reads to lay out the
   thumbnail grid.

CLI:

    python3 scripts/extract_all_figures.py <pdf> --out <dir>

Importable:

    from extract_all_figures import extract_all_figures
    figures = extract_all_figures(Path("paper.pdf"), Path("out/"))

Returns a list of dicts with `number`, `caption`, `page`, `bbox`,
`path`. Empty list if the PDF has no detectable numbered figures
(common for talks, books, and very early working papers).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]


# `Figure 3:` and `Figure 3.` are the two conventions this site's
# corpus actually uses. Tolerate `Figure 3a:` (panel labels) by
# capturing the whole token, but the manifest keeps the integer for
# slash-command targeting.
_CAPTION_RE = re.compile(
    r"^\s*(?:Figure|Fig\.)\s+(\d+)([A-Za-z]?)\s*[:.]",
)


def _caption_locations(page: "fitz.Page") -> list[tuple[int, str, "fitz.Rect", str]]:
    """Return [(figure_number, panel_letter, caption_rect, full_text), ...] for `page`.

    Uses the structured text layout (block -> line -> span) so multi-
    line captions still resolve to the first line, which is where the
    figure number lives. Lines whose first 60 characters don't match
    `_CAPTION_RE` are ignored.
    """
    out: list[tuple[int, str, fitz.Rect, str]] = []
    seen_numbers: set[tuple[int, str]] = set()
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans") or []
            if not spans:
                continue
            text = "".join((s.get("text") or "") for s in spans).lstrip()
            if not text:
                continue
            m = _CAPTION_RE.match(text[:60])
            if not m:
                continue
            num = int(m.group(1))
            panel = (m.group(2) or "").lower()
            if (num, panel) in seen_numbers:
                continue
            seen_numbers.add((num, panel))
            xs = [s["bbox"][0] for s in spans]
            ys = [s["bbox"][1] for s in spans]
            xs2 = [s["bbox"][2] for s in spans]
            ys2 = [s["bbox"][3] for s in spans]
            rect = fitz.Rect(min(xs), min(ys), max(xs2), max(ys2))
            out.append((num, panel, rect, text.strip()))
    out.sort(key=lambda t: t[2].y0)
    return out


def _figure_bbox(
    page: "fitz.Page",
    caption_y0: float,
    upper_bound_y: float,
) -> "fitz.Rect | None":
    """Compute the figure's bbox above `caption_y0` and below `upper_bound_y`.

    Two-pass logic so that body text *above* the figure (e.g. the last
    paragraph of the previous section) doesn't get included:

    1. Collect every vector-drawing rect and embedded-image rect inside
       the band `(upper_bound_y, caption_y0)`. This gives us the figure
       skeleton — the actual graphical content.
    2. Then add text spans only if their vertical extent overlaps with
       the skeleton's extent. That way axis labels, legend entries, and
       text-inside-boxes survive, but a paragraph that happens to sit
       between the previous figure and this caption does not.

    If no drawings or images exist in the band (very rare — e.g. a
    figure that's literally just centered text with no rule), we fall
    back to using every text span in the band.

    The final bbox is padded by 4 PDF points and clamped to the page.
    """
    art_rects: list[fitz.Rect] = []

    for d in page.get_drawings():
        r = d.get("rect")
        if r is None:
            continue
        if r.y1 <= caption_y0 - 1 and r.y0 >= upper_bound_y - 1:
            art_rects.append(fitz.Rect(r))

    for img in page.get_images(full=True):
        xref = img[0]
        try:
            for r in page.get_image_rects(xref):
                if r.y1 <= caption_y0 - 1 and r.y0 >= upper_bound_y - 1:
                    art_rects.append(fitz.Rect(r))
        except Exception:
            continue

    # Text-only fallback: when there's no graphical art in the band at
    # all, treat every span in the band as the figure.
    rects: list[fitz.Rect] = list(art_rects)

    if art_rects:
        art_y0 = min(r.y0 for r in art_rects)
        art_y1 = max(r.y1 for r in art_rects)
        # 6 pt slack lets caption-style labels that print just under or
        # just over the drawing rect (typical when text sits inside a
        # `box` shape with a 1-2 pt internal padding) join the figure.
        slack = 6.0
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bx0, by0, bx1, by1 = span.get("bbox", (0, 0, 0, 0))
                    if by1 <= caption_y0 - 1 and by0 >= upper_bound_y - 1:
                        if by1 >= art_y0 - slack and by0 <= art_y1 + slack:
                            rects.append(fitz.Rect(bx0, by0, bx1, by1))
    else:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bx0, by0, bx1, by1 = span.get("bbox", (0, 0, 0, 0))
                    if by1 <= caption_y0 - 1 and by0 >= upper_bound_y - 1:
                        rects.append(fitz.Rect(bx0, by0, bx1, by1))

    if not rects:
        return None

    x0 = min(r.x0 for r in rects) - 4
    y0 = min(r.y0 for r in rects) - 4
    x1 = max(r.x1 for r in rects) + 4
    y1 = max(r.y1 for r in rects) + 4
    page_rect = page.rect
    x0 = max(x0, page_rect.x0)
    y0 = max(y0, page_rect.y0)
    x1 = min(x1, page_rect.x1)
    y1 = min(y1, page_rect.y1)
    if x1 <= x0 or y1 <= y0:
        return None
    return fitz.Rect(x0, y0, x1, y1)


def extract_all_figures(
    pdf: Path,
    out_dir: Path,
    zoom: float = 5.0,
    max_figures: int = 30,
) -> list[dict[str, Any]]:
    """Render every numbered figure in `pdf` to `out_dir/figure-<N>.png`.

    Parameters
    ----------
    pdf : Path
        Source PDF. Must exist on disk; PyMuPDF reads it directly.
    out_dir : Path
        Destination directory. Created if missing. Existing
        `figure-*.png` and `figures.json` files inside are removed
        first so re-running on the same paper doesn't leave stale
        thumbnails behind.
    zoom : float
        Render scale factor. 5.0 corresponds to ~360 DPI on a standard
        612x792 PDF and yields thumbnails sharp enough to use directly
        as a `featured.png`.
    max_figures : int
        Safety cap. If a paper somehow declares more figures than this
        we render the first `max_figures` and stop, to keep the PR
        body and CI time bounded.

    Returns
    -------
    A list of manifest dicts, one per figure rendered. Empty if the
    PDF has no detectable numbered captions or if PyMuPDF isn't
    importable.
    """
    if fitz is None:
        return []
    try:
        doc = fitz.open(pdf)
    except Exception:
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("figure-*.png"):
        try:
            stale.unlink()
        except OSError:
            pass
    manifest_path = out_dir / "figures.json"
    if manifest_path.exists():
        try:
            manifest_path.unlink()
        except OSError:
            pass

    manifest: list[dict[str, Any]] = []

    try:
        # Build (page_index, fig_num, panel, caption_rect, caption_text)
        # for the whole document, in caption-order, deduping by number
        # so multi-panel papers (Figure 3a / Figure 3b) only contribute
        # one thumbnail (Figure 3 itself).
        captions: list[tuple[int, int, str, fitz.Rect, str]] = []
        seen_nums: set[int] = set()
        for pno in range(doc.page_count):
            page = doc[pno]
            for num, panel, rect, text in _caption_locations(page):
                if num in seen_nums:
                    continue
                # Only count `Figure 3:` (no panel) OR the very first
                # panel `Figure 3a:` we encounter — we want the figure
                # itself, not each subpanel.
                if panel and panel != "a":
                    continue
                seen_nums.add(num)
                captions.append((pno, num, panel, rect, text))
                if len(captions) >= max_figures:
                    break
            if len(captions) >= max_figures:
                break

        captions.sort(key=lambda t: t[1])

        for pno, num, panel, cap_rect, cap_text in captions:
            page = doc[pno]
            # On this same page, figure out the upper bound: either
            # the previous caption's bottom (so two figures on one
            # page don't bleed into each other) or the top margin.
            page_caps = _caption_locations(page)
            upper_bound = float(page.rect.y0)
            for other_num, _other_panel, other_rect, _ in page_caps:
                if other_rect.y1 < cap_rect.y0 - 1 and other_num != num:
                    upper_bound = max(upper_bound, float(other_rect.y1) + 2)

            bbox = _figure_bbox(page, float(cap_rect.y0), upper_bound)
            if bbox is None:
                continue
            mat = fitz.Matrix(zoom, zoom)
            try:
                pix = page.get_pixmap(matrix=mat, clip=bbox, alpha=False)
            except Exception:
                continue
            out_png = out_dir / f"figure-{num}.png"
            pix.save(str(out_png))
            manifest.append(
                {
                    "number": num,
                    "page": pno + 1,
                    "caption": cap_text[:240],
                    "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                    "path": out_png.name,
                    "width": pix.width,
                    "height": pix.height,
                }
            )
    finally:
        doc.close()

    if manifest:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf", type=Path, help="Path to the source PDF")
    ap.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Directory to write figure-<N>.png + figures.json into",
    )
    ap.add_argument(
        "--zoom",
        type=float,
        default=5.0,
        help="Render scale factor (default 5.0 = ~360 DPI)",
    )
    ap.add_argument(
        "--max-figures",
        type=int,
        default=30,
        help="Maximum number of figures to render (safety cap)",
    )
    args = ap.parse_args()

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 1
    if fitz is None:
        print("PyMuPDF (fitz) is required: pip install pymupdf", file=sys.stderr)
        return 1

    manifest = extract_all_figures(
        args.pdf, args.out, zoom=args.zoom, max_figures=args.max_figures
    )
    print(json.dumps({"figures": manifest, "count": len(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
