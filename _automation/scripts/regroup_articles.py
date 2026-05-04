#!/usr/bin/env python3
"""Classify the journal-article slugs in EditMe/Writings/Articles/Unsorted/
into <Topic>/<Decade>/<slug>/ using research_areas.json + frontmatter date.

Topic resolution rule: a paper is classified into the FIRST methods area
(in the order they appear in research_areas.json) that lists its slug.
Papers not listed under any methods area go to Articles/Other/<decade>/.

Decade is derived from the paper's frontmatter `date:` field. Papers
without a parseable date go to <Topic>/unknown-decade/<slug>/.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITME = ROOT / "EditMe"
ARTICLES_UNSORTED = EDITME / "Writings" / "Articles" / "Unsorted"
ARTICLES = EDITME / "Writings" / "Articles"
RESEARCH_AREAS = EDITME / "ResearchAreas" / "Data" / "research_areas.json"

# Map the canonical research-area name to a CamelCase folder name. These
# names match the layout shown in EditMe/Writings/Articles/README.md.
METHODS_TO_FOLDER = {
    "Anchoring Vignettes (for interpersonal incomparability)": "AnchoringVignettes",
    "Automated Text Analysis":                                 "AutomatedTextAnalysis",
    "Causal Inference":                                        "CausalInference",
    "Event Counts and Durations":                              "EventCountsAndDurations",
    "Ecological Inference":                                    "EcologicalInference",
    "Missing Data, Measurement Error, Differential Privacy":   "MissingDataMeasurementErrorPrivacy",
    "Qualitative Research":                                    "QualitativeResearch",
    "Rare Events":                                             "RareEvents",
    "Survey Research":                                         "SurveyResearch",
    "Unifying Statistical Analysis":                           "UnifyingStatisticalAnalysis",
}


def get_decade(index_md: Path) -> str:
    text = index_md.read_text(errors="replace")
    if not text.startswith("---"):
        return "unknown-decade"
    end = text.find("\n---", 3)
    if end < 0:
        return "unknown-decade"
    fm = text[3:end]
    m = re.search(r"""^\s*date\s*:\s*['"]?(\d{4})""", fm, re.MULTILINE)
    if not m:
        return "unknown-decade"
    return f"{(int(m.group(1)) // 10) * 10}s"


def build_slug_to_folder() -> dict[str, str]:
    """Walk research_areas.methods in declaration order; the first area
    that lists a slug wins."""
    with open(RESEARCH_AREAS) as f:
        data = json.load(f)
    slug_to_folder: dict[str, str] = {}
    for area in data.get("methods", []):
        folder = METHODS_TO_FOLDER.get(area["name"])
        if not folder:
            print(f"WARN: unmapped methods area: {area['name']}", file=sys.stderr)
            continue
        for sub in area.get("subcategories", []):
            for paper in sub.get("papers", []):
                slug = paper.get("slug")
                if slug and slug not in slug_to_folder:
                    slug_to_folder[slug] = folder
    return slug_to_folder


def main() -> int:
    if not RESEARCH_AREAS.exists():
        print(f"Missing {RESEARCH_AREAS}", file=sys.stderr)
        return 1

    slug_to_folder = build_slug_to_folder()
    counts: dict[str, int] = {}
    skipped: list[str] = []

    for slug_dir in sorted(ARTICLES_UNSORTED.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        index_md = slug_dir / "index.md"
        if not index_md.exists():
            skipped.append(slug)
            continue

        topic = slug_to_folder.get(slug, "Other")
        decade = get_decade(index_md)
        dst = ARTICLES / topic / decade / slug
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", str(slug_dir), str(dst)], check=True, cwd=ROOT)
        counts[topic] = counts.get(topic, 0) + 1

    # Drop the now-empty Unsorted bucket if it has nothing real left.
    if ARTICLES_UNSORTED.exists():
        remaining = [p for p in ARTICLES_UNSORTED.rglob("*") if p.is_file()]
        if not remaining:
            subprocess.run(["git", "rm", "-rf", str(ARTICLES_UNSORTED)], check=True, cwd=ROOT)
        else:
            # Keep _index.md if that's all that's left; relocate to Articles/.
            idx = ARTICLES_UNSORTED / "_index.md"
            if idx.exists() and len(remaining) == 1:
                dst = ARTICLES / "_index.md"
                if not dst.exists():
                    subprocess.run(["git", "mv", str(idx), str(dst)], check=True, cwd=ROOT)
            # try rmdir best-effort
            try:
                ARTICLES_UNSORTED.rmdir()
            except OSError:
                pass

    print("\n--- regroup_articles.py summary ---")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"  skipped (no index.md): {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
