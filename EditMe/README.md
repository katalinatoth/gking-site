# EditMe/

Everything you can edit on the website lives somewhere inside this folder.
There's one sub-folder per item in the site's top menu, plus a `UI/` folder
for things like colors, fonts, and page layout.

## Plain-language map

| Folder | What's inside |
|---|---|
| [`UI/`](UI/) | All the visual / aesthetic bits (page templates, hover effects, color overrides). See `UI/README.md`. |
| [`HomePage/`](HomePage/) | The very first page you see at <https://gking.harvard.edu/>. |
| [`Bio/`](Bio/) | Bio & C.V. page. |
| [`Writings/`](Writings/) | Every paper, book, report, patent, court brief, and presentation. Organized by type, then topic, then decade. |
| [`ResearchAreas/`](ResearchAreas/) | The "Research Areas" section. |
| [`Software/`](Software/) | One folder per software package. |
| [`Dataverse/`](Dataverse/) | The Dataverse landing page. |
| [`People/`](People/) | Research group, collaborator profiles, paper-credit listings. |
| [`Teaching/`](Teaching/) | Teaching landing page + individual classes. |
| [`Blog/`](Blog/) | Blog posts (not in the top menu but reachable via direct URL). |
| [`Contact/`](Contact/) | Contact page. |
| [`Misc/`](Misc/) | Standalone pages that don't fit any menu item (advice, accessibility, recs, …). |
| [`Redirects/`](Redirects/) | Short URLs and legacy aliases (one YAML file). |

## Things that aren't in this folder (and why)

A few things have to live at the top of the repository instead of inside
`EditMe/`, because GitHub or the website-builder finds them by exact path
and doesn't look anywhere else. The full list with explanations is in
[`UI/PINNED-AT-ROOT.md`](UI/PINNED-AT-ROOT.md).

The short version:

- `assets/`, `layouts/` (shared theme bits) — pinned at repo root.
- `.github/`, `.githooks/` — pinned at repo root.
- `hugo.yaml`, `go.mod`, `package.json`, etc. — pinned at repo root.
- `_site/` (cross-section plumbing like the PDF pile) — pinned at repo root.
- `_automation/` (intake bots and helper scripts) — pinned at repo root.
- `docs/`, `README.md` — repo-level documentation.

## How the website-builder sees this folder

The Hugo website-builder requires content in folders called `content/`,
`layouts/`, `data/`, etc. The `module.mounts` block in
[`../hugo.yaml`](../hugo.yaml) re-maps every folder under `EditMe/` to
those required paths at build time. URLs on the live site are unchanged.

When you add or remove a folder under `EditMe/`, run

```bash
python3 _automation/scripts/generate_mounts.py
```

to regenerate the `module.mounts` block. CI also runs this check.
