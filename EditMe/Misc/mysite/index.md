---
title: "Build Your Academic Website in 15 Minutes"
slug: "mysite"
url: /mysite/
date: '2026-06-16'
type: mysite
summary: "A startup guide for graduate students and senior researchers — build a full academic website with AI, hosted for free. No coding required."

# --- Blind link (unlisted, not indexed). Remove these keys to publish. ---
blind: true        # adds <meta name="robots" content="noindex, nofollow, noarchive">
build:
  render: always   # page still builds at /site-prompts/
  list: never      # but is excluded from every page list (tabs, related, homepage, sitemap)

# --- Prompt documents (embedded inside the "Get your prompt" step). ---
prompts:
  - name: "Grad Student Prompt"
    meta: "for PhD students, postdocs & fellows"
    file: "files/GRAD_STUDENT_SITE_PROMPT.md"
  - name: "Academic Prompt"
    meta: "for faculty & senior researchers"
    file: "files/ACADEMIC_SITE_PROMPT.md"

# --- Printable guides (shown at the bottom of the page). ---
guides:
  - name: "Step-by-Step Guide"
    meta: "the quick walkthrough on this page"
    file: "files/Website-Prompt-Step-by-Step.pdf"
  - name: "Detailed Guide"
    meta: "the full explainer of how it all works"
    file: "files/ACADEMIC_SITE_HUMAN_DOC.pdf"
---

<!-- The step-by-step instructions live in layouts/site-prompts/single.html as a
     collapsible accordion. This body is intentionally left blank. -->
