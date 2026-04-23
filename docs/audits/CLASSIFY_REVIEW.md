# Classification audit — items needing manual review

Generated after the auto-fix pass. None of these are bugs per se — they need a human to look at the underlying PDF / slide deck before moving them.

## Dual-typed entries (journal_article + software) — left as journal

These entries carry both `journal_article` and `software` in `publication_types`. Because they are journal articles *about* a piece of software (not the software product page itself), they remain on the Journal Articles tab:

- `an-overview-of-the-virtual-data-center-project-and-software`
- `boocio-an-education-system-with-hierarchical-concept-maps`

If you'd prefer them on the Software tab instead, flip `data/writings_legacy_map.json` for the slug (`tab: software`, `drupal: software`) and they will move over.

## Talks that legitimately carry a `publication:` journal reference

These are talks that cite the underlying published paper in their `publication:` field. The auto-fix already normalized their `publication_types` to `[presentation]`, so they display correctly in the talk listings:

- `a-politically-robust-experimental-design-for-public-policy-evaluation-with-appli-2006` (JPAM)
- `an-improved-method-of-automated-nonparametric-content-analysis-for-social-scienc-2016` (Political Analysis)
- `death-by-survey-estimating-adult-mortality-without-selection-bias-from-sibling-s-2005` (Demography)
- `how-censorship-in-china-allows-government-criticism-but-silences-collective-expr-2012` (APSR)
- `how-to-measure-legislative-district-compactness-if-you-only-know-it-when-you-see-2019-99` (AJPS)
- `the-balance-sample-size-frontier-in-matching-methods-for-causal-inference-2014` (AJPS)
- `the-future-of-death-in-america-2008` (Demographic Research)
- `why-propensity-scores-should-not-be-used-for-matching-2015-203` (Political Analysis)

These are correctly on the Presentations tab; the `publication:` field on each is informational and points readers to the underlying paper.
