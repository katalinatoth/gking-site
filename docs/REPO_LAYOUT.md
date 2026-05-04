# What's in this repository?

A plain-language tour of every folder and file you'll see at the top level of
[`iqss-research/gking-site`](https://github.com/iqss-research/gking-site) on
GitHub. No background knowledge needed.

## The big picture

The website at <https://gking.harvard.edu/> is built from this repository. A
robot reads everything in here, does some assembly, and turns it into a fully
functional website.

The folders fall into four groups:

1. **Website-section folders** — one per section in the site's top menu (Bio,
   Writings, Software, etc.). Anything you'd want to edit about that section
   lives in its folder.
2. **Underscore folders** (`_site/`, `_automation/`, `_vendor/`) — supporting
   pieces that aren't a section of the website themselves but make the site
   work. The leading underscore is a hint to "skip this when you're looking
   for content."
3. **Hidden folders** (names that start with a dot, like `.github/`) — used by
   GitHub itself or by helper tools. You usually never need to touch these.
4. **Configuration files at the very top** — small files that tell the
   website-builder robot how to assemble everything.

---

## 1. Website-section folders (the ones you'll edit most)

Each of these matches one entry in the website's top menu. To change anything
about a section, look here first. Every section folder typically contains:

- `content/` — the actual words and pictures of the section's pages.
- `layouts/` — instructions for how those pages should look.
- `data/` — supporting lists (e.g., a list of co-authors, a list of software
  packages).
- `scripts/` — small helper programs specific to that section.
- `README.md` — a short note explaining how that section is organized.

Not every section has all five of those — some are simple and only need
`content/`.

### `bio/`
Gary's bio, CV, and photo. Lives at <https://gking.harvard.edu/bio/>.

### `writings/`
The "Writings" page and every individual paper page (~298 papers). The biggest
folder in the repo by file count. Lives at
<https://gking.harvard.edu/publication/>.

### `software/`
The "Software" page and pages for each software package (Amelia, EI, Clarify,
etc.). Lives at <https://gking.harvard.edu/software/>.

### `dataverse/`
The "Dataverse" page (the data-sharing service). Lives at
<https://gking.harvard.edu/dataverse/>.

### `people/`
The "People" page in the menu. Includes three sub-categories:
- `people/content/group/` — Gary's current and former research-group members.
- `people/content/profiles/` — short profile cards for ~350 collaborators.
- `people/content/authors/` — the credit listing on each paper page.

### `teaching/`
The "Teaching" page and individual class pages. Lives at
<https://gking.harvard.edu/teaching/>.

### `talks/`
The "Talks" listing — each entry typically points to a video or slides.
URLs use the path `/talk/...`.

### `blog/`
The blog. Lives at <https://gking.harvard.edu/blog/>.

### `research-areas/`
The "Research Areas" page that groups Gary's work by topic. Lives at
<https://gking.harvard.edu/research-areas/>.

### `contact/`
The "Contact" page. Lives at <https://gking.harvard.edu/contact/>.

### `home/`
The website's home page (the very first page you see at
<https://gking.harvard.edu/>). Kept separate from `pages/` because it's the
landing page, not a regular content page.

### `pages/`
A handful of standalone pages that don't fit into any of the menu sections —
things like the accessibility statement, the "advice to grad students" page,
the "miscellanea" page, recommendation-letter info, etc. They each have their
own URL but you'd never find them by clicking the menu.

### `redirects/`
A list of "shortcuts" — short URLs like `/amelia/` or `/zoom/` that
automatically forward visitors to the right page. The actual list is one
file: `redirects/data/redirects.yaml`. Edit that file to add or remove a
shortcut.

---

## 2. Underscore folders (supporting plumbing)

These aren't sections of the website you'd ever browse to. They're behind-
the-scenes pieces. The leading underscore is a convention that says "skip
this when you're looking for content."

### `_site/`
Cross-section plumbing for the website-builder robot:
- `_site/data/` — site-wide data files used by multiple sections.
- `_site/static/` — the giant collection of PDF papers, supplementary
  materials, and historical images that get served as-is. Anything in
  `static/files/` becomes available at `/files/...` on the live site.
- `_site/archetypes/` — templates for what a "new paper" or "new talk"
  should look like when one gets created.
- `_site/i18n/` — text strings for translations (currently English only;
  reserved for future use).

### `_automation/`
The robots and helper scripts that automate maintenance:
- `_automation/scripts/` — Python helpers that run during deploys (rebuild
  redirect stubs, compute publication dates, etc.) or that maintainers run
  by hand.
- `_automation/intake/` — a drop folder used by the "upload a new paper"
  GitHub-Issue workflow. When someone submits a paper through the form, the
  PDF lands here briefly and an automation moves it into `writings/`.

### `_vendor/`
Pinned copies of external dependencies (the website's theme, in particular).
Auto-managed; you never edit this by hand. It exists so that a deploy doesn't
break if an upstream theme changes unexpectedly.

---

## 3. Folders that have to live at the top level (Hugo / theme conventions)

A handful of folders can't be moved into the section layout because the
website-builder robot expects them in fixed locations:

### `assets/`
CSS and small media files that get processed (minified, fingerprinted) before
being included in the final pages. The most important file is
`assets/css/custom.css` — site-wide style overrides.

### `layouts/`
The site's shared page templates: the overall page skeleton (`baseof.html`),
the default list/single-page templates (`_default/`), reusable building blocks
like the navigation bar and footer (`_partials/`), and small reusable
ingredients you can drop into a page (`shortcodes/`). Section-specific
layouts live inside each section folder; only the shared ones live here.

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
- `.github/workflows/` — the seven robots that run automatically (deploy the
  site, link-check, accept paper uploads via Issues, etc.).
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
to assemble together when building. The "remap" instructions that let the
section-driven layout work all live in this file.

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
| The home page | `home/content/_index.md` |
| Gary's bio | `bio/content/index.md` |
| A specific paper | `writings/content/<paper-slug>/index.md` |
| The featured-papers list on the home page | `writings/data/featured_publications.yaml` |
| A software package's page | `software/content/<software-slug>/index.md` |
| A research-group member's bio | `people/content/group/<their-slug>/_index.md` |
| The list of research-group members | `people/data/research_group.json` |
| Add a new short URL like `/foo/` | `redirects/data/redirects.yaml` |
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
there. The READMEs inside each folder also have more detail.
