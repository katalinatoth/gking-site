# What's in this repository?

A plain-language tour of every folder and file you'll see at the top level of
[`iqss-research/gking-site`](https://github.com/iqss-research/gking-site) on
GitHub. No background knowledge needed.

## The big picture

The website at <https://gking.harvard.edu/> is built from this repository. A
robot reads everything in here, does some assembly, and turns it into a fully
functional website.

The folders fall into four groups:

1. **`EditMe/`** — the one place to look for anything you might want to
   change. Has one sub-folder per item in the site's main menu, plus a
   `UI/` folder for the visual / aesthetic settings (CSS, page templates,
   per-section layout overrides). If you can edit it on the website, it
   lives somewhere inside `EditMe/`.
2. **Underscore folders** (`_site/`, `_automation/`, `_vendor/`) — supporting
   pieces that aren't part of the website's content but make the build
   work. The leading underscore is a hint to "skip this when you're looking
   for content."
3. **Hidden folders** (names that start with a dot, like `.github/`) — used by
   GitHub itself or by helper tools. You usually never need to touch these.
4. **Configuration files at the very top** — small files that tell the
   website-builder robot how to assemble everything.

There's also a small handful of folders (`assets/`, `layouts/`, `themes/`)
that have to live at the top level next to `EditMe/` because the
website-builder robot looks for them by literal name. They're listed
under "Folders pinned at the root" below, and explained more fully in
[`EditMe/UI/PINNED-AT-ROOT.md`](../EditMe/UI/PINNED-AT-ROOT.md).

---

## 1. `EditMe/` — everything you can change about the site

There is exactly **one sub-folder for each item in the site's top menu**,
plus an extra folder (`UI/`) for visual settings. To change anything about
a page, look here first. Each folder has its own `README.md` with a more
detailed cheat sheet for that section.

### `EditMe/UI/`
All the aesthetic / visual bits in one place: per-section page-template
overrides (`PerSectionLayouts/`), CSS overrides via the project root
(see `EditMe/UI/PINNED-AT-ROOT.md`), and config snippets for the global
menu and visual parameters (`Config/`).

### `EditMe/HomePage/`
The website's home page (the very first page you see at
<https://gking.harvard.edu/>).

### `EditMe/Bio/`
Gary's bio, CV, and photo. Lives at <https://gking.harvard.edu/bio/>.

### `EditMe/Writings/`
Every paper, book, report, patent, court brief, slide deck, and
software-paper Gary has published — about 300 in total. Organised by
type, then research topic, then decade, so you can drop a new paper
into the right slot without scrolling through hundreds of folders:

- `Articles/<Topic>/<Decade>/<slug>/` — journal articles and working
  papers (e.g. `Articles/CausalInference/2010s/foo/`).
- `Books/<Decade>/<slug>/` — books.
- `Reports/<Decade>/<slug>/` — technical reports and similar.
- `Patents/<Decade>/<slug>/` — patents.
- `CourtBriefs/<Decade>/<slug>/` — amicus / court-brief filings.
- `SoftwareNotes/<Decade>/<slug>/` — papers describing a software
  package (the actual `/software/` pages live under `EditMe/Software/`).
- `Presentations/<title-slug>/<venue-slug>/` — slide decks. Same talk
  given at multiple venues clusters under one title-slug folder.
- `Data/` — small JSON / YAML files that drive the Writings page tabs,
  the Featured carousel, and so on.

URLs at `/publication/<slug>/` and `/talk/<slug>/` are unchanged from
the previous flat layout — Hugo's `module.mounts` block in `hugo.yaml`
remaps the deep tree onto the URL space.

### `EditMe/ResearchAreas/`
The "Research Areas" page that groups Gary's work by topic. Lives at
<https://gking.harvard.edu/research-areas/>. The list of areas and the
papers they include live in `EditMe/ResearchAreas/Data/research_areas.json`.

### `EditMe/Software/`
The "Software" page and pages for each software package (Amelia, EI,
Clarify, etc.). Lives at <https://gking.harvard.edu/software/>.

### `EditMe/Dataverse/`
The "Dataverse" page (the data-sharing service). Lives at
<https://gking.harvard.edu/dataverse/>.

### `EditMe/People/`
The People area in the menu. Includes three sub-categories:

- `EditMe/People/ResearchGroup/` — Gary's current and former research-group members.
- `EditMe/People/Profiles/` — short profile cards for ~350 collaborators.
- `EditMe/People/Authors/` — the credit listing on each paper page.

The roster itself lives at `EditMe/People/Data/research_group.json`.

### `EditMe/Teaching/`
The "Teaching" page and individual class pages. Lives at
<https://gking.harvard.edu/teaching/>.

### `EditMe/Blog/`
The blog. Lives at <https://gking.harvard.edu/blog/>. Reachable via direct
URL even though it isn't in the top menu.

### `EditMe/Contact/`
The "Contact" page. Lives at <https://gking.harvard.edu/contact/>.

### `EditMe/Misc/`
A handful of standalone pages that don't fit into any of the menu sections —
things like the accessibility statement, the "advice to grad students" page,
the "miscellanea" page, recommendation-letter info, etc. They each have their
own URL but you'd never find them by clicking the menu.

### `EditMe/Redirects/`
A list of "shortcuts" — short URLs like `/amelia/` or `/zoom/` that
automatically forward visitors to the right page. The actual list is one
file: `EditMe/Redirects/Data/redirects.yaml`. Edit that file to add or
remove a shortcut. The deploy step regenerates the matching content
stubs into `EditMe/Redirects/content/` (auto-generated, gitignored).

---

## 2. Underscore folders (supporting plumbing)

These aren't part of the content. They're behind-the-scenes pieces. The
leading underscore is a convention that says "skip this when you're looking
for content."

### `_site/`
Cross-section plumbing for the website-builder robot:
- `_site/data/` — site-wide data files used by multiple sections.
- `_site/static/` — the giant collection of PDF papers, supplementary
  materials, and historical images that get served as-is. Anything in
  `_site/static/files/` becomes available at `/files/...` on the live
  site.
- `_site/archetypes/` — templates for what a "new paper" or "new talk"
  should look like when one gets created.
- `_site/i18n/` — text strings for translations (currently English only;
  reserved for future use).

### `_automation/`
The robots and helper scripts that automate maintenance:
- `_automation/scripts/` — every Python helper in the repo lives here,
  organised by topic:
  - `_automation/scripts/writings/` — paper-intake bot, DOI fillers,
    citation audits, link repair, etc.
  - `_automation/scripts/people/` — profile scrapers and research-group
    sync.
  - top-level scripts (`build_redirects.py`, `generate_mounts.py`,
    `apply_pr_edits.py`, ...) — anything that runs across multiple
    sections.
- `_automation/intake/` — a drop folder used by the "upload a new paper"
  GitHub flow. When someone submits a paper through the form, the PDF
  lands here briefly and an automation moves it into
  `EditMe/Writings/Articles/Unsorted/`.

### `_vendor/`
Pinned copies of external dependencies (the website's theme, in particular).
Auto-managed; you never edit this by hand. It exists so that a deploy doesn't
break if an upstream theme changes unexpectedly.

---

## 3. Folders pinned at the root (Hugo / theme conventions)

A handful of folders can't be moved into `EditMe/` because the
website-builder robot expects them in fixed locations. The full list and
the reason for each is in
[`EditMe/UI/PINNED-AT-ROOT.md`](../EditMe/UI/PINNED-AT-ROOT.md). The most
visible ones:

### `assets/`
CSS and small media files that get processed (minified, fingerprinted) before
being included in the final pages. The most important file is
`assets/css/custom.css` — site-wide style overrides.

### `layouts/`
The site's shared page templates: the overall page skeleton (`baseof.html`),
the default list/single-page templates (`_default/`), reusable building blocks
like the navigation bar and footer (`_partials/`), and small reusable
ingredients you can drop into a page (`shortcodes/`). Per-section layout
overrides live under `EditMe/UI/PerSectionLayouts/`; only the shared ones
live here.

### `themes/`
Empty in this repository — themes are pulled in via the configuration file
(`hugo.yaml`) and cached in `_vendor/`. The folder exists because the
website-builder robot looks for it; it usually has nothing in it.

---

## 4. Hidden folders (start with a dot)

These are configured by GitHub or by command-line tools. Usually you can
ignore them.

### `.github/`
Files that configure GitHub itself:
- `.github/workflows/` — the half-dozen robots that run automatically
  (deploy the site, link-check, accept paper uploads via Issues, strip
  intake artefacts from `main`, etc.).
- `.github/ISSUE_TEMPLATE/` — the forms people see when they click "New
  Issue" on GitHub (e.g., the "Upload a paper" form).

### `.githooks/`
Small scripts that run on _your_ computer when you do a git operation.
There's currently one: a "post-commit" hook that automatically pushes
commits up to GitHub so you don't have to remember the second step. Only
runs locally; doesn't affect anyone else.

### `.gitattributes`
A short list telling git how to handle particular file types (e.g., binary
files like PDFs). Set-and-forget.

### `.gitignore`
A list of files git is told to ignore — local cruft, build output,
auto-generated files. So that those don't accidentally get checked in.

---

## 5. Configuration files at the top level

These are short files that the website-builder robot needs to find at the
very top of the repository.

### `README.md`
The first thing visitors see when they land on the GitHub page. A welcome
mat that explains the layout and points at the docs.

### `hugo.yaml`
The main configuration file. Tells the website-builder which sections exist,
what their URLs should be, what the menu should look like, and which folders
to assemble together when building. The big "remap" block (`module.mounts`)
that lets the `EditMe/` layout work without changing any URLs is
auto-generated by `_automation/scripts/generate_mounts.py` — re-run that
script after adding or removing folders under `EditMe/`.

### `go.mod`, `go.sum`
A pair of files that lock down which version of the website's theme to use.
Auto-managed; you only touch them if you intentionally update the theme.

### `package.json`, `package-lock.json`
A pair of files that lock down which version of the styling tools (Tailwind
CSS, etc.) to use. Auto-managed.

### `hugo_stats.json`
A list of CSS class names the website builder found in your pages. Used by
the styling tools to know which styles to actually ship. Auto-regenerated on
each build.

---

## "I want to change X — where do I look?"

| Want to change | Look in |
|---|---|
| The home page | `EditMe/HomePage/_index.md` |
| Gary's bio | `EditMe/Bio/index.md` |
| A specific paper | `EditMe/Writings/<Type>/<Topic>/<Decade>/<slug>/index.md` (e.g. `Articles/CausalInference/2010s/foo/`) |
| A specific talk | `EditMe/Writings/Presentations/<title-slug>/<venue-slug>/index.md` |
| The featured-papers list on the home page | `EditMe/Writings/Data/featured_publications.yaml` |
| The Writings page tab routing | `EditMe/Writings/Data/writings_legacy_map.json` |
| A software package's page | `EditMe/Software/<software-slug>/index.md` |
| A research-group member's bio | `EditMe/People/ResearchGroup/<their-slug>/_index.md` |
| The list of research-group members | `EditMe/People/Data/research_group.json` |
| The Research Areas grid | `EditMe/ResearchAreas/Data/research_areas.json` |
| Add a new short URL like `/foo/` | `EditMe/Redirects/Data/redirects.yaml` |
| The site's navigation menu | `hugo.yaml` (look for `menus:`) |
| Site-wide colors or fonts | `assets/css/custom.css` |
| The "upload a paper" form | `.github/ISSUE_TEMPLATE/upload-paper.yml` |
| What runs when something gets pushed to `main` | `.github/workflows/deploy.yml` |

---

## What you'll never see in this list

- `public/` — the finished website that the robot produces. It's regenerated
  fresh on every deploy and isn't checked in.
- `resources/`, `node_modules/` — tooling caches, regenerated as needed.
- Local-only files like `.DS_Store`, `.Rhistory`, `.venv-fix/` — they exist
  on your laptop but git is told to ignore them.

---

If something in this doc gets out of date, the source of truth is the actual
folder layout — run `ls -la` at the top of the repo to see what's really
there. The READMEs inside each folder also have more detail (every folder
under `EditMe/` has one).
