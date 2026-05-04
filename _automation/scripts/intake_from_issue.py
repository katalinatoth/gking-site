#!/usr/bin/env python3
"""Process an `intake`-labeled GitHub Issue Form into a draft PR.

Triggered by `.github/workflows/intake-from-issue.yml` when somebody
opens an issue from the **Upload a paper** template. The workflow runs:

    python3 _automation/scripts/intake_from_issue.py \
        --body  /tmp/issue_body.md \
        --issue 42 \
        --token "$GITHUB_TOKEN" \
        --report-out /tmp/intake_report.json \
        --pr-body-out /tmp/pr_body.md \
        --branch-out /tmp/intake_branch_name.txt

This script:

1.  Parses the issue body into fields (kind, main PDF link, short URL,
    supplementary PDF links, notes). Issue Forms render each field
    under a `### <Label>` heading, so we just split on those.
2.  Downloads every linked PDF from GitHub's user-attachments CDN
    (those URLs are private; we authenticate with `GITHUB_TOKEN`).
3.  Drops the main PDF into `intake/`, `intake/talk/`, or
    `intake/book/` according to the chosen type, then invokes the
    existing `intake_publication.run(...)` so the index.md, the move
    to `_site/static/files/<slug>.pdf`, and the writings legacy map
    all happen via the same code path as the legacy intake/ flow.
4.  Saves any supplementary PDFs straight into `_site/static/files/`
    with deterministic names (`<slug>-supplement-<N>.pdf`) and patches
    the new index.md to add a `links:` entry for each one.
5.  Patches `aliases:` if a short URL was set.
6.  Renders every numbered figure from the PDF into
    `EditMe/Writings/<slug>/_intake_figures/` (or
    `EditMe/Writings/Presentations/<slug>/_intake_figures/`).
7.  Writes the PR body (abstract preview + figure picker + edit
    instructions) by calling `build_intake_pr_body.render_pr_body`.
8.  Emits a slugified branch name (`intake/issue-<N>-<slug>`) so the
    workflow can `git checkout -b` and push.

The script does NOT shell out to git — that's the workflow's job.
This keeps the script unit-testable and re-runnable locally.

Manual local invocation (offline-ish — without the token, supplementary
PDF downloads will fail unless the URLs are public):

    python3 _automation/scripts/intake_from_issue.py \
        --body /path/to/issue.md \
        --issue 1 --token "" \
        --report-out /tmp/r.json \
        --pr-body-out /tmp/b.md \
        --branch-out /tmp/branch.txt
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
# THIS_DIR is `_automation/scripts/`, so:
#   parents[0] = `_automation/`
#   parents[1] = repo root (gking-site/hugo-site/)
ROOT = THIS_DIR.parents[1]


# Reuse the actual intake script's helpers (slugify, run, _yaml_dump).
# Loading by file path lets the workflow run without installing the
# package or fiddling with PYTHONPATH. After the section-driven repo
# reorg, intake_publication and extract_all_figures live in
# _automation/scripts/writings/.
_writings_scripts = ROOT / "_automation" / "scripts" / "writings"
_intake_spec = importlib.util.spec_from_file_location(
    "intake_publication", _writings_scripts / "intake_publication.py"
)
assert _intake_spec and _intake_spec.loader
_intake = importlib.util.module_from_spec(_intake_spec)
_intake_spec.loader.exec_module(_intake)

_figs_spec = importlib.util.spec_from_file_location(
    "extract_all_figures", _writings_scripts / "extract_all_figures.py"
)
assert _figs_spec and _figs_spec.loader
_figs = importlib.util.module_from_spec(_figs_spec)
_figs_spec.loader.exec_module(_figs)

_body_spec = importlib.util.spec_from_file_location(
    "build_intake_pr_body", THIS_DIR / "build_intake_pr_body.py"
)
assert _body_spec and _body_spec.loader
_body = importlib.util.module_from_spec(_body_spec)
_body_spec.loader.exec_module(_body)


# Map of dropdown labels -> intake subfolder.
KIND_TO_FOLDER: dict[str, str] = {
    "article": "",
    "article (journal / working paper)": "",
    "paper": "",
    "book": "book",
    "talk": "talk",
    "talk (slide deck)": "talk",
    # Patent and software are not PDF-driven content types in this site;
    # we still scaffold a publication page for them and rely on Gary to
    # fix the type via /type or the YAML field afterwards.
    "patent": "",
    "software": "",
}


def parse_issue_body(body: str) -> dict[str, Any]:
    """Split an Issue Form body into a dict keyed by field heading.

    Issue Forms render every field as:

        ### <Label>

        <value>

    so we walk the body line-by-line, treating any line that starts
    with `###` followed by a space as a new section header. Values
    of `_No response_` (GitHub's literal placeholder for unfilled
    optional fields) become empty strings.

    Returns a dict keyed by the lowercase, dash-collapsed label
    (so `### Short URL` -> `"short-url"`).
    """
    fields: dict[str, str] = {}
    cur_key: str | None = None
    cur_lines: list[str] = []
    header_re = re.compile(r"^###\s+(.+?)\s*$")

    def _flush() -> None:
        if cur_key is None:
            return
        text = "\n".join(cur_lines).strip()
        if text == "_No response_":
            text = ""
        fields[cur_key] = text

    for raw_line in body.splitlines():
        m = header_re.match(raw_line)
        if m:
            _flush()
            label = m.group(1).strip()
            cur_key = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
            cur_lines = []
        elif cur_key is not None:
            cur_lines.append(raw_line)
    _flush()
    return fields


_LINK_RE = re.compile(r"\[([^\]]+?)\]\((https?://[^\s)]+)\)")


def parse_attachment_lines(text: str) -> list[dict[str, str]]:
    """Pull `[name](url)` links (and optional `| label`) out of a textarea.

    The Issue Form's `pdf` and `supplementary` fields ask the user to
    drag PDFs into a textarea, which GitHub auto-rewrites as
    `[file.pdf](https://github.com/user-attachments/...)` markdown
    links. We extract those links, plus any text after a pipe on the
    same line as a human-readable label.

    Returns a list of `{"name": ..., "url": ..., "label": ...}` dicts.
    `label` is `""` if the user didn't supply one.
    """
    out: list[dict[str, str]] = []
    if not text:
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _LINK_RE.search(line)
        if not m:
            continue
        name = m.group(1).strip()
        url = m.group(2).strip()
        # Anything after a pipe (anywhere in the line) is the label.
        label = ""
        if "|" in line:
            label = line.split("|", 1)[1].strip()
        out.append({"name": name, "url": url, "label": label})
    return out


def download_pdf(url: str, dest: Path, token: str | None) -> None:
    """Fetch `url` to `dest` using `Authorization: token <token>` if available.

    GitHub's user-attachments CDN serves private-repo files only with
    a valid token; without one (e.g. in a local dry-run) we still try
    the fetch unauthenticated and let the caller deal with the
    HTTPError if it's a 404.
    """
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "gking-site-intake-bot/1.0")
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.read())


def kind_from_field(value: str) -> str:
    """Map the dropdown selection to an intake subfolder ('', 'talk', 'book')."""
    key = (value or "").strip().lower()
    return KIND_TO_FOLDER.get(key, "")


def patch_index_md(
    md_path: Path,
    *,
    short_url: str | None,
    supplementary: list[dict[str, str]],
) -> None:
    """Add `aliases:` and supplementary `links:` entries to a freshly-written index.md.

    `intake_publication.run(...)` writes the file via `_yaml_dump` and
    we want to keep the same field ordering, so we re-parse the YAML,
    inject the new keys, and re-dump.
    """
    import yaml  # noqa: PLC0415 — keep the import close to the use site

    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    end = text.find("\n---", 3)
    if end == -1:
        return
    fm_text = text[3:end].lstrip("\n")
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    fm: dict[str, Any] = yaml.safe_load(fm_text) or {}

    if short_url:
        clean = short_url.strip().strip("/")
        if clean:
            alias = f"/{clean}/"
            existing_aliases = fm.get("aliases") or []
            if not isinstance(existing_aliases, list):
                existing_aliases = [existing_aliases]
            if alias not in existing_aliases:
                existing_aliases.append(alias)
            fm["aliases"] = existing_aliases

    if supplementary:
        existing_links = fm.get("links") or []
        if not isinstance(existing_links, list):
            existing_links = []
        for s in supplementary:
            url = s.get("path") or s.get("url") or ""
            if not url:
                continue
            label = s.get("label") or s.get("name") or "Supplementary Material"
            existing_links.append({"name": label, "url": url})
        fm["links"] = existing_links

    rendered = "---\n" + _intake._yaml_dump(fm) + "---\n"
    if body:
        rendered += body if body.startswith("\n") else "\n" + body
    md_path.write_text(rendered, encoding="utf-8")


def slugify_for_branch(slug: str, issue_number: int) -> str:
    safe = re.sub(r"[^a-z0-9-]", "-", (slug or "intake").lower()).strip("-")
    if len(safe) > 60:
        safe = safe[:60].rstrip("-")
    return f"intake/issue-{issue_number}-{safe or 'paper'}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--body", type=Path, required=True,
                    help="File containing the issue body")
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""),
                    help="GITHUB_TOKEN for downloading user-attachments PDFs")
    ap.add_argument("--owner", default="iqss-research")
    ap.add_argument("--repo", default="gking-site")
    ap.add_argument("--report-out", type=Path, required=True,
                    help="Where to write the intake JSON report")
    ap.add_argument("--pr-body-out", type=Path, required=True,
                    help="Where to write the rendered PR body markdown")
    ap.add_argument("--branch-out", type=Path, required=True,
                    help="Where to write the desired branch name")
    args = ap.parse_args()

    body_text = args.body.read_text(encoding="utf-8")
    fields = parse_issue_body(body_text)

    kind_label = fields.get("type", "") or fields.get("kind", "")
    folder = kind_from_field(kind_label)

    main_pdfs = parse_attachment_lines(fields.get("main-pdf", ""))
    if not main_pdfs:
        print(
            f"::error::Issue body does not contain a main PDF link. "
            f"Fields parsed: {sorted(fields.keys())}",
            file=sys.stderr,
        )
        return 2
    main_pdf = main_pdfs[0]

    intake_dir = ROOT / "_automation" / "intake"
    if folder:
        intake_dir = intake_dir / folder
    intake_dir.mkdir(parents=True, exist_ok=True)

    raw_name = main_pdf.get("name") or "paper.pdf"
    raw_name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw_name).strip("-")
    if not raw_name.lower().endswith(".pdf"):
        raw_name = raw_name + ".pdf"
    target = intake_dir / raw_name
    if target.exists():
        # Disambiguate to avoid overwriting another in-flight intake.
        for i in range(2, 50):
            cand = intake_dir / f"{Path(raw_name).stem}-{i}.pdf"
            if not cand.exists():
                target = cand
                break

    print(f"Downloading {main_pdf['url']} -> {target}", file=sys.stderr)
    try:
        download_pdf(main_pdf["url"], target, args.token)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"::error::Failed to download main PDF: {e}", file=sys.stderr)
        return 3

    # 1) Run the existing pipeline. This moves target -> _site/static/files/<slug>.pdf
    #    and writes EditMe/Writings/<slug>/index.md (or EditMe/Writings/Presentations/<slug>/).
    report = _intake.run(target, dry_run=False)
    slug = report["slug"]
    intake_kind = report["intake_kind"]

    # 2) Save supplementary PDFs to static/files/<slug>-supplement-<N>.pdf and
    #    record them so we can patch the new index.md and surface them in the
    #    PR body.
    supplementary_inputs = parse_attachment_lines(
        fields.get("supplementary-materials", "") or fields.get("supplementary", "")
    )
    supplementary_records: list[dict[str, str]] = []
    static_files = ROOT / "_site" / "static" / "files"
    static_files.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(supplementary_inputs, start=1):
        name = s.get("name") or f"supplement-{i}.pdf"
        ext = Path(name).suffix or ".pdf"
        dest_name = f"{slug}-supplement-{i}{ext}"
        dest = static_files / dest_name
        try:
            download_pdf(s["url"], dest, args.token)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"::warning::Failed to download supplementary {s['url']}: {e}",
                  file=sys.stderr)
            continue
        supplementary_records.append({
            "label": s.get("label") or "Supplementary Material",
            "name": name,
            "path": f"files/{dest_name}",
            "url": s["url"],
        })

    # 3) Patch index.md with aliases + supplementary links.
    short_url = (fields.get("short-url") or "").strip()
    md_path = ROOT / report["target_index_md"]
    patch_index_md(
        md_path,
        short_url=short_url,
        supplementary=supplementary_records,
    )

    # 4) Render every figure from the moved PDF into the page directory.
    pdf_path = ROOT / report["target_pdf"]
    figures_dir = md_path.parent / "_intake_figures"
    figures = _figs.extract_all_figures(pdf_path, figures_dir)
    report["figure_count"] = len(figures)

    # 5) Write the intake report (with extra fields the PR-body builder uses).
    report["short_url"] = short_url
    report["supplementary"] = supplementary_records
    report["notes"] = fields.get("notes-optional", "") or fields.get("notes", "")
    report["issue_number"] = args.issue

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 6) Decide the branch name and write it.
    branch = slugify_for_branch(slug, args.issue)
    args.branch_out.parent.mkdir(parents=True, exist_ok=True)
    args.branch_out.write_text(branch + "\n", encoding="utf-8")

    # 7) Render the PR body.
    abstract_full = ""
    rendered_fm = report.get("rendered_front_matter") or ""
    # Re-extract the abstract straight from the YAML so the PR body
    # shows the full prose, not the truncated count.
    try:
        import yaml as _yaml
        if md_path.is_file():
            text = md_path.read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("\n---", 3)
                if end != -1:
                    fm = _yaml.safe_load(text[3:end].lstrip("\n")) or {}
                    abstract_full = (fm.get("abstract") or "").strip()
    except Exception:
        pass
    if abstract_full:
        report["abstract_full"] = abstract_full

    pr_body = _body.render_pr_body(
        report,
        figures or None,
        owner=args.owner,
        repo=args.repo,
        branch=branch,
        issue_number=args.issue,
        short_url=short_url or None,
        supplementary=supplementary_records or None,
        notes=report["notes"] or None,
    )
    args.pr_body_out.parent.mkdir(parents=True, exist_ok=True)
    args.pr_body_out.write_text(pr_body, encoding="utf-8")

    print(json.dumps({
        "slug": slug,
        "branch": branch,
        "intake_kind": intake_kind,
        "figure_count": len(figures),
        "supplementary_count": len(supplementary_records),
        "target_index_md": report["target_index_md"],
        "target_pdf": report["target_pdf"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
