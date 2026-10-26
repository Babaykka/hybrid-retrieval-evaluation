# Final Scientific QA

## Remaining Issues

1. **[P2] Qualify full-set uncertainty and score provenance in the notes.** Slides 10-11 display narrow query-bootstrap intervals, but their notes omit the conditioning assumptions. The uncertainty qualification on slide 14 concerns the manual experiment and is insufficient for these figures. Add to slide 10 or 16 notes: "Full-set intervals use 2,000 paired query-bootstrap resamples and are pointwise, conditional on the recorded rankings, judge scores and fixed threshold. They exclude judge-training and annotation uncertainty." Retain the distinction between analysis of saved scores and reproduction of training: the full-set artifact explicitly does not establish checkpoint recovery or validation. This is an evidence qualification, not a request to rerun ML or change numbers. [Current full-set notes](./presentation_2026/premium/build/speaker_script.json:78), [protocol](./revision_2026/results/fullset_summary.json:2764), [validity boundaries](./revision_2026/results/fullset_summary.json:2963).

2. **[P3] Scope seed 42 to query splitting.** Slide 15 places "seed 42" immediately after the training hyperparameters, which can imply a verified training RNG seed. The corrected manuscript establishes seed 42 for query-group shuffling. Replace with "query-split seed 42"; retain two epochs, batch 16, length 512 and warmup 100. Do not claim end-to-end deterministic training reproduction. [Slide 15 note](./presentation_2026/premium/build/speaker_script.json:118), [corrected training description](./delivery_revision/manuscript_en.tex:108).

## Version-Specific Finding

The requested `candidate-v1.pptx` has an incorrect ROC x-axis display: 0, 0, 0, 1, 1, 1 instead of fractional false-positive rates. **Already corrected in v3 during this review:** both ROC axes use `0.0`, and the refreshed slide-08 render shows 0.0, 0.2, ..., 1.0. Carry the correction into the final export; do not deliver v1. Verified v3 SHA-256 begins `ed3113db2a275d4f`. [Current ROC configuration](./presentation_2026/premium/build/build_deck.mjs:125).

## Language Pass

Per the latest coordination message, affected-pair wording, within-system invariance across K, the hypothesized reference benefit, precise ROC denominators and source-process wording are assigned to the language agent. They are not duplicate open findings here; final exported copy still needs to include that pass. For the concluding sentence, the changing "order" must mean the **measured system comparison**, never the order of documents in either fixed ranking. Preserve the scientific saved-score qualification when removing internal process language.

## Checks Passed

- Reviewed all 18 slide texts and notes, the scientific diagrams/charts, corrected manuscript and summaries. Embedded notes in v1/v2 matched the pre-language-pass script. The script allocates 810 seconds to 13 main slides, with five backups.
- No invented model architecture, new training run or completed reference-conditioned experiment found. Human assessment/reference-assisted pooling and query-plus-candidate MiniLM inputs remain correctly separated; auxiliary channels are not promoted into comparable retrieval systems.
- Independently recalculated held-out metrics from archived annotations and scores, verifying source hashes: 5,002 pairs give AUC 0.90696756 and F1 0.87545565; excluding six unresolved-label pairs and one empty-text pair leaves 4,995, AUC 0.90897164 and F1 0.87625418. No ML was run. Both displayed roundings are correct.
- Manual means, NDCG changes, full-set counts, RRF contrasts and 14.4% outside-pool proportion agree with the corrected results. The 128.6 unconditional mean is correctly separated from 130.7 conditional on positive pools. The retired "19,354 discoveries" criticism does not apply: the visible headline reports means; the pre-copy-pass note describes a count difference and discloses the seed distinction.
- Fixed-input RRF supports reversal of the measured comparison under different assessment pools, not better retrieval. The deck retains single-judge, selected-pool, English-only scope, unmeasured inter-assessor agreement and lack of independent full-set human validation.

Only this review file was written. No source, builder, deck or data edits; no training or inference rerun.
