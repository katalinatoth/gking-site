# CV ⇄ Site audit

Compares Gary's CV (`~/Downloads/vitae.pdf`, Oct 2024) against site content, using the
CV's own 5-category taxonomy of writings:

| CV category           | Count in CV | On site | Notes |
|-----------------------|-------------|---------|-------|
| Books                 | 9           | 9       | all present (site New Edition counts separately) |
| Articles              | ~190        | ≥ 190   | all present; site also has 2024+ additions not yet on CV |
| Software              | 23          | 23      | all present; site also lists 20+ utility libraries and startups not on CV |
| Patents               | 17          | 17      | all present |
| US Supreme Court Amici Briefs | 4   | 4       | all present (currently filed under "Other/miscellaneous") |

Conclusion: **no CV item is missing from the site.** The remaining notes below list
(a) CV items currently filed in the wrong tab on the site, (b) site items not in the CV,
and (c) structural changes needed to make the site's tabs match the CV's categories
exactly.

---

## 1. CV items filed in the wrong tab on the site

These CV items exist on the site but live under a tab that doesn't match the CV category.
All should move into the **Articles** tab to match the CV (which has no separate "Book
Chapters" section — everything non-book in that part of the CV is an "Article").

### 1a. Book chapters the CV treats as articles  (currently Other/book_chapter → Articles)

- `advantages-of-conflictual-redistricting` (1996)
- `determinants-of-inequality-in-child-survival-results-from-39-countries` (2003)
- `ecological-inference` (2006, Palgrave entry)
- `empirically-evaluating-the-electoral-college` (2004)
- `inference-in-case-control-studies-2004` (2004) and `inference-in-case-control-studies` (2010)
- `information-in-ecological-inference-an-introduction` (2004)
- `numerical-issues-involved-in-inverting-hessian-matrices` (2003)
- `party-competition-and-media-messages-in-us-presidential-election-campaigns` (1994)
- `preface-big-data-is-not-about-the-data` (2016)
- `racial-fairness-in-legislative-redistricting` (1996)
- `so-youre-a-grad-student-now-maybe-you-should-do-this` (2020)
- `the-c-span-archives-as-the-policymaking-record-of-american-representative-democr` (2016)
- `the-changing-evidence-base-of-social-science-research-2009` (2009)
- `the-effect-of-war-on-the-supreme-court` (2006)
- `the-methodology-of-presidential-research` (1993)
- `data-analyses-and-reports-for-the-arizona-independent-redistricting-commission-f` (2012)
- `the-silverlining-project-finding-social-good-in-clouds-on-the-dark-web` (2020)

### 1b. Op-eds the CV treats as articles  (currently Other/newspaper_article → Articles)

- `theres-a-simple-solution-to-the-latest-census-fight` (2021)
- `how-to-conquer-partisan-gerrymandering` (2017)
- `the-citys-losing-clout` (1979) — NOT in CV; keep in Other

### 1c. Working papers the CV treats as articles  (currently Other/working_paper → Articles)

- `education-and-scholarship-by-video` (2021)
- `how-not-to-lie-without-statistics` (2008)
- `google-flu-trends-still-appears-sick-an-evaluation-of-the-20132014-flu-season` (2014)
- `how-human-subjects-research-rules-mislead-you-and-your-university-and-what-to-do` (2016)
- `evaluating-covid-19-public-health-messaging-in-italy-self-reported-compliance-an` (2020)

(`expert-report-of-gary-king-in-bowyer-et-al-v-ducey-governor-et-al-us-district-co` (2020)
is an expert report, not a CV Article — stays in Other.)

### 1d. Items mis-tagged as "presentation" on /publication/  (→ Articles)

These are actual journal articles whose `publication_types` front-matter is `[presentation]`
but which appear in the CV Articles section:

- `an-improved-method-of-automated-nonparametric-content-analysis-for-social-scienc`
- `how-to-measure-legislative-district-compactness-if-you-only-know-it-when-you-see-2021`
- `why-propensity-scores-should-not-be-used-for-matching`
- `how-the-chinese-government-fabricates-social-media-posts-for-strategic-distracti-2017-166`
- `the-balance-sample-size-frontier-in-matching-methods-for-causal-inference`
- `how-censorship-in-china-allows-government-criticism-but-silences-collective-expr-2013`
- `the-future-of-death-in-america`
- `a-politically-robust-experimental-design-for-public-policy-evaluation-with-appli-2007`
- `death-by-survey-estimating-adult-mortality-without-selection-bias-from-sibling-s`

### 1e. Books wrongly tagged (→ Books tab)

- `demographic-forecasting-2008` — tab=presentation in legacy_map; should be tab=book

### 1f. Amici Briefs (→ new Court Briefs tab)

- `brief-of-amici-curiae-professors-gary-king-bernard-grofman-andrew-gelman-and-jon` (2005)
- `brief-of-empirical-scholars-as-amici-curiae` (2012)
- `brief-of-heather-k-gerken-jonathan-n-katz-gary-king-larry-j-sabato-and-samuel-s` (2017)
- `brief-of-empirical-scholars-as-amici-curiae-in-support-of-respondents` (2022)

---

## 2. Site items NOT in the CV

The CV in `~/Downloads/vitae.pdf` is dated **October 2024**. Everything 2024-Q4 and later
is legitimately missing from the CV.

### 2a. Articles not on CV (11 items)

Newer than the CV:

- `a-simulation-based-comparative-effectiveness-analysis-of-policies-to-improve-glo` (2023)
- `assessing-differences-in-country-level-estimates-of-maternal-mortality-a-compari` (2025)
- `correcting-measurement-error-bias-in-conjoint-survey-experiments` (2025)
- `experimental-evidence-on-the-limited-influence-of-reputable-media-outlets` (2025)
- `global-maternal-health-country-typologies-a-framework-to-guide-policy` (2024)
- `how-american-politics-ensures-electoral-accountability-in-congress` (2025)
- `if-a-statistical-model-predicts-that-common-events-should-occur-only-once-in-100` (2025)
- `inducing-sustained-creativity-and-diversity-in-large-language-models` (2026)
- `statistical-intuition-without-coding-or-teachers` (2025)
- `survey-estimates-of-wartime-mortality` (2025)
- `evaluating-the-impacts-of-swapping-on-the-us-decennial-census` (2025, conf proceedings)

Older entries on the site that the CV does not list as articles:

- `book-review-of-forecasting-presidential-elections` (1985) — early book review
- `scoring-social-security-proposals-response-from-kashin-king-and-soneji` (2016) — short response-to-comment
- `twitter-big-data-opportunitiesresponse` (2014) — short response
- `an-overview-of-the-virtual-data-center-project-and-software` (2001) — CV lists the related "Introduction" article, not this "Overview" one
- `learning-catalytics-acquired-by-pearson` (2011) — startup/product page, currently mis-tagged as journal_article; belongs elsewhere
- `thresher-acquired-by-two-six-technologies-a-carlyle-group-company` (2017) — startup/product page, same issue

### 2b. Software on site but not in CV's Software section

The CV lists 23 named software packages. The site has more, because it also catalogs
supporting libraries, legacy software, and startups:

- `gillmurraycholeskyfactorization` (1987) — supporting library
- `schnabeleskowcholeskyfactorization` (1988) — supporting library
- `pc-checkbook-manager` (1982) — personal software from college
- `autocast-automated-bayesian-forecasting-with-yourcast` (2011) — YourCast companion
- `opendp-developing-open-source-tools-for-differential-privacy` (2020) — differential-privacy tool
- `robustse` (2015) — regression utility
- `openscholar` / `openscholar-2009` (duplicate software-page entries) — CV lists OpenScholar under **Companies Founded**, not Software
- `perusall` / `perusall-2015` (duplicate software-page entries) — CV lists Perusall under **Companies Founded**
- `quickcode` (2020) — CV lists under **Companies Founded**
- `privacyunbiased` / `unbiasedprivacy` (duplicate software-page entries) — not in CV
- plus several year-suffixed duplicates (`amelia-ii-…-2009`, `ei-…-2003`, `matchit-…-2007`,
  `perusall-2015`, `relogit-…-2003`, `whatif-…-2005`, `openscholar-2009`) that are copies
  of the canonical software pages

### 2c. Patents on site but not in CV

None. All 17 patents match.

### 2d. Books on site but not in CV

None. All 9 books match.

### 2e. Court Briefs on site but not in CV

None. All 4 amici briefs match.

### 2f. Items that fall outside any CV writings category (stay in Other)

- `the-citys-losing-clout` (1979, newspaper op-ed) — early op-ed, not in CV
- `the-stability-of-party-identification-among-us-representatives-political-loyalty` (1984, unpublished)
- `understanding-the-lee-carter-mortality-forecasting-method` (2007, unpublished)
- `archive-of-the-controversy-involving-wendy-k-tam-cho-brian-j-gaines-and-the-amer` (2002, report)
- `10-million-international-dyadic-events` (2003, dataset)
- `elections-to-the-united-states-house-of-representatives-1898-1992` (1994, dataset)
- `replication-data-for-public-policy-for-the-poor-…` (2009, dataset)
- `replication-data-for-explaining-systematic-bias-…` (2015, dataset)
- `replication-data-for-systematic-bias-…` (2015, dataset)
- `crimson-hexagon-merged-with-brandwatch-acquired-by-cision` (2007, company founding)
- `an-update-on-dataverse` (2014, blog-style web article)
- `expert-report-of-gary-king-in-bowyer-et-al-v-ducey-governor-et-al-us-district-co` (2020, expert report)
- `methods-for-extremely-large-scale-media-experiments-and-observational-studies-po` (2014, conference poster)
- `you-lie-patterns-of-partisan-taunting-in-the-us-senate-poster` (2014, conference poster)
- `automated-cognitive-debriefing` (2024, conference paper)
- `letter-to-us-census-bureau-request-for-release-of-noisy-measurements-file-by-sep` (2021, letter)

---

## 3. Tab structure changes to match CV

**Before:** Journal Articles · Books & Chapters · Presentations · Software · Patents · Other

**After:** Books · Articles · Software · Patents · Court Briefs · Presentations · Other

Counts after reclassification (approximate):

- Books: **9**
- Articles: **≈215** (183 current journal + ~32 moved from Other + 2024/5/6 additions)
- Software: **43** (unchanged)
- Patents: **17** (unchanged)
- Court Briefs: **4** (new)
- Presentations: **258** (unchanged)
- Other: **~17** (residual: datasets, expert reports, company/startup entries, letters, etc.)
