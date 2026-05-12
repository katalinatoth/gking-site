# Site Audit — April 2026

Captured: 2026-04-23. Based on a fresh crawl of the built site
(`public/`), the source templates, and the live site at
<https://gking.harvard.edu/>.

The headline is that the site is in good structural shape. The
real low-hanging fruit is (1) a small list of actually-broken
links and (2) ~25% of the homepage HTML is redundant inline
`style=""` attributes that could be collapsed to a tiny CSS
sheet. Everything else is either polish or opt-in growth.

---

## Part 1 — Broken link audit

### 1a. Internal links — 17 real failures

Crawled every HTML page under `public/` and resolved every
`<a href>` and `<img src>` against the filesystem, normalizing
encoding (Hugo is inconsistent about whether non-ASCII directory
names are percent-encoded on disk).

| Impact | Link | Source pages | Fix |
|---|---|---|---|
| 4 | `/software/eir-an-r-program-for-ecological-inference/` | EI pub/software pages | The EI page still points at a non-existent "eiR" sub-page. Either resurrect that page, or rewrite the link as a GitHub repo URL (e.g. `https://github.com/iqss-research/ei`). |
| 2 each ×6 | `/files/abs/{cem-math,cem-plus,cemStata,counterf,counterft,jp,smooth,sv,words,writeit}-abs.shtml` | CEM / WhatIf / JudgeIt / ReadMe / SSA | Drupal-era abstract stubs that no longer exist. Replace with the matching `/publication/<slug>/` URL. |
| 1 each ×2 | `/files/abs/0s-abs.shtml`, `evil-abs.shtml` | Relogit, Amelia II | Same pattern. |
| 1 each ×2 | `/files/gking/files/diss2.pdf`, `profdev2.pdf` | `/teaching/` | Path is doubled — should be `/files/diss2.pdf` and `/files/profdev2.pdf`. |
| 1 | `/publication/boocio-an-education-system-with-hierarchical-concept-maps/` | `/software/` | Dead slug; drop the link or fix it. |
| 1 | `/software/relogit-rare-events-logistic-regression/g/files/abs/1s-abs.shtml` | Relogit | Malformed relative path (`/g/files/...`). |

All 1,400+ other apparent failures from a naive crawl are false
positives from:

- Alpine.js `:href` bindings in the Pagefind search widget
  (evaluated at runtime, not static links).
- Inconsistent encoding of non-ASCII directory names between
  `publication/` (raw Unicode) and `people/` (percent-encoded).
  GitHub Pages normalizes both forms in a real browser.

### 1b. External links — 20 real 404s + 40+ dead hosts

Out of 603 unique external URLs, 125 responded with anything
other than a 200. Most of the noise is publisher anti-bot
fingerprinting (NEJM, SAGE, Science, PNAS, JSTOR, LinkedIn) that
behaves fine in a real browser. The genuinely dead ones:

**HTTP 404 (URL moved or deleted)**

- `http://polimetrics.com/team.html` — link on Bradley Palmquist's people page.
- `http://polisci.ucsd.edu/faculty/zeng.html` — link on WhatIf.
- `http://www.acthomas.ca/academic/acthomas.htm` — link on JudgeIt.
- `http://www.ingentaconnect.com/.../jep/...art00012` — link on the Social Security "Response" paper.
- `http://www.iq.harvard.edu/blog/sss/archives/author/gary-king/` — in the "Are You Making Causal Inferences" blog post.
- `http://www.polsci.ucsb.edu/faculty/hstoll/` — link on WhatIf.
- `http://www.press.umich.edu/titleDetailDesc.do?id=23784` — link on the homepage hero area.
- `http://www.rand.org/methodology/econ/girosi.html` — link on YourCast.
- `https://doi.org/10.1016/j.eclinm.2024` — incomplete DOI (missing article id) on the maternal-mortality paper.
- `https://doi.org/10.1111/j.1467-985X.2004.00319.x` — DOI on the ecological-inference comment; worth a second verification before replacing.
- `https://findanexpert.unimelb.edu.au/profile/10856-alan-lopez` — on Alan Lopez's people page.
- `https://github.com/IQSS/garyking_website_files/blob/main/ei_0.pdf` — the file is already available at `/files/ei_0.pdf` locally; link there.
- `https://github.com/IQSS/garyking_website_files/blob/main/evil.pdf` — same; the PDF should be served locally.
- `https://github.com/iqss-research/ei/tree/master/progs` — branch renamed to `main`; change `master` → `main` or drop the link.
- `https://github.com/schwenzfeier/udp` — repo is gone; drop or find authoritative replacement.
- `https://gsg.skku.edu/.../perId=LZStrKINQ...` — URL-encoded query string on Gi Heon Kwon's page broke; use a plain faculty profile URL.
- `https://www.gob.mx/imss/estructuras/mauricio-hernandez-avila` — Mauricio Hernández Ávila.
- `https://www.gob.mx/salud/.../directorio-de-la-direccion-general-de-evaluacion-del-desempeno-dged` — Manett Vargas.
- `https://www.press.umich.edu/books/9780472082823/unifying-political-methodology` — Michigan Press URL scheme changed.
- `https://www.valdosta.edu/.../bernard-tamas.php` — Bernard Tamas.

