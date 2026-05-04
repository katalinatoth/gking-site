# people/

Source for the **People** section (`/research-group/`, `/people/`, `/authors/` URL spaces).

```
people/
├── content/
│   ├── group/               /research-group/ landing page
│   ├── profiles/            /people/<slug>/ - individual profiles (~350)
│   └── authors/             /authors/<slug>/ - taxonomy author pages
├── data/
│   └── research_group.json  current/alumni/affiliate roster used by the layouts
├── layouts/                 templates; mounted at layouts/research-group/, layouts/people/, layouts/authors/
└── scripts/                 Python tooling for syncing/scraping people
```

## How Hugo sees this

`hugo.yaml` declares:

- `people/content/group`    -> `content/research-group`
- `people/content/profiles` -> `content/people`
- `people/content/authors`  -> `content/authors`
- `people/layouts`          -> `layouts` (merged; the layouts/research-group, layouts/people,
                                          layouts/authors subfolders inside it are picked up)
- `people/data`             -> `data`

URLs and templates are unchanged.
