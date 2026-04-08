---
title: "Simplifying Causal Inference"
date: "2014-01-01"
authors:
  - "Gary King"
publication_types:
  - "speech"
abstract: "We propose a simplified approach to matching for causal inference that simultaneously optimizes both balance (between the treated and control groups) and matched sample size. This procedure resolves two widespread (bias-variance trade off-related) tensions in the use of this powerful and popular methodology. First, current practice is to run a matching method that maximizes one balance metric (such as a propensity score or average Mahalanobis distance), but then to check whether it succeeds with respect to a different balance metric for which it was not designed (such as differences in means or L1). Second, current matching methods either fix the sample size and maximize balance (e.g., Mahalanobis or propensity score matching), fix balance and maximize the sample size (such as coarsened exact matching), or are arbitrary compromises between the two (such as calipers with ad hoc thresholds applied to other methods). These tensions lead researchers to either try to optimize manually, by iteratively tweaking their matching method and rechecking balance, or settle for suboptimal solutions. We address these tensions by first defining thematching frontieras the set of matching solutions with maximum balance for each possible sample size. Researchers can then choose one, several, or all matching solutions from the frontier for analysis in one step without iteration. The main difficulty in this strategy is that checking all possible solutions is exponentially difficult. We solve this problem with new algorithms that finish fast and require no iteration or manual tweaking. We also offer easy-to-use software that implements these ideas, along with several empirical applications.  Along the way, we reveal surprising problems with some existing methods of matching.  This talk is based, in part, onthis paperwith Christopher Lucas and Richard Nielsen."
links:
  - type: pdf
    url: "/files/pspara-usc.pdf"
---
