#!/usr/bin/env python3
"""Apply slash-command edits posted in a PR comment to publication front matter.

Designed to be invoked by .github/workflows/intake-edit.yml when somebody
posts a comment containing one or more `/command value` lines on an open
intake PR. The workflow runs:

    python3 _automation/scripts/apply_pr_edits.py \
        --comment /tmp/comment_body.txt \
        --report  /tmp/edit_report.json \
        writings/content/foo/index.md [writings/content/bar/index.md ...]

For every target index.md, this script:

1. Parses the comment body into (cmd, value) pairs. A command line starts
   at column 0 with `/cmd ...`; subsequent indented or unindented lines
   that are NOT another `/cmd` line are appended to the previous value
   (so `/abstract` can span multiple paragraphs).
2. Applies the recognised commands to the YAML front matter, preserving
   key ordering and block-scalar style via the same `_yaml_dump`
   helper used by `intake_publication.py`.
3. Writes a JSON report listing what changed, what the new values are,
   and any warnings (unknown commands, invalid DOIs, etc.) so the
   workflow can post a confirmation comment back on the PR.

Recognised commands (case-insensitive):

    /title <text>               replace the title
    /authors A; B; C            split on ';' (use this even if your
                                names contain commas, e.g. "King, Gary")
    /year <YYYY> | /year <date> stores as ISO date in `date:`
    /date  <date>               alias for /year
    /abstract <multi-line text> replace the abstract
    /publication <text>         replace the citation line
    /doi <doi>                  replace the DOI; rewrites the
                                Publisher's Version link too
    /type <slug>                replace publication_types and re-route
                                the Writings tab via writings_legacy_map.json
    /figure <N>                 swap featured.png for the Nth figure
                                rendered into _intake_figures/figure-N.png
    /alias </foo/>              add a vanity short URL to `aliases:`
                                (multiple aliases supported; pass several
                                /alias lines to add several)
    /supplement <url> | <label> append a links: entry. <label> is optional;
                                defaults to "Supplementary Material".

A comment with no recognised commands produces no diff and no report rows.

Manual local use:

    echo '/title New Title' > /tmp/body.txt
    python3 _automation/scripts/apply_pr_edits.py \
        --comment /tmp/body.txt --report /tmp/r.json \
        writings/content/foo/index.md
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parents[1]

# Reuse the YAML dumper / legacy-map updater from intake_publication so
# the formatting and routing stay byte-for-byte consistent with the
# files generated at intake time. After the section-driven repo reorg,
# intake_publication lives in writings/scripts/.
_intake_spec = importlib.util.spec_from_file_location(
    "intake_publication", ROOT / "writings" / "scripts" / "intake_publication.py"
)
assert _intake_spec and _intake_spec.loader
_intake = importlib.util.module_from_spec(_intake_spec)
_intake_spec.loader.exec_module(_intake)

_yaml_dump = _intake._yaml_dump
update_legacy_map = _intake.update_legacy_map


# Map publication_types slug -> Writings tab. Mirrors the logic in
# build_writings_legacy_map.py (single source of truth for tab routing).
PUB_TYPE_TO_TAB = {
    "journal_article": "journal",
    "book": "book",
    "book_chapter": "journal",
    "working_paper": "journal",
    "conference_paper": "other",
    "report": "other",
    "data": "other",
    "software": "software",
    "courtbrief": "courtbrief",
    "presentation": "presentation",
    "other": "other",
}

VALID_TYPES = sorted(PUB_TYPE_TO_TAB)


# Anchored at start-of-line: a line that begins (after optional spaces)
# with `/`, then a letter, then word characters / dashes is treated as a
# command boundary. A bare `/` or `/word` not followed by whitespace +
# args is still a command (e.g. `/title` with the value on the next line),
# but `https://example.com` mid-paragraph is not.
CMD_PATTERN = re.compile(r"^\s{0,3}/([a-zA-Z][\w-]*)\b[ \t]*(.*)$")


SINGLE_LINE_CMDS = {
    "title", "authors", "year", "date", "doi", "type", "publication",
    "figure", "alias", "supplement",
}
MULTI_LINE_CMDS = {"abstract"}


def parse_commands(body: str) -> list[tuple[str, str]]:
    """Parse slash commands from a comment body.

    Returns a list of (lowercase_cmd, value) pairs in the order they
    appear. Single-line commands (`title`, `authors`, `year`/`date`,
    `doi`, `type`, `publication`) take only the rest of their line as
    the value, so trailing prose in the same comment doesn't get
    swallowed. Multi-line commands (`abstract`) absorb every following
    line until the next command line or end-of-comment, so a multi-
    paragraph abstract works.

    Unknown commands are treated like single-line commands (so a typo
    like `/titel` won't eat the rest of the comment) and surfaced as
    warnings.
    """
    out: list[tuple[str, str]] = []
    cur_cmd: str | None = None
    cur_lines: list[str] = []
    for raw_line in body.splitlines():
        m = CMD_PATTERN.match(raw_line)
        if m:
            if cur_cmd is not None:
                out.append((cur_cmd, "\n".join(cur_lines).rstrip()))
                cur_cmd = None
                cur_lines = []
            cmd = m.group(1).lower()
            tail = m.group(2)
            if cmd in MULTI_LINE_CMDS:
                cur_cmd = cmd
                cur_lines = [tail] if tail else []
            else:
                out.append((cmd, tail.strip()))
        elif cur_cmd is not None:
            cur_lines.append(raw_line)
    if cur_cmd is not None:
        out.append((cur_cmd, "\n".join(cur_lines).rstrip()))
    return out


def parse_year_or_date(value: str) -> str | None:
    """Convert flexible date input to ISO date, or None if unparseable.

    Accepted: `2024`, `2024-03-15`, `2024/3/15`, `2024-3-1`.
    """
    v = value.strip()
    if re.fullmatch(r"\d{4}", v):
        return f"{v}-01-01"
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", v)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


_DOI_RE = re.compile(r"^10\.\d{4,9}/[^\s]+$")


def normalize_doi(value: str) -> tuple[str, bool]:
    """Strip URL prefixes and validate DOI shape.

    Returns (cleaned_doi, is_valid). We always apply Gary's input even
    if invalid (he might know something the regex doesn't), but the
    workflow's feedback comment surfaces a warning so he can re-edit.
    """
    v = value.strip()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.IGNORECASE)
    v = v.strip().rstrip(".,;)")
    return v, bool(_DOI_RE.match(v))


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split `---\\nyaml\\n---\\nbody` into (parsed_yaml, raw_body).

    Body is preserved verbatim (whitespace, trailing newlines) so we
    don't accidentally rewrite the markdown portion of files that
    happen to have one.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].lstrip("\n")
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    fm = yaml.safe_load(fm_text) or {}
    return fm, body


def render_index_md(fm: dict[str, Any], body: str) -> str:
    rendered = "---\n" + _yaml_dump(fm) + "---\n"
    if body:
        rendered += body if body.startswith("\n") else "\n" + body
    return rendered


def update_doi_link(fm: dict[str, Any], doi: str) -> None:
    """Make sure links: contains exactly one source link to https://doi.org/<doi>."""
    target_url = f"https://doi.org/{doi}"
    links = fm.get("links")
    if not isinstance(links, list):
        links = []
    found = False
    for it in links:
        if not isinstance(it, dict):
            continue
        is_source = (
            it.get("type") == "source"
            or it.get("name") in ("Publisher's Version", "Source", "DOI")
            or "doi.org" in str(it.get("url") or "")
        )
        if is_source:
            it["type"] = "source"
            it["url"] = target_url
            found = True
            break
    if not found:
        links.append({"type": "source", "url": target_url})
    fm["links"] = links


def apply_authors(fm: dict[str, Any], value: str) -> tuple[bool, list[str]]:
    """Split the value on `;` and store as the authors list.

    Comma is intentionally NOT a separator: many academic name styles
    use `Last, First` (e.g. "King, Gary"), so commas inside a single
    name would otherwise misfire. Semicolons are unambiguous.
    """
    warnings: list[str] = []
    parts = [p.strip(" .") for p in value.split(";")]
    parts = [p for p in parts if p]
    if not parts:
        return False, ["/authors: no names found after splitting on ';'"]
    fm["authors"] = parts
    return True, warnings


def apply_type(
    fm: dict[str, Any], value: str, slug: str, legacy_map_path: Path
) -> tuple[bool, list[str]]:
    """Set publication_types[0] and re-route Writings tab via legacy map."""
    warnings: list[str] = []
    t = value.strip()
    if t not in VALID_TYPES:
        warnings.append(
            f"/type: '{t}' is not in {VALID_TYPES}; applied anyway "
            "(but the Writings tab may not match)."
        )
    fm["publication_types"] = [t]
    tab = PUB_TYPE_TO_TAB.get(t, "other")
    drupal = t
    if legacy_map_path.is_file():
        update_legacy_map(legacy_map_path, slug, drupal, tab)
    return True, warnings


def apply_alias(fm: dict[str, Any], value: str) -> tuple[bool, list[str]]:
    """Add a vanity short-URL alias to the page.

    Accepts `/instability/`, `instability`, `/instability`, `Instability/`
    — anything that looks like a single path segment. Hugo expects the
    alias as `/foo/` so we normalise to that form before storing.
    Multiple `/alias` commands accumulate into the existing aliases
    list rather than overwriting it.
    """
    warnings: list[str] = []
    raw = value.strip()
    if not raw:
        return False, ["/alias: empty value, skipped"]
    cleaned = raw.strip("/").strip()
    if not cleaned:
        return False, ["/alias: empty after stripping slashes"]
    if "/" in cleaned or " " in cleaned:
        warnings.append(
            f"/alias: '{raw}' contains a slash or space; using "
            f"'/{cleaned.split('/')[0].split()[0]}/' as the alias"
        )
        cleaned = cleaned.split("/")[0].split()[0]
    alias = f"/{cleaned}/"
    existing = fm.get("aliases") or []
    if not isinstance(existing, list):
        existing = [existing] if existing else []
    if alias in existing:
        warnings.append(f"/alias: '{alias}' is already set; nothing changed")
        return False, warnings
    existing.append(alias)
    fm["aliases"] = existing
    return True, warnings


def apply_supplement(fm: dict[str, Any], value: str) -> tuple[bool, list[str]]:
    """Append a `links:` entry from `/supplement <url> | <label>`.

    Accepts:
        /supplement files/foo.pdf | Online Appendix
        /supplement https://example.com/notes.pdf
        /supplement files/foo.pdf

    The label defaults to "Supplementary Material" if no `| label` is
    given. URLs without a scheme are stored verbatim, so existing
    site conventions like `files/foo.pdf` (resolved by Hugo's
    `staticrel`) keep working.
    """
    warnings: list[str] = []
    raw = value.strip()
    if not raw:
        return False, ["/supplement: empty value, skipped"]
    if "|" in raw:
        url_part, label_part = raw.split("|", 1)
        url = url_part.strip()
        label = label_part.strip() or "Supplementary Material"
    else:
        url = raw
        label = "Supplementary Material"
    if not url:
        return False, ["/supplement: no URL/path specified"]
    links = fm.get("links")
    if not isinstance(links, list):
        links = []
    links.append({"name": label, "url": url})
    fm["links"] = links
    return True, warnings


def apply_figure(
    md_path: Path, value: str
) -> tuple[bool, list[str]]:
    """Swap `featured.png` for `_intake_figures/figure-N.png` in the page dir.

    Returns (changed, warnings). Side-effects on the filesystem (file
    copy + `featured.*` cleanup) are performed when the source figure
    exists. The caller is responsible for `git add`-ing the page dir.
    """
    import shutil  # noqa: PLC0415 — keep close to use site

    warnings: list[str] = []
    raw = value.strip()
    m = re.fullmatch(r"#?(\d+)", raw)
    if not m:
        return False, [f"/figure: '{raw}' is not a number; expected /figure 3"]
    n = int(m.group(1))

    page_dir = md_path.parent
    src = page_dir / "_intake_figures" / f"figure-{n}.png"
    if not src.is_file():
        return False, [
            f"/figure: figure-{n}.png isn't in {page_dir}/_intake_figures/. "
            f"Either no Figure {n} was detected in the PDF, or the "
            f"_intake_figures/ folder has already been cleaned up "
            f"(this PR may have been re-run after a merge)."
        ]
    # Remove any stale featured.{png,jpg,jpeg,webp} so we don't end up
    # with two files Hugo would have to disambiguate between.
    for stale in page_dir.glob("featured.*"):
        try:
            stale.unlink()
        except OSError:
            pass
    target = page_dir / "featured.png"
    shutil.copyfile(src, target)
    return True, warnings


def apply_edits_to_file(
    md_path: Path,
    commands: list[tuple[str, str]],
    legacy_map_path: Path,
) -> dict[str, Any]:
    """Apply parsed commands to one index.md. Returns a per-file report.

    The report dict has the shape:
        {"path": str, "changes": [str, ...],
         "warnings": [str, ...], "applied_unknown": [...]}
    `changes` lists which fields were rewritten; `warnings` is what we
    want surfaced to Gary in the PR comment.
    """
    report: dict[str, Any] = {
        "path": str(md_path),
        "changes": [],
        "warnings": [],
        "unknown_cmds": [],
    }
    text = md_path.read_text(encoding="utf-8")
    fm, body = split_front_matter(text)
    if not fm:
        report["warnings"].append(
            f"{md_path}: no YAML front matter found; nothing changed."
        )
        return report

    slug = md_path.parent.name

    for cmd, value in commands:
        v = (value or "").strip()
        if not v and cmd not in {"abstract"}:
            report["warnings"].append(f"/{cmd}: empty value, skipped")
            continue
        if cmd == "title":
            fm["title"] = v
            report["changes"].append("title")
        elif cmd == "authors":
            ok, warns = apply_authors(fm, value)
            if ok:
                report["changes"].append("authors")
            report["warnings"].extend(warns)
        elif cmd in {"year", "date"}:
            iso = parse_year_or_date(v)
            if iso is None:
                report["warnings"].append(
                    f"/{cmd}: '{v}' is not a year or YYYY-MM-DD; skipped"
                )
                continue
            fm["date"] = iso
            report["changes"].append("date")
        elif cmd == "abstract":
            # Allow truly empty abstracts to be cleared with `/abstract `,
            # but only if they passed an explicit empty value (rare).
            fm["abstract"] = value.strip() if value.strip() else ""
            if fm["abstract"]:
                report["changes"].append("abstract")
            else:
                fm.pop("abstract", None)
                report["changes"].append("abstract (cleared)")
        elif cmd == "publication":
            fm["publication"] = v
            report["changes"].append("publication")
        elif cmd == "doi":
            doi, ok = normalize_doi(v)
            if not ok:
                report["warnings"].append(
                    f"/doi: '{v}' doesn't look like a DOI (expected `10.xxxx/...`); applied anyway"
                )
            fm["doi"] = doi
            update_doi_link(fm, doi)
            report["changes"].append("doi")
        elif cmd == "type":
            ok, warns = apply_type(fm, v, slug, legacy_map_path)
            if ok:
                report["changes"].append("publication_types")
            report["warnings"].extend(warns)
        elif cmd == "alias":
            ok, warns = apply_alias(fm, v)
            if ok:
                report["changes"].append("aliases")
            report["warnings"].extend(warns)
        elif cmd == "supplement":
            ok, warns = apply_supplement(fm, v)
            if ok:
                report["changes"].append("links")
            report["warnings"].extend(warns)
        elif cmd == "figure":
            # /figure swaps a binary file rather than editing YAML, so
            # it's tracked separately from the front-matter changes
            # but still rolls into `any_changes` upstream so the
            # workflow commits and pushes.
            ok, warns = apply_figure(md_path, v)
            if ok:
                report["changes"].append("featured.png")
                report["touched_files"] = list(set(
                    report.get("touched_files", []) + [str(md_path.parent / "featured.png")]
                ))
            report["warnings"].extend(warns)
        else:
            report["unknown_cmds"].append(cmd)

    if report["changes"]:
        new_text = render_index_md(fm, body)
        md_path.write_text(new_text, encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+", type=Path, help="index.md files to edit")
    ap.add_argument("--comment", type=Path, required=True,
                    help="File containing the comment body to parse")
    ap.add_argument("--report", type=Path, required=True,
                    help="Where to write the JSON report")
    ap.add_argument("--legacy-map", type=Path,
                    default=ROOT / "writings" / "data" / "writings_legacy_map.json",
                    help="Path to writings_legacy_map.json (for /type)")
    args = ap.parse_args()

    body = args.comment.read_text(encoding="utf-8")
    commands = parse_commands(body)

    if not commands:
        report = {
            "any_changes": False,
            "files": [],
            "commands_seen": 0,
            "note": "No slash commands recognised in the comment body.",
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0

    file_reports = []
    any_changes = False
    for md in args.targets:
        if md.is_absolute():
            md_resolved = md
        else:
            md_resolved = ROOT / md
        if not md_resolved.is_file():
            file_reports.append({
                "path": str(md),
                "changes": [],
                "warnings": [f"{md}: file not found"],
                "unknown_cmds": [],
            })
            continue
        r = apply_edits_to_file(md_resolved, commands, args.legacy_map)
        if r["changes"]:
            any_changes = True
        file_reports.append(r)

    report = {
        "any_changes": any_changes,
        "commands_seen": len(commands),
        "commands": [{"cmd": c, "value_preview": v[:120]} for c, v in commands],
        "files": file_reports,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
