# Visual Release Verdict: v4

**APPROVED FOR VISUAL RELEASE. No blocking visual defects remain.**

All **18 actual-PDF pages** were inspected individually using `premium/build/pdf-render/final-01.png` through `final-18.png`. No unintended text overlap, clipping, missing chart series, or connector/text collisions were observed. The intentional **13 core + 5 backup** structure remains intact, with a current script allocation of **810 seconds (13:30)**.

This is the current release verdict. Earlier findings in `design_final.md` and `design_pdf_v3.md` describe historical builds and do not represent the status of this v4 PDF.

## Accepted Artifact

- PDF: `presentation_2026/premium/build/validated/validated-v4.pdf`
- SHA-256, verified again at completion: `10f3b286e40030b18ec0e163ba5a4ff93356282475abeda2b37941f0eb6021c7`
- PDF metadata: 18 pages, created 2026-09-21 00:36:33 MSK, LibreOffice 26.2.3.2 exporter.
- Evidence: the fresh `final-XX.png` PDF renders, not the v1 presentation renders, old `slide-XX.png` PDF renders, or intermediate repair images.

## Earlier Defects Closed

| Finding | Verified v4 outcome |
| --- | --- |
| ROC horizontal ticks rounded to integers | Closed. Page 08 displays 0.0 through 1.0 at the correct fractional positions. |
| Missing ROC operating point and chance diagonal | Closed. Page 08 shows the diagonal and exactly one coral operating point near FPR 0.28 / TPR 0.90, with no false coral point at the origin. The threshold now has a visible explanatory label. |
| Missing page-10 means and confidence intervals | Closed. All five means and their capped intervals render in the actual PDF. The negative K=10 result and four positive deeper settings are visible. The exact K=200 estimate and interval are also printed below the plot. |
| Unclear difference direction and contradictory right-side callout placement | Closed. Page 10 states RRF(L=K) minus E5, retains the K=L condition, labels the zero level, and removes the competing right-side callouts. |
| Undersized exported axis titles | Closed as a readability defect. Axis titles on 08, 10, and 11 are now readable. A minor wrap on 11 is noted below. |
| Dark PDF table grids | Closed. The final tables use restrained horizontal rules without the earlier black cell grid. |
| Conclusion lacks metric and evidence-source assignment | Closed. Page 13 names E5 NDCG@10 and separately identifies the fixed-ranking result under single-judge pseudo-labels. |
| Precision/recall/F1 text runs together | Closed. Page 15 has three clearly separated metric groups. |
| Backup metric labels incomplete | Closed. Page 16 specifies NDCG@10; page 17 identifies human-label NDCG@10 and the post-exclusion population. |

## Individual Page Check

| Page | Result |
| --- | --- |
| 01 | Pass. Cover title, three authors, affiliation, and illustration fit without collisions; no email. |
| 02 | Pass. Passage text, IDs, judgment columns, highlighted example, and qualification remain readable. |
| 03 | Pass. Distinct human/model populations, counts, and selected-pool scope fit. |
| 04 | Pass. Source routes and assessment connector clear all text; reference-assisted inputs remain explicit. |
| 05 | Pass. Mean aggregation is explicit and both positive-pair captions align. |
| 06 | Pass. Both bar series, all eight values, legend, paired-effect annotation, and evaluation conditions render. |
| 07 | Pass. Joint-input diagram and excluded inputs are readable; no connector collisions. |
| 08 | Pass. ROC curve, chance diagonal, one operating point, correct ticks, threshold label, and held-out scope all render. |
| 09 | Pass. Both depth-series lines and five points per series render, with units, legend, and query denominator visible. |
| 10 | Pass. Five means and capped intervals render; subtraction direction, zero reference, depth condition, and pseudo-label qualification are visible. |
| 11 | Pass with one nonblocking typography note. All five points and the connecting line render; fixed inputs, zero, top-10 denominator, and endpoint annotations are visible. |
| 12 | Pass. Sensitivity rows and limitations fit without overlap or clipping. |
| 13 | Pass. Metric name and evidence-source distinction are explicit; the revised conclusion fits the dark layout. |
| 14 | Pass. Four paired-effect rows, confidence intervals, and statistical caption are readable. |
| 15 | Pass. Confusion matrix, separated metrics, and inherited-target qualification fit. |
| 16 | Pass. Five depth rows and all six columns fit; metric cutoffs and both RRF input conditions remain legible. |
| 17 | Pass. Self-contained human-label metric heading, sensitivity table, population count, and independence caveat fit. |
| 18 | Pass. Proposed inputs and planned status remain clear; connector clears all text and no achieved performance is implied. |

## Nonblocking Observation

Page 11's vertical axis title wraps "difference" as "dif-" / "ference" across two rotated lines. It remains legible and does not overlap the tick labels or plot. This is a minor typographic blemish, not a release blocker. No missing data or series is associated with it.

## Scope And Closure

This closes the independent **visual** review against the identified v4 PDF. It does not assert an independent PowerPoint/Excel interaction test or a new statistical recomputation. Native chart editability and application-opening checks reported by the main implementer are separate from this actual-PDF visual acceptance.

Only `design_release.md` was created. No presentation source, builder, scientific manuscript, PPTX, PDF, image, or historical review was modified. No further visual work is required from this reviewer for this release.
