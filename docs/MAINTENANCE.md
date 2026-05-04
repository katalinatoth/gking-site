# Site Maintenance Guide

> **Older notes — kept for reference.** The current canonical guide is
> [`UPDATING.md`](UPDATING.md). After the 2026 section-driven repo
> reorg, every "where does X live?" answer in this file points at the
> new section folders (`writings/`, `people/`, `software/`, …) rather
> than the old monolithic `content/`/`layouts/`/`data/` trees. Some of
> the legacy helper-script invocations referenced here
> (`python3 ../scripts/cross_link.py`, `link_dataverse.py`,
> `scrape_research_areas.py`) are migration scripts that lived outside
> the repo and aren't shipped with the checkout. Use `UPDATING.md` for
> anything you actually need to do.

This document explains how to add, edit, and manage content on the
Gary King academic website built with Hugo.

## Quick Start

```bash
cd gking-site/hugo-site   # the repo root
hugo server               # Local preview at http://localhost:1313/gking-site/
hugo --gc --minify        # Production build to public/
```

Push to `main` triggers automatic deployment via GitHub Actions.

---

## Adding a New Publication

1. Create a new directory under `writings/content/`:
   ```
   writings/content/my-new-paper/index.md
   ```

2. Front matter template:
   ```yaml
   ---
   title: "Full Paper Title"
   date: "2026-01-15"
   authors:
     - "Gary King"
     - "Coauthor Name"
   publication_types:
     - "journal_article"
   publication: "Journal Name, Vol, Pages"
   abstract: "Paper abstract text here."
   links:
     - type: pdf
       url: "files/my-paper.pdf"
     - type: source
       url: "https://doi.org/..."
     - name: "Supplementary Material"
       url: "files/my-paper-supp.pdf"
   ---
   ```

3. **Optional**: Add a featured image as `featured.jpg` or
   `featured.png` in the same directory.

4. **Link types**: `pdf` renders as "Article" button, `source`
   renders as "Publisher's Version". Custom links use the `name`
   field.

5. **PDF files**: Place PDFs in `_site/static/files/` and reference
   as `url: "files/filename.pdf"` (no leading slash). Hugo's
   `static/` mount in `hugo.yaml` makes everything under
   `_site/static/` available at the site root, so a file at
   `_site/static/files/foo.pdf` is served at `/files/foo.pdf`.

### Publication Types

Use one of: `journal_article`, `book`, `book_chapter`,
`conference_paper`, `conference_proceedings`, `data`, `miscellaneous`,
`newspaper_article`, `patent`, `presentation`, `report`, `software`,
`unpublished`, `web_article`, `website`, `working_paper`.

---

## Adding a New Talk/Presentation

Same structure as publications, but under `talks/content/`:

```
talks/content/my-talk-title-2026/index.md
```

```yaml
---
title: "Talk Title (venue, date)"
date: "2026-03-15"
authors:
  - "Gary King"
publication_types:
  - "presentation"
event: "Conference Name"
event_url: "https://conference-url.com"
location: "City, State"
abstract: "Talk abstract."
links:
  - type: pdf
    url: "files/my-talk-slides.pdf"
---
```

---

## Cross-Linking Papers and Talks

Add these fields to front matter to create "See Also" sections:

**In a publication** (link to talks):
```yaml
related_talks:
  - "talk-slug-1"
  - "talk-slug-2"
```

**In a talk** (link to paper):
```yaml
related_paper: "publication-slug"
```

**In a publication** (link to dataset):
```yaml
related_dataset: "dataset-publication-slug"
```

**Harvard Dataverse link**:
```yaml
dataverse_url: "https://doi.org/10.7910/DVN/XXXXX"
dataverse_name: "Replication Data for: Paper Title"
```

The site builds the "See Also" boxes automatically from these fields
(plus shared tags / authors / titles). The legacy `cross_link.py` and
`link_dataverse.py` migration scripts are no longer shipped — see
`UPDATING.md` for the current "See Also" rules.

---

## Adding a New Software Page

Create under `software/content/`:

```
software/content/my-software/index.md
```

```yaml
---
title: "Software Name"
date: "2024-01-01"
authors:
  - "Gary King"
  - "Developer Name"
publication_types:
  - "software"
abstract: "Software description."
links:
  - name: "Software Website"
    url: "https://software-url.com"
---
```

---

## Adding a Research Group Member

Profile pages live under `people/content/profiles/`; the `authors/`
folder is a separate Hugo taxonomy used only for the `gary-king`
author page. For a new research-group member create:

```
people/content/profiles/person-name/index.md
```

```yaml
---
title: "Person Name"
role: "Graduate Student"
organizations:
  - name: "Harvard University"
research_group_category: "current"
bio: "Short bio."
social:
  - icon: envelope
    link: "mailto:email@harvard.edu"
  - icon: globe
    link: "https://website.com"
---

Longer biography text here.
```

Add an avatar image as `avatar.jpg` in the same directory. To add
the person to the filterable roster on `/research-group/`, also
update `people/data/research_group.json` (see `UPDATING.md` for the
schema).

---

## Updating Research Areas

Research area data lives in `research-areas/data/research_areas.json`.
Each area has subcategories with lists of paper slugs.

To add a paper to a research area, add its slug to the appropriate
subcategory in the JSON file:

