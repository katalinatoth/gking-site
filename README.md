# gking-site

Source for <https://katalinatoth.github.io/gking-site/> — Gary King's
academic website, built with Hugo + Hugo Blox.

## Docs

- [**UPDATING.md**](UPDATING.md) — how to add papers, talks, software, etc.
  All edits can be done through github.com in a browser; no terminal
  required.
- [**MAINTENANCE.md**](MAINTENANCE.md) — older maintenance notes (kept for
  reference; the canonical guide is `UPDATING.md`).
- [**WEBSITE_PRINCIPLES.md**](WEBSITE_PRINCIPLES.md) — reusable
  playbook / architectural rules for building a similar academic site
  from scratch with an AI assistant.

## Deploy

Push to `main`. GitHub Actions (`.github/workflows/deploy.yml`) builds
Hugo, builds the Pagefind search index, and publishes to GitHub Pages.
No manual build step needed for normal content updates.

## Local preview (optional)

```bash
brew install hugo
cd gking-site     # the root of your `git clone`
hugo server       # http://localhost:1313/gking-site/
```

Production build:

```bash
hugo --gc --minify --baseURL "https://katalinatoth.github.io/gking-site/"
npx pagefind --site public
```
