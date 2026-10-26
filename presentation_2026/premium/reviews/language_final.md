# Final Copy QA

## Findings

The 18-slide version preserves the important distinctions between human judgments, pseudo-labels, and unchanged retrieval outputs. No broad claim of universal retrieval improvement was found. The remaining corrections below concern precision and spoken clarity, not a change to the scientific argument.

### Meaning And Claims

| Priority | Location | Finding and ready-to-use replacement |
| --- | --- | --- |
| P2 | Slides 8, 15 and 17, Russian notes ([script, slide 8](./presentation_2026/premium/build/speaker_script.json:62)) | **Count records, not label categories.** “Шесть неразрешённых категорий” means six distinct categories, whereas the test has six affected pairs. Replace with **“шесть пар с метками, смысл которых не установлен”**. On slide 17 replace “29 неразрешённых категорий” with **“29 пар с такими метками”**. The full manual data have three nonstandard values, `3`, `20`, and `22`, across 29 pairs. |
| P2 | Slide 11 notes and slide 13 conclusion ([script](./presentation_2026/premium/build/speaker_script.json:86), [slide copy](./presentation_2026/premium/build/build_deck.mjs:188)) | **Distinguish unchanged passage rankings from a reversed system comparison.** “И первая десятка RRF, и первая десятка E5 одинаковы…” can suggest that the systems return identical lists. Use **“При изменении K первая десятка каждой системы остаётся неизменной.”** Replace “Assessment coverage alone can change their order” with **“Changing the judgment pool can reverse which system scores higher”**. Retain the pseudo-label qualifier. The sign reversal is supported; the wording should not imply changed passage order or separate coverage from its effect on IDCG. |
| P2 | Slide 7 notes ([script](./presentation_2026/premium/build/speaker_script.json:54)) | **Keep the reference-input benefit hypothetical.** “Известный ответ был бы дополнительным полезным сигналом” presumes the outcome of future work. Use **“В следующем эксперименте проверим, улучшает ли качество судьи добавление эталонного фрагмента.”** The explicit future-work wording on slide 18 is otherwise appropriate. |
| P2 | Slide 8 notes ([script](./presentation_2026/premium/build/speaker_script.json:62)) | **Specify both ROC denominators.** “Долю найденных положительных пар относительно доли ложноположительных” is ambiguous. Use **“По вертикали ROC показана доля верно выявленных положительных пар среди всех положительных. По горизонтали показана доля ложноположительных среди всех отрицательных. Точки соответствуют разным порогам.”** Briefly define F1 as the harmonic mean of precision and recall; define those as the share of predicted positives confirmed by the labels and the share of labeled positives recovered. Do not call AUC accuracy; the existing caution is correct. |
| P2 | Slide 14 notes ([script](./presentation_2026/premium/build/speaker_script.json:110)) | **Avoid “Интервалы точечные”.** It sounds like point estimates rather than pointwise confidence intervals. Use **“Для каждого эффекта рассчитан отдельный 95%-ный доверительный интервал. Совместное покрытие всех четырёх эффектов не оценивается.”** Replace “Четыре эффекта проходят поправку Бонферрони” with **“Все четыре различия статистически значимы после поправки Бонферрони.”** Preserve the distinction between adjusted significance tests and unadjusted individual intervals. |
| P2 | Slide 18 final note ([script](./presentation_2026/premium/build/speaker_script.json:142)) | **Do not extend the fixed-output condition to every full-set experiment.** “При фиксированных сохранённых ранжированиях” is too broad as a final description: the fused output can change when `L = K`. Use **“Работа измеряет влияние покрытия разметки и глубины пулов, отдельно сравнивая изменяемые и фиксированные входы RRF.”** |

### Concision And Terminology

