#!/usr/bin/env python3
"""
Weekly site audit — checks content integrity, structural consistency,
and dependency freshness for gking-site.

Run locally:   python3 _automation/scripts/audit_site.py
Run in CI:     triggered by .github/workflows/weekly-audit.yml

Outputs a Markdown report to stdout (and optionally to a file path
passed as the first argument).
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]  # hugo-site/
EDITME = REPO_ROOT / "EditMe"
WRITINGS_DIR = EDITME / "Writings"
SOFTWARE_DIR = EDITME / "Software"
STATIC_FILES = REPO_ROOT / "_site" / "static" / "files"
RESEARCH_AREAS_JSON = EDITME / "ResearchAreas" / "Data" / "research_areas.json"
LEGACY_MAP_JSON = WRITINGS_DIR / "Data" / "writings_legacy_map.json"
REDIRECTS_YAML = EDITME / "Redirects" / "Data" / "redirects.yaml"
DEPLOY_YML = REPO_ROOT / ".github" / "workflows" / "deploy.yml"
GO_MOD = REPO_ROOT / "go.mod"
PACKAGE_JSON = REPO_ROOT / "package.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_front_matter(filepath):
    """Extract YAML front matter from an index.md file."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm_text = text[3:end]
    # Minimal YAML parsing for the fields we need
    fm = {}
    fm["_raw"] = fm_text
    # title
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', fm_text, re.M)
    if m:
        fm["title"] = m.group(1).strip('"').strip("'")
    # links with url fields
    fm["link_urls"] = re.findall(r'url:\s*"?([^"\n]+)"?', fm_text)
    # aliases
    fm["aliases"] = re.findall(r'^\s*-\s+(/[^\n]+)', fm_text[fm_text.find("aliases"):] if "aliases" in fm_text else "", re.M)
    # publication_types
    fm["publication_types"] = re.findall(r'^\s*-\s*"?([^"\n]+)"?', fm_text[fm_text.find("publication_types"):fm_text.find("\n", fm_text.find("publication_types") + 20) if fm_text.find("publication_types") > -1 else 0] if "publication_types" in fm_text else "", re.M)
    return fm


def get_all_content_slugs():
    """Walk EditMe/ and collect all content directories with an index.md."""
    slugs = {}  # slug -> path
    search_dirs = [WRITINGS_DIR, SOFTWARE_DIR]
    for base in search_dirs:
        if not base.exists():
            continue
        for index_md in base.rglob("index.md"):
            slug = index_md.parent.name
            if slug == "Data" or slug.startswith("_"):
                continue
            slugs[slug] = index_md
    return slugs


def get_research_area_slugs():
    """Extract all paper slugs referenced in research_areas.json."""
    if not RESEARCH_AREAS_JSON.exists():
        return set()
    data = json.loads(RESEARCH_AREAS_JSON.read_text(encoding="utf-8"))
    slugs = set()
    for category in ("methods", "applications"):
        for area in data.get(category, []):
            for subcat in area.get("subcategories", []):
                for paper in subcat.get("papers", []):
                    if "slug" in paper:
                        slugs.add(paper["slug"])
    return slugs


def get_legacy_map_slugs():
    """Get all slugs from writings_legacy_map.json."""
    if not LEGACY_MAP_JSON.exists():
        return set()
    data = json.loads(LEGACY_MAP_JSON.read_text(encoding="utf-8"))
    entries = data.get("entries", data)
    return set(entries.keys())


def get_pdf_references():
    """Scan all index.md files for references to local files/ PDFs."""
    referenced = set()
    for base in [WRITINGS_DIR, SOFTWARE_DIR]:
        if not base.exists():
            continue
        for index_md in base.rglob("index.md"):
            try:
                text = index_md.read_text(encoding="utf-8")
            except Exception:
                continue
            # Match url: "files/something.pdf" patterns in front matter links
            for m in re.finditer(r'url:\s*"?(files/[^"\s\n]+)"?', text):
                filename = m.group(1).replace("files/", "", 1)
                # Only count actual filenames (has an extension, no slashes suggesting external paths)
                if "." in filename and "/" not in filename and not filename.startswith("http"):
                    referenced.add(filename)
    return referenced


def get_static_pdfs():
    """List all files in _site/static/files/."""
    if not STATIC_FILES.exists():
        return set()
    return {f.name for f in STATIC_FILES.iterdir() if f.is_file()}


def get_redirect_targets():
    """Parse redirects.yaml and return list of (from, to) tuples."""
    if not REDIRECTS_YAML.exists():
        return []
    text = REDIRECTS_YAML.read_text(encoding="utf-8")
    redirects = []
    for block in re.finditer(r'-\s+from:\s*(\S+)\s*\n\s+to:\s*(\S+)', text):
        redirects.append((block.group(1), block.group(2)))
    return redirects