**Dead hosts — 34 URLs spread across 20 legacy `.edu` personal sites**

`neyman.stats.nwu.edu`, `jhfowler.ucsd.edu`, `polisci.lsa.umich.edu`,
`polisci2.ucsd.edu`, `r.iq.harvard.edu`, `www-polisci.tamu.edu`,
`www.hmdc.harvard.edu`, `www.polsci.purdue.edu`, `www.pupress.princeton.edu`,
`amacherdagdelen.com`, `chengyufu.org`, `ericmazur.com`,
`meredithdost.com`, `nicolenova.com`, `sinanaral.mit.edu`,
`www.chrisdanford.com`, `www.davidlazer.com`, etc. Each links
from at most two pages. Cheapest fix: replace each with the
person's current academic homepage; or drop the hyperlink and
keep the name as plain text.

### 1c. Tooling gap

The existing `.github/workflows/link-check.yml` only scans
external URLs in Markdown sources, runs weekly, and silently
misses (a) internal links between built pages and (b) links
inside layout partials, JS, and YAML. The 17 internal broken
links above wouldn't have been caught.

**Recommended change:** rewrite that workflow to run after the
Hugo build, using a `public/`-aware tool — either our own
cross-encoding-aware Python scanner (easy, lives in the repo)
or [`lychee`](https://github.com/lycheeverse/lychee) (one
binary, widely used). Run it on every push, not weekly, and
surface failures as a PR check.

---

## Part 2 — Performance

### What's fast today

- **Static site on GitHub Pages with gzip** — no server, no
  database, cold-cache paint is already quick.
- **Pagefind search** is precomputed; full-site search works
  offline in the browser with no backend round-trip.
- **Images** are converted to WebP by Hugo's image pipeline
  (968 WebPs in `public/`, avg ~12 KB) — the only uncompressed
  raster assets are a handful of JPGs in `_site/static/images/`.
- **CSS** is a single minified Tailwind v4 file, 208 KB raw /
  ~35 KB gzipped. That's in range for Tailwind.
- **Alpine.js 44 KB** is the heaviest JS; Hugo Blox's own JS is
  ~20 KB. Reasonable.

### Real issues worth fixing

#### Issue 1 — Homepage HTML is 1.04 MB (150 KB gzipped)

Breakdown of `public/index.html`:

| Component | Bytes | % of total |
|---|---|---|
| Research Areas section + inlined papers | 990 KB | **93%** |
| Inline `style="..."` attrs (deduped class candidates) | 275 KB | 26% of the same bytes |
| Inline `<svg>` icons | 147 KB | 14% |
| Inline `<script>` (accordion glue) | 10 KB | 1% |

Gzip gets this down to 150 KB over the wire, which is fine for
a fast connection. But the browser still has to parse **32,815
lines of HTML** with **320 `<details>` elements** at first
paint. That hurts Time-to-Interactive, especially on mobile, and
it's pure bloat given that most visitors expand *maybe* one or
two research areas.

**Three progressively-better fixes:**

