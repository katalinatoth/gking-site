#!/usr/bin/env python3
"""Import the official Drupal redirect table into data/redirects.yaml.

The source of truth is the redirect summary that Harvard's web team exported
from the old Drupal admin UI — see scraped_data/drupal_redirects.csv (a CSV
copy of gking.harvard.edu-HSD-Redirects-Summary.xlsx).

Each row in that CSV is a `(From, To, Status, Created)` tuple representing
one redirect that was active on the legacy site. This script:

  1. Reads scraped_data/drupal_redirects.csv (or a path passed via --source).
  2. Skips self-loops (rows where From == To).
  3. Translates each `to:` value through to a real new-site URL — chain-
     resolving short vanity targets (`/amelia`, `/cem`, `/zelig`, …) and
     legacy section paths (`/category/research-interests/...`,
     `/publications/<slug>`, `/presentations/<slug>`, `/software/<slug>/<id>`)
     to where their content actually lives on the new Hugo site.
  4. Writes the resulting redirects between BEGIN_MARK / END_MARK comments
     in data/redirects.yaml so re-runs are idempotent and the file stays
     hand-editable outside the managed block.

The translation table below was hand-curated against the new site as it
exists at the time of import. If a target's resolution looks wrong, edit
this script (or the resulting block in data/redirects.yaml directly) and
re-run with --apply.

Usage:
    python3 scripts/import_drupal_redirects.py --apply         # writes
    python3 scripts/import_drupal_redirects.py                 # dry-run
    python3 scripts/import_drupal_redirects.py --diff          # diff only
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


def _find_default_source() -> Path:
    """Locate scraped_data/drupal_redirects.csv across common layouts.

    The scraped Drupal data is large (~1 GB) and not committed to the
    repo, so different developers keep it in different places:

      * Inside the repo at `scraped_data/drupal_redirects.csv`
        — convenient if you've copied the data into your checkout.
      * One level up at `../scraped_data/drupal_redirects.csv`
        — the layout used by the original migration workspace,
        where the repo lived inside a wrapper folder alongside
        `scraped_data/`.

    We try each in turn. If neither exists, return the in-repo path
    so the script's `--source` error message points somewhere sensible.
    """
    candidates = [
        ROOT / "scraped_data" / "drupal_redirects.csv",
        ROOT.parent / "scraped_data" / "drupal_redirects.csv",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


DEFAULT_SRC = _find_default_source()
DATA_FILE = ROOT / "data" / "redirects.yaml"

BEGIN_MARK = "# BEGIN drupal-redirects-import (auto-managed by " \
             "scripts/import_drupal_redirects.py — do not edit by hand)"
END_MARK = "# END drupal-redirects-import"

VANITY_BEGIN_MARK = "# BEGIN vanity-shorts-import (auto-managed by " \
                    "scripts/import_drupal_redirects.py — do not edit by hand)"
VANITY_END_MARK = "# END vanity-shorts-import"


# ---------------------------------------------------------------------------
# Hand-curated translation table.
#
# Each entry maps an *exact* old-site URL (as it appears in the spreadsheet's
# `to:` column) to where the same content lives on the new Hugo site. If a
# target needs a more complex transformation (e.g. drop a trailing legacy
# node-id, swap `/publications/` → `/publication/`), it's handled in
# resolve_target() below.
# ---------------------------------------------------------------------------

# Vanity / short URLs that Gary publicises (or Drupal aliased) and which
# the spreadsheet uses as targets. These were path *aliases* on Drupal —
# not redirects — so they aren't in the spreadsheet's `from` column.
# Listing them here serves two purposes:
#   1. Chain-resolution: spreadsheet rows whose `to:` is a vanity URL
#      land directly on the resolved new-site URL (no chains).
#   2. Direct emission: each entry becomes a redirect on the new site
#      so that typing /amelia, /sibs, /Gov2020, etc. into the browser
#      forwards to the right place. (See emit_vanity_redirects.)
#
# Targets were verified by title-matching the publications.json scrape
# of the old site against content/publication/, content/talk/, and
# content/software/ on the new site. Software products prefer the
# /software/<slug>/ landing page; everything else uses /publication/
# or /talk/ as appropriate.
#
# CASE: Drupal was case-insensitive on path aliases, but the new site
# (Hugo on GitHub Pages) is case-sensitive. Mixed-case keys here will
# also get a lowercase alias auto-emitted by emit_vanity_redirects.
VANITY_TO_NEWSITE: dict[str, str] = {
    # ----- vanity short URLs from publications.json (40 of 41) -----
    # Papers / chapters / forthcoming work
    "/10k":            "/publication/if-a-statistical-model-predicts-that-common-events-should-occur-only-once-in-100/",
    "/2k1":            "/publication/statistical-intuition-without-coding-or-teachers/",
    "/50c":            "/publication/how-the-chinese-government-fabricates-social-media-posts-for-strategic-distracti-2017-166/",
    "/acc":            "/publication/how-american-politics-ensures-electoral-accountability-in-congress/",
    "/compact":        "/publication/how-to-measure-legislative-district-compactness-if-you-only-know-it-when-you-see-2021/",
    "/CompSS":         "/publication/computational-social-science-obstacles-and-opportunities/",
    "/conjointE":      "/publication/correcting-measurement-error-bias-in-conjoint-survey-experiments/",
    "/covid-ccc":      "/publication/building-an-international-consortium-for-tracking-coronavirus-health-status/",
    "/covid-italy":    "/publication/evaluating-covid-19-public-health-messaging-in-italy-self-reported-compliance-an/",
    "/deford":         "/publication/the-essential-role-of-statistical-inference-in-evaluating-electoral-systems-a-re/",
    "/dp":             "/publication/statistically-valid-inferences-from-privacy-protected-data/",
    "/dp-oped":        "/publication/theres-a-simple-solution-to-the-latest-census-fight/",
    "/dpd":            "/publication/statistically-valid-inferences-from-differentially-private-data-releases-with-ap/",
    "/dpd2":           "/publication/statistically-valid-inferences-from-differentially-private-data-releases-ii-exte/",
    "/DPsurvey":       "/publication/differentially-private-survey-research/",
    "/hacking":        "/publication/a-theory-of-statistical-inference-for-ensuring-the-robustness-of-scientific-resu/",
    "/IndiaChild":     "/publication/precision-mapping-child-undernutrition-for-nearly-600000-inhabited-census-villag/",
    "/kkv":            "/publication/designing-social-inquiry-scientific-inference-in-qualitative-research-new-editio/",
    "/matchingtheory": "/publication/a-theory-of-statistical-inference-for-matching-methods-in-causal-research/",
    "/mediaActivate":  "/publication/how-the-news-media-activate-public-expression-and-influence-national-agendas-2017/",
    "/partnerships":   "/publication/a-new-model-for-industry-academic-partnerships/",
    "/partyswitch":    "/publication/the-stability-of-party-identification-among-us-representatives-political-loyalty/",
    "/prefresher":     "/publication/the-math-prefresher-and-the-collective-future-of-political-science-graduate-trai/",
    "/reputable":      "/publication/experimental-evidence-on-the-limited-influence-of-reputable-media-outlets/",
    "/sibs":           "/publication/survey-estimates-of-wartime-mortality/",
    "/symmetry":       "/publication/theoretical-foundations-and-empirical-evaluations-of-partisan-fairness-in-distri/",
    "/videos":         "/publication/education-and-scholarship-by-video/",
    "/vpresent":       "/publication/video-presentations/",
    "/words":          "/publication/an-improved-method-of-automated-nonparametric-content-analysis-for-social-scienc/",
    # Software products (preferring /software/<slug>/ when both exist)
    "/amelia":         "/software/amelia-ii-a-program-for-missing-data/",
    "/anchors":        "/software/anchors-software-for-anchoring-vignettes-data/",
    "/cem":            "/software/cem-coarsened-exact-matching-software/",
    "/clarify":        "/software/clarify-software-for-interpreting-and-presenting-statistical-results/",
    "/ei":             "/software/ei-a-program-for-ecological-inference/",
    "/EzI":            "/software/ezi-an-easy-program-for-ecological-inference/",
    "/judgeit":        "/software/judgeit-ii-a-program-for-evaluating-electoral-systems-and-redistricting-plans/",
    "/matchit":        "/software/matchit-nonparametric-preprocessing-for-parametric-causal-inference/",
    "/maxlik":         "/software/maxlik/",
    "/psi":            "/software/psi-ψ-a-private-data-sharing-interface/",
    "/readme":         "/software/readme-software-for-automated-content-analysis/",
    "/relogit":        "/software/relogit-rare-events-logistic-regression/",
    "/va":             "/software/va-verbal-autopsies/",
    "/whatif":         "/software/whatif-software-for-evaluating-counterfactuals/",
    "/yourcast":       "/software/yourcast/",
    "/zelig":          "/software/zelig-everyones-statistical-software/",
    # Software vanity URLs not in publications.json but referenced by
    # the spreadsheet — old short URLs Gary may still be using in CVs,
    # talks, papers.
    "/eiR":            "/software/ei-a-program-for-ecological-inference/",  # variant of /ei
    "/scholar_software/maxlik": "/software/maxlik/",  # legacy scholar.harvard.edu path
    "/gauss":          "/software/",                  # no specific page; landing
    "/quest":          "/publication/inducing-sustained-creativity-and-diversity-in-large-language-models/",
    "/count":          "/publication/count-a-program-for-estimating-event-count-and-duration-regressions/",
    "/anchoring-vignettes-faqs": "/software/anchors-software-for-anchoring-vignettes-data/",
    "/vign":           "/software/anchors-software-for-anchoring-vignettes-data/",

    # ----- research areas (single page on new site, no per-area URLs) -----
    "/china":          "/research-areas/",
    "/research-interests#applications": "/research-areas/",
    "/research-interests#methods":      "/research-areas/",

    # ----- top-level pages already on the new site -----
    # Listed for chain-resolution. NOT emitted as redirects since the
    # `from` paths already serve real content (would loop or shadow).
    "/ssa":            "/ssa/",
    "/people":         "/people/",

    # ----- teaching: Drupal `/Gov2020` and `/class/...` → `/teaching/...` -----
    "/Gov2020":        "/teaching/gov2020/",
    "/class":          "/teaching/",
    "/class/designing-political-inquiry-government-1003-undergrads": "/teaching/gov1003/",
    "/class/introduction-quantitative-political-methodology-g1000": "/teaching/g1000/",
    "/class/math-prefresher-political-scientists-faculty-advisor":  "/teaching/math-prefresher/",
    "/class/quantitative-social-science-methods-i-government-2001-and-e-200": "/teaching/gov2001/",
    "/class/strategies-political-inquiry-government-2010":          "/teaching/gov2010/",
    "/class/workshop-applied-statistics":                           "/teaching/workshop-applied-statistics/",
    "/classes/materials/book-selection-and-purchasing-decision-making": "/teaching/",
    "/classes/materials/issues":                                    "/teaching/",

    # ----- homepage variants -----
    "/home":               "/",
    "/home-page":          "/",
    "/original-home-page": "/",
    "/gary-king-home-page": "/",
    "/clone-gary-king":    "/",
    "/blanktitle-7":       "/",
    "/blanktitle-8":       "/",
    "/faqs":               "/",
    "/eicamera/kinroot.html": "/",
}

# Vanity short URLs we'd publicly emit as redirects (i.e. that should
# resolve when typed into the browser). Computed below from
# VANITY_TO_NEWSITE, minus entries that:
#   - Are already a real page on the new site (e.g. /people/, /ssa/)
#     — emitting would shadow the real content.
#   - Carry a fragment in the *key* (e.g. /research-interests#applications);
#     fragments are document-internal, not paths to redirect from.
#   - Are multi-segment paths already handled by the spreadsheet's
#     `from` column (e.g. /class/<class>, /classes/materials/<...>).

# Software-page targets in the spreadsheet often look like
# `/software/<slug>/<legacy-node-id>` (e.g. `/software/cem-.../115`). The
# new site has the canonical software page at `/software/<slug>/` with no
# numeric suffix. We strip the trailing suffix and validate against
# content/software/.
_NEW_SOFTWARE_DIRS = sorted(
    d.name for d in (ROOT / "content" / "software").iterdir()
    if d.is_dir() and not d.name.startswith("_")
) if (ROOT / "content" / "software").is_dir() else []

# Slug equivalents: spreadsheet sometimes uses old Drupal slugs that we
# renamed on the new site (e.g. dropped "for", "in", "the").
SOFTWARE_SLUG_REWRITE = {
    "cem-coarsened-exact-matching-software":
        "cem-coarsened-exact-matching-software",
    "matchit-nonparametric-preprocessing-parametric-causal-inference":
        "matchit-nonparametric-preprocessing-for-parametric-causal-inference",
    "matchingfrontier-r-package-calculating-balance-sample-size-frontier":
        "matchingfrontier-r-package-for-calculating-the-balance-sample-size-frontier",
    "yourcast-time-series-cross-sectional-forecasting-your-assumptions":
        "yourcast",
    "whatif-software-evaluating-counterfactuals":
        "whatif-software-for-evaluating-counterfactuals",
    "readme-software-automated-content-analysis":
        "readme-software-for-automated-content-analysis",
    "boocio-software-education-system-hierarchical-concept-maps":
        "boocio-an-education-system-with-hierarchical-concept-maps",
    "autocast-automated-bayesian-forecasting-yourcast":
        "autocast-automated-bayesian-forecasting-with-yourcast",
}

# Publication-slug rewrites for spreadsheet rows where the Drupal slug
# differs from the new-site slug. Looked up empirically against the
# current content/publication/ directory. Some keys are truncation
# prefixes (the Drupal admin export displayed long slugs as `prefix…`);
# the resolver also tries the truncated prefix as a key when the full
# slug is not in this map.
PUBLICATION_SLUG_REWRITE = {
    "assessing-differences-country-level-estimates-maternal-mortality-comparison-gmath-un":
        "assessing-differences-in-country-level-estimates-of-maternal-mortality-a-compari",
    "assessing-differences-country-level-estimates-maternal-mortality":
        "assessing-differences-in-country-level-estimates-of-maternal-mortality-a-compari",
    "evaluating-impacts-swapping-us-decennial-census":
        "evaluating-the-impacts-of-swapping-on-the-us-decennial-census",
    "why-propensity-scores-should-not-be-used-formatching":
        "why-propensity-scores-should-not-be-used-for-matching",
    "randomized-experimental-study-censorship-china":
        "reverse-engineering-censorship-in-china-randomized-experimentation-and-participa",
    # `whos-blame-...` publication is not on the new site as of import;
    # the resolver will fall back to /publication/ for those rows.
}

# Talk-slug rewrites (Drupal `/presentations/<slug>` → new `/talk/<slug>/`).
# When multiple new-site talks match a spreadsheet row, we pick the most
# generic / earliest-dated one.
TALK_SLUG_REWRITE = {
    "reverse-engineering-chinese-government-information-controls-university-of-central":
        "reverse-engineering-chinese-government-information-controls-2017",
    "reverse-engineering-chinese-government-information-controls-univ":
        "reverse-engineering-chinese-government-information-controls-2017",
    "statistically-valid-inferences-privacy-protected-data-pew-research-center-1":
        "statistically-valid-inferences-from-privacy-protected-data-pew-research-center",
    "statistically-valid-inferences-privacy-protected-data-pew-resear":
        "statistically-valid-inferences-from-privacy-protected-data-pew-research-center",
    "how-measure-legislative-district-compactness-if-you-only-know-it-when-you-see-it":
        "how-to-measure-legislative-district-compactness-if-you-only-know-it-when-you-see",
    "how-measure-legislative-district-compactness-if-you-only-know-it":
        "how-to-measure-legislative-district-compactness-if-you-only-know-it-when-you-see",
}


# ---------------------------------------------------------------------------
# Resolver — turns each spreadsheet `to:` into a real new-site URL.
# ---------------------------------------------------------------------------

def _strip_trailing_node_id(slug: str) -> str:
    """Drop a trailing legacy Drupal node-id segment.

    Observed shapes in the spreadsheet:
      `<slug>/115`, `<slug>/24-21`, `<slug>/04-1`           -> `<slug>`
      `<slug>/s…`                (s-prefixed, truncated)    -> `<slug>`
      `<slug>/…`                 (display-truncated)        -> `<slug>`
    """
    parts = slug.rsplit("/", 1)
    if len(parts) == 2:
        last = parts[1]
        if (re.fullmatch(r"\d+(?:-\d+)?", last)
                or "\u2026" in last
                or last == "..."):
            return parts[0]
    return slug


def _strip_trailing_ellipsis(slug: str) -> str:
    """Strip a trailing U+2026 (…) or `...` if present.

    Also drops any trailing dash/underscore left over from a truncated
    slug, so that a key like `slug-mortality` matches a Drupal export
    that displayed as `slug-mortality-…`.
    """
    if slug.endswith("\u2026"):
        slug = slug[:-1]
    elif slug.endswith("..."):
        slug = slug[:-3]
    return slug.rstrip("-_")


def _apply_rewrite(slug: str, table: dict[str, str]) -> str:
    """Look up `slug` in `table`, falling back to a truncation-prefix
    lookup if `slug` ends in `…` or `...`."""
    if slug in table:
        return table[slug]
    if "\u2026" in slug or "..." in slug:
        prefix = _strip_trailing_ellipsis(slug)
        if prefix in table:
            return table[prefix]
    return slug


def _recover_truncated(slug: str, section: str) -> tuple[str, bool]:
    """If `slug` contains U+2026 (Drupal export display truncation), try
    to recover the full slug by prefix-matching against content/<section>/.

    Returns (recovered_slug, ok). If no unique match, returns the
    truncated-prefix-only slug and ok=False.
    """
    if "\u2026" not in slug and "..." not in slug:
        return slug, True
    prefix = _strip_trailing_ellipsis(slug)
    section_dir = _section_dir(section)
    if not section_dir.is_dir():
        return prefix, False
    matches = sorted(
        d.name for d in section_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_")
        and d.name.lower().startswith(prefix.lower())
    )
    if not matches:
        return prefix, False
    # Prefer the shortest match (most generic of any year-suffixed variants).
    matches.sort(key=len)
    return matches[0], True


def _section_dir(name: str) -> Path:
    return ROOT / "content" / name


def _exists_under(section: str, slug: str) -> bool:
    section_dir = _section_dir(section)
    return (section_dir / slug).is_dir() or (section_dir / f"{slug}.md").is_file()


# Hugo permalink :slug uses the page's `slug` field if set, otherwise the
# slugified title. The site has many content directories whose name was
# truncated when imported from Drupal, but whose actual published URL is
# derived from the (longer) title. We need to translate truncated content
# slugs → real public URLs so redirects don't 404.


def _slugify_title(title: str) -> str:
    """Reproduce Hugo's `:slug` derivation from a title.

    Verified against several known title→public-URL pairs on this site
    (e.g. "It's" → "its", "10,000" → "10000", "Ψ" → "ψ", "U.S." → "u.s.",
    "(n " → "n-").

    Algorithm:
      * Lowercase (with unicode case folding).
      * KEEP letters from any script (Latin, Greek, …), digits, dots,
        and hyphens.
      * CONVERT runs of whitespace to a single hyphen.
      * STRIP every other character (apostrophes, commas, colons,
        parens, brackets, exclamation, question marks, slashes, …)
        — i.e. punctuation is dropped *without* leaving a hyphen.
      * Collapse multiple hyphens, trim leading/trailing punctuation.
    """
    out: list[str] = []
    for ch in title.lower():
        if ch.isalnum() or ch in (".", "-"):
            out.append(ch)
        elif ch.isspace():
            out.append("-")
        else:
            # punctuation → strip (no hyphen)
            continue
    s = "".join(out)
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")
    return s


_PUBLIC_SLUG_CACHE: dict[tuple[str, str], str] = {}


def _public_slug(section: str, content_slug: str) -> str:
    """Return the public URL slug for a given content directory slug.

    Reads the content's front matter once (cached). If the page sets
    `slug:` explicitly, use that; otherwise fall back to slugifying the
    title. If no front matter or title is found, return content_slug
    unchanged.
    """
    key = (section, content_slug)
    if key in _PUBLIC_SLUG_CACHE:
        return _PUBLIC_SLUG_CACHE[key]
    section_dir = _section_dir(section)
    md = section_dir / content_slug / "index.md"
    if not md.is_file():
        md_alt = section_dir / f"{content_slug}.md"
        if md_alt.is_file():
            md = md_alt
        else:
            _PUBLIC_SLUG_CACHE[key] = content_slug
            return content_slug
    text = md.read_text(encoding="utf-8")[:5000]
    m_slug = re.search(r"^slug:\s*\"?([^\"\n]+)\"?\s*$", text, re.M)
    if m_slug:
        public = m_slug.group(1).strip()
        _PUBLIC_SLUG_CACHE[key] = public
        return public
    m_title = re.search(r"^title:\s*\"?(.+?)\"?\s*$", text, re.M)
    if m_title:
        public = _slugify_title(m_title.group(1).strip())
        _PUBLIC_SLUG_CACHE[key] = public
        return public
    _PUBLIC_SLUG_CACHE[key] = content_slug
    return content_slug


def _to_public_url(url: str) -> str:
    """Translate any `/<section>/<content-slug>/` URL into its public URL.

    Pass-through for non-section URLs (homepage, /research-areas/, etc.)
    and external links.
    """
    if not url.startswith(("/publication/", "/talk/", "/software/")):
        return url
    parts = url.lstrip("/").rstrip("/").split("/", 1)
    if len(parts) != 2:
        return url
    section, slug = parts
    if not _exists_under(section, slug):
        return url
    return f"/{section}/{_public_slug(section, slug)}/"


def _conflicts_with_existing(path: str) -> bool:
    """True if a redirect at `/<path>/` would shadow a real file or page
    on the new site. Checks both static/ (raw assets) and content/
    (Hugo pages).
    """
    rel = path.strip("/")
    if not rel:
        return False
    static_match = ROOT / "static" / rel
    if static_match.exists():
        return True
    content_match = ROOT / "content" / rel
    if content_match.is_dir() or content_match.with_suffix(".md").is_file():
        return True
    return False


def resolve_target(raw: str) -> tuple[str, str | None]:
    """Translate a raw spreadsheet `to:` into a new-site URL.

    Returns `(resolved_url, note)` where `note` is None on a clean
    resolution, or a short string explaining ambiguity / fallback.

    Post-processing: any /publication/, /talk/, or /software/ URL
    we emit gets routed through _to_public_url so the resulting
    URL matches Hugo's actual permalink (which is derived from the
    page title, not the truncated content directory name).
    """
    out, note = _resolve_target_inner(raw)
    return (_to_public_url(out), note)


def _resolve_target_inner(raw: str) -> tuple[str, str | None]:
    t = (raw or "").strip()
    if not t:
        return ("/", "empty target → /")

    # Bare site root.
    if t == "/":
        return ("/", None)

    # External URLs pass through untouched.
    if t.startswith(("http://", "https://", "mailto:")):
        return (t, None)

    # Filter URL parameters & fragments before exact-match lookup.
    base, sep, suffix = t.partition("?")
    base, _, frag = base.partition("#")

    # Direct hand-curated mapping? Case-insensitive lookup since Drupal
    # was case-insensitive and the spreadsheet sometimes references the
    # same vanity URL in two cases (e.g. /EzI and /Ezi).
    full = base + (("#" + frag) if frag else "")
    vanity_ci = {k.lower(): v for k, v in VANITY_TO_NEWSITE.items()}
    if full in VANITY_TO_NEWSITE:
        return (VANITY_TO_NEWSITE[full], None)
    if full.lower() in vanity_ci:
        return (vanity_ci[full.lower()], None)
    if base in VANITY_TO_NEWSITE or base.lower() in vanity_ci:
        out = VANITY_TO_NEWSITE.get(base, vanity_ci.get(base.lower()))
        # Preserve fragments (document-internal anchors stay meaningful)
        # but drop query strings — Drupal-style facet parameters have
        # no meaning on the new Hugo site.
        if frag and "#" not in out:
            out = out.rstrip("/") + "/#" + frag
        return (out, "drupal facet query string dropped" if sep else None)

    # `/category/research-interests/...` and `/research-interests/...`
    # → /research-areas/ (the new site has a single page; per-area
    # anchors are not implemented).
    if base.startswith("/category/research-interests/") or \
            base.startswith("/categories/research-interests/") or \
            base.startswith("/research-interests/"):
        return ("/research-areas/", "drupal /category/research-interests/* → /research-areas/")

    # `/sites/g/files/.../<filename.pdf>` and `/files/gking/files/<filename.pdf>`
    # — try to map to /files/<filename> on the new site.
    file_match = re.match(r"^/(?:files/gking/files|sites/[^/]+/files(?:/[^/]+)*)"
                          r"/([^/?#]+\.[A-Za-z0-9]+)$", base)
    if file_match:
        fname = file_match.group(1)
        candidate_static = ROOT / "static" / "files" / fname
        if candidate_static.is_file():
            return (f"/files/{fname}", None)
        # Not present yet — preserve the absolute archived URL so users
        # at least don't hit a same-host 404.
        if base.startswith("/sites/"):
            return (f"https://gking.harvard.edu{base}", "file not in new static/files/ — preserved as absolute archived URL")
        return (f"https://gking.harvard.edu{base}", "file not in new static/files/ — preserved as absolute archived URL")

    # `/software/<slug>/<id>` → `/software/<slug>/` (drop legacy node-id),
    # then re-slug if needed.
    if base.startswith("/software/"):
        slug = base[len("/software/"):].rstrip("/")
        slug = _strip_trailing_node_id(slug)
        slug = _apply_rewrite(slug, SOFTWARE_SLUG_REWRITE)
        if "\u2026" in slug or "..." in slug:
            slug, _ok = _recover_truncated(slug, "software")
        if _exists_under("software", slug):
            return (f"/software/{slug}/", None)
        # Fall back to the publication page if a same-named one exists
        # there (some software pages live under /publication/ on the new
        # site for historical reasons).
        if _exists_under("publication", slug):
            return (f"/publication/{slug}/", "spreadsheet target was /software/<slug>; matched a /publication/ page on the new site")
        # Last resort: send to the software index.
        return ("/software/", "software slug not found on new site — sent to /software/ index")

    # `/publications/<slug>` and `/publication/<slug>` → `/publication/<slug>/`
    if base.startswith("/publications/") or base.startswith("/publication/"):
        slug = base.split("/", 2)[2].rstrip("/")
        # Skip query-tab faceted views (`/publications/term/...`,
        # `/publications/type/...`, `/publications/year/...`,
        # `/publications?f%5B0...`) — point at the all-publications listing.
        first = slug.split("/", 1)[0]
        if first in {"term", "type", "year"} or "?" in t or "%" in t:
            return ("/publication/", "drupal facet/term tab → all-publications listing")
        slug = _apply_rewrite(slug, PUBLICATION_SLUG_REWRITE)
        if "\u2026" in slug or "..." in slug:
            slug, _ok = _recover_truncated(slug, "publication")
        if _exists_under("publication", slug):
            return (f"/publication/{slug}/", None)
        # Fall back to the all-publications listing rather than a
        # specific 404.
        return ("/publication/", "publication slug not found on new site — sent to /publication/ index")

    # `/presentations/<slug>` → `/talk/<slug>/`
    if base.startswith("/presentations/"):
        slug = base[len("/presentations/"):].rstrip("/")
        slug = _apply_rewrite(slug, TALK_SLUG_REWRITE)
        if "\u2026" in slug or "..." in slug:
            slug, _ok = _recover_truncated(slug, "talk")
        if _exists_under("talk", slug):
            return (f"/talk/{slug}/", None)
        return ("/talk/", "talk slug not found on new site — sent to /talk/ index")

    # `/people?...` (faceted listing) → `/people/`
    if base.startswith("/people"):
        return ("/people/", "drupal facet on /people → /people/" if "?" in t else None)

    # Long Drupal publication slug used as a top-level URL (e.g.
    # `/cem-coarsened-exact-matching-software`). These were path aliases
    # for the publication page; route through.
    seg = base.lstrip("/")
    if seg and "/" not in seg and _exists_under("publication", seg):
        return (f"/publication/{seg}/", None)
    if seg and "/" not in seg and _exists_under("publication", PUBLICATION_SLUG_REWRITE.get(seg, seg)):
        return (f"/publication/{PUBLICATION_SLUG_REWRITE[seg]}/", None)

    # /publications root
    if base in ("/publications", "/publications/"):
        return ("/publication/", None)

    # Fallback — pass through unchanged.
    return (t, "no rule matched — emitted target verbatim")


# ---------------------------------------------------------------------------
# CSV reader + main flow
# ---------------------------------------------------------------------------

def read_source(src: Path) -> Iterable[tuple[str, str, int]]:
    with src.open(encoding="utf-8", newline="") as f:
        rdr = csv.reader(f)
        header = next(rdr, None)
        for row in rdr:
            if not row or not any((c or "").strip() for c in row):
                continue
            f_, t_, sc, *_ = (row + ["", "", ""])[:3]
            f_ = (f_ or "").strip()
            t_ = (t_ or "").strip()
            if not f_ or not t_:
                continue
            try:
                code = int(str(sc).strip()) if str(sc).strip() else 301
            except ValueError:
                code = 301
            yield (f_, t_, code)


def yaml_quote(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_block(rows: list[tuple[str, str, int, str | None, str]]) -> str:
    """rows: list of (from_path, resolved_to, status, note, original_to)."""
    lines: list[str] = [
        BEGIN_MARK,
        "# Source: scraped_data/drupal_redirects.csv",
        "# Origin: gking.harvard.edu Drupal admin redirect-summary export",
        "#         (Harvard Web Publishing, exported 2025-2026).",
        "# Re-generate with: python3 scripts/import_drupal_redirects.py --apply",
        "#",
        "# Each entry's `to:` has been chain-resolved through to a real new-site",
        "# URL — vanity short URLs (/amelia, /cem, …) were path aliases on the old",
        "# Drupal site, not redirects, so they don't appear in the spreadsheet's",
        "# `from` column. The resolver in scripts/import_drupal_redirects.py",
        "# substitutes their actual new-site location so each redirect lands",
        "# directly on its destination (no chains).",
        "",
    ]
    for from_, to_, status, note, raw_to in rows:
        # Prefix `from` with a leading slash for readability — the build
        # script strips it on parse.
        lines.append(f'  - from: "{yaml_quote(from_)}"')
        lines.append(f'    to:   "{yaml_quote(to_)}"')
        if status != 301:
            lines.append(f"    status: {status}")
        if note:
            note_full = note
            if raw_to and raw_to != to_:
                note_full = f"{note} (drupal target: {raw_to})"
            lines.append(f'    note: "{yaml_quote(note_full)}"')
        elif raw_to and raw_to != to_:
            lines.append(f'    note: "drupal target: {yaml_quote(raw_to)}"')
        lines.append("")
    lines.append(END_MARK)
    return "\n".join(lines)


def emit_vanity_redirects(
    spreadsheet_from_paths: set[str],
) -> list[tuple[str, str, int, str | None, str]]:
    """Build redirect rows for each vanity short URL in VANITY_TO_NEWSITE.

    Skips entries that:
      * Have a fragment in the key (e.g. `/research-interests#applications`
        — fragments live on the target side, not the from side).
      * Already serve real content on the new site (e.g. `/people`,
        `/ssa` — emitting would shadow / loop).
      * Are already present in the spreadsheet's processed `from` set
        (de-dupe with the drupal-redirects block).

    For mixed-case `from` paths (`/Gov2020`, `/CompSS`, `/EzI`,
    `/IndiaChild`, `/conjointE`, `/DPsurvey`, `/mediaActivate`, `/eiR`,
    /dp-oped, …), also emits a lowercase alias since Drupal was
    case-insensitive on path aliases but Hugo on GitHub Pages is not.

    Returns a list shaped like the spreadsheet rows so the existing
    render path can handle both.
    """
    rows: list[tuple[str, str, int, str | None, str]] = []
    seen: set[str] = set()

    for short, target in VANITY_TO_NEWSITE.items():
        if "#" in short:
            continue
        from_path = short.lstrip("/").rstrip("/")
        if not from_path:
            continue
        # Already in spreadsheet?
        if from_path in spreadsheet_from_paths:
            continue
        # Real content on new site?
        if _conflicts_with_existing(from_path):
            continue
        if from_path in seen:
            continue
        seen.add(from_path)
        # Translate content-slug targets to their public URL so the
        # redirect lands on the actual rendered page.
        public = _to_public_url(target)
        rows.append((from_path, public, 301,
                     f"vanity short URL → {public}", ""))

        # Lowercase alias for mixed-case originals.
        lower = from_path.lower()
        if lower != from_path and lower not in seen \
                and lower not in spreadsheet_from_paths \
                and not _conflicts_with_existing(lower):
            seen.add(lower)
            rows.append((lower, public, 301,
                         f"case-insensitive alias of /{from_path}/",
                         ""))

    rows.sort(key=lambda r: r[0].lower())
    return rows


def render_vanity_block(rows: list[tuple[str, str, int, str | None, str]]) -> str:
    lines: list[str] = [
        VANITY_BEGIN_MARK,
        "# Source: hand-curated VANITY_TO_NEWSITE table in",
        "#         scripts/import_drupal_redirects.py, derived from",
        "#         scraped_data/publications.json (the old Drupal site's",
        "#         path aliases for vanity short URLs like /amelia, /sibs,",
        "#         /10k, /quest, etc.) plus a few manually-added entries.",
        "# Re-generate with: python3 scripts/import_drupal_redirects.py --apply",
        "#",
        "# Each entry forwards a short Gary publicises (in CVs, talks,",
        "# papers, slides) to the canonical page on the new site. For",
        "# mixed-case originals (/Gov2020, /CompSS, /EzI, …) a lowercase",
        "# alias is emitted alongside since the new site is case-sensitive.",
        "",
    ]
    for from_, to_, status, note, _raw in rows:
        lines.append(f'  - from: "{yaml_quote(from_)}"')
        lines.append(f'    to:   "{yaml_quote(to_)}"')
        if status != 301:
            lines.append(f"    status: {status}")
        if note:
            lines.append(f'    note: "{yaml_quote(note)}"')
        lines.append("")
    lines.append(VANITY_END_MARK)
    return "\n".join(lines)


def replace_block(existing_text: str, *new_blocks: str) -> str:
    """Substitute the auto-managed blocks, or append them if absent.

    We also strip out any prior block written by an older version of
    this importer (the legacy short-URL recovery script used different
    BEGIN/END markers).
    """
    legacy_marker_patterns = [
        # Older `import_legacy_short_urls.py` (now removed) used an inline
        # `-- BEGIN/END auto-recovered legacy short URLs --` marker.
        (r"#\s*-+\s*BEGIN auto-recovered legacy short URLs\s*-+",
         r"#\s*-+\s*END auto-recovered legacy short URLs\s*-+"),
        # Even older draft used hyphens (`short-URLs`) without decorations.
        (r"#\s*BEGIN auto-recovered legacy short-URLs",
         r"#\s*END auto-recovered legacy short-URLs"),
        # Current importer markers — for idempotency on re-runs.
        (re.escape(BEGIN_MARK), re.escape(END_MARK)),
        (re.escape(VANITY_BEGIN_MARK), re.escape(VANITY_END_MARK)),
    ]
    text = existing_text
    for begin_re, end_re in legacy_marker_patterns:
        pattern = re.compile(
            begin_re + r".*?" + end_re + r"\n?",
            re.DOTALL,
        )
        text = pattern.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.rstrip() + "\n\n" + "\n\n".join(new_blocks) + "\n"
    return text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    try:
        _default_display = DEFAULT_SRC.relative_to(ROOT.parent)
    except ValueError:
        _default_display = DEFAULT_SRC
    p.add_argument("--source", default=str(DEFAULT_SRC),
                   help=f"CSV path (default: {_default_display})")
    p.add_argument("--apply", action="store_true",
                   help="Write into data/redirects.yaml. Without this, run "
                        "in dry-run mode and just print the proposed block.")
    p.add_argument("--diff", action="store_true",
                   help="Print a unified diff against the current "
                        "data/redirects.yaml without writing.")
    args = p.parse_args(argv)

    src = Path(args.source).expanduser().resolve()
    if not src.is_file():
        print(f"[import_drupal_redirects] source not found: {src}", file=sys.stderr)
        return 2

    rows: list[tuple[str, str, int, str | None, str]] = []
    skipped_self_loops = 0
    skipped_truncated_from = 0
    skipped_existing_path = 0
    deduped_query_strings = 0
    seen_paths: set[str] = set()
    for from_, to_, status in read_source(src):
        if from_ == to_:
            skipped_self_loops += 1
            continue
        if "\u2026" in from_ or "..." in from_:
            skipped_truncated_from += 1
            continue
        # Strip any query string / fragment from `from` — static hosting
        # can only match on the URL path, not on the query string.
        path_only = from_.split("?", 1)[0].split("#", 1)[0]
        had_query = path_only != from_
        from_clean = path_only.lstrip("/").rstrip("/")
        if not from_clean:
            continue
        if from_clean in seen_paths:
            if had_query:
                deduped_query_strings += 1
            continue
        # Skip rows where `from` is already served by a real file or page
        # on the new site. A redirect there would either shadow real
        # content or fail the build outright (Hugo can't write a page at
        # a URL that's already a static file).
        if _conflicts_with_existing(from_clean):
            skipped_existing_path += 1
            continue
        seen_paths.add(from_clean)
        resolved, note = resolve_target(to_)
        rows.append((from_clean, resolved, status, note, to_))

    rows.sort(key=lambda r: r[0].lower())

    block = render_block(rows)
    vanity_rows = emit_vanity_redirects(seen_paths)
    vanity_block = render_vanity_block(vanity_rows)

    if args.diff:
        if DATA_FILE.exists():
            cur = DATA_FILE.read_text(encoding="utf-8")
        else:
            cur = ""
        proposed = replace_block(cur, block, vanity_block)
        import difflib
        diff = difflib.unified_diff(
            cur.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"a/{DATA_FILE.relative_to(ROOT)}",
            tofile=f"b/{DATA_FILE.relative_to(ROOT)}",
        )
        sys.stdout.writelines(diff)
        return 0

    if not args.apply:
        print(f"[import_drupal_redirects] DRY RUN — would write "
              f"{len(rows)} drupal redirects + {len(vanity_rows)} vanity "
              f"shorts to {DATA_FILE.relative_to(ROOT)}.")
        print(f"  drupal: skipped {skipped_self_loops} self-loops, "
              f"{skipped_truncated_from} truncated-from rows, "
              f"{skipped_existing_path} that would shadow existing files/pages, "
              f"{deduped_query_strings} duplicates from query-string variants.")
        unresolved = [r for r in rows if r[3] and (
            "not found" in r[3] or "no rule matched" in r[3]
            or "sent to" in r[3] or "best guess" in r[3])]
        if unresolved:
            print(f"  drupal: {len(unresolved)} use a fallback target:")
            for from_, to_, _, note, raw_to in unresolved:
                print(f"    /{from_}  →  {to_}   ({note})")
        print(f"  vanity: {len(vanity_rows)} short URLs (incl. lowercase "
              f"aliases for mixed-case originals).")
        print()
        print("Re-run with --apply to write the changes.")
        return 0

    if DATA_FILE.exists():
        cur = DATA_FILE.read_text(encoding="utf-8")
    else:
        cur = ""
    new_text = replace_block(cur, block, vanity_block)
    DATA_FILE.write_text(new_text, encoding="utf-8")

    print(f"[import_drupal_redirects] wrote {len(rows)} drupal redirects "
          f"+ {len(vanity_rows)} vanity short URLs to "
          f"{DATA_FILE.relative_to(ROOT)} (skipped {skipped_self_loops} "
          f"self-loops, {skipped_truncated_from} truncated-from rows, "
          f"{skipped_existing_path} that would shadow existing files/pages, "
          f"{deduped_query_strings} duplicates from query-string variants).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