def get_hugo_version_in_use():
    """Extract the Hugo version from deploy.yml."""
    if not DEPLOY_YML.exists():
        return None
    text = DEPLOY_YML.read_text(encoding="utf-8")
    m = re.search(r'HUGO_VERSION:\s*(\S+)', text)
    return m.group(1) if m else None


def check_duplicate_titles():
    """Find content items with identical titles (possible duplicates)."""
    titles = defaultdict(list)
    for base in [WRITINGS_DIR, SOFTWARE_DIR]:
        if not base.exists():
            continue
        for index_md in base.rglob("index.md"):
            slug = index_md.parent.name
            if slug == "Data" or slug.startswith("_"):
                continue
            fm = parse_front_matter(index_md)
            if fm and "title" in fm:
                titles[fm["title"].lower().strip()].append(slug)
    return {t: slugs for t, slugs in titles.items() if len(slugs) > 1}


def check_empty_content():
    """Find index.md files that are stubs (very short, no real content)."""
    stubs = []
    for base in [WRITINGS_DIR, SOFTWARE_DIR]:
        if not base.exists():
            continue
        for index_md in base.rglob("index.md"):
            slug = index_md.parent.name
            if slug == "Data" or slug.startswith("_"):
                continue
            try:
                text = index_md.read_text(encoding="utf-8")
            except Exception:
                continue
            # Strip front matter
            if text.startswith("---"):
                end = text.find("---", 3)
                body = text[end + 3:].strip() if end > -1 else ""
            else:
                body = text.strip()
            fm = parse_front_matter(index_md)
            has_title = fm and "title" in fm
            has_links = fm and fm.get("link_urls")
            if len(text) < 80 and not has_title:
                stubs.append(slug)
    return stubs


# ---------------------------------------------------------------------------
# Audit checks
# ---------------------------------------------------------------------------

