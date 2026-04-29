# intake/ — drop a PDF here to add a paper

This folder is the **one-stop drop zone for adding a new paper to the
website**.  See [UPDATING.md → Quick add: upload a PDF](../UPDATING.md#quick-add-upload-a-pdf)
for the click-by-click instructions.

## TL;DR

1. Click **Add file → Upload files** at the top of this folder on
   github.com.
2. Drag your PDF in.
3. Pick **"Create a new branch for this commit and start a pull
   request"**, then click **Propose changes** → **Create pull request**.
4. Wait ~1–2 minutes. A bot pushes a follow-up commit to the same PR
   with a generated `content/publication/<slug>/index.md`, the moved
   PDF (now under `static/files/`), and an updated
   `data/writings_legacy_map.json`. It also posts a summary comment.
5. Skim the PR diff. Edit any field in the **Files changed** tab if the
   auto-populate got something wrong (title, authors, year, abstract,
   citation line, etc.).
6. Click **Merge pull request**. The deploy workflow runs, and the new
   paper is live in another ~3 minutes.

## What does the bot fill in?

The bot reads the PDF and tries to find a DOI (printed on the masthead
of most journals). If it finds one — or if a Crossref title-search
matches — it pulls back:

- Canonical title and author list (full names, not just initials)
- Journal name, volume, issue, page range (or article number)
- Year
- Abstract (publisher-provided, when available)
- DOI link (used for the **Publisher's Version** button)

If no DOI / Crossref match is found (e.g. a brand-new working paper
that hasn't been indexed yet), the bot scaffolds the front matter from
the PDF's text and flags everything that needs human verification in
the PR comment.

## What if I want a different slug?

The bot derives the URL slug from the paper's canonical title. If you
want something different, just rename the folder
`content/publication/<slug>/` and the file `static/files/<slug>.pdf`
in the PR diff before merging. Hugo will use whatever folder name you
end with.

## Don't put anything else here

This folder should normally be empty. The bot moves PDFs out of it as
soon as a PR is opened. If you see leftover files here, it means an
intake PR was opened and never merged — clean it up by deleting the
file via the GitHub UI.
