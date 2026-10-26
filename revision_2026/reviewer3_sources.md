# Reviewer 3: Sources and EN/RU Insertions

Primary sources checked on 2026-09-14. Draft insertions only; no manuscript changes or new experiments. The recommended package adds four references. An optional MIRACL extension adds a fifth. Citation keys already present in the paper are retained.

## 1. Introduction

Suggested position: after the opening MS MARCO/mMARCO/RusBEIR paragraph, before the detailed discussion of sparse qrels. The final sentences below also provide a transition to that discussion. Counts exclude citation commands; hyphenated compounds count as one word.

### EN (180 words)

MS MARCO is one of several search-provider datasets, not a universal sample of information needs. Google's Natural Questions contains real, anonymized, aggregated search queries with human answer annotations on Wikipedia pages \cite{kwiatkowski2019naturalquestions}. Yahoo!'s Learning to Rank Challenge, distributed through Webscope, released set 1 and set 2 as query-document feature vectors with graded relevance labels, without query or document text \cite{chapelle2011yahoo}. Yandex's Personalized Web Search Challenge released session and click logs with anonymized numeric identifiers rather than readable queries and documents \cite{yandex2013personalized}. These are concrete counterparts in search research, but their tasks and released representations differ from MS MARCO passage ranking.

We use MS MARCO because accessible query and passage texts, sparse human-derived qrels, established evaluation tools, and publicly available pretrained ranking models support reproducible comparisons with prior work \cite{msmarco_datasets,reimers2019sentencebert}. Its sparse labels also directly motivate studying additional judgments within controlled candidate pools. This choice does not establish universality: provider-specific sampling, language, query intent, and document domain may affect transfer. Our analysis concerns the English MS MARCO collection and the specified annotation and pooling protocol, not all users or search settings.

### RU (191 words)

MS MARCO относится к наборам данных поисковых компаний, но не является универсальной выборкой информационных потребностей. Natural Questions компании Google содержит реальные обезличенные и агрегированные поисковые запросы с человеческой разметкой ответов на страницах Википедии \cite{kwiatkowski2019naturalquestions}. В Yahoo! Learning to Rank Challenge, распространявшемся через Webscope, наборы set 1 и set 2 представлены векторами признаков пар «запрос, документ» и градуированными оценками релевантности, без текстов запросов и документов \cite{chapelle2011yahoo}. Yandex Personalized Web Search Challenge содержит журналы сессий и кликов с обезличенными числовыми идентификаторами вместо читаемых запросов и документов \cite{yandex2013personalized}. Это конкретные аналоги по области исследований, однако их задачи и опубликованные представления данных отличаются от ранжирования фрагментов MS MARCO.

MS MARCO выбран благодаря доступности текстов запросов и фрагментов, разреженных qrels, полученных из человеческой разметки, устоявшихся инструментов оценки и открыто доступных предобученных моделей ранжирования, что обеспечивает воспроизводимые сопоставления с предшествующими работами \cite{msmarco_datasets,reimers2019sentencebert}. Разреженность исходных меток также непосредственно мотивирует исследование дополнительной разметки внутри контролируемых пулов кандидатов. Этот выбор не означает универсальности: на переносимость могут влиять особенности выборки поисковой системы, язык, намерение запроса и предметная область документов. Наш анализ относится к англоязычной коллекции MS MARCO и заданному протоколу разметки и пулинга, а не ко всем пользователям и сценариям поиска.

## 2. Related Work

Suggested position: after the opening dataset paragraph in Related Work. This compact paragraph complements, rather than repeats, the three provider examples.

### EN (55 words)

Beyond provider-specific resources, BEIR evaluates retrieval across 18 datasets covering diverse tasks and domains \cite{thakur2021beir}. This addresses cross-dataset robustness rather than representativeness of countries or social groups. Our study instead isolates annotation coverage and candidate selection within one collection; BEIR provides a relevant framework for future external validation, but no such evaluation is reported here.

### RU

