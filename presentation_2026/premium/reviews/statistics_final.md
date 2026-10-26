# Final Numerical QA: Validated v3

## Verdict

**Stored experimental numbers and all five embedded workbooks pass. The adjacent v3 PDF does not yet display all of the numerical evidence: slide 10's effect plot is blank, and interval/marker visibility needs correction.** No incorrect source-derived result, denominator, confidence interval value, table entry, or speaker-note numerical claim was found. The v1 ROC axis-format and coordinate-precision issues are resolved in the actual v3 package. No deck, builder, source data, or speaker script was edited in this review.

Scope: `premium/build/validated/validated-v3.pptx` and its adjacent PDF, checked after the original `candidate-v1.pptx` audit. All 18 slide/embedded-note numeric-token sequences are unchanged from audited v1. All cells in native tables 14-17 are unchanged. The five chart owners are exactly 6/8/9/10/11. All chart values were rechecked against corrected JSON, including the newly added CI cap series. The 13 main slides have a planned total of 810 seconds = 13 minutes 30 seconds; five appendix slides have zero planned time. This is a timing plan, not a measured rehearsal.

## Current Rendering Findings

### [P1] PDF slide 10 omits the five paired effects and all confidence intervals

The actual adjacent `validated-v3.pdf`, page 10, displays axes, text callouts, and the caption promising points with 95% intervals, but the plot contains no effect points or interval/cap strokes. This was visually checked from the PDF itself, then corroborated by inspecting its vector paths: there are no coral data drawings in the plot region. The corresponding PPTX chart contains the correct five effects, five vertical intervals, and ten cap series, and its workbook values match the caches. The data are present but the exported evidence is not visible.

**Action:** restore explicit visible effect markers and interval/cap strokes in the final output and re-export the PDF. The effect-marker definition in `ppt/slides/charts/chart4.xml` explicitly contains `c:marker/c:spPr/a:noFill`, while its series line is also no-fill/zero-width. Fix the marker styling and separately verify interval/cap export. The intervals have valid stroke definitions and data in XML, so their disappearance must not be dismissed as missing numeric inputs. No new calculation is required.

### [P2] PDF slides 8 and 11 also lose quantitative markers/intervals

- Page 8 shows the ROC curve but not the validation operating-point marker. The point (0.28017719, 0.90175219) exists in the native data, but its marker also has an explicit `a:noFill` and its line is disabled. The actual PDF has the teal ROC path but no coral operating-point drawing. Give that marker an explicit visible fill/outline if it is retained as evidence.
- Page 11 shows the connected fixed-input curve and its five filled point markers, but not the stored confidence-interval/cap series. PDF vector inspection finds the curve and five point drawings, with no interval/cap paths. The CI numbers themselves are correct. Either ensure those intervals survive export or avoid representing the final visual as if the intervals were present. Preserving the intended intervals is preferable.

These are final-output rendering issues, not changed experimental results. The initial builder PNGs are not sufficient evidence for the materialized PPTX-to-PDF conversion. Recheck the actual delivered PDF after the fix.

## V3 Workbook and Precision Checks

All five materialized workbooks were opened from the PPTX and compared cell-by-cell with the chart references/caches: **82 formula-linked ranges, 350 matching data cells, including 342 numeric cells.** No numeric cache/workbook value exceeds 15 significant digits. The new native CI caps use each corresponding lower/upper bound exactly, with graphical X endpoints at K-1.4 and K+1.4; they add no experimental observations.

Slide 8 now has `0.0` number format on both axes, limits 0-1, and major step 0.2. The actual PDF correctly prints 0.0, 0.2, 0.4, 0.6, 0.8, 1.0. Both ROC coordinate arrays, including the operating point, match the source rounded to eight decimals; all 80 vertices and the endpoints remain. The AUC callout is still **0.907**, sourced from the full-curve AUC **0.9069675618886842**. These two former issues are closed for v3.

## Resolved V1 Findings

