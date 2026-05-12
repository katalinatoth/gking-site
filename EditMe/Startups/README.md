# EditMe/Startups/

The **Startups** section of the site (`/startups/`). Each startup is a
page bundle with an `index.md` and (optionally) a `featured.png` image.

## Current startups (ordered by `weight`)

| Folder | Weight | Has story content? |
|---|---|---|
| `crimson-hexagon/` | 1 | Yes — Twitter thread (HTML in `abstract`) |
| `thresher/` | 2 | Yes — Twitter thread (HTML in `abstract`) |
| `learning-catalytics/` | 3 | Yes — Harvard Gazette article (HTML in `abstract`) |
| `openscholar/` | 4 | No — external link only |
| `perusall/` | 5 | No — external link only |
| `quickcode/` | 6 | No — external link only |

## Key files

- `_index.md` — section index page (sets title, cascade options)
- `<slug>/index.md` — per-startup front matter and content
- `<slug>/featured.png` — image shown on the startups page

## Layout overrides

- `EditMe/UI/PerSectionLayouts/Startups/list.html` — expandable dropdown layout
- `EditMe/UI/PerSectionLayouts/Startups/single.html` — redirect to list page with anchor

## Front matter fields

```yaml
title: "Startup Name"
date: "2007-01-01"
weight: 1                    # display order (ascending)
summary: "Short subtitle"   # shown next to title in dropdown
external_site: "https://…"  # "Visit site" link
abstract: |-                 # full HTML story (optional)
  <p>Story content here.</p>
image:
  filename: featured.png
  caption: "Photo credit"
aliases:
  - /publication/old-slug/   # redirect from old URL
```

## Adding a new startup

1. Create `<slug>/index.md` with the front matter above.
2. Set `weight` to position it in the list.
3. Optionally add a `featured.png` image in the same folder.
4. The homepage excerpt in `EditMe/UI/PerSectionLayouts/HomePage/landing/list.html`
   must be added manually (startup dropdowns on the homepage are hand-coded HTML).
