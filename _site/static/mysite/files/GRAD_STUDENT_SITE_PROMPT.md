# Build My Graduate Student Academic Website

## Who I Am

[Fill in the following fields. Leave blank any that don't apply to you.]

- **Name:**
- **Department and program** (e.g., "PhD Candidate, Department of Government, Harvard University"): 
- **Year in program** (e.g., "fourth-year PhD candidate"): 
- **Advisor(s):** 
- **Committee members** (if formed):
- **Institutional affiliations** (centers, institutes, labs — e.g., "affiliate of the Institute for Quantitative Social Science"): 
- **Email:** 
- **Photo** (attach file or URL — a professional headshot or department photo):

- **One-line tagline** (the single sentence under your name — e.g., "I study the political economy of conflict, post-conflict reconstruction, and migration"): 
- **Homepage bio** (2–4 paragraphs covering: what you study, your methods, your background before the PhD, and any notable achievements — written in first or third person, your choice):


- **Research interests** (list 3–6 keywords or short phrases, e.g., "causal inference," "political communication," "time series methods"):
- **Pre-PhD education** (degrees, institutions, years — e.g., "B.S. in Computer Science, Columbia University, 2020"):
- **Pre-PhD work experience** (if relevant — industry, research positions, government, etc.):
- **Job market paper** (if applicable):
  - Title:
  - Abstract (1 paragraph):
  - PDF (attach or link):
  - Status (e.g., "under review at AJPS," "working paper"):

- **Working papers** (for each, provide: title, coauthors, one-sentence description or abstract, PDF link if available, status):

- **Published papers** (for each: title, coauthors, journal/venue, year, DOI or link):

- **Software / tools / packages** (if any — name, one-sentence description, link to repo or docs):

- **Datasets or data projects** (if any — name, description, link):

- **Teaching experience** (for each: course name, role [TA/TF/Instructor], institution, term):

- **Fellowships, grants, and awards** (list with year — e.g., "NSF Graduate Research Fellowship, 2023"):


- **Presentations and talks** (for each: title, venue/conference, date — only include if you want a dedicated section): 
- **Blog posts or analytical writing** (if any — title, date, link or attach):
- **News / recent updates** (if you want a news feed — list recent items with dates, e.g., "Paper accepted at JCR, Aug 2025"):

- **Other sections you want** (personal interests, photography, media appearances, consulting, YouTube channel, etc. — describe what you'd like): 

- **CV** (attach PDF): 

- **Social links** (any you want displayed — GitHub, Twitter/X, Google Scholar, LinkedIn, ORCID, personal blog):

> **Note on voice:** Write your bio however feels natural to you. First person ("I study...") is the norm for grad students and reads as direct and confident. Third person ("Jane studies...") is fine too, especially if you're on the job market. Either way, keep it factual and credit-sharing — name your advisors, coauthors, and funding sources.

---

## What I Want

Build me a complete, deployment-ready personal academic website using Hugo, deployed via GitHub Pages with GitHub Actions. The site should be ready to push to a `username.github.io` repo and go live immediately.

The result should be clean, minimal, professional, mobile-friendly, and easy to maintain by editing Markdown files on GitHub. It should look like the personal website of a serious graduate student — not a corporate landing page, not a flashy portfolio, not a bare-bones default template.

---

## Architecture Requirements

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Static site generator | **Hugo** (extended) | Fast builds, single binary, great for academic sites, no Node runtime needed for content. |
| Theme | **Minimal custom layouts** (no heavy theme framework) | Grad student sites are simple enough to not need Hugo Blox's full machinery. Lighter = easier to understand and maintain. |
| CSS | Single `assets/css/style.css` processed by Hugo Pipes | One file, no build tools, easy to customize. |
| Hosting | **GitHub Pages** user site (`username.github.io`) | Free, versioned, standard for grad students. |
| CI | GitHub Actions | Build Hugo → deploy pages artifact. |

### Directory Structure

```
site/
├── assets/
│   └── css/
│       └── style.css              # all styles
├── content/
│   ├── _index.md                  # homepage (all main content lives here)
│   ├── research/
│   │   └── _index.md              # research page (if separate from homepage)
│   ├── blog/                      # optional blog posts
│   │   ├── _index.md
│   │   └── post-slug/
│   │       └── index.md
│   └── cv/
│       └── _index.md              # CV page (or just link to PDF)
├── layouts/
│   ├── _default/
│   │   ├── baseof.html            # site shell
│   │   ├── single.html            # generic single page
│   │   └── list.html              # generic list page
│   ├── index.html                 # homepage layout
│   ├── blog/
│   │   ├── list.html              # blog index
│   │   └── single.html            # blog post
│   └── partials/
│       ├── head.html              # <head> with meta, CSS, favicon
│       ├── nav.html               # top navigation
│       └── footer.html            # site footer
├── static/
│   ├── files/                     # PDFs (CV, papers)
│   ├── images/                    # photos, project images
│   └── favicon.ico                # custom favicon
├── hugo.yaml                      # site configuration
├── .github/workflows/deploy.yml   # CI/CD
├── UPDATING.md                    # how to add/edit content
└── README.md                      # repo overview
```

### hugo.yaml Essentials

```yaml
baseURL: "https://USERNAME.github.io/"
title: "Full Name"
languageCode: en-us

params:
  description: "PhD Candidate, Department, University"
  author: "Full Name"
  email: "email@university.edu"

menu:
  main:
    - name: Research
      url: "/#research"
      weight: 10
    - name: Teaching
      url: "/#teaching"
      weight: 20
    - name: CV
      url: "/files/cv.pdf"
      weight: 30
    - name: Contact
      url: "/#contact"
      weight: 40

markup:
  goldmark:
    renderer:
      unsafe: true
```

Menu items link to sections on the homepage (anchor links) or to files. This keeps the single-page feel while maintaining navigability. Add a "Blog" or "News" menu item only if the student has that content.

---

## Content Model

### Homepage (`content/_index.md`)

The homepage is the heart of the site. It contains all primary content in sections, rendered by `layouts/index.html`. The front matter is minimal; the body is structured Markdown with heading-delimited sections that the layout renders as distinct visual blocks.

```yaml
---
title: "Full Name"
---
```

The layout template reads from `hugo.yaml` params and renders sections for: hero/bio, research, publications, teaching, awards, news, and contact. Content for each section is either in the `_index.md` body or pulled from front matter / data files as appropriate.

### Publications and Working Papers

These are listed directly in the homepage content or in a `data/papers.yaml` file for cleaner templating:

```yaml
# data/papers.yaml
- title: "Paper Title Here"
  authors: ["First Last", "First Last"]
  year: 2025
  status: "working paper"  # or: "published", "under review", "revise and resubmit"
  venue: ""  # journal name if published
  pdf: "files/paper-slug.pdf"  # local PDF path
  link: ""  # external link (DOI, publisher, SSRN)
  abstract: "One paragraph abstract."
  job_market_paper: false  # set true for THE job market paper
  tags: ["causal inference", "text analysis"]
```

**Status vocabulary:**
| Value | Meaning |
|-------|---------|
| `published` | Appeared in a peer-reviewed venue |
| `accepted` | Accepted, not yet in print |
| `revise and resubmit` | R&R at a journal |
| `under review` | Submitted and under review |
| `working paper` | Complete draft, circulating |
| `work in progress` | Early-stage, not yet circulating |

### Teaching

Listed in `data/teaching.yaml`:

```yaml
- course: "GOV 50: Data"
  role: "Teaching Fellow"
  institution: "Harvard University"
  term: "Fall 2024"
  instructor: "Prof. Name"  # optional
```

### Software / Projects

Listed in `data/projects.yaml` (if any):

```yaml
- name: "ProjectName"
  description: "One-sentence description of what it does."
  url: "https://github.com/username/project"
  language: "R"  # or Python, etc.
```

### Blog Posts

Each blog post is a content directory: `content/blog/post-slug/index.md`

```yaml
---
title: "Post Title"
date: 2025-03-15
description: "One-sentence summary."
tags: ["methodology", "tutorial"]
---
```

---

## Homepage Layout

The homepage is a single scrolling page with clearly delineated sections. This matches how nearly all grad student sites in the examples are structured.

### Section order (top to bottom):

1. **Hero / About** — Photo, name, title, department, university, 1-2 sentence research tagline, social links, CV button
2. **Bio** — 2-4 paragraphs of fuller description (research interests, methods, background)
3. **Research** — Job market paper highlighted at top (if applicable), then working papers, then publications. Each item: title (linked to PDF), coauthors, status badge, one-line description or venue.
4. **Software / Projects** — Only if they have them. Name, one-line description, link.
5. **Teaching** — Simple list: course name, role, term.
6. **Awards & Fellowships** — Compact list with years.
7. **News / Updates** — Optional. Reverse-chronological feed of recent items (talks given, papers accepted, awards received). Show 5-8 most recent.
8. **Blog** — Optional. Links to 3-5 most recent posts with dates, with "View all" link if more exist.
9. **Contact** — Email, office address if desired, social links repeated.

### Hero section layout rules

- **Photo on the LEFT**, text (name, title, department, tagline, buttons) on the **RIGHT** — on desktop (>768px).
- On mobile, stack vertically: photo centered on top, text below.
- Photo: circular crop, ~160-200px diameter.
- Below the name/title block: a row of small icon links (GitHub, Twitter, Google Scholar, email) and a "CV (PDF)" button.

### Research section layout rules

- **Job market paper** (if designated) gets a highlighted card: title in bold, full abstract shown, prominent PDF link, status badge. Visually distinct from other papers (subtle background, border, or left-accent bar).
- **Other papers** listed as compact rows: authors, year, "Title" (linked), status in parentheses. No abstracts shown inline (keep it scannable); link to PDF is the title itself.
- Group by status: "Working Papers" subheading, then "Publications" subheading. Only show subheadings that have content.

---

## Design Principles

### Clean over dense

Grad student sites have little content. The design challenge is making 3 papers and 2 teaching roles look intentional and professional, not empty. Use generous whitespace, clear typography, and confident simplicity. Do NOT try to fill space with decorative elements.

### One page does the work

A visitor (faculty on a hiring committee, fellow student, conference attendee) should get the full picture without clicking away from the homepage. The only reasons to navigate away: reading a full blog post, downloading a PDF, or visiting an external link.

### Mobile-first

Grad students share their site URL on Twitter, in email signatures, and on conference name tags. More than half of visits will be on phones. Every element must work on a 375px-wide screen.

### Stable URLs

`username.github.io` is the URL that goes on your CV, your email signature, your conference papers. It must not break. Use the user-site pattern (`username.github.io`) not the project-site pattern, so there's no `/repo/` subpath complexity.

### Maintainable by the owner

A grad student should be able to add a new paper by editing `data/papers.yaml` and uploading a PDF to `static/files/` — directly on GitHub in the browser if they want. No build tools to install locally. No complex template logic to understand.

### No dead ends

Every page (including blog posts) has navigation back to the homepage. The 404 page includes navigation. External links open in new tabs.

### Understated tone

State facts. Don't editorialize accomplishments. "NSF Graduate Research Fellowship, 2023" — not "prestigious NSF fellowship." Let the nouns carry their own weight. Name advisors and coauthors. The site signals seriousness through its clarity and completeness, not through self-promotion.

### Accessibility

- Semantic HTML (`<nav>`, `<main>`, `<article>`, `<section>`, proper heading hierarchy)
- All images have meaningful `alt` text
- Sufficient color contrast (WCAG AA)
- Keyboard navigable
- `prefers-reduced-motion` respected
- Skip-to-content link

### Performance

- HTML meaningful at first paint — no JS required for content
- Images lazy-loaded below the fold
- No external fonts (use system font stack) — fast and respects OS settings
- Total page weight under 500KB excluding PDFs
- No JavaScript frameworks

---

## CSS / Styling

### Philosophy

The site should feel like a clean, well-typeset document — not a "website." Think: the visual clarity of a well-formatted academic CV, translated to a screen. Warm, professional, quietly confident.

### Color palette

```css
:root {
  --color-bg: #fdfbf8;           /* warm off-white background */
  --color-surface: #f5f0eb;      /* slightly warmer for cards/highlights */
  --color-text: #2d2926;         /* warm charcoal for body text */
  --color-text-muted: #6b6560;   /* warm gray for metadata, dates */
  --color-accent: #5c7a8a;       /* desaturated slate blue — links, highlights */
  --color-accent-hover: #3d5a6a; /* darker on hover */
  --color-border: #e2ddd5;       /* warm border tone */
  --color-highlight: #f0ebe3;    /* job market paper highlight bg */
}
```

Adjust `--color-accent` to coordinate with the student's institution if desired (e.g., a desaturated Harvard crimson, a muted Stanford cardinal). The accent should feel like a monogram, not a paint job.

### Typography

- System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- Body: 1rem / 1.6 line-height
- Name (h1): 2rem, bold, `--color-text`
- Section headings (h2): 1.4rem, semibold, with a subtle bottom border
- Paper titles: 1rem, medium weight, `--color-accent` (they're links)
- Metadata (year, status, role): 0.875rem, `--color-text-muted`

### Key style rules

1. **Max content width:** 720px, centered. Academic text reads best in a narrow column.
2. **Section spacing:** `4rem` between major sections, `1.5rem` between items within a section.
3. **Links:** `--color-accent`, no underline by default, underline on hover. Visited links same color (academic sites are reference material, not reading-once content).
4. **Status badges:** Small inline labels (`font-size: 0.75rem`, uppercase, letter-spaced) next to paper titles — e.g., `UNDER REVIEW`, `R&R`, `WORKING PAPER`. Use `--color-text-muted` with a subtle background.
5. **Job market paper card:** `--color-highlight` background, `1px` left border in `--color-accent`, `1.5rem` padding.
6. **Hero photo:** `border-radius: 50%`, `width: 160px`, `height: 160px`, `object-fit: cover`.
7. **Footer:** Minimal — name, year, "Built with Hugo" (optional). Same `--color-text-muted`. **Always** include, in small print at the bottom right of the homepage, a credit line: `Created using <a href="https://garyking.org/mysite">GaryKing.org/mysite</a>`.
8. **Nav:** Sticky top, `--color-bg` background, subtle bottom border. Name on left, links on right. On mobile: hamburger menu or a simple horizontal scroll.
9. **No dark mode.** Force light always. Grad student sites are viewed in professional contexts (committee meetings, browser tabs alongside papers). Consistency matters more than preference.
10. **Favicon:** Student's initials on a square of `--color-accent`. E.g., "NK" for Nakamura Kentaro — white bold text centered on a filled square.

---

## GitHub Actions Deployment

`.github/workflows/deploy.yml`:

```yaml
name: Deploy Hugo site to Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.147.0
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb
          sudo dpkg -i ${{ runner.temp }}/hugo.deb

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Build with Hugo
        env:
          HUGO_ENVIRONMENT: production
          TZ: America/New_York
        run: hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"

      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Deliverables Checklist

Produce ALL of the following:

1. **`hugo.yaml`** — complete config with params, menus, markup settings
2. **`assets/css/style.css`** — complete stylesheet implementing the design spec above (palette, typography, layout, hero, nav, sections, status badges, job market card, responsive breakpoints, accessibility)
3. **`layouts/index.html`** — homepage layout rendering all sections (hero, bio, research, teaching, awards, news, blog teasers, contact)
4. **`layouts/_default/baseof.html`** — site shell (html, head, body, skip link, nav, main, footer)
5. **`layouts/_default/single.html`** — generic page template
6. **`layouts/_default/list.html`** — generic list template
7. **`layouts/blog/single.html`** — blog post template (if blog content exists)
8. **`layouts/blog/list.html`** — blog index template (if blog content exists)
9. **`layouts/partials/head.html`** — `<head>` with meta tags, open graph, CSS link, favicon
10. **`layouts/partials/nav.html`** — sticky navigation (name left, links right, mobile hamburger)
11. **`layouts/partials/footer.html`** — minimal footer
12. **`content/_index.md`** — homepage content with bio text
13. **`data/papers.yaml`** — all publications and working papers
14. **`data/teaching.yaml`** — teaching history
15. **`data/projects.yaml`** — software/projects (if any)
16. **`static/files/cv.pdf`** — the student's CV (from attached file)
17. **`static/files/`** — all paper PDFs
18. **`static/images/photo.jpg`** — the student's headshot
19. **Custom favicon** — initials on accent-colored square (favicon.ico, favicon-32x32.png, apple-touch-icon.png) in `static/`
20. **`.github/workflows/deploy.yml`** — the Actions workflow above
21. **`UPDATING.md`** — plain-language guide for the student: how to add a paper, update bio, add a blog post, change their photo. Written for someone who edits files on GitHub in the browser.
22. **Blog content** (if provided) — each post as `content/blog/slug/index.md`

**The site must build cleanly with `hugo --gc --minify` and deploy correctly to GitHub Pages on first push.**

---

## Things That Go Wrong (So Avoid Them)

- [ ] **Empty-feeling sites.** If the student only has 2 papers and 1 TA role, the site must still look intentional. Use whitespace confidently; don't add filler sections. Hide section headings for sections with no content.
- [ ] **Broken links to PDFs.** All `href` values for local files must use Hugo's `relURL` or be relative paths. Test that `/files/cv.pdf` actually resolves.
- [ ] **Photo not displaying.** Ensure the image path in the template matches where the file actually lives in `static/`.
- [ ] **"Under construction" energy.** Never leave placeholder text visible. If a section has no content, omit it entirely — don't show an empty heading.
- [ ] **Over-engineering.** Do not add search, filtering, JavaScript interactivity, or any feature that a site with <20 content items doesn't need. Complexity is a maintenance burden for a busy grad student.
- [ ] **Treating working papers like published papers.** Always show status clearly. Never imply something is published when it's a working paper. But also don't be apologetic about working papers — they're the norm for students.
- [ ] **Forgetting the CV link.** The CV PDF must be downloadable from the nav bar — this is the single most important action item for any visitor.
- [ ] **Institutional brand overkill.** A subtle accent colour is fine. Don't plaster the university logo everywhere or make the site look like a department page.
- [ ] **Ignoring mobile.** Test at 375px width. The hero section, nav, and paper list must all work on a phone screen.

---

## UPDATING.md Content Guide

The `UPDATING.md` file should explain (in plain language, with examples) how to:

1. **Add a new paper:** Edit `data/papers.yaml`, add a new entry with the fields, upload PDF to `static/files/`, push to main.
2. **Update your bio:** Edit `content/_index.md` or the relevant param in `hugo.yaml`.
3. **Add a teaching entry:** Edit `data/teaching.yaml`.
4. **Add a blog post:** Create `content/blog/your-slug/index.md` with the front matter template.
5. **Update your CV:** Replace `static/files/cv.pdf` with the new version (keep the same filename).
6. **Change your photo:** Replace `static/images/photo.jpg`.
7. **Add a news item:** Edit the news section in `content/_index.md` or `data/news.yaml`.
8. **Mark a paper as published:** Change its `status` field in `data/papers.yaml` from `"working paper"` to `"published"` and add the `venue` field.
9. **Add your job market paper:** Set `job_market_paper: true` on the relevant entry in `data/papers.yaml`.

All changes auto-deploy within ~2 minutes of pushing to main.

---

## Reproducing This Architecture — Quickstart

For a new grad student site, follow this order:

1. Create the repo: `username.github.io` (GitHub user site)
2. `hugo new site . --force` in the repo root
3. Add `hugo.yaml` with the student's info, menu, and params
4. Create `layouts/` with the templates above
5. Create `assets/css/style.css` with the full stylesheet
6. Add `data/papers.yaml`, `data/teaching.yaml`, `data/projects.yaml` from the student's materials
7. Write `content/_index.md` with the bio
8. Place PDFs in `static/files/`, photo in `static/images/`
9. Generate the favicon (initials on accent square)
10. Add `.github/workflows/deploy.yml`
11. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
12. Push to main. Site is live.
13. Write `UPDATING.md` and hand the student the repo URL.