1. *(Low effort, big win)* Deduplicate the inline
   `style="..."` attributes into a handful of CSS classes
   targeting the Research Areas and card grids. Files to touch:
   `layouts/_partials/home_research_area.html`,
   `layouts/_partials/research_areas_pub_item.html`,
   `layouts/landing/list.html`. Expected saving: ~250 KB HTML,
   ~30 KB gzipped.
2. *(Medium)* Inline only area titles/descriptions; move paper
   metadata into `/EditMe/ResearchAreas/Data.json` and hydrate each
   area's subcategory lazily when the user opens it (one-shot
   `fetch` on first `toggle`). Expected saving: ~800 KB HTML,
   and cheaper renders for a page that already fails the "only
   send what you need" test.
3. *(Higher effort, long-term)* Switch the homepage research-
   areas UI to a client-side component that renders from a
   small JSON bundle, and ship it as an `<iframe>`-free web
   component. Probably overkill at current traffic.

I'd pick **#1 now** and plan **#2** for later.

#### Issue 2 — `enableGitInfo: true` makes every CI build slower

We just enabled `enableGitInfo: true` for the Working Papers
roll-off. It's harmless, but on CI with `fetch-depth: 0` (which
you already have) Hugo now runs `git log` for every page. On a
repo this size it adds a few seconds per build.

Not worth reverting, but worth noting: `last-commit date` per
page is the only thing it's used for, and Hugo exposes it on
every page now, so if you ever want "Last updated: YYYY-MM-DD"
badges on publications, they're free.

#### Issue 3 — `public/` ships 1.2 GB of PDFs

The ten `compact-*.pdf` and ten `udp-*.pdf` slide decks are
each **10–20 MB**. Shipping them through GitHub Pages means
they count toward the Pages soft size limit (1 GB currently;
hard limit 100 GB). Each deploy also pushes the same 1 GB
artifact through the upload-pages-artifact step.

**Recommendation:** host those PDFs on Gary's IQSS page, on
Dataverse, or on `garyking.org` (or wherever the domain lands),
and replace the `/files/compact-*.pdf` links with external
URLs. Saves ~1 GB of every deploy and takes the repo from
"bulky" to "lean."

#### Issue 4 — Three fingerprinted JS bundles, only two needed

The Hugo Blox theme loads `hb-head`, `hugo-blox-en`,
`hb-search`, and Alpine.js on every page. `hb-search.min.js`
(465 bytes) is a loader for the search modal that's only used
when the user clicks the search icon. Tiny, but it's a blocking
`<script>` in the head. Making it `defer` is a one-line change
in the theme's `site_head.html`.

#### Issue 5 — Writings page (/publication/) is 761 KB

Same shape as the homepage — all publication metadata is
embedded as a JSON blob in `<script>var data = [...]</script>`,
plus every result's HTML is prebuilt above the fold. Since the
page already uses client-side filtering (search, sort, facets),
it could ship just the JSON and render the list in JS on load.
That would cut the HTML footprint ~60%. Deferred though — the
filter/search UX is excellent as-is, and the gzipped payload is
155 KB, which is workable.

---

## Part 3 — UX / design / retention

I read the homepage, writings page, software, and people pages
in context. Ranked rough-cut by *"will this change behavior?"*:

### Highest leverage

#### A. Add a "new & noteworthy" shelf to the hero

Right now the hero is text + photo + a "Full Bio and CV"
button. That's beautiful, but every visitor — whether they came
for Ecological Inference or Perusall or a new preprint — gets
the same CTA.

Add a narrow strip directly under the paragraph with 3–4 pill
buttons that point at the freshest things:

- "New: *Inducing Sustained Creativity*" → paper page
- "Software: MatchIt 4.7" → software page
- "Talk: 24th Jan 2026, Oxford" → talk page
- "Course: Gov 2001 S26" → teaching

These pills should be driven by a tiny YAML (`data/hero_pills.yaml`)
with at most five items and a date — same pattern as the Working
Papers shelf. Pure signal, no clutter.

Behavioral rationale: first-time visitors often don't know what
they came for until they see it. This is the front page of a
retail store.

#### B. Make the Research Areas card clickable, not just accordion

Right now clicking "Ecological Inference" opens a subtree of
subcategory expanders. That's discovery-slow: two clicks to get
to a paper, and users frequently miss that each paper line is a
link.

