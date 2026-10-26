# Scientific Talk Narrative

## Editorial Decision

Use 13 core slides for 13:30 of speaking, followed by five backup slides. Keep English slide copy and Russian speaker notes. Preserve the paper title, , , , and . No email.

Two viable structures are a measurement-first talk and a methods-first talk. The former makes the contribution understandable before introducing model terminology. The latter permits a fuller account of annotation and training but delays the main result. Recommend the measurement-first structure below for DAMDID's multidisciplinary audience.

**Narrative spine:** a correct answer can lack a judgment; human assessment measures the resulting change in evaluation with rankings fixed; a validated baseline judge permits a larger, explicitly conditional experiment; a fixed-fusion diagnostic distinguishes assessment coverage from changes to ranked output.

**Contribution statement:** "We quantify how additional human judgments change the evaluation of fixed rankings, and examine how assessment depth and fusion input depth affect comparisons under a fixed judge."

The contribution is empirical analysis of a measurement procedure. Do not present sparse judgments, pooling, MiniLM, or RRF as new inventions.

## Changes to the Existing Talk

- Keep the actual query example, separation of human and predicted labels, and fixed-ranking comparison. These already provide a sound scientific foundation.
- Move the evaluation design before the first aggregate result. The audience should know what stays fixed before interpreting a larger number.
- The existing script already budgets 810 seconds. Strength comes from reallocating those seconds, not adding a longer introduction or more results tables.
- Replace the dedicated future-judge slide with the completed fixed-input RRF diagnostic from the corrected manuscript. The old slide 10 mentions two changing factors, but does not show this control.
- Replace the two-system score curves on old slide 10 with paired RRF-minus-E5 effects and confidence intervals. The scientific quantity of interest becomes visible without magnifying small differences through a narrow absolute-score axis.
- End with the measured human-label effect and the evaluation controls. A planned judge architecture should not displace the completed contribution in the final minute.

## Core Slides

Each message below is exact proposed English copy, not an extra paragraph to place under the title. Prefer the message as a single chart annotation or short concluding line. Target 25-40 visible body words, excluding chart labels, necessary conditions, and sources. The concrete example may exceed this slightly. Put definitions, reasoning, transitions, and secondary numbers in Russian notes.

### 1. Deep Re-annotation and Controlled Candidate Pools

**Time:** 0:25. **Subtitle:** "Re-evaluating ranking models on MS MARCO"

**Message:** "How judgment coverage changes the evaluation of existing rankings."

**Evidence/layout:** Minimal title, three authors, affiliation, conference. Do not add an agenda or a second promotional headline. The spoken contribution statement supplies the purpose.

**Russian note cue:** "Мы измеряем, как полнота оценок релевантности меняет оценку уже существующей поисковой выдачи. Затем отдельно рассматриваем глубину пула и глубину списков, поступающих в объединение."

### 2. A relevant answer can receive zero gain

**Time:** 1:05. **Message:** "Passage 7399382 answers the query but is absent from the original positive judgments."

**Evidence/layout:** Query 1086224, "what causes boiling point to increase". Show three short passage paraphrases with original and human labels: salt raises the boiling point (7112148, relevant/relevant), non-volatile solute raises it (7399382, unjudged/relevant), acetone's boiling temperature (987600, unjudged/not relevant). Visually emphasize only the middle row. Label the excerpts "Shortened paraphrases".

**Russian note cue:** "Отсутствие оценки даёт нулевой вклад в метрику, хотя фрагмент отвечает на вопрос. Это конкретный пример, а не оценка частоты таких случаев во всём корпусе."

### 3. Human judgments and a larger pool experiment

**Time:** 0:45. **Message:** "Human labels support the annotation comparison. Judge predictions support the depth experiment."

**Evidence/layout:** One simple study map: 1,179 queries / 33,667 pairs with human assessments, then a judge, then 101,093 queries with predicted labels. Label the collection "English MS MARCO". Visibly distinguish the evidence types. Do not imply the larger set is independent: all 1,179 manual queries occur within it.

**Russian note cue:** "Сначала проверяем эффект доразметки на человеческих оценках. Затем расширяем эксперимент с помощью модели. Большой набор включает ручную часть, поэтому независимость проверяем отдельно только там, где она действительно обеспечена."

### 4. Reference-assisted manual annotation

**Time:** 1:05. **Message:** "The assessor sees the query, candidate passage, and a known relevant answer."

