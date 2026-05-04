# gking-site

Source for <https://katalinatoth.github.io/gking-site/> — Gary King's
academic website, built with Hugo + Hugo Blox.

## Repository layout

The repo is organised by **website section**. Anything Writings-related
lives under `writings/`, everything People-related under `people/`, and
so on. Hugo's hard-coded `content/`, `layouts/`, `data/`, etc. folders
disappear from the top level and are reassembled at build time via
`module.mounts` in [`hugo.yaml`](hugo.yaml).

```
hugo-site/                  the gking-site git repo root
├── hugo.yaml               site config + module.mounts (the wiring)
├── go.mod, package.json    Hugo modules + Tailwind plumbing
│
├── home/                   "/" landing page
├── bio/                    /bio/
├── writings/               /publication/  (~298 papers)
├── software/               /software/
├── dataverse/              /dataverse/
├── people/                 /research-group/, /people/, /authors/
├── teaching/               /teaching/
├── talks/                  /talk/
├── blog/                   /blog/
├── research-areas/         /research-areas/
├── contact/                /contact/
├── pages/                  standalone pages (apply, recs, …)
├── redirects/              legacy URL aliases
│
├── layouts/                shared theme bits — baseof.html, _default/,
│                           _partials/, shortcodes/, page/. STAYS at the
│                           project root because HugoBlox's get_hook
│                           partial calls os.ReadDir on this path
│                           literally and is not mount-aware.
├── assets/                 css/custom.css + media/. STAYS at the project
│                           root for the same reason (HugoBlox's
│                           site_head.html uses fileExists on this path).
│
├── _site/                  cross-section Hugo plumbing (static/, data/,
│                           archetypes/, i18n/) — see _site/README.md.
├── _automation/            intake bots, cross-section scripts,
│                           _automation/intake/ uploads.
├── docs/                   repo docs (UPDATING.md, MAINTENANCE.md,
│                           WEBSITE_PRINCIPLES.md, audits/).
│
└── .github/, .githooks/    CI workflows + auto-push hook. STAY at the
                            project root — GitHub Actions and git both
                            look for these by literal path and don't
                            follow Hugo mounts.
```

Each section folder has its own `content/`, `layouts/`, `data/`, and
(where it makes sense) `scripts/` subfolders, plus a `README.md` with a
section-specific cheat sheet. Hugo's `module.mounts` block remaps each
of those onto Hugo's expected target paths so URLs and the build are
unchanged.

## Where do I find X?

| You want to edit / find …                  | Look here                                                       |
| ------------------------------------------ | --------------------------------------------------------------- |
| A specific paper                           | `writings/content/<slug>/index.md`                              |
| A specific talk / slide deck               | `talks/content/<slug>/index.md`                                 |
| A software tool's page                     | `software/content/<slug>/index.md`                              |
| Someone's research-group / alumni profile  | `people/content/profiles/<slug>/index.md`                       |
| Site bio                                   | `bio/content/index.md`                                          |
| Home page sections                         | `home/content/_index.md`                                        |
| The "Featured" carousel                    | `writings/data/featured_publications.yaml`                      |
| The Writings page tab routing              | `writings/data/writings_legacy_map.json`                        |
| The dataverse list                         | `dataverse/data/dataverse.json`                                 |
| The research-group roster                  | `people/data/research_group.json`                               |
| Legacy URL redirects                       | `redirects/data/redirects.yaml`                                 |
| PDFs                                       | `_site/static/files/<slug>.pdf`                                 |
| Section-specific scripts (e.g. intake)     | `<section>/scripts/`                                            |
| Cross-section / CI scripts                 | `_automation/scripts/`                                          |
| Intake bot upload folder                   | `_automation/intake/` (PDFs land here in PRs)                   |
| GitHub workflows                           | `.github/workflows/` (root-level — see note above)              |
| Custom CSS                                 | `assets/css/custom.css` (root-level — see note above)           |
| Site-wide partials / shortcodes            | `layouts/_partials/`, `layouts/shortcodes/` (root-level)        |
| Section-specific layouts                   | `<section>/layouts/`                                            |

## Docs

- [**docs/UPDATING.md**](docs/UPDATING.md) — how to add papers, talks,
  software, etc. All edits can be done through github.com in a browser;
  no terminal required.
- [**docs/MAINTENANCE.md**](docs/MAINTENANCE.md) — older maintenance
  notes (kept for reference; the canonical guide is `UPDATING.md`).
- [**docs/WEBSITE_PRINCIPLES.md**](docs/WEBSITE_PRINCIPLES.md) — reusable
  playbook / architectural rules for building a similar academic site
  from scratch with an AI assistant.
- [**docs/SITE_AUDIT.md**](docs/SITE_AUDIT.md) — periodic content audits.

## Deploy

Push to `main`. GitHub Actions (`.github/workflows/deploy.yml`) builds
Hugo, builds the Pagefind search index, and publishes to GitHub Pages.
No manual build step needed for normal content updates.

## Local preview (optional)

```bash
brew install hugo
cd gking-site/hugo-site    # the repo root
hugo server                # http://localhost:1313/gking-site/
```

Production build:

```bash
hugo --gc --minify --baseURL "https://katalinatoth.github.io/gking-site/"
npx pagefind --site public
```

## Tracing history across renames

The 2026 section-driven reorg moved nearly every tracked file with
`git mv`, so blame and log are preserved — but you have to ask for it
explicitly:

```bash
git log --follow -- writings/content/<slug>/index.md
git blame --follow writings/content/<slug>/index.md
```

`--follow` makes git walk through the rename. Without it, `git log` will
only show the file's history *since the rename commit*.