Two micro-fixes:

1. Make the area title itself open in-place *and* show a thin
   "→ See all" link that jumps to a dedicated
   `/EditMe/ResearchAreas/ecological-inference/` page (already exists
   — it's how the site is structured). That gives both a quick
   peek and a deep-dive in one click.
2. On the subcategory rows, make the whole row clickable (not
   just the title text). A subtle hover fill already signals
   affordance.

#### C. Persistent "What just changed" affordance

Most returning visitors are checking "did Gary post a new
paper?" or "is there new Amelia code?" — they want a single
place to see activity.

One small addition, high perceived value: a **"Recent activity"**
panel in the footer (or a standalone `/activity/` page linked
from the header) auto-built from the git log over the last 30
days, grouped by section. Build it with the same first-commit
script you just added; it's five lines of Hugo.

#### D. Writings page — add "Cite" button on each result

The writings page already has "Download citations" for the
full filtered list. Add a small "Cite" icon on each card that
copies a BibTeX entry to clipboard. Impossible to forget
academics' #1 action: grab a citation. Implementation is ~20
lines of JS (the data is already in the embedded JSON).

#### E. Software page — rescue the "Older" section

After the recent cleanup, "Older" is visually indistinguishable
from "Active" — same color, same pill style. Users can't tell
at a glance whether `CEM` or `JudgeIt` is maintained.

Two tweaks:

1. Desaturate the "Older" card backgrounds to a 5–10% gray and
   switch their title color from `#337ab7` to `#64748b`.
2. Add a muted caption under the "Older" header: "Historical
   software, no longer actively updated. Please see GitHub for
   the current maintained packages."

### Medium leverage

#### F. Hero CTA goes to Bio — consider "Contact" or "Teaching"

Academic visitors who land on the homepage are usually doing
one of: (1) reading Gary's papers, (2) trying to contact him,
(3) looking for course material, (4) evaluating his research
group. The current hero CTA ("Full Bio and CV") addresses (4)
only. Consider a second, secondary button ("Get in touch" →
`/contact/`) for (2).

#### G. Sticky mini-TOC on long publication pages

Long publication pages like
`/publication/survey-estimates-of-wartime-mortality/` scroll
through abstract → citation → BibTeX → related papers. A
sticky `<nav>` in the margin with section jumps improves
scannability for anyone scanning a paper they haven't read.

#### H. People page filter and groupings

The "Current Research Group" card at the top is a big win. The
rest of the page is a flat filterable list of alumni +
collaborators. Add one piece of structure: a "Graduation year"
facet in the filter sidebar (you already render graduation year
data). Most visitors will only care about a window, not
everyone ever.

#### I. Add Related / See Also to talks as well as publications

Your new category-driven related-finder works great on
`/publication/` and `/software/`. The same treatment on
`/talk/` pages would surface "other talks in this research
area" and double the discovery paths.

#### J. "Collections" landing pages as an alternative entry

Give each research area a page-size hero:

- `/EditMe/ResearchAreas/ecological-inference/` with a 1-paragraph
  overview + the 3–5 representative papers + the software +
  the talks, not the exhaustive list.

Many of these URLs already resolve; they're currently rendered
with the generic `/EditMe/ResearchAreas/` list template. Swapping in
a `section.html` that uses the curated first-line blurbs in
`EditMe/ResearchAreas/Data/research_areas.json` would be a 30-minute job
and give the site five new "shop window" pages.

### Small polish

- **Consistent accent color.** The hero button is burnt orange
  (`#a04a02`), the nav links are slate, the Research Areas
  accordions use `#337ab7` blue, the footer is near-black. Pick
  one accent (blue) and use orange only for a single
  prominent-action CTA. Right now both colors compete.
- **Hero photo is very wide and gets cropped on laptops.** A
  `object-position: center top` would keep Gary's face in-frame
  at every viewport.
- **Move the Twitter/X link out of the footer.** The account is
  still linked as `@KingGary` but the site now reads as a
  research portal; X isn't where methodologists publish.
  Replace with a Bluesky or Mastodon link, or just drop.
- **Contact page — add response-time expectation.** A one-liner
  like "Response usually within a week" sets expectations and
  cuts repeat emails.
- **404 page could feature top destinations.** Currently it's a
  generic "Page not found." Listing the five most-visited
  sections turns a dead end into a bounce-saver.

### Engagement / retention heuristics — how your site stacks up

| Principle | Today | Verdict |
|---|---|---|
| **Above-the-fold primary value** | Hero photo + intro + CTA | Good. Tiny improvement: add the "new & noteworthy" pills. |
| **Clear primary pathways** | 8-item top nav, Research Areas section | Good. Nav labels are concrete, not cute. |
| **Scanning hierarchy** | H1s, card grids, accordion on homepage | Good. The accordion work you did is the correct pattern. |
| **Reduced cognitive load** | Writings page filter UI, Working Papers spotlight | Strong. The primacy + Von Restorff framing is doing real work. |
| **Clear next actions** | Every paper/software row links out | Strong on paper pages; weaker on the homepage where the only next action is "Bio & CV". |
| **Trust signals** | Harvard branding, citation counts on Dataverse | Decent. Could add total-citation counter (Scholar) as a single-line fact. |
| **Return visits** | RSS feed (yes, generated at `/index.xml`) | The feed works. Expose a "Subscribe to updates" link in the footer near the social links. |
| **Exit friction** | External links open in new tabs (`target="_blank"`) on most places | Good — user doesn't lose you when clicking a GitHub link. |

---

## Part 4 — Feature ideas (highest → lowest ROI)

1. **Working Papers preprint badge** with DOI / bioRxiv / arXiv
   where it exists; auto-fill from a small YAML of preprint
   servers keyed by slug. One-line UX upgrade on every preprint
   page.
2. **Citation counter per paper.** Scrape (or let the curator
   input) Google Scholar counts quarterly into a YAML. Display
   a small "Cited N times" pill on each publication card.
   Hugely motivating for visitors deciding what to read.
3. **Per-paper BibTeX / RIS copy-to-clipboard** (the "Cite"
   button above).
4. **"Subscribe" modal** in the nav: a single-click capture
   (email or RSS URL) that points at `index.xml`. Academic
   visitors often want notifications; you don't currently ask.
5. **`/now/` page** (inspired by nownownow.com / Derek Sivers
   pattern). A single page you update every month or two with
   "what Gary is working on right now." Low maintenance, very
   high return-visitor engagement.
6. **Search result pinning.** The Pagefind-powered site search
   works, but it doesn't know what's important. Add a small
   `_site/data/pinned_searches.yaml` so typing "matching" or "ei"
   always surfaces MatchIt / EI at the top.
7. **Reading time on publication pages.** Free from the
   abstract length + a constant; cues users that a particular
   paper is a 20-minute read rather than a 90-minute one.
8. **Paper series / co-author graph landing page.** Given all
   the coauthor metadata you already have in
   `EditMe/People/Authors/`, a small D3 or sigma.js graph on
   `/people/` or `/research-group/` would be a conversation
   piece and a genuine discovery tool.
9. **Canonical "How to cite Gary's work"** page linked from the
   footer. Three paragraphs + three canonical citations.
   Saves everyone time.
10. **Hosted slide decks with per-slide deep links.** Given how
    many of the site's PDFs are slide decks, a lightweight
    Reveal.js-based "View slides" mode on talk pages would
    surface content that currently lives only in PDF.

---

## Priority queue (if you tackle one thing a day)

1. Fix the 17 internal broken links and the 20 external 404s.
2. Move PDFs > 5 MB off GitHub Pages (saves 1 GB of repo heft).
3. Collapse the homepage inline styles into CSS classes
   (saves ~250 KB HTML).
4. Add the "new & noteworthy" hero pills, driven by a tiny YAML.
5. Add per-paper "Cite" copy-to-clipboard.
6. Switch the Research Areas paper list from eager HTML to
   lazy-load on first open (saves ~800 KB HTML).
7. Replace the weekly external-link workflow with a
   post-build full internal+external check that runs on every
   push.
8. Rescue the "Older" software category visually.
9. Add a citation-count pill to publication cards.
10. Add a `/now/` page and a Subscribe-to-RSS link in the nav.

Happy to start on any of these — point me at the one(s) you'd
like first.
