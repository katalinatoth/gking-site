"""Quick-add a new piece of content to the website from the terminal.

Companion to writings/scripts/intake_publication.py. The intake bot is
great for papers/talks/books that come as a PDF — drop the file under
_automation/intake/ and the bot fills in the front matter from Crossref.
But:

  * Software pages don't have a PDF; the canonical artefact is a GitHub
    or CRAN URL. They also need a row appended to
    software/data/software_legacy_rows.yaml.
  * Patent pages rarely have a Crossref hit — Gary has the patent number
    and a USPTO/Google Patents URL in hand.
  * Sometimes Gary already has all the metadata for a paper, talk, or
    book (e.g. retyping a citation from an email) and would rather skip
    the Crossref round-trip entirely.

This script handles all five content types via a uniform CLI:

    python3 _automation/scripts/quick_add.py software --slug my-tool \\
        --title "MyTool: An R Package for ..." \\
        --year 2026 \\
        --authors "Gary King; Jane Doe" \\
        --github https://github.com/IQSS/my-tool

    python3 _automation/scripts/quick_add.py patent --slug my-patent-2025 \\
        --title "..." \\
        --year 2025 \\
        --authors "Gary King; Co-Inventor" \\
        --publication "United States of America 12,345,678 B2" \\
        --source https://patents.google.com/patent/US12345678

    python3 _automation/scripts/quick_add.py paper --slug my-paper \\
        --title "..." --year 2026 --authors "Gary King" \\
        [--pdf ~/Downloads/my-paper.pdf]
        [--doi 10.1017/...]

    python3 _automation/scripts/quick_add.py talk --slug my-talk \\
        --title "..." --date 2026-04-30 --authors "Gary King" \\
        [--pdf ~/Downloads/slides.pdf]

    python3 _automation/scripts/quick_add.py book --slug my-book \\
        --title "..." --year 2026 --authors "Gary King" \\
        --publisher "Cambridge University Press" \\
        [--pdf ~/Downloads/manuscript.pdf]

Use `--dry-run` to print the would-be index.md and the exact files
this script would touch (no writes).

After running, commit + push and the deploy workflow goes live in ~3
minutes. With auto-push enabled (_automation/scripts/enable-auto-push.sh)
one `git commit` is all you need.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# Reuse intake_publication's YAML helpers so output style matches.
# After the section-driven repo reorg, intake_publication lives under
# writings/scripts/ rather than alongside us in _automation/scripts/.
sys.path.insert(0, str(ROOT / "writings" / "scripts"))
from intake_publication import (  # type: ignore[import-not-found]
    _yaml_dump,
    slugify,
    update_legacy_map,
    write_index_md,
)


def _parse_authors(raw: str | None) -> list[str]:
    """Accept either '; '-separated or comma-separated author lists.

    `; ` is preferred (some authors have commas in their displayed
    names, e.g. "King, Jr."). Falls back to comma split if no
    semicolons are present.
    """
    if not raw:
        return ["Gary King"]
    parts = [p.strip() for p in (raw.split(";") if ";" in raw else raw.split(","))]
    return [p for p in parts if p] or ["Gary King"]


def _section_dir(kind: str) -> Path:
    """Map content type to the section folder that owns its bundles."""
    if kind == "talk":
        return ROOT / "talks" / "content"
    if kind == "software":
        return ROOT / "software" / "content"
    # Papers, books, patents all live alongside the rest of /publication/.
    return ROOT / "writings" / "content"


def _pick_slug(requested: str | None, title: str) -> str:
    """Honour an explicit --slug, otherwise derive from title.

    Always run through slugify so we don't accept a manual slug with
    spaces, capitals, or unicode.
    """
    candidate = requested or title
    return slugify(candidate)


def _ensure_unique_slug(slug: str) -> str:
    """Append -2, -3, … if a folder already exists in either content
    section. Same logic as intake_publication.run()."""
    pub_dir = ROOT / "writings" / "content"
    talk_dir = ROOT / "talks" / "content"
    sw_dir = ROOT / "software" / "content"

    def _taken(s: str) -> bool:
        return (pub_dir / s).exists() or (talk_dir / s).exists() or (sw_dir / s).exists()

    if not _taken(slug):
        return slug
    for n in range(2, 9):
        candidate = f"{slug}-{n}"
        if not _taken(candidate):
            return candidate
    raise SystemExit(f"Could not find an unused slug starting with '{slug}'")


def _maybe_copy_pdf(src: Path | None, slug: str, dry_run: bool) -> Path | None:
    """Copy a user-supplied PDF into _site/static/files/<slug>.pdf and return
    the destination, or None if no PDF was given."""
    if src is None:
        return None
    src = Path(src).expanduser().resolve()
    if not src.is_file():
        raise SystemExit(f"--pdf path not found: {src}")
    dest = ROOT / "_site" / "static" / "files" / f"{slug}.pdf"
    if dry_run:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    shutil.copy2(src, dest)
    return dest


def _build_links(
    *,
    pdf_dest: Path | None,
    doi: str | None,
    github: str | None,
    cran: str | None,
    site: str | None,
    source: str | None,
    extra: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """Build the Hugo `links:` array.

    Type vocabulary follows existing content:
      - pdf        local PDF on this site
      - source     external authoritative URL (Publisher's Version, USPTO, etc.)
      - code       GitHub / repo URL (used by software pages)
      - site       project website (used by software pages)
    """
    links: list[dict[str, str]] = []
    if pdf_dest is not None:
        links.append({"type": "pdf", "url": f"files/{pdf_dest.name}"})
    if github:
        links.append({"type": "code", "url": github})
    if cran:
        links.append({"type": "site", "url": cran})
    if site:
        links.append({"type": "site", "url": site})
    if source:
        links.append({"type": "source", "url": source})
    elif doi:
        links.append({"type": "source", "url": f"https://doi.org/{doi}"})
    for t, u in extra:
        links.append({"type": t, "url": u})
    return links


def _build_front_matter(
    *,
    kind: str,
    title: str,
    date: str,
    authors: list[str],
    publication_line: str | None,
    publication_types: list[str],
    abstract: str | None,
    doi: str | None,
    links: list[dict[str, str]],
) -> dict[str, Any]:
    fm: dict[str, Any] = {
        "title": title,
        "date": date,
        "authors": authors,
        "publication_types": publication_types,
    }
    # Talks intentionally omit `publication`/`doi` — see content/talk/* schema.
    if publication_line and kind != "talk":
        fm["publication"] = publication_line
    if abstract:
        fm["abstract"] = abstract
    if doi and kind != "talk":
        fm["doi"] = doi
    fm["links"] = links
    return fm


def _append_software_row(slug: str, year: int, status: str, dry_run: bool) -> Path:
    """Append a row to software/data/software_legacy_rows.yaml.

    Manual append (rather than yaml.dump of the whole file) preserves the
    extensive header comments and the existing per-row formatting.
    """
    path = ROOT / "software" / "data" / "software_legacy_rows.yaml"
    text = path.read_text(encoding="utf-8")

    if f"slug: {slug}\n" in text or f"slug: '{slug}'\n" in text:
        return path

    new_row_lines = [f"  - year: {year}", f"    slug: {slug}"]
    if status and status != "current":
        new_row_lines.append(f"    status: {status}")
    new_row = "\n".join(new_row_lines) + "\n"

    if not text.endswith("\n"):
        text += "\n"
    text += new_row

    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return path


def _drupal_tab_for(kind: str, publication_types: list[str]) -> tuple[str, str]:
    """Return (drupal_type, writings_legacy_map.tab) for a kind."""
    pt = (publication_types or [""])[0]
    if kind == "software":
        return ("software", "software")
    if kind == "patent":
        return ("patent", "patent")
    if kind == "book":
        return ("book", "book")
    if kind == "talk":
        return ("presentation", "presentation")
    # paper / default — let publication_types[0] decide where it routes.
    if pt in ("journal_article", "conference_paper", "report"):
        return (pt, "journal" if pt == "journal_article" else "other")
    return ("working_paper", "journal")


def _resolve_date(year: int | None, explicit_date: str | None) -> str:
    """Return an ISO `YYYY-MM-DD`. Defaults to <year>-01-01 if only --year."""
    if explicit_date:
        return explicit_date
    if year:
        return f"{year}-01-01"
    raise SystemExit("--date or --year is required")


def cmd_software(args: argparse.Namespace) -> dict[str, Any]:
    if not (args.github or args.cran or args.site):
        raise SystemExit(
            "Software needs at least one external link: --github, --cran, "
            "or --site (in increasing order of preference, --github is best "
            "if available)."
        )

    title = args.title
    slug = _ensure_unique_slug(_pick_slug(args.slug, title))
    authors = _parse_authors(args.authors)
    pub_types = ["software"]
    date = _resolve_date(args.year, args.date)

    pdf_dest = _maybe_copy_pdf(args.pdf, slug, args.dry_run)
    links = _build_links(
        pdf_dest=pdf_dest,
        doi=None,
        github=args.github,
        cran=args.cran,
        site=args.site,
        source=None,
        extra=[],
    )

    fm = _build_front_matter(
        kind="software",
        title=title,
        date=date,
        authors=authors,
        publication_line=args.publication,
        publication_types=pub_types,
        abstract=args.abstract,
        doi=None,
        links=links,
    )

    target_md = _section_dir("software") / slug / "index.md"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    drupal, tab = _drupal_tab_for("software", pub_types)
    rows_file = _append_software_row(
        slug=slug,
        year=int(date[:4]),
        status=args.status,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        write_index_md(target_md, fm)
        update_legacy_map(legacy_map, slug, drupal, tab)

    return {
        "kind": "software",
        "slug": slug,
        "target_index_md": str(target_md.relative_to(ROOT)),
        "wrote_files": [
            str(target_md.relative_to(ROOT)),
            str(legacy_map.relative_to(ROOT)),
            str(rows_file.relative_to(ROOT)),
        ] + ([str(pdf_dest.relative_to(ROOT))] if pdf_dest else []),
        "rendered_front_matter": "---\n" + _yaml_dump(fm) + "---\n",
    }


def cmd_patent(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title
    slug = _ensure_unique_slug(_pick_slug(args.slug, title))
    authors = _parse_authors(args.authors)
    pub_types = ["patent"]
    date = _resolve_date(args.year, args.date)

    pdf_dest = _maybe_copy_pdf(args.pdf, slug, args.dry_run)
    links = _build_links(
        pdf_dest=pdf_dest,
        doi=None,
        github=None,
        cran=None,
        site=None,
        source=args.source,
        extra=[],
    )

    fm = _build_front_matter(
        kind="patent",
        title=title,
        date=date,
        authors=authors,
        publication_line=args.publication,
        publication_types=pub_types,
        abstract=args.abstract,
        doi=None,
        links=links,
    )

    target_md = _section_dir("patent") / slug / "index.md"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    drupal, tab = _drupal_tab_for("patent", pub_types)

    if not args.dry_run:
        write_index_md(target_md, fm)
        update_legacy_map(legacy_map, slug, drupal, tab)

    return {
        "kind": "patent",
        "slug": slug,
        "target_index_md": str(target_md.relative_to(ROOT)),
        "wrote_files": [
            str(target_md.relative_to(ROOT)),
            str(legacy_map.relative_to(ROOT)),
        ] + ([str(pdf_dest.relative_to(ROOT))] if pdf_dest else []),
        "rendered_front_matter": "---\n" + _yaml_dump(fm) + "---\n",
    }


def cmd_paper(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title
    slug = _ensure_unique_slug(_pick_slug(args.slug, title))
    authors = _parse_authors(args.authors)
    pub_types = [args.type]
    date = _resolve_date(args.year, args.date)

    pdf_dest = _maybe_copy_pdf(args.pdf, slug, args.dry_run)
    links = _build_links(
        pdf_dest=pdf_dest,
        doi=args.doi,
        github=None,
        cran=None,
        site=None,
        source=None,
        extra=[],
    )

    fm = _build_front_matter(
        kind="paper",
        title=title,
        date=date,
        authors=authors,
        publication_line=args.publication,
        publication_types=pub_types,
        abstract=args.abstract,
        doi=args.doi,
        links=links,
    )

    target_md = _section_dir("paper") / slug / "index.md"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    drupal, tab = _drupal_tab_for("paper", pub_types)

    if not args.dry_run:
        write_index_md(target_md, fm)
        update_legacy_map(legacy_map, slug, drupal, tab)

    return {
        "kind": "paper",
        "slug": slug,
        "target_index_md": str(target_md.relative_to(ROOT)),
        "wrote_files": [
            str(target_md.relative_to(ROOT)),
            str(legacy_map.relative_to(ROOT)),
        ] + ([str(pdf_dest.relative_to(ROOT))] if pdf_dest else []),
        "rendered_front_matter": "---\n" + _yaml_dump(fm) + "---\n",
    }


def cmd_talk(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title
    slug = _ensure_unique_slug(_pick_slug(args.slug, title))
    authors = _parse_authors(args.authors)
    pub_types = ["presentation"]
    date = _resolve_date(args.year, args.date)

    pdf_dest = _maybe_copy_pdf(args.pdf, slug, args.dry_run)
    links = _build_links(
        pdf_dest=pdf_dest,
        doi=None,
        github=None,
        cran=None,
        site=None,
        source=None,
        extra=[],
    )

    fm = _build_front_matter(
        kind="talk",
        title=title,
        date=date,
        authors=authors,
        publication_line=None,
        publication_types=pub_types,
        abstract=args.abstract,
        doi=None,
        links=links,
    )

    target_md = _section_dir("talk") / slug / "index.md"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    drupal, tab = _drupal_tab_for("talk", pub_types)

    if not args.dry_run:
        write_index_md(target_md, fm)
        update_legacy_map(legacy_map, slug, drupal, tab)

    return {
        "kind": "talk",
        "slug": slug,
        "target_index_md": str(target_md.relative_to(ROOT)),
        "wrote_files": [
            str(target_md.relative_to(ROOT)),
            str(legacy_map.relative_to(ROOT)),
        ] + ([str(pdf_dest.relative_to(ROOT))] if pdf_dest else []),
        "rendered_front_matter": "---\n" + _yaml_dump(fm) + "---\n",
    }


def cmd_book(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title
    slug = _ensure_unique_slug(_pick_slug(args.slug, title))
    authors = _parse_authors(args.authors)
    pub_types = ["book"]
    date = _resolve_date(args.year, args.date)

    publication_line = args.publication
    if not publication_line and args.publisher:
        publication_line = (
            f"{args.publisher}, {args.year}" if args.year else args.publisher
        )

    pdf_dest = _maybe_copy_pdf(args.pdf, slug, args.dry_run)
    links = _build_links(
        pdf_dest=pdf_dest,
        doi=args.doi,
        github=None,
        cran=None,
        site=None,
        source=None,
        extra=[],
    )

    fm = _build_front_matter(
        kind="book",
        title=title,
        date=date,
        authors=authors,
        publication_line=publication_line,
        publication_types=pub_types,
        abstract=args.abstract,
        doi=args.doi,
        links=links,
    )

    target_md = _section_dir("book") / slug / "index.md"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    drupal, tab = _drupal_tab_for("book", pub_types)

    if not args.dry_run:
        write_index_md(target_md, fm)
        update_legacy_map(legacy_map, slug, drupal, tab)

    return {
        "kind": "book",
        "slug": slug,
        "target_index_md": str(target_md.relative_to(ROOT)),
        "wrote_files": [
            str(target_md.relative_to(ROOT)),
            str(legacy_map.relative_to(ROOT)),
        ] + ([str(pdf_dest.relative_to(ROOT))] if pdf_dest else []),
        "rendered_front_matter": "---\n" + _yaml_dump(fm) + "---\n",
    }


# --------------------------------------------------------------------------
# CLI plumbing
# --------------------------------------------------------------------------

_COMMON_ARGS_HELP = """
Common arguments (apply to every subcommand unless noted):

  --title TEXT       Required. Display title.
  --slug TEXT        Optional. URL slug; defaults to slugify(title).
  --year YYYY        Year (used to scaffold date as YYYY-01-01).
  --date YYYY-MM-DD  Exact date (overrides --year).
  --authors "..."    Semicolon-separated list. Defaults to "Gary King".
  --abstract TEXT    Free-form abstract / summary.
  --pdf PATH         Optional local PDF; copied to static/files/<slug>.pdf.
  --dry-run          Print what would happen; touch nothing.
"""


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--title", required=True, help="Display title.")
    p.add_argument("--slug", help="URL slug; defaults to slugify(title).")
    p.add_argument("--year", type=int, help="Year (date defaults to YYYY-01-01).")
    p.add_argument("--date", help="ISO date YYYY-MM-DD; overrides --year.")
    p.add_argument(
        "--authors",
        default="Gary King",
        help='Semicolon-separated list, e.g. "Gary King; Jane Doe". '
        'Defaults to "Gary King".',
    )
    p.add_argument("--abstract", help="Abstract / summary text.")
    p.add_argument(
        "--pdf",
        help="Optional local PDF; copied to _site/static/files/.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Render but don't write any files.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quick_add",
        description=(
            "Scaffold a <section>/content/<slug>/index.md and update "
            "writings/data/writings_legacy_map.json (and "
            "software/data/software_legacy_rows.yaml for software). "
            "One subcommand per content type."
        ),
        epilog=_COMMON_ARGS_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    sw = sub.add_parser(
        "software",
        help="New software entry (no PDF; uses GitHub/CRAN/site URL).",
    )
    _add_common(sw)
    sw.add_argument("--github", help="GitHub repo URL (preferred).")
    sw.add_argument("--cran", help="CRAN package URL.")
    sw.add_argument("--site", help="Project website URL.")
    sw.add_argument(
        "--publication",
        help='Optional citation line (rare for software).',
    )
    sw.add_argument(
        "--status",
        choices=("current", "older"),
        default="current",
        help="Group on /software/. 'current' is the default; 'older' "
        "appears in the desaturated section at the bottom.",
    )
    sw.set_defaults(func=cmd_software)

    pat = sub.add_parser(
        "patent",
        help="New patent entry (rarely has Crossref data).",
    )
    _add_common(pat)
    pat.add_argument(
        "--publication",
        help='Citation line, e.g. "United States of America 12,345,678 B2".',
    )
    pat.add_argument(
        "--source",
        help="USPTO / Google Patents URL (sets the Publisher's Version button).",
    )
    pat.set_defaults(func=cmd_patent)

    pap = sub.add_parser(
        "paper",
        help=(
            "New paper / journal article (use intake/<file>.pdf for the "
            "Crossref-backed flow; this subcommand is for when you already "
            "have all the metadata in hand)."
        ),
    )
    _add_common(pap)
    pap.add_argument(
        "--type",
        choices=(
            "journal_article", "conference_paper", "working_paper", "report",
        ),
        default="journal_article",
        help="publication_types[0]. Default: journal_article.",
    )
    pap.add_argument("--publication", help="Citation line.")
    pap.add_argument("--doi", help="DOI (without the doi.org/ prefix).")
    pap.set_defaults(func=cmd_paper)

    tk = sub.add_parser(
        "talk",
        help=(
            "New talk / presentation (use intake/talk/<file>.pdf for the "
            "drop-and-go flow; this is for when you don't have a PDF)."
        ),
    )
    _add_common(tk)
    tk.set_defaults(func=cmd_talk)

    bk = sub.add_parser(
        "book",
        help=(
            "New book (use intake/book/<file>.pdf for the Crossref-backed "
            "flow; this is for when you already have all the metadata)."
        ),
    )
    _add_common(bk)
    bk.add_argument("--publisher", help='e.g. "Cambridge University Press".')
    bk.add_argument("--publication", help="Citation line; overrides --publisher.")
    bk.add_argument("--doi", help="Crossref DOI for the book, if any.")
    bk.set_defaults(func=cmd_book)

    args = parser.parse_args(argv)
    report = args.func(args)
    if args.dry_run:
        report["dry_run"] = True
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
