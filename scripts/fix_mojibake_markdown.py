#!/usr/bin/env python3
"""
Fix UTF-8 mojibake in markdown (smart quotes, en dashes, NBSP) stored as Latin-1
by applying ftfy, then normalizing non-breaking spaces to regular spaces in prose.
Requires: pip install ftfy (see scripts/requirements-mojibake.txt)

If a title: '...' field in front matter contained typographic quotes, ftfy may
convert them to ASCII apostrophes and break YAML (unmatched single quotes). In
that case, change the title to use double quotes, e.g.
  title: "Who's to Blame for …"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import ftfy
except ImportError:
    print("Install ftfy: pip install ftfy", file=sys.stderr)
    sys.exit(1)


def fix_text(s: str) -> str:
    t = ftfy.fix_text(s)
    t = t.replace("\u00a0", " ")
    # Collapse runs of 2+ spaces between non-whitespace (e.g. after ".  " mojibake fix)
    t = re.sub(r"(?<=\S) {2,}(?=\S)", " ", t)
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files (default: content/**/*.md under hugo site root)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write changes (default is dry run)",
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Hugo site root (parent of content/)",
    )
    args = ap.parse_args()
    root: Path = args.root

    if args.paths:
        files = [p for p in args.paths if p.suffix == ".md"]
    else:
        files = sorted((root / "content").rglob("*.md"))

    changed = 0
    for path in files:
        path = path.resolve()
        raw = path.read_text(encoding="utf-8")
        fixed = fix_text(raw)
        if fixed == raw:
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        print(f"fix: {rel}")
        if args.apply:
            path.write_text(fixed, encoding="utf-8", newline="\n")
        changed += 1

    print(f"Done. {changed} file(s) need fixes ({'applied' if args.apply else 'dry run'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
