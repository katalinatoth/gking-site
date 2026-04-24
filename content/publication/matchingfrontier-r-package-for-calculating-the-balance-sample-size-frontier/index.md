---
title: "MatchingFrontier: R Package for Calculating the Balance-Sample Size Frontier"
date: "2014-01-01"
authors:
  - "Gary King"
  - "Christopher Lucas"
  - "Richard Nielsen"
publication_types:
  - "software"
abstract: |-
  Matching methods have become extremely popular among researchers working with observational data, especially when used as a nonparametric preprocessing step to reduce model dependence. But despite this popularity, existing matching approaches leave researchers with two fundamental tensions. First, they are often designed to maximize one metric (such as propensity score or Mahalanobis distance) but are judged against another for which they were not designed (such as the L1 statistic or differences in means). Second, they lack a principled solution to revealing the implicit bias-variance trade off: matching methods need to optimize with respect to both imbalance (between the treated and control groups) and the number of observations pruned, but existing approaches optimize with respect to only one; users then either ignore the second or tweak it without a formal stopping rule.

  MatchingFrontier resolves both tensions by consolidating previous techniques into a single, optimal, and flexible approach. The software calculates the matching solution with maximum balance for each possible sample size (N, N−1, N−2, …) and returns each solution, the whole of which constitute the frontier, from which the user can easily choose one, several, or all subsamples with which to conduct the final analysis, given their own choice of imbalance metric and quantity of interest. MatchingFrontier solves the joint optimization problem in one run, automatically, without manual tweaking, and without iteration. Although for each subset size k there exist a huge number of unique subsets, MatchingFrontier includes specially designed and extremely fast algorithms that give the optimal answer, usually in a few minutes or less. Methods are based on King, Lucas, and Nielsen (2017).
---
