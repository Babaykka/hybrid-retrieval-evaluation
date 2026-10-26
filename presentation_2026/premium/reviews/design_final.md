# Candidate v1: Independent Visual QA

## Verdict

**Revise before the PDF pass.** Two high-priority chart defects remain: slide 08 rounds fractional ROC-axis ticks to integers, and slide 10 visually hides the confidence intervals promised in its caption. The overall design is substantially clearer than the earlier deck. No widespread clipping, off-canvas content, or connector/text collisions were observed in the 18 PNGs.

Keep the intentional **13 core + 5 backup** structure. The current speaker script totals **810 seconds, or 13:30**. This review does not request more slides or a return to the previous structure.

## High-Priority Fixes

### V01 [P1] Slide 08: Incorrect ROC tick labels

The false-positive-rate axis visibly reads **0, 0, 0, 1, 1, 1**, although positions represent 0.0 through 1.0 in 0.2 increments. This prevents quantitative reading of the curve. The actual PPTX confirms a bottom-axis number format of `0` in `ppt/slides/charts/chart2.xml`; this is not merely an ambiguous screenshot.

**Fix:** explicitly set the horizontal axis to `0.0`, with bounds 0 and 1 and major step 0.2. Retain the same fractional data. Verify labels **0.0, 0.2, 0.4, 0.6, 0.8, 1.0** in the next PNG and PDF. Do not multiply data by 100 unless both the axis and labels switch consistently to percentages.

### V02 [P1] Slide 10: Confidence intervals are visually swallowed by markers

The caption promises 95% query-bootstrap intervals, but the plot reads as five unqualified dots. The PPTX contains the correct five interval segments in `ppt/slides/charts/chart4.xml`; they are not missing data. Their short vertical extent, uncapped ends, and same-color 8-point mean markers make the intervals effectively indistinguishable at the current figure size.

**Fix:** reduce mean markers to approximately 4-5 points and add short horizontal end caps to each exact CI endpoint. Give the interval stroke sufficient contrast and keep markers above the interval lines. A taller or full-width plot can improve legibility further. Do not inflate interval lengths or change the axis scale silently. If precise interval extents still cannot be read, retain capped intervals and add a compact endpoint annotation, for example **K=200: +0.0088 [0.0082, 0.0095]**. Confirm all five intervals visually, not only their XML presence.

## Other Actionable Fixes

### V03 [P2] Slide 10: Contrast direction and side-callout placement

The vertical title says only "NDCG@10 difference", without defining the subtraction. In addition, the **E5 higher** negative-result callout sits beside the positive region, while **RRF higher** sits beside the negative region. The attached numbers are correct, but the spatial arrangement works against the plot.

**Fix:** visibly define **RRF(L=K) minus E5**. Prefer direct annotations at K=10 and K=200, or place the positive summary above the negative one. Label the zero reference as **0**. Keep the existing adjacent condition **assessment depth K = RRF input depth L** and the single-judge qualification.

### V04 [P2] Slide 08: Unexplained highlighted operating point

The orange dot on the ROC curve has no visible label. The F1 caption mentions a validation threshold but does not identify the dot as that threshold's test-set operating point.

**Fix:** add a short nearby label **Validation-selected threshold**, placed in open plot space with a short leader if necessary. The encoded point is approximately **FPR 0.280, TPR 0.902**. A threshold selected on validation must not appear to have been optimized on the test ROC. Preserve "177 held-out queries; 5,002 pairs" and the inherited-label qualification.

### V05 [P2] Slide 13: Put the metric and evidence condition into the conclusion itself

The large **E5: 0.488 to 0.879** omits the metric name. The second conclusion says coverage can "change their order" immediately after "Fixed RRF and E5 rankings", which can sound as though the supposedly fixed document order changed. The footer names human judgments and pseudo-labels together without assigning them to their respective claims.

**Fix:** label the first finding **E5 NDCG@10: 0.488 to 0.879**. Label the second finding explicitly as a **measured system comparison under single-judge pseudo-labels**, for example: "Assessment coverage can reverse the measured comparison under this judge's pseudo-labels." Keep **fixed output rankings** and **selected MS MARCO pools** visible. Two compact lines are preferable to shrinking the conclusion text.

### V06 [P2] Slide 15: Metric labels run together

The bottom line visually runs **Recall 0.902** into **F1 0.875**. The source shape uses repeated spaces inside one text string, which do not provide reliable visual separation after rendering.

**Fix:** use three independently aligned native text groups on one baseline, with a consistent 24-32 px gap at the 1280 px design size. Keep each metric name attached to its own value. Do not add cards or separators that compete with the confusion matrix.

### V07 [P2] Slides 16-17: Backup tables need self-contained metric labels

