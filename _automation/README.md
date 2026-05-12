# _automation/

Repository-wide automation: cross-section Python scripts plus the issue-driven
intake bot. Writings-specific scripts (e.g. `intake_publication.py`) live in
`_automation/scripts/writings/`; people-related scripts live in
`_automation/scripts/people/`.

```
_automation/
├── intake/                  drop-zone for the auto-import bot
│   ├── README.md            how the intake flow works end to end
│   ├── book/                drop book PDFs here
│   └── talk/                drop talk PDFs here
└── scripts/                 all Python tooling
    ├── writings/            intake, DOI fillers, citation audits, link repair
    ├── people/              profile scrapers, research-group sync
    ├── build_redirects.py
    ├── apply_rewrites.py
    ├── generate_mounts.py
    ├── import_drupal_redirects.py
    ├── intake_from_issue.py
    ├── build_intake_pr_body.py
    ├── apply_pr_edits.py
    ├── quick_add.py
    ├── regroup_articles.py
    ├── regroup_writings.py
    ├── regroup_presentations.py
    ├── regroup_presentations_fuzzy.py
    ├── fix_mojibake_markdown.py
    ├── enable-auto-push.sh
    ├── scrape.py
    ├── convert.py
    └── requirements*.txt
```

## A note on `.github/`

GitHub Actions only scans `.github/workflows/` at the **repository root**, so
`.github/` cannot move under `_automation/`. The workflows there call into
`_automation/scripts/` for their actual logic.

## A note on `.githooks/`

The local `core.hooksPath` git config (set by
[`_automation/scripts/enable-auto-push.sh`](scripts/enable-auto-push.sh))
points at `.githooks/` at the repo root. This is per-clone and stays at the
root for the same reason `.github/` does (tools expect the conventional
location).
