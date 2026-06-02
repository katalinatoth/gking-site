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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
    """Scan all markdown content for references to local files/<name>.pdf.

    Looks in BOTH front-matter `url:` fields AND the markdown body
    (e.g., `[link](files/foo.pdf)` or raw `files/foo.pdf` references).
    Restricted to .pdf extension only; this check is "PDF Integrity".

    Skips EditMe/Redirects/ and PINNED-AT-ROOT.md: the former contains
    redirect FROM-paths (not references to local files), and the latter
    is internal documentation that uses path examples like /files/foo.pdf.
    """
    referenced = set()
    pdf_pattern = re.compile(r'(?<!/)files/([A-Za-z0-9_\-.]+\.pdf)\b')
    skip_paths = {
        EDITME / "Redirects",
        EDITME / "UI" / "PINNED-AT-ROOT.md",
    }
    for base in [EDITME]:
        if not base.exists():
            continue
        for index_md in base.rglob("*.md"):
            if any(str(index_md).startswith(str(p)) for p in skip_paths):
                continue
            try:
                text = index_md.read_text(encoding="utf-8")
            except Exception:
                continue
            for m in pdf_pattern.finditer(text):
                filename = m.group(1)
                if " " not in filename:
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


def _section_for_path(path):
    """Return a high-level section bucket for a content path.

    'Articles', 'Presentations', 'Books', 'SoftwareNotes', 'Patents', 'Reports',
    'Software', or 'Other'. We use this so the duplicate-title check only flags
    same-section duplicates: an article that has 8 presentations of the same
    talk legitimately shares its title across sections; that's not a dupe.
    """
    parts = path.parts
    for marker in ("Articles", "Presentations", "Books", "SoftwareNotes",
                   "Patents", "Reports", "Software"):
        if marker in parts:
            return marker
    return "Other"


def check_duplicate_titles():
    """Find content items with identical titles within the SAME section,
    excluding Presentations.

    Cross-section matches (Articles + Presentations of the same talk) are
    expected. Presentations/Presentations matches are also expected: by design
    one paper has many presentation copies (one per venue/year), all sharing
    the paper's title. The signal we want is article-level duplicates: e.g.
    two folders under Articles/ with the same title — that's likely a genuine
    duplicate that should be merged.
    """
    titles = defaultdict(list)
    for base in [WRITINGS_DIR, SOFTWARE_DIR]:
        if not base.exists():
            continue
        for index_md in base.rglob("index.md"):
            slug = index_md.parent.name
            if slug == "Data" or slug.startswith("_"):
                continue
            section = _section_for_path(index_md)
            if section == "Presentations":
                continue
            fm = parse_front_matter(index_md)
            if fm and "title" in fm:
                titles[fm["title"].lower().strip()].append((section, slug))

    dupes = {}
    for title, entries in titles.items():
        by_section = defaultdict(list)
        for section, slug in entries:
            by_section[section].append(slug)
        same_section_dupes = {sec: slugs for sec, slugs in by_section.items() if len(slugs) > 1}
        if same_section_dupes:
            flat = []
            for sec, slugs in same_section_dupes.items():
                flat.extend(f"{sec}/{slug}" for slug in slugs)
            dupes[title] = flat
    return dupes


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


def extract_external_urls():
    """Walk all markdown files and extract external URLs with their source files."""
    all_urls = {}  # url -> list of files
    content_dirs = [EDITME]
    for d in content_dirs:
        if not d.exists():
            continue
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.endswith('.md'):
                    fp = os.path.join(root, f)
                    try:
                        text = Path(fp).read_text(encoding="utf-8")
                    except Exception:
                        continue
                    for m in re.finditer(r'https?://[^\s\)\]"\'<>]+', text):
                        url = m.group(0).rstrip('.,;:')
                        if url not in all_urls:
                            all_urls[url] = []
                        all_urls[url].append(fp)
    return all_urls


