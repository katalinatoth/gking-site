#!/usr/bin/env python3
"""Tier-1 fuzzy clustering for EditMe/Writings/Presentations/.

The first-pass clustering (regroup_presentations.py) groups talks whose
slugified title matches *exactly*. That misses cases like:

  - venue-in-parens variants:
      "Correcting Measurement Error Bias ... (Stanford University)"
      "Correcting Measurement Error Bias ... (Harvard Experiments WG)"
  - subtitle drift:
      "Big Data Is Not About the Data!"
      "Big Data Is Not About the Data, With Applications"
      "Big Data Is Not About the Data! The Power of Modern Analytics"
  - leading-verb drift:
      "Discovering and Explaining Systematic Bias ..."
      "Explaining Systematic Bias ..."
  - one-word swaps (e.g., "Numeric Data" ↔ "Quantitative Data")
  - morphological variants ("Censorship in China" ↔ "Chinese Censorship")

This script does a second pass over the existing
EditMe/Writings/Presentations/<title-slug>/<venue-slug>/ tree and proposes
merging title-slug folders whose titles are sufficiently similar.

Auto-merge signals (any one triggers a merge edge with score 1.0):

  1. **Base-title equality** — slugify(strip_parens(title_a)) ==
     slugify(strip_parens(title_b)). Catches the venue-in-parens case.
  2. **Prefix containment** — normalized one title is a strict word-prefix
     of the other, shorter has ≥ 3 normalized words.
  3. **Strict subset with bounded diff** — smaller's tokens ⊂ larger's
     tokens, smaller has ≥ 3 tokens, AND diff is ≤ 35% of the larger.
     Catches subset cases (Dataverse Intro ⊃ The Dataverse) without
     auto-merging "Detecting Model Dependence" ⊃ "Detecting and Reducing
     Model Dependence in Causal Inference" where the expansion is too
     large (3 of 6 tokens added — a different talk, not a rename).
  4. **Near-subset** — symmetric difference ≤ 2 AND min(|A|,|B|) ≥ 4.
     Catches one- or two-word swaps and morphological variants like
     "china" ↔ "chinese".

Plus plain **Jaccard ≥ --threshold** (default 0.60) as a softer signal.

To prevent topic-soup false positives, when the symmetric difference
between two token sets contains a "topic-prefix word" — generic talk-
style qualifiers like "introduction", "simplifying", "comparative",
"talks", "overview" — the auto-merge is blocked. This cleanly rejects
pairs like "Introduction to Matching" ↔ "Matching Methods" while still
catching pairs whose differing words are content-bearing
("nonexistent" ↔ "random", "numeric" ↔ "quantitative").

Tokens are lowercased, ASCII-only, alphanumeric, > 2 chars, and not in
the shared stopword list (matches layouts/_partials/related_finder.html).

Clustering is done in two tiers:

  - Tier 1 — **single-linkage union-find** on the strong auto-merge
    edges only (base-title eq, prefix, subset, near-subset). These
    signals are confident enough that transitivity is safe: if A is
    clearly an alias of B and B is clearly an alias of C, then A and C
    belong in the same cluster even if their direct pair score is low.
    This handles the "subtitle drift" case where A is the short title
    and B and C are two independent subtitle expansions.
  - Tier 2 — **complete-linkage agglomeration** on the soft Jaccard
    edges, growing the tier-1 clusters. A merge is only allowed when
    EVERY cross-cluster pair scores at or above threshold. This
    prevents transitive chaining like A↔B↔C through weak links.

Pairs that score below the auto-merge bar but above --review-threshold
(default 0.40) are listed in a "review band" section so you can decide
manually whether to merge them.

Manual overrides:

  - --exclude-pair SLUG_A SLUG_B  (repeatable) — never merge this pair.
  - --excludes-file PATH          — YAML/JSON of pairs to exclude;
    defaults to EditMe/Writings/Data/presentation_clustering_excludes.yaml
    when present.

Default mode is dry-run: no files are touched. The script writes a
human-readable report to EditMe/Writings/Data/presentation_clustering_report.md
and prints it to stdout.

Run with --apply to perform git-mv merges and re-run generate_mounts.py.

Usage:
  python3 _automation/scripts/regroup_presentations_fuzzy.py
  python3 _automation/scripts/regroup_presentations_fuzzy.py --threshold 0.65
  python3 _automation/scripts/regroup_presentations_fuzzy.py \
      --exclude-pair matching-methods-for-causal-inference \
                     simplifying-matching-methods-for-causal-inference
  python3 _automation/scripts/regroup_presentations_fuzzy.py --apply
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITME = ROOT / "EditMe"
PRES = EDITME / "Writings" / "Presentations"
DATA_DIR = EDITME / "Writings" / "Data"
REPORT_PATH = DATA_DIR / "presentation_clustering_report.md"
DEFAULT_EXCLUDES = DATA_DIR / "presentation_clustering_excludes.yaml"

# Same stopword list used by layouts/_partials/related_finder.html so the
# fuzzy clustering and the See-Also widget agree on what counts as a
# meaningful word.
STOPWORDS = {
    "a", "an", "and", "the", "of", "for", "in", "on", "to", "with", "by",
    "at", "as", "is", "are", "be", "or", "from", "into", "using", "via",
    "new", "not", "no", "it", "its", "we", "our", "their", "you", "your",
    "this", "that", "these", "those", "but", "if", "than", "then", "so",
    "can", "will", "would", "could", "should", "may", "might", "also",
    "more", "most", "some", "all", "any", "each", "every", "who", "whom",
    "which", "what", "when", "where", "why", "how", "about", "between",
    "among", "through", "over", "under", "after", "before", "upon",
    "across", "per", "vs", "de", "la", "les", "et", "du",
}

# Topic-prefix words. When the symmetric difference between two title
# token sets contains any of these words, both auto-merge and Jaccard
# clustering are suppressed for the pair. The differing word is a
# strong signal that the two are DIFFERENT talks on the same topic.
#
# This list is intentionally narrow. Words that often appear as filler
# in a longer rephrasing of the same talk (e.g., "introduction" in "An
# Introduction to X" vs "X: An Infrastructure for Y") are deliberately
# NOT included — they would block legitimate merges. Only words with a
# strong "this is a different version of the talk" signal go here:
#
#   - "simplifying" — Gary's renaming pattern for evolved talks; usually
#     marks a different talk than the unprefixed version
#   - "comparative" / "comparing" — "Comparative Effectiveness of X" is
#     usually a different methods-comparison talk than "X"
#   - "advanced" — "Advanced X" is usually a follow-up talk to "X"
#   - "introductory" — adjective form, signals beginner/tutorial track
#
# If you encounter a real-world merge that's incorrectly blocked, drop
# the offending word here OR use --exclude-pair on the false-merge it
# would otherwise create. We err on the side of merging too aggressively
# because the dry-run report makes false merges easy to spot.
TOPIC_PREFIX_WORDS = {
    "simplifying", "simplified",
    "comparative", "comparison", "comparing",
    "advanced",
    "introductory",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or "untitled"


def strip_parens(title: str) -> str:
    """Drop trailing parenthetical or bracketed venue/notes from a title."""
    out = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    out = re.sub(r"\s*\[[^\]]*\]\s*$", "", out).strip()
    return out


def normalize_for_prefix(title: str) -> str:
    """Lowercase, ASCII-only, collapse non-alphanumeric runs to single
    spaces. Result is a sequence of words separated by single spaces,
    suitable for word-prefix comparison."""
    s = unicodedata.normalize("NFKD", title)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def is_prefix_match(a: str, b: str, min_words: int = 3) -> bool:
    """True if normalize(a) is a strict word-prefix of normalize(b) or
    vice versa, and the shorter has >= min_words words."""
    na = normalize_for_prefix(a)
    nb = normalize_for_prefix(b)
    if not na or not nb or na == nb:
        return False
    short, long_ = (na, nb) if len(na) < len(nb) else (nb, na)
    if len(short.split()) < min_words:
        return False
    return long_.startswith(short + " ")


def tokenize(title: str) -> set[str]:
    s = unicodedata.normalize("NFKD", title)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    raw = re.split(r"[^a-z0-9]+", s)
    return {tok for tok in raw if len(tok) > 2 and tok not in STOPWORDS}


def extract_title(index_md: Path) -> str | None:
    text = index_md.read_text(errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fm = text[3:end]
    m = re.search(r"""^\s*title\s*:\s*['"]?(.+?)['"]?\s*$""", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


@dataclass
class TitleFolder:
    """One title-slug folder under EditMe/Writings/Presentations/."""

    slug: str
    path: Path
    venues: list[Path] = field(default_factory=list)
    title: str = ""
    base_title: str = ""
    base_slug: str = ""
    tokens: set[str] = field(default_factory=set)


def collect_title_folders() -> list[TitleFolder]:
    folders: list[TitleFolder] = []
    for child in sorted(PRES.iterdir()):
        if not child.is_dir():
            continue
        venues = sorted(p for p in child.iterdir() if p.is_dir())
        if not venues:
            continue
        rep_title = None
        for v in venues:
            idx = v / "index.md"
            if idx.exists():
                rep_title = extract_title(idx)
                if rep_title:
                    break
        if not rep_title:
            continue
        base = strip_parens(rep_title)
        folders.append(
            TitleFolder(
                slug=child.name,
                path=child,
                venues=venues,
                title=rep_title,
                base_title=base,
                base_slug=slugify(base),
                tokens=tokenize(base),
            )
        )
    return folders


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def has_topic_prefix_diff(a: set[str], b: set[str]) -> str | None:
    """Return the offending topic-prefix word in (A △ B), or None."""
    diff = a.symmetric_difference(b)
    for w in diff:
        if w in TOPIC_PREFIX_WORDS:
            return w
    return None


@dataclass
class PairResult:
    """Result of comparing two title folders.

    auto_merge=True means the pair has a strong-confidence signal
    (base-title eq / prefix / subset / near-subset) and should be
    single-linkage merged in tier 1.

    score is Jaccard regardless (0.0 if blocked or empty), used by the
    tier-2 complete-linkage agglomeration.

    blocked=True means a topic-prefix word in the symmetric difference
    suppressed both tiers; the pair will not merge.
    """

    auto_merge: bool
    score: float
    why: str
    blocked: bool = False


def pair_score(a: TitleFolder, b: TitleFolder) -> PairResult:
    """Compute a structured similarity result.

    Auto-merge signals (any one is sufficient):
      - base-title equality
      - prefix containment
      - strict subset with bounded diff (smaller ⊂ larger, diff ≤ 35%)
      - near-subset (symmetric difference ≤ 2, both ≥ 4 tokens)

    Topic-prefix-word block applies to ALL tiers: if any word in the
    symmetric difference is in TOPIC_PREFIX_WORDS, neither auto-merge
    nor Jaccard-tier merge is allowed. The differing word is usually a
    talk-style qualifier ("introduction", "simplifying", "comparative",
    "talks") that marks a DIFFERENT talk on the same topic.
    """
    if a.base_slug and a.base_slug == b.base_slug:
        return PairResult(True, 1.0, f"base-title match ('{a.base_title}')")
    if is_prefix_match(a.title, b.title):
        return PairResult(True, 1.0, "prefix containment")

    ta, tb = a.tokens, b.tokens
    inter = len(ta & tb)
    union = len(ta | tb)
    j = inter / union if union else 0.0
    sym_diff = len(ta ^ tb)
    smaller = min(len(ta), len(tb))
    larger = max(len(ta), len(tb))

    blocker = has_topic_prefix_diff(ta, tb)
    if blocker is not None:
        return PairResult(
            False, 0.0,
            f"BLOCKED by topic-prefix word '{blocker}' in symmetric "
            f"difference (raw Jaccard would have been {j:.2f})",
            blocked=True,
        )

    # Strict subset with bounded diff — only fires when smaller ⊂ larger
    # and the expansion is modest (≤ 35% of the larger title). Rejects
    # "Detecting Model Dependence" ⊃ "Detecting and Reducing Model
    # Dependence in Causal Inference" where diff/larger = 0.50.
    if (
        (ta <= tb or tb <= ta)
        and smaller >= 3
        and larger > 0
        and (larger - smaller) / larger <= 0.35
    ):
        return PairResult(
            True, 1.0,
            f"strict subset (|A∩B|={inter}, diff={larger - smaller}, "
            f"diff/larger={(larger - smaller) / larger:.2f})",
        )

    # Near-subset — small symmetric difference, both titles substantive.
    if sym_diff <= 2 and smaller >= 4:
        return PairResult(
            True, 1.0,
            f"near-subset (sym-diff={sym_diff}, min-tokens={smaller})",
        )

    return PairResult(False, j, f"Jaccard {j:.2f} (|A∩B|={inter}, |A∪B|={union})")


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[ry] = rx


def two_tier_cluster(
    n: int,
    score_matrix: dict[tuple[int, int], PairResult],
    threshold: float,
) -> list[list[int]]:
    """Two-tier clustering.

    Tier 1: union-find single-linkage on every pair where auto_merge is
    True. Strong signals (base-title eq, prefix, subset, near-subset)
    are transitively closed: if A is a clear alias of B and B is a
    clear alias of C, A and C end up in the same cluster even if A↔C
    direct score is low. This is what catches the multi-subtitle case
    "Big Data Is Not About the Data" + "...The Power of Modern
    Analytics" + "...With Applications", where A↔B and A↔C are both
    prefix matches but B↔C is unrelated.

    Tier 2: complete-linkage agglomeration on the resulting clusters,
    using the soft Jaccard score. A merge is only allowed when every
    pair across the two candidate clusters scores ≥ threshold AND no
    pair is blocked by the topic-prefix-word filter.
    """
    uf = UnionFind(n)
    for (i, j), pr in score_matrix.items():
        if pr.auto_merge:
            uf.union(i, j)
    by_root: dict[int, list[int]] = {}
    for i in range(n):
        by_root.setdefault(uf.find(i), []).append(i)
    clusters = list(by_root.values())

    def cross_min_jaccard(ca: list[int], cb: list[int]) -> float:
        worst = 1.0
        for a in ca:
            for b in cb:
                key = (min(a, b), max(a, b))
                pr = score_matrix.get(key)
                if pr is None or pr.blocked:
                    return 0.0
                if pr.score < worst:
                    worst = pr.score
        return worst

    while True:
        best_i = best_j = -1
        best_score = threshold - 1e-9
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                m = cross_min_jaccard(clusters[i], clusters[j])
                if m >= threshold and m > best_score:
                    best_score = m
                    best_i, best_j = i, j
        if best_i < 0:
            break
        clusters[best_i] = clusters[best_i] + clusters[best_j]
        del clusters[best_j]

    return [c for c in clusters if len(c) > 1]


def collect_review_pairs(
    score_matrix: dict[tuple[int, int], PairResult],
    lo: float,
    hi: float,
    in_cluster: set[int],
) -> list[tuple[int, int, float, str]]:
    """Pairs scoring in [lo, hi) that did NOT end up in a cluster."""
    out: list[tuple[int, int, float, str]] = []
    for (i, j), pr in score_matrix.items():
        if pr.blocked:
            continue
        if i in in_cluster and j in in_cluster:
            continue
        if lo <= pr.score < hi:
            out.append((i, j, pr.score, pr.why))
    out.sort(key=lambda t: -t[2])
    return out


def collect_blocked_pairs(
    score_matrix: dict[tuple[int, int], PairResult],
    min_jaccard_to_show: float = 0.50,
) -> list[tuple[int, int, str]]:
    """Pairs that the topic-prefix-word filter zeroed out, but whose raw
    Jaccard would have been suspiciously high. Useful so the user can
    spot real false-blocks."""
    out: list[tuple[int, int, str]] = []
    for (i, j), pr in score_matrix.items():
        if not pr.blocked:
            continue
        m = re.search(r"would have been ([\d.]+)", pr.why)
        if not m:
            continue
        if float(m.group(1)) >= min_jaccard_to_show:
            out.append((i, j, pr.why))
    return out


def pick_canonical(folders: list[TitleFolder], indices: list[int]) -> int:
    """Pick the cluster member to KEEP. Most venues wins; tiebreak by
    shortest slug; then alphabetical."""
    return min(
        indices,
        key=lambda i: (
            -len(folders[i].venues),
            len(folders[i].slug),
            folders[i].slug,
        ),
    )


def render_report(
    folders: list[TitleFolder],
    clusters: list[list[int]],
    score_matrix: dict[tuple[int, int], PairResult],
    review_pairs: list[tuple[int, int, float, str]],
    blocked_pairs: list[tuple[int, int, str]],
    threshold: float,
    review_threshold: float,
    excludes: set[frozenset[str]],
    apply_mode: bool,
) -> str:
    lines: list[str] = []
    lines.append("# Presentation Clustering Report")
    lines.append("")
    mode = "APPLIED" if apply_mode else "DRY RUN"
    lines.append(
        f"_Mode: **{mode}**, threshold: {threshold:.2f}, "
        f"review band: [{review_threshold:.2f}, {threshold:.2f})_"
    )
    lines.append("")
    n_folders = len(folders)
    n_clusters = len(clusters)
    n_merging = sum(len(c) - 1 for c in clusters)
    n_after = n_folders - n_merging
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Title-slug folders before: **{n_folders}**")
    lines.append(f"- Clusters merging ≥ 2 folders: **{n_clusters}**")
    lines.append(
        f"- Folders that would be removed (merged into a sibling): **{n_merging}**"
    )
    lines.append(f"- Title-slug folders after: **{n_after}**")
    if excludes:
        lines.append(f"- Manual `--exclude-pair` overrides honored: **{len(excludes)}**")
    lines.append("")

    lines.append("## Proposed clusters")
    lines.append("")
    if not clusters:
        lines.append("_No clusters above the threshold._")
        lines.append("")
    for ci, members in enumerate(clusters, start=1):
        canonical = pick_canonical(folders, members)
        lines.append(f"### Cluster {ci} — keeps `{folders[canonical].slug}/`")
        lines.append("")
        lines.append(f"- canonical title: `{folders[canonical].title}`")
        lines.append("- members:")
        for m in sorted(members, key=lambda i: (i != canonical, folders[i].slug)):
            tag = "**KEEP**" if m == canonical else "merge"
            n_v = len(folders[m].venues)
            lines.append(
                f"  - {tag} `{folders[m].slug}/` "
                f"({n_v} venue{'s' if n_v != 1 else ''}) "
                f"— `{folders[m].title}`"
            )
        cluster_set = set(members)
        cluster_edges = [
            ((i, j), score_matrix[(i, j)])
            for (i, j) in score_matrix
            if i in cluster_set and j in cluster_set
        ]
        if cluster_edges:
            lines.append("- evidence:")
            for (i, j), pr in cluster_edges:
                tag = "AUTO" if pr.auto_merge else "Jaccard"
                lines.append(
                    f"  - [{tag}] `{folders[i].slug}` ↔ `{folders[j].slug}` "
                    f"(score {pr.score:.2f}) — {pr.why}"
                )
        canon_path_rel = folders[canonical].path.relative_to(ROOT)
        existing = {p.name for p in folders[canonical].venues}
        any_move = False
        lines.append("- proposed moves:")
        for m in members:
            if m == canonical:
                continue
            for v in folders[m].venues:
                src = v.relative_to(ROOT)
                dst_name = v.name
                if dst_name in existing:
                    dst_name = f"{dst_name}--from-{folders[m].slug}"
                existing.add(dst_name)
                dst = canon_path_rel / dst_name
                lines.append(f"  - `{src}` → `{dst}`")
                any_move = True
        if not any_move:
            lines.append("  - _(none — only one folder in this cluster has venues)_")
        lines.append("")

    lines.append("## Review band (close-but-below threshold)")
    lines.append("")
    lines.append(
        f"_Pairs in [{review_threshold:.2f}, {threshold:.2f}) — not auto-merged. "
        "Eyeball these and use `--exclude-pair` to permanently reject "
        "false positives, or lower `--threshold` if you want them merged._"
    )
    lines.append("")
    if not review_pairs:
        lines.append("_(empty)_")
        lines.append("")
    else:
        for i, j, s, why in review_pairs:
            lines.append(
                f"- {s:.2f} — `{folders[i].slug}` vs `{folders[j].slug}` — {why}"
            )
            lines.append(f"    - A: `{folders[i].title}`")
            lines.append(f"    - B: `{folders[j].title}`")
        lines.append("")

    if blocked_pairs:
        words = ", ".join(f"`{w}`" for w in sorted(TOPIC_PREFIX_WORDS))
        lines.append("## Topic-prefix-word blocked pairs (high-Jaccard only)")
        lines.append("")
        lines.append(
            f"_These pairs had Jaccard ≥ 0.50 but the symmetric difference "
            f"contained a talk-style qualifier ({words}), so the merge was "
            "suppressed because the differing word usually marks a "
            "DIFFERENT talk on the same topic. If any of these are actually "
            "the same talk, override with `--exclude-pair` on the "
            "false-merge it would otherwise create, manually `git mv` the "
            "venue subfolders, or edit `TOPIC_PREFIX_WORDS` in the script._"
        )
        lines.append("")
        for i, j, why in blocked_pairs:
            lines.append(f"- `{folders[i].slug}` vs `{folders[j].slug}`")
            lines.append(f"    - A: `{folders[i].title}`")
            lines.append(f"    - B: `{folders[j].title}`")
            lines.append(f"    - reason: {why}")
        lines.append("")

    if excludes:
        lines.append("## Manual exclusions honored")
        lines.append("")
        for pair in sorted(map(sorted, excludes)):
            lines.append(f"- `{pair[0]}` ⊻ `{pair[1]}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def apply_moves(
    folders: list[TitleFolder], clusters: list[list[int]]
) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    for members in clusters:
        canonical = pick_canonical(folders, members)
        existing_names = {p.name for p in folders[canonical].venues}
        for m in members:
            if m == canonical:
                continue
            for v in folders[m].venues:
                dst_name = v.name
                if dst_name in existing_names:
                    dst_name = f"{dst_name}--from-{folders[m].slug}"
                existing_names.add(dst_name)
                dst = folders[canonical].path / dst_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "mv", str(v), str(dst)],
                    check=True,
                    cwd=ROOT,
                )
                moves.append((v, dst))
            try:
                if folders[m].path.exists() and not any(folders[m].path.iterdir()):
                    folders[m].path.rmdir()
            except OSError:
                pass
    return moves


