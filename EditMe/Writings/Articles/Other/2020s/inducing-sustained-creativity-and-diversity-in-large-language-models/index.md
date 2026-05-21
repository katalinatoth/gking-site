---
title: "Inducing Sustained Creativity and Diversity in Large Language Models"
url: /quest/
aliases:
  - /publication/inducing-sustained-creativity-and-diversity-in-large-language-models/
date: 2026-03-01
authors:
  - Queenie Luo
  - Gary King
  - Michael Puett
  - Michael D. Smith
publication_types:
  - "article-journal"
abstract: |-
  We address a not-widely-recognized subset of exploratory search, where a user sets out on a typically long "search quest" for the perfect wedding dress, overlooked research topic, killer company idea, etc. The first few outputs of current large language models (LLMs) may be helpful but only as a start, since the quest requires learning the search space and evaluating many diverse and creative alternatives along the way. Although LLMs encode an impressive fraction of the world's knowledge, common decoding methods are narrowly optimized for prompts with correct answers and thus return mostly homogeneous and conventional results. Other approaches, including those designed to increase diversity across a small set of answers, start to repeat themselves long before search quest users learn enough to make final choices, or offer a uniform type of "creativity" to every user asking similar questions. We develop a novel, easy-to-implement decoding scheme that induces sustained creativity and diversity in LLMs, producing as many conceptually unique results as desired, even without access to the inner workings of an LLM's vector space. The algorithm unlocks an LLM's vast knowledge, both orthodox and heterodox, well beyond modal decoding paths. With this approach, search quest users can more quickly explore the search space and find satisfying answers.
links:
  - type: pdf
    url: "files/Inducing-Sustained-Creativity-LLM.pdf"
  - type: appendix
    url: "files/Inducing-Sustained-Creativity-LLM-supplement.pdf"
    label: Appendix
---

<div class="not-prose" style="overflow-x:auto;width:100%;margin:1rem 0 0;">
<img src="{{< staticrel "files/inducing-sustained-creativity/RD-1.5x.gif" >}}" width="1500" height="300" alt="Animation: ordinary decoding versus recoding decoding (RD)" style="max-width:100%;width:100%;height:auto;display:block;min-height:120px;" loading="lazy" />
</div>

<div class="not-prose" style="overflow-x:auto;margin-top:1rem;">
<img loading="lazy" src="{{< staticrel "files/inducing-sustained-creativity/SQ_0.jpg" >}}" width="4988" height="7964" alt="Visual comparison" style="max-width:100%;height:auto;display:block;" />
</div>
