#!/usr/bin/env python3
"""Auto-import a publication from a PDF.

Designed to be invoked by .github/workflows/intake-publication.yml when
Gary uploads a PDF to intake/ in a pull request. The workflow runs:

    python3 scripts/intake_publication.py intake/the-paper.pdf

This script:

1.  Reads the PDF, extracts a DOI when one is printed (PyMuPDF).
2.  When no DOI is in the PDF, searches Crossref by title+author.
3.  Pulls full Crossref metadata (journal, volume, issue, pages,
    canonical title, full author list, abstract, year).
4.  Generates a slug from the title.
5.  Writes content/publication/<slug>/index.md with front matter that
    Hugo + the existing related_finder.html will render correctly.
6.  Moves the PDF from intake/ to static/files/<slug>.pdf and links it
    from the index.md.
7.  Adds the new slug to data/writings_legacy_map.json so the Writings
    page tabs route correctly.
8.  Writes a JSON intake report (data/_intake_report.json) summarising
    everything we found, everything we guessed, and everything Gary
    should double-check. The workflow turns that into a PR comment.

Manual local use (from hugo-site/):

    python3 scripts/intake_publication.py intake/foo.pdf
    python3 scripts/intake_publication.py intake/foo.pdf --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent

_doi_spec = importlib.util.spec_from_file_location(
    "fill_publication_from_doi", THIS_DIR / "fill_publication_from_doi.py"
)
_doi_mod = importlib.util.module_from_spec(_doi_spec)
assert _doi_spec and _doi_spec.loader
_doi_spec.loader.exec_module(_doi_mod)

clean_doi = _doi_mod.clean_doi
crossref_fetch = _doi_mod.crossref_fetch
crossref_search_by_title = _doi_mod.crossref_search_by_title
dois_in_pdf = _doi_mod.dois_in_pdf
first_crossref_doi = _doi_mod.first_crossref_doi
format_publication_line = _doi_mod.format_publication_line


try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]


PUB_TYPE_TO_TAB = {
    "journal-article": ("journal_article", "journal"),
    "proceedings-article": ("conference_paper", "other"),
    "book-chapter": ("book_chapter", "journal"),
    "book": ("book", "book"),
    "monograph": ("book", "book"),
    "report": ("report", "other"),
    "report-component": ("report", "other"),
    "posted-content": ("working_paper", "journal"),
    "dataset": ("data", "other"),
}


def slugify(text: str, max_len: int = 80) -> str:
    """URL-safe slug. Mirrors the convention in existing content/publication/* dirs."""
    if not text:
        return "paper"
    s = unicodedata.normalize("NFKD", text)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"['\u2018\u2019\u201c\u201d`]+", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "paper"


def _pdf_text(pdf: Path, max_pages: int = 3) -> str:
    if fitz is None:
        return ""
    try:
        doc = fitz.open(pdf)
    except Exception:
        return ""
    try:
        chunks = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            chunks.append(page.get_text() or "")
        return "\n".join(chunks)
    finally:
        doc.close()


def _guess_title_from_pdf(text: str) -> str:
    """Heuristic: the first non-empty, non-header line on page 1.

    Skip 'RESEARCH', 'Open Access', publisher mastheads, and other
    common boilerplate by looking for a line that's at least 6 words
    long with mostly Title Case-ish words. Used only as a last-resort
    fallback when Crossref has nothing.
    """
    HEADER_NOISE = {
        "research", "open access", "review", "letter", "letters",
        "article", "articles", "perspective", "commentary", "report",
        "abstract",
    }
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower().strip(":. ")
        if low in HEADER_NOISE:
            continue
        if len(line) < 12:
            continue
        if len(line.split()) < 3:
            continue
        return line
    return ""


def _guess_authors_from_pdf(text: str, title: str) -> list[str]:
    """Best-effort: take the line(s) right after the title until we see
    an institutional affiliation or 'Abstract'."""
    if not text:
        return []
    lines = [l.strip() for l in text.splitlines()]
    try:
        idx = next(i for i, l in enumerate(lines) if title and title in l)
    except StopIteration:
        return []
    candidates: list[str] = []
    for line in lines[idx + 1 : idx + 6]:
        if not line:
            continue
        if re.search(r"abstract\b|university|department|institute|©|copyright", line, re.IGNORECASE):
            break
        if "@" in line or re.search(r"\b(usa|uk|edu|harvard|mit|stanford)\b", line, re.IGNORECASE):
            break
        candidates.append(line)
    if not candidates:
        return []
    blob = " ".join(candidates)
    blob = re.sub(r"\d+", "", blob)  # affiliation footnote markers
    blob = re.sub(r"[*†‡§¶]+", "", blob)
    parts = re.split(r"\s*(?:,|\sand\s|\&)\s*", blob)
    return [p.strip(" .") for p in parts if p.strip()]


def _crossref_authors(msg: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for a in msg.get("author") or []:
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        if family and given:
            out.append(f"{given} {family}")
        elif family:
            out.append(family)
        elif given:
            out.append(given)
    return out


def _crossref_year(msg: dict[str, Any]) -> str:
    issued = (msg.get("issued") or {}).get("date-parts") or [[None]]
    yr = (issued[0] or [None])[0]
    return str(yr) if yr else ""


def _crossref_abstract(msg: dict[str, Any]) -> str:
    a = msg.get("abstract") or ""
    if not a:
        return ""
    a = re.sub(r"</?(jats:[a-z]+|p|i|b|em|strong)\s*/?>", "", a, flags=re.IGNORECASE)
    a = re.sub(r"\s+", " ", a).strip()
    if a.lower().startswith("abstract"):
        a = a[len("abstract") :].lstrip(":. ")
    return a


