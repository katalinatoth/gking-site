---
title: 'WhatIf: Software for Evaluating Counterfactuals'
date: '2005-01-01'
authors:
- Heather Stoll
- Gary King
- Langche Zeng
links:
  - type: site
    url: "https://CRAN.R-project.org/package=WhatIf"
---

<article class="node node--type-hwp-page node--view-mode-full" lang="en">
<div class="hwp-page-title hwp-bg-dark-base">
<div class="hwp-container hwp-container-px hwp-py-32">
</div>
</div>
<div class="hwp-container hwp-w-full hwp-py-32 lg:hwp-py-64">
<div class="hwp-flex hwp-flex-col hwp-flex-1 hwp-overflow-hidden">
<div class="hwp-mb-16 hwp-container-px">
<div class="hwp-text-block field field--name-field-hwp-body field--type-text-long field--label-hidden"><p id="content"><span>Authors: </span><a href="http://www.polsci.ucsb.edu/faculty/hstoll/">Heather Stoll</a><span>, </span><a href="/gking-site/">Gary King</a><span>, </span><a href="http://polisci.ucsd.edu/faculty/zeng.html">Langche Zeng</a></p><p>Inferences about counterfactuals are essential for prediction, answering "what if" questions, and estimating causal effects. However, when the counterfactuals posed are too far from the data at hand, conclusions drawn from well-specified statistical analyses become based largely on speculation hidden in convenient modeling assumptions that few would be willing to defend.</p><p> </p><span id="sort-hint" style="display:none;">Sort</span><div class="hwp-table-wrap"><table class="hwp-table js-hwp-table dataTable" tabindex="0"><tbody><tr><td><div class="hwp-table__cell-content"><div class="hwp-media hwp-media--full-width">
<div class="field field--name-field-media-image field--type-image field--label-hidden"> <img alt="pilot" height="177" loading="lazy" src="/gking-site/images/software-import/whatif.jpg" width="250"/>
</div>
</div>
<p><em>What would happen if pigs could fly?</em><span>The first known attempt to answer this question was in 1909 by J.T.C. Moore-Brabazon, who earlier the same year was the first British pilot to fly in Britain. On the left is Moore-Brabazon in his personal French-built Voisin aero plane. On the right is a pig in a wicker basket behind a sign that says "I am the first pig to fly."</span></p></div></td><td><div class="hwp-table__cell-content"><p><span>Unfortunately, standard statistical approaches assume the veracity of the model rather than revealing the degree of model-dependence, which makes this problem hard to detect. WhatIf offers easy-to-apply methods to evaluate counterfactuals that do not require sensitivity testing over specified classes of models. If an analysis fails the tests offered here, then we know that substantive inferences will be sensitive to at least some modeling choices that are not based on empirical evidence, no matter what method of inference one chooses to use. WhatIf is also used to identify the areas of common support in causal inference. It is implemented in </span><a class="hwp-link" data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="09b04a36-4d6b-4f6f-b0af-17dd09f2aa2d" href="#" title="MatchIt: Nonparametric Preprocessing for Parametric Causal Inference"><span>MatchIt</span></a><span> and can easily process </span><a class="hwp-link" data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="93026193-f7fe-4ef4-aab5-235b2a7b35f9" href="#" title="Zelig: Everyone's Statistical Software"><span>Zelig</span></a><span> output objects so that counterfactuals can be evaluated, prior to computing quantities of interest, with only one additional command.</span></p><p><span>WhatIf implements the methods for evaluating counterfactuals discussed in Gary King and Langche Zeng, 2006, "</span><a class="hwp-link" href="/gking-site/files/abs/counterft-abs.shtml"><span>The Dangers of Extreme Counterfactuals</span></a><span>," </span><em><span>Political Analysis</span></em><span> 14 (2): 131-159; and Gary King and Langche Zeng, 2007, "</span><a class="hwp-link" href="/gking-site/files/abs/counterf-abs.shtml"><span>When Can History Be Our Guide? The Pitfalls of Counterfactual Inference</span></a><span>," </span><em><span>International Studies Quarterly</span></em><span> 51 (March): 183-210.</span></p></div></td></tr></tbody></table><div aria-live="polite" class="hwp-visually-hidden" id="sort-note"></div></div><ul><li><strong>Reporting Bugs and Issues: </strong>Please use our Github Issue <a href="https://github.com/IQSS/whatif/issues/new">form.</a><br/> </li><li><strong>Questions and feature requests:</strong> Discuss the software on our Discussions <a href="https://github.com/IQSS/whatif/discussions">page</a>.<br/> </li><li><span><strong>WhatIf for R:</strong></span><ul><li>Github: <a href="https://github.com/IQSS/WhatIf">https://github.com/IQSS/WhatIf</a></li><li><span>Installation directly from Github:  devtools::install_github("IQSS/WhatIf")</span></li><li><span>Documentation: </span><a href="http://r.iq.harvard.edu/docs/whatif/"><span>Read on-line</span></a><span> or </span><a href="http://r.iq.harvard.edu/docs/whatif/1.5-5/whatif.pdf"><span>Download PDF</span></a><br/> </li></ul></li><li><span><strong>Presentations on Whatif:</strong> Stoll:</span> <a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="277d081e-dd5c-4c1d-80ca-9bb6a492c8fa" href="#" title="2006_QMSS.ppt">PPT</a>, <span>King:</span> <a data-entity-substitution="canonical" data-entity-type="node" data-entity-uuid="a481128f-8f2f-4134-8151-f2a651a60d7e" href="#" title="cfmtlk.pdf">PDF</a></li></ul></div>
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
              WhatIf: Software for Evaluating Counterfactuals
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