Помимо ресурсов отдельных поисковых компаний, BEIR оценивает поиск на 18 наборах данных с разнообразными задачами и предметными областями \cite{thakur2021beir}. Такая оценка характеризует устойчивость между наборами данных, а не репрезентативность стран или социальных групп. В нашей работе охват разметки и отбор кандидатов исследуются внутри одной коллекции; BEIR задаёт подходящую основу для последующей внешней проверки, которая здесь не проводилась.

## 3. External Validity

Suggested position: expand the existing scope restriction in Discussion, without repeating an adjacent sentence that already limits conclusions to MS MARCO.

### EN (60 words)

Our findings are limited to English MS MARCO and the evaluated pools. Provider, language, intent, and document-domain differences may change relevance judgments and system comparisons. We do not evaluate differences across countries or social groups, so population-level generalization is untested. Additional judgments improve coverage within selected pools; they do not provide exhaustive corpus annotations or representative coverage of user populations.

### RU (57 words)

Выводы ограничены англоязычной MS MARCO и исследованными пулами. Различия поисковых систем, языков, намерений запросов и предметных областей документов могут менять оценки релевантности и сопоставления систем. Различия между странами и социальными группами не исследовались, поэтому обобщение на эти группы не проверено. Дополнительная разметка расширяет охват выбранных пулов, но не обеспечивает исчерпывающую разметку корпуса или репрезентативный охват пользовательских групп.

## 4. Response to Reviewer 3

Response-letter draft. The completed-change wording below is appropriate only after the corresponding insertions have been incorporated into both manuscript versions.

### EN

Thank you for requesting broader dataset context and clarification of generalizability. We have added three concrete provider counterparts: Google's Natural Questions, Yahoo! Webscope Learning to Rank set 1/set 2, and Yandex's Personalized Web Search Challenge. We distinguish their text, feature, and interaction-log representations without treating them as interchangeable benchmarks or claiming an exhaustive inventory. We explain that MS MARCO supports comparison with prior work through available texts, sparse human-derived qrels, pretrained models, and evaluation tools. We also discuss BEIR and explicitly limit our findings to English MS MARCO and the studied pools. Transfer across countries and social groups has not been evaluated; no demographic representativeness is claimed. These changes clarify context and scope without adding experiments.

### RU

Благодарим за предложение расширить контекст наборов данных и уточнить границы обобщения. Добавлены три конкретных аналога от поисковых компаний: Natural Questions компании Google, Yahoo! Webscope Learning to Rank set 1/set 2 и Yandex Personalized Web Search Challenge. Мы разграничили текстовые данные, признаки ранжирования и журналы взаимодействий, не представляя эти ресурсы как взаимозаменяемые бенчмарки или исчерпывающий перечень. Выбор MS MARCO обоснован сопоставимостью с предшествующими работами благодаря доступности текстов, разреженных qrels на основе человеческой разметки, предобученных моделей и инструментов оценки. Также обсуждается BEIR и явно ограничивается область выводов англоязычной MS MARCO и исследованными пулами. Переносимость между странами и социальными группами не оценивалась; демографическая репрезентативность не утверждается. Изменения уточняют контекст и границы работы без новых экспериментов.

## 5. Reviewer 1: One Terminological Clarification

Suggested position: first occurrence of "deep re-annotation" in the main text. This is a definition, not an additional empirical claim.

### EN

Here, "deep re-annotation" means collecting denser relevance judgments for candidates within a defined pool; it refers to annotation coverage, not neural-network depth, and does not imply exhaustive corpus annotation.

### RU

Под «глубокой доразметкой» понимается получение более плотных оценок релевантности кандидатов внутри заданного пула; термин относится к охвату разметки, а не к глубине нейронной сети, и не означает исчерпывающей разметки корпуса.

## 6. Verified Source Notes

These notes support the insertions; they are not additional paragraphs for the article. Historical release, readable content, and current access or reuse rights are separate claims.

