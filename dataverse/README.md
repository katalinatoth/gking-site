# dataverse/

Source for the **Dataverse** section (`/dataverse/` URL space).

```
dataverse/
├── content/                 single index.md
├── data/
│   └── dataverse.json
└── layouts/                 templates; mounted at layouts/dataverse/
    └── single.html
```

## How Hugo sees this

- `dataverse/content` -> `content/dataverse`
- `dataverse/layouts` -> `layouts/dataverse`
- `dataverse/data`    -> `data`
