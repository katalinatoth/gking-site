#!/usr/bin/env python3
"""Render the markdown body for an intake PR (and the matching follow-up comment).

Both `intake-publication.yml` (the legacy intake/ folder upload flow)
and `intake-from-issue.yml` (the new issue-form flow) call this so the
two paths produce a consistent rich preview:

- Title / authors / publication line / DOI in a metadata block
- The auto-picked featured image, rendered inline with a permalink
- A thumbnail grid of every other Figure N detected in the PDF, with
  one-click `/figure N` swap commands underneath each thumbnail
- The full abstract, in a quoted block (the field most likely to
  need correction)
- Any supplementary materials we attached, with their resolved paths
- "Things to double-check" notes carried over from the intake report
- A clear pointer at the PR's `Files changed` tab as the primary
  edit surface, with the slash-command reference as a secondary path

CLI:

    python3 scripts/build_intake_pr_body.py \
        --report /tmp/intake_report.json \
        --figures content/publication/<slug>/_intake_figures/figures.json \
        --branch  intake/issue-12-foo \
        --pr-context > /tmp/pr_body.md

Either flag is optional. With no `--figures`, the figure picker is
omitted; with no `--branch`, image preview links are made relative to
the diff (so they still render on github.com inside the PR diff view).

Importable:

    from build_intake_pr_body import render_pr_body
    md = render_pr_body(report, figures, branch=branch, owner=..., repo=...)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _md_quote(text: str, prefix: str = "> ") -> str:
    """Indent every line of `text` with `prefix`. Preserves blank lines."""
    if not text:
        return ""
    return "\n".join(prefix + line if line else prefix.rstrip()
                     for line in text.splitlines())


def _raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    """https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>.

    Used so the embedded markdown image preview keeps working even
    when GitHub renders the PR description on a public page (the
    user-attachments CDN serves only signed URLs that expire).
    """
    safe_path = path.lstrip("/")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{safe_path}"


def render_pr_body(
    report: dict[str, Any],
    figures: list[dict[str, Any]] | None,
    *,
    owner: str,
    repo: str,
    branch: str,
    pr_number: int | None = None,
    short_url: str | None = None,
    supplementary: list[dict[str, str]] | None = None,
    issue_number: int | None = None,
    notes: str | None = None,
) -> str:
    """Build the PR body / comment markdown from an intake report.

    Parameters
    ----------
    report : dict
        Output of `scripts/intake_publication.py` (the JSON written
        to `data/_intake_report.json`).
    figures : list[dict] or None
        The `figures.json` manifest produced by
        `scripts/extract_all_figures.py`. Pass `None` if no figures
        were extracted (e.g. talks with no numbered captions).
    owner, repo, branch : str
        Used to build raw.githubusercontent.com URLs for image
        previews. They have to live somewhere stable so the
        thumbnails keep rendering after the PR is reviewed.
    pr_number : int, optional
        For deep-linking to the PR's Files-changed tab when the
        rendered body is posted as a follow-up comment rather than
        the original PR description (which can already see itself).
    short_url, supplementary, issue_number, notes :
        Surfaced verbatim from the issue form when present, so the
        PR body shows the maintainer the intent they expressed.
    """
    out: list[str] = []
    slug = report.get("slug") or "<unknown>"
    title = report.get("title") or "_(missing)_"
    authors = report.get("authors") or []
    year = report.get("year") or ""
    doi = report.get("doi") or ""
    publication = report.get("publication") or ""
    pub_types = report.get("publication_types") or []
    legacy_tab = report.get("legacy_tab") or ""
    abstract_chars = report.get("abstract_chars", 0)
    review_notes = list(report.get("review_notes") or [])
    rendered_fm = report.get("rendered_front_matter") or ""
    target_md = report.get("target_index_md") or ""
    target_pdf = report.get("target_pdf") or ""
    img_source = report.get("featured_image_source") or ""

    out.append(f"## Auto-import: `{slug}`")
    out.append("")
    if issue_number:
        out.append(f"_From issue #{issue_number}._")
        out.append("")
    out.append(f"**Title** &nbsp;{title}")
    if authors:
        out.append(f"**Authors** &nbsp;{', '.join(authors)}")
    if year:
        out.append(f"**Year** &nbsp;{year}")
    if pub_types or legacy_tab:
        ttypes = ", ".join(pub_types) or "_(none)_"
        out.append(
            f"**Type** &nbsp;{ttypes}"
            f" (Writings tab: **{legacy_tab or 'unrouted'}**)"
        )
    if doi:
        out.append(f"**DOI** &nbsp;[{doi}](https://doi.org/{doi}) "
                   f"(source: `{report.get('doi_source', 'unknown')}`)")
    if publication:
        out.append(f"**Citation** &nbsp;{publication}")
    if short_url:
        clean = short_url.strip().strip("/")
        out.append(f"**Short URL** &nbsp;`/{clean}/` "
                   f"(written into the page's `aliases:` list)")
    out.append("")
    out.append(f"PDF moved to `{target_pdf}`. Page lives at `{target_md}`.")
    out.append("")

    target_dir = ""
    if target_md:
        target_dir = str(Path(target_md).parent)

    out.append("### Featured image")
    out.append("")
    if img_source == "embedded_figure":
        out.append("Bot picked the largest embedded raster figure in the PDF.")
    elif img_source == "first_page_render":
        out.append(
            "No embedded figures large enough to use as a thumbnail; bot "
            "fell back to a render of page 1. **You'll almost certainly "
            "want to swap this** — see the figure picker below."
        )
    elif img_source:
        out.append(f"Bot couldn't extract a featured image (`{img_source}`).")
    else:
        out.append("_(no featured image written)_")
    if target_dir:
        for ext in ("png", "jpg", "jpeg"):
            featured_path = f"{target_dir}/featured.{ext}"
            out.append("")
            out.append(
                f"![Auto-picked featured image]({_raw_url(owner, repo, branch, featured_path)})"
            )
            break
    out.append("")

    if figures:
        out.append(f"### Figure picker ({len(figures)} figures detected)")
        out.append("")
        out.append(
            "To use a different figure as the page's featured image, "
            "comment **`/figure N`** below (e.g. `/figure 3`). The bot will "
            "swap `featured.png` and push the change."
        )
        out.append("")
        out.append("<table>")
        i = 0
        while i < len(figures):
            row = figures[i : i + 2]
            out.append("<tr>")
            for f in row:
                num = f.get("number")
                cap = (f.get("caption") or "").strip()
                page = f.get("page")
                fig_path = f"{target_dir}/_intake_figures/{f.get('path', '')}"
                img_url = _raw_url(owner, repo, branch, fig_path)
                cap_short = cap if len(cap) <= 200 else cap[:197] + "..."
                out.append("<td valign=\"top\" width=\"50%\">")
                out.append(f'<a href="{img_url}"><img src="{img_url}" alt="Figure {num}" /></a>')
                out.append("<br />")
                out.append(f"<sub><b>Figure {num}</b> (page {page}) "
                           f"&nbsp;&middot;&nbsp; <code>/figure {num}</code></sub>")
                if cap_short:
                    out.append("<br />")
                    out.append(f"<sub>{cap_short}</sub>")
                out.append("</td>")
            out.append("</tr>")
            i += 2
        out.append("</table>")
        out.append("")
    else:
        out.append("### Figure picker")
        out.append("")
        out.append(
            "_No numbered `Figure N:` captions detected in the PDF "
            "(common for talks, books, and very early working papers). "
            "If you want a different featured image, drop a "
            "`featured.png`/`featured.jpg` into `" + target_dir + "/` "
            "via the GitHub UI._"
        )
        out.append("")

    abstract_full = report.get("abstract_full") or ""
    if not abstract_full and rendered_fm:
        # Reconstruct from the YAML if the caller didn't pass one in.
        # The block scalar for `abstract:` is fenced by `|-` and
        # de-indented by two spaces; this is good enough for a preview.
        marker = "abstract: |-"
        if marker in rendered_fm:
            tail = rendered_fm.split(marker, 1)[1]
            lines = []
            for raw in tail.splitlines():
                if raw and not raw.startswith("  ") and not raw.startswith("\t"):
                    if raw.startswith("---"):
                        break
                    if ":" in raw and not raw.startswith(" "):
                        break
                lines.append(raw[2:] if raw.startswith("  ") else raw)
            abstract_full = "\n".join(lines).strip()

    out.append(f"### Abstract ({abstract_chars:,} chars)")
    out.append("")
    if abstract_full:
        out.append(_md_quote(abstract_full))
    else:
        out.append("> _(no abstract was extracted — Crossref didn't have one and "
                   "the PDF text didn't contain a recognisable Abstract section)_")
    out.append("")

    if supplementary:
        out.append("### Supplementary materials")
        out.append("")
        for s in supplementary:
            label = s.get("label") or s.get("name") or "Supplementary Material"
            url = s.get("url") or s.get("path") or ""
            out.append(f"- **{label}** — `{url}`")
        out.append("")

    if review_notes:
        out.append("### Things to double-check")
        out.append("")
        for n in review_notes:
            out.append(f"- {n}")
        out.append("")

    if notes:
        out.append("### Notes from the upload form")
        out.append("")
        out.append(_md_quote(notes.strip()))
        out.append("")

    out.append("### Edit anything")
    out.append("")
    files_changed_link = ""
    if pr_number:
        files_changed_link = (
            f"https://github.com/{owner}/{repo}/pull/{pr_number}/files"
        )
    out.append(
        "Click into **Files changed** "
        + (f"([direct link]({files_changed_link})) " if files_changed_link else "")
        + "and edit `index.md` directly — every front-matter field is just "
        "YAML, and GitHub's web editor handles it inline. That's the easiest "
        "way to fix the abstract, title, authors, year, citation, or any "
        "other field."
    )
    out.append("")
    out.append(
        "If you'd rather not click into the file (e.g. on mobile), you can "
        "post one of these slash commands as a PR comment:"
    )
    out.append("")
    out.append("| Command | Example | Effect |")
    out.append("|---|---|---|")
    out.append("| `/figure N` | `/figure 3` | swap the featured image to Figure N |")
    out.append("| `/title` | `/title The Real Title` | replace the title |")
    out.append("| `/authors` | `/authors Gary King; Jane Doe` | semicolon-separated |")
    out.append("| `/year` | `/year 2026-05-01` | year only or full ISO date |")
    out.append("| `/abstract` | (multi-line, until next `/cmd`) | replace the abstract |")
    out.append("| `/publication` | `/publication PNAS, 122, 4` | citation line |")
    out.append("| `/doi` | `/doi 10.1073/pnas.2412345121` | rewrites DOI link |")
    out.append("| `/type` | `/type journal_article` | re-routes Writings tab |")
    out.append("| `/alias` | `/alias /instability/` | adds a vanity short URL |")
    out.append("| `/supplement` | `/supplement files/foo.pdf \\| Online Appendix` | append a link |")
    out.append("")

    if rendered_fm:
        out.append("<details><summary>Generated front matter</summary>")
        out.append("")
        out.append("```yaml")
        out.append(rendered_fm.rstrip())
        out.append("```")
        out.append("")
        out.append("</details>")
        out.append("")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True,
                    help="Path to the intake_publication.py JSON report")
    ap.add_argument("--figures", type=Path, default=None,
                    help="Path to figures.json from extract_all_figures.py")
    ap.add_argument("--owner", default="iqss-research")
    ap.add_argument("--repo", default="gking-site")
    ap.add_argument("--branch", required=True,
                    help="Branch the PR is on (used to build raw image URLs)")
    ap.add_argument("--pr-number", type=int, default=None)
    ap.add_argument("--issue-number", type=int, default=None)
    ap.add_argument("--short-url", default=None)
    ap.add_argument("--supplementary-json", type=Path, default=None,
                    help="Optional JSON list [{label, url}, ...]")
    ap.add_argument("--notes", default=None)
    ap.add_argument("--abstract", type=Path, default=None,
                    help="Optional file containing the full abstract text")
    args = ap.parse_args()

    if not args.report.is_file():
        print(f"Report not found: {args.report}", file=sys.stderr)
        return 1
    report = json.loads(args.report.read_text(encoding="utf-8"))

    figures: list[dict[str, Any]] | None = None
    if args.figures and args.figures.is_file():
        figures = json.loads(args.figures.read_text(encoding="utf-8"))

    supplementary = None
    if args.supplementary_json and args.supplementary_json.is_file():
        supplementary = json.loads(args.supplementary_json.read_text(encoding="utf-8"))

    if args.abstract and args.abstract.is_file():
        report["abstract_full"] = args.abstract.read_text(encoding="utf-8").strip()

    body = render_pr_body(
        report,
        figures,
        owner=args.owner,
        repo=args.repo,
        branch=args.branch,
        pr_number=args.pr_number,
        short_url=args.short_url,
        supplementary=supplementary,
        issue_number=args.issue_number,
        notes=args.notes,
    )
    sys.stdout.write(body)
    if not body.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
