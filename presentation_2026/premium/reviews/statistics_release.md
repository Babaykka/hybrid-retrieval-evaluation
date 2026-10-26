# Statistical Release Check: v4

## Verdict

**Numerical source/export checks pass. One PDF evidence-display issue remains: confidence intervals/caps are not separately visible on slides 10 and 11.** The previous missing mean points and ROC operating marker are restored. No experimental number needs correction.

This bounded review inspected the current builder/stamper, `validated-v4.pptx`, its five embedded workbooks, the adjacent PDF, and the 18 embedded speaker notes. It used the corrected local JSON and existing ROC evidence. No ML, resampling, new effect estimates, or source/deck edits were performed. Only this report was created.

## Remaining Finding

### [P2] Confirm visible confidence intervals in the delivered PDF

The PPTX contains correct native custom error bars, but the actual adjacent PDF shows only the five mean markers on slide 10, and the connected mean line plus five markers on slide 11. At normal view the intervals/caps are not distinguishable. Vector inspection finds the mean-marker polygons and the fixed-input connecting line, but no separate interval/cap drawing paths. This means the data-level native-error-bar check does not, by itself, confirm that the PDF presents the intended uncertainty.

Slide 10 still says "Points with 95% paired query-bootstrap intervals." Its K=200 numerical CI callout is correct, but that callout covers only one of the five comparisons.

**Action for the main author:** verify custom-error-bar rendering in the final PDF export path and ensure the intended bars/caps are visibly distinguishable from the point markers. The native CI values should remain unchanged. A renderer that preserves custom error bars, or a visibility adjustment followed by direct PDF inspection, can address this without recomputing results. Do not infer that the bars are absent from the PPTX: they are present and numerically correct.

Scope of this finding: PDF `validated-v4.pdf`, hash below, pages 10-11. The operating marker on page 8 and all mean points on page 10 are now visibly present, so those v3 findings are closed.

## Native Error Bars: Pass

- Chart owners remain exactly slides **6, 8, 9, 10, 11**.
- Each of the two RRF comparison charts now contains exactly two series: the zero reference and `RRF minus E5`. The temporary CI and cap-helper series are absent from the finalized package.
- Each mean series contains native `c:errBars` with `errDir=y`, `errBarType=both`, `errValType=cust`, and `noEndCap=0`.
- Both plus/minus arrays have five nonnegative offsets. For all ten comparisons, **stored mean + plus = stored upper bound** and **stored mean - minus = stored lower bound**, exactly in decimal arithmetic at eight-decimal presentation precision.
- All **20 reconstructed CI endpoints** match the appropriate corrected `fullset_summary.json -> paired_inference.all_queries` bounds rounded to eight decimals. The five means and their K coordinates also match the selected variable-input or fixed-input contrast.
- These are the existing percentile query-bootstrap intervals. The stamp does not create new intervals, error models, or statistical tests.

## ROC and Short-Series Padding: Pass

The actual finalized data, not merely the source implementation, satisfy the following:

| Series | Final coordinates | Interpretation |
|---|---|---|
| MiniLM ROC | The existing 80 selected ROC vertices, both coordinates rounded to eight decimals | Same display geometry to the approved coordinate precision |
| Chance line | (0,0), (1,1), followed by 78 repeats of (1,1) | Same diagonal, no extra segment to the origin |
| Validation operating point | 80 repeats of (0.28017719, 0.90175219) | One geometric point, not 80 observations |
| RRF zero references | (0,0), (210,0), followed by three repeats of (210,0) | Same horizontal zero reference |

No new origin coordinates are introduced by padding. The original ROC sample still represents **177 held-out queries / 5,002 pairs**. Marker repetition does not alter that denominator. All displayed scatter series have smoothing disabled and explicit fill on visible markers.

Full empirical AUC remains **0.9069675618886842**, displayed as **0.907**, and is not recomputed from the simplified/padded display path. Both ROC axes use `0.0`, limits 0-1, and step 0.2. The actual PDF visibly shows the correct tick labels, chance diagonal, and coral validation operating marker.

## Values, Tables, and Denominators: Pass

