# gking-site

Source for <https://gking.harvard.edu/> — Gary King's academic website,
built with Hugo + Hugo Blox and deployed to GitHub Pages via GitHub Actions.

> **Repository:** <https://github.com/iqss-research/gking-site> ·
> **Live site:** <https://gking.harvard.edu/> ·
> **Shortcut:** <https://GaryKing.org>

Every push to `main` triggers a live deploy (~3 minutes). There is no
staging environment.

---

**This file is the single reference for human maintainers.** Click any
section heading below to expand it. For AI-agent-specific workflow rules
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
<summary><h2>1. Overview</h2></summary>

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

- **Terminal** — edit files in your editor, `git commit`, and (with the
  auto-push hook) the change deploys automatically.
- **GitHub.com** — pencil-icon edits in the browser. No local tools
  needed. Works from a phone or borrowed laptop.

Either path makes the change live within ~3 minutes.

</details>

---

<details>
<summary><h2>2. Repository layout</h2></summary>

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
├── _automation/                      ← maintenance + intake bots
│   ├── intake/                       ← drop-zone for auto-import (paper/talk/book)
│   │   ├── talk/
│   │   └── book/
│   └── scripts/                      ← every Python helper
│       ├── writings/                 ← intake_publication.py, DOI fillers, audits
│       ├── people/                   ← profile sync, research-group scrapers
│       └── (top-level)               ← build_redirects.py, generate_mounts.py, …
│
├── docs/audits/                      ← point-in-time audit reports
├── .github/workflows/                ← CI/CD: deploy, intake, link-check
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
<summary><h2>3. Where do I find X?</h2></summary>

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
| Intake bot upload folder | `_automation/intake/` (PDFs land here in PRs) |
| GitHub workflows | `.github/workflows/` |
| Site-wide partials / shortcodes | `layouts/_partials/`, `layouts/shortcodes/` |
| GaryAI chatbot page | `EditMe/Misc/ask-gary/index.md` + `layouts/chatbot/single.html` |
| GaryAI popup widget | `_site/static/js/gking-chat-widget.js` |
| Google Analytics tracking | `layouts/_partials/hooks/head-start/google-analytics.html` (tag `G-NDZT9P326S`) |
| The "upload a paper" form | `.github/ISSUE_TEMPLATE/upload-paper.yml` |
| What runs when something is pushed to `main` | `.github/workflows/deploy.yml` |
| Navigation menu | `hugo.yaml` → `menus.main` |
| Button label overrides ("Article", etc.) | `_site/i18n/en.yaml` |

</details>

---

<details>
<summary><h2>4. Quick add (every content type)</h2></summary>

Five content types, three entry points. **The simplest path for any PDF
is the Issue Form — no terminal, no folder navigation.**

