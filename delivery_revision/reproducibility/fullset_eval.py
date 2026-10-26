#!/usr/bin/env python3
"""Streaming, reproducible pooled-pseudoqrel evaluation of retrieval-data.zip.

Run: python fullset_eval.py --zip /path/to/retrieval-data.zip
Test: python fullset_eval.py --self-test

Only the three run files, raw judge scores, judge configuration, and human
query IDs are read. No corpus, embeddings, training, or archived pseudoqrels.
Dependencies: numpy, pandas, ijson. All output paths have a fullset prefix.
Caches are reusable only when their schema and ZIP entry CRC/size match.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import platform
import resource
import sys
import time
import zipfile

import numpy as np
import pandas as pd


KS = np.array([10, 30, 50, 100, 200], dtype=np.int64)
MODELS = ["bm25", "e5", "bge", "rrf_variable", "rrf_fixed200"]
RUN_MODELS = MODELS[:3]
THRESHOLD = -0.21871782839298248
RRF_C = 60
DEPTH = 200
SENTINEL = np.iinfo(np.uint32).max
DISCOUNTS = 1.0 / np.log2(np.arange(2, 12, dtype=np.float64))
IDEALS = np.r_[0.0, np.cumsum(DISCOUNTS)]
RUN_SCHEMA = 1
LABEL_SCHEMA = 1
EVAL_SCHEMA = 1
START = time.monotonic()


def rss_gib():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024**3 if sys.platform == "darwin" else 1024**2)


def log(event, **kwargs):
    print(json.dumps({"event": event, "elapsed_seconds": round(time.monotonic() - START, 2),
                      "peak_rss_gib": round(rss_gib(), 3), **kwargs}), flush=True)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(path)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class HashingReader(io.RawIOBase):
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.digest = hashlib.sha256()
        self.byte_count = 0

    def readable(self):
        return True

    def read(self, size=-1):
        data = self.source.read(size)
        self.digest.update(data)
        self.byte_count += len(data)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


class UniqueDict(dict):
    """Reject duplicate JSON document keys rather than silently replacing scores."""

    def __setitem__(self, key, value):
        require(key not in self, f"Duplicate JSON key: {key}")
        super().__setitem__(key, value)


def entry_record(info):
    return {"name": info.filename, "crc32": f"{info.CRC:08x}",
            "uncompressed_size": info.file_size, "compressed_size": info.compress_size,
            "compression_type": info.compress_type}


def resolve_entries(archive):
    suffixes = {model: f"msmarco/run_files/{model}.run" for model in RUN_MODELS}
    suffixes.update(scores="output_fixed/msmarco_full/judge_scores_full.json",
                    config="output_fixed/judge_config.json",
                    manual="output_fixed/human_qrels_extended.json")
    result = {}
    for key, suffix in suffixes.items():
        matches = [info for info in archive.infolist() if info.filename.endswith(suffix)]
        require(len(matches) == 1, f"Expected one entry for {suffix}, got {len(matches)}")
        result[key] = entry_record(matches[0])
    return result


def read_small_json(archive, record):
    data = archive.read(record["name"])
    record["sha256_uncompressed"] = hashlib.sha256(data).hexdigest()
    record["streamed_bytes"] = len(data)
    return json.loads(data)


def signature(records, keys):
    return {key: {field: records[key][field] for field in
                  ("name", "crc32", "uncompressed_size", "compressed_size")}
            for key in keys}


def cache_matches(path, expected):
    if not path.exists():
        return False
    with path.open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    return all(metadata.get(key) == value for key, value in expected.items())


def load_runs(archive, records, cache, expected_queries, chunksize, refresh):
    manifest_path = cache / "fullset_runs_manifest.json"
    runs_path = cache / "fullset_runs.npy"
    query_path = cache / "fullset_query_ids.npy"
    expected = {"schema": RUN_SCHEMA, "inputs": signature(records, RUN_MODELS),
                "expected_queries": expected_queries, "depth": DEPTH}
    if (not refresh and runs_path.exists() and query_path.exists()
            and cache_matches(manifest_path, expected)):
        metadata = json.loads(manifest_path.read_text())
        for model in RUN_MODELS:
            records[model].update(metadata["hashes"][model])
        log("run_cache_loaded")
        return np.load(runs_path, mmap_mode="r"), np.load(query_path), metadata

    runs = np.full((expected_queries, 3, DEPTH), SENTINEL, dtype=np.uint32)
    query_to_index = {}
    audit = {}
    for model_index, model in enumerate(RUN_MODELS):
        row_count = 0
        retained = 0
        query_present = np.zeros(expected_queries, dtype=bool)
        with archive.open(records[model]["name"]) as source:
            reader = HashingReader(source)
            chunks = pd.read_csv(reader, sep=r"\s+", header=None,
                                 names=["qid", "q0", "docid", "rank", "score", "tag"],
                                 usecols=["qid", "docid", "rank", "score"],
                                 dtype={"qid": np.int64, "docid": np.int64,
                                        "rank": np.int64, "score": np.float64},
                                 chunksize=chunksize)
            for frame in chunks:
                row_count += len(frame)
                qids = frame.qid.to_numpy()
                require(np.all(qids >= 0), "Negative query ID")
                require(np.all(np.isfinite(frame.score.to_numpy())), "Non-finite run score")
                for qid in np.unique(qids):
                    if int(qid) not in query_to_index:
                        require(len(query_to_index) < expected_queries,
                                "Run query union exceeds --expected-queries")
                        query_to_index[int(qid)] = len(query_to_index)
                rows = frame.qid.map(query_to_index).to_numpy(dtype=np.int64)
                query_present[rows] = True
                ranks = frame["rank"].to_numpy()
                docs = frame.docid.to_numpy()
                require(np.all(ranks >= 1), "Run ranks must be 1-based")
                require(np.all((docs >= 0) & (docs < SENTINEL)), "Invalid document ID")
                keep = ranks <= DEPTH
                rows, ranks, docs = rows[keep], ranks[keep] - 1, docs[keep]
                keys = rows * DEPTH + ranks
                require(len(np.unique(keys)) == len(keys), "Duplicate query/rank within chunk")
                require(np.all(runs[rows, model_index, ranks] == SENTINEL),
                        "Duplicate query/rank across chunks")
                runs[rows, model_index, ranks] = docs
                retained += len(rows)
                if row_count % (chunksize * 4) == 0:
                    log("run_progress", model=model, rows=row_count,
                        queries_seen=len(query_to_index))
            require(reader.byte_count == records[model]["uncompressed_size"],
                    "Run stream did not reach end of ZIP entry")
            records[model].update(sha256_uncompressed=reader.digest.hexdigest(),
                                  streamed_bytes=reader.byte_count)
        audit[model] = {"rows": row_count, "rows_top200": retained,
                        "queries_present": int(query_present.sum())}
        log("run_complete", model=model, **audit[model])

    require(len(query_to_index) == expected_queries,
            f"Expected {expected_queries} run-union queries, got {len(query_to_index)}")
    original_ids = np.fromiter(query_to_index, dtype=np.int64)
    order = np.argsort(original_ids)
    query_ids = original_ids[order]
    runs = runs[order]
    for m, model in enumerate(RUN_MODELS):
        ordered_docs = np.sort(runs[:, m], axis=1)
        duplicates = (ordered_docs[:, 1:] == ordered_docs[:, :-1]) & (ordered_docs[:, 1:] != SENTINEL)
        require(not np.any(duplicates), f"Duplicate document within {model} query ranking")
        present = runs[:, m] != SENTINEL
        counts = present.sum(axis=1)
        gaps = present & (np.arange(DEPTH)[None, :] >= counts[:, None])
        require(not np.any(gaps), f"Noncontiguous ranks in {model}")
        audit[model].update(queries_missing=int(np.sum(counts == 0)),
                            queries_short_top10=int(np.sum(counts < 10)),
                            queries_short_top200=int(np.sum(counts < 200)),
                            min_retained=int(counts.min()), max_retained=int(counts.max()))
    np.save(runs_path, runs, allow_pickle=False)
    np.save(query_path, query_ids, allow_pickle=False)
    metadata = {**expected, "audit": audit,
                "hashes": {model: {key: records[model][key] for key in
                                   ("sha256_uncompressed", "streamed_bytes")}
                           for model in RUN_MODELS}}
    atomic_json(manifest_path, metadata)
    del runs
    return np.load(runs_path, mmap_mode="r"), query_ids, metadata


def load_labels(archive, records, runs, query_ids, cache, expected_scores, refresh):
    import ijson

    manifest_path = cache / "fullset_labels_manifest.json"
    labels_path = cache / "fullset_labels.npy"
    audit_path = cache / "fullset_score_audit.npz"
    expected = {"schema": LABEL_SCHEMA,
                "inputs": signature(records, [*RUN_MODELS, "scores", "config"]),
                "threshold": THRESHOLD, "comparison": ">=", "expected_scores": expected_scores}
    if (not refresh and labels_path.exists() and audit_path.exists()
            and cache_matches(manifest_path, expected)):
        metadata = json.loads(manifest_path.read_text())
        records["scores"].update(metadata["hashes"])
        with np.load(audit_path) as data:
            audits = {key: data[key] for key in data.files}
        log("label_cache_loaded")
        return np.load(labels_path, mmap_mode="r"), audits, metadata

    n = len(query_ids)
    labels = np.full(runs.shape, -1, dtype=np.int8)
    query_to_index = {str(int(qid)): i for i, qid in enumerate(query_ids)}
    seen = np.zeros(n, dtype=bool)
    audits = {key: np.zeros(n, dtype=np.int32) for key in
              ("score_count", "raw_positive_count", "scores_outside_union200",
               "missing_union200", "threshold_equal_count")}
    query_count = 0
    with archive.open(records["scores"]["name"]) as source:
        reader = HashingReader(source)
        for qid, scores in ijson.kvitems(reader, "", use_float=True, map_type=UniqueDict):
            require(qid in query_to_index, f"Scored query absent from all runs: {qid}")
            i = query_to_index[qid]
            require(not seen[i], f"Repeated score query: {qid}")
            seen[i] = True
            require(isinstance(scores, dict), f"Scores are not a mapping for {qid}")
            values = np.fromiter(scores.values(), dtype=np.float64, count=len(scores))
            require(np.all(np.isfinite(values)), f"Non-finite score in query {qid}")
            audits["score_count"][i] = len(values)
            audits["raw_positive_count"][i] = np.sum(values >= THRESHOLD)
            audits["threshold_equal_count"][i] = np.sum(values == THRESHOLD)
            docs, inverse = np.unique(runs[i].ravel(), return_inverse=True)
            unique_labels = np.full(len(docs), -1, dtype=np.int8)
            matched = 0
            for j, doc in enumerate(docs):
                if doc == SENTINEL:
                    continue
                score = scores.get(str(int(doc)))
                if score is not None:
                    unique_labels[j] = int(score >= THRESHOLD)
                    matched += 1
            labels[i] = unique_labels[inverse].reshape(3, DEPTH)
            audits["scores_outside_union200"][i] = len(scores) - matched
            audits["missing_union200"][i] = int(np.sum(docs != SENTINEL)) - matched
            query_count += 1
            if query_count % 5000 == 0:
                log("score_progress", queries=query_count,
                    pairs=int(audits["score_count"].sum()),
                    positives=int(audits["raw_positive_count"].sum()))
        require(reader.byte_count == records["scores"]["uncompressed_size"],
                "Score stream did not reach end of ZIP entry")
        records["scores"].update(sha256_uncompressed=reader.digest.hexdigest(),
                                 streamed_bytes=reader.byte_count)
    for i in np.flatnonzero(~seen):
        audits["missing_union200"][i] = len(np.unique(runs[i][runs[i] != SENTINEL]))
    audits["score_query_present"] = seen
    total = int(audits["score_count"].sum())
    require(total == expected_scores, f"Expected {expected_scores} scores; got {total}")
    np.save(labels_path, labels, allow_pickle=False)
    np.savez_compressed(audit_path, **audits)
    metadata = {**expected, "query_count": query_count, "score_count": total,
                "positive_count": int(audits["raw_positive_count"].sum()),
                "queries_without_score_record": int((~seen).sum()),
                "scores_outside_union200": int(audits["scores_outside_union200"].sum()),
                "missing_union200": int(audits["missing_union200"].sum()),
                "threshold_equal_count": int(audits["threshold_equal_count"].sum()),
                "ijson_backend": ijson.backend,
                "hashes": {key: records["scores"][key] for key in
                           ("sha256_uncompressed", "streamed_bytes")}}
    atomic_json(manifest_path, metadata)
    log("scores_complete", **{key: metadata[key] for key in
                               ("query_count", "score_count", "positive_count",
                                "scores_outside_union200", "missing_union200")})
    del labels
    return np.load(labels_path, mmap_mode="r"), audits, metadata


def query_metrics(run, labels):
    """Compute each system against the SAME binary ideal for each pool depth."""
    flat = run.ravel()
    valid = flat != SENTINEL
    docs, inverse = np.unique(flat[valid], return_inverse=True)
    rank_values = np.tile(np.arange(1, DEPTH + 1), 3)[valid]
    model_values = np.repeat(np.arange(3), DEPTH)[valid]
    ranks = np.full((len(docs), 3), DEPTH + 1, dtype=np.int64)
    ranks[inverse, model_values] = rank_values
    first_rank = ranks.min(axis=1) if len(docs) else np.array([], dtype=np.int64)
    y = np.full(len(docs), -1, dtype=np.int8)
    y[inverse] = labels.ravel()[valid]
    require(np.array_equal(y[inverse], labels.ravel()[valid]), "Inconsistent duplicate labels")
    index_matrix = np.full(run.shape, -1, dtype=np.int64)
    index_matrix.ravel()[valid] = inverse
    base_lists = [row[row >= 0] for row in index_matrix[:, :10]]
    fused = []
    tie_count = np.zeros(len(KS), dtype=np.uint16)
    for j, k in enumerate(KS):
        contributions = np.where(ranks <= k, 1.0 / (RRF_C + ranks), 0.0)
        # Sorting the three contributions makes sums invariant to model order.
        scores = np.sort(contributions, axis=1).sum(axis=1)
        members = np.flatnonzero(first_rank <= k)
        ordered = members[np.lexsort((docs[members], -scores[members]))]
        fused.append(ordered[:10])
        ordered_scores = scores[ordered]
        tie_count[j] = np.sum(ordered_scores[1:] == ordered_scores[:-1])
    shape = (len(KS), len(MODELS))
    result = {key: np.zeros(shape, dtype=np.uint8) for key in
              ("top10_count", "top10_positive", "top10_unjudged", "top10_outside_pool",
               "top10_missing_score")}
    result.update(ndcg=np.zeros(shape, dtype=np.float64), dcg=np.zeros(shape, dtype=np.float64),
                  candidate_count=np.zeros(len(KS), dtype=np.uint16),
                  positive_count=np.zeros(len(KS), dtype=np.uint16),
                  missing_score_count=np.zeros(len(KS), dtype=np.uint16),
                  idcg=np.zeros(len(KS), dtype=np.float64),
                  rrf_tied_adjacent_scores=tie_count,
                  rrf_top10_docids=np.full((len(KS), 10), SENTINEL, dtype=np.uint32))
    for j, k in enumerate(KS):
        in_pool = first_rank <= k
        gains = (y == 1) & in_pool
        positives = int(gains.sum())
        ideal = IDEALS[min(positives, 10)]
        result["candidate_count"][j] = in_pool.sum()
        result["positive_count"][j] = positives
        result["missing_score_count"][j] = np.sum(in_pool & (y < 0))
        result["idcg"][j] = ideal
        result["rrf_top10_docids"][j, :len(fused[j])] = docs[fused[j]]
        for m, ranking in enumerate([*base_lists, fused[j], fused[-1]]):
            dcg = float(np.dot(gains[ranking], DISCOUNTS[:len(ranking)]))
            outside = ~in_pool[ranking]
            missing = in_pool[ranking] & (y[ranking] < 0)
            result["dcg"][j, m] = dcg
            result["ndcg"][j, m] = dcg / ideal if ideal > 0 else 0.0
            result["top10_count"][j, m] = len(ranking)
            result["top10_positive"][j, m] = gains[ranking].sum()
            result["top10_outside_pool"][j, m] = outside.sum()
            result["top10_missing_score"][j, m] = missing.sum()
            result["top10_unjudged"][j, m] = (outside | missing).sum()
    return result


def evaluate(runs, labels, query_ids, manual_ids, results, score_audits):
    arrays = None
    for i, qid in enumerate(query_ids):
        row = query_metrics(runs[i], labels[i])
        if arrays is None:
            arrays = {key: np.empty((len(query_ids), *value.shape), dtype=value.dtype)
                      for key, value in row.items()}
        for key, value in row.items():
            arrays[key][i] = value
        if (i + 1) % 5000 == 0:
            log("metric_progress", queries=i + 1)
    arrays.update(query_ids=query_ids, ks=KS, model_names=np.array(MODELS),
                  manual_overlap=np.isin(query_ids, list(manual_ids)),
                  retriever_top10_docids=np.array(runs[:, :, :10]), **score_audits)
    require(np.all(np.diff(arrays["candidate_count"].astype(np.int32), axis=1) >= 0),
            "Candidate pools are not nested")
    require(np.all(np.diff(arrays["positive_count"].astype(np.int32), axis=1) >= 0),
            "Positive pools are not nested")
    require(np.all((arrays["ndcg"] >= 0) & (arrays["ndcg"] <= 1 + 1e-12)),
            "NDCG outside [0,1]")
    require(np.all(arrays["ndcg"][arrays["idcg"] == 0] == 0), "Nonzero zero-IDCG query")
    require(np.allclose(arrays["dcg"][:, :, :3], arrays["dcg"][:, :1, :3], atol=0, rtol=0),
            "Base retriever DCG changed as pool depth changed")
    require(np.array_equal(arrays["ndcg"][:, -1, 3], arrays["ndcg"][:, -1, 4]),
            "Variable and fixed RRF differ at K=200")
    require(np.array_equal(arrays["missing_score_count"][:, -1], arrays["missing_union200"]),
            "Coverage mismatch between streaming and evaluation passes")
    np.savez_compressed(results / "fullset_perquery.npz", **arrays)
    return arrays


def finite_mean(values):
    return float(np.mean(values)) if len(values) else None


def summarize(arrays, mask):
    n = int(mask.sum())
    rows = []
    for j, k in enumerate(KS):
        positive = mask & (arrays["positive_count"][:, j] > 0)
        candidates = arrays["candidate_count"][mask, j]
        positives = arrays["positive_count"][mask, j]
        missing = arrays["missing_score_count"][mask, j]
        row = {"k": int(k), "queries": n, "positive_queries": int(positive.sum()),
               "zero_idcg_queries": n - int(positive.sum()),
               "candidate_pairs": int(candidates.sum()), "positive_pairs": int(positives.sum()),
               "candidates_mean_all_queries": finite_mean(candidates),
               "candidates_mean_positive_queries": finite_mean(arrays["candidate_count"][positive, j]),
               "positives_mean_all_queries": finite_mean(positives),
               "positives_mean_positive_queries": finite_mean(arrays["positive_count"][positive, j]),
               "missing_score_pairs": int(missing.sum()),
               "queries_with_missing_scores": int(np.sum(missing > 0)),
               "score_coverage": 1 - float(missing.sum()) / int(candidates.sum())
               if candidates.sum() else None,
               "models": {}}
        for m, model in enumerate(MODELS):
            values = arrays["ndcg"][mask, j, m]
            row["models"][model] = {
                "ndcg10_mean_all_queries": finite_mean(values),
                "ndcg10_mean_positive_queries": finite_mean(arrays["ndcg"][positive, j, m]),
                "dcg10_mean_all_queries": finite_mean(arrays["dcg"][mask, j, m]),
                "queries_with_ndcg_zero": int(np.sum(values == 0)),
                **{key + "_total": int(arrays[key][mask, j, m].sum()) for key in
                   ("top10_count", "top10_positive", "top10_unjudged",
                    "top10_outside_pool", "top10_missing_score")}}
        rows.append(row)
    return {"query_count": n, "depths": rows}


def paired_inference(deltas, repetitions, seed, batch_size=8):
    """Ordinary query bootstrap; two-sided paired Monte Carlo sign flips."""
    n, dimensions = deltas.shape
    require(n > 0, "Cannot perform inference on empty query population")
    bootstrap_rng = np.random.default_rng(np.random.SeedSequence([seed, 0]))
    signs_rng = np.random.default_rng(np.random.SeedSequence([seed, 1]))
    bootstrap = np.empty((repetitions, dimensions), dtype=np.float64)
    signflip = np.empty_like(bootstrap)
    observed = deltas.mean(axis=0)
    for begin in range(0, repetitions, batch_size):
        size = min(batch_size, repetitions - begin)
        indices = bootstrap_rng.integers(0, n, size=(size, n), dtype=np.int32)
        bootstrap[begin:begin + size] = deltas[indices].mean(axis=1)
        signs = signs_rng.integers(0, 2, size=(size, n), dtype=np.int8).astype(np.float64)
        signs *= 2
        signs -= 1
        signflip[begin:begin + size] = (signs @ deltas) / n
    tolerance = 16 * np.finfo(np.float64).eps
    extreme = (np.abs(signflip) >= np.abs(observed)[None, :] - tolerance).sum(axis=0)
    intervals = np.quantile(bootstrap, [0.025, 0.975], axis=0, method="linear")
    stats = []
    for d in range(dimensions):
        stats.append({"queries": n, "mean_delta": float(observed[d]),
                      "bootstrap_ci95": intervals[:, d].tolist(),
                      "paired_signflip_p_two_sided": float((extreme[d] + 1) / (repetitions + 1)),
                      "signflip_extreme_count": int(extreme[d]),
                      "wins": int(np.sum(deltas[:, d] > 0)),
                      "ties": int(np.sum(deltas[:, d] == 0)),
                      "losses": int(np.sum(deltas[:, d] < 0))})
    return stats, bootstrap, signflip


def inference_all(arrays, scenarios, repetitions, seed, results):
    contrasts = [(j, m) for j in range(len(KS)) for m in [3, 4]]
    deltas = np.column_stack([arrays["ndcg"][:, j, m] - arrays["ndcg"][:, j, 1]
                             for j, m in contrasts])
    output = {}
    saved = {"contrast_k": np.array([int(KS[j]) for j, _ in contrasts]),
             "contrast_model": np.array([MODELS[m] for _, m in contrasts])}
    for number, (name, mask) in enumerate(scenarios.items()):
        if not np.any(mask):
            continue
        log("inference_start", population=name, queries=int(mask.sum()), repetitions=repetitions)
        stats, bootstrap, signflip = paired_inference(deltas[mask], repetitions, seed + number)
        output[name] = [{"k": int(KS[j]), "contrast": MODELS[m] + "_minus_e5", **stat}
                        for (j, m), stat in zip(contrasts, stats)]
        saved[name + "_bootstrap_mean_delta"] = bootstrap
        saved[name + "_signflip_mean_delta"] = signflip
        log("inference_complete", population=name, k200_variable=output[name][-2])
    np.savez_compressed(results / "fullset_inference_replicates.npz", **saved)
    return output


def reference_query(run, labels):
    """Independent, intentionally simple dictionary/list implementation for tests."""
    rankings = [[int(d) for d in row if d != SENTINEL] for row in run]
    score_labels = {int(doc): int(y) for row, ys in zip(run, labels)
                    for doc, y in zip(row, ys) if doc != SENTINEL}

    def fuse(k):
        contributions = {}
        for row in rankings:
            for rank, doc in enumerate(row[:k], 1):
                contributions.setdefault(doc, []).append(1 / (RRF_C + rank))
        return sorted(contributions, key=lambda doc: (-sum(sorted(contributions[doc])), doc))[:10]

    fixed = fuse(DEPTH)
    values = []
    for k in KS:
        pool = set(itertools.chain.from_iterable(row[:k] for row in rankings))
        positives = {doc for doc in pool if score_labels[doc] == 1}
        ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(positives), 10) + 1))
        row_values = []
        for ranking in [*[row[:10] for row in rankings], fuse(int(k)), fixed]:
            dcg = sum((doc in positives) / math.log2(rank + 1)
                      for rank, doc in enumerate(ranking, 1))
            row_values.append(dcg / ideal if ideal else 0)
        values.append(row_values)
    return np.array(values)


def self_test():
    rng = np.random.default_rng(1871)
    for trial in range(60):
        run = np.full((3, DEPTH), SENTINEL, dtype=np.uint32)
        truth = rng.integers(-1, 2, size=501, dtype=np.int8)
        if trial == 0:
            truth[:] = 0
        for m in range(3):
            count = int(rng.integers(0, DEPTH + 1))
            run[m, :count] = rng.choice(501, size=count, replace=False)
        labels = np.full(run.shape, -1, dtype=np.int8)
        valid = run != SENTINEL
        labels[valid] = truth[run[valid]]
        actual = query_metrics(run, labels)
        np.testing.assert_allclose(actual["ndcg"], reference_query(run, labels), atol=1e-14, rtol=0)
        np.testing.assert_array_equal(actual["rrf_top10_docids"],
                                      query_metrics(run[::-1], labels[::-1])["rrf_top10_docids"])
    run = np.full((3, DEPTH), SENTINEL, dtype=np.uint32)
    run[0, :2], run[1, :2] = [20, 3], [3, 20]
    labels = np.where(run != SENTINEL, 1, -1).astype(np.int8)
    result = query_metrics(run, labels)
    require(result["rrf_top10_docids"][0, :2].tolist() == [3, 20], "Numeric docid tie failed")
    run[:] = SENTINEL
    run[0, :2], run[1, :2] = [20, 3], [30, 4]
    labels = np.full(run.shape, -1, dtype=np.int8)
    labels[0, :2], labels[1, :2] = [1, 0], [1, 1]
    result = query_metrics(run, labels)
    require(np.isclose(result["ndcg"][0, 0], 1 / IDEALS[3]), "IDCG was not shared")
    require(np.all(query_metrics(np.full_like(run, SENTINEL), np.full_like(labels, -1))["ndcg"] == 0),
            "Empty query not retained as zero")
    delta = np.column_stack([np.zeros(20), np.ones(20), -np.ones(20)])
    stats, boot, flips = paired_inference(delta, 200, 7)
    require(stats[0]["paired_signflip_p_two_sided"] == 1, "Zero delta p-value is not one")
    np.testing.assert_array_equal(boot[:, 1], 1)
    np.testing.assert_array_equal(flips[:, 1], -flips[:, 2])
    np.testing.assert_array_equal(boot, paired_inference(delta, 200, 7)[1])
    log("self_test_passed", randomized_query_cases=60,
        checks=["independent_reference", "numeric_ties", "shared_idcg", "zero_idcg",
                "missing_scores", "short_runs", "model_order_invariance", "bootstrap_seed",
                "paired_signflip_symmetry"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=Path("retrieval-data.zip"))
    parser.add_argument("--expected-queries", type=int, default=101093)
    parser.add_argument("--expected-scores", type=int, default=45647587)
    parser.add_argument("--chunksize", type=int, default=400000)
    parser.add_argument("--repetitions", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    require(args.repetitions >= 200, "Use at least 200 Monte Carlo repetitions")
    import ijson

    root = Path(__file__).resolve().parent
    cache, results = root / "cache", root / "results"
    cache.mkdir(exist_ok=True)
    results.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.zip) as archive:
        records = resolve_entries(archive)
        config = read_small_json(archive, records["config"])
        require(config["threshold"] == THRESHOLD, "Configured threshold differs from required threshold")
        manual = read_small_json(archive, records["manual"])
        manual_ids = set(map(int, manual))
        require(len(manual_ids) == 1179, "Manual query ID reference is not the expected 1179 queries")
        log("start", zip=str(args.zip.resolve()), manual_queries=len(manual_ids),
            threshold=THRESHOLD, repetitions=args.repetitions)
        runs, query_ids, run_meta = load_runs(archive, records, cache, args.expected_queries,
                                             args.chunksize, args.refresh_cache)
        labels, score_audits, label_meta = load_labels(archive, records, runs, query_ids, cache,
                                                       args.expected_scores, args.refresh_cache)
    arrays = evaluate(runs, labels, query_ids, manual_ids, results, score_audits)
    scenarios = {"all_queries": np.ones(len(query_ids), dtype=bool),
                 "excluding_manual_queries": ~arrays["manual_overlap"],
                 "manual_overlap_only": arrays["manual_overlap"]}
    overlap_ids = query_ids[arrays["manual_overlap"]].tolist()
    provenance = {"zip_path": args.zip.name, "zip_size": args.zip.stat().st_size,
                  "entries": records, "script_sha256": sha256_file(Path(__file__)),
                  "python": sys.version, "executable": Path(sys.executable).name,
                  "platform": platform.platform(),
                  "dependencies": {"numpy": np.__version__, "pandas": pd.__version__,
                                   "ijson": ijson.__version__},
                  "command": ["python", Path(__file__).name, "--zip", args.zip.name, "--repetitions", str(args.repetitions), "--seed", str(args.seed)],
                  "blas_thread_environment": {key: os.environ.get(key) for key in
                                              ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
                                               "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")}}
    summary = {
        "schema_version": EVAL_SCHEMA, "status": "metrics_complete_inference_pending",
        "protocol": {
            "metric": "binary pooled-pseudoqrel NDCG@10", "depths": KS.tolist(),
            "label": f"raw_score >= {THRESHOLD!r}",
            "pool": "union of bm25, e5, bge rank-1-through-K document IDs per query",
            "query_universe": "union of all run query IDs; require all score query IDs in this universe",
            "idcg": "shared across every system for a query and K: sum of first min(pool positives,10) log2 discounts",
            "zero_idcg": "retain query; every system receives exactly zero",
            "run_order": "explicit 1-based rank column is authoritative; do not reorder rounded retrieval scores",
            "rrf": "sum 1/(60+rank) over present ranks <=K; absent ranks contribute zero; top10",
            "rrf_ties": "float64 contributions sorted ascending before summing; equal scores use ascending numeric docid",
            "fixed200": "one RRF top10 from all three top200 lists, evaluated against each variable-K label pool",
            "unjudged": "outside-pool or missing-raw-score documents get zero gain; both counts reported separately",
            "primary_average": "all queries, including zero-IDCG queries",
            "conditional_average": "diagnostic only, restrict to queries with at least one positive pooled label at each K",
            "bootstrap": "ordinary nonparametric paired query bootstrap with replacement; percentile 95% CI; shared resamples across contrasts",
            "signflip": "two-sided paired query sign-flip Monte Carlo; shared signs across contrasts; (extreme+1)/(B+1), no multiplicity correction",
            "repetitions": args.repetitions, "seed": args.seed,
            "bootstrap_batch_size": 8,
            "seed_per_population": {name: args.seed + i for i, name in enumerate(scenarios)},
            "model_ids": {"e5": "intfloat/e5-small-v2", "bge": "BAAI/bge-small-en-v1.5"}},
        "manual_overlap": {"manual_queries": len(manual_ids), "fullset_overlap_queries": len(overlap_ids),
                           "fullset_excluding_manual_queries": int((~arrays["manual_overlap"]).sum()),
                           "overlap_query_ids": overlap_ids,
                           "manual_ids_absent_from_fullset": sorted(manual_ids - set(query_ids.tolist())),
                           "interpretation": "Exclude all 1179 manual IDs as sensitivity to possible judge training/validation/test query reuse. The specific 825 training IDs are not established by this pipeline; exclusion is not proof of independent labels."},
        "run_audit": run_meta["audit"], "score_audit": label_meta,
        "populations": {name: summarize(arrays, mask) for name, mask in scenarios.items()},
        "validity_notes": [
            "These are consistency metrics against one learned judge's binary pseudoqrels, not independent human relevance or generalization estimates.",
            "The judge checkpoint is not recovered or validated here; saved raw scores and configured threshold are the evaluated artifacts.",
            "Changing K changes both pooled labels and variable RRF inputs; the fixed200 comparator isolates label-pool changes for one ranking.",
            "Base-retriever top10 and their DCG stay fixed; their NDCG can fall when deeper pools increase the common IDCG.",
            "Fixed200 RRF may return documents outside a shallow label pool; zero-gain treatment is conventional unjudged handling, not a claim that those documents are irrelevant.",
            "Uncertainty intervals condition on the recorded runs, scores, threshold, and protocol; they do not include judge-training or labeling uncertainty.",
            "K comparisons are paired but use different qrels. Conditional positive-query averages have K-dependent populations and are diagnostic only."],
        "provenance": provenance}
    atomic_json(results / "fullset_summary.json", summary)
    atomic_json(results / "fullset_provenance.json", provenance)
    for row in summary["populations"]["all_queries"]["depths"]:
        log("actual_metrics", k=row["k"], queries=row["queries"], positive_queries=row["positive_queries"],
            candidates_mean=row["candidates_mean_all_queries"], positives_mean=row["positives_mean_all_queries"],
            ndcg={model: value["ndcg10_mean_all_queries"] for model, value in row["models"].items()})
    log("metrics_saved", path=str(results / "fullset_summary.json"), manual_overlap=len(overlap_ids))
    summary["paired_inference"] = inference_all(arrays, scenarios, args.repetitions, args.seed, results)
    summary["status"] = "complete"
    summary["elapsed_seconds"] = time.monotonic() - START
    summary["peak_rss_gib"] = rss_gib()
    summary["artifacts"] = {}
    for name in ("fullset_perquery.npz", "fullset_inference_replicates.npz", "fullset_provenance.json"):
        path = results / name
        summary["artifacts"][name] = {"path": path.name, "bytes": path.stat().st_size,
                                     "sha256": sha256_file(path)}
    atomic_json(results / "fullset_summary.json", summary)
    log("complete", summary=str(results / "fullset_summary.json"),
        elapsed_seconds=round(summary["elapsed_seconds"], 2), peak_rss_gib=round(rss_gib(), 3))


if __name__ == "__main__":
    main()
