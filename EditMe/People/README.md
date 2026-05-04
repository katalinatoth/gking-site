# EditMe/People/

Three different audiences live under "People" in the menu, each with a
different URL on the live site:

```
People/
├── ResearchGroup/      Gary's actual research-group members
│                       (current students, postdocs, alumni)
│                       → /research-group/ on the live site
│
├── Profiles/           ~350 collaborator profile cards
│                       (everyone who's co-authored a paper or talk)
│                       → /people/<slug>/ on the live site
│
├── Authors/            paper-credit listings (the entries shown on each
│                       paper's "by" line, linking through to a profile)
│                       → /authors/<slug>/ on the live site
│
└── Data/               data files used by the three sub-folders above
    └── research_group.json   the research-group roster
```

Each profile in `Profiles/` is a folder with `_index.md` plus a photo.
