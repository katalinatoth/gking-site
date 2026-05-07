#!/usr/bin/env python3
"""Post-build rewrite: copy rendered HTML from target pages to short URL paths.

Run this AFTER `hugo build` (and after Pagefind indexing, to avoid
duplicating search entries).  For every internal redirect or Hugo alias,
it copies the fully rendered HTML from the target page's output path to
the short URL's output path.  The result is that GitHub Pages serves the
real page content at the short URL — no client-side redirect needed.

External targets (https://…) are left untouched; their meta-refresh
redirect stubs remain.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "[apply_rewrites] ERROR: PyYAML is required. "
        "Install with `pip install pyyaml`.",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DATA_FILE = ROOT / "data" / "redirects.yaml"
CONTENT_DIR = ROOT / "content"


def _strip(path: str) -> str:
    """Strip leading/trailing slashes."""
    return path.strip("/")


def _is_external(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


# ── redirects.yaml entries ──────────────────────────────────────────────

def _load_redirect_pairs() -> list[tuple[str, str]]:
    """Return (from_path, to_path) for internal entries in redirects.yaml."""
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open() as f:
        doc = yaml.safe_load(f) or {}
    entries = doc.get("redirects", []) or []
    pairs: list[tuple[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        from_raw = str(entry.get("from", "")).strip()
        to_raw = str(entry.get("to", "")).strip()
        if not from_raw or not to_raw or _is_external(to_raw):
            continue
        pairs.append((_strip(from_raw), _strip(to_raw)))
    return pairs


# ── Hugo aliases from content front matter ──────────────────────────────

_FM_RE = re.compile(r"\A---\n(.*?\n)---", re.DOTALL)


def _load_alias_pairs() -> list[tuple[str, str]]:
    """Scan content/ for Hugo aliases; return (alias_path, canon_path)."""
    if not CONTENT_DIR.exists():
        return []
    pairs: list[tuple[str, str]] = []
    for md in CONTENT_DIR.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _FM_RE.match(text)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        aliases = fm.get("aliases")
        if not aliases or not isinstance(aliases, list):
            continue

        canon = _canon_path(md, fm)
        for alias in aliases:
            alias_str = _strip(str(alias).split("#")[0])
            if alias_str:
                pairs.append((alias_str, canon))
    return pairs


def _canon_path(md: Path, fm: dict) -> str:
    """Derive the rendered output path for a content file.

    If the page sets an explicit `url:`, use that.  Otherwise infer from
    the file's location relative to content/ (matching Hugo's default
    permalink behaviour).
    """
    if fm.get("url"):
        return _strip(str(fm["url"]))
    rel = md.relative_to(CONTENT_DIR)
    parts = list(rel.parts)
    if parts[-1] in ("index.md", "_index.md"):
        return "/".join(parts[:-1])
    return "/".join(parts[:-1] + [parts[-1].removesuffix(".md")])


# ── copy logic ──────────────────────────────────────────────────────────

def _resolve_src(to_path: str) -> Path | None:
    """Find the rendered index.html for a given URL path in public/."""
    if not to_path:
        # Root page: public/index.html
        candidate = PUBLIC / "index.html"
        return candidate if candidate.exists() else None
    candidate = PUBLIC / to_path / "index.html"
    if candidate.exists():
        return candidate
    # Some Hugo outputs omit trailing-slash dirs (unlikely but safe)
    candidate = PUBLIC / (to_path + ".html")
    return candidate if candidate.exists() else None


def _apply(pairs: list[tuple[str, str]], label: str) -> tuple[int, int]:
    applied = skipped = 0
    for from_path, to_path in pairs:
        src = _resolve_src(to_path)
        if src is None:
            print(
                f"  [{label}] SKIP /{from_path}/ → /{to_path}/ "
                f"(target not found in public/)"
            )
            skipped += 1
            continue
        dst = PUBLIC / from_path / "index.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        applied += 1
    return applied, skipped


# ── main ────────────────────────────────────────────────────────────────

def main() -> int:
    if not PUBLIC.exists():
        print("[apply_rewrites] public/ not found — run `hugo` first.")
        return 1

    redirect_pairs = _load_redirect_pairs()
    alias_pairs = _load_alias_pairs()

    if not redirect_pairs and not alias_pairs:
        print("[apply_rewrites] nothing to rewrite.")
        return 0

    total_applied = total_skipped = 0

    if redirect_pairs:
        a, s = _apply(redirect_pairs, "redirect")
        total_applied += a
        total_skipped += s

    if alias_pairs:
        a, s = _apply(alias_pairs, "alias")
        total_applied += a
        total_skipped += s

    print(
        f"[apply_rewrites] {total_applied} page(s) rewritten, "
        f"{total_skipped} skipped."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
