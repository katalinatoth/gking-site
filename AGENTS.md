# AGENTS.md

Conventions for AI agents editing this repo. Both Gary King and Katalina
Toth use AI assistants here and both push directly to `main`, so these
rules also keep us from stepping on each other.

If anything below conflicts with the README or with
`EditMe/UI/PINNED-AT-ROOT.md`, defer to those — they're the source of
truth for layout. This file is about *workflow*. The README is the
comprehensive human-facing guide with detailed procedures, templates,
and prompts.

---

## Project context

- This repo builds Gary King's academic website (gking.harvard.edu) using
  Hugo + HugoBlox. Hugo version is pinned to `0.160.1` in
  `.github/workflows/deploy.yml`; local builds should match.
- All editable content lives under `EditMe/`. Anything outside `EditMe/`
  is build infrastructure, generated output, theme code, or configuration —
  see `EditMe/UI/PINNED-AT-ROOT.md` for the full list of pinned-at-root
  files and why they can't move.
- **Pushing to `main` triggers a live deploy** via
  `.github/workflows/deploy.yml`. There is no staging environment.
- Build failures in CI block the deploy (the previous live site stays up),
  but they also block every subsequent push from deploying until fixed.

---

## Git workflow: direct-to-main with frequent syncs

We don't use feature branches or pull requests. Every push goes straight
to `main` and triggers a live deploy. Because Gary and Katalina both work
this way, the rules below are stricter than they'd be on a single-author
repo.

### Rule 1: `git pull` at the start of every session
Run `git fetch origin && git status` first. If local is behind
`origin/main`, merge before making any edits.

### Rule 2: `git pull` again right before pushing
If more than ~15 minutes have passed since the last fetch, refetch before
any push. Surface any new commits on `origin/main`, merge them in, and
rebuild locally before pushing.

### Rule 3: Build locally before pushing
Run `hugo` from the repo root and confirm no errors. If you've changed
front-matter `url:` or `aliases:` fields, also run
`python3 _automation/scripts/build_redirects.py`. Anything beyond that
(pagefind, first-commit dates) CI will handle.

### Rule 4: Show the diff and confirm before pushing OR committing
Never `git push` (or, if the auto-push hook is enabled, `git commit`)
without first showing the user:
  (a) the files and lines being changed,
  (b) the commit messages,
  (c) the result of the local build,
and asking "OK to push?" Wait for explicit yes.

**Note:** `.githooks/post-commit` is an auto-push hook that may be
enabled via `_automation/scripts/enable-auto-push.sh`. If it's active,
*commit* is effectively the same as *push* — same review rules apply.

### Rule 5: Small atomic commits with descriptive messages
One logical change per commit. Messages explain *why*, not just *what*.

  Good: "Fix dead link to NSF grant page on bio (URL changed last month)."
  Bad:  "fix link"

### Rule 6: Never force-push to `main`
No `git push --force`, no `--force-with-lease`, no rewriting `main`'s
history.

---

## Where editable content lives

All editable content is under `EditMe/`:

- `EditMe/UI/` — site-wide aesthetic (CSS, per-section layouts, navigation).
  See `EditMe/UI/PINNED-AT-ROOT.md` for what *can't* move here.
- `EditMe/HomePage/` — the "/" landing page
- `EditMe/Bio/` — `/bio/`
- `EditMe/Writings/` — every paper, book, report, patent, court brief,
  and slide deck:
    - `Articles/<topic>/<decade>/<slug>/` — scholarly articles
    - `Books/`, `Reports/`, `SoftwareNotes/`, `CourtBriefs/`, `Patents/`
    - `Presentations/<title-slug>/<venue-slug>/` — talks, one folder per
      title with subfolders per venue
    - `Data/` — YAML/JSON inputs for the auto-clustering and audit scripts
    - `_SectionPages/` — `_index.md` files for the `/publication/` and
      `/talk/` section list pages (controls page titles)
- `EditMe/Startups/` — `/startups/` section. One folder per startup
  (Crimson Hexagon, Thresher, Learning Catalytics, OpenScholar,
  Perusall, QuickCode). Display order is controlled by `weight` in front
  matter. Startups with stories have full HTML content in `abstract`;
  those without just have `external_site` links. Layout overrides are at
  `EditMe/UI/PerSectionLayouts/Startups/`. The homepage shows truncated
  excerpts with "Read more" links to `/startups/#<slug>`.
- `EditMe/ResearchAreas/` — `/research-areas/`
- `EditMe/Software/` — `/software/`, one folder per package
- `EditMe/Dataverse/` — `/dataverse/`
- `EditMe/Teaching/` — teaching pages
- `EditMe/People/` — collaborators, students, etc.
- `EditMe/Blog/`, `EditMe/Contact/`, `EditMe/Misc/`, `EditMe/Redirects/`