# Hosts that consistently 403 bots regardless of UA (Cloudflare/Akamai-protected
# publishers, university faculty pages behind WAFs). These almost always work in
# real browsers; flagging them is noise, not signal. Add new entries cautiously
# — only after confirming the URL works in a browser but the audit reports 403.
PAYWALL_AND_BOT_BLOCKED_HOSTS = {
    # Academic publishers / DOI resolvers
    "pan.oxfordjournals.org",
    "journals.sagepub.com",
    "science.sciencemag.org",
    "www.science.org",
    "pnas.org", "www.pnas.org",
    "nejm.org", "www.nejm.org",
    "journals.uchicago.edu", "www.journals.uchicago.edu",
    "www.cambridge.org",
    "onlinelibrary.wiley.com",
    "www.tandfonline.com",
    "academic.oup.com",
    "www.nature.com",
    "www.sciencedirect.com",
    "doi.org", "dx.doi.org",
    # University sites with aggressive WAFs
    "www.stat.columbia.edu",
    "www.columbia.edu",
    "blogs.cuit.columbia.edu",
    "www.american.edu",
    "ps.ucdavis.edu",
    "chds.hsph.harvard.edu",
    "hsph.harvard.edu", "www.hsph.harvard.edu",
    "popcenter.harvard.edu",
    "lsa.umich.edu",
    "clasprofiles.wayne.edu",
    "as.nyu.edu",
    "profiles.rice.edu",
    "gsg.skku.edu",
    "research.chop.edu",
    "dfreelon.org",
    # Social media (always bot-block)
    "twitter.com", "x.com",
    "www.linkedin.com", "in.linkedin.com", "linkedin.com",
    # Government / nonprofit sites with Cloudflare
    "www.nasonline.org",
    "www.ssa.gov",
    "www.cbo.gov",
    "www.gob.mx",
    "www.c-span.org",
    # Major media / corporate sites
    "www.nytimes.com",
    "www.fastcompany.com",
    "www.carlyle.com",
    "www.aei.org",
    "www.ariadnelabs.org",
    "www.umassmed.edu",
    "www.w3.org",
    # Misc sites that bot-block but work in browsers
    "biblatex-biber.sourceforge.net",
    "www.ctan.org",
    "psiprivacy.org",
    "csph.brighamandwomens.org",
    "www.stephenpettigrew.com",
    # GitHub rate-limits (429) bots aggressively
    "github.com",
}

