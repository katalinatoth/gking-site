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

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def die(msg: str) -> None:
    print(f"[build_redirects] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def existing_top_level_slugs() -> set[str]:
    """Slugs currently owned by something else in content/.

    We only guard against direct collisions with existing top-level
    directories or single-file pages (e.g. content/bio/, content/apply/).
    Section-internal slugs like /publication/foo/ are fine.
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


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    entries = load_entries()
    if not entries:
        print("[build_redirects] no redirects defined; nothing to do.")
        return 0

    existing = existing_top_level_slugs()
    seen: set[str] = set()
    OUT_DIR.mkdir(parents=True)

    for entry in entries:
        slug = str(entry.get("from", "")).strip().strip("/").lower()
        target = str(entry.get("to", "")).strip()
        note = str(entry.get("note", "") or "")

        if not slug:
            die("An entry is missing its `from` value.")
        if not target:
            die(f"Entry `{slug}` is missing its `to` value.")
        if not SLUG_RE.match(slug):
            die(
                f"Entry `from: {slug}` is invalid. Use lowercase letters, "
                "digits, and dashes only (no slashes, no spaces)."
            )
        if slug in seen:
            die(f"Duplicate `from: {slug}` in data/redirects.yaml.")
        if slug in existing:
            die(
                f"Entry `from: {slug}` collides with an existing page "
                f"content/{slug}/ — pick a different short URL."
            )
        seen.add(slug)

        page_dir = OUT_DIR / slug
        page_dir.mkdir()
        (page_dir / "index.md").write_text(
            f"""---
title: "Redirect to {yaml_quote(target)}"
url: /{slug}/
layout: redirect
target_url: "{yaml_quote(target)}"
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

    print(
        f"[build_redirects] generated {len(seen)} redirect stub(s) in "
        f"{OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
