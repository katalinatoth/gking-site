# Academic Website Principles & Playbook

A distilled set of rules, architectural decisions, and gotchas learned from
building the Gary King academic website. Feed this document back to your
AI assistant whenever you start a new professor/research-lab site and it
will produce a result with the same properties without re-deriving the
hard parts from scratch.

The audience for this document is **you + an AI assistant**, not end users.

---

## 0. Core premises (non-negotiable)

1. **The site owner updates content by committing Markdown on GitHub.**
   Everything else is infrastructure. If the owner needs a terminal to
   publish a paper, the architecture has failed.
2. **Content and presentation are fully separated.** Content is in
   `content/**/*.md` with YAML front matter. Templates in `layouts/` and
   CSS in `assets/css/` render it. A content change never touches a
   template.
3. **Deployment is automatic on push to `main`.** GitHub Actions builds
   Hugo, builds the search index, and publishes to GitHub Pages. No
   manual build step is ever needed for normal publishing.
4. **Related-content links are automatic by default, overridable per
   item.** The default behaviour handles 90% of cases; explicit front
   matter wins where it matters.
5. **The site must match the legacy source closely enough that the
   professor does not notice a change.** Preserve URLs, tab names, palette,
   labels, and publication ordering of the predecessor site.

---

## 1. Tech stack defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Static site generator | **Hugo** (extended) | Fast, one binary, first-class academic theme ecosystem, no Node build pipeline for content. |
| Theme | **Hugo Blox** (`blox-tailwind`) via Go module | Academic-CV-ready partials, taxonomy, author cards, search modal, Tailwind pipeline. |
| CSS | Tailwind-compiled by Blox + a single `assets/css/custom.css` for overrides | Tailwind for quick styling, custom.css for CMS-visible semantic classes like `.gk-see-also`. |
| Search | **Pagefind** (static, wasm-based) | No search server; index built in CI; works on GitHub Pages. |
| Hosting | **GitHub Pages** project site (`username.github.io/repo/`) | Free, versioned, identical to dev. |
| CI | GitHub Actions | Build Hugo → build Pagefind → deploy pages artifact. |
| Vendored theme | `_vendor/` (Hugo module vendor) | Freezes theme version; allows searching/copying vendor templates. |

Create a `go.mod` in `hugo-site/` that imports Blox modules:
```go
module github.com/ORG/REPO-site
go 1.22
require (
  github.com/HugoBlox/hugo-blox-builder/modules/blox-tailwind v0.10.0
)
```
Run `hugo mod vendor` to lock it into `_vendor/`.

---

## 2. Directory contract

```
hugo-site/
├── archetypes/                # templates for `hugo new`
├── assets/css/custom.css      # project-wide overrides
├── content/                   # all pages (markdown)
│   ├── _index.md              # homepage
│   ├── publication/           # papers, books, datasets
│   ├── talk/                  # presentations
│   ├── software/              # R packages / tools
│   ├── authors/               # people profiles (_index.md per person)
│   ├── bio/, teaching/, …     # flat singleton pages
│   └── research-areas/        # topic landing pages
├── data/                      # project-owned JSON / YAML
├── i18n/en.yaml               # label overrides
├── layouts/                   # project-level theme overrides
│   ├── _partials/             # mirror of vendor _partials for overrides
│   ├── publication/{list,single}.html
│   ├── talk/{list,single}.html
│   ├── software/{list,single}.html
│   └── shortcodes/staticrel.html  # see §4
├── static/files/              # PDFs, supplementary downloads
├── static/images/             # non-content images (bio photo, logos)
├── scripts/                   # optional Python scrapers & data builders
├── _vendor/                   # hugo mod vendor output (checked in)
├── go.mod, go.sum
├── hugo.yaml                  # site config
├── package.json               # just for `npx pagefind`
├── .github/workflows/deploy.yml
├── UPDATING.md                # Gary-facing guide
└── WEBSITE_PRINCIPLES.md      # this file
```

**Rule of thumb for overrides:** if you need to customize a Blox partial,
copy it from `_vendor/.../layouts/_partials/<path>` to
`layouts/_partials/<path>` and edit there. Hugo picks the project copy.

---

## 3. `hugo.yaml` essentials

