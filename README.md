# Hybrid Retrieval Evaluation

Evaluation of lexical, dense and hybrid retrieval on MS MARCO with controlled
candidate pools, manual relevance judgments and reciprocal rank fusion (RRF).
The repository contains the development notebook, maintained evaluation scripts,
saved results, manuscript sources and the final conference presentation.

![Presentation preview](docs/presentation-preview.png)

## Explore the project

| Material | Files |
| --- | --- |
| Retrieval and training development | [Jupyter notebook](msmarco_final.ipynb) |
| Evaluation code and commands | [revision_2026](revision_2026/README.md) |
| Saved numerical results | [revision_2026/results](revision_2026/results/) |
| Manuscripts with recomputed results | [English PDF](delivery_revision/manuscript_en.pdf) · [Russian PDF](delivery_revision/manuscript_ru.pdf) · [LaTeX and build instructions](delivery_revision/README_RU.md) |
| Latest editorial manuscript | [Version notes and sources](original_based_2026/README.md) |
| Final presentation | [PDF](DAMDID_2026_Проверено_13-10/DAMDID_2026_Презентация_RU.pdf) · [PowerPoint](DAMDID_2026_Проверено_13-10/DAMDID_2026_Презентация_RU.pptx) |
| Presentation speech | [DOCX](DAMDID_2026_Проверено_13-10/DAMDID_2026_Текст_выступления_RU.docx) |

The manual analysis covers **1,179 queries and 33,667 query–document pairs**.
The full saved-score analysis covers **101,093 queries and 45,647,587 scores**.
Saved outputs include query-level metrics, paired uncertainty estimates,
bootstrap replicates, labels and query splits.

## Run the analysis tools

Use Python 3.12 or newer in a separate environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python revision_2026/fullset_eval.py --self-test
```

The included results are sufficient to rebuild the manuscript tables and figures:

```sh
.venv/bin/python revision_2026/build_tables.py
.venv/bin/python revision_2026/make_figures.py
```

These commands write to `delivery_revision/`. See the
[evaluation guide](revision_2026/README.md) for arguments and recomputation from
the research archive, and [ENVIRONMENT.md](ENVIRONMENT.md) for document builds.
The notebook retains its development code with saved cell outputs cleared;
its model and data dependencies are listed within the notebook.

## Reading the results

Use `revision_2026/results/` and `delivery_revision/` for the checked evaluation.
Systems share the same pool-based IDCG and query set; queries with zero gain
remain in the averages. The evaluation reuses saved retrieval runs, judge scores
and labels. It does not represent a new training run or a recovered checkpoint.
See the [methodological notes](delivery_revision/AUTHOR_NOTES_RU.md) for scope
and remaining interpretation limits.

`original_based_2026/source/` is a distinct editorial version that retains earlier
reported numerical values. It is preserved as the latest version of that text,
and must be distinguished from the recomputed analysis. Its
[version notes](original_based_2026/ПОЯСНЕНИЕ.md) explain the differences.

## Data and full archive

The [Telegram index](https://t.me/zzakazzy/37) contains the complete 25-part
research-data archive, additional result arrays and the full development snapshot.
The [part manifest](data/retrieval-data.parts.json) lists the exact links, sizes
and SHA-256 values. Follow [RESTORE.md](RESTORE.md) to obtain the matching data.

The original upstream MS MARCO corpus, queries and official qrels are obtained
from their source using [tools/fetch_upstream.py](tools/fetch_upstream.py).
[MS MARCO source terms](https://microsoft.github.io/msmarco/Notice.html) continue
to apply. Scientific references and bundled template notices are retained.

The current branch contains one canonical copy of each retained project component.
Earlier deliveries and intermediate builds are available in the
[dated full snapshot](ARCHIVE.md).