```json
{
  "name": "Subcategory Name",
  "papers": [
    {"title": "Paper Title", "section": "publication", "slug": "paper-slug"}
  ]
}
```

The legacy `scrape_research_areas.py` migration script is no longer
shipped with the checkout.

---

## Updating the Writings Page

The Writings landing page auto-generates from every publication and
talk bundle. No manual updates needed — just add new content under
`writings/content/<slug>/` or `talks/content/<slug>/` and they
appear automatically. Tab placement is driven by
`writings/data/writings_legacy_map.json`; the intake bots maintain
that file for new entries.

---

## Modifying the Navigation Bar

Edit the `menus.main` block in `hugo.yaml`. The nav links and their
order are defined there.

---

## Modifying Page Templates

After the section-driven reorg, layout files live under their owning
section. The shared theme bits (`baseof.html`, `_default/`,
`_partials/`, `shortcodes/`, `page/`) stay at the project root in
`layouts/` because HugoBlox's `get_hook` partial reads them with
`os.ReadDir`, which is not mount-aware.

| Template                                            | Controls                              |
|-----------------------------------------------------|---------------------------------------|
| `writings/layouts/single.html`                      | Individual publication pages          |
| `talks/layouts/single.html`                         | Individual talk pages                 |
| `writings/layouts/list.html`                        | Writings list page                    |
| `research-areas/layouts/single.html`                | Research areas page                   |
| `home/layouts/landing/list.html`                    | Homepage                              |
| `layouts/_partials/page_links.html`                 | Link button rendering                 |
| `layouts/_partials/page_author_card.html`           | Author card at bottom of pages        |
| `assets/css/custom.css`                             | All custom CSS                        |
| `_site/i18n/en.yaml`                                | Button label overrides (Article, Publisher's Version) |

---

## Changing Button Labels

To change "Article" or "Publisher's Version" labels, edit
`_site/i18n/en.yaml`:

```yaml
- id: btn_pdf
  translation: Article

- id: btn_source
  translation: "Publisher's Version"
```

---

## Automated Systems

### Deployment

Pushes to `main` trigger `.github/workflows/deploy.yml` which builds
Hugo + Pagefind search index and deploys to GitHub Pages. As part of
the build, the workflow runs:

- `_automation/scripts/build_redirects.py` — materialise
  `redirects/data/redirects.yaml` into Hugo content stubs.
- `writings/scripts/compute_publication_first_commit.py` — refresh
  the spotlight ordering map.

### Link Checker

`.github/workflows/link-check.yml` runs every Monday at 9am UTC. It
walks every `<section>/content/` tree and checks all external URLs;
if it finds anything broken it creates / updates a GitHub Issue
labelled `link-check`. Can also be triggered manually from the
Actions tab.

### Intake bots

`.github/workflows/intake-publication.yml`,
`.github/workflows/intake-from-issue.yml`, and
`.github/workflows/intake-edit.yml` together implement the
"drop a PDF, get a draft PR" intake flow. See `UPDATING.md` →
"Quick add" for the user-facing details.

---

## Local Development

```bash
# Install Hugo (macOS)
brew install hugo

# Preview locally
cd gking-site/hugo-site            # the repo root
hugo server

# Build for production
hugo --gc --minify --baseURL "https://katalinatoth.github.io/gking-site/"

# Build search index
npx pagefind --site public
```

---

## File Structure

```
gking-site/hugo-site/         # root of the git checkout
├── home/                     # Homepage (content + layouts)
├── bio/                      # Bio & CV page
├── writings/                 # Papers, datasets, patents (content + data + layouts + scripts)
├── talks/                    # Presentations (content + layouts)
├── software/                 # Software pages (content + data + layouts)
├── dataverse/                # Dataverse landing (content + data + layouts)
├── people/                   # Group / profiles / authors (content + data + layouts + scripts)
├── teaching/                 # Teaching pages (content + layouts)
├── research-areas/           # Research areas (content + data + layouts)
├── blog/                     # Blog (content + layouts)
├── contact/                  # Contact page (content + layouts)
├── pages/                    # Standalone pages (apply, recs, …)
├── redirects/                # redirects/data/redirects.yaml + auto-generated stubs
│
├── layouts/                  # Shared theme bits — STAYS at project root
├── assets/css/custom.css     # Custom CSS — STAYS at project root
│
├── _site/                    # Cross-section Hugo plumbing
│   ├── static/files/         # PDFs and downloadable files
│   ├── static/images/        # Site-wide images
│   ├── archetypes/, i18n/
│   └── data/                 # Cross-section data outputs
├── _automation/              # Maintenance + intake bots
│   ├── intake/               # Drop-zone for the auto-import bot
│   └── scripts/              # Cross-section helper scripts
├── docs/                     # Repo docs (UPDATING.md, etc.)
│
├── .github/workflows/        # CI/CD, intake bots, link checker
├── .githooks/                # post-commit auto-push hook
└── hugo.yaml                 # Top-level Hugo config (mounts + menus)
```

The Hugo build sees a single logical `content/` / `layouts/` /
`data/` tree because `hugo.yaml`'s `module.mounts` block remaps each
of these section folders onto Hugo's expected target paths. URLs and
templates are unchanged from the pre-reorg layout.
