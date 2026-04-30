# Updating the Website

This guide is for **Gary** (or anyone doing content maintenance). Every
task below is described two ways:

- **Terminal** — preferred when you have a checkout handy. Edit a file in
  your editor, `git commit`, and (with the auto-push hook installed) the
  change is on its way to GitHub before you've moved on.
- **GitHub.com** — pencil-icon edits in the browser. No local tools, no
  developer knowledge required. Use this when you're on a phone or a
  borrowed laptop.

Either path lands the change on the live site within ~3 minutes: every
push to `main` triggers the `Deploy Hugo site to GitHub Pages` workflow,
which builds Hugo, regenerates the search index, regenerates short-URL
redirects, refreshes first-commit dates for the spotlight, and publishes.

> Repository: <https://github.com/iqss-research/gking-site>
> Live site: <https://gking.harvard.edu/>

---

## TL;DR — three things to remember

1. Every piece of content is a folder under `hugo-site/content/` containing
   an `index.md` (or `_index.md` for section landing pages). Copy an
   existing one and edit it.
2. PDFs and images go under `hugo-site/static/files/` (PDFs) or
   `hugo-site/static/images/` (one-off images), or alongside the page's
   `index.md` (featured / per-page assets).
3. After you commit + push, wait ~3 minutes and refresh. GitHub Actions
   rebuilds everything automatically — the Pagefind search index, the
   "See Also" links, the Writings tabs, the redirect stubs, and the
   Working-Papers spotlight.

