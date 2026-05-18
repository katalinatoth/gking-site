---
dataverse_url: "https://doi.org/10.7910/DVN/A9LZNV"
dataverse_name: "Replication Data for: Why Propensity Scores Should Not Be Used for Matching"
image:
  alt_text: "Figure 1: simulated data sets comparing Mahalanobis, propensity score, and random matching (graphic from the paper)."
title: "Why Propensity Scores Should Not Be Used for Matching"
date: "2019-01-01"
authors:
  - "Gary King"
  - "Richard Nielsen"
publication_types:
  - "journal_article"
abstract: |-
  This talk summarizes a paper -- Gary King and Richard Nielsen. 2015. "[Why Propensity Scores Should Not Be Used for Matching](/publication/why-propensity-scores-should-not-be-used-for-matching/)" -- with this abstract: Researchers use propensity score matching (PSM) as a data preprocessing step to selectively prune units prior to applying a model to estimate a causal effect. The goal of PSM is to reduce imbalance in the chosen pre-treatment covariates between the treated and control groups, thereby reducing the degree of model dependence and potential for bias. We show here that PSM often accomplishes the opposite of what is intended --- increasing imbalance, inefficiency, model dependence, and bias. The weakness of PSM is that it attempts to approximate a completely randomized experiment, rather than, as with other matching methods, a more powerful fully blocked randomized experiment. PSM, unlike other matching methods, is thus blind to the often large portion of imbalance that could have been eliminated by approximating full blocking. Moreover, in data balanced enough to approximate complete randomization, either to begin with or after pruning some observations, PSM approximates random matching which turns out to increase imbalance. For other matching methods, the point where additional pruning increases imbalance occurs much later in the pruning process, when full blocking is approximated and there is no reason to prune, and so the danger is considerably less. We show that these problems with PSM occur even in data designed for PSM, with as few as two covariates, and in many real applications. Although these results suggest that researchers replace PSM with one of the other available methods when performing matching, propensity scores have many other productive uses.

  See also [related work](/research-areas/#causal-inference).
links:
  - type: pdf
    url: "files/pan1900011_rev.pdf"
  - type: source
    url: "https://doi.org/10.1017/pan.2019.11"
  - type: appendix
    label: Appendix
    url: "files/psnot-supp.pdf"
publication: "Political Analysis, 27, 4, Pp. 435–454"
---
