# _automation/

Repository-wide automation: cross-section Python scripts plus the issue-driven
intake bot. Section-specific scripts (e.g. `intake_publication.py`) live next
to the section they belong to (`writings/scripts/`).

```
_automation/
├── intake/                  GitHub-issue intake bot
│   ├── README.md            how the intake flow works end to end
│   ├── book/                book intake configuration
│   └── talk/                talk intake configuration
└── scripts/                 cross-section Python tooling
    ├── build_redirects.py
    ├── import_drupal_redirects.py
    ├── intake_from_issue.py
    ├── build_intake_pr_body.py
    ├── apply_pr_edits.py
    ├── quick_add.py
    ├── fix_mojibake_markdown.py
    ├── scrape.py
    ├── convert.py
    └── requirements*.txt
```

## A note on `.github/`

GitHub Actions only scans `.github/workflows/` at the **repository root**, so
`.github/` cannot move under `_automation/`. The workflows there call into
`_automation/scripts/` and `<section>/scripts/` for their actual logic.

## A note on `.githooks/`

The local `core.hooksPath` git config (set by
[`_automation/scripts/enable-auto-push.sh`](scripts/enable-auto-push.sh))
points at `.githooks/` at the repo root. This is per-clone and stays at the
root for the same reason `.github/` does (tools expect the conventional
location).