def audit():
    findings = []

    # --- 1. Papers not in any research area ---
    all_slugs = get_all_content_slugs()
    ra_slugs = get_research_area_slugs()
    # Only check writings (articles, books, reports, etc.) — not software or presentations
    writing_slugs = {}
    presentation_keywords = {"Presentations", "SoftwareNotes", "_SectionPages", "Data"}
    for slug, path in all_slugs.items():
        parts = set(path.parts)
        if not parts.intersection(presentation_keywords) and "Software" not in str(path):
            writing_slugs[slug] = path

    not_in_ra = set(writing_slugs.keys()) - ra_slugs
    # Filter out presentations by checking legacy map
    legacy_slugs_map = {}
    if LEGACY_MAP_JSON.exists():
        data = json.loads(LEGACY_MAP_JSON.read_text(encoding="utf-8"))
        legacy_slugs_map = data.get("entries", data)
    papers_not_in_ra = []
    for slug in sorted(not_in_ra):
        entry = legacy_slugs_map.get(slug, {})
        tab = entry.get("tab", "")
        if tab in ("presentation", "software"):
            continue
        papers_not_in_ra.append(slug)

    if papers_not_in_ra:
        findings.append({
            "level": "WARN",
            "category": "Research Areas",
            "title": f"{len(papers_not_in_ra)} papers not in any research area",
            "details": papers_not_in_ra[:30],
            "note": "(showing first 30)" if len(papers_not_in_ra) > 30 else "",
        })

    # --- 2. Legacy map out of sync ---
    legacy_map_slugs = get_legacy_map_slugs()
    content_slugs = set(all_slugs.keys())

    map_without_content = sorted(legacy_map_slugs - content_slugs)
    content_without_map = sorted(content_slugs - legacy_map_slugs)
    # Filter out known non-writing content (software, section pages)
    content_without_map = [s for s in content_without_map
                          if s not in ("_index", "Data")
                          and not s.startswith("_")]

    if map_without_content:
        findings.append({
            "level": "WARN",
            "category": "Legacy Map Sync",
            "title": f"{len(map_without_content)} legacy map entries have no matching content folder",
            "details": map_without_content[:20],
            "note": "(showing first 20)" if len(map_without_content) > 20 else "",
        })

    if content_without_map and len(content_without_map) <= 50:
        findings.append({
            "level": "INFO",
            "category": "Legacy Map Sync",
            "title": f"{len(content_without_map)} content folders not in legacy map",
            "details": content_without_map[:20],
            "note": "(showing first 20)" if len(content_without_map) > 20 else "",
        })

    # --- 3. PDF integrity ---
    referenced_pdfs = get_pdf_references()
    static_pdfs = get_static_pdfs()

    missing_pdfs = sorted(referenced_pdfs - static_pdfs)
    orphaned_pdfs = sorted(static_pdfs - referenced_pdfs)

    if missing_pdfs:
        findings.append({
            "level": "ERROR",
            "category": "PDF Integrity",
            "title": f"{len(missing_pdfs)} PDFs referenced in content but missing from static/files/",
            "details": missing_pdfs[:20],
            "note": "(showing first 20)" if len(missing_pdfs) > 20 else "",
        })

    if orphaned_pdfs and len(orphaned_pdfs) <= 100:
        findings.append({
            "level": "INFO",
            "category": "PDF Integrity",
            "title": f"{len(orphaned_pdfs)} PDFs in static/files/ not referenced by any content",
            "details": orphaned_pdfs[:15],
            "note": "(showing first 15)" if len(orphaned_pdfs) > 15 else "",
        })

    # --- 4. Redirect targets pointing to non-existent pages ---
    redirects = get_redirect_targets()
    bad_redirects = []
    for from_path, to_path in redirects:
        if to_path.startswith("http"):
            continue  # External — checked by link-check workflow
        # Internal path: check if it resolves to a content page
        clean = to_path.strip("/")
        if clean.startswith("publication/"):
            slug = clean.replace("publication/", "").strip("/")
            if slug and slug not in content_slugs:
                bad_redirects.append(f"/{from_path}/ → {to_path} (slug '{slug}' not found)")
        # We can't fully resolve all internal paths without Hugo, so only check publication/

    if bad_redirects:
        findings.append({
            "level": "WARN",
            "category": "Redirects",
            "title": f"{len(bad_redirects)} redirects point to non-existent publication pages",
            "details": bad_redirects[:10],
            "note": "",
        })

    # --- 5. Duplicate titles ---
    dupes = check_duplicate_titles()
    if dupes:
        dupe_list = [f'"{t}" → {", ".join(slugs)}' for t, slugs in list(dupes.items())[:10]]
        findings.append({
            "level": "INFO",
            "category": "Duplicates",
            "title": f"{len(dupes)} titles appear in multiple content folders (possible duplicates)",
            "details": dupe_list,
            "note": "(showing first 10)" if len(dupes) > 10 else "",
        })

    # --- 6. Dependency versions ---
    hugo_version = get_hugo_version_in_use()
    blox_version = None
    if GO_MOD.exists():
        m = re.search(r'blox-tailwind\s+v([\d.]+)', GO_MOD.read_text())
        if m:
            blox_version = m.group(1)

    pagefind_version = None
    if PACKAGE_JSON.exists():
        pkg = json.loads(PACKAGE_JSON.read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        pf = deps.get("pagefind", "")
        pagefind_version = pf.lstrip("^~>=")

    version_info = []
    if hugo_version:
        version_info.append(f"Hugo: {hugo_version}")
    if blox_version:
        version_info.append(f"Hugo Blox (blox-tailwind): {blox_version}")
    if pagefind_version:
        version_info.append(f"Pagefind: {pagefind_version}")

    # We can't check latest versions without network, so just report current
    findings.append({
        "level": "INFO",
        "category": "Dependencies",
        "title": "Current dependency versions (check for updates manually or see workflow output)",
        "details": version_info,
        "note": "",
    })

    # --- 7. Empty folders / structural issues ---
    empty_dirs = []
    for base in [WRITINGS_DIR, SOFTWARE_DIR]:
        if not base.exists():
            continue
        for d in base.rglob("*"):
            if d.is_dir() and d.name not in ("Data", "_SectionPages"):
                children = list(d.iterdir())
                if not children:
                    empty_dirs.append(str(d.relative_to(REPO_ROOT)))
    if empty_dirs:
        findings.append({
            "level": "INFO",
            "category": "Structure",
            "title": f"{len(empty_dirs)} empty directories (can be removed)",
            "details": empty_dirs[:15],
            "note": "",
        })

    return findings


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(findings):
    errors = [f for f in findings if f["level"] == "ERROR"]
    warns = [f for f in findings if f["level"] == "WARN"]
    infos = [f for f in findings if f["level"] == "INFO"]

    lines = []
    lines.append("# Weekly Site Audit Report")
    lines.append("")
    lines.append(f"**Summary:** {len(errors)} errors, {len(warns)} warnings, {len(infos)} informational")
    lines.append("")

    if not errors and not warns:
        lines.append("Everything looks good. No action needed.")
        lines.append("")

    for section_name, section_findings in [("Errors", errors), ("Warnings", warns), ("Informational", infos)]:
        if not section_findings:
            continue
        lines.append(f"## {section_name}")
        lines.append("")
        for f in section_findings:
            lines.append(f"### [{f['level']}] {f['category']}: {f['title']}")
            lines.append("")
            if f.get("note"):
                lines.append(f"_{f['note']}_")
                lines.append("")
            if f["details"]:
                for item in f["details"]:
                    lines.append(f"- `{item}`")
                lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    findings = audit()
    report = generate_report(findings)

    # Output to stdout
    print(report)

    # Optionally write to file
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])
        output_path.write_text(report, encoding="utf-8")
        print(f"\nReport written to {output_path}", file=sys.stderr)

    # Exit code: 1 if errors found, 0 otherwise
    errors = [f for f in findings if f["level"] == "ERROR"]
    sys.exit(1 if errors else 0)