### ROC X-axis tick labels in candidate-v1: resolved in v3

The horizontal axis uses number format `0` with ticks every 0.2. Both the PNG preview and `ppt/slides/charts/chart2.xml` show the consequence: labels **0, 0, 0, 1, 1, 1** rather than **0.0, 0.2, 0.4, 0.6, 0.8, 1.0**. The underlying coordinates are correct. Use format `0.0` for this axis, leaving the depth-chart axes integer-formatted.

The owner added `xformat` in `xy()` at lines 23-24 and the ROC call passed `xformat:'0.0'` at line 125. The actual v3 XML and PDF now confirm this correction; the older candidate's labels are retained here only as review history.

### ROC coordinate precision in candidate-v1: resolved in v3

The original candidate stored all 80 ROC X coordinates at full precision while Y coordinates were rounded to eight decimals. It contained 73 chart numeric literals exceeding 15 significant digits, all in the ROC chart. `layout.mjs:48` rounds both `values` and `xValues` to eight decimals; the v3 caches and workbooks now confirm the change. This was an export-policy issue, not a wrong empirical ROC curve.

- Exact full-curve AUC: **0.9069675618886842**, which correctly displays as **0.907**.
- Maximum change from rounding source coordinates to eight decimals: X **4.8062015617356124e-9**; Y **4.918648266460934e-9**.
- Area of the original candidate's 80-point display polygon: **0.9069837608250276**.
- Area with both coordinate arrays rounded to eight decimals, as in v3: **0.9069837596961873**.
- Neither polygon is the full empirical curve. Keep the AUC annotation sourced from the full-curve statistic, exactly as the builder already does. No AUC recalculation or new experimental claim is needed.

The original candidate had no embedded chart workbooks. V3 has five, all checked as described above. This review is tied to the v3 hashes below and does not automatically certify later re-exports.

## Verified Numerical Ledger

| Slides | Claim | Result |
|---|---|---|
| 1 | Conference year and author count | 2026; three named authors, no email shown. These are identity/context fields, not experimental metrics. |
| 2 | Example query and passage IDs | Query 1086224; passages 7112148, 7399382, 987600 match the archived annotation JSON. Their human categories are 1, 2, 0; only 7112148 is official-positive. The other two are unjudged under official qrels. |
| 3 | Corpus/population sizes | 8,841,823 passages -> 8.84 million; manual 1,179 queries / 33,667 distinct pairs; full set 101,093 queries. The corpus count agrees with the corrected manuscript. |
| 4 | Manual pooling | Top 10 per controlled retriever; mean 28.555555555555557 -> 28.56 candidates/query; maximum 63 in notes. |
| 5, 13 | Positive-label density | 1,243/1,179 = 1.0542832909245123 -> 1.05; 20,597/1,179 = 17.46988973706531 -> 17.47. Difference 19,354 pairs. The 14 seed-only pairs are correctly distinguished from official qrels. |
| 6, 13, 14 | Manual NDCG and paired effects | All eight chart values, four paired differences, eight interval bounds, and repeated E5 callouts agree with the corrected manual summary. Exact-to-display values are below. |
| 7 | Judge stage | No new numeric effectiveness claim. Its pseudo-labeling role remains distinct from retrieval. |
| 8, 15 | Held-out test | 177 queries / 5,002 pairs; AUC 0.907, F1 0.875, precision 0.851, recall 0.902, accuracy 0.836 in notes. Original inherited encoding is disclosed. |
| 8, 15 | Split and sensitivity | 825/177/177 queries; 23,543/5,122/5,002 pairs. Six unresolved categories plus one empty-text record are included in the test protocol. Exclusion leaves 4,995 pairs, AUC 0.909 and F1 0.876, matching the previously verified saved-score sensitivity. |
| 9, 16 | Pool counts | All five K coordinates and ten plotted per-query means agree with `populations.all_queries.depths`. The primary denominator is 101,093 throughout. |
| 10 | Variable-input RRF minus E5 | Correct five effects and ten CI endpoints; K=10 -0.0195, K=200 +0.0088, K=200 CI [0.0082, 0.0095]. The notes correctly state that K and RRF input depth change together. |
| 11 | Fixed-input RRF minus E5 | Correct five effects and ten CI endpoints. Gap -0.0661 at K=10, +0.0080 at K=30. Both rankings remain fixed; coverage and IDCG can change. |
| 11 | Outside-pool rate | 145,643 / (101,093 x 10) x 100 = **14.406833311900924% -> 14.4%**. This is a fraction of returned query-passage pairs, not queries or all pooled candidates. At K=30, 3,555 / 1,010,930 x 100 = **0.35165639559613426% -> 0.35%**. |
| 12, 17 | Query exclusions | 1,179 - 23 = 1,156; 101,093 - 1,179 = 99,914. Manual system order and the signs of all five full-set RRF/E5 comparisons are preserved. |
| 14 | Inference protocol | 5,000 query bootstraps, 10,000 sign flips, seed 20260914. Each manual annotation p = 1/10,001; four-test Bonferroni-adjusted p <= 0.000399960004. Thus the displayed p < 0.001 is valid. Intervals remain pointwise. |
| 15 | Training/threshold context | Two epochs, batch 16, maximum length 512, 100 warmup steps, query-split seed 42 agree with the corrected manuscript. Threshold -0.21871782839298248 -> -0.2187178284 is correct. No training rerun is implied. |
| 16 | K=200 totals | 45,647,587 candidate pairs and 13,004,336 predicted-positive pairs, matching the source. |
| 17 | Exclusion effect | 0.008773487528061993 -> +0.00877; CI [0.008044686244299984, 0.009443022156330074] -> [0.00804, 0.00944]. |
| 18 | Proposed judge | No effectiveness numbers or completed-experiment claims are attached to the proposed reference-conditioned judge. |

