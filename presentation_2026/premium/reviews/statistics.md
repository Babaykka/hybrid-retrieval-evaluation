# Statistical Audit for the Premium DAMDID Presentation

## Conclusions

- The corrected manual and full-set summary values agree with the saved per-query arrays. Use these results, not `original_based_2026` or numbers copied from the existing deck.
- The manual result is **a change in measured effectiveness under denser judgments, with rankings unchanged**, not a retrieval-model improvement. E5 remains above three-way RRF on human labels.
- The strongest control is available: **with RRF inputs fixed at top-200, RRF-minus-E5 changes from negative to positive when only the assessment pool expands from depth 10 to 30**. Missing assessments and fusion-input truncation are distinct effects.
- Held-out judge agreement is credible as an artifact-based estimate, but the headline test protocol includes six unresolved labels mapped to zero. Report that limitation and its small exclusion sensitivity. Never substitute the training-inclusive diagnostics for the held-out result.

## Sources and Verification

Authoritative sources, all under `.`:

- `revision_2026/results/manual_summary.json`: `density`, `metrics`, `paired_human_comparisons`, `judge_rescored_split_metrics`, and `judge_rerank_heldout`.
- `revision_2026/results/fullset_summary.json`: `populations.all_queries`, `paired_inference`, `protocol`, and `score_audit`.
- `revision_2026/results/manual_per_query.npz`, `manual_judge_diagnostics.npz`, `fullset_perquery.npz`, and `fullset_inference_replicates.npz`.
- `revision_2026/results/manual_splits.json`; small annotation/score members of `phd2.zip`: `phd2/new_data/*.json`, `phd2/output_fixed/judge_scores_raw.json`, and `phd2/msmarco/qrels/dev.tsv`.
- Corrected interpretation: `delivery_revision/manuscript_en.tex`, `results_macros.tex`, `fullset_interpretation_en.tex`, and their manual/judge/full-set tables.

Verified: all manual system means and clean-subset means; exact reproduction of six annotation-effect bootstrap intervals/sign-flip tests and four manual system contrasts; all 75 full-set system means across three populations; all 30 full-set contrasts and saved bootstrap intervals/sign-flip results; shared IDCG, zero-IDCG handling, invariant base-retriever DCG, and equality of variable/fixed RRF at K=200. Full-set artifact SHA-256 values match the summary. Held-out split IDs are disjoint and reproduce the recorded query-group split; agreement was independently recalculated from saved scores and annotation records. No ML, model training, or full-set evaluation pipeline was rerun. Extra calculations below are explicitly identified.

## Denominators

| Quantity | Correct denominator and value |
|---|---|
| Manual evaluation | 1,179 queries; 33,667 distinct query-passage pairs; the same queries in every system mean |
| Manual pool size | 33,667 / 1,179 = 28.555555555555557; maximum 63, not a universally capped 40 |
| Official positives within manual pool | 1,243 / 1,179 = 1.0542832909245123 per query; median 1 |
| Human positives | 20,597 / 1,179 = 17.46988973706531 per query; median 17 |
| Manual label coverage change | 19,354 additional positive pairs relative to official qrels; 16.570394207562348 times as many positives |
| Regenerated manual pseudo-positives | 22,206 / 1,179 = 18.834605597964376 per query; 1,174 queries have a positive prediction |
| Manual data-quality sensitivity | Remove 23 affected queries, leaving 1,156; 29 unresolved label values and five empty passage texts in the original pool |
| Full-set primary population | 101,093 queries, including zero-positive pools; not the 6,980-query official labeled development subset |
| Full-set overlap sensitivity | All 1,179 manual IDs occur in the full set; exclusion leaves 99,914 queries |
| K=200 pseudo-positives, primary | 13,004,336 / 101,093 = 128.63735372379887 per query |
| K=200 pseudo-positives, conditional | 13,004,336 / 99,501 = 130.69553069818394 per positive-pool query; excludes 1,592 queries |

