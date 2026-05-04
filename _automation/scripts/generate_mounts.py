#!/usr/bin/env python3
"""Generate the module.mounts block in hugo.yaml from EditMe/ structure.

Walks EditMe/ and emits one mount per directory that contains page
bundles, plus per-section layout/data mounts. Replaces the contents
between the BEGIN AUTO-GENERATED / END AUTO-GENERATED markers in
hugo.yaml.

Usage:
    python3 _automation/scripts/generate_mounts.py            # update hugo.yaml in place
    python3 _automation/scripts/generate_mounts.py --check    # exit 1 if hugo.yaml is stale
    python3 _automation/scripts/generate_mounts.py --print    # print to stdout, don't touch hugo.yaml

Run after adding or removing folders under EditMe/. The deploy workflow
runs this with --check to catch drift between EditMe/ and the committed
hugo.yaml mounts block.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]  # _automation/scripts/<this> -> _automation/scripts -> _automation -> repo root
EDITME = ROOT / "EditMe"
HUGO_YAML = ROOT / "hugo.yaml"

BEGIN_MARKER = "# === BEGIN AUTO-GENERATED MOUNTS (run _automation/scripts/generate_mounts.py) ==="
END_MARKER = "# === END AUTO-GENERATED MOUNTS ==="

# ---------------------------------------------------------------------------
# Section tables. Each entry says: (relative_path_in_repo, hugo_target_path).
#
# CONTENT_SHALLOW: sections where one EditMe folder maps to one Hugo target.
# CONTENT_DEEP:    sections where leaf folders inside EditMe each map to
#                  the same Hugo target (used for Writings/Articles where
#                  papers nest inside topic/decade folders, and for
#                  Writings/Presentations where talks nest inside title
#                  folders).
# LAYOUTS:         per-section layout overrides under EditMe/UI/PerSectionLayouts/.
# DATA:            data files inside EditMe/<Section>/Data/ that get merged
#                  into Hugo's site.Data tree.
# ---------------------------------------------------------------------------

CONTENT_SHALLOW = [
    ("HomePage",           "content"),
    ("Bio",                "content/bio"),
    ("Misc",               "content"),
    ("Blog",               "content/blog"),
    ("ResearchAreas",      "content/research-areas"),
    ("Software",           "content/software"),
    ("Dataverse",          "content/dataverse"),
    ("People/ResearchGroup", "content/research-group"),
    ("People/Profiles",    "content/people"),
    ("People/Authors",     "content/authors"),
    ("Teaching",           "content/teaching"),
    ("Contact",            "content/contact"),
    ("Redirects/content",  "content/_redirects"),
]

# For deep sections, the script walks the EditMe sub-tree and emits one
# mount per directory that DIRECTLY CONTAINS page-bundle subdirectories
# (i.e., subdirectories that have an index.md or _index.md inside).
CONTENT_DEEP = [
    ("Writings/Articles",      "content/publication"),
    ("Writings/Books",         "content/publication"),
    ("Writings/Reports",       "content/publication"),
    ("Writings/Patents",       "content/publication"),
    ("Writings/CourtBriefs",   "content/publication"),
    ("Writings/Presentations", "content/talk"),
]

LAYOUTS = [
    ("UI/PerSectionLayouts/Bio",             "layouts/bio"),
    ("UI/PerSectionLayouts/Blog",            "layouts/blog"),
    ("UI/PerSectionLayouts/Contact",         "layouts/contact"),
    ("UI/PerSectionLayouts/Dataverse",       "layouts/dataverse"),
    ("UI/PerSectionLayouts/HomePage",        "layouts"),
    ("UI/PerSectionLayouts/People",          "layouts/people"),
    ("UI/PerSectionLayouts/ResearchAreas",   "layouts/research-areas"),
    ("UI/PerSectionLayouts/ResearchGroup",   "layouts/research-group"),
    ("UI/PerSectionLayouts/Software",        "layouts/software"),
    ("UI/PerSectionLayouts/Talks",           "layouts/talk"),
    ("UI/PerSectionLayouts/Teaching",        "layouts/teaching"),
    ("UI/PerSectionLayouts/TeachingClass",   "layouts/teaching-class"),
    ("UI/PerSectionLayouts/Writings",        "layouts/publication"),
]

DATA_DIRS = [
    "Writings/Data",
    "Software/Data",
    "Dataverse/Data",
    "People/Data",
    "ResearchAreas/Data",
    "Redirects/Data",
]

# ---------------------------------------------------------------------------
# Legacy fallback. Until move-content commits land, EditMe is mostly empty
# and content still lives at the legacy paths from PR #10's section-driven
# reorg. The script falls back to those paths when EditMe doesn't have the
# corresponding folder yet, so the build keeps working through the migration.
# ---------------------------------------------------------------------------

LEGACY_FALLBACKS = {
    "EditMe/HomePage":           "home/content",
    "EditMe/Misc":               "pages/content",
    "EditMe/Bio":                "bio/content",
    "EditMe/Blog":               "blog/content",
    "EditMe/ResearchAreas":      "research-areas/content",
    "EditMe/Software":           "software/content",
    "EditMe/Dataverse":          "dataverse/content",
    "EditMe/People/ResearchGroup": "people/content/group",
    "EditMe/People/Profiles":    "people/content/profiles",
    "EditMe/People/Authors":     "people/content/authors",
    "EditMe/Teaching":           "teaching/content",
    "EditMe/Contact":            "contact/content",
    "EditMe/Redirects/content":  "redirects/content",

    # deep sections fall back to the flat legacy folders
    "EditMe/Writings/Articles":      "writings/content",
    "EditMe/Writings/Books":         None,    # legacy folds books into writings/content
    "EditMe/Writings/Reports":       None,
    "EditMe/Writings/Patents":       None,
    "EditMe/Writings/CourtBriefs":   None,
    "EditMe/Writings/Presentations": "talks/content",

    # layouts
    "EditMe/UI/PerSectionLayouts/Bio":           "bio/layouts",
    "EditMe/UI/PerSectionLayouts/Blog":          "blog/layouts",
    "EditMe/UI/PerSectionLayouts/Contact":       "contact/layouts",
    "EditMe/UI/PerSectionLayouts/Dataverse":     "dataverse/layouts",
    "EditMe/UI/PerSectionLayouts/HomePage":      "home/layouts",
    "EditMe/UI/PerSectionLayouts/People":        "people/layouts/people",
    "EditMe/UI/PerSectionLayouts/ResearchAreas": "research-areas/layouts",
    "EditMe/UI/PerSectionLayouts/ResearchGroup": "people/layouts/research-group",
    "EditMe/UI/PerSectionLayouts/Software":      "software/layouts",
    "EditMe/UI/PerSectionLayouts/Talks":         "talks/layouts",
    "EditMe/UI/PerSectionLayouts/Teaching":      "teaching/layouts/teaching",
    "EditMe/UI/PerSectionLayouts/TeachingClass": "teaching/layouts/teaching-class",
    "EditMe/UI/PerSectionLayouts/Writings":      "writings/layouts",

    # data
    "EditMe/Writings/Data":      "writings/data",
    "EditMe/Software/Data":      "software/data",
    "EditMe/Dataverse/Data":     "dataverse/data",
    "EditMe/People/Data":        "people/data",
    "EditMe/ResearchAreas/Data": "research-areas/data",
    "EditMe/Redirects/Data":     "redirects/data",
}


def has_real_content(path: Path) -> bool:
    """A folder is 'populated' if it contains at least one non-README, non-hidden file."""
    if not path.exists():
        return False
    for entry in path.rglob("*"):
        if entry.is_file():
            if entry.name.startswith("."):
                continue
            if entry.name.lower() == "readme.md":
                continue
            return True
    return False


def find_page_bundle_parents(root: Path) -> list[Path]:
    """Find directories that directly contain page-bundle subdirs.

    A page bundle is a directory containing index.md or _index.md.
    The "parent" of a page bundle is the directory immediately above it.
    Multiple page bundles under the same parent collapse to one mount.
    """
    if not root.exists():
        return []
    parents: set[Path] = set()
    for index_md in list(root.rglob("index.md")) + list(root.rglob("_index.md")):
        bundle = index_md.parent
        if bundle == root:
            # _index.md directly inside `root` means root itself is a bundle parent
            parents.add(root)
        else:
            parents.add(bundle.parent)
    return sorted(parents)


def resolve_source(editme_relpath: str) -> str | None:
    """Return the source path to mount for `editme_relpath`, or None if neither
    EditMe nor the legacy fallback exists."""
    editme_full = EDITME / editme_relpath
    if has_real_content(editme_full):
        return f"EditMe/{editme_relpath}"
    legacy_key = f"EditMe/{editme_relpath}"
    legacy = LEGACY_FALLBACKS.get(legacy_key)
    if legacy is None:
        return None
    legacy_full = ROOT / legacy
    if legacy_full.exists():
        return legacy
    return None


def build_mounts() -> list[tuple[str, str, str]]:
    """Compute the canonical list of mounts.

    Returns a list of (source, target, comment_label) triples.
    """
    mounts: list[tuple[str, str, str]] = []

    # 1. Shared layouts (always at root, never moves)
    mounts.append(("layouts", "layouts", "shared theme bits (pinned at root)"))

    # 2. Per-section layouts
    for editme_relpath, target in LAYOUTS:
        src = resolve_source(editme_relpath)
        if src:
            mounts.append((src, target, ""))

    # 3. Shallow content sections
    for editme_relpath, target in CONTENT_SHALLOW:
        src = resolve_source(editme_relpath)
        if src:
            mounts.append((src, target, ""))

    # 4. Deep content sections (one mount per page-bundle parent)
    for editme_relpath, target in CONTENT_DEEP:
        editme_full = EDITME / editme_relpath
        if editme_full.exists():
            parents = find_page_bundle_parents(editme_full)
            if parents:
                for p in parents:
                    rel = p.relative_to(ROOT).as_posix()
                    mounts.append((rel, target, ""))
                continue
        # fall back to legacy if EditMe is empty
        legacy = LEGACY_FALLBACKS.get(f"EditMe/{editme_relpath}")
        if legacy and (ROOT / legacy).exists():
            mounts.append((legacy, target, ""))

    # 5. Site-wide data (always at _site/data)
    mounts.append(("_site/data", "data", "cross-section data files"))

    # 6. Per-section data
    for editme_relpath in DATA_DIRS:
        src = resolve_source(editme_relpath)
        if src:
            mounts.append((src, "data", ""))

    # 7. Static, archetypes, i18n, assets (pinned at root)
    mounts.append(("assets", "assets", "pinned at root: HugoBlox theme uses fileExists"))
    mounts.append(("_site/static", "static", ""))
    mounts.append(("_site/archetypes", "archetypes", ""))
    mounts.append(("_site/i18n", "i18n", ""))

    return mounts


def render_block(mounts: list[tuple[str, str, str]]) -> str:
    """Render the mounts list as YAML lines, preserving 4-space indentation
    matching the rest of hugo.yaml's module: block."""
    lines = []
    src_width = max(len(s) for s, _, _ in mounts) + 1  # +1 for the comma
    for src, tgt, comment in mounts:
        # source field with comma, padded
        src_field = (src + ",").ljust(src_width)
        line = f"    - {{source: {src_field} target: {tgt}}}"
        if comment:
            line = f"{line:<70} # {comment}"
        lines.append(line)
    return "\n".join(lines)


