"""Recover short-URL redirects from the legacy gking.harvard.edu Drupal site.

The old site used Drupal path aliases to expose memorable URLs like
`gking.harvard.edu/amelia`, `/sibs`, `/10k`, `/psi`, etc. — the URLs
Gary publicizes in his CV, talk titles, and other people's papers.

When the site moved to Hugo + GitHub Pages, those short URLs broke.
The list of which short URLs existed and where they pointed was never
explicitly exported, so we reconstruct it from `scraped_data/publications.json`
(harvested from the live old site during the migration). Each scraped
publication entry carries its old `url`, and one-segment URLs of the
form `https://gking.harvard.edu/<word>` are vanity short URLs that
should be preserved as redirects.

Run from hugo-site/:

    python3 scripts/import_legacy_short_urls.py            # print the YAML
    python3 scripts/import_legacy_short_urls.py --apply    # rewrite data/redirects.yaml

This script is idempotent: re-running it after additional vanity URLs
have been added to scraped_data/publications.json (extremely unlikely)
would refresh the recovered block without touching any hand-edited
entries that come after the recovered block's end-marker comment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent  # repo root holding scraped_data/

sys.path.insert(0, str(Path(__file__).resolve().parent))
from intake_publication import slugify  # type: ignore[import-not-found]

# Markers used to fence the auto-recovered block so re-running the
# script doesn't disturb anything Gary has hand-added below.
BEGIN_MARK = "  # -- BEGIN auto-recovered legacy short URLs --"
END_MARK = "  # -- END auto-recovered legacy short URLs --"

NAMESPACED = ("files", "publications", "publication", "presentations")


def _read_old_publications() -> list[dict]:
    """Load scraped_data/publications.json from the workspace root.

    The file lives at ../scraped_data/publications.json relative to
    hugo-site/. Bail with a clear message if it isn't there (e.g. in a
    sparse checkout).
    """
    candidates = [
        WORKSPACE / "scraped_data" / "publications.json",
        ROOT.parent / "scraped_data" / "publications.json",
    ]
    for c in candidates:
        if c.is_file():
            return json.loads(c.read_text(encoding="utf-8"))
    raise SystemExit(
        "Could not find scraped_data/publications.json. Looked in:\n  "
        + "\n  ".join(str(c) for c in candidates)
    )


def _extract_vanity_urls(pubs: list[dict]) -> list[tuple[str, str, str]]:
    """Return [(short_path, title, publication_type), ...] for every old
    vanity URL of shape gking.harvard.edu/<word> we can find.

    `<word>` excludes Drupal namespaces (`/files/`, `/publications/`,
    `/presentations/`) since those aren't user-facing short URLs.
    """
    vanity: list[tuple[str, str, str]] = []
    for p in pubs:
        u = (p.get("url") or "").strip()
        if not u:
            continue
        pr = urlparse(u)
        if "gking.harvard.edu" not in pr.netloc:
            continue
        parts = pr.path.strip("/").split("/")
        if len(parts) != 1 or not parts[0]:
            continue
        if parts[0].lower() in NAMESPACED:
            continue
        vanity.append(
            (parts[0], p.get("title", "").strip(), p.get("publication_type", ""))
        )
    return vanity


def _build_new_site_index() -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    """Return (slug_index, title_index).

    slug_index maps `slugify(title)` -> (section, folder_name).
    title_index maps lowercased title -> (section, folder_name).
    """
    slug_index: dict[str, tuple[str, str]] = {}
    title_index: dict[str, tuple[str, str]] = {}
    for sec in ("publication", "talk", "software"):
        base = ROOT / "content" / sec
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            idx = d / "index.md"
            if not idx.is_file():
                continue
            text = idx.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^title:\s*['\"]?(.*?)['\"]?\s*$", text, flags=re.M)
            if not m:
                continue
            title = m.group(1).strip().rstrip("\"").rstrip("'")
            s = slugify(title)
            slug_index.setdefault(s, (sec, d.name))
            title_index.setdefault(title.lower(), (sec, d.name))
    return slug_index, title_index


def _match(short: str, title: str, slug_index, title_index) -> tuple[str, str] | None:
    s = slugify(title)
    if s in slug_index:
        return slug_index[s]
    return title_index.get(title.lower())


def _yaml_quote(s: str) -> str:
    """Return s safe for a single-quoted YAML scalar."""
    return s.replace("'", "''")


def render_block(entries: list[dict]) -> str:
    """Render the recovered entries as a YAML block.

    The block sits between BEGIN_MARK / END_MARK so re-runs can replace
    just the auto-section, preserving any hand-edited entries that
    follow it in data/redirects.yaml.
    """
    lines = [
        BEGIN_MARK,
        "  # Vanity short URLs recovered from the legacy Drupal site",
        "  # via scripts/import_legacy_short_urls.py reading",
        "  # ../scraped_data/publications.json. Re-run that script to refresh",
        "  # this block; hand-edits below the END marker are preserved.",
        "  #",
        "  # The old site was case-insensitive on path aliases. Mixed-case",
        "  # originals (e.g. /CompSS, /EzI, /IndiaChild) are stored here as",
        "  # lowercase per the build's slug constraint; users typing the",
        "  # lowercase form get redirected, users typing the original",
        "  # mixed case will see a 404.",
        "",
    ]
    for e in entries:
        lines.append(f"  - from: {e['from']}")
        lines.append(f"    to:   {e['to']}")
        if e.get("note"):
            lines.append(f"    note: \"{_yaml_quote(e['note'])}\"")
        lines.append("")
    lines.append(END_MARK)
    return "\n".join(lines) + "\n"


def build_entries() -> tuple[list[dict], list[tuple[str, str]]]:
    """Return (entries, unmatched).

    `entries` is the list of dicts ready to render into YAML. `unmatched`
    is a list of (short_url, title) tuples that we couldn't link to a
    new-site page; the caller may want to print them as warnings.
    """
    pubs = _read_old_publications()
    vanity = _extract_vanity_urls(pubs)
    slug_index, title_index = _build_new_site_index()

    seen_short: set[str] = set()
    entries: list[dict] = []
    unmatched: list[tuple[str, str]] = []

    for short, title, _ptype in sorted(vanity, key=lambda t: t[0].lower()):
        lc = short.lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", lc):
            unmatched.append((short, title))
            continue
        if lc in seen_short:
            continue
        hit = _match(short, title, slug_index, title_index)
        if not hit:
            unmatched.append((short, title))
            continue
        sec, slug = hit
        target = f"/{sec}/{slug}/"
        # Trim ridiculously long titles in the note so the YAML stays readable.
        note_title = title if len(title) <= 80 else title[:77] + "..."
        note = f"old short URL was /{short}; goes to: {note_title}"
        entries.append({"from": lc, "to": target, "note": note})
        seen_short.add(lc)

    return entries, unmatched


def apply(dry_run: bool) -> None:
    entries, unmatched = build_entries()
    block = render_block(entries)

    redirects_yaml = ROOT / "data" / "redirects.yaml"
    text = redirects_yaml.read_text(encoding="utf-8")

    if BEGIN_MARK in text and END_MARK in text:
        # Replace existing block, keep hand-edits below END.
        head, tail = text.split(BEGIN_MARK, 1)
        _, tail = tail.split(END_MARK, 1)
        new_text = head.rstrip("\n") + "\n\n" + block + tail.lstrip("\n")
    else:
        # First-time injection. Insert immediately after `redirects:` line.
        m = re.search(r"^redirects:\s*\n", text, flags=re.M)
        if not m:
            raise SystemExit("redirects.yaml is missing a `redirects:` mapping key.")
        insert_at = m.end()
        new_text = text[:insert_at] + "\n" + block + text[insert_at:]

    if dry_run:
        sys.stdout.write(block)
    else:
        redirects_yaml.write_text(new_text, encoding="utf-8")
        print(f"Wrote {len(entries)} entries to {redirects_yaml.relative_to(ROOT)}")

    if unmatched:
        print()
        print(f"WARNING: {len(unmatched)} short URL(s) could not be matched:")
        for short, title in unmatched:
            print(f"  /{short:20s}  {title[:70]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite data/redirects.yaml in place. Without this, the "
        "block is printed to stdout for inspection.",
    )
    args = ap.parse_args()
    apply(dry_run=not args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