All official manual positives are also human positives, verified from source records. Fourteen seed-marked positives are absent from official qrels, so the official count must not be reconstructed from the seed category. The manual positive-count ratio is annotation coverage inside an answer-assisted pool, not corpus-wide relevance density. Counts are query-passage pairs, not distinct corpus passages.

NDCG uses binary gain, rank-preserving zero gain for unjudged items, and one IDCG shared across systems **within each query and label set**. IDCG is recomputed between label sets/pool depths; do not describe it as numerically fixed before and after annotation. A zero-IDCG query contributes zero and stays in the mean. Do not mix positive-query-only averages with all-query averages.

## Chart 1: Paired Annotation Effects

**Form:** four-row before/after dumbbell on a 0-1 NDCG axis, with an aligned forest plot of the paired differences and 95% intervals. Give the difference panel its own labeled axis; intervals describe differences, not either endpoint mean. Include only BM25, E5, BGE, and RRF(3), with manual fusion input depth 10 and c=60.

**English heading:** "Denser judgments change measured effectiveness"

Exact source values:

| System | Official NDCG@10 | Human NDCG@10 | Mean paired change | Paired 95% CI |
|---|---:|---:|---:|---|
| BM25 | 0.24818879111418393 | 0.6438929888870051 | 0.3957041977728211 | [0.3723868732880059, 0.4188399861931222] |
| E5 | 0.48799936165737934 | 0.8793460642124787 | 0.3913467025550994 | [0.3652797868387797, 0.4171863934438634] |
| BGE | 0.4332277402703794 | 0.8279509421697896 | 0.3947232018994101 | [0.3691000840349604, 0.41940349215647305] |
| RRF(3) | 0.45864250226585984 | 0.8538416380658425 | 0.3951991357999827 | [0.3708269140301979, 0.418594531488229] |

Show three decimals on the slide. Source: `manual_summary.json -> metrics[system]`; arrays are `(query, model)` with names in `models`.

- Same 1,179 queries; 5,000 paired query bootstrap resamples and 10,000 sign flips, seed 20260914. Each p-value is 1/10,001 = 0.00009999000099990002; show `p < 0.001`, never zero. The four effects pass Bonferroni correction; the displayed CIs are still pointwise, not simultaneous.
- Human-label RRF-minus-E5 = **-0.025504426146636193**, CI **[-0.032413001177822705, -0.018711674437559424]**. Do not claim fusion dominates E5 in the manual experiment.
- On 1,156 clean queries, human NDCG is BM25 0.6437674969000173; E5 0.8792218061273852; BGE 0.8279787199172698; RRF 0.8546528489054969. The ordering is unchanged.
- The average increase is not universal: E5 has 797 increases, 142 ties, and 240 decreases, using absolute difference <=1e-12 as a tie. Denser labels can increase IDCG enough to reduce an individual query's NDCG.
- Omit `e5-rerank` and `judge-rerank` from this controlled four-system chart. Auxiliary/reference-assisted channels are not interchangeable with the three query-only retrievers.

**Russian speaker note:** «Выдача не менялась: менялась полнота оценок. Поэтому рост NDCG показывает чувствительность метрики к разметке, а не улучшение модели. На ручных оценках E5 остаётся сильнее трёхстороннего RRF».

## Chart 2: Held-Out Judge Agreement

**Form:** a native editable ROC curve using the supplied empirical coordinates, with the validation operating point marked and the full-curve AUC labeled. Use a small adjacent 2x2 error-count table or compact precision/recall statistics. Native XY scatter with straight segments, both axes 0-1; do not use a categorical line chart, smoothed spline, or training-inclusive score histogram.

**Editable chart data:** `presentation_2026/premium/reviews/test_roc.json` contains 80 deterministically selected observed ROC points, including (0,0), (1,1), and the validation operating point. The full test curve has 4,996 points from 4,995 distinct scores. Its exact empirical AUC is 5,234,995 / 5,771,976 = **0.9069675618886842**, matching the corrected summary. The simplified displayed polygon has area 0.9069837608472384, only 0.00001619895855420328 higher; annotate the full-curve AUC, not the display polygon's area. The JSON includes counts, score thresholds, full-curve indices, exact source hashes, split IDs, target encoding, downsampling method, and display guidance. This extraction uses only saved scores and annotation records; no ML was run.

