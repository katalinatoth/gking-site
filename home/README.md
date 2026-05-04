# home/

Source for the site **home page** (`/`).

```
home/
├── content/
│   └── _index.md            type: landing - drives the landing template
└── layouts/
    └── landing/list.html    the landing page template
```

## How Hugo sees this

- `home/content` -> `content` (mounts the home `_index.md` at the content root)
- `home/layouts` -> `layouts` (so `landing/` lands at `layouts/landing/`)