def load_excludes_file(path: Path) -> set[frozenset[str]]:
    """Load --excludes-file. Accepts YAML or JSON with a list of {a, b}
    or {pair: [a, b]} entries. Falls back to an empty set if the file
    doesn't exist."""
    if not path.exists():
        return set()
    text = path.read_text()
    pairs: set[frozenset[str]] = set()
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
    except Exception:
        import json
        data = json.loads(text)
    if not data:
        return pairs
    for entry in data:
        if isinstance(entry, dict) and "pair" in entry:
            a, b = entry["pair"]
        elif isinstance(entry, dict) and "a" in entry and "b" in entry:
            a, b = entry["a"], entry["b"]
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            a, b = entry
        else:
            continue
        pairs.add(frozenset((str(a), str(b))))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--threshold", type=float, default=0.60,
        help=(
            "Jaccard threshold for auto-merging (default 0.60). "
            "Auto-signals (base-title, prefix, subset, near-subset) "
            "always merge regardless of this value, unless a "
            "topic-prefix word blocks them."
        ),
    )
    ap.add_argument(
        "--review-threshold", type=float, default=0.40,
        help="Lower bound for the review band (default 0.40).",
    )
    ap.add_argument(
        "--exclude-pair", action="append", nargs=2, metavar=("SLUG_A", "SLUG_B"),
        default=[],
        help=(
            "Pair of title-slug folder names that should NEVER merge. "
            "Repeatable. Pairs are also loaded from --excludes-file."
        ),
    )
    ap.add_argument(
        "--excludes-file", type=Path, default=DEFAULT_EXCLUDES,
        help=(
            "YAML/JSON file listing pairs to exclude. "
            f"Default: {DEFAULT_EXCLUDES.relative_to(ROOT)} (used if it exists)."
        ),
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Perform git mv merges and re-run generate_mounts.py. Default is dry-run.",
    )
    ap.add_argument(
        "--report", type=Path, default=REPORT_PATH,
        help=f"Where to write the markdown report (default: {REPORT_PATH.relative_to(ROOT)}).",
    )
    args = ap.parse_args()

    if not PRES.exists():
        print(f"error: {PRES} does not exist", file=sys.stderr)
        return 2

    folders = collect_title_folders()
    if not folders:
        print(f"error: no title folders found under {PRES}", file=sys.stderr)
        return 2

    excludes: set[frozenset[str]] = set()
    if args.excludes_file:
        excludes |= load_excludes_file(args.excludes_file)
    for a, b in args.exclude_pair:
        excludes.add(frozenset((a, b)))

    score_matrix: dict[tuple[int, int], PairResult] = {}
    n = len(folders)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset((folders[i].slug, folders[j].slug))
            if pair in excludes:
                score_matrix[(i, j)] = PairResult(
                    False, 0.0, "excluded by user", blocked=True,
                )
                continue
            score_matrix[(i, j)] = pair_score(folders[i], folders[j])

    clusters = two_tier_cluster(n, score_matrix, args.threshold)
    in_cluster: set[int] = set()
    for c in clusters:
        in_cluster.update(c)
    review_pairs = collect_review_pairs(
        score_matrix, args.review_threshold, args.threshold, in_cluster
    )
    blocked_pairs = collect_blocked_pairs(score_matrix)

    report = render_report(
        folders, clusters, score_matrix, review_pairs, blocked_pairs,
        args.threshold, args.review_threshold, excludes, args.apply,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report)
    print(report)
    print(f"\n[wrote report to {args.report.relative_to(ROOT)}]")

    if args.apply:
        moves = apply_moves(folders, clusters)
        print(f"\n[applied {len(moves)} venue move(s)]")
        gen = ROOT / "_automation" / "scripts" / "generate_mounts.py"
        if gen.exists():
            print("[running generate_mounts.py]")
            subprocess.run([sys.executable, str(gen)], check=True, cwd=ROOT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