```yaml
baseURL: "https://USERNAME.github.io/REPO/"   # MUST end with a slash
title: "Site Title"
languageCode: en-us

module:
  imports:
    - path: github.com/HugoBlox/hugo-blox-builder/modules/blox-tailwind

outputs:
  home: [HTML, RSS, JSON]

params:
  header:
    navbar:
      enable: true
      show_search: true
  features:
    search:
      provider: flexsearch   # Blox default; Pagefind still works via overridden modal

taxonomies:
  tag: tags
  category: categories
  publication_type: publication_types
  author: authors

permalinks:
  publication: /publication/:slug/
  talk: /talk/:slug/
  software: /software/:slug/
```

**Critical:** when the site is deployed to a project subpath
(`username.github.io/repo/`), **everything that produces a URL must respect
the base path.** This is the #1 cause of 404s. See §4.

---

## 4. Subpath-safe URLs (the single biggest gotcha)

GitHub Pages project sites live under `/REPO/`. Any literal `/files/foo.pdf`
or `import('/pagefind/pagefind.js')` resolves to the **host root**, not the
project path, and 404s in production.

### Rules

1. **Never write `/foo` literally** in content or templates if it needs to
   resolve under `baseURL`.
2. **In templates**, use `relURL` without a leading slash:
   ```go
   {{ "pagefind/pagefind.js" | relURL }}    {{/* yields /REPO/pagefind/... */}}
   ```
   Hugo's docs are explicit: `relURL "/x"` strips the base path;
   `relURL "x"` keeps it.
3. **In content Markdown**, never write `/files/foo.pdf`. Instead provide a
   shortcode:
   ```html
   {{</* staticrel "files/foo.pdf" */>}}
   ```
   which wraps `relURL` and produces the correct `/REPO/files/foo.pdf`.
4. **For images inside content**, likewise use the shortcode:
   ```markdown
   ![figure]({{</* staticrel "files/figure.png" */>}})
   ```

### The `staticrel` shortcode

```html
{{/* layouts/shortcodes/staticrel.html */}}
{{- (.Get 0) | relURL -}}
```

### The Pagefind fix

Blox's default search modal hard-codes `import('/pagefind/pagefind.js')`.
On a project site this breaks. Override
`layouts/_partials/components/search-modal.html` and change that one line
to:
```go
import('{{ "pagefind/pagefind.js" | relURL }}')
```
Pagefind then derives its asset base from `import.meta.url` and correctly
loads all chunks and the WASM blob from under `/REPO/pagefind/`.

---

## 5. Content model

Every content type is a directory per item, containing `index.md` (or
`_index.md` for list/root pages and `authors/`). The **directory name is
the slug** and appears in the URL.

### Publications, talks, software share a minimal front-matter shape

```yaml
---
title: "…"
date: YYYY-MM-DD
authors: ["Gary King", "…"]
publication_types: ["journal_article"]
publication: "Journal Name, Vol, Pages"   # optional
abstract: "…"
links:
  - name: Article
    url: "files/foo.pdf"
  - name: Publisher's Version
    url: "https://doi.org/…"
---
```

- `publication_types` drives filtering and templates. Keep the controlled
  vocabulary stable (see appendix in UPDATING.md).
- `links` with `name` + `url` renders as styled buttons. `url` starting
  with `files/…` points at `static/files/`.
- Featured image: drop `featured.jpg`/`.png` next to `index.md` and the
  layout auto-discovers it via `partial "functions/get_featured_image.html"`.

### Datasets are publications

Datasets are just `publication_types: [data]` with two optional fields:

```yaml
dataverse_url: "https://doi.org/10.7910/DVN/XXXXX"
dataverse_name: "Replication Data for: Paper Title"
related_paper: "paper-slug"   # renders a "Replication data for:" banner
```

### Authors are people

```
content/authors/jane-doe/_index.md
```

Contains `user_groups` to slot them into Research Group sections
(`Current Members`, `Alumni`, …). Avatar is `avatar.jpg` alongside.

---

## 6. "See Also" = automatic by default, manual when needed

This was a specific user requirement — uploading a new paper should
auto-find presentations, software, and datasets that are its cousins.

### Design

A single partial, `layouts/_partials/related_finder.html`, runs at build
time on every publication/talk/software page:

1. **Explicit overrides always win.** Front-matter fields are honored first,
   in this order: `related_papers`, `related_talks`, `related_software`,
   `related_datasets`, then legacy singular `related_paper` /
   `related_dataset`.
2. **Automatic scoring.** Every other page across
   `{publication, talk, software}` gets a score:
   - +2 per overlapping **title token** (lowercased, stopwords stripped,
     tokens < 3 chars dropped)
   - +1 per shared **author**
   - +2 per shared **tag / keyword**
