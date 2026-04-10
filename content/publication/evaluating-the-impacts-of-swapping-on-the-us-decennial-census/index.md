---
title: "Evaluating the Impacts of Swapping on the US Decennial Census"
date: "2025-01-01"
authors:
  - "María Ballesteros"
  - "Cynthia Dwork"
  - "Gary King"
  - "Conlan Olson"
  - "Manish Raghavan"
publication_types:
  - "conference_proceedings"
abstract: "To meet its dual burdens of providing useful statistics and ensuring privacy of individual respondents, the US Census Bureau has for decades introduced some form of “noise” into published statistics. Initially, they used a method known as “swapping” (1990–2010). In 2020, they switched to an algorithm called TopDown that ensures a form of Differential Privacy. While the TopDown algorithm has been made public, no implementation of swapping has been released and many details of the deployed swapping methodology deployed have been kept secret. Further, the Bureau has not published (even a synthetic) “original” dataset and its swapped version. It is therefore difficult to evaluate the effects of swapping, and to compare these effects to those of other privacy technologies. To address these difficulties we describe and implement a parameterized swapping algorithm based on Census publications, court documents, and informal interviews with Census employees. With this implementation, we characterize the impacts of swapping on a range of statistical quantities of interest. We provide intuition for the types of shifts induced by swapping and compare against those introduced by TopDown. We find that even when swapping and TopDown introduce errors of similar magnitude, the direction in which statistics are biased need not be the same across the two techniques. More broadly, our implementation provides researchers with the tools to analyze and potentially correct for the impacts of disclosure avoidance systems on the quantities they study."
links:
  - type: pdf
    url: "/files/cslaw25-final22_1.pdf"
---
