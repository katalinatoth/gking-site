#!/usr/bin/env python3
"""Bulk-rename publication folders to match their Hugo public URL slugs.

Renames ~286 folders whose names diverge from what Hugo publishes as the
:slug, updating all folder-keyed data files and cross-references in one
atomic pass.

Usage:
    python3 _automation/scripts/rename_writings_folders.py              # dry-run (default)
    python3 _automation/scripts/rename_writings_folders.py --apply      # execute renames
    python3 _automation/scripts/rename_writings_folders.py --skip-presentations  # skip talk mounts
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_automation" / "lib"))
from slug import public_slug  # noqa: E402

WRITINGS_DIR = ROOT / "EditMe" / "Writings"
DATA_DIR = WRITINGS_DIR / "Data"
LEGACY_MAP = DATA_DIR / "writings_legacy_map.json"
FIRST_COMMIT = DATA_DIR / "publication_first_commit.json"
FEATURED = DATA_DIR / "featured_publications.yaml"
HUGO_YAML = ROOT / "hugo.yaml"
STATIC_FILES = ROOT / "_site" / "static" / "files"


def _git_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uno"], capture_output=True, text=True, cwd=ROOT
    )
    return bool(result.stdout.strip())


def _extract_title(md_path: Path) -> str | None:
    text = md_path.read_text(encoding="utf-8")[:5000]
    m = re.search(r'^title:\s*"(.+?)"\s*$', text, re.M)
    if not m:
        m = re.search(r"^title:\s*'(.+?)'\s*$", text, re.M)
    if not m:
        m = re.search(r"^title:\s*(.+?)\s*$", text, re.M)
    return m.group(1).strip() if m else None


def _extract_explicit_slug(md_path: Path) -> str | None:
    text = md_path.read_text(encoding="utf-8")[:5000]
    m = re.search(r'^slug:\s*"?([^"\n]+)"?\s*$', text, re.M)
    return m.group(1).strip() if m else None


def _find_mismatches(skip_presentations: bool = False) -> list[dict]:
    mismatches = []
    for md in sorted(WRITINGS_DIR.rglob("index.md")):
        if md.parent.name == "Data":
            continue
        if skip_presentations and "Presentations" in str(md):
            continue
        folder = md.parent.name
        title = _extract_title(md)
        if not title:
            continue
        explicit = _extract_explicit_slug(md)
        expected = explicit if explicit else public_slug(title)
        if folder != expected:
            mismatches.append({
                "folder": folder,
                "expected": expected,
                "dir": md.parent,
                "md": md,
                "is_presentation": "Presentations" in str(md),
            })
    return mismatches


def _add_slug_to_frontmatter(md_path: Path, slug_value: str) -> None:
    """Insert slug: field after title: in front matter if not already present."""
    text = md_path.read_text(encoding="utf-8")
    if re.search(r"^slug:", text, re.M):
        return
    text = re.sub(
        r'^(title:\s*.+)$',
        rf'\1\nslug: "{slug_value}"',
        text,
        count=1,
        flags=re.M,
    )
    md_path.write_text(text, encoding="utf-8")


def _update_legacy_map(renames: dict[str, str]) -> None:
    if not LEGACY_MAP.exists():
        return
    data = json.loads(LEGACY_MAP.read_text(encoding="utf-8"))
    entries = data.get("entries", {})
    new_entries = {}
    for key, val in entries.items():
        new_key = renames.get(key, key)
        new_entries[new_key] = val
    data["entries"] = new_entries
    LEGACY_MAP.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _update_first_commit(renames: dict[str, str]) -> None:
    if not FIRST_COMMIT.exists():
        return
    data = json.loads(FIRST_COMMIT.read_text(encoding="utf-8"))
    new_data = {}
    for key, val in data.items():
        new_key = renames.get(key, key)
        new_data[new_key] = val
    FIRST_COMMIT.write_text(json.dumps(new_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _update_featured(renames: dict[str, str]) -> None:
    if not FEATURED.exists():
        return
    text = FEATURED.read_text(encoding="utf-8")
    for old, new in renames.items():
        text = text.replace(f"  - {old}\n", f"  - {new}\n")
        text = text.replace(f"- {old}\n", f"- {new}\n")
    FEATURED.write_text(text, encoding="utf-8")


def _update_hugo_yaml_mounts(renames: dict[str, str]) -> None:
    """Update presentation mount paths in hugo.yaml.

    Uses regex with a trailing comma/whitespace boundary to avoid partial
    matches where one folder name is a prefix of another.
    """
    if not HUGO_YAML.exists():
        return
    text = HUGO_YAML.read_text(encoding="utf-8")
    for old, new in sorted(renames.items(), key=lambda x: -len(x[0])):
        text = re.sub(
            rf"Presentations/{re.escape(old)}(\s*,)",
            rf"Presentations/{new}\1",
            text,
        )
    HUGO_YAML.write_text(text, encoding="utf-8")


def _update_related_refs(renames: dict[str, str]) -> None:
    """Update related_paper/related_papers/see_also slug references.

    Uses regex with boundary assertions to avoid partial matches.
    """
    for md in WRITINGS_DIR.rglob("index.md"):
        if md.parent.name == "Data":
            continue
        text = md.read_text(encoding="utf-8")
        changed = False
        for old, new in sorted(renames.items(), key=lambda x: -len(x[0])):
            if old in text:
                new_text = re.sub(
                    rf'related_paper:\s*"{re.escape(old)}"',
                    f'related_paper: "{new}"',
                    text,
                )
                new_text = re.sub(
                    rf"related_paper:\s*{re.escape(old)}$",
                    f"related_paper: {new}",
                    new_text,
                    flags=re.M,
                )
                new_text = re.sub(
                    rf"^(\s*-\s*){re.escape(old)}$",
                    rf"\1{new}",
                    new_text,
                    flags=re.M,
                )
                if new_text != text:
                    text = new_text
                    changed = True
        if changed:
            md.write_text(text, encoding="utf-8")


def _update_relrefs(renames: dict[str, str]) -> None:
    """Update Hugo relref shortcodes across all content files.

    Handles patterns like: {{< relref "/publication/old-slug" >}}
    """
    editme = ROOT / "EditMe"
    for md in editme.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        changed = False
        for old, new in sorted(renames.items(), key=lambda x: -len(x[0])):
            if old in text:
                new_text = re.sub(
                    rf'(relref\s+"/[^"]*?/){re.escape(old)}(")',
                    rf"\1{new}\2",
                    text,
                )
                if new_text != text:
                    text = new_text
                    changed = True
        if changed:
            md.write_text(text, encoding="utf-8")


def _rename_pdfs(renames: dict[str, str]) -> list[str]:
    """Rename PDFs in _site/static/files/ that match old folder names."""
    moved = []
    if not STATIC_FILES.is_dir():
        return moved
    for old, new in renames.items():
        old_pdf = STATIC_FILES / f"{old}.pdf"
        if old_pdf.exists():
            new_pdf = STATIC_FILES / f"{new}.pdf"
            subprocess.run(["git", "mv", str(old_pdf), str(new_pdf)], cwd=ROOT)
            moved.append(f"{old}.pdf -> {new}.pdf")
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Execute renames (default is dry-run)")
    parser.add_argument("--skip-presentations", action="store_true",
                        help="Skip presentations (they have complex mount patterns)")
    args = parser.parse_args()

    if args.apply and _git_dirty():
        print("ERROR: Working tree has uncommitted changes. Commit or stash first.", file=sys.stderr)
        return 1

    mismatches = _find_mismatches(skip_presentations=args.skip_presentations)
    if not mismatches:
        print("No mismatches found. All folders match their public slugs.")
        return 0

    renames: dict[str, str] = {}
    git_moves: list[tuple[Path, Path]] = []

    for m in mismatches:
        old_folder = m["folder"]
        new_folder = m["expected"]
        old_dir = m["dir"]
        new_dir = old_dir.parent / new_folder

        if new_dir.exists():
            print(f"  SKIP (target exists): {old_folder} -> {new_folder}", file=sys.stderr)
            continue

        renames[old_folder] = new_folder
        git_moves.append((old_dir, new_dir))

    pres_renames = {old: new for old, new in renames.items()
                    if any(m["folder"] == old and m["is_presentation"] for m in mismatches)}

    print(f"{'DRY RUN' if not args.apply else 'APPLYING'}: {len(renames)} renames")
    print(f"  ({len(pres_renames)} are presentations with hugo.yaml mounts)")

    if not args.apply:
        for old, new in sorted(renames.items()):
            print(f"  {old}")
            print(f"    -> {new}")
        print(f"\nRun with --apply to execute.")
        return 0

    print("Renaming folders...")
    for old_dir, new_dir in git_moves:
        subprocess.run(["git", "mv", str(old_dir), str(new_dir)], cwd=ROOT, check=True)

    print("Updating writings_legacy_map.json...")
    _update_legacy_map(renames)

    print("Updating publication_first_commit.json...")
    _update_first_commit(renames)

    print("Updating featured_publications.yaml...")
    _update_featured(renames)

    if pres_renames:
        print("Updating hugo.yaml presentation mounts...")
        _update_hugo_yaml_mounts(pres_renames)

    print("Updating related_paper/related_papers/see_also references...")
    _update_related_refs(renames)

    print("Updating relref shortcodes...")
    _update_relrefs(renames)

    print("Adding slug: to front matter of renamed pages...")
    for m in mismatches:
        if m["folder"] in renames:
            new_dir = m["dir"].parent / renames[m["folder"]]
            new_md = new_dir / "index.md"
            if new_md.exists():
                _add_slug_to_frontmatter(new_md, renames[m["folder"]])

    print("Renaming PDFs...")
    pdf_moves = _rename_pdfs(renames)
    for pm in pdf_moves:
        print(f"  {pm}")

    print(f"\nDone. {len(renames)} folders renamed.")
    print("Next steps:")
    print("  1. git add -A && git status  (review changes)")
    print("  2. hugo  (verify build)")
    print("  3. git commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