**Evidence/layout:** BM25, E5, BGE top-ten lists and auxiliary candidate channels feed a deduplicated pool, then human assessment. Label the auxiliary contribution "Includes reference-based similarity". Distinguish this arrow from query-only retrieval. Average pool size: 28.56 candidates/query. Identify BM25 as lexical retrieval, E5/BGE as dense retrieval orally.

**Russian note cue:** "Известный ответ помогает отбирать и оценивать кандидатов. Обычный поисковый алгоритм этой информации не получает. Пул намеренно обогащён подходящими ответами, поэтому его нельзя считать случайной выборкой корпуса."

### 5. Evaluation with unchanged rankings

**Time:** 1:00. **Message:** "The rankings and query set stay fixed. Only the relevance judgments change."

**Evidence/layout:** One ranked list evaluated under original and extended human labels. Define NDCG@10 in speech as a score that rewards relevant passages near the top. Essential visible conditions: "Shared ideal ranking per query and label set" and "All 1,179 queries". Explain RRF as merging the ranks from the three retrieval systems. Full equations belong in backup.

**Russian note cue:** "Идеальный знаменатель общий для всех систем при данном запросе и наборе меток, но после доразметки он может измениться. Сравниваем оценку неизменной выдачи, без повторного обучения моделей."

### 6. Human judgments identify 19,354 additional positives

**Time:** 0:55. **Message:** "Mean positive judgments per query rise from 1.05 to 17.47 within the selected pools."

**Evidence/layout:** One original-versus-human comparison, 1,243 versus 20,597 positive pairs. Use either total counts or means as the chart axis, with the other measure as a small annotation, not a competing graphic. Keep "1,179 queries; selected candidate pools" visible.

**Russian note cue:** "Считаем положительные пары внутри одного и того же пула. Дополнительные 19 354 пары определены относительно официальных qrels, пересечённых с пулом. Это не число всех релевантных фрагментов в коллекции."

### 7. NDCG increases for all four fixed rankings

**Time:** 1:25. **Message:** "The observed mean increases are about 0.39 NDCG@10. E5 remains the highest-scoring system in this comparison."

**Evidence/layout:** One paired before/after plot with four rows, not separate score and significance panels. BM25 0.248 / 0.644, E5 0.488 / 0.879, BGE 0.433 / 0.828, RRF(3) 0.459 / 0.854. Label conditions "Original qrels" and "Human judgments". Include a small paired-effect annotation for E5: +0.391, 95% CI [0.365, 0.417]. Other intervals and tests go in backup.

**Russian note cue:** "Это изменение измеренной оценки, а не прирост качества модели после обучения. Во всех четырёх случаях интервал изменения не включает ноль. Порядок сравниваемых систем сохраняется: E5, RRF, BGE, BM25."

### 8. MiniLM agreement with held-out judgments

**Time:** 1:05. **Message:** "On 177 held-out queries, the judge reaches ROC-AUC 0.907 and F1 0.875."

**Evidence/layout:** Query text plus candidate text enter a compact cross-encoder. Show test size 5,002 pairs and a visible "Threshold selected on validation" condition. Keep precision 0.851 and recall 0.902 in notes or backup. Do not reuse the all-manual-pairs score histogram as independent test evidence.

**Russian note cue:** "Судья совместно обрабатывает два текста и не получает известный ответ, ранги или оценки поисковых моделей. Запросы разделены между обучением, валидацией и тестом. Даже при таком согласии предсказания остаются ошибочными в части случаев."

### 9. Larger pools contain more predicted positives

**Time:** 1:00. **Message:** "Mean predicted positives rise from 14.2 to 128.6 as pooling depth increases from 10 to 200."

**Evidence/layout:** A single five-point curve at K = 10, 30, 50, 100, 200. Values: 14.2, 33.7, 49.4, 81.0, 128.6. Axis: "Predicted positive passages per query". State "Union of BM25, E5, BGE top-K results" and "Same judge and threshold; all 101,093 queries". Explain orally that K is each source's list depth, not deduplicated pool size. Candidate means increase from 21.9 to 451.5.

**Russian note cue:** "Общий балл пары и порог не меняются между глубинами. Добавляются кандидаты, среди которых судья находит новые положительные предсказания. Нулевые запросы входят в среднее. По этому графику нельзя оценить истинную полноту корпуса."

### 10. RRF changes position relative to E5

**Time:** 1:10. **Message:** "RRF is below E5 at K = 10 and slightly above it at the four larger tested depths."

