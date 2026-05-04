# teaching/

Source for the **Teaching** section (`/teaching/` URL space).

```
teaching/
├── content/                 one folder per course/workshop + _index.md
└── layouts/                 templates; mounted at layouts/teaching/ and layouts/teaching-class/
    ├── teaching/{list,single}.html
    └── teaching-class/single.html
```

## How Hugo sees this

- `teaching/content` -> `content/teaching`
- `teaching/layouts` -> `layouts` (merged; the teaching/ and teaching-class/ subfolders
                                   inside it land at layouts/teaching/ and layouts/teaching-class/)