def _publication_types_from_crossref(msg: dict[str, Any] | None) -> tuple[list[str], str, str]:
    """Return (publication_types_for_front_matter, drupal_type, legacy_tab)."""
    t = (msg or {}).get("type") or ""
    if t in PUB_TYPE_TO_TAB:
        drupal, tab = PUB_TYPE_TO_TAB[t]
        return ([drupal], drupal, tab)
    return (["journal_article"], "journal_article", "journal")


_FIELD_ORDER = (
    "title", "date", "authors", "publication", "publication_types",
    "abstract", "doi", "links",
)


class _LiteralStr(str):
    """str subclass tagged so yaml renders it as a block scalar (|-)."""


def _literal_representer(dumper: yaml.Dumper, data: _LiteralStr):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


class _IndentedDumper(yaml.SafeDumper):
    """SafeDumper variant that indents list items under their parent
    key, matching the style of existing content/publication/*/index.md
    files (e.g. `authors:\n  - Gary King` not `authors:\n- Gary King`)."""

    def increase_indent(self, flow=False, indentless=False):  # noqa: ARG002
        return super().increase_indent(flow=flow, indentless=False)


_IndentedDumper.add_representer(_LiteralStr, _literal_representer)


def _yaml_dump(fm: dict[str, Any]) -> str:
    """Produce front matter YAML in roughly the same style as existing files.

    Field ordering is preserved (Hugo doesn't care, but humans do).
    Multi-line strings (e.g. abstract) render as `|-` block scalars to
    match the convention used by content/publication/* index.md files.
    """
    ordered: dict[str, Any] = {}
    for k in _FIELD_ORDER:
        if k in fm and fm[k] not in (None, "", []):
            v = fm[k]
            if isinstance(v, str) and (k == "abstract" or "\n" in v):
                v = _LiteralStr(v)
            ordered[k] = v
    for k, v in sorted(fm.items()):
        if k not in _FIELD_ORDER and v not in (None, "", []):
            ordered[k] = v
    return yaml.dump(
        ordered,
        Dumper=_IndentedDumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=10000,
    )