3. Pages above threshold (default 4) are appended after explicit picks,
   sorted by score desc. Capped at 6 total.
4. Each rendered item is labelled `[Paper]`, `[Talk]`, `[Software]`, or
   `[Dataset]` so the reader sees the relationship at a glance.

### Why this design

- **No scripts.** Lives entirely in Hugo templates; rebuilds happen in CI
  automatically with no additional step.
- **Owner does nothing.** Upload a new paper, get cross-links
  automatically.
- **Power users still have full control.** Front matter overrides always
  win, in the order declared.
- **No stale data files** (a Python-generated `related_map.json` would go
  out of date the moment you add a paper and forget to re-run the script).

### When to add explicit overrides

- When the auto-match picks something tangentially related.
- When two items share no title words but are conceptually the same work
  (e.g. a software package named differently from the paper that describes
  its method).

---

## 7. Tabs, filters, legacy mapping

Complex list pages (e.g. "Writings") are best implemented as:

1. **Hugo template** that serializes all regular pages in the relevant
   sections to a JSON array (`window.GK_ENTRIES`).
2. **Vanilla JS** on the page that renders tabs, sidebar filters, search,
   and sort client-side.

This pattern is in `layouts/publication/list.html`. It is fast (<2k items
on academic sites), works with search engines (HTML present at load), and
lets non-trivial filtering happen without a framework.

### Legacy category mapping

When migrating from a Drupal / legacy site with its own category taxonomy,
do not try to reproduce it at the content level. Instead:

1. Scrape the legacy categories from GTM / sitemap into a JSON map:
   `data/writings_legacy_map.json = { entries: { slug: { tab, drupal } } }`.
2. In the template, look up each item's slug to get its `legacyTab` /
   `legacyDrupal`, and use those as filter attributes.

This keeps migration metadata out of the content files entirely — it lives
in one regenerable JSON file under `data/`.

---

## 8. The "quest-paper" / full-replica pattern

Sometimes an item needs a **custom page layout** that differs from the
default publication rendering (e.g. to replicate a legacy special-case
page with animations and non-standard attachments). Don't fork the
template. Instead:

1. Add `quest_replica: true` (or any boolean) to the item's front matter.
2. In `layouts/publication/single.html`, branch on that flag and skip the
   default citation/abstract/buttons blocks when true.
3. Put the custom layout inline in the Markdown body using raw HTML,
   `staticrel` shortcodes, and the existing CSS.

This lets one template serve both the normal and special cases without
template sprawl.

---

## 9. Overriding Blox partials

Rule: **the project `layouts/` directory mirrors `_vendor/.../layouts/`
exactly.** Partials that live at `_vendor/.../layouts/_partials/foo.html`
must be overridden at `layouts/_partials/foo.html` (not
`layouts/partials/foo.html` — Hugo Blox uses the `_partials` convention).

Workflow:
1. `cp _vendor/.../layouts/_partials/path/to/file.html layouts/_partials/path/to/file.html`
2. Edit the project copy.
3. Rebuild — the project version shadows vendor.

Common overrides:
- `_partials/components/search-modal.html` (fix Pagefind path)
- `_partials/components/headers/navbar.html` (custom nav)
- `_partials/page_links.html` (button labels / order)
- `_partials/page_author_card.html` (author-card layout)

---

## 10. GitHub Actions deployment

Key fragments of `.github/workflows/deploy.yml`:

```yaml
- name: Build with Hugo
  env:
    HUGO_ENVIRONMENT: production
    TZ: America/New_York
  run: hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"

- name: Build Pagefind search index
  run: npx pagefind --site public

- uses: actions/upload-pages-artifact@v3
  with:
    path: ./public
```

Important:

- `--baseURL` uses the URL GitHub Pages gives you (includes trailing slash
  for project sites).
- Pagefind must run **after** Hugo, against `public/`.
- Commit a `package.json` containing just `"devDependencies": { "pagefind":
  "^1.5" }` (or let `npx pagefind` resolve it each run).

---

## 11. Link health & content hygiene

- Run a **weekly scheduled link-check workflow** (`link-check.yml`) that
  scrapes every external URL from content Markdown and opens/updates a
  GitHub issue labelled `link-check` when any 404. Keeps the site usable
  without the owner policing it.
