#!/usr/bin/env python3
"""Generate Hugo content stubs from data/redirects.yaml.

For every entry `{ from: X, to: Y }` this writes a small content page at
`content/_redirects/X/index.md` with `url: /X/` and a `redirect` layout.
Hugo then renders that page as a meta-refresh HTML file pointing to `Y`.

The `content/_redirects/` directory is ignored by git and regenerated on
every build. Gary edits ONLY `data/redirects.yaml`; the CI workflow runs
this script before the Hugo build.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    print(
        "[build_redirects] ERROR: PyYAML is required. Install with "
        "`pip install pyyaml`.",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "redirects.yaml"
OUT_DIR = ROOT / "content" / "_redirects"
CONTENT_DIR = ROOT / "content"
NETLIFY_REDIRECTS_FILE = ROOT / "static" / "_redirects"

# A redirect `from` is a URL path with one or more segments, separated by `/`.
# Each segment must be alnum/dash/underscore/dot. We preserve case because the
# new site is case-sensitive (e.g. `/Gov2020/` and `/gov2020/` differ).
SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ALLOWED_STATUSES = {301, 302, 307, 308}
DEFAULT_STATUS = 301


def die(msg: str) -> None:
    print(f"[build_redirects] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def existing_top_level_slugs() -> set[str]:
    """Slugs currently owned by something else in content/.

    We only guard against direct collisions where a redirect's *single-segment*
    `from` would shadow an existing top-level page (e.g. content/bio/,
    content/apply/). Multi-segment redirect paths and section-internal
    paths like /publication/foo/ are fine.
    """
    slugs: set[str] = set()
    if not CONTENT_DIR.exists():
        return slugs
    for entry in CONTENT_DIR.iterdir():
        if entry.name.startswith("_"):
            continue
        if entry.is_dir():
            slugs.add(entry.name.lower())
        elif entry.name.endswith(".md"):
            slugs.add(entry.stem.lower())
    return slugs


def parse_path(raw: str, *, source_label: str = "from") -> str:
    """Normalize and validate a redirect `from`-path.

    Strips leading/trailing slashes and validates each segment. Returns the
    cleaned path (no leading slash, segments preserved). Multi-segment paths
    are allowed: `research-interests/methods/missing-data` is valid.
    Case is preserved.
    """
    cleaned = (raw or "").strip().lstrip("/").rstrip("/")
    if not cleaned:
        die(f"An entry has an empty `{source_label}` value.")
    for seg in cleaned.split("/"):
        if not SEGMENT_RE.match(seg):
            die(
                f"Path segment {seg!r} in `{source_label}: /{cleaned}/` is "
                f"invalid. Each segment must start with an alnum and contain "
                f"only letters, digits, dashes, underscores, or dots."
            )
    return cleaned


def yaml_quote(value: str) -> str:
    """Conservative YAML double-quoted string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def load_entries() -> list[dict]:
    if not DATA_FILE.exists():
        print(
            f"[build_redirects] {DATA_FILE.relative_to(ROOT)} not found; "
            f"nothing to do."
        )
        return []
    with DATA_FILE.open() as f:
        doc = yaml.safe_load(f) or {}
    entries = doc.get("redirects", doc if isinstance(doc, list) else []) or []
    if not isinstance(entries, list):
        die("`redirects:` must be a YAML list.")
    cleaned: list[dict] = []
    for raw in entries:
        if not isinstance(raw, dict):
            die(f"Every entry must be a mapping; got {raw!r}.")
        cleaned.append(raw)
    return cleaned


def parse_status(raw, slug: str) -> int:
    """Coerce a redirect entry's `status` value to one of the allowed codes."""
    if raw is None or raw == "":
        return DEFAULT_STATUS
    try:
        code = int(str(raw).strip())
    except (TypeError, ValueError):
        die(
            f"Entry `from: {slug}` has invalid `status: {raw!r}`. "
            f"Use one of {sorted(ALLOWED_STATUSES)}."
        )
    if code not in ALLOWED_STATUSES:
        die(
            f"Entry `from: {slug}` has unsupported `status: {code}`. "
            f"Use one of {sorted(ALLOWED_STATUSES)}."
        )
    return code


def write_netlify_redirects(rules: list[tuple[str, str, int]]) -> None:
    """Write a Netlify/Cloudflare-Pages style `_redirects` file.

    GitHub Pages ignores this file, but emitting it keeps the redirect
    table portable: a future migration to a host that honours `_redirects`
    will pick up the real HTTP status codes automatically.
    """
    NETLIFY_REDIRECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not rules:
        if NETLIFY_REDIRECTS_FILE.exists():
            NETLIFY_REDIRECTS_FILE.unlink()
        return
    lines = [
        "# Auto-generated by scripts/build_redirects.py from data/redirects.yaml.",
        "# Honoured by Netlify, Cloudflare Pages, etc. Ignored by GitHub Pages,",
        "# which serves the meta-refresh stubs in content/_redirects/ instead.",
        "",
    ]
    for path, target, status in rules:
        lines.append(f"/{path}/   {target}   {status}")
        lines.append(f"/{path}    {target}   {status}")
    NETLIFY_REDIRECTS_FILE.write_text("\n".join(lines) + "\n")