**Evidence/layout:** Plot the five paired differences RRF_K minus E5 with a clear zero line and 95% intervals. Differences: -0.0195, +0.0109, +0.0085, +0.0077, +0.0088. Annotate the endpoint +0.0088, 95% CI [0.0082, 0.0095]. Essential visible qualifier: "Pseudo-label evaluation; pool depth and RRF input depth both vary". Avoid a "best K" recommendation.

**Russian note cue:** "Здесь одновременно расширяется пул оценки и меняются входные списки RRF. Поэтому нельзя объяснить смену порядка только полнотой разметки. Небольшой выигрыш означает большее согласие с этим судьёй, а не доказанное превосходство по человеческим оценкам."

### 11. Assessment depth changes scores for fixed RRF output

**Time:** 1:30. **Message:** "With RRF input fixed at 200, the same output receives different scores as the assessment pool changes."

**Evidence/layout:** This is the pivotal added result. Show one curve for fixed RRF input 200 against assessment K = 10, 30, 50, 100, 200: NDCG@10 0.805, 0.859, 0.856, 0.853, 0.850. Clearly label the fixed input depth separately from the horizontal axis. At K = 10, annotate "145,643 returned query-passage pairs outside the assessed pool". Those pairs receive zero gain. They are not all known positives and are not 145,643 unique passages.

**Russian note cue:** "Теперь сам результат RRF зафиксирован. При узком пуле часть возвращённых фрагментов остаётся вне оценивания. Расширение пула меняет покрытие и нормировку. Поэтому кривая не обязана расти монотонно. Это диагностический контроль, а не полное количественное разложение двух эффектов."

### 12. Scope of the evidence

**Time:** 1:05. **Message:** "The findings concern selected English MS MARCO pools and predictions from one judge."

**Evidence/layout:** Two restrained evidence statements, not a wall of disclaimers: "Manual system order survives exclusion of 23 affected queries" and "Depth-comparison directions survive exclusion of all 1,179 manual queries". Label the remaining populations 1,156 and 99,914 respectively. One boundary line: "No exhaustive corpus judgments or independent human validation of full-set results".

**Russian note cue:** "Проверки устойчивости сохраняют основные направления результатов. Но они не устраняют смещение обогащённого пула, ошибки одного судьи и отсутствие независимой оценки согласованности аннотаторов. Перенос на другие языки и коллекции здесь не проверен."

### 13. Relevance coverage and fusion depth affect evaluation

**Time:** 1:00. **Message:** "Denser human judgments change scores for fixed rankings. Pool coverage and fusion input depth also affect pseudo-label comparisons."

**Evidence/layout:** Two concise result lines, each with one anchor: "Human labels: E5 0.488 to 0.879, same ranking" and "Fixed RRF input: 145,643 returned pairs unjudged at assessment K = 10". Small condition: "Evidence within the evaluated pools". Leave this slide on screen during questions. Put the next experiment in the final spoken sentence or backup, not in the primary conclusion.

**Russian note cue:** Use the closing below. Do not end with the unsupported headline "RRF wins" or a promise that more labels always raise NDCG.

## Opening and Closing

**Opening, Russian, across slides 1-2:**

"Сегодня мы рассматриваем, как разметка влияет на оценку поисковой выдачи. Наш вклад состоит в измерении эффекта дополнительной человеческой разметки при неизменных результатах поиска и в отдельном анализе глубины пулов. Посмотрим на пример: запрос спрашивает, почему повышается температура кипения. Один фрагмент отвечает через добавление соли, другой через нелетучее растворённое вещество. Оба подходят, но второй отсутствует в исходных положительных оценках и получает нулевой вклад в метрику. Что изменится, если оценить такие ответы, не меняя сам поиск?"

**Closing, Russian, approximately 50-60 seconds:**

"На 1179 запросах дополнительная человеческая разметка увеличила среднее число положительных оценок внутри выбранных пулов с 1,05 до 17,47. Для тех же результатов E5 оценка NDCG выросла с 0,488 до 0,879. Мы измерили влияние покрытия разметки на оценку существующей выдачи. В большом эксперименте мы также показали, почему нужно различать глубину пула и глубину входных списков RRF: даже фиксированная выдача получает разные оценки при изменении пула. Практический вывод для сравнения моделей: вместе с метрикой необходимо указывать, какие кандидаты оценивались, кем и на каком наборе запросов. Эти выводы относятся к исследованным пулам английского MS MARCO. Следующий шаг состоит в независимой человеческой проверке с более сильными судьями. Спасибо."