**English heading:** "Judge agreement on unseen queries"

Split: train 825 queries / 23,543 pairs; validation 177 / 5,122; test 177 / 5,002. Threshold **-0.21871782839298248**, selected on validation; prediction rule **score >= threshold**. Scores are not calibrated probabilities.

| Metric | Held-out test, saved-score recomputation |
|---|---:|
| ROC-AUC | 0.9069675618886842 |
| F1 | 0.8754556500607534 |
| Precision | 0.8506493506493507 |
| Recall | 0.9017521902377973 |
| Accuracy | 0.8360655737704918 |
| Cohen's kappa | 0.6362850215020354 |

| Original split target | Predicted negative | Predicted positive | Row total |
|---|---:|---:|---:|
| Negative under inherited mapping | 1,300 (71.98%) | 506 (28.02%) | 1,806 |
| Positive | 314 (9.82%) | 2,882 (90.18%) | 3,196 |

Source: `manual_summary.json -> judge_rescored_split_metrics.test`. Precision has denominator 3,388; recall has denominator 3,196. The 28.02% rate is false positives among target negatives, not one minus precision. Do not call AUC an accuracy percentage.

**Label caveat:** split classification targets retain the inherited mapping `label in [1,2]`, else zero (`manual_eval.py`, lines 136-163). Test therefore includes six unresolved categories and one empty-text record. Label the matrix as agreement with the original split targets, not 5,002 fully resolved human assessments. This is separate from rank evaluation's unjudged/zero-gain treatment.

**Additional lightweight sensitivity, recalculated from the archive:** excluding those seven records leaves 4,995 test pairs. Confusion matrix becomes `[[1299,500],[314,2882]]`; AUC 0.9089716439601754; F1 0.8762541806020067; precision 0.8521584861028977; recall 0.9017521902377973; accuracy 0.837037037037037; kappa 0.6382420503078199. This supports robustness but does not repair the original training labels. Keep the 5,002-pair headline to match the corrected manuscript and put the sensitivity in notes/backup; do not silently mix protocols.

**Additional query-cluster uncertainty, not stored in the source summary:** 2,000 ordinary bootstrap samples of 177 test-query IDs with replacement, carrying every pair of each selected query together; sorted saved test IDs, NumPy `default_rng(20260921)`, fixed scores and threshold, percentile intervals. Verified from the raw archived manual scores:

| Metric | Additional 95% query-bootstrap CI |
|---|---|
| ROC-AUC | [0.8869355152542386, 0.9253144955746959] |
| F1 | [0.8550239515523408, 0.8942548996086545] |
| Precision | [0.8214336920551423, 0.8762774965778499] |
| Recall | [0.8764287693229151, 0.9237111761052879] |

These intervals refer to the original 5,002-pair target mapping, not the cleaned sensitivity. They condition on the fitted model, chosen threshold, and selected query population; they do not include training or human-label uncertainty. Source `manual_judge_diagnostics.npz` has 33,633 training-inclusive pairs and no query IDs, so it must not be used alone to construct a held-out chart.

Recorded base validation AUC 0.8647677747789919 and rescored fine-tuned validation AUC 0.9082579141764859 may be shown as context, but do not plot the former against test AUC as a same-split experiment or attach a paired CI without base scores. Whole-pool AUC 0.955331704366212 and F1 0.9143832413728608 are not held-out results. Held-out judge reranking human NDCG 0.93843663302468 is conditional on the answer-assisted manual pool, not full-corpus retrieval; omit it from a retriever leaderboard.

**Russian speaker note:** «Порог выбран на валидации, а здесь показаны отдельные 177 тестовых запросов. Судья воспроизводит человеческие оценки достаточно хорошо для анализа псевдоразметки, но допускает ошибки и не заменяет независимую оценку качества поиска».

