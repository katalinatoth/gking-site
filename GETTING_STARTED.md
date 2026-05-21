# Getting Started: Academic Website in 15 Minutes

This is a plain-English guide to setting up and managing an academic website
like [gking.harvard.edu](https://gking.harvard.edu). No prior web development
knowledge required.

---

## What We Use (and Why)

| Tool | What it is | Why we use it |
|------|-----------|---------------|
| **Hugo** | A program that turns plain text files into a website | Produces blazingly fast pages (no database, no server-side code), virtually no security risks, free to host |
| **Hugo Blox** | A pre-built academic theme for Hugo | Gives us publication pages, people profiles, a search bar, and responsive design out of the box |
| **Tailwind CSS** | A styling system | Makes the site look modern and consistent without writing custom design code |
| **Pagefind** | A search engine that runs entirely in the browser | No search server to maintain; works automatically on any hosting |
| **GitHub** | Where the site's files live (version-controlled) | Every change is tracked, reversible, and visible to collaborators |
| **GitHub Pages** | Free website hosting from GitHub | The site goes live automatically every time you save a change — no manual "deploy" step |
| **GitHub Actions** | Automatic build system | Rebuilds the site in ~3 minutes whenever a file changes on GitHub |
| **Claude** (in Cursor) | AI assistant | Handles all the technical complexity — you describe what you want in English, it makes the changes |

### Benefits of this approach

- **Speed**: Pages load in under a second. There's no database or server to slow things down.
- **Security**: Since the site is just static files (HTML, CSS, images), there's nothing to hack. No WordPress vulnerabilities, no plugin updates.
- **Zero maintenance**: No servers to patch, no software to update, no hosting bills.
- **AI-friendly**: The entire site is plain text files. Claude can read, understand, and modify any part of it. You never need to learn code.
- **Reversible**: Every change is versioned. If something breaks, any previous state can be restored instantly.

---

## Installation

### Option A: Start from scratch (new site)

1. **Get the tools** — Install [Cursor](https://cursor.com) (a code editor with Claude built in). That's the only thing you need on your computer. Claude handles everything else.

2. **Create the site** — Open Cursor and tell Claude:

   > "Create a new academic website for [Name], hosted at [username].github.io/[repo-name]. Here's their CV [attach PDF]. Set up Hugo with Hugo Blox, GitHub Pages deployment, and Pagefind search."

3. **Done** — Claude will scaffold the site, create the GitHub repository, and deploy it. You'll have a live URL in about 15 minutes.

### Option B: Bring over an existing site

If there's already a website (e.g., an old WordPress or Drupal site), tell Claude:

> "Migrate the site at [old-url] to this Hugo setup. Here's the CV [attach PDF]. Preserve all existing URLs so links don't break."

Claude will scrape the existing content, convert it to the new format, and deploy. The old URLs will still work via automatic redirects.

---

## How the Site Is Organized

Everything you'd ever want to edit lives in one folder: **`EditMe/`**. The subfolders map directly to sections of the website:

```
EditMe/
├── HomePage/          → The landing page
├── Bio/               → Biography section
├── Writings/          → All publications, books, talks
├── Software/          → Software projects
├── Teaching/          → Courses
├── People/            → Research group profiles
├── Startups/          → Companies/startups
├── ResearchAreas/     → Topic groupings on the homepage
├── Blog/              → Blog posts
├── Contact/           → Contact page
└── Redirects/         → URL forwarding rules
```

Each page is a simple text file (`index.md`) with a title, date, authors, and body text. You never need to touch anything outside `EditMe/`.

---

## How To: Common Tasks

For all of these, just open Cursor and describe what you want to Claude. Here are examples of the exact kind of instruction that works:

### Add a new publication

> "Add this paper to the site: [paste citation or attach PDF]. The authors are X, Y, Z. It was published in 2025 in [Journal Name]. Here's the PDF [attach file]."

Claude will create the page, extract the metadata, place the PDF, and generate a BibTeX citation — all in the correct location.

### Add a new section or tab to the navigation menu

> "Add a new section called 'Datasets' to the site navigation, between Software and Teaching."

### Edit existing content

> "On the page about [paper title], change the abstract to [new text]."

> "Update Gary's bio to mention his new appointment as [title]."

### Add a person to the research group

> "Add [Name] to the People section. They're a PhD student working on [topic]. Here's their photo [attach image]."

### Change the site's appearance

> "Make the navigation bar darker. Change the accent color to Harvard crimson."

### Add a blog post

> "Create a blog post titled '[Title]' with this content: [paste text]."

### Fix something that looks wrong

> "On the publications page, the buttons for [paper name] are missing. Can you fix that?"

---

## How It Works (the 30-second version)

1. You tell Claude what you want (in Cursor).
2. Claude edits the text files in `EditMe/`.
3. Claude pushes the change to GitHub.
4. GitHub Actions automatically rebuilds the site (~3 minutes).
5. The live site updates. Done.

You can also browse and edit files directly on GitHub.com (click any file → pencil icon → edit → commit). The site rebuilds the same way.

---

## Quick Reference

| I want to... | Tell Claude... |
|---|---|
| Add a paper | "Add this paper: [citation]. Here's the PDF." |
| Add a talk | "Add a talk titled [X] given at [venue] on [date]." |
| Edit a page | "On the [page name] page, change [X] to [Y]." |
| Add a redirect | "Make [old-url] redirect to [new-url]." |
| Check the live site | Visit your GitHub Pages URL |
| See recent changes | "Show me git log" or check GitHub's commit history |
| Undo a change | "Revert the last commit" |

---

## If Something Goes Wrong

- **Site won't load**: Check GitHub Actions (repository → Actions tab). If the latest run has a red X, tell Claude: "The build failed. Here's the error: [paste]."
- **Change didn't appear**: Wait 3 minutes for the rebuild. If still missing, ask Claude to check.
- **Want to undo**: Everything is versioned. Tell Claude "revert the last change" or "go back to how the site was yesterday."

---

## Further Reading (optional, for the curious)

- `README.md` — Full technical reference for the site's architecture
- `AGENTS.md` — Rules and conventions for AI assistants working on the site
- `WEBSITE_PRINCIPLES.md` — Design philosophy and reusable patterns for building academic sites
