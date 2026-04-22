---
title: 'VA: Verbal Autopsies'
date: '2008-01-01'
authors:
- Gary King
- Ying Lu
---

{{< figure src="/images/software-import/va.jpg" alt="VA software" width="200" >}}

VA is an easy-to-use R program that automates the analysis of verbal autopsy data. These data are widely used for estimating cause-specific mortality in areas without medical death certification.

Data on symptoms reported by caregivers along with the cause of death are collected from a medical facility, and the cause-of-death distribution is estimated in the population where only symptom data are available. Current approaches analyze only one cause at a time, involve assumptions judged difficult or impossible to satisfy, and require expensive, time consuming, or unreliable physician reviews, expert algorithms, or parametric statistical models. By generalizing current approaches to analyze multiple causes, [King and Lu (2008)](/publication/verbal-autopsy-methods-with-multiple-causes-of-death/) show how most of the difficult assumptions underlying existing methods can be dropped. These generalizations, which we implement here, also make physician review, expert algorithms, and parametric statistical assumptions unnecessary. While no method of analyzing verbal autopsy data can give accurate estimates in all circumstances, the procedure offered is conceptually simpler, less expensive, more general, as or more replicable, and easier to use in practice.

More generally, the software takes as input a multicategory variable *D*, and a set of dichotomous variables ***S*** (cause of Death and Symptoms, respectively, in verbal autopsy applications). Both variables exist in one data set (a hospital in the application) but only ***S*** exists in the population of interest. The goal of the procedure is to estimate the probability distribution (or histogram) of *D* in the population of interest.

For more information, see Gary King and Ying Lu, ["Verbal Autopsy Methods with Multiple Causes of Death"](/publication/verbal-autopsy-methods-with-multiple-causes-of-death/).

- **Reporting bugs and issues:** Please use our [GitHub Issues form](https://github.com/iqss-research/VA-package/issues/new).
- **Questions and feature requests:** Discuss the software on our [Discussions page](https://github.com/iqss-research/VA-package/discussions).
- **VA for R:**
    - To install: first, install and load the `devtools` library. Then, `install_github("iqss-research/va-package")`.
    - For built-in documentation in R: `library(VA)`, and then `?va`.
    - GitHub repository: <https://github.com/iqss-research/VA-package>.
- **License:** Creative Commons Attribution–Noncommercial–No Derivative Works 3.0 License, for academic use only. A commercial (and industrial-strength) version has been built by, and licensed to, Crimson Hexagon.
