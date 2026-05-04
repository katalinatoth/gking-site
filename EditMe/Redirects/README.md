# EditMe/Redirects/

Short URLs and legacy aliases. Editing is done in a single YAML file.

```
Redirects/
├── redirects.yaml          the source of truth: short URLs → real URLs
└── content/                generated meta-refresh stub pages
                            (auto-regenerated; do not edit by hand)
```

To add or remove a redirect, edit `redirects.yaml`. The YAML file has
inline comments showing the format. The `content/` folder is regenerated
automatically by the deploy workflow from `redirects.yaml`.

## Examples of what lives here

```yaml
- from: zoom
  to:   https://harvard.zoom.us/j/...
  note: "Gary's Zoom meeting room"

- from: amelia
  to:   /software/amelia-ii-a-program-for-missing-data/
  note: "shortcut to the Amelia software page"
```

When someone visits `https://gking.harvard.edu/zoom/`, they get
forwarded to the Zoom URL. When they visit `https://gking.harvard.edu/amelia/`,
they get forwarded to the software page.
