---
title: "MatchingFrontier: R Package for Calculating the Balance-Sample Size Frontier"
date: "2014-01-01"
authors:
  - "Gary King"
  - "Christopher Lucas"
  - "Richard Nielsen"
links:
  - type: site
    url: "https://projects.iq.harvard.edu/frontier"
summary: |
  MatchingFrontier is an easy-to-use R Package for making optimal causal inferences from observational data.  Despite their popularity, existing matching approaches leave researchers with two fundamental tensions. First, they are designed to maximize one metric (such as propensity score or Mahalanobis distance) but are judged against another for which they were not designed (such as L1 or differences in means). Second, they lack a principled solution to revealing the implicit bias-variance trade off: matching methods need to optimize with respect to both imbalance (between the treated and control groups) and the number of observations pruned, but existing approaches optimize with respect to only one; users then either ignore the other, or tweak it, usually suboptimally, by hand.

  MatchingFrontier resolves both tensions by consolidating previous techniques into a single, optimal, and flexible approach. It calculates the matching solution with maximum balance for each possible sample size (N, N-1, N-2,...). It thus directly calculates the entire balance-sample size frontier, from which the user can easily choose one, several, or all subsamples from which to conduct their final analysis, given their own choice of imbalance metric and quantity of interest. MatchingFrontier solves the obvious joint optimization problem in one run, automatically, without manual tweaking, and without iteration.  Although for each subset size k, there exist a huge (N choose k) number of unique subsets, MatchingFrontier includes specially designed fast algorithms that give the optimal answer, usually in a few minutes.

  MatchingFrontier has officially been "Qualified for Scientific Use" by the U.S. Food and Drug Administration.
---

MatchingFrontier is an easy-to-use R Package for making optimal causal inferences from observational data.  Despite their popularity, existing matching approaches leave researchers with two fundamental tensions. First, they are designed to maximize one metric (such as propensity score or Mahalanobis distance) but are judged against another for which they were not designed (such as L1 or differences in means). Second, they lack a principled solution to revealing the implicit bias-variance trade off: matching methods need to optimize with respect to both imbalance (between the treated and control groups) and the number of observations pruned, but existing approaches optimize with respect to only one; users then either ignore the other, or tweak it, usually suboptimally, by hand.

MatchingFrontier resolves both tensions by consolidating previous techniques into a single, optimal, and flexible approach. It calculates the matching solution with maximum balance for each possible sample size (N, N-1, N-2,...). It thus directly calculates the entire balance-sample size frontier, from which the user can easily choose one, several, or all subsamples from which to conduct their final analysis, given their own choice of imbalance metric and quantity of interest. MatchingFrontier solves the obvious joint optimization problem in one run, automatically, without manual tweaking, and without iteration.  Although for each subset size k, there exist a huge (N choose k) number of unique subsets, MatchingFrontier includes specially designed fast algorithms that give the optimal answer, usually in a few minutes.

MatchingFrontier has officially been "Qualified for Scientific Use" by the U.S. Food and Drug Administration.