No dramatic claims about a broken benchmark, universal model rankings, or human-equivalent judges. For this audience, explain the measurement issue before expanding qrels, NDCG, RRF, or cross-encoder terminology.

## Backup Slides

1. **NDCG@10 and paired inference.** Message: "Systems share the ideal denominator for each query and label set." Equations, zero-gain handling, all-query averaging, four manual paired intervals. Manual bootstrap 5,000, sign flips 10,000. Full-set bootstrap and sign flips 2,000. Distinguish absolute score changes from changes in model output.
2. **Judge inputs, split, and threshold.** Message: "Query groups separate training, validation, and test." Show 825/177/177 queries, 23,543/5,122/5,002 pairs, raw-score threshold -0.2187178284, precision/recall, and two-epoch training. Disclose inherited handling of 29 unresolved labels. Reference-conditioned judging is a proposed comparison with no reported result.
3. **Pool provenance and query exclusions.** Message: "Sensitivity checks preserve the observed system order and depth-comparison directions." Manual auxiliary channels are incompletely specified and excluded from system comparisons. Include 29 unresolved labels, five empty text fields, 23 affected queries, and the full-set manual-query exclusion. Do not describe exclusion as independent human validation.
4. **Full depth results and fixed-output diagnostics.** Message: "Assessment depth and fusion input depth are distinct experimental settings." Provide full score/count tables and paired intervals. Note that the individual retrievers' top-ten DCG stays constant while IDCG changes. At K = 200, 1,592 queries have no positive prediction and remain in the main mean. Keep conditional means explicitly separate.
5. **Positioning and next validation.** Message: "The study quantifies annotation effects in defined pools." Compact references to pooling, MS MARCO, RRF, and cross-encoders from the manuscript. Future work: stronger and reference-conditioned judges against held-out human judgments, followed by other collections. No claimed new architecture, comprehensive benchmark repair, or verified transfer.

## Timing and Claim Controls

- Core timing totals 810 seconds, or 13:30, without Q&A. The result slides receive the longest pauses.
- For a strict 12-minute delivery, reduce slides 2, 3, 4, 5, 6, 8, 9, 10, and 12 by ten seconds each. Retain the human effect, fixed-input diagnostic, and conclusion.
- For a 15-minute delivery, allow reading and explanation on slides 2, 7, and 11. Do not add a literature survey or more model specifications.
- Treat all numerical results as pool-based. "17.47" describes human-positive passages within selected manual pools. "128.6" describes predicted positives at K = 200 over all 101,093 queries.
- State the observed increase in NDCG for these rankings only. Additional judgments can also enlarge IDCG, so a general monotonic-improvement claim is false.
- Use 0.854 for manual RRF on all 1,179 queries. The 0.855 value belongs to the clean 1,156-query subset.
- Restrict the core system comparison to BM25, E5, BGE, and their three-way RRF. Auxiliary-channel or judge-reranking numbers in JSON do not belong on the same leaderboard.
- Give each chart a nearby evidence condition, such as "Human judgments; 1,179 queries" or "Pseudo-labels; all 101,093 queries". Use Russian notes for full source paths and qualifications, never unreadable footnotes as the only disclosure.

## Source Basis

Read-only inspection covered the existing PPTX text, all 16 speaker-script entries, the existing builder's narrative definitions, and rendered result/conclusion slides 7, 10, and 12. The original PPTX/PDF and both builders are outside this report's edit scope.

- `delivery_revision/manuscript_en.tex`: contribution, example, annotation protocol, model roles, controlled comparison, and limitations.
- `delivery_revision/fullset_interpretation_en.tex`: fixed-input RRF diagnostic and interpretation of overlapping query sets.
- `revision_2026/results/manual_summary.json`: `density.official`, `density.human`, `metrics.{bm25,e5,bge,rrf3}`, `judge_rescored_split_metrics.test`.
- `revision_2026/results/fullset_summary.json`: `populations.all_queries.depths`, `paired_inference.all_queries`, `manual_overlap`, and exclusion sensitivity.
- `presentation_2026/build/speaker_script.json`, `presentation_2026/build/build_deck.mjs`, and `Презентация_DAMDID/DAMDID_2026_Talk.pptx`: prior narrative and slide-copy baseline only.

No legacy results from `original_based_2026` enter this recommendation.