- Slide 6: all eight manual NDCG values retain the correct BM25/E5/BGE/RRF association and match the corrected manual summary to eight-decimal storage precision. E5 remains **0.488 to 0.879**, paired change **+0.391**, CI **[0.365, 0.417]**.
- Slide 9: all ten candidate/positive means and all five K coordinates match `populations.all_queries.depths`. All means use **101,093** queries, including zero-positive pools.
- Slides 10-11: all ten paired mean differences and twenty native CI endpoints are source-consistent. The text callouts **+0.0088 [0.0082, 0.0095]** at K=200, and fixed-input **-0.0661** at K=10 / **+0.0080** at K=30 are correct.
- Slide 11: **14.4%** retains its previously verified denominator: **145,643 of 1,010,930 returned RRF top-10 query-passage pairs**. It is not a fraction of queries or of the whole candidate pool.
- Tables 14-17: every data cell was independently matched to the corrected manual/full-set JSON at the displayed precision. Updated headings such as `NDCG@10` and `1,156 after exclusions` preserve the metric and denominator meanings.
- Judge matrix and summary: **TN=1,300, FP=506, FN=314, TP=2,882**, **5,002** pairs; **AUC 0.907, F1 0.875, precision 0.851, recall 0.902**. Inherited binary encoding and the unresolved-label sensitivity remain disclosed.
- Exclusions remain **1,179 to 1,156** manual queries and **101,093 to 99,914** full-set queries. The full-set exclusion effect **+0.00877** at K=200 is unchanged and correctly bounded in the notes.
- Key displayed numbers in the actual 18-page PDF, including tables 14-17 and the new CI/fixed-input callouts, match the checked PPTX/source values.

## Workbooks and Notes: Pass

All five embedded workbooks were opened read-only and compared against the chart caches through their formula references: **22 linked ranges, 556 matching cells, including 548 numeric worksheet cells**. The additional 20 native error-bar offsets are verified separately. Across numerical chart caches/literals there are **568 points**, with no value exceeding 15 significant digits. There is no stale v1/v3 workbook-data discrepancy.

All 18 embedded speaker-note bodies match the current `speaker_script.json`. The corrected methodological distinctions are present:

- Full-set uncertainty uses **2,000 paired query-bootstrap resamples**, with intervals conditional on the recorded rankings, judge scores, and fixed threshold; training/labeling uncertainty is not included.
- Manual annotation effects retain **5,000** query bootstraps, **10,000** sign flips, and seed **20260914**. Their individual 95% intervals are not described as simultaneous intervals.
- Seed **42** is explicitly attached to the **query split**, not asserted as a general training seed.
- The judge remains a saved-score model evaluation; no independent validation of deeper pools or completed reference-conditioned experiment is claimed.
- The planned main-talk duration remains **810 seconds = 13 minutes 30 seconds**, with 13 main slides and five appendix slides. This is a plan, not a timed rehearsal.

## Audited Snapshot

Files are under `./presentation_2026/premium`.

```text
build/validated/validated-v4.pptx
SHA256 f0dc2ffb39fe18939ff93a92d4b67424e430e4ef1ea9dad471f6e6071174504a

build/validated/validated-v4.pdf
SHA256 10f3b286e40030b18ec0e163ba5a4ff93356282475abeda2b37941f0eb6021c7

build/build_deck.mjs
SHA256 b7f6104b8427227b17d03f00011c159c7b543ef7ebe5805810135f4482a4ba7f

build/stamp_pptx.py
SHA256 949e8dfe18e3824ff56fd2333c60dc73bab59a7b634015ad456b1a23eb266da7

build/speaker_script.json
SHA256 2b00756c73c1bba317a781e3e780891875d26e4de6f64251a8d7b06a1a4d36d4
```

Primary evidence: `revision_2026/results/manual_summary.json`, `fullset_summary.json`, and `premium/reviews/test_roc.json`. Prior source/NPZ reconciliation is recorded in `statistics.md`; no new experiment was introduced during this release check. The remaining request is a final-output visibility check for uncertainty, not any change to the scientific numbers.