def write_index_md(target: Path, fm: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("---\n" + _yaml_dump(fm) + "---\n", encoding="utf-8")


def update_legacy_map(legacy_map_path: Path, slug: str, drupal: str, tab: str) -> bool:
    data = json.loads(legacy_map_path.read_text(encoding="utf-8"))
    entries = data.setdefault("entries", {})
    if slug in entries and entries[slug].get("tab") == tab and entries[slug].get("drupal") == drupal:
        return False
    entries[slug] = {"tab": tab, "drupal": drupal}
    # ensure_ascii=True matches the existing convention in this file
    # (e.g. "psi-\u03c8-..." rather than the literal Greek letter).
    legacy_map_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return True


def find_research_area_suggestions(
    title: str,
    abstract: str,
    research_areas_path: Path,
    top: int = 3,
) -> list[dict[str, Any]]:
    """Score every research_areas.json subcategory by token overlap.

    We don't auto-edit research_areas.json, but we surface the top
    candidates in the PR comment so Gary can copy-paste the slug into
    the right subcategory if he wants tighter See Also coverage."""
    if not research_areas_path.is_file():
        return []
    data = json.loads(research_areas_path.read_text(encoding="utf-8"))
    STOP = {
        "the", "a", "an", "and", "or", "of", "for", "in", "on", "to", "with",
        "by", "at", "as", "is", "are", "be", "we", "our", "this", "that",
        "from", "into", "using", "via", "new", "not", "no", "it", "its",
        "their", "you", "your", "but", "if", "so", "can", "will", "more",
        "most", "some", "all", "any", "each", "who", "which", "what",
    }

    def toks(s: str) -> set[str]:
        out = set()
        for w in re.split(r"[^A-Za-z0-9]+", (s or "").lower()):
            if len(w) > 3 and w not in STOP:
                out.add(w)
        return out

    paper_tokens = toks(title) | toks(abstract)
    if not paper_tokens:
        return []
    candidates: list[dict[str, Any]] = []
    for area_key in ("methods", "applications"):
        for area in data.get(area_key) or []:
            for sub in area.get("subcategories") or []:
                desc_tokens = toks(area.get("description", "")) | toks(sub.get("name", ""))
                for p in sub.get("papers") or []:
                    desc_tokens |= toks(p.get("title", ""))
                score = len(paper_tokens & desc_tokens)
                if score:
                    candidates.append(
                        {
                            "area": area.get("name"),
                            "subcategory": sub.get("name"),
                            "score": score,
                        }
                    )
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:top]