_HEADLESS_INTERMEDIATE = """---
title: ""
headless: true
sitemap:
  disable: true
robotsNoIndex: true
build:
  list: never
  render: never
---
"""


def ensure_intermediate_index(parent: Path) -> None:
    """Make sure every intermediate directory under content/_redirects/
    has a non-rendering `_index.md`.

    Without this, Hugo would auto-generate a section listing at e.g.
    `/research-interests/` once we put a redirect stub at
    `/research-interests/methods/missing-data/`. We don't want those
    listings to compete with real content.
    """
    if parent == OUT_DIR:
        return
    index = parent / "_index.md"
    if not index.exists():
        index.write_text(_HEADLESS_INTERMEDIATE)
    ensure_intermediate_index(parent.parent)


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    entries = load_entries()
    if not entries:
        write_netlify_redirects([])
        print("[build_redirects] no redirects defined; nothing to do.")
        return 0

    existing = existing_top_level_slugs()
    seen: set[str] = set()
    OUT_DIR.mkdir(parents=True)

    # Pre-pass: build the set of paths that are *parents* of other
    # redirects. For those, we must emit `_index.md` (a Hugo section
    # page), not `index.md` (a leaf bundle), or Hugo will treat the
    # whole directory as a leaf bundle and ignore its child redirects.
    all_paths = {parse_path(str(e.get("from", ""))) for e in entries}
    parents_of_other_redirects: set[str] = set()
    for p in all_paths:
        for q in all_paths:
            if p != q and q.startswith(p + "/"):
                parents_of_other_redirects.add(p)
                break
    # Suppress the section page itself: every redirect child sets its own
    # absolute `url:` (e.g. /quest/) so the synthetic section listing at
    # /_redirects/ is unwanted, and would also clash with the Netlify
    # `_redirects` file written into static/ below.
    (OUT_DIR / "_index.md").write_text(
        """---
title: "Redirects (internal)"
headless: true
sitemap:
  disable: true
robotsNoIndex: true
build:
  list: never
  render: never
---
"""
    )
    netlify_rules: list[tuple[str, str, int]] = []

    for entry in entries:
        path = parse_path(str(entry.get("from", "")))
        target = str(entry.get("to", "")).strip()
        note = str(entry.get("note", "") or "")
        status = parse_status(entry.get("status"), path or "<unknown>")

        if not target:
            die(f"Entry `from: /{path}/` is missing its `to` value.")
        # Normalize for duplicate detection (path is case-sensitive on
        # output, but `/Foo/` and `/Foo/` are still the same redirect).
        if path in seen:
            die(f"Duplicate `from: /{path}/` in data/redirects.yaml.")

        # Collision check: a single-segment redirect must not shadow an
        # existing top-level page. Multi-segment redirects are allowed to
        # nest under section directories (those are owned by Hugo's normal
        # content tree, but we don't write into them — we route via
        # content/_redirects/<segs>/index.md and an absolute `url:`).
        first_seg = path.split("/", 1)[0].lower()
        if "/" not in path and first_seg in existing:
            die(
                f"Entry `from: /{path}/` collides with an existing page "
                f"content/{first_seg}/ — pick a different short URL."
            )
        seen.add(path)
        netlify_rules.append((path, target, status))

        page_dir = OUT_DIR / path
        page_dir.mkdir(parents=True, exist_ok=True)
        ensure_intermediate_index(page_dir.parent)
        # If this path is a parent of another redirect, emit `_index.md`
        # (section page) so Hugo continues into child directories. Else
        # emit `index.md` (leaf bundle).
        is_parent = path in parents_of_other_redirects
        index_filename = "_index.md" if is_parent else "index.md"
        (page_dir / index_filename).write_text(
            f"""---
title: "Redirect to {yaml_quote(target)}"
url: /{path}/
layout: redirect
target_url: "{yaml_quote(target)}"
redirect_status: {status}
redirect_note: "{yaml_quote(note)}"
sitemap:
  disable: true
robotsNoIndex: true
build:
  list: never
  render: always
---
"""
        )

    write_netlify_redirects(netlify_rules)
    print(
        f"[build_redirects] generated {len(seen)} redirect stub(s) in "
        f"{OUT_DIR.relative_to(ROOT)} and {NETLIFY_REDIRECTS_FILE.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
