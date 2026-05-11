# Claude Prompts for Common Website Tasks

Copy-paste any prompt below into Claude (or Cursor). Replace every **`XXX`** with your actual information before sending. Where a prompt says to **upload** a file, attach it to the same message.

---

## Table of Contents

1. [Add a New Journal Article](#1-add-a-new-journal-article)
2. [Add a New Book](#2-add-a-new-book)
3. [Add a New Presentation](#3-add-a-new-presentation)
4. [Add a New Court Brief](#4-add-a-new-court-brief)
5. [Add a New Patent](#5-add-a-new-patent)
6. [Add a New Software Package Page](#6-add-a-new-software-package-page)
7. [Replace or Update a PDF](#7-replace-or-update-a-pdf)
8. [Add a Short URL (Redirect)](#8-add-a-short-url-redirect)
9. [Add a Paper to a Research Area on the Homepage](#9-add-a-paper-to-a-research-area-on-the-homepage)
10. [Add a New Teaching Class](#10-add-a-new-teaching-class)
11. [Update the Bio / CV Page](#11-update-the-bio--cv-page)
12. [Add a New Blog Post](#12-add-a-new-blog-post)

---

## 1. Add a New Journal Article

**Upload:** The article PDF (and supplementary material PDF, if any).

```
Add a new journal article to the website. Here are the details:

- Title: XXX
- Authors: XXX (comma-separated, e.g. "Gary King, Jane Doe, John Smith")
- Publication venue: XXX (e.g. "American Political Science Review, 111, 3, Pp. 484–501")
- Year: XXX
- Abstract: XXX
- Publisher's DOI or URL: XXX
- Dataverse DOI (if any): XXX

The article PDF is attached. [Also attach supplementary material if applicable.]

Place it in EditMe/Writings/Articles/ under the correct topic folder and decade.
The topic folders are: AnchoringVignettes, AutomatedTextAnalysis, CausalInference,
EcologicalInference, EventCountsAndDurations, MissingDataMeasurementErrorPrivacy,
QualitativeResearch, RareEvents, SurveyResearch, UnifyingStatisticalAnalysis, or
Other (if none of the above apply). The topic for this paper is: XXX

Create a slug from the title (lowercase, hyphens, max ~80 chars), make the folder
at EditMe/Writings/Articles/<Topic>/<Decade>/<slug>/, write index.md with the
standard front matter, and put the PDF(s) in _site/static/files/. Reference them
as "files/<filename>.pdf" in the links. Commit and push.
```

---

## 2. Add a New Book

**Upload:** Nothing required, but optionally attach a cover image (named `featured.jpg` or `featured.png`).

```
Add a new book to the website. Here are the details:

- Title: XXX
- Authors: XXX
- Publisher: XXX (e.g. "Princeton University Press")
- Publisher city: XXX (e.g. "Princeton, NJ")
- Year: XXX
- Abstract / description: XXX
- Publisher's URL (if any): XXX
- Dataverse DOI (if any): XXX

[If you have a cover image, say: "I've attached a cover image — save it as featured.jpg
in the book's folder."]

Place it in EditMe/Writings/Books/<Decade>/<slug>/index.md with the standard book
front matter (publication_types: book). Commit and push.
```

---

## 3. Add a New Presentation

**Upload:** The presentation PDF (slides).

```
Add a new presentation to the website. Here are the details:

- Talk title: XXX
- Presenter(s): XXX
- Venue / event name: XXX
- Year: XXX
- Abstract: XXX
- Related publication slug (if this talk is based on a paper already on the site): XXX

The slides PDF is attached.

Presentations live in EditMe/Writings/Presentations/<title-slug>/<venue-slug>/.
The title-slug groups all venues where the same talk was given. The venue-slug
becomes the URL: /talk/<venue-slug>/. Create the folders, write index.md with
publication_types: presentation, put the PDF in _site/static/files/, and add
"related_paper: <slug>" if there's a matching publication. Commit and push.
```

---

## 4. Add a New Court Brief

**Upload:** The court brief PDF.

```
Add a new court brief to the website. Here are the details:

- Title: XXX (e.g. "Brief of Amici Curiae Professors ... in Support of ...")
- Authors: XXX (all signatories, comma-separated)
- Year: XXX
- Abstract: XXX
- Related publication slug (if any): XXX

The brief PDF is attached.

Place it in EditMe/Writings/CourtBriefs/<Decade>/<slug>/index.md with
publication_types: court_brief. Put the PDF in _site/static/files/.
Commit and push.
```

---

## 5. Add a New Patent

**Upload:** The patent PDF.

```
Add a new patent to the website. Here are the details:

- Title: XXX
- Inventors: XXX (comma-separated)
- Year granted: XXX
- Patent number: XXX (e.g. "United States of America US 8,914,373 B2")
- Abstract: XXX

The patent PDF is attached.

Place it in EditMe/Writings/Patents/<Decade>/<slug>/index.md with
publication_types: patent. The "publication" field should contain the
patent number string. Put the PDF in _site/static/files/. Commit and push.
```

---

## 6. Add a New Software Package Page

**Upload:** Nothing required.

```
Add a new software package page to the website. Here are the details:

- Software name: XXX
- Authors / maintainers: XXX
- Year: XXX
- External website URL: XXX
- Brief description (for the page body): XXX
- Related software to cross-reference (if any): XXX

Create EditMe/Software/<package-slug>/index.md. Use a "site" link type pointing
to the external URL. If there are related packages, add a see_also list with
title/section/slug entries. Commit and push.
```

---

## 7. Replace or Update a PDF

**Upload:** The new PDF file.

```
Replace the PDF for an existing item on the website.

- Item title: XXX
- Type (article / book / presentation / brief / patent): XXX
- New PDF is attached.

Find the item's index.md by searching for the title under EditMe/Writings/ (or
EditMe/Software/ for software). Look at its links to find the current PDF filename
in _site/static/files/. Replace that file with the new PDF I've attached, keeping
the same filename so existing links stay valid. If the filename should change,
update the links in index.md too. Commit and push.
```

---

## 8. Add a Short URL (Redirect)

**Upload:** Nothing required.

```
Add a new short URL redirect to the website.

- Short URL path: XXX (e.g. "privacy" → gking.harvard.edu/privacy/)
- Target: XXX (e.g. "/publication/statistically-valid-inferences-from-privacy-protected-data/"
  for an internal page, or "https://example.com" for an external URL)
- Note (optional): XXX (e.g. "vanity URL for the privacy paper")

Add a new entry to EditMe/Redirects/Data/redirects.yaml. Internal targets
will be served inline (address bar keeps the short URL); external targets
redirect normally. Make sure the short URL doesn't collide with an existing
top-level page. Commit and push.
```

---

## 9. Add a Paper to a Research Area on the Homepage

**Upload:** Nothing required.

```
Add a paper to one of the Research Areas on the homepage.

- Paper title: XXX
- Paper slug (the folder name under EditMe/Writings/ or content/): XXX
- Paper section: XXX (usually "publication")
- Research area name: XXX (e.g. "Causal Inference")
- Subcategory within that area: XXX (e.g. "Matching" — look at existing
  subcategories in the data file to pick the right one, or suggest a new one)

Edit EditMe/ResearchAreas/Data/research_areas.json. Find the correct area
under "methods" or "applications", find or create the subcategory, and add
an entry like {"title": "...", "section": "publication", "slug": "..."}.
Commit and push.
```

---

## 10. Add a New Teaching Class

**Upload:** Nothing required.

```
Add a new teaching class to the website.

- Class name / number: XXX (e.g. "Gov 2001")
- Slug for the URL: XXX (e.g. "gov2001" → /teaching/gov2001/)
- Description / page content (HTML or plain text): XXX
- Link to syllabus or course site (if any): XXX

Create EditMe/Teaching/<slug>/index.md with type: teaching-class in the
front matter. The page body can be HTML. Also add a card for it in the
grid inside EditMe/Teaching/_index.md so it shows up on the teaching
landing page. Commit and push.
```

---

## 11. Update the Bio / CV Page

**Upload:** The new CV PDF (if updating the CV).

```
Update the Bio/CV page on the website.

Changes to make:
XXX (describe what should change — e.g. "update the job title to ...",
"add a new award", "replace the CV PDF with the attached file", etc.)

If replacing the CV PDF: put the new file at _site/static/files/vitae.pdf.
The bio page content is in EditMe/Bio/. Commit and push.
```

---

## 12. Add a New Blog Post

**Upload:** Any images for the post (optional).

```
Add a new blog post to the website.

- Title: XXX
- Date: XXX (YYYY-MM-DD)
- Content: XXX (the post body, in markdown)

Create EditMe/Blog/<slug>/index.md with the title and date in front matter
and the content in the body. If there are images, place them in the same
folder. Commit and push.
```

---

## Tips

- **Finding an existing item:** If you're not sure of the exact path, ask Claude to search for the item by title: *"Find the index.md for the paper titled 'XXX' and show me its path."*
- **Previewing locally:** After any change, ask: *"Build the site locally with `hugo server` and let me check it before pushing."*
- **Multiple changes at once:** You can combine prompts — e.g., upload a new article AND ask to add it to a research area AND create a short URL, all in one message.