## Chart 3: Separate Pool Depth from Fusion Depth

**Form:** two aligned effect plots, both centered on zero: (A) variable RRF input K, (B) fixed RRF input 200. X-axis is assessment-pool depth K at the five tested values; y-axis is paired RRF-minus-E5 NDCG@10. Show pointwise 95% bootstrap intervals, consistent scales, and explicit panel labels. Annotate fixed-input results with the outside-pool fraction at K=10 and K=30. Do not use a dual-axis count/quality chart.

**English heading:** "Assessment coverage can reverse a fixed-ranking comparison"

All 101,093 queries, binary pseudo-qrels from the same saved judge scores and threshold; BM25+E5+BGE fusion with c=60.

| Assessment K | E5 NDCG | Variable-input RRF NDCG | Fixed-input RRF-200 NDCG |
|---:|---:|---:|---:|
| 10 | 0.8713320367712676 | 0.8518110092608054 | 0.8052150842472356 |
| 30 | 0.850973715777927 | 0.86183139976919 | 0.858986453450791 |
| 50 | 0.8471235863711642 | 0.8556662807953272 | 0.8561123163417435 |
| 100 | 0.8437324623973037 | 0.8514443748661746 | 0.8526413708000298 |
| 200 | 0.8415186204472788 | 0.8503505477342735 | 0.8503505477342735 |

Exact plotting effects and intervals, from `fullset_summary.json -> paired_inference.all_queries`:

| K | Variable RRF minus E5 | 95% CI | Fixed RRF-200 minus E5 | 95% CI |
|---:|---:|---|---:|---|
| 10 | -0.01952102751046075 | [-0.020236169626920614, -0.018827293378693356] | -0.06611695252402394 | [-0.06706846127891082, -0.06516867672176008] |
| 30 | 0.01085768399126286 | [0.010215788471751742, 0.011507410871116711] | 0.008012737672863895 | [0.007276259005221247, 0.00875622718864606] |
| 50 | 0.008542694424163031 | [0.007843982122311723, 0.009253885343824774] | 0.008988729970579019 | [0.008283307905637784, 0.00970650494225309] |
| 100 | 0.0077119124688706945 | [0.007010064828356759, 0.0084328767502203] | 0.008908908402725993 | [0.008227928177292235, 0.009625587451657711] |
| 200 | 0.008831927286994425 | [0.008158797330961746, 0.009537026233668824] | 0.008831927286994425 | [0.008158797330961746, 0.009537026233668824] |

**Strong fixed-input control:** the RRF-200 top ten and E5 top ten do not change across columns. Nevertheless, their gap changes from **-0.06612** at pool depth 10 to **+0.00801** at depth 30. At depth 10, **145,643 / 1,010,930 = 14.406833311900924%** of returned RRF-200 pairs are outside the judged pool and get zero gain. At depth 30 this is **3,555 / 1,010,930 = 0.35165639559613426%**. Affected-query counts are 72,373 and 3,196 respectively. Outside-pool counts at K=50/100/200 are 116/2/0. Unjudged does not mean nonrelevant.

**Additional contrast from saved shared bootstrap replicates:** the K=30 minus K=10 change in the fixed-input RRF-minus-E5 gap is **0.07412969019689578**, 95% CI **[0.07351908595552542, 0.07474367809982053]**. Obtained by subtracting columns 1 from 3 of `all_queries_bootstrap_mean_delta` (zero-based), then taking the 2.5th/97.5th percentiles. Because the resamples are shared, pairing is retained. This is assessment sensitivity, not a model-improvement interval.

Do not attribute that control to the denominator alone: expanding the pool credits previously unjudged RRF-200 documents **and** may increase IDCG. The denominator-only diagnostic is E5: its mean DCG stays **3.712996858206333** at all depths while NDCG drops from **0.8713320367712676** to **0.8415186204472788**. Every base retriever's per-query DCG is exactly invariant.

