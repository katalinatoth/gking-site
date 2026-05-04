# EditMe/Writings/Presentations/

Talks Gary has given. Each unique talk title gets its own folder; inside
that folder, each venue where the talk was given gets a sub-folder.

```
Presentations/
└── <title-slug>/                       one folder per talk title
    └── <venue-slug>/index.md           one sub-folder per venue
        ├── slides.pdf                  PDFs and other resources travel
        └── ...                         with the venue page-bundle
```

About 30 talks were given at multiple venues (the same talk delivered
at different conferences or universities); for those, multiple venue
sub-folders share one title folder. The other ~230 talks were
single-venue, so their title folder has one venue sub-folder inside.

We keep the consistent two-deep structure even for single-venue talks
so that the layout is uniform.

## Where these appear on the live site

Each venue sub-folder maps to one page at `/talk/<venue-slug>/` on the
live site. The "Presentations" tab on the Writings page aggregates
them.