### Slides 6 and 14: Manual Values at Display Precision

| System | Original | Human | Human minus original | Paired 95% CI |
|---|---:|---:|---:|---|
| BM25 | 0.248 | 0.644 | +0.396 | 0.372 to 0.419 |
| E5 | 0.488 | 0.879 | +0.391 | 0.365 to 0.417 |
| BGE | 0.433 | 0.828 | +0.395 | 0.369 to 0.419 |
| RRF (3) | 0.459 | 0.854 | +0.395 | 0.371 to 0.419 |

The chart reverses the category array for horizontal-bar placement but preserves the correct value-to-system association. All source-to-chart deviations are <=5.01e-9, consistent with eight-decimal storage. Paired differences come from unrounded source numbers, not subtraction of the three-decimal labels. E5 remains first among these four systems before and after annotation. The wording correctly identifies a measurement change with unchanged rankings.

### Slides 8 and 15: Test Errors and ROC

Native matrix `[[1300,506],[314,2882]]` is in TN/FP/FN/TP order. Total = 5,002; positives = 3,196; negatives = 1,806; predicted positives = 3,388. Thus precision = 2,882/3,388 = 0.8506493506493507 and recall = 2,882/3,196 = 0.9017521902377973. No confusion of accuracy with AUC is present.

The chart contains all 80 retained observed ROC vertices from `reviews/test_roc.json`, not a synthetic curve. The validation operating point is FPR 0.28017718715393136 and TPR 0.9017521902377973, consistent with FP=506 and TP=2,882. Endpoints and monotonicity are retained. AUC and F1 callouts use held-out values, not the higher training-inclusive diagnostic metrics.

### Slides 9 and 16: Full-Set Table

| K | Candidates/query | Predicted relevant/query | E5 | RRF L=K | RRF L=200 |
|---:|---:|---:|---:|---:|---:|
| 10 | 21.9 | 14.2 | 0.871 | 0.852 | 0.805 |
| 30 | 65.8 | 33.7 | 0.851 | 0.862 | 0.859 |
| 50 | 110.4 | 49.4 | 0.847 | 0.856 | 0.856 |
| 100 | 222.9 | 81.0 | 0.844 | 0.851 | 0.853 |
| 200 | 451.5 | 128.6 | 0.842 | 0.850 | 0.850 |

