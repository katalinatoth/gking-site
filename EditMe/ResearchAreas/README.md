# EditMe/ResearchAreas/

The "Research Areas" landing page that groups Gary's work by topic.

Most of what's shown on the live page is generated automatically from
data files: the topic structure is in the data, and each topic block
on the page lists the papers tagged with that topic.

```
ResearchAreas/
├── _index.md       intro text shown above the list of research areas
└── Data/
    └── research_areas.json   the topic tree (10 top-level methods,
                              with sub-categories and the papers in each)
```

To add or rename a research area, edit `Data/research_areas.json`.
