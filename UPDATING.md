# Updating the Website

This guide is for **Gary** (or anyone doing content maintenance). Every task
below can be done from **github.com in a web browser** — no terminal, no
local tools, no developer knowledge required. Just edit the file, click
"Commit", and the site rebuilds itself within a few minutes.

> Repository: <https://github.com/KatalinaToth/gking-site>
> Live site: <https://katalinatoth.github.io/gking-site/>

---

## TL;DR — Three things to remember

1. Every piece of content is a folder under `hugo-site/content/` containing
   an `index.md` file. Copy an existing one and edit it.
2. PDFs and images go under `hugo-site/static/files/` (PDFs) or
   alongside your `index.md` (featured images).
3. After you commit, wait 3 minutes and refresh the site. GitHub Actions
   rebuilds everything automatically, including the “See Also” links, the
   search index, and the Writings tabs.

---

## Table of Contents

1. [How the repo is organized](#how-the-repo-is-organized)
2. [Editing from GitHub.com (no terminal)](#editing-from-githubcom-no-terminal)
3. [Add a new paper / article / book](#add-a-new-paper--article--book)
4. [Add a new talk or presentation](#add-a-new-talk-or-presentation)
5. [Add a new software / R package page](#add-a-new-software--r-package-page)
6. [Add a new dataset / Dataverse link](#add-a-new-dataset--dataverse-link)
7. [Link things together (“See Also”)](#link-things-together-see-also)
8. [Update your bio or CV](#update-your-bio-or-cv)
9. [Add / remove research-group members](#add--remove-research-group-members)
10. [Edit the homepage](#edit-the-homepage)
11. [Edit the navigation menu](#edit-the-navigation-menu)
12. [Change a button label (“Article”, “Publisher’s Version”, …)](#change-a-button-label)
13. [Add a paper to a Research Area](#add-a-paper-to-a-research-area)
14. [Edit the teaching / contact / other pages](#edit-the-teaching--contact--other-pages)
15. [Troubleshooting](#troubleshooting)

---

## How the repo is organized

```
hugo-site/
├── content/              ← every page lives here
│   ├── publication/      ← papers, articles, books, datasets, patents
│   ├── talk/             ← presentations
│   ├── software/         ← R packages / tools
│   ├── authors/          ← people profiles (students, coauthors)
│   ├── bio/              ← "Bio & CV" page
│   ├── teaching/         ← "Teaching" page
│   ├── research-areas/   ← "Research Areas" topics
│   └── research-group/   ← "Research Group" listing page
├── static/files/         ← PDFs, supplementary downloads
├── data/                 ← JSON/YAML data files (research-area mapping, etc.)
├── layouts/              ← page templates (edit only for design tweaks)
└── assets/css/custom.css ← site-wide CSS
```

Each piece of content is a folder whose name becomes part of the URL.
Example: `content/publication/ecological-inference/index.md` →
`/gking-site/publication/ecological-inference/`.

---

## Editing from GitHub.com (no terminal)

1. Go to <https://github.com/KatalinaToth/gking-site>.
2. Click the folder path to drill into `hugo-site/…`.
3. Click any file → pencil icon ("Edit this file") → make changes → scroll
   down → **Commit changes**.
4. To **add a new file**: browse to the parent folder → **Add file → Create
   new file**. Type the full path in the filename box, e.g.
   `hugo-site/content/publication/my-new-paper/index.md`, then paste the
   template below.
5. To **upload PDFs**: browse to `hugo-site/static/files/` → **Add file →
   Upload files** → drag the PDF in → Commit.

Every commit to the `main` branch automatically runs the "Deploy Hugo site
to GitHub Pages" workflow. You can watch progress at
<https://github.com/KatalinaToth/gking-site/actions>. It usually finishes
in 3–4 minutes.

---

## Add a new paper / article / book

### Step 1: upload the PDF
Drop the PDF into `hugo-site/static/files/`. Use a short, lowercase,
hyphenated filename, e.g. `gerrymandering-partisan-symmetry-2026.pdf`.

### Step 2: create the page folder
Create a new file at:
```
hugo-site/content/publication/my-short-slug/index.md
```
Where `my-short-slug` is whatever you want to appear in the URL (lowercase,
hyphens, no spaces). This becomes the page URL permanently — so pick
something readable and stable.

### Step 3: paste this template and edit

```yaml
---
title: "Full Paper Title"
date: 2026-01-15
authors:
  - "Gary King"
  - "Coauthor Name"
publication_types:
  - "journal_article"
publication: "Journal Name, Vol, Pages"
abstract: "Paper abstract text here."
links:
  - name: Article
    url: "files/my-paper.pdf"
  - name: Publisher's Version
    url: "https://doi.org/10.xxxx/xxxxx"
  - name: Supplementary Material
    url: "files/my-paper-supp.pdf"
---
```

**Notes**

- `publication_types` must be one of the values listed in
  [the appendix](#appendix-publication-types).
- Any link in `links:` becomes a button on the page. `files/...` paths
  (no leading `/`) point at `static/files/`.
- `date` should be `YYYY-MM-DD` or `'YYYY-MM-DD'` — both work.
- `authors:` controls ordering; write names however you want them displayed.

### Which Writings tab does a paper land in?

The `/publication/` page groups items into tabs: **Journal Articles**,
**Books & Chapters**, **Presentations**, **Software**, **Patents**, and
**Other**. Tab placement is driven by `data/writings_legacy_map.json`,
which records each item's legacy category.

For new items, add an entry to that file (the keys are `tab` and
`drupal`). Valid `drupal` values and the tab each one appears in:

| `drupal`                 | Tab                  |
| ------------------------ | -------------------- |
| `journal_article`        | Journal Articles     |
| `book`                   | Books & Chapters     |
| `book_chapter`           | Books & Chapters     |
| `presentation`           | Presentations        |
| `software`               | Software             |
| `patent`                 | Patents              |
| anything else            | Other                |

The **Books** section on the homepage is built dynamically from all
entries in this file where `drupal: book`, so adding a new book here
surfaces it on the homepage automatically — no separate edit required.

### Step 4 (optional): featured image

Place a `featured.jpg` or `featured.png` next to `index.md`. It will be
shown at the top of the page and as the card thumbnail on the Writings
list.

---

## Add a new talk or presentation

Exactly the same pattern, but under `content/talk/`:

```
hugo-site/content/talk/my-talk-slug/index.md
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
  - name: Slides
    url: "files/my-talk-slides.pdf"
---
```

---

## Add a new software / R package page

Under `content/software/`:

```
hugo-site/content/software/my-software-slug/index.md
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
software_page_href: "https://gking.harvard.edu/software/my-tool"
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

### Where does a software item appear on the `/software/` page?

The software landing page groups items into three sections:

- **Active** — currently maintained / in current use
- **Acquired & Commercialized** — spun off into a company or long-lived
  product maintained elsewhere
- **Archived** — historical interest, superseded, or no longer maintained

Which section a given item lands in is controlled by the file
`hugo-site/data/software_legacy_rows.yaml`. Each row looks like:

```yaml
- year: 2020
  slug: opendp-developing-open-source-tools-for-differential-privacy
  status: active
```

To move an item between sections, just change its `status` to one of
`active`, `acquired`, or `archived`. To add a new item to the page,
append a new row with the same three fields (`year`, `slug`, `status`);
the `slug` must match the folder name under `content/publication/` (or
`content/software/`). Rows with no `status` default to `archived`.

---

## Add a new dataset / Dataverse link

A dataset is just a publication with `publication_types: data`. Put it
under `content/publication/` like any paper. Two extra fields unlock the
green "Harvard Dataverse" banner on the page:

```yaml
publication_types:
  - "data"
dataverse_url: "https://doi.org/10.7910/DVN/ABCDEF"
dataverse_name: "Replication Data for: Paper Title"
```

If the dataset is the replication archive for a specific paper, point at it
so a "Replication data for: …" banner is shown:

```yaml
related_paper: "publication-slug-of-the-paper"
```

---

## Link things together ("See Also")

The site automatically fills the "See Also" box at the bottom of every
paper, talk, and software page. The rules:

1. **You don't have to do anything** — the site scans titles, authors, and
   tags and links content that overlaps. Upload a new paper and any
   existing talk with a similar title / shared authors / shared tags
   will auto-link both ways after the next build.
2. **To force specific links**, add any of these to the front matter. Each
   takes a **slug** (the folder name of the other item). Whatever you put
   here always appears first:
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
4. The "See Also" box shows at most 6 items, sorted explicit-first, then by
   match strength, then by year (newest first).

---

## Update your bio or CV

**Bio text** — edit `hugo-site/content/bio/index.md`. Everything below the
`---` line is Markdown; write naturally.

**CV PDF** — upload a new file named `vitae.pdf` to
`hugo-site/static/files/` (overwriting the old one). The download button
already points there.

**Bio photo** — upload a new image named `gking-bio-photo.jpg` to
`hugo-site/static/images/` (overwriting the old one).

---

## Add / remove research-group members

Each person has their own folder under `hugo-site/content/authors/`:

```
hugo-site/content/authors/jane-doe/_index.md
```
(Note the leading underscore: `_index.md`, not `index.md`, for authors.)

```yaml
---
title: "Jane Doe"
role: "Graduate Student"
organizations:
  - name: "Harvard University"
user_groups:
  - "Current Members"
bio: "Short bio line."
social:
  - icon: envelope
    link: "mailto:jane@harvard.edu"
  - icon: globe
    link: "https://janedoe.com"
---

Longer biography in Markdown.
```

Upload a square photo named `avatar.jpg` next to `_index.md`.

To move someone from current to past, change `user_groups` to
`"Alumni"` (or whichever group is shown on the Research Group page).

---

## Edit the homepage

The homepage is assembled from "blocks" listed in
`hugo-site/content/_index.md`. To tweak wording on an existing block
(welcome text, research-area cards, featured items), edit that file.

To change which papers / talks are featured on the homepage, look for the
`featured:` lists near the top of `_index.md` and swap the slugs.

---

## Edit the navigation menu

The top menu is defined in `hugo-site/hugo.yaml` under `menus.main`. Each
entry has a `name`, a `url`, and a `weight` (lower = more to the left):

```yaml
menus:
  main:
    - name: Bio & C.V.
      url: /bio/
      weight: 10
    - name: Writings
      url: /publication/
      weight: 20
```

Add, remove, or reorder by editing this list.

---

## Change a button label

Button text such as "Article" or "Publisher's Version" is controlled in
`hugo-site/i18n/en.yaml`:

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
`hugo-site/data/research_areas.json`. Each area has subcategories, each
with a `papers:` list. To add a paper, append its slug:

```json
{
  "name": "Ecological Inference",
  "papers": [
    {"title": "Paper Title", "section": "publication", "slug": "paper-slug"}
  ]
}
```

`section` is one of `publication`, `talk`, or `software`.

---

## Edit the teaching / contact / other pages

Plain pages are all under `hugo-site/content/`, one folder each, with an
`index.md` inside. Edit that Markdown file directly.

| Page | File |
|------|------|
| Teaching | `content/teaching/_index.md` |
| Contact | `content/contact/index.md` |
| Dataverse | `content/dataverse/index.md` |
| Research Group landing | `content/research-group/index.md` |
| Homepage | `content/_index.md` |

### Advice & Suggestions

All of the "Advice and Suggestions" links live at the **bottom of the
Teaching page** (`content/teaching/_index.md`, under the `<h2
id="advice">` heading). The footer bar's "Advice and Suggestions" link
jumps there via the `#advice` anchor, and the legacy `/advice/` URL
auto-redirects to the Teaching page (via the `aliases:` entry at the top
of `teaching/_index.md`). To add, remove, or reorder advice items, edit
that section.

---

## Troubleshooting

**"I committed and nothing changed on the site."**
Give it 3–4 minutes. Then visit
<https://github.com/KatalinaToth/gking-site/actions>. If the latest run has
a red ✗, click it to see the error (almost always a typo in YAML front
matter, e.g. a missing quote or a bad date).

**"A PDF returns 404 on the live site."**
Confirm the file is in `hugo-site/static/files/` and the `url:` in the
page's `links:` starts with `files/` (no leading slash).

**"The 'See Also' box is empty or wrong."**
Add shared `tags:` or pin specific items with `related_papers`, etc. (see
above). Explicit wins always override the automatic ones.

**"Search finds nothing."**
The search index is rebuilt on each deploy. Wait until the Actions run is
green and hard-refresh the page.

**"I accidentally broke the site."**
In GitHub, click the commit that broke things → **Revert**. That creates a
new commit undoing the change. After the build finishes, the site is back.

---

## Appendix: publication types

Use exactly one of these strings in `publication_types:`.

```
journal_article
book
book_chapter
conference_paper
conference_proceedings
data
miscellaneous
newspaper_article
patent
presentation
report
software
unpublished
web_article
website
working_paper
```