> **Adding a new paper, talk, book, software entry, or patent?** Skip
> the manual templates entirely — see [Quick add](#quick-add) for the
> shortest path for each content type. Most flows are "drop a PDF" or
> "one terminal command".

---

## Table of contents

1. [One-time setup (terminal)](#one-time-setup-terminal)
2. [Quick add (every content type)](#quick-add)
3. [How the repo is organized](#how-the-repo-is-organized)
4. [Two ways to edit](#two-ways-to-edit)
5. [Add a paper / article / book (manual template)](#add-a-paper--article--book-manual-template)
6. [Add a talk or presentation](#add-a-talk-or-presentation)
7. [Add a software / R package page](#add-a-software--r-package-page)
8. [Add a dataset / Dataverse link](#add-a-dataset--dataverse-link)
9. [Featured publications spotlight](#featured-publications-spotlight)
10. [Link things together ("See Also")](#link-things-together-see-also)
11. [Update the bio or CV](#update-the-bio-or-cv)
12. [Add / remove research-group members](#add--remove-research-group-members)
13. [Edit the homepage](#edit-the-homepage)
14. [Edit the navigation menu](#edit-the-navigation-menu)
15. [Change a button label ("Article", "Publisher's Version", …)](#change-a-button-label)
16. [Add a paper to a Research Area](#add-a-paper-to-a-research-area)
17. [Edit the teaching / contact / other pages](#edit-the-teaching--contact--other-pages)
18. [Short URLs & redirects (`/rd`, `/quest`, …)](#short-urls--redirects)
19. [Helper scripts (terminal only)](#helper-scripts-terminal-only)
20. [Automation: workflows that run on every change](#automation-workflows-that-run-on-every-change)
21. [Local preview](#local-preview)
22. [Troubleshooting](#troubleshooting)
23. [Appendix: publication types](#appendix-publication-types)

---

## One-time setup (terminal)

Once per machine. Skip this section if you only ever edit through
github.com.

```bash
git clone https://github.com/iqss-research/gking-site.git
cd gking-site/hugo-site

# Install the auto-push hook so every `git commit` immediately
# `git push`es to origin. Removes the easy-to-forget last step.
scripts/enable-auto-push.sh
```

After that, the daily flow is just:

```bash
git pull            # before you start
# …edit files in your editor…
git add -A
git commit -m "short message"
# (the post-commit hook pushes for you)
```

Notes on the auto-push hook:

- One-off skip: `SKIP_AUTO_PUSH=1 git commit -m "wip"`.
- Turn it off permanently: `git config hooks.skip-auto-push true`.
- It only pushes if the branch already has an upstream
  (`git push -u origin main` once if it ever asks).

For a local preview before pushing, see [Local preview](#local-preview).

---

## Quick add

Five content types, one shortcut each. If your content has a PDF, drop
it under `intake/` (in the right subfolder) and a bot fills in the
metadata. If it doesn't (software, patents, or anything you already
have the metadata for), `scripts/quick_add.py` scaffolds the file in
one command.

| Content type           | If you have a PDF…                          | If you don't…                                          |
|------------------------|---------------------------------------------|---------------------------------------------------------|
| Paper / article         | `intake/<file>.pdf` → bot uses Crossref     | `python3 scripts/quick_add.py paper …`                  |
| Talk / presentation     | `intake/talk/<file>.pdf` → slide-deck flow  | `python3 scripts/quick_add.py talk …`                   |
| Book                    | `intake/book/<file>.pdf` → book flow        | `python3 scripts/quick_add.py book …`                   |
| Software / R package    | _(no PDF flow — software is URL-based)_     | `python3 scripts/quick_add.py software --github …`      |
| Patent                  | optional `intake/<file>.pdf` then `/type patent` | `python3 scripts/quick_add.py patent --source …`   |

After every shortcut, `git commit` + push (auto-push pushes for you)
and the deploy workflow makes it live in ~3 minutes.

### Quick add: paper / article

The fastest path. Drop a PDF in `intake/` and the bot looks up the
DOI / Crossref metadata for you.

**Terminal flow (~30 seconds of work):**

```bash
git checkout -b add-my-paper            # any branch name
cp ~/Downloads/whatever.pdf intake/     # filename doesn't matter
git add intake/whatever.pdf
git commit -m "Drop PDF for auto-import"
git push -u origin add-my-paper         # auto-push handles this on subsequent commits
gh pr create --fill                     # or open the URL git printed
```

Wait ~1–2 minutes; the bot pushes a follow-up commit to your branch
with a generated `content/publication/<slug>/index.md`, the moved PDF,
an updated `data/writings_legacy_map.json`, and a featured-image
thumbnail (see [What happens automatically](#what-happens-automatically)).

**GitHub.com flow:**

1. Open <https://github.com/iqss-research/gking-site/tree/main/intake>
   (or click into the `intake/` folder from the repo's main page).
2. Click **Add file → Upload files**.
3. Drag the paper's PDF onto the page.
4. Pick **"Create a new branch for this commit and start a pull
   request"**, then click **Propose changes**.
5. On the next page click **Create pull request**. No description
   needed; the bot writes one.

**Already have all the metadata (no PDF, or skipping Crossref)?**

```bash
python3 scripts/quick_add.py paper \
    --title "An Example Paper" \
    --slug an-example-paper \
    --year 2026 \
    --authors "Gary King; Jane Doe" \
    --doi 10.1017/example.2026.1 \
    --publication "Political Analysis, 32, 1, Pp. 1-20" \
    --pdf ~/Downloads/example.pdf      # optional
git add -A && git commit -m "Add example paper"
```

### Quick add: talk / presentation

Drop a slide-deck PDF in `intake/talk/` (note the `talk/` subfolder).
The bot writes `content/talk/<slug>/index.md` (not `publication/`),
sets `publication_types: ["presentation"]`, routes the Writings tab to
**Presentations**, and skips Crossref (slide decks aren't indexed).

**Terminal flow:**

```bash
git checkout -b add-my-talk
mkdir -p intake/talk
cp ~/Downloads/slides.pdf intake/talk/
git add intake/talk/slides.pdf
git commit -m "Drop slides for auto-import"
git push -u origin add-my-talk
gh pr create --fill
```

**GitHub.com flow:** same as paper, but click into the `intake/talk/`
subfolder before **Add file → Upload files**. (If the subfolder doesn't
exist yet, create it first via **Add file → Create new file** and type
`talk/.gitkeep` as the path.)

The talk schema is intentionally minimal — `title`, `date`, `authors`,
`publication_types`, `links` — matching every existing entry under
`content/talk/`. After the PR opens you can fix anything via the
[slash commands](#slash-commands-for-the-pr-bot) or the **Files
changed** pencil.

**No PDF for the talk?**

```bash
python3 scripts/quick_add.py talk \
    --title "Misadventures in Survey Methodology" \
    --slug misadventures-survey-methodology \
    --date 2026-04-30 \
    --authors "Gary King"
```

### Quick add: book

Drop the book PDF (or a manuscript / chapter sample) in `intake/book/`.
The bot still consults Crossref (book metadata IS indexed there) but
forces the type to `book` regardless, so it lands on the **Books** tab
of the Writings page.

```bash
git checkout -b add-my-book
mkdir -p intake/book
cp ~/Downloads/manuscript.pdf intake/book/
git add intake/book/manuscript.pdf
git commit -m "Drop book PDF for auto-import"
git push -u origin add-my-book
gh pr create --fill
```

If Crossref doesn't have a hit, the bot scaffolds title / authors /
year from the PDF text and prompts you (in its PR comment) to add the
`publication:` line — typically `Cambridge University Press, 2026`.
Use the `/publication …` slash command or the pencil to fill it in.

**No PDF, just metadata?**

```bash
python3 scripts/quick_add.py book \
    --title "Demographic Forecasting" \
    --slug demographic-forecasting \
    --year 2008 \
    --authors "Federico Girosi; Gary King" \
    --publisher "Princeton University Press" \
    --abstract "..."
```

### Quick add: software / R package

Software entries are URL-based, not PDF-based, so there's no `intake/`
flow. The helper script is the easy path:

```bash
python3 scripts/quick_add.py software \
    --title "MyTool: An R Package for Quick Adds" \
    --slug my-tool \
    --year 2026 \
    --authors "Gary King; Jane Doe" \
    --github https://github.com/IQSS/my-tool \
    --abstract "Short summary of what the tool does."
git add -A && git commit -m "Add my-tool software entry"
```

That single command:

- Writes `content/publication/my-tool/index.md` with
  `publication_types: ["software"]` and a `code` link to the GitHub URL.
- Appends a row to `data/software_legacy_rows.yaml` so the entry shows
  up at the top of `/software/` (newest year first). Pass
  `--status older` to put it in the desaturated "Older" section.
- Adds the slug to `data/writings_legacy_map.json` (`tab: software`)
  so it also lands on the Writings → Software tab.

Other supported flags: `--cran <url>`, `--site <url>` (project website),
`--pdf <path>` (rare — only if there's an accompanying PDF).

**GitHub.com flow** (no terminal): click **Add file → Create new file**
in the repo and type `content/publication/<slug>/index.md` as the path.
Paste this template, fill it in, then commit on a new branch and merge
the PR:

```yaml
---
title: "MyTool: An R Package for ..."
date: "2026-01-01"
authors:
  - Gary King
publication_types:
  - software
abstract: |-
  Short summary of what the tool does.
links:
  - type: code
    url: "https://github.com/IQSS/my-tool"
---
```

After merging, edit `data/software_legacy_rows.yaml` to add a row at
the top:

```yaml
  - year: 2026
    slug: my-tool
```

…and add an entry to `data/writings_legacy_map.json`:

```json
"my-tool": { "tab": "software", "drupal": "software" },
```

(The terminal helper does all three in one shot.)

### Quick add: patent

Patents almost never have Crossref metadata, so the helper is the
easy path:

```bash
python3 scripts/quick_add.py patent \
    --title "Participant Grouping for Enhanced Interactive Experience" \
    --slug participant-grouping-enhanced-experience-2026 \
    --year 2026 \
    --authors "Gary King; Co-Inventor Name" \
    --publication "United States of America 12,345,678 B2" \
    --source https://patents.google.com/patent/US12345678 \
    --pdf ~/Downloads/us12345678.pdf       # optional
git add -A && git commit -m "Add new patent"
```

That single command writes `content/publication/<slug>/index.md` with
`publication_types: ["patent"]`, routes the Writings tab to **Patents**,
and (if you passed `--pdf`) copies the PDF to `static/files/<slug>.pdf`.
The `--source` URL becomes the **Publisher's Version** button link.

If you _do_ have a PDF and would rather use the github.com upload UI,
drop it in `intake/` (default flow), let the bot scaffold the page,
then post `/type patent` and `/publication …` on the resulting PR.

### What happens automatically

The `Auto-import publication from PDF` workflow
(`.github/workflows/intake-publication.yml`) runs on every PDF added
under `intake/`, `intake/talk/`, or `intake/book/` in a pull request.
For each PDF it:

- Detects the content kind from the subfolder
  (`intake/foo.pdf` = paper, `intake/talk/foo.pdf` = presentation,
  `intake/book/foo.pdf` = book).
- Reads the PDF and looks for a printed DOI; if absent, falls back to
  a Crossref title+author search (skipped for talks).
- Pulls Crossref's canonical title, full author list, journal /
  publisher name, volume / issue / pages (or article number), year,
  and abstract.
- Generates a slug from the title and creates the right `index.md`
  under `content/publication/<slug>/` (papers, books, patents) or
  `content/talk/<slug>/` (talks).
- Moves the PDF from `intake/` to `static/files/<slug>.pdf` and links
  it from the page.
- Adds the slug to `data/writings_legacy_map.json` so it routes to the
  correct Writings-page tab.
- Extracts a thumbnail: walks the PDF for embedded raster figures and
  saves the largest one (≥250 px on a side, with anti-monochrome
  filtering) as `featured.png` (or `.jpg`). If none qualifies (e.g. a
  text-heavy working paper), it renders page 1 as a fallback. The PR
  comment tells you which path was used.
- Pushes one extra commit to your PR branch and posts a comment that
  summarizes everything it found, plus a "**things to double-check**"
  list if it had to guess anything.

### Reviewing the PR

Open the PR after the bot's comment shows up. The comment lists, for
each PDF: title, authors, year, DOI, generated citation line, detected
publication type, and any review notes (e.g. *"Abstract was extracted
from PDF body text — skim it for OCR artifacts"*).

If everything looks right, click **Merge pull request**. The deploy
workflow runs and the entry is live in another ~3 minutes.

### Slash commands for the PR bot

If something needs editing, **post a comment on the PR with one or more
slash commands**. The bot picks them up within ~30 seconds and pushes
a follow-up commit:

```
/title The Real Title of the Paper
/authors Gary King; Jane Doe; Last, First
/year 2024
/doi 10.1017/pan.2021.48
/type journal_article
/publication Political Analysis, 31, 2, Pp. 100-110
/abstract The corrected abstract goes here.
It can span multiple paragraphs and continues
until the next slash command or end of comment.
```

Recognised commands (case-insensitive):

| Command | What it does | Notes |
|---|---|---|
| `/title <text>` | replaces the title | single line |
| `/authors A; B; C` | sets the full authors list | use `;` even if names contain commas, e.g. `King, Gary` |
| `/year <YYYY>` _or_ `/year <YYYY-MM-DD>` | sets the publication date | year-only is stored as `YYYY-01-01` |
| `/date <date>` | alias for `/year` | |
| `/abstract <text>` | replaces the abstract | spans every line until the next `/cmd` or end of comment, so multi-paragraph abstracts work |
| `/publication <text>` | replaces the citation line | e.g. `Political Analysis, 31, 2, Pp. 100-110` |
| `/doi <doi>` | sets the DOI | also rewrites the **Publisher's Version** link to `https://doi.org/<doi>` |
| `/type <slug>` | replaces `publication_types` | also re-routes the Writings tab. Valid slugs: `journal_article`, `book`, `book_chapter`, `working_paper`, `conference_paper`, `report`, `data`, `software`, `courtbrief`, `presentation`, `other` |

The bot reacts 👍 on the comment, posts a confirmation listing what
changed (and warnings for any commands it didn't understand), and
commits the result to the PR branch. You can keep iterating.

If you'd rather edit `index.md` directly, you still can: from the
terminal, edit the file the bot just generated; or from github.com,
open the **Files changed** tab and click the pencil on the new
`index.md`. Either path works; mix and match.

The site rebuilds automatically once the PR is merged. The "See Also"
box at the bottom of the page is filled in automatically (the build
scans titles, authors, and tags across the whole site to surface
related content).

### Manual run (terminal, no PR needed)

If you'd rather run the import locally without opening a PR:

```bash
cd hugo-site
pip install pyyaml certifi pymupdf      # one time
python3 scripts/intake_publication.py intake/whatever.pdf --dry-run
# happy with the report? drop --dry-run:
python3 scripts/intake_publication.py intake/whatever.pdf
# subfolders work too:
python3 scripts/intake_publication.py intake/talk/slides.pdf
python3 scripts/intake_publication.py intake/book/manuscript.pdf
git add -A && git commit -m "Add new content"
```

`scripts/quick_add.py` runs entirely locally too — no PR opened, just
direct file writes. Add `--dry-run` to preview the rendered front
matter without touching anything.

### When this won't work / fallbacks

- The PR-triggered bot **only** runs from a pull-request branch, never
  a direct push to `main`. If you accidentally pushed straight to
  `main`, remove the file from `intake/` and re-do it on a branch.
- The bot also skips PRs from forks (the GitHub token can't push back
  to a fork's branch). Open the PR from a branch in this repo.
- If Crossref has nothing for the paper (very recent working paper,
  unindexed conference proceedings, etc.), the bot still creates a
  scaffolded `index.md` from the PDF text — but it'll flag every field
  that needs human verification in the PR comment.
- If a slide-deck PDF doesn't have a useful first slide (or any
  embedded figures), the bot renders page 1 as a thumbnail anyway. To
  override, drop a `featured.png` (or `.jpg`) next to the new
  `index.md` before merging.
- If you'd rather hand-write the front matter from scratch, the manual
  templates are still there:
  [Add a paper (manual template)](#add-a-paper--article--book-manual-template),
  [Add a talk](#add-a-talk-or-presentation),
  [Add software](#add-a-software--r-package-page).

---

## How the repo is organized

```
hugo-site/
├── content/                ← every page lives here
│   ├── publication/        ← papers, articles, books, datasets, patents
│   ├── talk/               ← presentations
│   ├── software/           ← stand-alone software / R-package pages
│   ├── people/             ← profile pages for collaborators / alumni
│   ├── authors/            ← author taxonomy pages (only `gary-king/`)
│   ├── bio/                ← "Bio & CV" page
│   ├── teaching/           ← "Teaching" page (+ per-class subfolders)
│   ├── research-areas/     ← "Research Areas" page
│   ├── research-group/     ← "People" page (built from data/research_group.json)
│   ├── dataverse/, contact/, blog/, advice/, …
│   └── _index.md           ← homepage
├── static/
│   ├── files/              ← PDFs, slides, supplementary downloads
│   └── images/             ← bio photo, site-wide images
├── data/                   ← YAML/JSON data files driving dynamic pages
├── intake/                 ← drop-zone for the auto-import bot (normally empty)
│   ├── talk/               ← drop slide-deck PDFs here for the talk flow
│   └── book/               ← drop book PDFs here for the book flow
├── layouts/                ← Hugo templates (edit only for design tweaks)
├── assets/css/custom.css   ← site-wide CSS overrides
├── i18n/en.yaml            ← UI strings (button labels, etc.)
├── .github/workflows/      ← deploy + intake + link-check automations
├── scripts/                ← Python helper scripts (see below)
└── hugo.yaml               ← top-level Hugo config (menus, theme, etc.)
```

Each piece of content is a folder whose name becomes part of the URL.
Example: `content/publication/ecological-inference/index.md` →
`https://gking.harvard.edu/publication/ecological-inference/`.

---

## Two ways to edit

### Terminal

```bash
cd gking-site/hugo-site
$EDITOR content/publication/some-paper/index.md
git add -A && git commit -m "Fix typo in abstract"
# (auto-push hook pushes; otherwise: `git push`)
```

To **add a new file**, just create the folder and `index.md` in your
editor — Hugo picks up new content automatically on the next build.

### GitHub.com

1. Go to <https://github.com/iqss-research/gking-site>.
2. Click into `hugo-site/…`.
3. Click any file → pencil icon → make changes → scroll down →
   **Commit changes**.
4. To **add a new file**: browse to the parent folder → **Add file →
   Create new file**. Type the full path in the filename box, e.g.
   `hugo-site/content/publication/my-new-paper/index.md`, then paste
   the template below.
5. To **upload PDFs**: browse to `hugo-site/static/files/` →
   **Add file → Upload files** → drag the PDF in → Commit.

Watch the build at
<https://github.com/iqss-research/gking-site/actions>. It usually
finishes in 3–4 minutes.

---

## Add a paper / article / book (manual template)

> Most of the time you should use the
> [Quick add](#quick-add) flow above (drop a PDF in `intake/` and let
> the bot handle this, or run `scripts/quick_add.py paper …`). The
> manual template here is a fallback for cases where the bot can't
> find Crossref data, or when you want fine-grained control over every
> field from the start.

### Step 1 — upload the PDF

Put the PDF at `hugo-site/static/files/<slug>.pdf`. Use a short,
lowercase, hyphenated filename, e.g.
`gerrymandering-partisan-symmetry-2026.pdf`.

### Step 2 — create the page folder

Create a new file at:

```
hugo-site/content/publication/<slug>/index.md
```

`<slug>` is whatever you want in the URL (lowercase, hyphens, no
spaces). It becomes the page URL permanently — pick something readable
and stable.

### Step 3 — paste this template and edit

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

**Notes**

- `publication_types` must be one of the values listed in
  [the appendix](#appendix-publication-types).
- Each entry in `links:` becomes a button on the page. The site
  recognises two **canonical types**:
  - `type: pdf` → "Article" button (the i18n translation can be
    changed; see [Change a button label](#change-a-button-label)).
  - `type: source` → "Publisher's Version" button (also rewritten by
    `/doi` slash commands).
  Anything else uses `name:` for the button label, e.g.
  `name: "Supplementary Material"`. The intake bot writes the
  `type:`-style links; older hand-written pages sometimes use the
  `name:`-style. Both work.
- `files/...` URLs (no leading `/`) point at `static/files/`.
- `date` should be `YYYY-MM-DD` or quoted `'YYYY-MM-DD'`.
- `authors:` controls ordering; write names however you want them
  displayed.
- `abstract: |-` keeps line breaks; `abstract: "single line"` works too.

### Step 4 — pick the Writings tab

Tab placement is driven by `data/writings_legacy_map.json`, which
records each item's legacy category. The intake bot updates this for
you; if you're hand-writing a page, append an entry like:

```json
"<slug>": { "tab": "<tab-id>", "drupal": "<type>" }
```

| `drupal` value (matches `publication_types[0]`) | `tab` id        | Where it shows on `/publication/` |
| ----------------------------------------------- | --------------- | ------------------------------------- |
| `journal_article`                               | `journal`       | Journal Articles                      |
| `working_paper`                                 | `journal`       | Working Papers spotlight (top)        |
| `book`                                          | `book`          | Books & Chapters                      |
| `book_chapter`                                  | `journal` *or* `other` | varies — both exist in current data |
| `presentation`                                  | `presentation`  | Presentations                         |
| `software`                                      | `software`      | Software                              |
| `patent`                                        | `patent`        | Patents                               |
| `courtbrief`                                    | `courtbrief`    | Court Briefs                          |
| anything else                                   | `other`         | Other                                 |

Books on the homepage are rendered from this same file (every entry
with `drupal: book` is surfaced automatically), so you don't need a
separate edit there.

### Step 5 (optional) — featured image

Drop a `featured.jpg` or `featured.png` next to `index.md`. It's shown
at the top of the page and as the card thumbnail on the Writings list.
If you don't, the [`scripts/add_featured_from_pdf.py`](#helper-scripts-terminal-only)
helper can render page 1 of the PDF for you.

---

## Add a talk or presentation

Same pattern as a publication, but under `content/talk/`:

```
hugo-site/content/talk/<slug>/index.md
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

Talks don't need a `writings_legacy_map.json` entry — the Presentations
tab is driven from the publication side, not the talk side.

---

## Add a software / R package page

Under `content/software/`:

```
hugo-site/content/software/<slug>/index.md
```

```yaml
---
title: "Software Name"
date: 2024-01-01
authors:
  - "Gary King"
  - "Developer Name"
publication_types:
  - "software"
abstract: "Short description."
links:
  - name: "Project Website"
    url: "https://my-software-site.com"
  - name: "GitHub"
    url: "https://github.com/IQSS/my-tool"
  - name: "CRAN"
    url: "https://cran.r-project.org/package=MyTool"
---

Optional Markdown body: installation instructions, changelog, citations, etc.
```

### Where does a software item appear on `/software/`?

The software landing page groups items into two visual sections:

- **(default, no header)** — actively available code (GitHub, CRAN,
  public website, etc.).
- **Older** — desaturated section at the bottom for archived,
  superseded, or no-longer-maintained software.

Which group a row lands in is controlled by
`hugo-site/data/software_legacy_rows.yaml`:

```yaml
rows:
  - year: 2020
    slug: opendp-developing-open-source-tools-for-differential-privacy
    # status omitted → "current" (default group, on top)
  - year: 2017
    slug: boocio-an-education-system-with-hierarchical-concept-maps
    status: older
```

`status` accepts `current` (or omit) and `older`. Within each group,
rows are sorted by `year` descending. To add a new item, append a row
with `year`, `slug`, and (optionally) `status`. The `slug` must match a
folder under `content/publication/` *or* `content/software/`.

A few related data files you usually don't need to touch:

- `data/software_legacy_overrides.yaml` — per-slug citation lines, list
  titles, alternate links, abstract suppression.
- `data/software_fallback_urls.yaml` — direct URLs for software whose
  publication+software bundle has no http(s) link.
- `data/software_prefer_internal.yaml` — slugs where lists should link
  to `/software/<slug>/` first instead of an external project URL.
- `data/software_list_exclude.yaml` — currently empty hook for one-off
  exclusions.

---

## Add a dataset / Dataverse link

A dataset is just a publication with `publication_types: data`. Put it
under `content/publication/` like any paper. Two extra fields unlock the
green "Harvard Dataverse" banner on the page:

```yaml
publication_types:
  - "data"
dataverse_url: "https://doi.org/10.7910/DVN/ABCDEF"
dataverse_name: "Replication Data for: Paper Title"
```

If the dataset is the replication archive for a specific paper, point
at it so a "Replication data for: …" banner is shown:

```yaml
related_paper: "publication-slug-of-the-paper"
```

The Dataverse landing page (`/dataverse/`) is built from
`data/dataverse.json`, which is regenerated by scrapers when needed —
you usually don't edit it directly.

---

## Featured publications spotlight

The "Working Papers" spotlight at the top of `/publication/` is
controlled by `hugo-site/data/featured_publications.yaml`:

```yaml
count: 5

order:
  - inducing-sustained-creativity-and-diversity-in-large-language-models
  - survey-estimates-of-wartime-mortality
  - if-a-statistical-model-predicts-that-common-events-should-occur-only-once-in-100
  - experimental-evidence-on-the-limited-influence-of-reputable-media-outlets
  - how-american-politics-ensures-electoral-accountability-in-congress

exclude:
  - amelia-ii-a-program-for-missing-data-jss
```

How the displayed list is built:

1. Start with the manually curated `order` list.
2. Before each build, any journal-article publication NOT already in
   `order` (and NOT in `exclude`) is prepended by its **first-commit
   date** (newest first), so adding a fresh paper auto-promotes it
   into the spotlight and the oldest curated entry rolls off the
   bottom.
3. The displayed list is capped at `count` entries (set `count: 0` to
   hide the spotlight).

First-commit dates live in `data/publication_first_commit.json` and are
refreshed automatically in CI by
`scripts/compute_publication_first_commit.py`. Run it locally any time
with:

```bash
python3 scripts/compute_publication_first_commit.py
```

Edit `order` to pin a slug into the list, or `exclude` to keep a recent
slug out (e.g. when a fresh commit on an old paper would otherwise
re-promote it as if it were new).

---

## Link things together ("See Also")

The site automatically fills the "See Also" box at the bottom of every
paper, talk, and software page. The rules:

1. **Do nothing** and the site scans titles, authors, and tags and
   links content that overlaps. Add a new paper and any existing talk
   with similar title / shared authors / shared tags will auto-link
   both ways after the next build.
2. **To force specific links**, add any of these to the front matter.
   Each takes a **slug** (the folder name of the other item). Whatever
   you put here always appears first:
   ```yaml
   related_talks:    ["talk-slug-1", "talk-slug-2"]
   related_papers:   ["paper-slug-1"]
   related_software: ["software-slug-1"]
   related_datasets: ["dataset-slug-1"]
   ```
3. **To improve auto-matching**, add shared `tags:` or `keywords:` to
   related items:
   ```yaml
   tags: ["ecological inference", "voting rights"]
   ```
4. The "See Also" box shows at most 6 items, sorted explicit-first,
   then by match strength, then by year (newest first).

---

## Update the bio or CV

**Bio text** — edit `hugo-site/content/bio/index.md`. The portion below
the front matter `---` is plain Markdown / HTML; write naturally.

**CV PDF** — replace `hugo-site/static/files/vitae.pdf` (overwrite the
old one). The "Download CV (PDF)" button on the Bio page already points
there.

**Bio photo** — replace `hugo-site/static/images/gking-bio-photo.jpg`
(overwrite the old one).

---

## Add / remove research-group members

People are managed in two places:

- `hugo-site/content/people/<slug>/index.md` — one folder per person
  with a tiny YAML stub.
- `hugo-site/data/research_group.json` — Harvard taxonomy (categories,
  affiliations, last-name letter buckets) that drives the filter
  sidebar on the People page.

### Current Research Group (Harvard affiliates today)

The "Current Research Group" box at the top of `/research-group/` is
**curated by hand** in
`hugo-site/layouts/research-group/single.html`. It has three
subsections — *PhD Students & Research Assistants*, *Undergraduate
Research Assistants*, and *Other*. To add or remove someone here, edit
that template directly (look for the `<a href="...">` cards under each
`<h3>`).

### Alumni & Collaborators

Everyone else (alumni, post-docs, collaborators) lives below in the
filterable list. To add someone:

1. Create `hugo-site/content/people/<slug>/index.md`:

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
   `alumni_students`, `alumni_postdocs`, `collaborators`. Multiple
   categories per person come from `data/research_group.json` (see
   below).

2. (Optional but recommended) add a row to
   `hugo-site/data/research_group.json` so the affiliation /
   letter-bucket filters count them correctly:

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

To **move someone between alumni / collaborators**, edit
`research_group_category` (in their `index.md`) or
`research_group_categories` (in `research_group.json`).

To **remove** someone, delete the folder under `content/people/` and
the matching row in `data/research_group.json`.

---

## Edit the homepage

The homepage at `content/_index.md` is intentionally minimal:

```yaml
---
title: "Gary King"
type: landing
---
```

All of the visual blocks (welcome, research-area cards, featured
papers, books, software, etc.) are rendered by
`layouts/landing/list.html`, which pulls from:

- `content/publication/` (newest entries by `date`)
- `data/writings_legacy_map.json` (for "Books")
- `data/featured_publications.yaml` (for the Working Papers spotlight)
- `data/research_areas.json` (for the Research Areas grid)

So most homepage updates happen by editing one of those files (a paper
front-matter, the spotlight, the research area), not the homepage
itself. To restyle a block, edit `layouts/landing/list.html` (treat
that as a developer task).

---

## Edit the navigation menu

The top menu is defined in `hugo-site/hugo.yaml` under `menus.main`.
Each entry has a `name`, a `url`, and a `weight` (lower = more to the
left):

```yaml
menus:
  main:
    - name: Bio & C.V.
      url: /bio/
      weight: 10
    - name: Writings
      url: /publication/
      weight: 20
    - name: Research Areas
      url: /#research-areas
      weight: 30
    - name: Software
      url: /software/
      weight: 40
    - name: Dataverse
      url: /dataverse/
      weight: 50
    - name: People
      url: /research-group/
      weight: 60
    - name: Teaching
      url: /teaching/
      weight: 70
    - name: Contact
      url: /contact/
      weight: 80
```

Add, remove, or reorder by editing this list.

---

## Change a button label

Button text such as "Article" or "Publisher's Version" is controlled
in `hugo-site/i18n/en.yaml`:

```yaml
- id: btn_pdf
  translation: Article
- id: btn_source
  translation: "Publisher's Version"
```

Change the value on the right, commit.

---

## Add a paper to a Research Area

Research-area groupings live in
`hugo-site/data/research_areas.json`. The file has two top-level keys —
`methods` and `applications` — each containing areas, each with
subcategories, each with a `papers:` list. To add a paper, append an
entry to the right `papers` list:

```json
{
  "name": "Ecological Inference",
  "subcategories": [
    {
      "name": "Overview",
      "papers": [
        { "title": "Paper Title", "section": "publication", "slug": "paper-slug" }
      ]
    }
  ]
}
```

`section` is one of `publication`, `talk`, or `software`.

The intake bot prints **Suggested Research Areas** in the PR comment
based on title/abstract overlap, so you usually have a copy-pasteable
slug + subcategory waiting for you.

---

## Edit the teaching / contact / other pages

Plain pages all live under `hugo-site/content/`, one folder each, with
an `index.md` (or `_index.md` for section pages). Edit the Markdown
directly.

| Page                        | File                                |
| --------------------------- | ----------------------------------- |
| Teaching                    | `content/teaching/_index.md`        |
| Per-class teaching sub-page | `content/teaching/<class>/index.md` |
| Contact                     | `content/contact/index.md`          |
| Dataverse                   | `content/dataverse/index.md`        |
| Research Group landing      | `content/research-group/index.md`   |
| Homepage                    | `content/_index.md`                 |
| Bio                         | `content/bio/index.md`              |

### Advice & Suggestions

All of the "Advice and Suggestions" links live at the **bottom of the
Teaching page** (`content/teaching/_index.md`, under the `<h2
id="advice">` heading). The footer bar's "Advice and Suggestions" link
jumps there via the `#advice` anchor, and the legacy `/advice/` URL
auto-redirects to the Teaching page (via the `aliases:` entry at the
top of `teaching/_index.md`). To add, remove, or reorder advice items,
edit that section.

---

## Short URLs & redirects

The old Drupal site had short URLs that forwarded elsewhere — e.g.
`gking.harvard.edu/rd` to a Google Doc, or `gking.harvard.edu/quest` to
a specific paper. The new site keeps the same idea, but in a much
simpler way: **one YAML file for the whole list**.

> **136 redirects from the old Drupal site are already restored.**
> Every redirect Harvard's web team had registered on the old
> `gking.harvard.edu` Drupal admin is now live on the new site —
> including `/zoom`, `/Gov2020`, all the long-form Drupal slugs
> (`/cem-coarsened-exact-matching-software` → `/publication/cem-...-software/`),
> all the legacy `/research-interests/...` and `/category/research-interests/...`
> taxonomy paths (forward to `/research-areas/`), all the `/classes/...` and
> `/class/...` course paths (forward to `/teaching/...`), the homepage
> aliases (`/home`, `/home3`, `/home-page`, `/original-home-page`, …),
> and many file-path redirects (`/files/gking/files/teaching.pdf` →
> `/files/teaching.pdf`).
>
> The source of truth is `scraped_data/drupal_redirects.csv` (a CSV
> copy of the official Harvard Web Publishing redirect-summary export
> for `gking.harvard.edu`) plus a hand-curated table of "vanity short
> URLs" (`/whatif`, `/amelia`, `/sibs`, `/Gov2020`, `/quest`, …) that
> Drupal stored as path *aliases* — not as redirects — and so don't
> appear in the CSV. The translation lives in
> `scripts/import_drupal_redirects.py` and is materialised into two
> blocks in `data/redirects.yaml`:
>
> - `# BEGIN drupal-redirects-import` — every spreadsheet row, with
>   each `to:` chain-resolved through to a real new-site URL.
> - `# BEGIN vanity-shorts-import` — every short URL Gary publicises
>   in CVs / talks / papers (e.g. `gking.harvard.edu/whatif`,
>   `/Gov2020`, `/CompSS`). Mixed-case originals also get a lowercase
>   alias because the new site is case-sensitive but Drupal wasn't.
>
> Hand-edits *outside* those blocks are preserved across re-runs; edits
> *inside* will be overwritten. The importer also auto-translates
> truncated content directory names (e.g. `if-a-statistical-...-100`)
> to their actual published Hugo URLs (which are derived from the full
> page title, e.g. `if-a-statistical-...-10000-elections-maybe-its-the-wrong-model`)
> — so every emitted redirect lands on a real page, not a 404. To
> regenerate after editing the resolver, the rewrite tables, or the
> vanity URL table, run:
>
> ```bash
> python3 scripts/import_drupal_redirects.py --apply
> ```

### (A) Short URL that forwards somewhere

Edit `hugo-site/data/redirects.yaml`. It's a list under `redirects:`,
one entry per short URL:

```yaml
redirects:
  - from: rd
    to:   https://docs.google.com/document/d/abcdef123/edit
    note: "Research Directions living doc"

  - from: quest
    to:   /publication/quest/
    status: 301
    note: "Short URL for the Quest paper"

  - from: ei
    to:   https://github.com/iqss-research/ei
    status: 308
    note: "EI software repo (modern permanent redirect)"
```

Field reference:

- `from` (required) — the URL path you want to own. Either a single
  segment (`rd`, `quest`) or a multi-segment path (`research-interests/methods/missing-data`,
  `class/workshop-applied-statistics`). Each segment must start with a
  letter or digit, then contain only letters, digits, dashes,
  underscores, or dots. **Case is preserved** — `/Gov2020/` and
  `/gov2020/` are different URLs; add both forms if you want both to
  work. A *single*-segment `from` MUST NOT collide with an existing
  top-level page (e.g. `bio` is already `/bio/`); the build fails with
  a clear message if it does, so you can pick a different one.
- `to` (required) — full external URL (`https://…`) or internal path
  (`/publication/my-paper/`).
- `status` (optional) — `301` (default, permanent), `302`/`307`
  (temporary), `308` (modern permanent). Static GitHub Pages can't
  send a real HTTP status code, so the build emits a meta-refresh page
  whose markup reflects the chosen semantic (e.g. omitting the
  canonical link for 302/307 so search engines don't transfer page
  authority). The build also writes a Netlify-format `_redirects` file
  so a future migration to Netlify/Cloudflare Pages would honour the
  real status code automatically.
- `note` (optional) — free-form reminder to your future self. Ignored
  by the build.

Commit, wait ~3 minutes, and the redirect is live at `/<from>/`. The
generator (`scripts/build_redirects.py`) runs in CI on every deploy
and writes the actual HTML stubs into `content/_redirects/` (gitignored).

### (B) Short URL that forwards to one specific paper / talk / software

If the short URL is *about* a particular paper and should redirect to
that paper's page, you have two equally-good options:

**Option 1** — add it to `data/redirects.yaml` (same as above), pointing
`to:` at the paper's path. Simple, and keeps all redirects in one place.

**Option 2** — add it to the paper's own `index.md` as an `aliases:`
entry:

```yaml
---
title: "Quest: A Better Way to Measure X"
date: '2026-04-15'
aliases:
  - /quest/
authors:
  - Gary King
---
```

Hugo will automatically generate `/quest/index.html` that redirects to
the paper's canonical URL. The advantage of this option is that the
short URL lives inside the paper itself, so if you ever delete or
rename the paper, the redirect goes with it.

Use Option 1 for "living" redirects (docs, spreadsheets, external
projects that change over time). Use Option 2 for "this short URL
belongs to this paper" redirects.

### (C) Preserving old Drupal URLs

Every paper, talk, and software page on the new site uses the **same
slug** as the old Drupal site, so URLs like
`/publication/quest-a-better-way.../` already work without any extra
configuration. Section pages (`/bio/`, `/contact/`, `/dataverse/`,
`/teaching/`, `/research-areas/`, `/research-group/`, etc.) are
preserved too.

If you spot an old URL that stopped working after the migration, add
it to `data/redirects.yaml` pointing at its new home, and the old link
will work again.

---

## Helper scripts (terminal only)

These all live under `hugo-site/scripts/`. Most are dry-run by default
and ask for `--apply` (or have an obvious side-effect path) before
they touch files.

| Script | What it does |
|---|---|
| `enable-auto-push.sh` | One-shot — registers `.githooks/post-commit` so every commit auto-pushes to `origin`. |
| `intake_publication.py` | The auto-import pipeline used by CI. Run locally with `python3 scripts/intake_publication.py intake/foo.pdf [--dry-run]` to bypass the PR flow. Subfolder picks the type: `intake/foo.pdf` = paper, `intake/talk/foo.pdf` = presentation, `intake/book/foo.pdf` = book. |
| `quick_add.py` | Companion to `intake_publication.py` for content that doesn't have a PDF (software, patents) or where you already have all the metadata. `python3 scripts/quick_add.py {software,patent,paper,talk,book} --title ... --slug ...`. See [Quick add](#quick-add). |
| `apply_pr_edits.py` | The slash-command processor used by CI. Useful for testing locally: `python3 scripts/apply_pr_edits.py --comment body.txt --report r.json content/publication/foo/index.md`. |
| `build_redirects.py` | Regenerates the meta-refresh stubs and Netlify `_redirects` file from `data/redirects.yaml`. Supports single- and multi-segment paths and preserves case. Runs automatically in CI. |
| `import_drupal_redirects.py` | Recovers redirects from the old Drupal site. Reads `scraped_data/drupal_redirects.csv` (the official Harvard Web Publishing redirect-summary export) plus a hand-curated `VANITY_TO_NEWSITE` table covering vanity short URLs Drupal stored as path aliases (`/whatif`, `/amelia`, `/Gov2020`, `/CompSS`, …). Translates each entry's target through to a real new-site URL — including translating truncated content directory names to their full Hugo-published URL — and writes the result into the `BEGIN drupal-redirects-import` and `BEGIN vanity-shorts-import` blocks of `data/redirects.yaml`. For mixed-case vanity originals also emits a lowercase alias (Drupal was case-insensitive, the new site isn't). Idempotent — re-runs replace only those blocks, leaving hand-added redirects elsewhere in the file untouched. |
| `compute_publication_first_commit.py` | Refreshes `data/publication_first_commit.json` (drives the spotlight ordering). Runs automatically in CI. |
| `fill_publication_from_doi.py` | Fills the `publication:` citation line on existing pages from Crossref by DOI. Add `--apply` to write. |
| `repair_publication_links.py` | Audits external URLs in publication front matter; rewrites tinyurl/ezproxy/dead links to canonical DOIs. `--apply` to write. |
| `audit_writings_citations.py` | Cross-references each publication with Crossref and writes a JSON + text summary report. |
| `add_featured_from_pdf.py` | For each `content/publication/*/` missing a `featured.*`, renders page 1 of the linked PDF as `featured.png`. `--apply` to write. |
| `fetch_publication_thumbnails.py` | Re-downloads featured thumbnails from the legacy Drupal site (uses `scraped_data/`). |
| `refresh_featured_uncropped.py` | Replaces older Drupal-cropped thumbnails with full-resolution originals (HTML scrape + PDF figure match). |
| `fix_mojibake_markdown.py` | Repairs UTF-8 encoded-as-Latin-1 mojibake (smart quotes, en dashes, NBSP) across `content/`. Requires `pip install ftfy`. |
| `enrich_people_profiles.py`, `rescrape_people.py` | Fill / refresh `content/people/<slug>/index.md` stubs from upstream sources. |
| `sync_research_group.py`, `sync_research_group_from_harvard.py` | Refresh `data/research_group.json` from the Harvard / IQSS roster. |
| `verify_writings_parity.py` | Sanity-check that every legacy slug has a matching new-site page. |
| `build_writings_legacy_map.py` | Rebuild `data/writings_legacy_map.json` from `scraped_data/`. |
| `convert.py`, `scrape.py` | Original migration scripts (one-time, kept for reference). |

Most scripts only need `pip install -r scripts/requirements.txt`. A
few (`refresh_featured_uncropped.py`, `fix_mojibake_markdown.py`)
have dedicated `requirements-*.txt` files next to them.

---

## Automation: workflows that run on every change

`.github/workflows/` has four pieces of automation:

- **`deploy.yml` — Deploy Hugo site to GitHub Pages.** Triggered by
  every push to `main`. Installs Hugo + Node + Go + Python, runs
  `build_redirects.py` and `compute_publication_first_commit.py`,
  builds the site, builds the Pagefind search index, and publishes to
  GitHub Pages. Usually finishes in 3–4 minutes.
- **`intake-publication.yml` — Auto-import publication from PDF.**
  Triggered when a PR adds a PDF under `intake/`, `intake/talk/`, or
  `intake/book/`. See [Quick add](#quick-add) for the user-facing
  details and the per-subfolder routing.
- **`intake-edit.yml` — Apply PR comment edits.** Triggered when
  someone posts a comment on an open intake PR that contains slash
  commands like `/title`, `/authors`, `/year`, `/abstract`, `/doi`,
  `/publication`, `/type`. Applies them to every publication
  `index.md` added/changed by the PR, commits the result, and reacts
  +1 with a summary.
- **`link-check.yml` — Weekly external link check.** Runs every
  Monday at 09:00 UTC (also `workflow_dispatch`). Checks every
  external URL in content files; if it finds anything broken, it
  opens or updates a GitHub Issue labelled `link-check`.

You can manually trigger any of these from the **Actions** tab on
github.com.

---

## Local preview

```bash
brew install hugo                         # one time, macOS
cd hugo-site
hugo server                               # http://localhost:1313/
```

Production-equivalent build (rare; CI does this for you):

```bash
hugo --gc --minify
npx pagefind --site public                # search index
```

Hugo's live-reload picks up edits within ~50ms, so you can iterate on a
page with `hugo server` running and see the change immediately. When
you're happy, commit + push.

---

## Troubleshooting

**"I committed and nothing changed on the site."**
Give it 3–4 minutes, then visit
<https://github.com/iqss-research/gking-site/actions>. If the latest
run has a red ✗, click it to see the error (almost always a typo in
YAML front matter — missing quote, bad date, etc.).

**"`git commit` succeeded but didn't auto-push."**
The post-commit hook only pushes if the branch already has an upstream.
Run `git push -u origin <branch>` once and it'll auto-push from then
on. If it's still not running, check that
`scripts/enable-auto-push.sh` was run on this clone
(`git config core.hooksPath` should print `.githooks`).

**"A PDF returns 404 on the live site."**
Confirm the file is in `hugo-site/static/files/` and the `url:` in the
page's `links:` starts with `files/` (no leading slash).

**"The 'See Also' box is empty or wrong."**
Add shared `tags:` or pin specific items with `related_papers`, etc.
Explicit wins always override the automatic ones.

**"The intake bot didn't run on my PR."**
Two common causes: the PDF was committed straight to `main` (the bot
only runs on PRs), or the PR is from a fork (the GitHub token can't
push back to a fork branch). Re-do it on a branch in this repo.

**"My slash command in a PR comment was ignored."**
The command line must start at column 0 (or with up to 3 spaces of
indent). `/title` mid-paragraph won't trigger; put it on its own line.
Also valid commands only: `/title`, `/authors`, `/year`, `/date`,
`/abstract`, `/publication`, `/doi`, `/type`. The bot replies with a
warning listing any unrecognised commands.

**"Search finds nothing."**
The Pagefind index is rebuilt on each deploy. Wait until the Actions
run is green and hard-refresh the page.

**"I accidentally broke the site."**
Click the offending commit on github.com → **Revert**. From the
terminal: `git revert <sha>` (and let auto-push send it). After the
build finishes, the site is back.

---

## Appendix: publication types

Use exactly one of these strings in `publication_types:`. The first
group is what the slash-command bot validates against (and the most
common in current content); the second group also exists in the data
and is preserved for legacy reasons.

**Primary (recommended):**

```
journal_article
book
book_chapter
working_paper
conference_paper
report
data
software
courtbrief
presentation
other
```

**Also recognised (legacy / Drupal):**

```
conference_proceedings
miscellaneous
newspaper_article
patent
unpublished
web_article
website
```

If you use a value outside the primary list, the slash-command bot
will warn you and apply it anyway, but the Writings tab routing might
fall back to "Other".
