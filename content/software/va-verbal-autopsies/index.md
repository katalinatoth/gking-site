---
title: 'VA: Verbal Autopsies'
date: '2008-01-01'
authors:
- Gary King
- Ying Lu
---

<article class="node node--type-hwp-page node--view-mode-full" lang="en">
<div class="hwp-page-title hwp-bg-dark-base">
<div class="hwp-container hwp-container-px hwp-py-32">
</div>
</div>
<div class="hwp-container hwp-w-full hwp-py-32 lg:hwp-py-64">
<div class="hwp-flex hwp-flex-col hwp-flex-1 hwp-overflow-hidden">
<div class="hwp-mb-16 hwp-container-px">
<div class="hwp-text-block field field--name-field-hwp-body field--type-text-long field--label-hidden"><h3 id="content"><span>Authors: </span><a href="/gking-site/">Gary King</a><span>, </span>Ying Lu</h3><p>VA is an easy-to-use R program that automates the analysis of verbal autopsy data. These data are widely used for estimating cause-specific mortality in areas without medical death certification.</p><div class="align-left hwp-media hwp-media--full-width">
<div class="field field--name-field-media-image field--type-image field--label-hidden"> <img alt="va" height="280" loading="lazy" src="/gking-site/images/software-import/va.jpg" width="200"/>
</div>
</div>
<p>Data on symptoms reported by caregivers along with the cause of death are collected from a medical facility, and the cause-of-death distribution is estimated in the population where only symptom data are available. Current approaches analyze only one cause at a time, involve assumptions judged difficult or impossible to satisfy, and require expensive, time consuming, or unreliable physician reviews, expert algorithms, or parametric statistical models. By generalizing current approaches to analyze multiple causes, <a href="/gking-site/files/abs/vamc-abs.shtml">King and Lu (2008)</a> show how most of difficult assumptions underlying existing methods can be dropped. These generalizations, which we implement here, also make physician review, expert algorithms, and parametric statistical assumptions unnecessary. While no method of analyzing verbal autopsy data can give accurate estimates in all circumstances, the procedure offered is conceptually simpler, less expensive, more general, as or more replicable, and easier to use in practice.</p><p>More generally, the software takes as input a multicategory variable <em>D</em>, and a set of dichotomous variables <em><strong>S</strong></em> (cause of Death and Symptoms, respectively, in verbal autopsy applications). Both variables exist in one data set (a hospital in the application) but only <em><strong>S</strong></em> exists in the population of interest. The goal of the procedure is to estimate the probability distribution (or histogram) of <em>D</em> in the population of interest.</p><p>For more information, see Gary King and Ying Lu. <span>Verbal Autopsy Methods with Multiple Causes of Death</span> (<span>Paper:</span> <a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="56436237-affa-46e2-8bbc-5ff3314897ce" href="#" title="vamc.pdf">PDF</a>)</p><ul><li><strong>Reporting Bugs and Issues: </strong>Please use our Github Issue <a href="https://github.com/iqss-research/VA-package/issues/new">form.</a><br/> </li><li><strong>Questions and feature requests:</strong> Discuss the software on our Discussions <a href="https://github.com/iqss-research/VA-package/discussions">page</a>.<br/> </li><li><strong>VA for R:</strong><ul><li>To install: first, install and load the <span>devtools</span> library. Then, <span>install_github("iqss-research/va-package")</span>.</li><li>For documentation see this <a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="b62ca347-2b8f-477f-8964-4684b6e66be4" href="#" title="va.pdf">PDF</a>.</li><li>For built-in documentation in R: <span>library(VA)</span>, and then <span>?va</span></li><li>Github repository: <a href="https://github.com/iqss-research/VA-package">https://github.com/iqss-research/VA-package</a><br/> </li></ul></li><li><span><strong>License:</strong></span> Creative Commons Attribution- Noncommercial-No Derivative Works 3.0 License, for academic use only. A commercial (and industrial strength) version has been built by, and licensed to, <a href="http://crimsonhexagon.com/">Crimson Hexagon</a></li></ul><h2 id="columns">Software Releases</h2><p><a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="8099dd9e-d2eb-480d-8dc4-a37d3554d279" href="/gking-site/software/yourcast/" title="YourCast: Time Series Cross-Sectional Forecasting with Your Assumptions"><span>YourCast: Time Series Cross-Sectional Forecasting with Your Assumptions</span></a></p><p><a href="#"><span>1.6</span></a><span> Sep 4 2013</span><br/><a href="https://github.com/IQSS/garyking_website_files/blob/main/YourCast_1.6.tar.gz"><span>Download</span></a><span> (2.37 MB)</span></p><p><a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="520940fe-ba26-40fc-8ef7-df7e04e6e61d" href="#" title="AutoCast: Automated Bayesian Forecasting with YourCast"><span>AutoCast: Automated Bayesian Forecasting with YourCast</span></a></p><p><a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="ce34e5e6-023d-44c7-a582-8dd91f6dc5d3" href="#" title="AutoCast: Automated Bayesian Forecasting with YourCast 0.1-10"><span>0.1-10</span></a><span> Mar 18 2011</span><br/><a href="https://github.com/IQSS/garyking_website_files/blob/main/AutoCast_0.1-10.tar.gz"><span>Download</span></a><span> (981.89 KB)</span></p><p><a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="4d948acf-ae22-411b-b14a-3db4be4716f9" href="#" title="Maxlik"><span>Maxlik</span></a></p><p><a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="5ddb8c9c-f856-4c6e-83fb-8d869cc6d835" href="#" title="Maxlik 1.0:dos-exe"><span>1.0:dos-exe</span></a><span> Jul 7 1998</span><br/><a href="https://github.com/IQSS/garyking_website_files/blob/main/ml.exe_.zip"><span>Download</span></a><span> (141.85 KB)</span></p></div>
</div>
<div class="hwp-news-footer hwp-pt-24 lg:hwp-pt-64">
<div class="field field--name-field-hwp-file-upload field--type-entity-reference field--label-hidden">
<div></div>
</div>
<div class="page-tags">
<span class="hwp-mb-16 hwp-block">See also:</span>
<ul class="hwp-news-footer__tags hwp-flex hwp-flex-wrap hwp-gap-16 hwp-mb-24">
<li class="max-sm:hwp-w-full">
<a class="hwp-button-tag hwp-button-tag--dark" href="#">
              Software Project
            </a>
</li>
<li class="max-sm:hwp-w-full">
<a class="hwp-button-tag hwp-button-tag--dark" href="#">
              VA: Verbal Autopsy Software
            </a>
</li>
<li class="max-sm:hwp-w-full">
<a class="hwp-button-tag hwp-button-tag--dark" href="#">
              Software Project
            </a>
</li>
</ul>
</div>
</div>
</div>
</div>
</article>
