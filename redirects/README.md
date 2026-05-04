# redirects/

Legacy URL aliasing. The Drupal site that preceded this Hugo site had a large
table of short URLs (`/cem`, `/words`, etc.) that 302'd to canonical pages.
We preserve those URLs by:

1. Editing `redirects/data/redirects.yaml` (the source of truth).
2. Running [`_automation/scripts/build_redirects.py`](../_automation/scripts/build_redirects.py),
   which regenerates the per-redirect Hugo content stubs under `redirects/content/`
   and the Netlify-style flat file at `_site/static/_redirects`.

```
redirects/
├── content/                 generated meta-refresh stub pages, one per redirect
│                            (committed; rebuilt by build_redirects.py)
└── data/
    └── redirects.yaml       hand-maintained table; the source of truth
```

## How Hugo sees this

- `redirects/content` -> `content/_redirects`
- `redirects/data`    -> `data`

The leading underscore in `_redirects` is intentional: it groups the auto-generated
pages out of the way under the published site's root.
