# EditMe/UI/PerSectionLayouts/

Section-specific page templates. One sub-folder per menu section that
needs its own layout overrides.

```
PerSectionLayouts/
├── Bio/                    layout overrides for /bio/
├── Blog/                   layout overrides for /blog/
├── Contact/                layout overrides for /contact/
├── Dataverse/              layout overrides for /dataverse/
├── HomePage/               layout overrides for the homepage
├── People/                 layout overrides for /people/
├── ResearchAreas/          layout overrides for /research-areas/
├── ResearchGroup/          layout overrides for /research-group/
├── Software/               layout overrides for /software/
├── Talks/                  layout overrides for /talk/
├── Teaching/               layout overrides for /teaching/
├── TeachingClass/          layout overrides for individual class pages
└── Writings/               layout overrides for /publication/
```

If a section doesn't have its own layout overrides, it just falls back
to the shared default templates in [`../../../layouts/_default/`](../../../layouts/_default/).

## What's NOT here

The shared, site-wide layouts (`baseof.html`, `_default/`, `_partials/`,
`shortcodes/`, `page/`, `alias.html`) live at the repo root in
`../../../layouts/`. See [`../PINNED-AT-ROOT.md`](../PINNED-AT-ROOT.md)
for why.
