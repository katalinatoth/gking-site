# pages/

Standalone pages that aren't part of any nav section but still live on the site
(e.g. `/accessibility/`, `/apply/`, `/recs/`, `/aiwrite/`, `/commencement-speech/`,
`/pnas-edit/`, `/ssa/`, `/electronic-collection/`, `/advice/`, `/miscellanea/`,
`/papers/`).

```
pages/
└── content/
    ├── accessibility/index.md
    ├── apply/index.md
    ├── recs/index.md
    └── ... etc
```

## How Hugo sees this

- `pages/content` -> `content` (each subfolder becomes its own root-level URL)

A future content-cleanup pass may merge, redirect, or delete some of these.
This folder exists so they aren't scattered across the repo in the meantime.
