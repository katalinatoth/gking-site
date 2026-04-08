---
title: "Why Propensity Scores Should Not Be Used for Matching"
date: "2019-01-01"
authors:
  - "Gary King"
  - "Richard Nielsen"
publication_types:
  - "article-journal"
abstract: "We show that propensity score matching (PSM), an enormously popular method of preprocessing data for causal inference, often accomplishes the opposite of its intended goal --- thus increasing imbalance, inefficiency, model dependence, and bias. The weakness of PSM comes from its attempts to approximate a completely randomized experiment, rather than, as with other matching methods, a more efficient fully blocked randomized experiment. PSM is thus uniquely blind to the often large portion of imbalance that can be eliminated by approximating full blocking with other matching methods. Moreover, in data balanced enough to approximate complete randomization, either to begin with or after pruning some observations, PSM approximates random matching which, we show, increases imbalance even relative to the original data. Although these results suggest researchers replace PSM with one of the other available matching methods, propensity scores have other productive uses.Replication data at the Harvard Dataverse:https://doi.org/10.7910/DVN/A9LZNV."
links:
  - type: pdf
    url: "/files/pan1900011_rev.pdf"
  - type: source
    url: "https://doi.org/10.1017/pan.2019.11"
  - name: "Supplementary Material"
    url: "/files/psnot-supp.pdf"
---