- Keep a small **scripts/** directory of idempotent Python scrapers for
  migrating or refreshing data. Each must be **safe to re-run** and must
  write only to `data/` or `content/`, never to `layouts/`.

---

## 12. Reproducing this architecture (kickstart checklist)

For a new faculty/lab site:

1. `mkdir prof-site && cd prof-site && git init && gh repo create`.
2. `hugo new site hugo-site` (keep the `hugo-site/` subfolder — leaves room
   for scripts, READMEs, and sibling projects).
3. Add `hugo.yaml`, `go.mod`, `package.json` with Pagefind, and the Blox
   module import. Run `hugo mod vendor`.
4. Copy in `deploy.yml` and `link-check.yml` from this project.
5. Copy `staticrel.html` shortcode and `related_finder.html` partial.
6. Override the Blox search modal (one-line `relURL` fix).
7. Create one example piece of content in each section
   (`publication/`, `talk/`, `software/`, `authors/`) as a canonical template.
8. Commit; verify Pages deploy works; verify Pagefind finds the examples;
   verify "See Also" auto-link works between two items that share authors.
9. Write the site-specific `UPDATING.md` (clone this project's).
10. Hand the owner the repo URL and the `UPDATING.md`. You're done.

---

## 13. Things I learned the hard way in this build (checklist of past pain)

Feed this list to the AI assistant; it preemptively avoids each one.

- [ ] `baseURL` in `hugo.yaml` **must include the `/REPO/` suffix and a
      trailing slash** for project Pages deployments. Missing trailing
      slash breaks `relURL` math.
- [ ] `relURL "/x"` returns `/x`; `relURL "x"` returns `/REPO/x`. Use the
      latter unless you *want* to escape the base path.
- [ ] Blox search modal hard-codes `/pagefind/pagefind.js`. Patch it with
      `{{ "pagefind/pagefind.js" | relURL }}`.
- [ ] Hugo Blox uses `layouts/_partials/…`, not `layouts/partials/…`.
      Getting this wrong means the override is silently ignored.
- [ ] Don't use `<iframe>` for animated GIFs on GitHub Pages project
      sites — `<img>` works and respects `relURL` via `staticrel`.
- [ ] Do not put a leading `/` on `url:` in front-matter `links:`. The
      page-links partial resolves `files/foo.pdf` correctly; `/files/...`
      bypasses the base path.
- [ ] Migration JSON belongs in `data/`, not in content front matter. This
      keeps migrations regeneratable.
- [ ] Replica / special pages: branch the template on a boolean front
      matter flag (`quest_replica: true`) rather than forking the
      template.
- [ ] Write "See Also" as a single template-level partial using
      title-token + author + tag scoring. Do NOT introduce a Python script
      that writes `related_map.json` — it inevitably gets stale.
- [ ] Pagefind must be built **after** Hugo in the Actions workflow, and
      before the upload-artifact step. Both against `public/`.
- [ ] Commit `_vendor/` to the repo. It's the only way to reliably
      override Blox partials and keeps builds hermetic.
- [ ] The `go.sum` must be checked in alongside `go.mod`, or Hugo mod
      verification will fail in CI.
- [ ] When a button or label needs to be renamed site-wide, change it in
      `i18n/en.yaml`, not the template.

---

## 14. Style / UX principles

- **Match the legacy site's information density, not modern minimalism.**
  Academic audiences expect dense citation lists with links, not hero
  sections.
- **Burnt-orange highlight palette** (`#BF5803` → `#d4690a`) is a strong
  candidate for headers/banners on academic sites — used on the legacy GK
  site; Harvard crimson is too aggressive.
- **Typography**: native system stack (`font: native` in Blox params) is
  fastest and matches most institutional style guides.
- **Never rely on JavaScript for primary content**; JS is fine for
  filters, tabs, and search, but the paper list should be in HTML at load.
- **Every external link in "Links / See Also / banners" should indicate
  type** (`[Paper]`, `[Talk]`, `Harvard Dataverse`, etc.) so readers
  orient at a glance.

---

## 15. For your next site

Hand this document to the AI alongside:

1. The legacy site URL.
2. The owner's CV / bio PDF.
3. A list of any unique content types beyond paper/talk/software/dataset.
4. The GitHub repo name (so it can fix `baseURL` correctly).

Ask it to:

1. Scaffold per §12.
2. Scrape the legacy site per §7 into `data/*.json`.
3. Ingest the CV into publication content files.
4. Wire the auto "See Also" per §6.
5. Write a site-specific `UPDATING.md` based on this project's template.
6. Deploy and hand back the URL.

That, empirically, produces a faithful, auto-updating academic site in a
few hours of iteration instead of weeks.
