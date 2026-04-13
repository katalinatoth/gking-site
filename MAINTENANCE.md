# Site Maintenance Guide

This document explains how to add, edit, and manage content on the Gary King academic website built with Hugo.

## Quick Start

```bash
cd hugo-site
hugo server          # Local preview at http://localhost:1313/gking-site/
hugo --gc --minify   # Production build to public/
```

Push to `main` triggers automatic deployment via GitHub Actions.

---

## Adding a New Publication

1. Create a new directory under `content/publication/`:
   ```
   content/publication/my-new-paper/index.md
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

3. **Optional**: Add a featured image as `featured.jpg` or `featured.png` in the same directory.

4. **Link types**: `pdf` renders as "Article" button, `source` renders as "Publisher's Version". Custom links use the `name` field.

5. **PDF files**: Place PDFs in `static/files/` and reference as `url: "files/filename.pdf"` (no leading slash).

### Publication Types

Use one of: `journal_article`, `book`, `book_chapter`, `conference_paper`, `conference_proceedings`, `data`, `miscellaneous`, `newspaper_article`, `patent`, `presentation`, `report`, `software`, `unpublished`, `web_article`, `website`, `working_paper`.

---

## Adding a New Talk/Presentation

Same structure as publications, under `content/talk/`:
```
content/talk/my-talk-title-2026/index.md
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

To re-run automated cross-linking: `python3 ../scripts/cross_link.py`
To re-run Dataverse linking: `python3 ../scripts/link_dataverse.py`

---

## Adding a New Software Page

Create under `content/software/`:
```
content/software/my-software/index.md
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

Create under `content/authors/`:
```
content/authors/person-name/_index.md
```

```yaml
---
title: "Person Name"
role: "Graduate Student"
organizations:
  - name: "Harvard University"
user_groups:
  - "Current Members"
bio: "Short bio."
social:
  - icon: envelope
    link: "mailto:email@harvard.edu"
  - icon: globe
    link: "https://website.com"
---

Longer biography text here.
```

Add an avatar image as `avatar.jpg` in the same directory.

---

## Updating Research Areas

Research area data lives in `data/research_areas.json`. Each area has subcategories with lists of paper slugs.

To add a paper to a research area, add its slug to the appropriate subcategory in the JSON file:
```json
{
  "name": "Subcategory Name",
  "papers": [
    {"title": "Paper Title", "section": "publication", "slug": "paper-slug"}
  ]
}
```

To re-scrape from the original site: `python3 ../scripts/scrape_research_areas.py`

---

## Updating the Writings Page

The writings page (`content/publication/_index.md`) auto-generates from all publication and talk content. No manual updates needed — just add new content files and they appear automatically.

---

## Modifying the Navigation Bar

Edit `layouts/_partials/components/headers/navbar.html`. The nav links and their order are defined there.

---

## Modifying Page Templates

| Template | Controls |
|----------|----------|
| `layouts/publication/single.html` | Individual publication pages |
| `layouts/talk/single.html` | Individual talk pages |
| `layouts/publication/list.html` | Writings list page |
| `layouts/research-areas/single.html` | Research areas page |
| `layouts/landing/list.html` | Homepage |
| `layouts/_partials/page_links.html` | Link button rendering |
| `layouts/_partials/page_author_card.html` | Author card at bottom of pages |
| `assets/css/custom.css` | All custom CSS |
| `i18n/en.yaml` | Button label overrides (Article, Publisher's Version) |

---

## Changing Button Labels

To change "Article" or "Publisher's Version" labels, edit `i18n/en.yaml`:
```yaml
- id: btn_pdf
  translation: Article

- id: btn_source
  translation: "Publisher's Version"
```

---

## Automated Systems

### Deployment
Pushes to `main` trigger `.github/workflows/deploy.yml` which builds Hugo + Pagefind search index and deploys to GitHub Pages.

### Link Checker
`.github/workflows/link-check.yml` runs every Monday at 9am UTC. It checks all external URLs in content files and creates/updates a GitHub Issue labeled `link-check` if broken links are found. Can also be triggered manually from the Actions tab.

---

## Local Development

```bash
# Install Hugo (macOS)
brew install hugo

# Preview locally
cd hugo-site
hugo server

# Build for production
hugo --gc --minify --baseURL "https://katalinatoth.github.io/gking-site/"

# Build search index
npx pagefind --site public
```

---

## File Structure

```
hugo-site/
├── content/              # All site content (markdown files)
│   ├── publication/      # Papers, datasets, patents
│   ├── talk/             # Presentations
│   ├── software/         # Software pages
│   ├── authors/          # People profiles
│   ├── bio/              # Bio & CV page
│   ├── teaching/         # Teaching page
│   ├── research-areas/   # Research areas page
│   └── research-group/   # Research group page
├── static/files/         # PDFs and downloadable files
├── layouts/              # Custom template overrides
├── assets/css/           # Custom CSS
├── data/                 # Data files (research_areas.json)
├── i18n/                 # Translation overrides
└── .github/workflows/    # CI/CD and link checker
```
