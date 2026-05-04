#!/usr/bin/env python3
"""Capture the first-commit date for every EditMe/Writings/ markdown.

Hugo's built-in .GitInfo only exposes the *latest* commit that touched a
file, which means editing a paper later (e.g. fixing a link) would bump
it to the top of any git-based ordering. For the "Current Working
Papers" spotlight we want "when was this paper added to the site" —
i.e. the file's *first* commit.

This script walks EditMe/Writings/*/index.md, asks git for each
file's earliest commit timestamp, and writes the result to
EditMe/Writings/Data/publication_first_commit.json as {slug: iso8601-date}.
Hugo reads that file to order the spotlight.

Run locally after adding a new paper to refresh the map; CI runs it
automatically before every build.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def first_commit_iso(repo_root: Path, rel_path: Path) -> str | None:
    """Return the ISO-8601 author date of the earliest commit that added rel_path.

    Uses --diff-filter=A so we only look at the addition commit (handles
    renames via --follow). Returns None if the file has never been
    committed (new local-only file).
    """

    try:
        out = subprocess.check_output(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--follow",
                "--format=%aI",
                "--",
                str(rel_path),
            ],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None

    if not out:
        return None
    return out.splitlines()[-1].strip()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    pub_dir = repo_root / "EditMe" / "Writings"
    out_path = repo_root / "EditMe" / "Writings" / "Data" / "publication_first_commit.json"

    if not pub_dir.is_dir():
        print(f"error: {pub_dir} not found", file=sys.stderr)
        return 1

    data: dict[str, str] = {}
    # Papers and talks are nested several levels deep under EditMe/Writings/
    # (e.g. Articles/<topic>/<decade>/<slug>/index.md, Presentations/<title>/<venue>/index.md).
    # rglob walks the whole tree; the bundle slug is the parent dir's name. We
    # skip the data/ side-tree and any README markers.
    for md in sorted(pub_dir.rglob("index.md")):
        bundle = md.parent
        try:
            rel_to_pub = bundle.relative_to(pub_dir)
        except ValueError:
            continue
        if rel_to_pub.parts and rel_to_pub.parts[0] in {"Data", "data"}:
            continue
        rel = md.relative_to(repo_root)
        iso = first_commit_iso(repo_root, rel)
        if iso:
            data[bundle.name] = iso

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"wrote {len(data)} entries to {out_path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
