# Evaluation and saved results

This directory contains the current evaluation code and saved numerical results.
The scripts evaluate saved retrieval runs, annotations, and judge scores; they
do not train a new model or recover a training checkpoint. The manual analysis
covers 1,179 queries and 33,667 query–document pairs. The full saved-score analysis
covers 101,093 queries and 45,647,587 scores.

Run the commands below from the repository root with Python 3.12 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Tables and figures from included results

The files in `results/` are sufficient to rebuild the manuscript tables and
figures without downloading the research archive:

```sh
.venv/bin/python revision_2026/build_tables.py
.venv/bin/python revision_2026/make_figures.py
```

The defaults write tables, numerical macros, and interpretation text to
`delivery_revision/`, and figures to `delivery_revision/figures/`. To write to a
different location, pass `--package PATH` to `build_tables.py` and `--output PATH`
to `make_figures.py`. The figure builder also accepts `--results PATH` and
`--language en`, `ru`, or `both`.

## Recompute from saved runs and annotations

Download and join the research archive parts using the manifest and instructions
in [the Telegram archive index](https://t.me/zzakazzy/37). Keep the joined archive
as `retrieval-data.zip`, or replace that path in the commands below. The scripts
read the needed ZIP entries directly; extracting the complete archive is
unnecessary for these evaluations.

The anonymized archive omits the upstream official qrels. Obtain the exact small
development reference and pass it explicitly to the manual evaluator:

```sh
.venv/bin/python tools/fetch_upstream.py qrels --output data/qrels.dev.small.tsv
.venv/bin/python revision_2026/manual_eval.py \
  --archive retrieval-data.zip \
  --official-qrels data/qrels.dev.small.tsv \
  --output revision_2026/results
.venv/bin/python revision_2026/fullset_eval.py --zip retrieval-data.zip
```

The download helper and manual evaluator check the expected official qrels
version. Upstream data retain their original terms. The full-set evaluator
rebuilds a local `revision_2026/cache/` and writes results into
`revision_2026/results/`; allow space for those generated files. Evaluation
commands replace their corresponding saved result files. The repository includes
the saved results from the published analysis.

The full-set evaluator includes a small synthetic reference check that requires
no research archive:

```sh
.venv/bin/python revision_2026/fullset_eval.py --self-test
```

## Result files

- `manual_summary.json`, `manual_per_query.npz`: manual-pool metrics and paired
  uncertainty estimates.
- `manual_splits.json`, `manual_judge_qrels.json`: query splits and labels
  regenerated from the fixed judge threshold.
- `manual_judge_diagnostics.npz`: standard-label pairs with nonempty original
  text, including training queries; these diagnostics are not held-out results.
- `fullset_summary.json`, `fullset_perquery.npz`: full-set metrics and
  query-level diagnostics.
- `fullset_inference_replicates.npz`: saved bootstrap and randomization
  replicates.
- `fullset_provenance.json`, `fullset_validation.json`: recorded provenance and
  historical repeat-comparison information.

RRF(3) combines BM25, E5, and BGE with constant 60. Full-set metrics measure
agreement with the saved judge labels; they do not independently establish human
relevance. Provenance records describe the historical evaluation, rather than a
new run on the cleaned repository.

The root `msmarco_final.ipynb` preserves the original retrieval and training
development code with saved outputs cleared. It has additional model and data
dependencies; use this directory's scripts and saved results for the current
checked evaluation. Restoring raw annotation text for the notebook requires the
upstream sources and `tools/hydrate_annotations.py`, as described in the archive
restoration instructions.
