# writings/

Source for the **Writings** section of the site (`/publication/` URL space).
Books, journal articles, working papers, and book chapters all live here.

```
writings/
├── content/                 page bundles, one per item (~298 papers + ~125 talks live in talks/)
│   └── <slug>/
│       ├── index.md         front matter + abstract
│       ├── featured.png     thumbnail (page resource)
│       └── ...              PDFs, supplementary files
├── data/                    section-scoped data files, all merged into Hugo's site.Data
│   ├── featured_publications.yaml
│   ├── publication_doi_fill_report.json
│   ├── publication_first_commit.json
│   ├── publication_link_repair_report.json
│   └── writings_legacy_map.json
├── layouts/                 section templates; mounted at layouts/publication/
│   ├── list.html
│   └── single.html
└── scripts/                 Python tooling specific to writings
```

## How Hugo sees this

`hugo.yaml` declares:

- `writings/content` -> `content/publication`
- `writings/layouts` -> `layouts/publication`
- `writings/data`    -> `data` (merged with other section data folders)

So URLs like `/publication/<slug>/` and templates like `layouts/publication/single.html`
keep working unchanged.

## Adding a new paper

The standard intake flow is GitHub-issue-driven; see [`_automation/intake/`](../_automation/intake/)
and the workflows at [`.github/workflows/intake-*.yml`](../.github/workflows/).
Manual additions: drop a folder under `writings/content/<slug>/` with an `index.md`.