Slide 16 shortens the metric to "NDCG", omitting the cutoff. Slide 17 displays the manual comparison values without an on-slide metric or label-set description. Backup slides commonly appear out of sequence during questions.

**Fix:** specify **NDCG@10** in slide 16's metric headers or in one shared table caption; retain the distinction between L=K and L=200. Add **Human-label NDCG@10** above slide 17's table. Do not change the numerical precision merely to create visible differences between the sensitivity columns.

## Lower-Priority Polish

- **Slide 05 [P3]:** change "Relevant judgments per query" to **Mean positive judgments per query**, making the aggregation explicit. Align the two positive-pair count captions on the same baseline; the right caption is currently lower despite its heading fitting on one line.
- **Slide 11 [P3]:** clarify that **14.4%** refers to **returned RRF top-10 pairs**, rather than all retrieved pairs. The percentage is consistent with 145,643 / 1,010,930. Keep the zero-gain qualification and do not imply all uncovered pairs are relevant.
- **Slides 08-11 [P3]:** four consecutive figures repeat a left chart/right large-number composition. The simplest improvement is to make slide 10's corrected interval plot wider and directly labeled. This also addresses V02 and V03 without a cosmetic redesign of the whole deck.

## Individual Slide Log

| PNG | Result of individual visual inspection |
| --- | --- |
| slide-01.png | Pass. Strong dark opening, readable title/subtitle, all three authors, no email, no image/text collision. Keep the illustrative cover subordinate to the title. |
| slide-02.png | Pass. The changed relevance judgment is easy to locate; shortened-paraphrase wording and unjudged/negative distinction are visible. IDs remain prominent but are not a blocking defect. |
| slide-03.png | Pass. Human and model populations have explicit headings and contrasting colors. Long title fits in the inspected render. |
| slide-04.png | Pass. Orthogonal input routes join cleanly, arrowheads stop at operation boundaries, and the known-answer condition is visible. No connector crosses a label. |
| slide-05.png | Minor polish. Readable comparison and correct pool qualification; align the count captions and name the mean. |
| slide-06.png | Pass. Bars use a zero baseline and a full 0-1 scale. Endpoint values are readable; the E5 paired interval is visibly distinguished from absolute means. Shared-denominator condition remains visible. |
| slide-07.png | Pass. Straight routing, joint text input, excluded reference/rank/score inputs, and model-prediction status are clear. The simplified functional blocks are acceptable here. |
| slide-08.png | Fix V01 and V04. ROC x-axis formatting is wrong and the threshold marker lacks a label. |
| slide-09.png | Pass. Count axes and endpoints are readable, predictions use a different series color, and zero-positive queries/fixed judge/fixed threshold are stated. |
| slide-10.png | Fix V02 and V03. Correct data are not sufficiently communicated by the interval rendering and sign labeling. |
| slide-11.png | Pass with minor label refinement. Fixed top-200 inputs and unchanged output rankings are prominent; the zero reference and pool-exclusion explanation are clear. |
| slide-12.png | Pass. Sensitivity table and unmeasured inter-assessor/independent-human-validation limitations are readable and not clipped. |
| slide-13.png | Fix V05. Dark closing layout works, but attach the metric and pseudo-label condition to the respective conclusions. |
| slide-14.png | Pass. Paired effects and intervals are clearly aligned; the table is readable without a heavy grid. |
| slide-15.png | Fix V06. Confusion-matrix rows/columns and inherited mapping qualification are clear; the summary metric line needs proper spacing. |
| slide-16.png | Fix V07. Six-column table fits and numeric columns remain readable; specify the cutoff. |
| slide-17.png | Fix V07. Table, population exclusion, and independence caveat are readable; label the manual metric and judgment source. |
| slide-18.png | Pass. Proposed input and planned evaluation are explicit; no achieved result is implied. Connector clears all text. |

## Verification Scope

All 18 supplied PNGs were opened individually, not assessed only from a contact sheet. The Presentation skill's visual guidance was reread. Checks used the actual `presentation_2026/premium/build/candidate-v1.pptx`, its chart XML, corresponding layout JSON, current speaker script, and verified full-set summaries for the small contrasts and coverage denominator. The probe was ignored.

Reviewed PPTX SHA-256: `4e4efacdc3edf09b25017ed499307d7375f73a7a4c0faeed58fa8b7110e6eae3`.

No deck, builder, scientific source, or assets were edited. This report is the only created file. Native PowerPoint behavior and the forthcoming PDF were not visually tested in this pass. After fixes, prioritize PDF reinspection of slides **08, 10, 13, 15, 16, 17**, then scan all pages for font substitution, caption wrapping, and lost CI caps.
