# AGENTS.md

Conventions for AI agents editing this repo. Both Gary King and Katalina Toth use AI assistants here and both push directly to `main`, so these rules also keep us from stepping on each other.

If anything below conflicts with the README or with `EditMe/UI/PINNED-AT-ROOT.md`, defer to those — they're the source of truth for layout. This file is about *workflow*.

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

**Why:** Two collaborators on the same `main` means the local clone goes
stale fast. Editing on top of stale state causes merge conflicts at push
time or, worse, silently overwrites the other person's work.

### Rule 2: `git pull` again right before pushing
If more than ~15 minutes have passed since the last fetch, refetch before
any push. Surface any new commits on `origin/main`, merge them in, and
rebuild locally before pushing.

**Why:** The other person may have pushed during your session.

### Rule 3: Build locally before pushing
Run `hugo` from the repo root and confirm no errors. If you've changed
front-matter `url:` or `aliases:` fields, also run
`python3 _automation/scripts/build_redirects.py`. Anything beyond that
(pagefind, first-commit dates) CI will handle.

**Why:** No PR review means the local build is the only pre-push safety
net. CI catches the rest, but a broken push wastes a deploy slot for
everyone.

### Rule 4: Show the diff and confirm before pushing OR committing
Never `git push` (or, if the auto-push hook is enabled, `git commit`)
without first showing the user:
  (a) the files and lines being changed,
  (b) the commit messages,
  (c) the result of the local build,
and asking "OK to push?" Wait for explicit yes.

**Why:** Every push is a live deploy. The user must see exactly what is
about to hit the public site. **Note:** `.githooks/post-commit` is an
auto-push hook that may be enabled via
`_automation/scripts/enable-auto-push.sh`. If it's active, *commit* is
effectively the same as *push* — same review rules apply.

### Rule 5: Small atomic commits with descriptive messages
One logical change per commit. Messages explain *why*, not just *what*.

  Good: "Fix dead link to NSF grant page on bio (URL changed last month)."
  Bad:  "fix link"

**Why:** Direct-to-main makes commits the only paper trail and the only
undo unit. Reverting a clean atomic commit is one command; untangling a
mixed-purpose commit takes much longer.

### Rule 6: Never force-push to `main`
No `git push --force`, no `--force-with-lease`, no rewriting `main`'s
history.

**Why:** Force-push silently erases any commits the other collaborator
landed since your last fetch. There is no undo.

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

- `content/` — Hugo regenerates this from `EditMe/` via `module.mounts`.
  Edits here are clobbered on the next build.
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

**Why:** Each of these is generated, infrastructural, or fragile. Edits
get reverted by the build, break tooling, or quietly change behavior in
non-obvious ways.

---

## Site-specific quirks

### URLs and aliases
Many pages have `url:` or `aliases:` set in front matter. These exist to
preserve the original URL structure after the EditMe reorganization.
**Don't change them without consulting `_automation/scripts/build_redirects.py`.**

**Why:** External links — Gary's CV, citations on other academic sites,
search-engine indexes — point at the original URLs. Silent URL changes
become 404s for the rest of the world.

### Presentation clustering
- Driven by `_automation/scripts/regroup_presentations_fuzzy.py`.
- Always run with `--dry-run` first and review
  `EditMe/Writings/Data/presentation_clustering_report.md` before
  applying.
- The script supports manual exclusions via `--exclude-pair "A|B"` (one-off)
  or `--excludes-file <path>`. If a persistent excludes file becomes
  necessary, save it under `EditMe/Writings/Data/`.

**Why:** Clustering moves real folders around. An incorrect cluster
applied to a live push files real content under the wrong heading and
breaks URLs.

---

## Session conduct (rules for the agent, not the human)

- If a build fails or the site looks wrong, **stop and surface the
  failure**. Do not silently retry-and-fix; tell the user what failed.
- Periodically summarize what's been changed locally but not yet
  committed/pushed, so the user can see drift.
- For any operation that can't be undone (force-push, history rewrite,
  bulk delete, schema change, mass `git mv`), pause and confirm explicitly
  even if the user previously said "go ahead" for an unrelated step.
