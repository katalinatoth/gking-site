---
title: 'CEM: Coarsened Exact Matching Software'
date: '2009-01-01'
authors:
- Stefano Iacus
- Gary King
- Giuseppe Porro
---

<article class="node node--type-hwp-page node--view-mode-full" lang="en">
<div class="hwp-page-title hwp-bg-dark-base">
<div class="hwp-container hwp-container-px hwp-py-32">
</div>
</div>
<div class="hwp-container hwp-w-full hwp-py-32 lg:hwp-py-64">
<div class="hwp-flex hwp-flex-col hwp-flex-1 hwp-overflow-hidden">
<div class="hwp-mb-16 hwp-container-px">
<div class="hwp-text-block field field--name-field-hwp-body field--type-text-long field--label-hidden"><h3>Authors: Stefano Iacus, Gary King, Giuseppe Porro</h3><p>This program is designed to improve the estimation of causal effects via an extremely powerful method of matching that is widely applicable and exceptionally easy to understand and use (if you understand how to draw a histogram, you will understand this method). The program implements the Coarsened Exact Matching (CEM) algorithm described in:</p><blockquote><p><em>"</em><a href="/publication/causal-inference-without-balance-checking-coarsened-exact-matching/"><em>Causal Inference Without Balance Checking: Coarsened Exact Matching</em></a><em>" (Political Analysis, 2012) and "</em><a href="/publication/multivariate-matching-methods-that-are-monotonic-imbalance-bounding/"><em>Multivariate Matching Methods That are Monotonic Imbalance Bounding</em></a><em>" (JASA, 2011), "</em><a href="/publication/cem-coarsened-exact-matching-in-stata/"><em>CEM: Coarsened Exact Matching in Stata</em></a><em>" (Stata Journal, 2009, with Matthew Blackwell), "</em><a href="#"><em>CEM: Software for Coarsened Exact Matching</em></a><em>." (Journal of Statistical Software, 2009), "</em><a href="#"><em>A Theory of Statistical Inference for Matching Methods in Causal Research</em></a><em>" (Political Analysis, 2019). See also </em><a href="https://docs.google.com/document/d/1xQwyLt_6EXdNpA685LjmhjO20y5pZDZYwe2qeNoI5dE/edit"><em>An Explanation of CEM Weights</em></a><em>.</em></p></blockquote><div class="align-right hwp-media hwp-media--full-width">
<div class="field field--name-field-media-image field--type-image field--label-hidden"> <img alt="old photo of gathering at table" height="165" loading="lazy" src="/images/software-import/cem.jpg" width="200"/>
</div>
</div>
<p>Matching is a nonparametric method of preprocessing data to control for some or all of the potentially confounding influence of pretreatment control variables by reducing imbalance between the treated and control groups. After preprocessing in this way, any method of analysis that would have been used without matching can be applied to estimate causal effects, although some methods will have even better properties. CEM is a Monotonoic Imbalance Bounding (MIB) matching method --- which means that the balance between the treated and control groups is chosen by the user ex ante rather than discovered through the usual laborious process of checking after the fact and repeatedly reestimating, and so that adjusting the imbalance on one variable has no effect on the maximum imbalance of any other. CEM also strictly bounds through ex ante user choice both the degree of model dependence and the average treatment effect estimation error, eliminates the need for a separate procedure to restrict data to common empirical support, meets the congruence principle, is robust to measurement error, works well with multiple imputation methods for missing data, can be completely automated, and is extremely fast computationally even with very large data sets. After preprocessing data with CEM, the analyst may then use a simple difference in means or whatever statistical model they would have applied without matching. CEM also works well for multicategory treatments, determining blocks in experimental designs, and evaluating extreme counterfactuals.</p><p><em>CEM has officially been "Qualified for Scientific Use" by the </em><a href="https://www.fda.gov/"><em>U.S. Food and Drug Administration</em></a><em>.</em></p><ul><li><strong>Reporting Bugs and Issues: </strong>Please use our Github Issue <a href="https://github.com/IQSS/cem/issues/new">form</a>.<br/> </li><li><strong>Questions and feature requests:</strong> Discuss the software on our Discussions <a href="https://github.com/IQSS/cem/discussions">page</a>.<br/> </li><li><strong>CEM Package for R:</strong><ul><li>Can be installed from CRAN: <span>install.packages("cem")</span></li><li>To install, from R:<br/><span>library(devtools)</span>; <span>(install.packages("devtools")</span> first if necessary)<br/><span>install_github("</span><a href="https://github.com/IQSS/cem.git"><span>https://github.com/IQSS/cem.git</span></a><span>")</span></li><li>For documentation, from R, type <span>library(cem)</span>, and then ?cem (or the published <a href="#"><em>Journal of Statistical Software</em> version</a>)</li><li>Github repository: <a href="https://github.com/IQSS/cem">https://github.com/IQSS/cem</a><br/> </li></ul></li><li><strong>CEM in MatchIt for R</strong>: Most of the features of CEM are also available through the R Package <a href="https://kosukeimai.github.io/MatchIt/index.html">MatchIt: Nonparametric Preprocessing for Parametric Causal Inference</a>.<br/> </li><li><strong>CEM for SAS, by Stefano Verzillo, Paolo Berta, and Matteo Bossi</strong><br/>Download the <a href="https://github.com/IQSS/garyking_website_files/blob/main/macro_cem_updated_new_feb17.sas">SAS CEM Macro</a> (Version: 2/2017, Questions: <a href="mailto:stefano.verzillo@ec.europa.eu">stefano.verzillo@ec.europa.eu</a>)<br/>See also JSCS article: "<a href="http://www.tandfonline.com/doi/full/10.1080/00949655.2016.1203433">%CEM: A SAS macro to perform coarsened exact matching</a>"<br/> </li><li><strong>CEM for Stata</strong> (version 10 or later):<ul><li>To install, type: <br/><span>net from </span><a href="https://www.mattblackwell.org/files/stata"><span>https://www.mattblackwell.org/files/stata</span></a><br/><span>net install cem</span></li><li>You can also install from the SSC:<br/><span>ssc install cem</span></li><li>For documentation, type <span>help cem</span> or download <a href="/">PDF</a> (or the published version in <em>The Stata Journal</em>: <a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="67273085-bd68-4d22-8214-1d32a803918d" href="#" title="cemStata_0.pdf">PDF</a>).<br/> </li></ul></li><li><strong>CEM for SPSS: </strong><a href="http://projects.iq.harvard.edu/cem-spss/"><strong>Website</strong></a><br/> </li><li><strong>CEM for SQL (works with billions of observations):</strong><span><strong> </strong></span><a href="http://arxiv.org/abs/1609.03540"><span>ZaliQL</span></a><br/> </li><li><span><strong>CEM for Python:</strong> </span><a href="https://github.com/lewisbails/cem"><span>on github</span></a><span> </span></li></ul></div>
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
              Software Project
            </a>
</li>
</ul>
</div>
</div>
</div>
</div>
</article>
