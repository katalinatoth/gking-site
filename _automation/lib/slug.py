"""Canonical slug derivation matching Hugo's :slug permalink behavior.

This module is the single source of truth for computing the public URL slug
from a publication title.  Every script that needs to map titles to URLs
(intake, audit, rename, redirects) should import from here rather than
reimplementing the algorithm.
"""

from __future__ import annotations

import re


def public_slug(title: str) -> str:
    """Reproduce Hugo's :slug derivation from a page title.

    Algorithm (verified against the live site):
      - Lowercase with unicode case folding.
      - KEEP letters from any script (Latin, Greek, etc.), digits, dots,
        and hyphens.
      - CONVERT runs of whitespace to a single hyphen.
      - STRIP every other character (apostrophes, commas, colons, parens,
        brackets, exclamation/question marks, slashes, etc.) without
        leaving a hyphen.
      - Collapse multiple hyphens; trim leading/trailing hyphens.
    """
    out: list[str] = []
    for ch in title.lower():
        if ch.isalnum() or ch in (".", "-"):
            out.append(ch)
        elif ch.isspace():
            out.append("-")
        # All other punctuation is silently dropped.
    s = "".join(out)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")
