---
abstract: |-
  In this article, we introduce a Stata implementation of coarsened exact matching, a new method for improving the estimation of causal effects by reducing imbalance in covariates between treated and control groups. Coarsened exact matching is faster, is easier to use and understand, requires fewer assumptions, is more easily automated, and possesses more attractive statistical properties for many applications than do existing matching methods. In coarsened exact matching, users temporarily coarsen their data, exact match on these coarsened data, and then run their analysis on the uncoarsened, matched data. Coarsened exact matching bounds the degree of model dependence and causal effect estimation error by ex ante user choice, is monotonic imbalance bounding (so that reducing the maximum imbalance on one variable has no effect on others), does not require a separate procedure to restrict data to common support, meets the congruence principle, is approximately invariant to measurement error, balances all nonlinearities and interactions in sample (i.e., not merely in expectation), and works with multiply imputed datasets. Other matching methods inherit many of the coarsened exact matching method's properties when applied to further match data preprocessed by coarsened exact matching. The cem command implements the coarsened exact matching algorithm in Stata.
authors:
- Matthew Blackwell
- Stefano Iacus
- Gary King
- Giuseppe Porro
date: '2009-01-01'
links:
- type: pdf
  url: files/cemStata_0.pdf
- type: source
  url: https://doi.org/10.1177/1536867X0900900402
publication: The Stata Journal, 9(4), 524–546
publication_types:
- journal_article
title: 'CEM: Coarsened Exact Matching in Stata'
---
