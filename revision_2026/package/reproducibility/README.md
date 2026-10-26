# Reproducing the revised results

These scripts recompute evaluation from saved annotations, retrieval runs and judge scores. They do not train a new judge or claim to recover missing model weights.

## Tables and figures from included results

Python 3.12 or newer is recommended. From the manuscript directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/requirements.txt
.venv/bin/python reproducibility/build_tables.py --package .
.venv/bin/python reproducibility/make_figures.py --results reproducibility/results --output figures
```

The included summaries and per-query arrays are sufficient for rebuilding the tables and figures. The plot generator checks that numerical means match the summaries. PDF and SVG are vector outputs; PNGs are 300 dpi. PDF fonts are embedded; editable SVG text uses DejaVu Sans.

## Evaluation from the original archive

The original `phd2.zip` archive is approximately 26 GiB and is not duplicated in this delivery. The scripts read relevant entries directly; extracting the whole archive, downloading models and running GPU inference are unnecessary.

```sh
.venv/bin/python reproducibility/manual_eval.py --archive /path/to/phd2.zip --output reproducibility/results
.venv/bin/python reproducibility/fullset_eval.py --zip /path/to/phd2.zip
.venv/bin/python reproducibility/build_tables.py --package .
.venv/bin/python reproducibility/make_figures.py --results reproducibility/results --output figures
```

The full-set evaluator creates a local `reproducibility/cache/` directory. It validates run ordering, candidate coverage, shared ideal normalization, missing-score counts, zero-positive queries, rank-fusion tie handling, and the overlap with manual queries. Its synthetic/reference tests can run without the archive:

```sh
.venv/bin/python reproducibility/fullset_eval.py --self-test
```

## Files and interpretation

- `manual_summary.json`: label counts, metrics, paired effects and held-out judge agreement.
- `manual_per_query.npz`: per-query manual-pool scores; use `models` to identify columns.
- `manual_splits.json`: training, validation and test query IDs.
- `manual_judge_qrels.json`: labels regenerated from one fixed threshold.
- `manual_judge_diagnostics.npz`: standard-label, nonempty-text pairs, including training queries. Not a held-out dataset.
- `fullset_summary.json`: all-query results, manual-query exclusion analysis and statistical contrasts.
- `fullset_perquery.npz`: per-query metrics, counts and ranking diagnostics.
- `fullset_inference_replicates.npz`: bootstrap and paired sign-flip replicates.
- `fullset_provenance.json`: source-entry sizes, CRCs and runtime information.
- `fullset_validation.json`: successful exact-array comparison between repeated full-set evaluations.
- `verification_report.json`: manual rerun, concrete-example and compiled-PDF checks.

RRF(3) uses BM25, E5 and BGE only, with constant 60. Auxiliary annotation channels are not treated as verified retrieval architectures. Ranking scores computed against automatic labels measure agreement with this judge, not independent human validation. Revisions to IDCG and query inclusion change the numerical results relative to the previous manuscript; see `AUTHOR_NOTES_RU.md`.

The original training used nonstandard annotation categories as zero labels. The revision documents this inherited limitation and does not describe those categories as confirmed human negatives. More recent judges and reference-conditioned training remain future work.

Machine-specific absolute paths are removed from the distribution's JSON provenance; source sizes, CRCs and numerical results are preserved.
