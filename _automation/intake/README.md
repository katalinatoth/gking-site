# intake/ — drop a PDF here to add a paper, talk, or book

> **Easier path:** if you're not in your terminal, use the
> [**Upload a paper** Issue Form][issue-form] instead. It's a
> one-screen GitHub form (PDF + short URL + supplementary materials)
> and the bot opens a draft PR for you with a figure picker built in.
> See [UPDATING.md → Quick add: Issue Form](../UPDATING.md#quick-add-issue-form)
> for the walk-through.

[issue-form]: https://github.com/iqss-research/gking-site/issues/new?template=upload-paper.yml

This folder is the **one-stop drop zone for content that comes as a
PDF** if you'd rather work from the terminal (or just prefer the
folder-based workflow). See
[UPDATING.md → Quick add](../UPDATING.md#quick-add) for the
click-by-click instructions for every content type (including the
ones that don't have a PDF, like software and patents).

## Where the PDF goes picks the type

| Drop the PDF here | The bot creates                                     | Used for                          |
|-------------------|------------------------------------------------------|-----------------------------------|
| `intake/`         | `EditMe/Writings/Articles/Unsorted/<slug>/index.md`  | journal articles, working papers (default) |
| `intake/talk/`    | `EditMe/Writings/Presentations/<slug>/index.md`      | conference / seminar slide decks  |
| `intake/book/`    | `EditMe/Writings/Articles/Unsorted/<slug>/index.md` (`type: book`) | books                  |

There is no PDF flow for software or patents — use the
[`scripts/quick_add.py`](../scripts/quick_add.py) helper or the
github.com "Add file → Create new file" path documented in UPDATING.md.

## TL;DR (paper, the default)

1. Click **Add file → Upload files** at the top of this folder on
   github.com.
2. Drag your PDF in.
3. Pick **"Create a new branch for this commit and start a pull
   request"**, then click **Propose changes** → **Create pull request**.
4. Wait ~1–2 minutes. A bot pushes a follow-up commit to the same PR
   with a generated `EditMe/Writings/Articles/Unsorted/<slug>/index.md`,
   the moved PDF (now under `_site/static/files/`), and an updated
   `EditMe/Writings/Data/writings_legacy_map.json`. It also posts a
   summary comment.
5. Skim the PR diff. Edit any field in the **Files changed** tab if the
   auto-populate got something wrong (title, authors, year, abstract,
   citation line, etc.) — or comment with slash commands like
   `/title …`, `/authors …`, `/year …`, `/abstract …`, `/doi …`,
   `/type journal_article`.
6. Click **Merge pull request**. The deploy workflow runs, and the new
   paper is live in another ~3 minutes.

## TL;DR (talk slides)

Same workflow, but on step 1 navigate into the `talk/` subfolder before
clicking **Add file → Upload files**, OR rename the dropped file to
`talk/your-slides.pdf` in the github.com upload dialog before
committing. The bot will:

- write `EditMe/Writings/Presentations/<slug>/index.md` (not `Articles/`)
- set `publication_types: ["presentation"]` and route the Writings page
  tab to **Presentations**
- skip Crossref (slide decks are virtually never indexed)

The schema for talks is intentionally minimal — `title`, `date`,
`authors`, `publication_types`, `links` — matching every existing entry
under `EditMe/Writings/Presentations/`. If you want to remember the conference / venue,
edit the title or add it to the slides themselves.

## TL;DR (books)

Same workflow, but use the `book/` subfolder. The bot still consults
Crossref (book metadata IS indexed there) but forces the type to `book`
regardless of what Crossref returns, so the entry lands on the
**Books** tab of the Writings page. Set the `publication:` line (e.g.
`Cambridge University Press, 2026`) via the slash command
`/publication …` or the pencil icon if Crossref didn't fill it in.

## What does the bot fill in?

It reads the PDF and tries to find a DOI (printed on the masthead of
most journals). If it finds one — or if a Crossref title-search matches
(papers and books only) — it pulls back:

- Canonical title and author list (full names, not just initials)
- Journal/publisher name, volume, issue, page range (or article number)
- Year
- Abstract (publisher-provided, when available)
- DOI link (used for the **Publisher's Version** button)

If no DOI / Crossref match is found (e.g. a brand-new working paper
that hasn't been indexed yet, or a slide deck), the bot scaffolds the
front matter from the PDF's text and flags everything that needs human
verification in the PR comment.

## What if I want a different slug?

The bot derives the URL slug from the paper's canonical title. If you
want something different, just rename the folder
`EditMe/Writings/Articles/Unsorted/<slug>/` (or
`EditMe/Writings/Presentations/<slug>/` for talks) and the file
`_site/static/files/<slug>.pdf` in the PR diff before merging. Hugo will
use whatever folder name you end with.

## Don't leave anything stale here

This folder (and its `talk/`, `book/` subfolders) should normally be
empty. The bot moves PDFs out as soon as a PR is opened. If you see
leftover files, it means an intake PR was opened and never merged —
clean it up by deleting the file via the GitHub UI.
