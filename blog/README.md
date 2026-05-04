# blog/

Source for the **Blog** section (`/blog/` URL space).

```
blog/
├── content/                 one folder per post + _index.md
└── layouts/                 templates; mounted at layouts/blog/
    └── list.html
```

## How Hugo sees this

- `blog/content` -> `content/blog`
- `blog/layouts` -> `layouts/blog`
