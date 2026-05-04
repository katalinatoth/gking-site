# talks/

Source for the **Talks** section (`/talk/` URL space — Hugo singular by convention).

```
talks/
├── content/                 one folder per talk (~125 entries)
└── layouts/                 templates; mounted at layouts/talk/
    ├── list.html
    └── single.html
```

## How Hugo sees this

- `talks/content` -> `content/talk`
- `talks/layouts` -> `layouts/talk`
