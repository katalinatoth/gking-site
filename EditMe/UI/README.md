# EditMe/UI/

Visual / aesthetic things.

## What's in here

```
UI/
├── PerSectionLayouts/      page templates that override the default for
│                           a single menu section
│
├── Config/                 pointers to bits of hugo.yaml that affect
│                           appearance (menus, color params, etc.)
│
├── PINNED-AT-ROOT.md       list of UI things that have to live at the
│                           top of the repo (assets/, layouts/) because
│                           the theme expects them there
│
└── README.md               this file
```

## What's NOT in here (and why)

A few visual bits live at the top of the repository, not inside `UI/`:

- `assets/css/custom.css` — site-wide CSS overrides. Lives at the repo root.
- `layouts/baseof.html`, `layouts/_default/`, `layouts/_partials/`,
  `layouts/shortcodes/`, `layouts/page/` — the shared page skeleton and
  reusable HTML pieces. Live at the repo root.

The website-builder calls things like `fileExists "assets/css/custom.css"`
and `os.ReadDir "layouts/_partials/hooks/body-end/"` literally, so those
files have to live at the literal paths it expects. See
[`PINNED-AT-ROOT.md`](PINNED-AT-ROOT.md) for the full list.
