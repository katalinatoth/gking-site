# software/

Source for the **Software** section (`/software/` URL space).

```
software/
├── content/                 one folder per package (~32 entries) plus _index.md
├── data/                    section-scoped configuration
│   ├── software_fallback_urls.yaml
│   ├── software_legacy_overrides.yaml
│   ├── software_legacy_rows.yaml
│   ├── software_list_exclude.yaml
│   └── software_prefer_internal.yaml
└── layouts/                 templates; mounted at layouts/software/
    ├── list.html
    └── single.html
```

## How Hugo sees this

- `software/content` -> `content/software`
- `software/layouts` -> `layouts/software`
- `software/data`    -> `data`