**Why this layout:** the EditMe/ folder is a deliberate UX choice — one
obvious place where non-technical editors (and AI agents) can find content.
Edits scattered outside `EditMe/` break that contract.

---

## What NOT to edit (or: edit only with care)

- `public/` — Hugo build output. Never committed, never edited by hand.
- `assets/`, `layouts/`, `themes/`, `_vendor/`, `hugo_stats.json`,
  `go.mod`, `go.sum`, `package.json`, `package-lock.json` — pinned at
  the repo root for tooling reasons (see `EditMe/UI/PINNED-AT-ROOT.md`).
  Edit only when intentionally changing theme, build, or dependency
  behavior.
- `hugo.yaml`'s `module.mounts:` block — auto-generated. Run
  `_automation/scripts/generate_mounts.py` to regenerate; don't hand-edit.
- `.github/workflows/*.yml` — the live deploy and intake automations.
  Touch only when intentionally changing CI behavior, and surface the
  change clearly.
- `.git/`, `node_modules/`, `resources/`, `_site/static/files/` — internals
  and auto-managed caches.

---

## Site-specific quirks

### URLs and aliases
Many pages have `url:` or `aliases:` set in front matter. These exist to
preserve the original URL structure after the EditMe reorganization.
**Don't change them without consulting `_automation/scripts/build_redirects.py`.**

### Presentation clustering
- Driven by `_automation/scripts/regroup_presentations_fuzzy.py`.
- Always run with `--dry-run` first and review
  `EditMe/Writings/Data/presentation_clustering_report.md` before
  applying.

### GaryAI chatbot
The site has a native AI chatbot ("GaryAI") with two surfaces:

- **Popup widget** — a floating chat bubble on every page, powered by
  `_site/static/js/gking-chat-widget.js`. The script tag and
  `data-*` configuration attributes are in `layouts/baseof.html`.
- **Dedicated page** — `/ask-gary/`, content at
  `EditMe/Misc/ask-gary/index.md`, layout at
  `layouts/chatbot/single.html`. Uses a custom `type: chatbot` layout
  that renders a full-page chat UI with inline HTML/CSS/JS.

The backend API endpoints (AWS Lambda) are hardcoded in the widget JS
and the chatbot layout. Don't change them unless the AWS deployment
changes.

### Startups section
- Content: `EditMe/Startups/<slug>/index.md` — `weight` controls order,
  `abstract` holds full HTML story content, `external_site` provides
  the "Visit site" link.
- Layout: `EditMe/UI/PerSectionLayouts/Startups/list.html` (expandable
  dropdowns) and `single.html` (redirects to list with hash anchor).
- Homepage integration: truncated excerpts in
  `EditMe/UI/PerSectionLayouts/HomePage/landing/list.html` with
  "Read more" links.
- Config: mount, menu item (weight 45), and permalink in `hugo.yaml`.

### Google Analytics
Tracking is loaded via
`layouts/_partials/hooks/head-start/google-analytics.html` (tag
`G-NDZT9P326S`). The hook fires on every page because HugoBlox's
`site_head.html` scans the `hooks/head-start/` directory automatically.

---

## Publication types

The primary button label on each page changes based on
`publication_types` (handled in `layouts/_partials/page_links.html`).
Use exactly one of these strings:

**Primary (recommended):**

```
journal_article    → button: "Article"
book               → button: "Article"
book_chapter       → button: "Book Chapter"
working_paper      → button: "Article"
conference_paper   → button: "Article"
report             → button: "Article"
data               → button: "Article"
software           → button: "Article"
court_brief        → button: "Brief"
patent             → button: "Patent"
presentation       → button: "Presentation"
poster             → button: "Poster"
letter             → button: "Letter"
other              → button: "Article"
```

**Also recognised (legacy / Drupal):**

```
conference_proceedings, miscellaneous, newspaper_article,
unpublished, web_article, website
```

**Important:** The Writings tab placement for `/publication/` entries is
driven by `EditMe/Writings/Data/writings_legacy_map.json`, which takes
precedence over front-matter `publication_types` for tab routing.

---

## Session conduct (rules for the agent, not the human)

- If a build fails or the site looks wrong, **stop and surface the
  failure**. Do not silently retry-and-fix; tell the user what failed.
- Periodically summarize what's been changed locally but not yet
  committed/pushed, so the user can see drift.
- For any operation that can't be undone (force-push, history rewrite,
  bulk delete, schema change, mass `git mv`), pause and confirm explicitly
  even if the user previously said "go ahead" for an unrelated step.
