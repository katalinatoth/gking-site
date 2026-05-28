# gking-site

Source for <https://gking.harvard.edu/> — Gary King's academic website,
built with Hugo + Hugo Blox and deployed to GitHub Pages via GitHub Actions.

> **Repository:** <https://github.com/iqss-research/gking-site> ·  
> **Live site:** <https://gking.harvard.edu/> ·  
> **Shortcut:** <https://GaryKing.org>  

Every push to `main` triggers a live deploy (~3 minutes).

---

**This file is the single reference for human maintainers.** For AI-agent-specific workflow rules
see [`AGENTS.md`](AGENTS.md).

---

## Table of contents

1. [Overview](#overview)
2. [Repository layout](#repository-layout)
3. [Where do I find X?](#where-do-i-find-x)
4. [Quick add (every content type)](#quick-add-every-content-type)
5. [Manual content templates](#manual-content-templates)
6. [Startups section](#startups-section)
7. [GaryAI chatbot](#garyai-chatbot)
8. [Featured spotlight & See Also](#featured-spotlight--see-also)
9. [Short URLs & redirects](#short-urls--redirects)
10. [Research areas, homepage, navigation & other pages](#research-areas-homepage-navigation--other-pages)
11. [People & research group](#people--research-group)
12. [Claude prompts for common tasks](#claude-prompts-for-common-tasks)
13. [Automation & CI/CD](#automation--cicd)
14. [Architecture & principles](#architecture--principles)
15. [Local development](#local-development)
16. [Troubleshooting](#troubleshooting)
17. [Publication types reference](#publication-types-reference)

---

<details>
<summary><h2 id="overview">1. Overview</h2></summary>

| Layer | Choice |
|-------|--------|
| Static site generator | Hugo 0.160.1 (extended) |
| Theme | Hugo Blox (`blox-tailwind`) via Go module, vendored in `_vendor/` |
| CSS | Tailwind (compiled by Blox) + `assets/css/custom.css` for overrides |
| Search | Pagefind (static, wasm-based; index built in CI) |
| Hosting | GitHub Pages |
| CI/CD | GitHub Actions (`.github/workflows/deploy.yml`) |

All editable content lives under **`EditMe/`**. Hugo's `module.mounts`
block in `hugo.yaml` remaps every sub-folder onto Hugo's expected
`content/`, `layouts/`, and `data/` paths at build time, so URLs are
unchanged. The mounts block is auto-generated — run
`python3 _automation/scripts/generate_mounts.py` after adding or
removing folders under `EditMe/`.

**Two ways to edit:**

- **Claude / Cursor** — describe what you want changed in plain English.
  Claude edits the files and pushes. See [Claude prompts for common
  tasks](#claude-prompts-for-common-tasks) for ready-made prompts.
- **GitHub.com** — pencil-icon edits in the browser. No local tools
  needed. Works from a phone or borrowed laptop.

Either path makes the change live within ~3 minutes.

</details>

---

<details>
<summary><h2 id="repository-layout">2. Repository layout</h2></summary>

```
gking-site/hugo-site/                 ← root of the git checkout
├── EditMe/                           ← EVERY editable thing on the site
│   ├── UI/                           ← per-section layout overrides, CSS pointer
│   │   ├── PerSectionLayouts/        ← one subfolder per section with custom templates
│   │   │   ├── HomePage/landing/     ← homepage template
│   │   │   ├── Writings/             ← publication single/list pages
│   │   │   ├── Talks/                ← talk single page
│   │   │   ├── Startups/             ← startups list/single pages
│   │   │   ├── ResearchAreas/        ← research areas page
│   │   │   ├── ResearchGroup/        ← people/research-group page
│   │   │   ├── Software/             ← software list/single pages
│   │   │   └── ...
│   │   ├── Config/                   ← editorial config snippets
│   │   └── PINNED-AT-ROOT.md         ← explains what can't move into EditMe/
│   │
│   ├── HomePage/                     ← homepage (/_index.md)
│   ├── Bio/                          ← /bio/
│   ├── Writings/                     ← papers, books, reports, patents, court
│   │   │                                briefs, software-papers, slide decks
│   │   ├── Articles/<Topic>/<Decade>/<slug>/
│   │   ├── Books/<Decade>/<slug>/
│   │   ├── Reports/<Decade>/<slug>/
│   │   ├── Patents/<Decade>/<slug>/
│   │   ├── CourtBriefs/<Decade>/<slug>/
│   │   ├── SoftwareNotes/<Decade>/<slug>/
│   │   ├── Presentations/<title-slug>/<venue-slug>/
│   │   ├── Data/                     ← featured_publications.yaml,
│   │   │                                writings_legacy_map.json, …
│   │   └── _SectionPages/            ← _index.md for /publication/ and /talk/
│   │
│   ├── Startups/                     ← /startups/ (Crimson Hexagon, Thresher, etc.)
│   ├── ResearchAreas/                ← /research-areas/ (+ Data/research_areas.json)
│   ├── Software/                     ← /software/ (+ Data/*.yaml)
│   ├── Dataverse/                    ← /dataverse/ (+ Data/dataverse.json)
│   ├── People/                       ← /research-group/, /people/, /authors/
│   │   ├── ResearchGroup/
│   │   ├── Profiles/                 ← ~350 collaborator profiles
│   │   ├── Authors/                  ← author taxonomy (gary-king)
│   │   └── Data/research_group.json
│   ├── Teaching/                     ← /teaching/ (+ per-class sub-pages)
│   ├── Blog/                         ← /blog/
│   ├── Contact/                      ← /contact/
│   ├── Misc/                         ← standalone pages (advice, recs, ask-gary, …)
│   └── Redirects/                    ← legacy URL aliases
│       ├── Data/redirects.yaml
│       └── content/                  ← auto-generated stubs (gitignored)
│
├── layouts/                          ← shared theme bits (baseof.html, _default/,
│                                        _partials/, shortcodes/, chatbot/).
│                                        STAYS at project root — HugoBlox reads
│                                        with os.ReadDir (not mount-aware).
├── assets/                           ← css/custom.css + media/.
│                                        STAYS at project root (same reason).
│
├── _site/                            ← cross-section Hugo plumbing
│   ├── static/files/                 ← PDFs, slides, supplementary downloads
│   ├── static/images/                ← bio photo, site-wide images
│   ├── static/js/                    ← gking-chat-widget.js (GaryAI popup)
│   ├── archetypes/                   ← templates for `hugo new`
│   ├── i18n/                         ← button label overrides (en.yaml)
│   └── data/                         ← cross-section data outputs
│
├── _automation/                      ← maintenance scripts
│   └── scripts/                      ← every Python helper
│       ├── writings/                 ← DOI fillers, audits
│       ├── people/                   ← profile sync, research-group scrapers
│       └── (top-level)               ← build_redirects.py, generate_mounts.py, …
│
├── docs/audits/                      ← point-in-time audit reports
├── .github/workflows/                ← CI/CD: deploy, weekly-audit
├── .githooks/                        ← post-commit auto-push hook
└── hugo.yaml                         ← site config (menus, theme, module.mounts)
```

**Folders pinned at the project root** (cannot move into `EditMe/`):

- `layouts/` — HugoBlox's `get_hook` partial uses `os.ReadDir` (literal filesystem read).
- `assets/` — HugoBlox's `site_head.html` uses `fileExists` on this path.
- `.github/`, `.githooks/` — GitHub Actions and git look for these by literal path.

See [`EditMe/UI/PINNED-AT-ROOT.md`](EditMe/UI/PINNED-AT-ROOT.md) for
the full list and the exact tooling calls that force them to stay.

Each folder under `EditMe/` has its own small `README.md` for
quick navigation on GitHub.

</details>

---

<details>
<summary><h2 id="where-do-i-find-x">3. Where do I find X?</h2></summary>

| You want to edit / find … | Look here |
| --- | --- |
| A specific paper | `EditMe/Writings/<Type>/<Topic>/<Decade>/<slug>/index.md` |
| A specific talk / slide deck | `EditMe/Writings/Presentations/<title-slug>/<venue-slug>/index.md` |
| A software tool's page | `EditMe/Software/<slug>/index.md` |
| A person's profile | `EditMe/People/Profiles/<slug>/index.md` |
| Site bio / CV | `EditMe/Bio/index.md` · CV PDF at `_site/static/files/vitae.pdf` |
| Home page sections | `EditMe/HomePage/_index.md` · template at `EditMe/UI/PerSectionLayouts/HomePage/landing/list.html` |
| The "Featured" working-papers spotlight | `EditMe/Writings/Data/featured_publications.yaml` |
| The Writings page tab routing | `EditMe/Writings/Data/writings_legacy_map.json` |
| The Dataverse list | `EditMe/Dataverse/Data/dataverse.json` |
| The research-group roster | `EditMe/People/Data/research_group.json` |
| The Research Areas grid | `EditMe/ResearchAreas/Data/research_areas.json` |
| Startup pages (Crimson Hexagon, Thresher, etc.) | `EditMe/Startups/<slug>/index.md` |
| Startups page layout | `EditMe/UI/PerSectionLayouts/Startups/list.html` |
| Legacy URL redirects | `EditMe/Redirects/Data/redirects.yaml` |
| PDFs | `_site/static/files/<slug>.pdf` |
| Custom CSS | `assets/css/custom.css` |
| Per-section layout overrides | `EditMe/UI/PerSectionLayouts/<Section>/` |
| All Python helpers | `_automation/scripts/` |
| GitHub workflows | `.github/workflows/` |
| Site-wide partials / shortcodes | `layouts/_partials/`, `layouts/shortcodes/` |
| GaryAI chatbot page | `EditMe/Misc/ask-gary/index.md` + `layouts/chatbot/single.html` |
| GaryAI popup widget | `_site/static/js/gking-chat-widget.js` |
| Google Analytics tracking | `layouts/_partials/hooks/head-start/google-analytics.html` (tag `G-NDZT9P326S`) |
| What runs when something is pushed to `main` | `.github/workflows/deploy.yml` |
| Navigation menu | `hugo.yaml` → `menus.main` |
| Button label overrides ("Article", etc.) | `_site/i18n/en.yaml` |

</details>

---

<details>
<summary><h2 id="quick-add-every-content-type">4. Quick add (every content type)</h2></summary>

The easiest way to add content is to paste a prompt into Claude/Cursor.
Go to [Claude prompts for common tasks](#claude-prompts-for-common-tasks)
and copy the prompt for the type of content you want to add.

If you prefer to do it by hand on GitHub, follow the step-by-step
instructions in [Manual content templates](#manual-content-templates).

**What you need for each content type:**

| Content type | What to have ready |
|---|---|
| Paper / article | The PDF, plus: title, authors, year, journal/venue, abstract, DOI |
| Talk / presentation | The slides PDF, plus: title, venue name, year |
| Book | Title, authors, publisher, year, abstract |
| Software / R package | Name, website URL, short description |
| Patent | The PDF, plus: title, inventors, year, patent number |
| Court brief | The PDF, plus: title, authors, year, abstract |

After you push any change to `main`, the site rebuilds automatically.
Your change goes live in about 3 minutes.

</details>

---

<details>
<summary><h2 id="manual-content-templates">5. Manual content templates</h2></summary>

These are step-by-step instructions for adding content directly on
GitHub (without using Claude).

### Adding a paper or article

1. Go to https://github.com/iqss-research/gking-site
2. Click into `_site/static/files/`
3. Click **"Add file"** → **"Upload files"**
4. Drag in your PDF. Name it something short with dashes (e.g., `my-paper-title.pdf`)
5. Click **"Commit changes"**
6. Now go back to the repo root and click into the folder for your content type:
   - Journal article → `EditMe/Writings/Articles/`
   - Book → `EditMe/Writings/Books/`
   - Report → `EditMe/Writings/Reports/`
   - Patent → `EditMe/Writings/Patents/`
   - Court brief → `EditMe/Writings/CourtBriefs/`
7. For articles, pick the topic subfolder that fits (e.g., `CausalInference/`, `RareEvents/`, etc.). If unsure, use `Unsorted/`.
8. Click into the decade subfolder (e.g., `2020s/`)
9. Click **"Add file"** → **"Create new file"**
10. In the filename box, type: `your-paper-name/index.md` (this creates a folder and file at once)
11. Paste the following template and replace every placeholder with your actual info:

```yaml
---
title: "PASTE YOUR PAPER TITLE HERE"
date: YYYY-MM-DD
authors:
  - "Gary King"
  - "SECOND AUTHOR NAME"
publication_types:
  - "journal_article"
publication: "JOURNAL NAME, Volume(Issue), Pages"
abstract: |-
  PASTE ABSTRACT HERE.
doi: "PASTE DOI HERE (e.g., 10.1234/example)"
links:
  - type: pdf
    url: "files/YOUR-PDF-FILENAME.pdf"
  - type: source
    url: "https://doi.org/PASTE-DOI-HERE"
---
```

12. Click **"Commit changes"**
13. Finally, open `EditMe/Writings/Data/writings_legacy_map.json`, click the pencil icon, and add this line near the bottom (before the closing `}`):

```json
"your-paper-name": { "tab": "journal", "drupal": "journal_article" }
```

Use `"tab": "book"` for books, `"tab": "patent"` for patents, `"tab": "courtbrief"` for court briefs.

14. Click **"Commit changes"**

The site will rebuild in ~3 minutes with your new paper.

### Adding a talk / presentation

1. Upload the slides PDF to `_site/static/files/` (same as step 2-5 above)
2. Navigate to `EditMe/Writings/Presentations/`
3. Click **"Add file"** → **"Create new file"**
4. In the filename box, type: `your-talk-title/venue-name-year/index.md`
5. Paste this template and fill it in:

```yaml
---
title: "PASTE TALK TITLE HERE"
date: YYYY-MM-DD
authors:
  - "Gary King"
publication_types:
  - "presentation"
event: "CONFERENCE OR EVENT NAME"
location: "CITY, STATE"
abstract: "SHORT DESCRIPTION OF THE TALK."
links:
  - type: pdf
    url: "files/YOUR-SLIDES-FILENAME.pdf"
---
```

6. Click **"Commit changes"**

If the same talk was given at multiple venues, create another folder
next to the first one (e.g., `your-talk-title/second-venue-year/index.md`).

### Adding a software page

1. Navigate to `EditMe/Software/`
2. Click **"Add file"** → **"Create new file"**
3. In the filename box, type: `your-software-name/index.md`
4. Paste this template and fill it in:

```yaml
---
title: "SOFTWARE NAME"
date: YYYY-MM-DD
authors:
  - "Gary King"
publication_types:
  - "software"
abstract: "ONE-SENTENCE DESCRIPTION OF WHAT THE SOFTWARE DOES."
links:
  - name: "Project Website"
    url: "https://YOUR-SOFTWARE-WEBSITE.com"
  - name: "GitHub"
    url: "https://github.com/YOUR-ORG/YOUR-REPO"
---
```

5. Click **"Commit changes"**
6. Also open `EditMe/Software/Data/software_legacy_rows.yaml`, click the pencil icon, and add a line like:

```yaml
- year: 2026
  slug: your-software-name
```

7. Click **"Commit changes"**

### Adding a featured image

To add a thumbnail image to any paper, talk, or software page:

1. Navigate to the folder that contains the `index.md` you just created
2. Click **"Add file"** → **"Upload files"**
3. Upload an image named exactly `featured.jpg` or `featured.png`
4. Click **"Commit changes"**

### Link types reference

When writing the `links:` section in any template:

| What you type | What button appears on the page |
|---|---|
| `type: pdf` | "Article" (or "Presentation", "Brief", etc. depending on content type) |
| `type: source` | "Publisher's Version" |
| `type: code` | "Code" |
| `name: "Any Label"` | A button with whatever label you typed |

For the `url:` value: if it starts with `files/` (no slash at the beginning), it points to a PDF you uploaded to `_site/static/files/`. Otherwise, use a full URL starting with `https://`.

</details>

---

<details>
<summary><h2 id="startups-section">6. Startups section</h2></summary>

The Startups section at `/startups/` showcases Gary's startup companies.
It has its own menu item and dedicated layout.

### Content

Each startup is a page bundle under `EditMe/Startups/<slug>/index.md`.
Currently:

| Startup | Weight | Has story? |
|---|---|---|
| Crimson Hexagon | 1 | Yes (Twitter thread) |
| Thresher | 2 | Yes (Twitter thread) |
| Learning Catalytics | 3 | Yes (Harvard Gazette article) |
| OpenScholar | 4 | No (external link only) |
| Perusall | 5 | No (external link only) |
| QuickCode | 6 | No (external link only) |

Front matter fields for startups:

```yaml
---
title: "Startup Name"
date: "2007-01-01"
weight: 1
summary: "Merged with Brandwatch, acquired by Cision"
external_site: "https://www.brandwatch.com/"
abstract: |-
  Full HTML story content here (rendered with markdownify).
  Use <p> tags for paragraph spacing.
image:
  filename: featured.png
  caption: "Photo credit text"
aliases:
  - /publication/old-slug/
---
```

- `weight` controls display order on `/startups/` (ascending).
- `summary` appears as a subtitle next to the title in the dropdown.
- `external_site` creates a "Visit site" link.
- `abstract` contains the full story content (HTML allowed; Hugo's
  `unsafe: true` goldmark setting is required).
- Startups without stories (OpenScholar, Perusall, QuickCode) have no
  `abstract` — they show only the dropdown with a "Visit site" link.

### Layout

- **List page:** `EditMe/UI/PerSectionLayouts/Startups/list.html` —
  renders each startup as an expandable `<details>` dropdown, sorted
  by `weight`. Includes JavaScript to auto-open a dropdown via URL
  hash (e.g. `/startups/#thresher`).
- **Single page:** `EditMe/UI/PerSectionLayouts/Startups/single.html` —
  redirects to the list page with an anchor
  (`/startups/#<slug>`).

### Homepage integration

The homepage (`EditMe/UI/PerSectionLayouts/HomePage/landing/list.html`)
shows startup dropdowns with a short excerpt and "Read more" links
pointing to `/startups/#<slug>`. The full stories live only on the
dedicated `/startups/` page.

### Hugo config

In `hugo.yaml`:
- Mount: `EditMe/Startups` → `content/startups`
- Mount: `EditMe/UI/PerSectionLayouts/Startups` → `layouts/startups`
- Menu item: `Startups` at weight 45
- Permalink: `startups: /startups/:slug/`

### Adding a new startup

1. Create `EditMe/Startups/<slug>/index.md` with the front matter above.
2. Set `weight` to position it in the list.
3. Optionally add a `featured.png` image in the same folder.
4. Run `python3 _automation/scripts/generate_mounts.py` if the folder
   structure changed.

</details>

---

<details>
<summary><h2 id="garyai-chatbot">7. GaryAI chatbot</h2></summary>

The site has an AI chatbot ("GaryAI") with two surfaces:

### Popup widget (every page)

A floating chat bubble that appears on every page.

- **Script:** `_site/static/js/gking-chat-widget.js`
- **Loaded in:** `layouts/baseof.html` (with `data-*` attributes for
  API URLs, bot name, welcome message, etc.)

### Dedicated page (`/ask-gary/`)

A full-page chat UI.

- **Content:** `EditMe/Misc/ask-gary/index.md` (minimal — just sets
  `type: chatbot`)
- **Layout:** `layouts/chatbot/single.html` (~900 lines of inline
  HTML/CSS/JS implementing the full chat interface)

### Backend

The chatbot backend runs on AWS Lambda. Endpoints are hardcoded in the
widget script and the chatbot layout:

- **Chat API:** `https://smf5e3hgygflv6o2nibp47vvse0digjb.lambda-url.us-east-2.on.aws/`
- **Feedback API:** `https://4jk1rwjz4a.execute-api.us-east-2.amazonaws.com/feedback`

Don't change these unless the AWS deployment changes.

### Mobile behavior

- On `/ask-gary/` desktop: the native chat UI is used; the popup
  widget button is hidden via JS.
- On `/ask-gary/` mobile: the native chat is hidden; the popup widget
  opens full-screen instead.

</details>

---

<details>
<summary><h2 id="featured-spotlight--see-also">8. Featured spotlight & See Also</h2></summary>

### Working Papers spotlight

The "Working Papers" section at the top of `/publication/` is controlled
by `EditMe/Writings/Data/featured_publications.yaml`:

```yaml
count: 5

order:
  - slug-of-pinned-paper-1
  - slug-of-pinned-paper-2

exclude:
  - slug-to-keep-out
```

How the displayed list is built:

1. Start with the manually curated `order` list.
2. Any journal-article publication NOT already in `order` or `exclude`
   is prepended by its **first-commit date** (newest first), so
   adding a fresh paper auto-promotes it.
3. The list is capped at `count` entries.

First-commit dates live in
`EditMe/Writings/Data/publication_first_commit.json` and are refreshed
automatically in CI by
`_automation/scripts/writings/compute_publication_first_commit.py`.

### See Also

The site automatically fills the "See Also" box at the bottom of every
paper, talk, and software page. Rules:

1. **Do nothing** — the site scans titles, authors, and tags to surface
   related content automatically.
2. **Force specific links** with front matter:
   ```yaml
   related_talks:    ["talk-slug-1", "talk-slug-2"]
   related_papers:   ["paper-slug-1"]
   related_software: ["software-slug-1"]
   related_datasets: ["dataset-slug-1"]
   ```
3. **Improve auto-matching** by adding shared `tags:` or `keywords:`.
4. The box shows at most 6 items, sorted explicit-first, then by match
   strength, then by year.

### Cross-linking papers and talks

```yaml
# In a publication (link to talks):
related_talks:
  - "talk-slug-1"

# In a talk (link to paper):
related_paper: "publication-slug"

# Harvard Dataverse link:
dataverse_url: "https://doi.org/10.7910/DVN/XXXXX"
dataverse_name: "Replication Data for: Paper Title"
```

</details>

---

<details>
<summary><h2 id="short-urls--redirects">9. Short URLs & redirects</h2></summary>

### How to add a redirect (short URL)

This lets you create a short URL like `gking.harvard.edu/quest` that
sends visitors to a specific page or external link.

1. Go to https://github.com/iqss-research/gking-site
2. Click into `EditMe/` → `Redirects/` → `Data/`
3. Click on `redirects.yaml`
4. Click the **pencil icon** (top right of the file) to edit
5. Scroll to the bottom of the file
6. Add a new entry like this (keeping the same spacing as existing entries):

```yaml
  - from: YOUR-SHORT-URL
    to:   https://DESTINATION-URL.com
    note: "SHORT DESCRIPTION OF WHAT THIS REDIRECT IS FOR"
```

For example, if you want `gking.harvard.edu/quest` to go to a paper page:

```yaml
  - from: quest
    to:   /publication/quest/
    note: "Short URL for the Quest paper"
```

Or to an external link:

```yaml
  - from: rd
    to:   https://docs.google.com/document/d/abcdef123/edit
    note: "Research Directions living doc"
```

7. Click **"Commit changes"**

The redirect will start working after the site rebuilds (~3 minutes).

### Alternative: adding a short URL directly to a paper

If you just want a short URL for a specific paper:

1. Open that paper's `index.md` file on GitHub
2. Click the **pencil icon** to edit
3. Add these lines inside the `---` section at the top:

```yaml
aliases:
  - /your-short-url/
```

4. Click **"Commit changes"**

### Already-set-up Drupal redirects

136 redirects from the old Drupal site are already configured. You don't
need to do anything about these.

</details>

---

<details>
<summary><h2 id="research-areas-homepage-navigation--other-pages">10. Research areas, homepage, navigation & other pages</h2></summary>

### Research areas

Research-area groupings live in
`EditMe/ResearchAreas/Data/research_areas.json` with two top-level keys
(`methods` and `applications`), each containing areas with subcategories
and `papers` lists:

```json
{ "title": "Paper Title", "section": "publication", "slug": "paper-slug" }
```

`section` is one of `publication`, `talk`, or `software`.

### Homepage

The homepage at `EditMe/HomePage/_index.md` is minimal. All visual blocks
are rendered by
`EditMe/UI/PerSectionLayouts/HomePage/landing/list.html`, which pulls
from:

- `EditMe/Writings/` (newest entries by date)
- `EditMe/Writings/Data/writings_legacy_map.json` (for "Books")
- `EditMe/Writings/Data/featured_publications.yaml` (for spotlight)
- `EditMe/ResearchAreas/Data/research_areas.json` (for the grid)

Most homepage updates happen by editing those data files, not the
homepage itself.

### Navigation menu

Defined in `hugo.yaml` under `menus.main`. Current menu (by weight):

| Weight | Name | URL |
|---|---|---|
| 10 | Bio & C.V. | `/bio/` |
| 20 | Writings | `/publication/` |
| 30 | Research Areas | `/#research-areas` |
| 40 | Software | `/software/` |
| 45 | Startups | `/startups/` |
| 50 | Dataverse | `/dataverse/` |
| 60 | People | `/research-group/` |
| 70 | Teaching | `/teaching/` |
| 75 | GaryAI | `/ask-gary/` |
| 80 | Contact | `/contact/` |

### Button labels

Controlled by `_site/i18n/en.yaml`:

```yaml
- id: btn_pdf
  translation: Article
- id: btn_source
  translation: "Publisher's Version"
```

The primary button label also changes automatically based on
`publication_types` — see [Publication types reference](#publication-types-reference).

### Other pages

| Page | File |
|---|---|
| Teaching | `EditMe/Teaching/_index.md` |
| Per-class sub-page | `EditMe/Teaching/<class>/index.md` |
| Contact | `EditMe/Contact/index.md` |
| Dataverse | `EditMe/Dataverse/index.md` |
| Research Group landing | `EditMe/People/ResearchGroup/index.md` |
| Bio | `EditMe/Bio/index.md` |
| Blog posts | `EditMe/Blog/<slug>/index.md` |

The "Advice and Suggestions" links live at the bottom of
`EditMe/Teaching/_index.md` under `<h2 id="advice">`.

### Updating bio / CV

- **Bio text:** edit `EditMe/Bio/index.md`.
- **CV PDF:** replace `_site/static/files/vitae.pdf`.
- **Bio photo:** replace `_site/static/images/gking-bio-photo.jpg`.

</details>

---

<details>
<summary><h2 id="people--research-group">11. People & research group</h2></summary>

### Profiles

Each person has a folder at `EditMe/People/Profiles/<slug>/index.md`:

```yaml
---
title: "Jane Doe"
type: "people"
role: "Harvard University (Assistant Professor of Government)"
research_group_category: "collaborators"
website: "https://janedoe.com/"
---
```

Valid `research_group_category` values:
`alumni_students`, `alumni_postdocs`, `collaborators`.

### Research group roster

The filterable roster at `/research-group/` is driven by
`EditMe/People/Data/research_group.json`:

```json
{
  "slug": "jane-doe",
  "name": "Jane Doe",
  "affiliation": "Harvard University",
  "research_group_categories": ["collaborators"],
  "last_name_range": "D-G"
}
```

`last_name_range` must be one of:
`A-C`, `D-G`, `H-J`, `K-L`, `M-P`, `Q-S`, `T-V`, `W-Z`.

### Current Research Group box

The "Current Research Group" box at the top of `/research-group/` is
curated by hand in
`EditMe/UI/PerSectionLayouts/ResearchGroup/single.html`.

</details>

---

<details>
<summary><h2 id="claude-prompts-for-common-tasks">12. Claude prompts for common tasks</h2></summary>

These are copy-paste prompts. To use one:

1. Copy the prompt text (everything inside the gray box)
2. Replace every **`XXX`** with your actual information
3. If the prompt says "Attach:" — drag that file into the same message
4. Paste into Claude or Cursor and send

---

### Add a new journal article

Attach: the article PDF.

```
Add a new journal article to gking-site.

- Title: XXX
- Authors: XXX (comma-separated)
- Publication venue: XXX (e.g. "American Political Science Review, 111, 3, Pp. 484–501")
- Year: XXX
- Abstract: XXX
- Publisher's DOI or URL: XXX
- Dataverse DOI (if any): XXX
- Topic: XXX (pick one: AnchoringVignettes, AutomatedTextAnalysis, CausalInference, EcologicalInference, EventCountsAndDurations, MissingDataMeasurementErrorPrivacy, QualitativeResearch, RareEvents, SurveyResearch, UnifyingStatisticalAnalysis, or Other)

The article PDF is attached. Commit and push.
```

### Add a new book

```
Add a new book to gking-site.

- Title: XXX
- Authors: XXX
- Publisher: XXX
- Year: XXX
- Abstract: XXX
- Publisher's URL (if any): XXX

Commit and push.
```

### Add a new presentation

Attach: the slides PDF.

```
Add a new presentation to gking-site.

- Talk title: XXX
- Venue / event name: XXX
- Year: XXX
- Abstract: XXX

The slides PDF is attached. Commit and push.
```

### Add a new court brief

Attach: the brief PDF.

```
Add a new court brief to gking-site.

- Title: XXX
- Authors: XXX (all signatories)
- Year: XXX
- Abstract: XXX

The brief PDF is attached. Commit and push.
```

### Add a new patent

Attach: the patent PDF.

```
Add a new patent to gking-site.

- Title: XXX
- Inventors: XXX
- Year: XXX
- Patent number: XXX

The patent PDF is attached. Commit and push.
```

### Add a new software package page

```
Add a new software package page to gking-site.

- Software name: XXX
- Authors / maintainers: XXX
- Year: XXX
- External website URL: XXX
- Brief description: XXX

Commit and push.
```

### Replace or update a PDF

Attach: the new PDF.

```
Replace the PDF for an existing item on gking-site.

- Item title: XXX
- Type: XXX (article / book / presentation / brief / patent)

Find the item, replace the PDF keeping the same filename. Commit and push.
```

### Add a short URL (redirect)

```
Add a new short URL redirect to gking-site.

- Short URL path: XXX (this becomes gking.harvard.edu/XXX)
- Destination: XXX (full URL or site path like /publication/quest/)

Commit and push.
```

### Add a paper to a Research Area

```
Add a paper to a Research Area on gking-site.

- Paper title: XXX
- Research area name: XXX
- Subcategory: XXX

Commit and push.
```

### Other tasks

```
Update the Bio/CV page on gking-site.
Changes to make: XXX
```

```
Add a new blog post to gking-site.
- Title: XXX
- Date: XXX (YYYY-MM-DD)
- Content: XXX
```

### Update the weekly audit script

```
Update the weekly audit script (_automation/scripts/audit_site.py) on gking-site.

I want to add a new check: XXX

The script runs every Monday via GitHub Actions and emails a report.
It currently checks: research area coverage, legacy map sync, PDF integrity,
broken redirects, duplicate titles, empty dirs, dependency versions, and
broken external links. Add the new check and make sure it integrates with
the existing report format (level: ERROR/WARN/INFO, category, title, details list).

Commit and push.
```

### Tips

- **To find an existing item:** ask Claude to search by title.
- **To preview before publishing:** ask Claude to run `hugo server`.
- **Multiple changes at once:** combine prompts in one message.

</details>

---

<details>
<summary><h2 id="automation--cicd">13. Automation & CI/CD</h2></summary>

### GitHub Actions workflows

Two workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `deploy.yml` | Push to `main` | Build Hugo + Pagefind, run `build_redirects.py` + `apply_rewrites.py` + `compute_publication_first_commit.py`, deploy to GitHub Pages. |
| `weekly-audit.yml` | Weekly (Monday 10am ET) | Runs the site audit script and emails the report to ktoth@iq.harvard.edu (CC: king@harvard.edu). |

### Weekly site audit

The audit script (`_automation/scripts/audit_site.py`) automatically
checks for problems every Monday. It sends an email report covering:

1. Papers not assigned to any research area
2. Legacy map entries out of sync with content folders
3. PDFs referenced in content but missing from `_site/static/files/`
4. PDFs in `static/files/` not referenced by any page
5. Internal redirect targets that point to non-existent pages
6. Duplicate titles (possible accidental copies)
7. Empty directories that can be cleaned up
8. Dependency versions (Hugo, Hugo Blox, Pagefind) and whether updates are available
9. Broken external links (checks all URLs in content files)

**To run locally:**

```bash
cd hugo-site
python3 _automation/scripts/audit_site.py
```

To skip the slow external link check:

```bash
SKIP_LINK_CHECK=1 python3 _automation/scripts/audit_site.py
```

**Email setup:** The workflow needs 4 repository secrets to send email
(Settings → Secrets → Actions): `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`,
`SMTP_PASSWORD`. If not configured, it falls back to creating a GitHub Issue.

### Auto-push hook

`_automation/scripts/enable-auto-push.sh` registers `.githooks/post-commit`
so every `git commit` automatically pushes. One-off skip:
`SKIP_AUTO_PUSH=1 git commit -m "wip"`. Turn off permanently:
`git config hooks.skip-auto-push true`.

### Helper scripts

All Python helpers live under `_automation/scripts/`. Most need
`pip install -r _automation/scripts/requirements.txt`.

| Script | What it does |
|---|---|
| `generate_mounts.py` | Regenerate `module.mounts` in `hugo.yaml` after adding/removing `EditMe/` folders. `--check` to verify. |
| `build_redirects.py` | Generate redirect stubs from `redirects.yaml`. Runs in CI. |
| `apply_rewrites.py` | Post-build: replace redirect stubs with rendered HTML. Runs in CI. |
| `quick_add.py` | Scaffold new content (`paper`, `talk`, `book`, `software`, `patent`). `--dry-run` to preview. |
| `regroup_articles.py` | Sort `Unsorted/` articles into `<Topic>/<Decade>/`. |
| `regroup_writings.py` | Sort into `Books/`, `Reports/`, `Patents/`, etc. |
| `regroup_presentations.py` | Cluster talks by title-slug. |
| `writings/compute_publication_first_commit.py` | Refresh spotlight ordering. Runs in CI. |
| `people/sync_research_group.py` | Refresh `research_group.json` from roster. |

</details>

---

<details>
<summary><h2 id="architecture--principles">14. Architecture & principles</h2></summary>

Key architectural rules distilled from building this site:

1. **Content is updated through Claude or direct GitHub edits.**
   Describe a change to Claude in plain English or edit Markdown files
   directly on GitHub. No terminal or special tooling is needed.

2. **Content and presentation are fully separated.** Content is
   `EditMe/**/*.md` with YAML front matter. Templates in `layouts/` and
   CSS in `assets/css/` render it. A content change never touches a
   template.

3. **Deployment is automatic on push to `main`.** No manual build step
   is ever needed for normal content updates.

4. **The `EditMe/` umbrella scales.** One place to look for everything
   editable, one menu-driven sub-folder per concept. Within
   `EditMe/Writings/`, papers nest by `<Type>/<Topic>/<Decade>/<slug>/`
   so even the biggest section stays browsable.

5. **Mounts are transparent for content URLs.** Permalinks are driven by
   the **target** in `module.mounts`, not by where files live on disk.
   `EditMe/Writings/Articles/CausalInference/2010s/foo/` mounts onto
   `content/publication/foo` and serves at `/publication/foo/`.

6. **Three folders MUST stay at the project root:**
   - `layouts/` — HugoBlox's `get_hook` partial uses `os.ReadDir`.
   - `assets/` — HugoBlox's `site_head.html` uses `fileExists`.
   - `.github/`, `.githooks/` — GitHub/git expect literal paths.

7. **Never write `/foo` literally** in templates if it needs to resolve
   under `baseURL`. Use `relURL` without a leading slash:
   `{{ "pagefind/pagefind.js" | relURL }}`.

8. **Preserve URLs.** External links (CVs, citations, search indexes)
   point at the original URLs. Silent URL changes become 404s.

9. **`hugo.yaml`'s `module.mounts` block is auto-generated.** Don't
   hand-edit it. Run `python3 _automation/scripts/generate_mounts.py`
   after adding or removing `EditMe/` folders.

10. **Vendored theme in `_vendor/`.** Freezes the theme version so a
    deploy doesn't break if upstream changes. To customize a Blox
    partial, copy it from `_vendor/.../layouts/_partials/<path>` to
    `layouts/_partials/<path>` and edit the project copy.

</details>

---

<details>
<summary><h2 id="local-development">15. Local development</h2></summary>

### First-time setup (do this once)

1. Open Terminal (on Mac: press Cmd+Space, type "Terminal", press Enter)
2. Type the following commands one at a time, pressing Enter after each:

```bash
git clone https://github.com/iqss-research/gking-site.git
```

You should see a download progress message. When it finishes:

```bash
cd gking-site/hugo-site
```

3. Install Hugo (the tool that builds the website). Type:

```bash
brew install hugo
```

If you get "brew: command not found", first install Homebrew by going to https://brew.sh and following their one-line install command, then try again.

4. (Optional) Set up auto-push so every commit automatically publishes:

```bash
bash _automation/scripts/enable-auto-push.sh
```

### Previewing the site on your computer

1. Open Terminal
2. Go to the project folder:

```bash
cd gking-site/hugo-site
```

3. Start the local preview server:

```bash
hugo server
```

4. You should see a message that says "Web Server is available at http://localhost:1313/"
5. Open your web browser and go to: http://localhost:1313/
6. You'll see the site. Any changes you make to files will show up instantly in the browser.
7. When done previewing, go back to Terminal and press Ctrl+C to stop the server.

### Making changes and publishing them

1. Open Terminal and go to the project folder:

```bash
cd gking-site/hugo-site
```

2. Before making changes, get the latest version:

```bash
git pull
```

3. Make your edits to whatever files you need to change
4. When done, save your changes:

```bash
git add -A
git commit -m "describe what you changed here"
```

If you set up auto-push in the setup step, this will automatically publish your changes. Otherwise, type:

```bash
git push
```

The site will rebuild and go live in ~3 minutes.

### Looking up the history of a file

To see who changed a file and when:

```bash
git log --follow -- EditMe/Writings/Articles/CausalInference/2020s/your-paper/index.md
```

</details>

---

<details>
<summary><h2 id="troubleshooting">16. Troubleshooting</h2></summary>

**"I committed and nothing changed on the site."**
Give it 3–4 minutes, then check
<https://github.com/iqss-research/gking-site/actions>. A red X means a
build error (usually a YAML front-matter typo).

**"`git commit` succeeded but didn't auto-push."**
The post-commit hook only pushes if the branch has an upstream. Run
`git push -u origin main` once. Check that
`git config core.hooksPath` prints `.githooks`.

**"A PDF returns 404 on the live site."**
Confirm the file is in `_site/static/files/` and the `url:` in the
page's `links:` starts with `files/` (no leading slash).

**"The 'See Also' box is empty or wrong."**
Add shared `tags:` or pin specific items with `related_papers`, etc.

**"Search finds nothing."**
The Pagefind index is rebuilt each deploy. Wait for Actions to finish
and hard-refresh.

**"I accidentally broke the site."**
From terminal: `git revert <sha>`. Or on github.com: click the commit →
**Revert**. After the build finishes, the site is restored.

</details>

---

<details>
<summary><h2 id="publication-types-reference">17. Publication types reference</h2></summary>

Use exactly one of these strings in `publication_types:`.

### Primary (recommended)

| Type | Writings tab | Primary button label |
|---|---|---|
| `journal_article` | Journal Articles | Article |
| `book` | Books & Chapters | Article |
| `book_chapter` | varies | Book Chapter |
| `working_paper` | Working Papers spotlight | Article |
| `conference_paper` | Other | Article |
| `report` | Other | Article |
| `data` | Other | Article |
| `software` | Software | Article |
| `court_brief` | Court Briefs | Brief |
| `patent` | Patents | Patent |
| `presentation` | Presentations | Presentation |
| `poster` | Other | Poster |
| `letter` | Other | Letter |
| `other` | Other | Article |

### Also recognised (legacy / Drupal)

`conference_proceedings`, `miscellaneous`, `newspaper_article`,
`unpublished`, `web_article`, `website`.

### Notes

- The primary button label changes automatically based on
  `publication_types` (handled in `layouts/_partials/page_links.html`).
- For `/publication/` section entries, the Writings tab placement is
  driven by `EditMe/Writings/Data/writings_legacy_map.json`, which
  takes precedence over front-matter `publication_types` for tab routing.

</details>

---

## Audit reports

Point-in-time audit reports are kept in `docs/audits/` for historical
reference:

- [`docs/audits/SITE_AUDIT.md`](docs/audits/SITE_AUDIT.md) — April 2026
  site audit (broken links, performance, UX recommendations).
- [`docs/audits/CV_VS_SITE.md`](docs/audits/CV_VS_SITE.md) — CV vs site
  reconciliation.
- [`docs/audits/CLASSIFY_REVIEW.md`](docs/audits/CLASSIFY_REVIEW.md) —
  Post-auto-fix classification notes.
