# gking-site

Source for <https://gking.harvard.edu/> — Gary King's
academic website, built with Hugo + Hugo Blox.

## Repository layout

Everything you can edit on the site lives under one top-level folder:
[`EditMe/`](EditMe/). Inside that folder there's one sub-folder per
item in the site's main navigation, plus an `EditMe/UI/` folder for
the visual / aesthetic bits (page templates, hover effects, CSS
overrides).

The few folders that live at the project root next to `EditMe/` are
there because Hugo, HugoBlox, or GitHub need to find them at a
hard-coded literal path (no Hugo mount can move them) — see
[`EditMe/UI/PINNED-AT-ROOT.md`](EditMe/UI/PINNED-AT-ROOT.md) for the
full list and explanation.

```
hugo-site/                  the gking-site git repo root
├── hugo.yaml               site config + module.mounts (the wiring)
├── go.mod, package.json    Hugo modules + Tailwind plumbing
│
├── EditMe/                 EVERY editable thing on the site
│   ├── UI/                 visual / aesthetic settings (CSS, layouts,
│   │                       per-section template overrides). Includes
│   │                       PINNED-AT-ROOT.md explaining what *can't*
│   │                       move into EditMe/.
│   ├── HomePage/           "/" landing page
│   ├── Bio/                /bio/
│   ├── Writings/           every paper, book, report, patent, court
│   │                       brief, and slide deck — organised by type,
│   │                       then research topic, then decade
│   │                       (Articles/CausalInference/2010s/<slug>/),
│   │                       and presentations clustered by talk title
│   │                       and venue (Presentations/<title>/<venue>/)
│   ├── ResearchAreas/      /research-areas/
│   ├── Software/           /software/  (one folder per package)
│   ├── Dataverse/          /dataverse/
│   ├── People/             /research-group/, /people/, /authors/
│   ├── Teaching/           /teaching/
│   ├── Blog/               /blog/
│   ├── Contact/            /contact/
│   ├── Misc/                standalone pages (apply, recs, advice, …)
│   └── Redirects/           legacy URL aliases (one YAML file)
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
├── _automation/            intake bots, all Python helpers
│                           (_automation/scripts/), _automation/intake/
│                           PDF uploads.
├── docs/                   repo docs (UPDATING.md, MAINTENANCE.md,
│                           WEBSITE_PRINCIPLES.md, REPO_LAYOUT.md,
│                           audits/).
│
└── .github/, .githooks/    CI workflows + auto-push hook. STAY at the
                            project root — GitHub Actions and git both
                            look for these by literal path and don't
                            follow Hugo mounts.
```

`module.mounts` in `hugo.yaml` re-maps every sub-folder of `EditMe/`
onto the Hugo paths the build expects, so URLs and the rendered site
are unchanged. The block is auto-generated; run
`python3 _automation/scripts/generate_mounts.py` after adding or
removing folders under `EditMe/`.

## Where do I find X?

| You want to edit / find …                  | Look here                                                       |
| ------------------------------------------ | --------------------------------------------------------------- |
| A specific paper                           | `EditMe/Writings/<Type>/<Topic>/<Decade>/<slug>/index.md` (e.g. `Articles/CausalInference/2010s/foo/`) |
| A specific talk / slide deck               | `EditMe/Writings/Presentations/<title-slug>/<venue-slug>/index.md` |
| A software tool's page                     | `EditMe/Software/<slug>/index.md`                               |
| Someone's research-group / alumni profile  | `EditMe/People/Profiles/<slug>/index.md`                        |
| Site bio                                   | `EditMe/Bio/index.md`                                           |
| Home page sections                         | `EditMe/HomePage/_index.md`                                     |
| The "Featured" carousel                    | `EditMe/Writings/Data/featured_publications.yaml`               |
| The Writings page tab routing              | `EditMe/Writings/Data/writings_legacy_map.json`                 |
| The dataverse list                         | `EditMe/Dataverse/Data/dataverse.json`                          |
| The research-group roster                  | `EditMe/People/Data/research_group.json`                        |
| The Research Areas grid                    | `EditMe/ResearchAreas/Data/research_areas.json`                 |
| Legacy URL redirects                       | `EditMe/Redirects/Data/redirects.yaml`                          |
| PDFs                                       | `_site/static/files/<slug>.pdf`                                 |
| Custom CSS / per-section layout overrides  | `EditMe/UI/` (see `EditMe/UI/README.md`)                        |
| All Python helpers (intake, audits, sync)  | `_automation/scripts/`                                          |
| Intake bot upload folder                   | `_automation/intake/` (PDFs land here in PRs)                   |
| GitHub workflows                           | `.github/workflows/` (root-level — see note above)              |
| Site-wide partials / shortcodes            | `layouts/_partials/`, `layouts/shortcodes/` (root-level)        |
| GaryAI chatbot page                       | `EditMe/Misc/ask-gary/index.md` + `layouts/chatbot/single.html`|
| GaryAI popup widget                       | `_site/static/js/gking-chat-widget.js`                         |
| Google Analytics                          | `layouts/_partials/hooks/head-start/google-analytics.html`      |

If you can't find what you're looking for in the table, browse
`EditMe/<Section>/README.md` — every menu-item folder has its own
README that maps the editable bits inside it.

## Docs

- [**docs/REPO_LAYOUT.md**](docs/REPO_LAYOUT.md) — plain-language tour of
  every top-level folder and what it's for. Start here if folder names like
  `_site/`, `_automation/`, `.githooks/`, or `assets/` are confusing.
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
hugo server                # http://localhost:1313/
```

Production build:

```bash
hugo --gc --minify --baseURL "https://gking.harvard.edu/"
npx pagefind --site public
```

## Tracing history across renames

The 2026 EditMe/ reorg (and the section-driven reorg before it) moved
nearly every tracked file with `git mv`, so blame and log are
preserved — but you have to ask for it explicitly:

```bash
git log --follow -- EditMe/Writings/Articles/CausalInference/2010s/<slug>/index.md
git blame --follow EditMe/Writings/Articles/CausalInference/2010s/<slug>/index.md
```

`--follow` makes git walk through the rename. Without it, `git log` will
only show the file's history *since the rename commit*. If you don't
know exactly where a paper landed in the new tree, you can also point
`--follow` at the original path (e.g. `writings/content/<slug>/index.md`)
and git will trace it forward.