def run(pdf_path: Path, dry_run: bool = False) -> dict[str, Any]:
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if fitz is None:
        raise SystemExit("PyMuPDF (fitz) is required: pip install pymupdf")

    static_files = ROOT / "static" / "files"
    pub_dir = ROOT / "content" / "publication"
    legacy_map = ROOT / "data" / "writings_legacy_map.json"
    research_areas = ROOT / "data" / "research_areas.json"

    text = _pdf_text(pdf_path)
    pdf_dois = dois_in_pdf(pdf_path)
    review_notes: list[str] = []

    msg: dict[str, Any] | None = None
    doi: str | None = None
    doi_source = "none"

    if pdf_dois:
        doi = first_crossref_doi(pdf_dois)
        if doi:
            msg, err = crossref_fetch(doi)
            doi_source = "pdf"
            if not msg:
                review_notes.append(
                    f"Found DOI {doi} in PDF but Crossref lookup failed ({err}). Citation will be sparse."
                )

    if not msg:
        guess_title = _guess_title_from_pdf(text)
        guess_authors = _guess_authors_from_pdf(text, guess_title)
        if guess_title:
            doi_t, msg_t, _ = crossref_search_by_title(guess_title, guess_authors, None)
            if doi_t and msg_t:
                doi = doi_t
                msg = msg_t
                doi_source = "title_search"

    if msg:
        title = (msg.get("title") or [""])[0].strip() or _guess_title_from_pdf(text)
        authors = _crossref_authors(msg) or _guess_authors_from_pdf(text, title)
        year = _crossref_year(msg)
        abstract = _crossref_abstract(msg)
        publication_line = format_publication_line(msg) or ""
        pub_types, drupal, tab = _publication_types_from_crossref(msg)
    else:
        title = _guess_title_from_pdf(text) or pdf_path.stem.replace("-", " ").title()
        authors = _guess_authors_from_pdf(text, title)
        if not authors:
            authors = ["Gary King"]
            review_notes.append("Could not detect authors from PDF; defaulted to ['Gary King']. Edit the front matter.")
        year = ""
        abstract = ""
        publication_line = ""
        pub_types, drupal, tab = (["working_paper"], "working_paper", "journal")
        review_notes.append(
            "No DOI in the PDF and no Crossref title-match. Front matter is a scaffold "
            "from PDF text - title, authors, year, and abstract all need verification."
        )
    if not abstract:
        abstract_match = re.search(
            r"\bAbstract\b[\s:.\-]*([\s\S]{50,2500}?)(?:\n\s*\n|\bIntroduction\b|\bKeywords?\b|\bBackground\b)",
            text,
            flags=re.IGNORECASE,
        )
        if abstract_match:
            abstract = re.sub(r"\s+", " ", abstract_match.group(1)).strip()
            review_notes.append("Abstract was extracted from PDF body text - skim it for OCR artifacts.")

    if not year:
        m = re.search(r"\b(19|20)\d{2}\b", text[:1500])
        if m:
            year = m.group(0)
            review_notes.append(f"Year ({year}) was guessed from the PDF; double-check.")

    slug = slugify(title)
    if (pub_dir / slug).exists():
        for n in range(2, 9):
            new_slug = f"{slug}-{n}"
            if not (pub_dir / new_slug).exists():
                review_notes.append(f"Slug '{slug}' was already taken - using '{new_slug}'.")
                slug = new_slug
                break

    target_pdf = static_files / f"{slug}.pdf"
    target_md_dir = pub_dir / slug
    target_md = target_md_dir / "index.md"

    links: list[dict[str, str]] = [
        {"type": "pdf", "url": f"files/{target_pdf.name}"},
    ]
    if doi:
        links.append({"type": "source", "url": f"https://doi.org/{doi}"})

    fm: dict[str, Any] = {
        "title": title,
        "date": f"{year}-01-01" if year else "2026-01-01",
        "authors": authors,
        "publication_types": pub_types,
        "links": links,
    }
    if publication_line:
        fm["publication"] = publication_line
    if abstract:
        fm["abstract"] = abstract
    if doi:
        fm["doi"] = doi

    area_suggestions = find_research_area_suggestions(title, abstract, research_areas)

    report = {
        "slug": slug,
        "source_pdf": str(pdf_path.relative_to(ROOT)),
        "target_pdf": str(target_pdf.relative_to(ROOT)),
        "target_index_md": str(target_md.relative_to(ROOT)),
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "doi_source": doi_source,
        "publication": publication_line,
        "publication_types": pub_types,
        "drupal_type": drupal,
        "legacy_tab": tab,
        "abstract_chars": len(abstract),
        "review_notes": review_notes,
        "research_area_suggestions": area_suggestions,
        "dry_run": dry_run,
    }

    rendered_yaml = "---\n" + _yaml_dump(fm) + "---\n"
    report["rendered_front_matter"] = rendered_yaml

    if dry_run:
        return report

    target_md_dir.mkdir(parents=True, exist_ok=True)
    write_index_md(target_md, fm)
    static_files.mkdir(parents=True, exist_ok=True)
    if target_pdf.exists():
        target_pdf.unlink()
    shutil.move(str(pdf_path), str(target_pdf))
    update_legacy_map(legacy_map, slug, drupal, tab)
    report["wrote_files"] = [
        str(target_md.relative_to(ROOT)),
        str(target_pdf.relative_to(ROOT)),
        str(legacy_map.relative_to(ROOT)),
    ]
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path, help="Path to the PDF (e.g. intake/foo.pdf)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", type=Path, default=ROOT / "data" / "_intake_report.json")
    args = ap.parse_args()
    pdf = args.pdf if args.pdf.is_absolute() else (ROOT / args.pdf)
    report = run(pdf, dry_run=args.dry_run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
