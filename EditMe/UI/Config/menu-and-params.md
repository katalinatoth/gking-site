# Where to edit menus and visual parameters

These bits of the site live in [`../../../hugo.yaml`](../../../hugo.yaml)
and can't easily be split out into their own files. Use this doc as a
pointer to the right block to edit.

## Top-of-page menu items

Search `hugo.yaml` for `menus:`. The `main:` list under there controls
the order, names, and links of the items in the site's top navigation
bar.

```yaml
menus:
  main:
    - name: Bio & C.V.
      url: /bio/
      weight: 10
    - name: Writings
      url: /publication/
      weight: 20
    ...
```

`weight` controls ordering — lower numbers appear first. To reorder, edit
the weights. To add an item, add a new block. To remove, delete a block.

## Color, font, and feature parameters

Search `hugo.yaml` for `params:`. The block underneath includes:

```yaml
params:
  appearance:
    theme_day: custom        # which theme file to use during the day
    theme_night: custom      # which theme file to use at night
    color_mode: light        # default color mode
    font: native
    font_size: L             # site-wide font scale (S/M/L/XL)
  header:
    navbar:
      enable: true
      fixed: true            # whether the nav bar stays at top on scroll
      highlight_active_link: true
      show_search: true
  features:
    math:
      enable: false          # whether to render LaTeX math
    search:
      provider: flexsearch
```

The actual color values come from CSS files in `../../../assets/css/`.

## Permalinks (URL patterns)

Search `hugo.yaml` for `permalinks:`. Controls what URL each piece of
content gets:

```yaml
permalinks:
  publication: /publication/:slug/
  talk: /talk/:slug/
  software: /software/:slug/
```

Don't change these casually — every published paper would break its
URL.
