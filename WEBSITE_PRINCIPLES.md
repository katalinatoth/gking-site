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

## 14. Design principles

The single most important rule: **the user should never feel trapped,
confused, or forced to repeat themselves.** Every concrete rule below
ladders up to that. Use this section as a checklist when reviewing any
new page or feature.

### 14.1 No dead ends

Every page must lead somewhere useful. A reader who lands on any page —
via Google, a citation, a share link — must be one glance away from:

- **A way back up.** Breadcrumbs (Home / Writings / Paper Title) or a
  clearly-labelled parent link. Never rely on the browser back button as
  the only exit.
- **Related work.** Every paper/talk/software/dataset has an automatic
  "See Also" block (§6). If that block is empty for a page, something is
  wrong — either add tags or add an explicit override.
- **The site's main navigation.** The top navbar is present on every
  page, so readers entering mid-site can always find Bio, Writings,
  Research, Contact.
- **Site-wide search.** The search button is reachable from every page
  (navbar) and via `Cmd-K` / `Ctrl-K`.

404s must themselves be non-dead-ends: the 404 page shows the navbar and
a search box, not just "page not found".

### 14.2 Preserve context; prefer expansion over navigation

When opening secondary content, **do not pull the reader out of their
current context**. Concretely:

- **Filter and tab changes must not reload the page.** The Writings tabs,
  year facets, and sort order are all client-side JS. Changing a filter
  updates the URL (so it's shareable) but does not reset scroll position
  or lose other filter state.
- **The search modal is an overlay**, not a separate page. It opens on
  top of the current page with the backdrop visible, closes on `Esc`,
  and leaves the reader exactly where they were.
- **Dropdowns / expandable sections stay in place.** Do not link off to
  another page for something that can be expanded inline (e.g. "show
  more authors", "show abstract", "show citation").
- **Back button always works.** Every state change that creates a new
  visible page uses a real URL change with `history.pushState`. Arrow
  keys, filter buttons, and search do not trap the user in a modal
  stack.
- **Nested dialogs are banned.** If a modal opens another modal, the
  design has failed — flatten it.

### 14.3 Single source of truth; never duplicate information

Every fact lives in **exactly one place**.

- **Authors, title, abstract, date, venue** for a paper are defined once
  in the paper's `index.md` front matter. Every list view (Writings
  tabs, Research Area pages, author pages, "See Also") reads the same
  fields. You never type the title twice.
- **The abstract is shown once per page**, not in both a sidebar and the
  body. If the layout shows a banner + body, one must summarize and the
  other must be the full copy — never duplicates.
- **Do not render the same download button twice.** If a PDF is linked
  from the top button row, do not also put a text "Download PDF" link in
  the abstract. Exceptions: legacy replicas where the source site
  duplicated a link; keep it only to match fidelity.
- **Cross-links, not copies.** When a paper has a companion dataset, the
  dataset page *links* to the paper (and vice versa). It does not
  re-paste the paper's abstract.
- **Migration metadata lives in `data/`, never copied into
  content front matter.** (§7.) Legacy category, legacy Drupal node ID,
  thumbnail URL are attached by slug at build time.
- **Button labels are centralized in `i18n/en.yaml`.** Never inline the
  string "Article" or "Publisher's Version" in a template.

### 14.4 Stable, meaningful URLs — forever

Academic pages are cited in papers that will outlive the website. URLs
are a contract.

- **The directory name of a content folder is the permanent slug.** Never
  rename a folder once the site is live. If the title changes, edit
  `title:` in front matter but keep the folder.
- **Redirects for legacy URLs.** When migrating, use Hugo's `aliases:`
  front-matter key (or the generated redirect files under `public/`) to
  forward every old URL path to the new one. Nothing from the previous
  site should 404.
- **No URL-visible IDs.** Slugs are human-readable (kebab-case title),
  not numeric primary keys or random hashes.
- **Deep links work.** A reader who gets `…/publication/<slug>/#abstract`
  from a friend lands scrolled to the abstract. Do not use JS routers
  that discard hash fragments.

### 14.5 Information density over whitespace

Academic readers want **more on the screen**, not less. Reject marketing
defaults.

- No hero sections on content pages.
- Dense citation lists (author, year, title, venue in one line) are
  good; card grids with one paper per row are wasteful.
- White space belongs between logical sections, not padded around every
  line of text.
- The Writings page shows ~25 items per screen at reasonable zoom. If
  pagination is needed it is after 100+, not after 10.

### 14.6 Scannable structure; labels over ornament

- Every list item in "Links", "See Also", and banner areas must carry a
  **type label** (`[Paper]`, `[Talk]`, `[Software]`, `[Dataset]`,
  "Harvard Dataverse", "Publisher's Version", "Supplementary Material").
  The reader should never have to click to find out what a link is.
- **Link text describes the destination.** Never "click here" or "read
  more". Prefer "Article (PDF)", "Replication data on Harvard
  Dataverse", "Project website".
- **Headings follow a strict hierarchy.** H1 per page, H2 for main
  sections, H3 for subsections. Never skip levels for visual weight —
  use CSS instead.
- **Icons complement but do not replace text labels.** A lone envelope
  icon is ambiguous; "Email: gking@harvard.edu" is not.

### 14.7 Preserve the owner's voice and the legacy site's fidelity

- **Do not paraphrase the owner's content.** If the bio reads oddly,
  fix only typos or ask. Paraphrased academic bios are almost always
  worse than the original.
- **Match the legacy site's structure when migrating.** Same tab names,
  same ordering of categories, same colour accent, same button labels.
  Surprise is a bug. The owner should open the new site and not realize
  it is new.
- **When the legacy site is wrong, flag it, don't silently correct
  it.** Put a comment in the markdown. The owner decides.

### 14.8 Longevity and self-sufficiency

- **Everything required to render the site lives in the repo.** No CDN
  links that can go dark, no external iframes for primary content, no
  reliance on a third-party comments/analytics service for the page to
  be readable.
- **Search runs client-side** (Pagefind). No search server, no runtime
  API, no key management.
- **All PDFs live in `static/files/`.** Never link to someone else's
  copy of the author's own paper; host it here.
- **The published output is plain HTML + CSS + a small JS bundle.** It
  will render in 10 years, on any browser, even if the build toolchain
  has rotted.

### 14.9 Accessibility is table stakes

- **Every image has meaningful `alt` text.** Featured thumbnails use the
  paper title; figures in the body use their caption.
- **Semantic HTML.** `<nav>`, `<main>`, `<article>`, `<h1>`–`<h3>` per
  page. Do not style `<div>` soup to look like headings.
- **Keyboard navigation.** Tab goes through links in reading order;
  `Cmd-K` opens search; `Esc` closes any overlay; arrow keys navigate
  search results.
- **Focus states remain visible.** Never `outline: none` without a
  replacement.
- **Contrast ratios** hit WCAG AA minimum — body text 4.5:1, large text
  3:1. The burnt-orange banner uses white text over `#BF5803` =
  contrast 4.7:1; that's the floor, not the ceiling.
- **No colour-only signalling.** Draft vs published, dataset vs paper
  etc. are communicated with a text label **and** a colour, not colour
  alone.

### 14.10 Performance

- **HTML is meaningful at first paint.** Do not require JS for reading
  content. JS is only for interactivity (filters, search, tabs).
- **No layout shift during load.** Every `<img>` has explicit
  `width`/`height` (templates resolve these from Hugo image processing).
- **Minify HTML/CSS/JS in production** (already in `deploy.yml`).
- **Lazy-load images below the fold.** The template sets `loading="lazy"`
  on everything except the first hero/featured image on each page.
- **Pagefind is loaded on first search-open, not up front.** The navbar
  "Search" button defers the ~200KB WASM bundle until the modal opens.

### 14.11 Failure modes should degrade gracefully

Every interactive feature has a plausible failure. Design for it:

- **If JS fails**, the Writings page still shows all entries in static
  HTML (server-rendered). Filters are missing, but content isn't.
- **If Pagefind fails to load**, the search modal shows a text input
  that submits to a Google "site:" search as a fallback.
- **If an image 404s**, the `alt` text still tells the reader what was
  there.
- **If a content file is malformed**, the build fails in CI before the
  site is published. The owner sees a red X on their commit, not a
  broken live site.

### 14.12 Automation over discipline

Humans forget; scripts don't. Any recurring manual step is a bug.

- "See Also" is computed, not maintained (§6).
- Thumbnails are fetched and cropped by a script.
- Weekly link health check runs on a cron (§11).
- Deployment is on every push; nobody has to remember to deploy.
- **Anything a human has to remember to do weekly will not get done.**
  If a task recurs, move it into CI or into a build-time template.

### 14.13 Visual language

- **Typography:** native system font stack via Blox (`font: native`).
  Fast, respects OS settings, matches institutional style guides.
- **Palette (this site):** ink `#222` text, link blue `#337ab7`,
  muted `#666`/`#888` for metadata, burnt orange `#BF5803`–`#d4690a`
  for software/action headers, soft green `#f0f7ee`/`#2d6a1e` for
  dataset/Dataverse banners, soft blue `#e8f4fd`/`#337ab7` for
  replication-data banners.
- **Palette discipline:** colours mean things. Blue = a link. Green =
  data/replication. Orange = software/action. Don't reuse colours for
  unrelated purposes.
- **Shape:** rounded corners 4–8px; subtle shadows only on interactive
  cards; 1px hairlines (`#e2e8f0`) for dividers.
- **No ornamental animation.** Animated GIFs are used only as
  **content** (e.g. the quest paper's RD animation), never as decoration.

### 14.14 Editorial principles

These apply to every piece of text on the site.

- **Say the thing once, clearly.** Bios, abstracts, and descriptions
  that say the same idea three different ways get cut to one.
- **Active voice; present tense for current work, past for completed
  work.**
- **No academic hedging in interface copy.** Button says "Download PDF",
  not "You may wish to download the PDF".
- **Dates are unambiguous:** `Jan 2, 2026`, never `1/2/26`.
- **Author names spelled as the author spells them**, including
  diacritics, casing, and middle initials. Look this up for every
  coauthor.
- **No Oxford/Harvard commas wars** — pick one (Oxford) and use it
  everywhere.

### 14.15 Tone — understated, credit-sharing, never braggy

Academic personal sites rot fast into trophy cases. Don't let them.

- **State what the person did, not how impressive it is.** "Honours
  thesis on Indigenous health policy, supervised by Prof. X" is the
  right register. "Wrote a groundbreaking honours thesis that reshaped
  the field" is the wrong register.
- **No intensifiers, no self-superlatives.** Strike *groundbreaking*,
  *pioneering*, *world-class*, *highly*, *extremely*, *exceptional*
  from your vocabulary when writing about the site's owner. Strike
  them even when they appear in letters of reference you're drawing
  from.
- **Let the nouns do the work.** Harvard, Phi Beta Kappa, a named
  prize, a peer-reviewed citation count — these carry their own weight.
  Piling adjectives on top is a tell that the writer doesn't trust the
  reader to recognise the signal.
- **Share credit by default.** Research is collaborative. Name
  supervisors, co-authors, and labs in every description. Prefer "at
  Prof. X's lab, I contributed Y" over "I did Z" when both are true.
- **Awards go in an `Honors` section, once.** They are listed flatly,
  without editorializing. Never re-mention an award in a bio paragraph
  *and* in the honours list *and* in a project description.
- **Prizes are named, not ranked.** Say "Sophia Freund Prize" rather
  than "the most prestigious undergraduate prize at Harvard". If the
  reader needs to know what it is, they'll click — and the entry can
  quote the award citation verbatim, in a blockquote, rather than the
  owner's paraphrase.
- **No humble-bragging either.** "I was lucky to be selected for…"
  is worse than just stating the fact. Read copy aloud; if it sounds
  like a cover-letter opener, rewrite it.
- **When the CV is long, the prose is short.** The density of
  accomplishments on academic CVs is the signal; restating them in
  the bio dilutes it. Bio paragraphs are for context, narrative arc,
  and the questions the person cares about — not for a second pass
  over the honours list.
- **"Selected"** is the correct adjective for a section that is
  necessarily partial, not *notable*, *major*, or *key*.

### 14.16 Images — owned first, public web where necessary

Academic sites need photos they don't always have in hand: a portrait
of the owner, a conference room they spoke in, the cover of a journal
issue, a map of a field site. The repo-first principle (§14.8) rules
out hotlinking, but it does **not** rule out fetching.

- **Always prefer a photo the owner has given you**, or one the owner
  has on their institutional page. Ask once before scraping.
- **If no owned image exists, pull from the public web and commit it
  to the repo.** Good sources, in descending preference:
  1. The owner's institutional profile page (the university almost
     always has usage rights; mirror the photo into `assets/images/`
     or `static/images/`).
  2. Wikimedia Commons, Flickr with Creative Commons, or the
     publisher's own press-kit page.
  3. A screenshot of a publicly accessible page, only as a last
     resort, and only for *context* images (e.g. a legacy site
     mid-archive).
- **Never hotlink.** Download the image, commit it, reference it by
  its local path. External image hosts go dark; your site must not.
- **Record provenance.** Every non-owned image gets a
  `_credits.md` line in `data/image_credits.yaml`, or a `credit:`
  entry in the page's front matter, listing the source URL, date
  fetched, and licence ("CC-BY 4.0, Wikimedia", "institutional
  profile, fair use", "public press kit, Harvard Gazette").
- **Respect licences.** CC-BY requires attribution; CC-BY-SA
  requires share-alike; "all rights reserved" press-kit photos are
  usually fine for biographical use but flag them to the owner.
  When in doubt, pick a different photo.
- **Crop and optimise locally.** A portrait should be ~480×480 or
  ~720×720 square, under 150 KB after `hugo`'s image pipeline. Don't
  ship the 4 MB original.
- **Image alt text is factual, not promotional.** "Portrait of Prof.
  X, Harvard University" — not "Prof. X, distinguished professor".
- **Placeholder first, photo second.** Templates should render a
  neutral monogram or silhouette when the expected image is missing,
  so the site still looks intentional during migration. The AI should
  scaffold the placeholder and note in the commit message where to
  drop the real photo.
- **Portraits go to the homepage and bio only.** Don't decorate
  other pages with the owner's face; it undermines §14.15.

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