Every native cell matches the source directly at the displayed precision. At K=30, 65.8 is correct from 65.84688356266012; do not double-round it via 65.85 to 65.9. At K=50, both RRF values legitimately round to 0.856 although their full-precision values differ. At K=200 the two RRF outputs and metrics are genuinely identical.

Primary K=200 predicted-positive mean = 13,004,336/101,093 = 128.63735372379887. There are 1,592 zero-positive queries; the conditional denominator is 99,501, yielding 130.69553069818394 -> 130.7. Notes correctly distinguish the latter and do not mix it into the main chart/table.

### Slides 10 and 11: Paired Contrasts

| K | Variable-input delta | Variable-input 95% CI | Fixed-input delta | Fixed-input 95% CI |
|---:|---:|---|---:|---|
| 10 | -0.01952103 | [-0.02023617, -0.01882729] | -0.06611695 | [-0.06706846, -0.06516868] |
| 30 | +0.01085768 | [0.01021579, 0.01150741] | +0.00801274 | [0.00727626, 0.00875623] |
| 50 | +0.00854269 | [0.00784398, 0.00925389] | +0.00898873 | [0.00828331, 0.00970650] |
| 100 | +0.00771191 | [0.00701006, 0.00843288] | +0.00890891 | [0.00822793, 0.00962559] |
| 200 | +0.00883193 | [0.00815880, 0.00953703] | +0.00883193 | [0.00815880, 0.00953703] |

These are exactly the v3 chart-cache/workbook values at eight decimals, including each vertical interval's K coordinate. Sources are the respective `rrf_variable_minus_e5` and `rrf_fixed200_minus_e5` rows in `paired_inference.all_queries`. Pointwise query-bootstrap intervals and the zero reference have correct stored numbers; their PDF visibility is a separate open finding above. The connected fixed-input line does not support an untested optimal K or a continuous response claim; none is made in the notes.

### Slide 17: Clean-Query Table

BM25 0.644/0.644; E5 0.879/0.879; BGE 0.828/0.828; RRF 0.854/0.855 for all/clean queries. All cells match `metrics[model].human` and `clean_queries_human`. Equal three-decimal values are rounded equality, not identical underlying estimates. The notes correctly describe the changes as small rather than zero.

## Evidence and Snapshot

Primary numeric sources: `./revision_2026/results/manual_summary.json`, `fullset_summary.json`, and the previously verified `presentation_2026/premium/reviews/test_roc.json`. The existing NPZ audit and saved-score sensitivity are documented in `reviews/statistics.md`. For non-summary context, the corrected `delivery_revision/manuscript_en.tex` was checked, and the example's three labels/official membership were rechecked directly in the small archived annotation/qrels members. No ML or expensive inference was run.

Current reviewed snapshot SHA-256:

```text
validated/validated-v3.pptx
e12e695989ff1acb93c874b16c5a3168b2a6d61b25a1aa176e6ba47914d2d058
validated/validated-v3.pdf
2b78e7f02cbeb5dfb8bf8abc87b5e6c6fd8804d3202edb66673df43f1a778e87

Original comparison snapshot:
candidate-v1.pptx
4e4efacdc3edf09b25017ed499307d7375f73a7a4c0faeed58fa8b7110e6eae3
speaker_script.json
36d396efbd65cfde0b80a61c1fbfcecc2b88e2559736fa54c0b4b764d019a055
```

**Remaining acceptance:** make the five effects and all intended intervals/caps visible on PDF page 10; restore the ROC operating marker on page 8 and interval visibility on page 11; retain the already-verified chart/workbook values, axis labels, and AUC annotation. No experimental number needs to change.