**Additional fixed-assessment-pool control, optional backup:** the arrays also support holding pseudo-qrels at P200 while varying only fusion input depth. Every RRF-K returned document lies in PK, a subset of P200, so its saved DCG remains valid against P200; divide `dcg[:, j, 3]` by `idcg[:, -1]`, keeping zero-IDCG rows at zero. E5 stays 0.8415186204472788. These are descriptive derived values, not rows already stored in the summary; do not reuse the variable-pool CIs for them.

| RRF input depth | RRF NDCG under fixed P200 | RRF minus fixed E5 |
|---:|---:|---:|
| 10 | 0.8216855740717919 | -0.019833046375487006 |
| 30 | 0.8520463229681231 | 0.010527702520844198 |
| 50 | 0.8499284468323995 | 0.008409826385120679 |
| 100 | 0.8491613667135527 | 0.007642746266273802 |
| 200 | 0.8503505477342735 | 0.008831927286994631 |

Thus both mechanisms matter: assessment coverage can reverse a fixed-ranking comparison, and changing fusion inputs can reverse the comparison even with assessments fixed. The algebraic control needs no new scoring. The tiny difference in the final displayed delta versus the stored summary is floating-point reduction order, not a result discrepancy.

Full-set statistical support: 2,000 paired query bootstrap samples/sign flips; each stored p = 1/2,001 = 0.0004997501249375312. The five variable-input depth contrasts pass Bonferroni correction, but their CIs are pointwise. At K=200, excluding every manual query gives delta **0.008773487528061993**, CI **[0.008044686244299984, 0.009443022156330074]**, N=99,914; all five comparison directions are preserved. This is an overlap sensitivity, not proof of independent human relevance or absence of all training contamination. Do not describe K=30 as an established optimal depth: the stored tests compare RRF with E5, not all depths with one another.

**Russian speaker note:** «Здесь разделены две причины изменения результата. Даже если обе выдачи зафиксировать, более полный пул оценок способен изменить победителя сравнения. Отдельная проверка с фиксированными оценками показывает, что глубина входов RRF тоже влияет на результат. Оба вывода относятся к меткам этого судьи».

## Full-Set Count Reference

Use counts as a compact supporting table or notes, not another dominant chart. At each depth, divide totals by 101,093 for the primary per-query means.

| K | Candidate pairs | Pseudo-positive pairs | Candidates/query | Pseudo-positives/query | Zero-positive queries |
|---:|---:|---:|---:|---:|---:|
| 10 | 2,211,979 | 1,434,720 | 21.880634663131968 | 14.19208055948483 | 2,525 |
| 30 | 6,656,659 | 3,407,575 | 65.84688356266012 | 33.70732889517573 | 2,038 |
| 50 | 11,156,232 | 4,995,705 | 110.3561275261393 | 49.41692303126824 | 1,881 |
| 100 | 22,534,870 | 8,190,143 | 222.91226890091303 | 81.01592592958959 | 1,717 |
| 200 | 45,647,587 | 13,004,336 | 451.5405319853996 | 128.63735372379887 | 1,592 |

K is per-retriever input/pooling depth, not the deduplicated union size. The stored full-set score audit has zero missing scores across 45,647,587 candidate pairs; complete score coverage does not establish complete relevance coverage. Do not write "130 relevant documents per query" without identifying the judge, candidate pool, and conditional denominator.

## Presentation Decisions

1. Lead with the unchanged-ranking paired manual result, using means plus paired uncertainty rather than five similar metric dashboards.
2. Build the native held-out ROC from `test_roc.json`, annotate full-curve AUC 0.907, F1 0.875, and actual error counts; retain the unresolved-label caveat and cleaned sensitivity in speaker notes.
3. Make the fixed-input reversal the central full-set evidence. Keep the complementary fixed-P200 calculation as backup if a methodological question arises.
4. Use "pooled human judgments" versus "judge-generated pseudo-labels" consistently. All uncertainty is conditional on recorded runs, scores, threshold, and protocol; none measures annotation reliability, judge-training variability, or generalization to other search populations. Preserve every existing deck, manuscript, and builder unchanged.
