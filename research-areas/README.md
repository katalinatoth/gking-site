# research-areas/

Source for the **Research Areas** section (the homepage `#research-areas` block plus
the `/research-areas/` page).

```
research-areas/
├── content/                 single index.md
├── data/
│   └── research_areas.json  the canonical list, edited by hand and consumed by both
│                            the landing page and the research-areas single page
└── layouts/                 templates; mounted at layouts/research-areas/
    └── single.html
```

## How Hugo sees this

- `research-areas/content` -> `content/research-areas`
- `research-areas/layouts` -> `layouts/research-areas`
- `research-areas/data`    -> `data`
