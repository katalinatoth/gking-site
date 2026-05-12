# Things pinned at the repository root

A handful of files and folders can't live inside `EditMe/`. They have to
sit at the very top of the repository because GitHub, the website-builder,
or the styling tools find them by exact path and won't look anywhere else.

This is not a design choice — it's a constraint imposed by the underlying
tools. We've documented exactly which paths fall into this category and
why, so that "how do I find X?" has a clear answer for each one.

## The full list

### `assets/`

Site-wide CSS and small media files that get processed (minified,
fingerprinted) before being included in the final pages.

The most important file is `assets/css/custom.css` — site-wide style
overrides (colors, spacing, hover effects on the navigation, etc.).

**Why pinned:** the HugoBlox theme calls
`fileExists "assets/css/custom.css"` from `_partials/site_head.html`.
That's a literal filesystem check that doesn't follow Hugo's mount
rewrites. If `custom.css` doesn't exist at exactly `assets/css/custom.css`
on disk, the theme silently drops the `<link>` tag for it and the site
loses its custom styling.

**To edit colors, fonts, hover effects:** edit `../../assets/css/custom.css`.

### `layouts/`

The shared page skeleton and reusable building blocks:

- `layouts/baseof.html` — the overall page wrapper (HTML doctype, `<head>`,
  `<body>`).
- `layouts/_default/` — default templates for list pages and individual
  pages.
- `layouts/_partials/` — reusable HTML pieces (navigation bar, footer,
  paper-card markup, etc.).
- `layouts/shortcodes/` — small reusable ingredients you can drop into a
  page (figures, buttons, etc.).
- `layouts/page/` — additional page templates.
- `layouts/alias.html` — used for redirects.

Section-specific layouts (e.g., the layout for paper pages, the layout for
software pages) live inside `EditMe/UI/PerSectionLayouts/<Section>/` and
do go through Hugo's mount rewrites — only the *shared* bits are pinned.

**Why pinned:** the HugoBlox theme calls
`os.ReadDir "layouts/_partials/hooks/body-end/"` from
`_partials/functions/get_hook.html`. That's a literal directory listing
that doesn't follow mount rewrites. If `_partials/` isn't at exactly
`layouts/_partials/` on disk, the theme misses several hook scripts and
the rendered HTML loses functionality (theme switching, search hooks,
etc.).

**To edit the page skeleton, navigation bar, footer:** edit files under
`../../layouts/`.

### `.github/`

Used by GitHub itself, not by the website-builder:

- `.github/workflows/` — the six robots that run automatically (deploy
  the site, link-check, accept paper uploads via Issues, etc.).
- `.github/ISSUE_TEMPLATE/` — the forms people see when they click "New
  Issue" on GitHub (e.g., the "Upload a paper" form).

**Why pinned:** GitHub looks for these by literal path. There's no way
to redirect them.

### `.githooks/`

Small scripts that run on your *local* computer when you do a git
operation. Currently one: a "post-commit" hook that auto-pushes commits
up to GitHub.

**Why pinned:** git looks for hooks at `.git/hooks/` by default; we
override that via `git config core.hooksPath .githooks` so the hook
script lives in the repo. The override path is configured in `.git/config`
and points at the literal path `.githooks/`.

### `hugo.yaml`, `go.mod`, `go.sum`, `package.json`, `package-lock.json`

Configuration for the website-builder, the dependency manager, and the
styling tools.

**Why pinned:** these are the entry-point files for their respective
tools. Hugo opens `hugo.yaml` from whatever directory you run `hugo`
in. Go opens `go.mod` from the project root. npm opens `package.json`
from the project root. Moving them breaks the tooling.

### `themes/`, `_vendor/`, `hugo_stats.json`

Auto-managed caches; you never edit these by hand.

### `_site/`

Cross-section plumbing that doesn't belong to any one menu section:

- `_site/static/` — the giant pile of PDFs and historical static files.
  Lives at this path because some hardcoded URLs reference paths inside
  it (e.g., `/files/foo.pdf`), and changing the path would require
  updating those references.
- `_site/data/` — site-wide data files used across multiple sections.
- `_site/archetypes/` — templates for new content.
- `_site/i18n/` — translation strings (currently English only).

**Why pinned (sort of):** technically these could move into `EditMe/`
via mounts, but they're not really "editable content" — they're plumbing.
Keeping them clearly separate from `EditMe/` reduces confusion.

### `_automation/`

The robots and helper scripts that automate maintenance.

**Why pinned (sort of):** like `_site/`, technically movable but not
content. Pinning at the root keeps `EditMe/` purely about content.

### `README.md`, `docs/`

Repo-level documentation. The `README.md` at the root is the first thing
visitors see on GitHub; `docs/` holds longer guides.

**Why pinned:** GitHub renders `README.md` automatically from the repo
root. `docs/` is a convention — it's where most projects put their
documentation.

---

## Quick reference

| To edit | Look here |
|---|---|
| Site-wide colors, fonts, hover effects | `../../assets/css/custom.css` |
| The page skeleton (header, footer, nav bar) | `../../layouts/_partials/` |
| Default page template | `../../layouts/_default/` |
| Per-section layout (only the parts that override) | `../PerSectionLayouts/<Section>/` |
| The site's main menu (which items appear at the top) | `../../hugo.yaml` (search for `menus:`) |
| The site's color theme params | `../../hugo.yaml` (search for `params:`) |