| Resource | Verified scope and relevance to this paper | Access and licensing boundary |
| --- | --- | --- |
| Google: Natural Questions, Kwiatkowski et al. (2019) | Real Google queries, human answers on Wikipedia; original task is page-based QA, not MS MARCO passage ranking. Section 3.1 documents query filtering and Wikipedia-in-top-five selection, so this is not an unfiltered query sample. [Paper](https://aclanthology.org/Q19-1026/) | Google provides train/dev download instructions; the original test set is held out. The download page states "Creative Commons Share-Alike 3.0". The repository's Apache-2.0 code license is not the dataset license. [Official download page](https://ai.google.com/research/NaturalQuestions/download), [provider repository](https://github.com/google-research-datasets/natural-questions) |
| Yahoo!: Learning to Rank set 1/set 2, Chapelle and Chang (2011) | Feature vectors and editorial grades, not raw QA. Section 4 identifies US set 1 and an unnamed Asian-country set 2; query text and URLs were withheld. [Paper, Section 4](https://proceedings.mlr.press/v14/chapelle11a/chapelle11a.pdf) | Section 4.3 documents Webscope distribution and explicitly says this dataset was not restricted to academic researchers. The legacy Webscope site could not be retrieved in this check; current download access and precise reuse terms remain unverified. Do not call it academic-only or unrestricted open-license data. [Publication](https://proceedings.mlr.press/v14/chapelle11a.html) |
| Yandex: Personalized Web Search Challenge (2013-2014) | Numeric IDs encode users, queries, terms, sessions, URLs and domains, with rankings and clicks. Sampling covered one large city and excluded sessions with detected commercial intent. These are behavioral data, not readable Russian QA or a national population sample. [Official data description](https://www.kaggle.com/c/yandex-personalized-Web-search-challenge/data) | The indexed official page lists train/test files and a sign-in/rules-acceptance gate, with license "Subject to Competition Rules". Downloads and detailed reuse permissions were not tested. Challenge dates establish the 2013 start and 2014 close. [Official overview](https://www.kaggle.com/c/yandex-personalized-web-search-challenge) |
| BEIR, Thakur et al. (2021) | The published benchmark contains 18 datasets across retrieval tasks and domains. It motivates cross-dataset validation, not population representativeness. Use the published scope, not an assumed current dataset count. [Conference publication](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html) | The paper links its public implementation and documents the underlying collections. No blanket data-license claim is needed here; this check did not audit every component's terms. [Paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/65b9eea6e1cc6bb9f0cd2a47751a186f-Paper-round2.pdf) |

The Yandex facts above were recoverable from the search-indexed official Kaggle data page; direct page extraction returned an empty dynamic shell. This supports the description and displayed access gate, not a claim that a download was successfully completed.

### MS MARCO Rationale

The official ranking documentation identifies sparse judgments, human passage labels, query/passage files and candidate lists. Microsoft's data terms limit use to non-commercial research; public access should not be described as unrestricted licensing. These facts support a controlled re-annotation study and comparison with prior work, not universal coverage. [Official ranking datasets](https://microsoft.github.io/msmarco/Datasets), [MS MARCO project](https://microsoft.github.io/msmarco/)

For tooling, the provider's repository contains baseline and evaluation resources. The manuscript already identifies its public MiniLM cross-encoder and Sentence-Transformers citation; retain that model reference rather than adding another dataset citation to justify model availability. Comparability here means reuse of a research setting, not equivalence between pooled scores and full-corpus leaderboard scores. [Official ranking repository](https://github.com/microsoft/MSMARCO-Passage-Ranking)

### Interpretation Boundaries

- Provider provenance is not evidence of a particular nationality, income, age, or other social-group composition. Country or city sampling facts do not establish demographic representativeness.
- Language, query intent, document domain, provider selection, and annotation design are potential limits on transfer. The proposed text treats them as methodological concerns, not effects measured in this paper.
- Yahoo's missing text and Yandex's identifier-only representation prevent directly applying this paper's text-pair re-annotation protocol to those released files. This is an inference from the published formats, not a claim that these providers have never released other resources.
- The three examples are counterparts at the level of search research, not exact equivalents of the original MS MARCO QA dataset or its passage-ranking task.
- More judgments within a pool do not make that pool representative of all documents or users. Pseudo-labels remain distinct from human judgments.
- The response does not claim new cross-dataset, multilingual, geographic, or demographic experiments. Manual examples and other reviewer requests are outside this insertion package.

## 7. Four Core LaTeX Bibliography Entries

Use these with the manuscript's existing `thebibliography` format. Full author lists and years follow the primary publication metadata. The Yandex entry uses the dataset provider as corporate author and the challenge start year, not a fabricated paper citation.

```latex
\bibitem{kwiatkowski2019naturalquestions}
T.~Kwiatkowski, J.~Palomaki, O.~Redfield, M.~Collins, A.~Parikh,
C.~Alberti, D.~Epstein, I.~Polosukhin, J.~Devlin, K.~Lee,
K.~Toutanova, L.~Jones, M.~Kelcey, M.-W.~Chang, A.~M.~Dai,
J.~Uszkoreit, Q.~Le, S.~Petrov.
\newblock \textit{Natural Questions: A Benchmark for Question Answering Research}.
\newblock Transactions of the Association for Computational Linguistics, 7, 2019.
\newblock \url{https://aclanthology.org/Q19-1026/}.
\newblock DOI: \url{https://doi.org/10.1162/tacl_a_00276}.

\bibitem{chapelle2011yahoo}
O.~Chapelle, Y.~Chang.
\newblock \textit{Yahoo! Learning to Rank Challenge Overview}.
\newblock Proceedings of the Learning to Rank Challenge,
Proceedings of Machine Learning Research, 14:1--24, 2011.
\newblock \url{https://proceedings.mlr.press/v14/chapelle11a.html}.

\bibitem{yandex2013personalized}
Yandex.
\newblock \textit{Personalized Web Search Challenge}.
\newblock Kaggle competition, 2013--2014.
\newblock \url{https://www.kaggle.com/c/yandex-personalized-web-search-challenge}.
\newblock Dataset description:
\url{https://www.kaggle.com/c/yandex-personalized-Web-search-challenge/data}.
\newblock Accessed 14 September 2026.

\bibitem{thakur2021beir}
N.~Thakur, N.~Reimers, A.~R\"uckl\'e, A.~Srivastava, I.~Gurevych.
\newblock \textit{BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models}.
\newblock Proceedings of the Neural Information Processing Systems Track
on Datasets and Benchmarks, 1, 2021.
\newblock \url{https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html}.
```

## 8. Optional Multilingual Extension: MIRACL

Use this only if a fifth reference fits. It adds direct multilingual context beyond BEIR's task/domain diversity; it does not replace the three provider counterparts. Cite the final 2023 TACL article, not the earlier 2022 preprint title. The authors describe same-language retrieval over Wikipedia with native-speaker annotations; multilingual coverage alone is not evidence of country or social-group representativeness. [Published paper and full metadata](https://aclanthology.org/2023.tacl-1.63/)

### EN

MIRACL complements this perspective with Wikipedia retrieval and native-speaker relevance judgments across 18 languages \cite{zhang2023miracl}. Its multilingual scope motivates examining transfer beyond English, but does not itself establish representativeness across countries or social groups. Such validation is outside the present study.

### RU

MIRACL дополняет этот подход поиском по Википедии и оценками релевантности от носителей 18 языков \cite{zhang2023miracl}. Его многоязычный охват мотивирует изучение переносимости за пределы английского языка, но сам по себе не устанавливает репрезентативность стран или социальных групп. Такая проверка выходит за рамки настоящей работы.

```latex
\bibitem{zhang2023miracl}
X.~Zhang, N.~Thakur, O.~Ogundepo, E.~Kamalloo, D.~Alfonso-Hermelo,
X.~Li, Q.~Liu, M.~Rezagholizadeh, J.~Lin.
\newblock \textit{MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages}.
\newblock Transactions of the Association for Computational Linguistics,
11:1114--1131, 2023.
\newblock \url{https://aclanthology.org/2023.tacl-1.63/}.
\newblock DOI: \url{https://doi.org/10.1162/tacl_a_00595}.
```