def replace_block_in_hugo_yaml(new_block: str) -> tuple[str, str]:
    """Read hugo.yaml, replace the auto-generated block, return (old, new)."""
    text = HUGO_YAML.read_text()
    pattern = re.compile(
        rf"({re.escape(BEGIN_MARKER)})(.*?)({re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(
            f"hugo.yaml is missing the BEGIN/END markers. Add these two lines\n"
            f"around the existing mounts: list, then re-run.\n"
            f"  {BEGIN_MARKER}\n"
            f"  ... mounts go here ...\n"
            f"  {END_MARKER}"
        )
    new_text = pattern.sub(
        lambda m: f"{m.group(1)}\n{new_block}\n    {m.group(3)}",
        text,
    )
    return text, new_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if hugo.yaml mounts block is stale")
    parser.add_argument("--print", action="store_true", dest="just_print",
                        help="print generated block to stdout without touching hugo.yaml")
    args = parser.parse_args(argv)

    mounts = build_mounts()
    block = render_block(mounts)

    if args.just_print:
        print(block)
        return 0

    old, new = replace_block_in_hugo_yaml(block)

    if args.check:
        if old != new:
            print("hugo.yaml is out of sync with EditMe/. Run:", file=sys.stderr)
            print("  python3 _automation/scripts/generate_mounts.py", file=sys.stderr)
            return 1
        print("hugo.yaml mounts are up to date.")
        return 0

    if old == new:
        print("hugo.yaml is already up to date.")
        return 0

    HUGO_YAML.write_text(new)
    n = sum(1 for line in block.splitlines() if line.strip().startswith("-"))
    print(f"hugo.yaml updated: {n} mounts written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