# Browser-style User-Agent. Some servers (Cloudflare, Akamai) block strings that
# contain "bot", "checker", "crawler" etc. A real browser UA reduces false 403s.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def check_external_links(all_urls, max_workers=5):
    """Check external URLs for broken links. Requires 'requests' library."""
    if not HAS_REQUESTS:
        return None  # Signal that we couldn't check

    def is_bot_blocked_host(url):
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or ""
            return host.lower() in PAYWALL_AND_BOT_BLOCKED_HOSTS
        except Exception:
            return False

    def check_one(url):
        try:
            resp = requests.head(url, timeout=15, allow_redirects=True,
                                 headers={"User-Agent": BROWSER_UA})
            if resp.status_code == 405:
                resp = requests.get(url, timeout=15, allow_redirects=True,
                                    headers={"User-Agent": BROWSER_UA},
                                    stream=True)
            return url, resp.status_code, None
        except requests.exceptions.Timeout:
            return url, None, "timeout"
        except requests.exceptions.ConnectionError:
            return url, None, "connection_error"
        except Exception as e:
            return url, None, str(e)[:80]

    broken = []
    skipped_bot_blocked = 0
    checked = 0
    total = len(all_urls)
    print(f"Checking {total} external URLs...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(check_one, url): url for url in all_urls}
        for future in as_completed(futures):
            url, status, error = future.result()
            checked += 1
            if checked % 100 == 0:
                print(f"  Checked {checked}/{total}...", file=sys.stderr)
            if error or (status and status >= 400):
                # Suppress 403s from known bot-blocking publishers. They're
                # almost always reachable in a real browser; reporting them
                # buries the genuine broken links in noise.
                if status == 403 and is_bot_blocked_host(url):
                    skipped_bot_blocked += 1
                    continue
                broken.append({
                    "url": url,
                    "status": status,
                    "error": error,
                    "files": all_urls[url][:3],
                })

    print(f"  Done: {checked} checked, {len(broken)} broken, "
          f"{skipped_bot_blocked} bot-blocked publisher 403s suppressed",
          file=sys.stderr)
    return broken


# ---------------------------------------------------------------------------
# Audit checks
# ---------------------------------------------------------------------------

def audit():
    findings = []

    # --- 1. Papers not in any research area ---
    all_slugs = get_all_content_slugs()
    ra_slugs = get_research_area_slugs()
    # Only check writings (articles, books, reports) — not software, presentations, or patents.
    # Patents legitimately don't fit the research-area taxonomy; presentations and software
    # have their own home tabs and shouldn't appear in research-area accordions.
    writing_slugs = {}
    skip_section_dirs = {"Presentations", "SoftwareNotes", "Patents", "_SectionPages", "Data"}
    for slug, path in all_slugs.items():
        parts = set(path.parts)
        if not parts.intersection(skip_section_dirs) and "Software" not in str(path):
            writing_slugs[slug] = path

    not_in_ra = set(writing_slugs.keys()) - ra_slugs
    legacy_slugs_map = {}
    if LEGACY_MAP_JSON.exists():
        data = json.loads(LEGACY_MAP_JSON.read_text(encoding="utf-8"))
        legacy_slugs_map = data.get("entries", data)
    papers_not_in_ra = []
    for slug in sorted(not_in_ra):
        entry = legacy_slugs_map.get(slug, {})
        tab = entry.get("tab", "")
        if tab in ("presentation", "software", "patent"):
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

    # Filter out items that legitimately don't need a legacy-map entry:
    #   - Section/meta folders (_index, Data, anything starting with _)
    #   - Presentation subfolders (one talk → many venue/year folders); only the
    #     canonical talk slug at the top of Presentations/<talk>/ matters.
    #   - Patents (their own taxonomy, no legacy-map mapping needed)
    def _needs_map_entry(slug):
        if slug in ("_index", "Data") or slug.startswith("_"):
            return False
        path = all_slugs.get(slug)
        if path is None:
            return False
        parts = path.parts
        if "Presentations" in parts or "Patents" in parts:
            return False
        return True

    content_without_map = [s for s in content_without_map if _needs_map_entry(s)]

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
        if pf:
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

    # --- 8. External broken links ---
    skip_links = os.environ.get("SKIP_LINK_CHECK", "").lower() in ("1", "true", "yes")
    if not skip_links:
        all_urls = extract_external_urls()
        broken_links = check_external_links(all_urls)
        if broken_links is None:
            findings.append({
                "level": "INFO",
                "category": "External Links",
                "title": "Skipped — 'requests' library not installed (run: pip install requests)",
                "details": [],
                "note": "",
            })
        elif broken_links:
            broken_details = []
            for b in sorted(broken_links, key=lambda x: x["url"])[:25]:
                status = b["status"] or b["error"]
                files_str = ", ".join(os.path.relpath(f, REPO_ROOT) for f in b["files"])
                broken_details.append(f"{status} — {b['url']} (in: {files_str})")
            findings.append({
                "level": "WARN",
                "category": "External Links",
                "title": f"{len(broken_links)} broken external links found",
                "details": broken_details,
                "note": f"(showing first 25 of {len(broken_links)})" if len(broken_links) > 25 else "",
            })
        else:
            findings.append({
                "level": "INFO",
                "category": "External Links",
                "title": f"All {len(all_urls)} external URLs are reachable",
                "details": [],
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