| Content type | Easiest (any browser) | Terminal | No PDF / metadata-only |
|---|---|---|---|
| Paper / article | [Issue Form](#issue-form) | `_automation/intake/<file>.pdf` | `quick_add.py paper …` |
| Talk / presentation | [Issue Form](#issue-form) | `_automation/intake/talk/<file>.pdf` | `quick_add.py talk …` |
| Book | [Issue Form](#issue-form) | `_automation/intake/book/<file>.pdf` | `quick_add.py book …` |
| Software / R package | _(URL-based — no PDF)_ | — | `quick_add.py software --github …` |
| Patent | [Issue Form](#issue-form) | `_automation/intake/<file>.pdf` then `/type patent` | `quick_add.py patent --source …` |

After every shortcut, `git commit` + push and the deploy workflow
makes it live in ~3 minutes.

### Issue Form

1. Open <https://github.com/iqss-research/gking-site/issues/new/choose>
   and click **Upload a paper**.
2. Pick the **Type**, drag the PDF in, optionally type a short URL,
   and **Submit new issue**.
3. Wait ~2 minutes. The bot downloads the PDF, runs Crossref lookup,
   extracts figures, and **opens a draft PR** with the metadata,
   featured image, and a figure-picker grid.
4. Edit anything via the **Files changed** pencil or post
   [slash commands](#slash-commands) on the PR.
5. Click **Merge pull request**. Live in ~3 more minutes.

### Terminal: drop a PDF

```bash
git checkout -b add-my-paper
cp ~/Downloads/paper.pdf _automation/intake/      # paper
cp ~/Downloads/slides.pdf _automation/intake/talk/ # talk
cp ~/Downloads/book.pdf _automation/intake/book/   # book
git add -A && git commit -m "Drop PDF for auto-import"
git push -u origin add-my-paper
gh pr create --fill
```

The bot pushes a follow-up commit with the generated `index.md`,
moved PDF, legacy-map entry, and featured image.

### Terminal: quick_add.py (no PDF)

```bash
python3 _automation/scripts/quick_add.py paper \
    --title "An Example Paper" --slug an-example-paper \
    --year 2026 --authors "Gary King; Jane Doe" \
    --doi 10.1017/example --pdf ~/Downloads/example.pdf
git add -A && git commit -m "Add example paper"
```

Works for `paper`, `talk`, `book`, `software`, `patent`. Add `--dry-run`
to preview without writing files.

### Slash commands

Post a comment on an intake PR with one or more commands. The bot picks
them up within ~30 seconds:

| Command | What it does |
|---|---|
| `/title <text>` | Replace the title |
| `/authors A; B; C` | Set the full authors list (use `;` separator) |
| `/year <YYYY>` or `/date <YYYY-MM-DD>` | Set the publication date |
| `/abstract <text>` | Replace the abstract (spans to next `/cmd` or end of comment) |
| `/publication <text>` | Replace the citation line |
| `/doi <DOI>` | Set the DOI + rewrite Publisher's Version link |
| `/type <slug>` | Change the publication type + re-route Writings tab |
| `/figure <N>` | Swap featured image for Figure N from the PDF |
| `/alias </foo/>` | Add a vanity short URL to `aliases:` |
| `/supplement <url> \| <label>` | Append a supplementary-material link |

### What happens automatically

Both the Issue Form and `_automation/intake/` flows share the same
auto-import code:

- Detects content kind from the form dropdown or `_automation/intake/` subfolder.
- Looks up DOI / Crossref metadata (skipped for talks).
- Generates slug, creates `index.md` under `EditMe/Writings/`.
- Moves PDF to `_site/static/files/<slug>.pdf`.
- Adds entry to `writings_legacy_map.json`.
- Extracts featured image from the PDF.
- Renders every numbered figure into `_intake_figures/` for the
  figure-picker grid.

After merging, run the appropriate regroup script to file the content
into the correct `<Type>/<Topic>/<Decade>/` folder:

```bash
python3 _automation/scripts/regroup_articles.py     # for articles
python3 _automation/scripts/regroup_writings.py     # for books/reports/patents
python3 _automation/scripts/regroup_presentations.py # for talks
```

</details>

---

<details>
<summary><h2>5. Manual content templates</h2></summary>

Use these when the bot can't find Crossref data or you want fine-grained
control.

### Paper / article / book

**Step 1** — Put the PDF at `_site/static/files/<slug>.pdf`.

**Step 2** — Create the page folder:

```
EditMe/Writings/Articles/<Topic>/<Decade>/<slug>/index.md
EditMe/Writings/Books/<Decade>/<slug>/index.md
EditMe/Writings/Reports/<Decade>/<slug>/index.md
EditMe/Writings/Patents/<Decade>/<slug>/index.md
EditMe/Writings/CourtBriefs/<Decade>/<slug>/index.md
```

Topic folders for Articles: `AnchoringVignettes`, `AutomatedTextAnalysis`,
`CausalInference`, `EcologicalInference`, `EventCountsAndDurations`,
`MissingDataMeasurementErrorPrivacy`, `QualitativeResearch`, `RareEvents`,
`SurveyResearch`, `UnifyingStatisticalAnalysis`, `Other`.

If unsure, use `EditMe/Writings/Articles/Unsorted/<slug>/` and run
`regroup_articles.py` afterwards.

**Step 3** — Paste this template and edit:

```yaml
---
title: "Full Paper Title"
date: 2026-01-15
authors:
  - "Gary King"
  - "Coauthor Name"
publication_types:
  - "journal_article"
publication: "Journal Name, Volume(Issue), pages"
abstract: |-
  Multi-paragraph abstract goes here.

  Paragraph two, etc.
doi: "10.xxxx/xxxxx"
links:
  - type: pdf
    url: "files/my-paper.pdf"
  - type: source
    url: "https://doi.org/10.xxxx/xxxxx"
  - name: "Supplementary Material"
    url: "files/my-paper-supp.pdf"
---
```

**Step 4** — Pick the Writings tab by adding an entry to
`EditMe/Writings/Data/writings_legacy_map.json`:

```json
"<slug>": { "tab": "<tab-id>", "drupal": "<type>" }
```

| `drupal` value | `tab` id | Writings page tab |
|---|---|---|
| `journal_article` | `journal` | Journal Articles |
| `working_paper` | `journal` | Working Papers spotlight |
| `book` | `book` | Books & Chapters |
| `book_chapter` | `journal` or `other` | varies |
| `presentation` | `presentation` | Presentations |
| `software` | `software` | Software |
| `patent` | `patent` | Patents |
| `court_brief` | `courtbrief` | Court Briefs |
| anything else | `other` | Other |

**Step 5** (optional) — Drop a `featured.jpg` or `featured.png` next to
`index.md`.

### Talk / presentation

```
EditMe/Writings/Presentations/<title-slug>/<venue-slug>/index.md
```

```yaml
---
title: "Talk Title"
date: 2026-03-15
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

Talks cluster by title-slug: multiple venues for the same talk live as
sibling sub-folders under one shared title-slug folder.

### Software / R package page

```
EditMe/Software/<slug>/index.md
```

```yaml
---
title: "Software Name"
date: 2024-01-01
authors:
  - "Gary King"
publication_types:
  - "software"
abstract: "Short description."
links:
  - name: "Project Website"
    url: "https://my-software-site.com"
  - name: "GitHub"
    url: "https://github.com/IQSS/my-tool"
---
```

Also add a row to `EditMe/Software/Data/software_legacy_rows.yaml`
(`year`, `slug`, optional `status: older`) and an entry in
`writings_legacy_map.json` with `"tab": "software"`.

### Link types

- `type: pdf` → "Article" button (label changes by publication type — see [Publication types reference](#publication-types-reference))
- `type: source` → "Publisher's Version" button
- `type: code` → "Code" button
- `name: "Custom Label"` → custom-labeled button

`files/...` URLs (no leading `/`) resolve to `_site/static/files/`.

</details>

---

<details>
<summary><h2>6. Startups section</h2></summary>

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
<summary><h2>7. GaryAI chatbot</h2></summary>

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
<summary><h2>8. Featured spotlight & See Also</h2></summary>

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
<summary><h2>9. Short URLs & redirects</h2></summary>

### Adding a redirect

Edit `EditMe/Redirects/Data/redirects.yaml`:

```yaml
redirects:
  - from: rd
    to:   https://docs.google.com/document/d/abcdef123/edit
    note: "Research Directions living doc"

  - from: quest
    to:   /publication/quest/
    status: 301
    note: "Short URL for the Quest paper"
```

Fields:

- `from` (required) — URL path to own. Case-sensitive.
- `to` (required) — full external URL or internal path.
- `status` (optional) — `301` (default), `302`/`307`, `308`.
- `note` (optional) — reminder to your future self.

The generator (`_automation/scripts/build_redirects.py`) runs in CI on
every deploy. After deploy, `apply_rewrites.py` replaces internal
redirect stubs with actual page content (so the address bar keeps the
short URL).

### Alternative: aliases in front matter

For paper-specific short URLs, add to the paper's `index.md`:

```yaml
aliases:
  - /quest/
```

Hugo generates the redirect automatically.

### Preserved Drupal URLs

136 redirects from the old Drupal site are already restored in
`redirects.yaml`. The import script is
`_automation/scripts/import_drupal_redirects.py`.

</details>

---

<details>
<summary><h2>10. Research areas, homepage, navigation & other pages</h2></summary>

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
<summary><h2>11. People & research group</h2></summary>

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
<summary><h2>12. Claude prompts for common tasks</h2></summary>

Copy-paste any prompt below into Claude or Cursor. Replace every
**`XXX`** with your actual information. Where a prompt says to
**upload** a file, attach it to the same message.

### Add a new journal article

**Upload:** the article PDF.

```
Add a new journal article to gking-site. Here are the details:

- Title: XXX
- Authors: XXX (comma-separated)
- Publication venue: XXX (e.g. "American Political Science Review, 111, 3, Pp. 484–501")
- Year: XXX
- Abstract: XXX
- Publisher's DOI or URL: XXX
- Dataverse DOI (if any): XXX

The article PDF is attached.

Place it in EditMe/Writings/Articles/ under the correct topic folder and decade.
The topic folders are: AnchoringVignettes, AutomatedTextAnalysis, CausalInference,
EcologicalInference, EventCountsAndDurations, MissingDataMeasurementErrorPrivacy,
QualitativeResearch, RareEvents, SurveyResearch, UnifyingStatisticalAnalysis, or
Other. The topic for this paper is: XXX

Create a slug, write index.md with standard front matter, put the PDF in
_site/static/files/. Commit and push.
```

### Add a new book

```
Add a new book to gking-site. Here are the details:

- Title: XXX
- Authors: XXX
- Publisher: XXX
- Year: XXX
- Abstract: XXX
- Publisher's URL (if any): XXX

Place it in EditMe/Writings/Books/<Decade>/<slug>/index.md with
publication_types: book. Commit and push.
```

### Add a new presentation

**Upload:** the slides PDF.

```
Add a new presentation to gking-site. Here are the details:

- Talk title: XXX
- Venue / event name: XXX
- Year: XXX
- Abstract: XXX
- Related publication slug (if based on a paper already on the site): XXX

The slides PDF is attached.

Presentations live in EditMe/Writings/Presentations/<title-slug>/<venue-slug>/.
Put the PDF in _site/static/files/. Commit and push.
```

### Add a new court brief

**Upload:** the brief PDF.

```
Add a new court brief to gking-site.

- Title: XXX
- Authors: XXX (all signatories)
- Year: XXX
- Abstract: XXX

Place it in EditMe/Writings/CourtBriefs/<Decade>/<slug>/index.md with
publication_types: court_brief. Put the PDF in _site/static/files/.
Commit and push.
```

### Add a new patent

**Upload:** the patent PDF.

```
Add a new patent to gking-site.

- Title: XXX
- Inventors: XXX
- Year: XXX
- Patent number: XXX

Place it in EditMe/Writings/Patents/<Decade>/<slug>/index.md with
publication_types: patent. Put the PDF in _site/static/files/.
Commit and push.
```

### Add a new software package page

```
Add a new software package page to gking-site.

- Software name: XXX
- Authors / maintainers: XXX
- Year: XXX
- External website URL: XXX
- Brief description: XXX

Create EditMe/Software/<package-slug>/index.md with a "site" link.
Commit and push.
```

### Replace or update a PDF

**Upload:** the new PDF.

```
Replace the PDF for an existing item on gking-site.

- Item title: XXX
- Type: XXX (article / book / presentation / brief / patent)

Find the item's index.md under EditMe/Writings/. Replace the PDF in
_site/static/files/ keeping the same filename. Commit and push.
```

### Add a short URL (redirect)

```
Add a new short URL redirect to gking-site.

- Short URL path: XXX (e.g. "privacy" → gking.harvard.edu/privacy/)
- Target: XXX (internal path or external URL)

Add to EditMe/Redirects/Data/redirects.yaml. Commit and push.
```

### Add a paper to a Research Area

```
Add a paper to one of the Research Areas on gking-site.

- Paper title: XXX
- Paper slug: XXX
- Research area name: XXX
- Subcategory: XXX

Edit EditMe/ResearchAreas/Data/research_areas.json. Commit and push.
```

### Other common tasks

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

### Tips

- **Finding an existing item:** ask Claude to search by title.
- **Previewing locally:** ask to run `hugo server` before pushing.
- **Multiple changes at once:** combine prompts in one message.

</details>

---

<details>
<summary><h2>13. Automation & CI/CD</h2></summary>

### GitHub Actions workflows

Six workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `deploy.yml` | Push to `main` | Build Hugo + Pagefind, run `build_redirects.py` + `apply_rewrites.py` + `compute_publication_first_commit.py`, deploy to GitHub Pages. |
| `intake-publication.yml` | PR adds PDF in `_automation/intake/` | Auto-import: Crossref lookup, `index.md` generation, featured image, figure extraction. |
| `intake-from-issue.yml` | Issue with `intake` label | Same auto-import, triggered from Issue Form. Opens a draft PR automatically. |
| `intake-edit.yml` | PR comment with `/` commands | Applies slash commands (`/title`, `/authors`, etc.) to the PR's `index.md`. |
| `cleanup-intake-figures.yml` | Push to `main` | Removes `_intake_figures/` directories after intake PRs merge. |
| `link-check.yml` | Weekly (Monday 09:00 UTC) | Checks all external URLs in content files; opens/updates a GitHub Issue if broken. |

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
| `apply_pr_edits.py` | Process slash commands from PR comments. Used by CI. |
| `import_drupal_redirects.py` | Recover redirects from old Drupal site. |
| `regroup_articles.py` | Sort `Unsorted/` articles into `<Topic>/<Decade>/`. |
| `regroup_writings.py` | Sort into `Books/`, `Reports/`, `Patents/`, etc. |
| `regroup_presentations.py` | Cluster talks by title-slug. |
| `regroup_presentations_fuzzy.py` | Second-pass fuzzy merge of talk folders. `--dry-run` first. |
| `fix_mojibake_markdown.py` | Repair UTF-8 mojibake across markdown files. |
| `writings/intake_publication.py` | Core PDF intake pipeline (used by CI and locally). |
| `writings/fill_publication_from_doi.py` | Fill `publication:` line from Crossref. |
| `writings/repair_publication_links.py` | Audit and rewrite broken external URLs. |
| `writings/audit_writings_citations.py` | Cross-reference publications with Crossref. |
| `writings/add_featured_from_pdf.py` | Generate `featured.png` from PDF page 1. |
| `writings/compute_publication_first_commit.py` | Refresh spotlight ordering. Runs in CI. |
| `people/sync_research_group.py` | Refresh `research_group.json` from roster. |
| `people/enrich_people_profiles.py` | Fill profile stubs from upstream sources. |

</details>

---

<details>
<summary><h2>14. Architecture & principles</h2></summary>

Key architectural rules distilled from building this site:

1. **The site owner updates content by committing Markdown on GitHub.**
   If a terminal is needed to publish a paper, the architecture has
   failed.

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
<summary><h2>15. Local development</h2></summary>

### One-time setup

```bash
git clone https://github.com/iqss-research/gking-site.git
cd gking-site/hugo-site
brew install hugo    # macOS — Hugo 0.160.1 extended

# Install the auto-push hook (optional):
_automation/scripts/enable-auto-push.sh
```

### Daily flow

```bash
git pull                               # before you start
# …edit files…
git add -A && git commit -m "message"  # auto-push sends it
```

### Local preview

```bash
hugo server    # http://localhost:1313/ with live reload
```

### Production build (rare; CI does this)

```bash
hugo --gc --minify --baseURL "https://gking.harvard.edu/"
npx pagefind --site public
```

### Tracing history across renames

The 2026 EditMe/ reorg moved nearly every file with `git mv`:

```bash
git log --follow -- EditMe/Writings/Articles/<Topic>/<Decade>/<slug>/index.md
git blame --follow EditMe/Writings/Articles/<Topic>/<Decade>/<slug>/index.md
```

</details>

---

<details>
<summary><h2>16. Troubleshooting</h2></summary>

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

**"The intake bot didn't run on my PR."**
Two causes: the PDF was committed to `main` (bot only runs on PRs), or
the PR is from a fork (token can't push back). Re-do on a branch.

**"My slash command was ignored."**
The command must start at column 0. Put `/title` on its own line.

**"Search finds nothing."**
The Pagefind index is rebuilt each deploy. Wait for Actions to finish
and hard-refresh.

**"I accidentally broke the site."**
From terminal: `git revert <sha>`. Or on github.com: click the commit →
**Revert**. After the build finishes, the site is restored.

</details>

---

<details>
<summary><h2>17. Publication types reference</h2></summary>

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
- The slash-command bot validates against the primary list and warns on
  unrecognised values.

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