| Location | Existing wording | Preferred wording |
| --- | --- | --- |
| Slide 2, Russian qrels definition | “файл суждений о релевантности запросам” | **“оценки релевантности пар «запрос-фрагмент»”**. This names what is judged rather than only the storage format. Add **“in this evaluation”** to the English zero-gain sentence. |
| Slide 5, English label | “Relevant judgments per query” | **“Passages judged relevant per query”**. Passages, not judgments, are relevant. |
| Slides 4, 7 and 18, reference input | “known relevant answer”; “известный релевантный ответ” | **“reference passage labeled relevant”**; **“эталонный фрагмент из исходной разметки”**. Apply consistently. Avoid implying one definitive answer. |
| Slide 12, table | “Comparison directions unchanged” | **“Signs of RRF-E5 differences unchanged”**. Identify the comparison explicitly. |
| Slide 16, three metric headers | “NDCG” | **“NDCG@10”**, consistent with the reported metric elsewhere. |
| Slide 17, table and footer | “Clean 1,156 queries”; “Exclusion checks preserve the observed directions, not independent human validity.” | Header: **“After exclusions: 1,156 queries”**. Footer: **“Exclusion checks do not replace independent human assessment.”** “Human validity” is not a clear technical term, and exclusion does not certify a clean dataset. |
| Slides 7, 13, 15 and 18, Russian notes | “обучаемый baseline”; “reference-conditioned судьи”; “сырые scores”; “запрос, reference passage labeled relevant, кандидат” | **“дообученная базовая модель”**; **“судьи с доступом к эталонному фрагменту”**; **“выходные баллы модели до порогового преобразования”**; **“запрос, эталонный фрагмент из исходной разметки, оцениваемый фрагмент”**. Keep model identifiers unchanged. |
| Slides 12 and 17, Russian notes | “человеческая валидация”; “независимая человеческая релевантность”; “чувствительность удаляет…” | **“независимая ручная оценка”**; **“проверка на независимой ручной разметке”**; **“в проверке устойчивости исключаем…”**. |

## Process Language

No TODOs, client instructions, AI/ChatGPT references, or builder-status narration were found in the visible English slide copy. Keep legitimate methodological disclosures: label mapping, saved-score reuse, source provenance, and absence of independent human validation.

- Slide 8: move **“Кривая визуально сокращена до 80 фактических точек…”** from spoken narration to the technical source note. Preserve the disclosure there, including that AUC uses the full curve. Replace the editorial **“Основные числа оставлены для исходного протокола”** with **“Основная оценка использует исходное бинарное кодирование меток.”** The seven-record sensitivity check can remain in appendix slide 15, with a short caveat on slide 8.
- Slide 15: replace **“Повторная оценка использует сохранённые scores; новое нейросетевое обучение здесь не выполнялось”** with **“Метрики рассчитаны по сохранённым выходным баллам одной дообученной модели.”** This preserves provenance without describing production work on the presentation.
- All source blocks: **“Corrected pool-based evaluation.”** is revision-status language appended to the paper citation. Remove that sentence or use **“Pool-based evaluation.”** Keep the actual paper title and reproducibility references.

## Known Typo

Slide 2 still contains **“ацона”** in both the builder and script at review time. The requested replacement **“ацетона”** is correct and already acknowledged; it is not counted as a new finding.

## Verification

Reviewed all English titles, labels, table text and footers in [build_deck.mjs](./presentation_2026/premium/build/build_deck.mjs), plus every note and source block in [speaker_script.json](./presentation_2026/premium/build/speaker_script.json). All 18 script notes matched the builder at the check. Author names and order remain correct: **, , **. Affiliation matches the corrected manuscript; no email is present. Timing totals **810 seconds (13:30)** across 13 main slides, with five untimed appendix slides; this is planned timing, not a rehearsal measurement.

Interpretation checks used [the corrected manuscript](./delivery_revision/manuscript_en.tex), [manual_summary.json](./revision_2026/results/manual_summary.json), [fullset_summary.json](./revision_2026/results/fullset_summary.json), and [test_roc.json](./presentation_2026/premium/reviews/test_roc.json). This was copy QA of the supplied sources, not a new visual or statistical audit. Only this report was created; no source edits were made.
