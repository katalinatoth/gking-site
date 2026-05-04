# EditMe/Writings/

Every paper, book, report, patent, court brief, and presentation. This
is the largest section of the site (~553 entries).

## Folder layout

```
Writings/
├── Articles/                       (~210 journal articles)
│   ├── CausalInference/
│   │   ├── 2020s/<slug>/index.md
│   │   ├── 2010s/<slug>/index.md
│   │   ├── 2000s/<slug>/index.md
│   │   └── 1990s/<slug>/index.md
│   ├── AutomatedTextAnalysis/<decade>/<slug>/
│   ├── EcologicalInference/<decade>/<slug>/
│   ├── EventCountsAndDurations/<decade>/<slug>/
│   ├── MissingDataMeasurementErrorPrivacy/<decade>/<slug>/
│   ├── QualitativeResearch/<decade>/<slug>/
│   ├── RareEvents/<decade>/<slug>/
│   ├── SurveyResearch/<decade>/<slug>/
│   ├── UnifyingStatisticalAnalysis/<decade>/<slug>/
│   ├── AnchoringVignettes/<decade>/<slug>/
│   └── Other/<decade>/<slug>/      (papers not tagged with a research area)
│
├── Books/<decade>/<slug>/          (9 books)
├── Reports/<decade>/<slug>/        (~17 reports / "other")
├── Patents/<decade>/<slug>/        (17 patents)
├── CourtBriefs/<decade>/<slug>/    (5 court briefs)
│
├── Presentations/                  (~259 talks)
│   └── <title-slug>/
│       └── <venue-slug>/index.md   (one folder per venue; for talks
│                                    given at a single venue, the title
│                                    folder still has a one-deep folder
│                                    inside, for consistency)
│
├── FeaturedOnHomepage.yaml         which papers appear in the "Featured"
│                                    carousel on the homepage
├── TabRouting.json                 maps each writing to a tab on the
│                                    /publication/ page (Articles tab,
│                                    Books tab, Presentations tab, …)
└── README.md                       this file
```

## How to navigate

To find a specific paper without using search:

1. Pick the **type** (Articles, Books, etc.).
2. For Articles, pick the **research topic**.
3. Pick the **decade**.
4. Each `<slug>/` folder has the paper's `index.md` with frontmatter
   (title, authors, abstract, date) plus the PDF and figures that
   travel with that paper.

## Caveats and limitations

### Multi-topic papers (~9 papers)

Some papers belong to two or more research areas. Since a folder can
only physically be in one place, each paper picks a single primary
topic. The paper still appears under all of its topics on the live site
(the Research Areas page is generated from the paper's frontmatter
`tags:`, not from the folder location).

### Single-venue talks

Most talks were only given at one venue. We still create a one-deep
folder structure (`Presentations/<title-slug>/<venue-slug>/index.md`)
for them, so the layout is consistent with multi-venue talks. The
"venue-slug" sub-folder might just be `default/` or named after the
year for single-venue talks.

### "Other" articles bucket

Roughly 91 articles aren't tagged with a research area in the data file.
They go in `Articles/Other/<decade>/<slug>/`. To re-classify a paper,
move its folder into the appropriate topic folder and update its
frontmatter `tags:`.

## How the website-builder sees this

Each leaf folder under `Writings/Articles/<topic>/<decade>/` is mounted
to `content/publication/` in the website-builder's view. URLs on the
live site (`/publication/<slug>/`) are unchanged.

The mounts block in [`../../hugo.yaml`](../../hugo.yaml) is regenerated
by [`../../_automation/scripts/generate_mounts.py`](../../_automation/scripts/generate_mounts.py)
whenever folders are added or removed.
