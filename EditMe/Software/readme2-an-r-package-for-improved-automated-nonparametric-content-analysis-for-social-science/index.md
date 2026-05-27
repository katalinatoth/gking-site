---
title: "Readme2: An R Package for Improved Automated Nonparametric Content Analysis for Social Science"
date: "2018-01-01"
aliases:
  - /scholar_software/readme2-an-r-package-for-improved-automated-nonparametric-content-analysis-for-social-science/
authors:
  - "Connor T. Jerzak"
  - "Gary King"
  - "Anton Strezhnev"
links:
  - type: site
    url: "https://github.com/iqss-research/readme-software"
summary: |
  An R package for estimating category proportions in an unlabeled set of documents given a labeled set, by implementing the method described in Jerzak, King, and Strezhnev (2023). This method is meant to improve on the ideas in Hopkins and King (2010), which introduced a quantification algorithm to estimate category proportions without directly classifying individual observations. This version of the software refines the original method by implementing a technique for selecting optimal textual features in order to minimize the error of the estimated category proportions. Automatic differentiation, stochastic gradient descent, and batch re-normalization are used to carry out the optimization. Other pre-processing functions are available, as well as an interface to the earlier version of the algorithm for comparison. The package also provides users with the ability to extract the generated features for use in other tasks.

  Some scholars build models to classify documents into chosen categories. Others, especially social scientists who tend to focus on population characteristics, instead usually estimate the proportion of documents in each category—using either parametric "classify-and-count" methods or "direct" nonparametric estimation of proportions without individual classification. Unfortunately, classify-and-count methods can be highly model dependent or generate more bias in the proportions even as the percent of documents correctly classified increases. Direct estimation avoids these problems, but can suffer when the meaning of language changes between training and test sets or is too similar across categories. The underlying approach includes and optimizes continuous text features, along with a form of matching adapted from the causal inference literature.
---

An R package for estimating category proportions in an unlabeled set of documents given a labeled set, by implementing the method described in Jerzak, King, and Strezhnev (2023). This method is meant to improve on the ideas in Hopkins and King (2010), which introduced a quantification algorithm to estimate category proportions without directly classifying individual observations. This version of the software refines the original method by implementing a technique for selecting optimal textual features in order to minimize the error of the estimated category proportions. Automatic differentiation, stochastic gradient descent, and batch re-normalization are used to carry out the optimization. Other pre-processing functions are available, as well as an interface to the earlier version of the algorithm for comparison. The package also provides users with the ability to extract the generated features for use in other tasks.

Some scholars build models to classify documents into chosen categories. Others, especially social scientists who tend to focus on population characteristics, instead usually estimate the proportion of documents in each category—using either parametric "classify-and-count" methods or "direct" nonparametric estimation of proportions without individual classification. Unfortunately, classify-and-count methods can be highly model dependent or generate more bias in the proportions even as the percent of documents correctly classified increases. Direct estimation avoids these problems, but can suffer when the meaning of language changes between training and test sets or is too similar across categories. The underlying approach includes and optimizes continuous text features, along with a form of matching adapted from the causal inference literature.
