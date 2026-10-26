"""Re-evaluate the saved manual pool without running a neural model."""

import argparse
import csv
import io
import hashlib
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.stats import rankdata


MODELS = ["bm25", "e5", "bge", "rrf3", "e5-rerank", "judge-rerank"]
WEIGHTS = 1 / np.log2(np.arange(10) + 2)


def paired_stats(values, rng, n_bootstrap=5000, n_permutations=10000):
    values = np.asarray(values, dtype=float)
    means = np.empty(n_bootstrap)
    for start in range(0, n_bootstrap, 100):
        stop = min(start + 100, n_bootstrap)
        means[start:stop] = values[rng.integers(len(values), size=(stop-start, len(values)))].mean(1)
    observed = abs(values.mean())
    extreme = 0
    for start in range(0, n_permutations, 100):
        size = min(100, n_permutations-start)
        signs = rng.integers(0, 2, size=(size, len(values)), dtype=np.int8)*2-1
        extreme += np.count_nonzero(np.abs((signs*values).mean(1)) >= observed-1e-15)
    return {"mean": float(values.mean()), "ci95": np.quantile(means, [.025, .975]).tolist(),
            "p_two_sided": (int(extreme)+1)/(n_permutations+1), "queries": len(values)}


def classifier_stats(truth, scores, threshold):
    truth = np.asarray(truth, dtype=int)
    scores = np.asarray(scores, dtype=float)
    pred = scores >= threshold
    tp = int(np.sum(pred & (truth == 1)))
    fp = int(np.sum(pred & (truth == 0)))
    fn = int(np.sum(~pred & (truth == 1)))
    tn = int(np.sum(~pred & (truth == 0)))
    precision = tp / (tp+fp) if tp+fp else 0
    recall = tp / (tp+fn) if tp+fn else 0
    pos, neg = int(truth.sum()), int(len(truth)-truth.sum())
    auc = (rankdata(scores)[truth == 1].sum()-pos*(pos+1)/2)/(pos*neg)
    expected = ((tp+fp)*(tp+fn)+(tn+fn)*(tn+fp))/len(truth)**2
    accuracy = (tp+tn)/len(truth)
    return {"n": len(truth), "precision": precision, "recall": recall,
            "f1": 2*precision*recall/(precision+recall), "accuracy": accuracy,
            "auc": float(auc), "kappa": (accuracy-expected)/(1-expected),
            "confusion_matrix": [[tn, fp], [fn, tp]]}


def split_queries(qids):
    # Reproduce GroupShuffleSplit using its sorted unique groups and RandomState.
    groups = np.array(sorted(qids))
    permutation = np.random.RandomState(42).permutation(len(groups))
    n_temp = int(np.ceil(.3*len(groups)))
    train = set(groups[permutation[n_temp:]])
    temp = np.array(sorted(groups[permutation[:n_temp]]))
    second = np.random.RandomState(42).permutation(len(temp))
    n_test = int(np.ceil(.5*len(temp)))
    return {"train": train, "validation": set(temp[second[n_test:]]), "test": set(temp[second[:n_test]])}



OFFICIAL_PAIR_SHA256 = "59c979e9e648a775f15559113907a416884bff67863a22e8b1a4c109a21b07aa"


def text_is_nonempty(item):
    if "text" in item:
        return bool(item["text"].strip())
    if isinstance(item.get("text_present"), bool):
        return item["text_present"]
    raise ValueError("Missing original text or exact preserved text_present; hydrate annotations before evaluation")


def official_positive_pairs(content):
    pairs = set()
    for line in content.decode("utf-8").splitlines():
        fields = line.split()
        if not fields or fields == ["query-id", "corpus-id", "score"]:
            continue
        if len(fields) == 4 and fields[1] in {"0", "Q0"}:
            qid, did, score = fields[0], fields[2], fields[3]
        elif len(fields) == 3:
            qid, did, score = fields
        else:
            raise ValueError("Official qrels must be three-column TSV or four-column TREC")
        if not qid.isdecimal() or not did.isdecimal() or not np.isfinite(float(score)):
            raise ValueError("Invalid official qrel")
        if float(score) > 0:
            pairs.add((qid, did))
    digest = hashlib.sha256(json.dumps(sorted(pairs), separators=(",", ":")).encode()).hexdigest()
    if digest != OFFICIAL_PAIR_SHA256:
        raise ValueError("Official qrels differ from the exact 7,437-pair historical dev/small reference; use qrels.dev.small.tsv")
    return pairs, digest


def archive_prefix(archive):
    suffix = "output_fixed/judge_config.json"
    matches = [p for p in archive.namelist() if p.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError("Expected one project archive root")
    return matches[0][:-len(suffix)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=Path("retrieval-data.zip"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--official-qrels", type=Path, help="Downloaded qrels.dev.small.tsv; exact historical pair hash is checked")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.archive) as archive:
        root = archive_prefix(archive)
        data = {}
        used = sorted(p for p in archive.namelist() if p.startswith(root+"new_data/") and p.endswith(".json") and "/text-hashes/" not in p)
        for path in used:
            data.update(json.loads(archive.read(path)))
        prefix = root+"output_fixed/"
        raw = json.loads(archive.read(prefix+"judge_scores_raw.json"))
        config = json.loads(archive.read(prefix+"judge_config.json"))
        previous = json.loads(archive.read(prefix+"all_results.json"))
        stored = json.loads(archive.read(prefix+"pseudo_qrels_judge.json"))
        dev_path = root+"msmarco/qrels/dev.tsv"
        if dev_path in archive.namelist():
            qrel_content = archive.read(dev_path)
            used.append(dev_path)
        elif args.official_qrels:
            qrel_content = args.official_qrels.read_bytes()
        else:
            parser.error("This anonymized archive omits official source qrels. Download qrels.dev.small.tsv with fetch_upstream.py qrels, then pass --official-qrels FILE")
        dev, official_hash = official_positive_pairs(qrel_content)
        used += [prefix+"judge_scores_raw.json", prefix+"judge_config.json"]
        provenance = {p: {"size": archive.getinfo(p).file_size, "crc32": f"{archive.getinfo(p).CRC:08x}"} for p in used}
        provenance["official_dev_small_reference"] = {"positive_pairs": len(dev), "canonical_pair_sha256": official_hash,
            "source": "https://msmarco.z22.web.core.windows.net/msmarcoranking/qrels.dev.small.tsv"}

    qids = sorted(data)
    splits = split_queries(qids)
    tau = config["threshold"]
    arrays = {name: np.zeros((len(qids), len(MODELS))) for name in ["official", "human", "judge"]}
    labels = Counter()
    channel_counts = Counter()
    clean_query_mask = []
    density = {name: [] for name in arrays}
    valid_truth, valid_scores = [], []
    all_truth, all_scores, all_qids = [], [], []
    extra_sources = 0
    invalid_pairs, empty_pairs = [], []
    for qi, qid in enumerate(qids):
        docs = data[qid]["documents"]
        rels = {
            "official": {d for d in docs if (qid, d) in dev},
            "human": {d for d, item in docs.items() if item.get("true relevant", 0) in [1, 2]},
            "judge": {d for d in docs if raw[qid][d] >= tau},
        }
        ranks = {}
        for model in ["bm25", "e5", "bge", "e5-rerank"]:
            ranks[model] = sorted((d for d, item in docs.items() if model in item.get("systems", {})),
                                  key=lambda d: (-docs[d]["systems"][model], int(d)))
        fusion = {}
        for model in ["bm25", "e5", "bge"]:
            for rank, docid in enumerate(ranks[model][:10], 1):
                fusion.setdefault(docid, []).append(1/(60+rank))
        ranks["rrf3"] = sorted(fusion, key=lambda d: (-sum(sorted(fusion[d])), int(d)))
        ranks["judge-rerank"] = sorted(docs, key=lambda d: (-raw[qid][d], int(d)))
        for label_set, relevant in rels.items():
            ideal = WEIGHTS[:min(10, len(relevant))].sum()
            density[label_set].append(len(relevant))
            for mi, model in enumerate(MODELS):
                gain = np.array([d in relevant for d in ranks[model][:10]], dtype=float)
                arrays[label_set][qi, mi] = float((gain*WEIGHTS[:len(gain)]).sum()/ideal) if ideal else 0
        clean = True
        for docid, item in docs.items():
            label = item.get("true relevant", 0)
            labels[label] += 1
            channel_counts.update(item.get("systems", {}).keys())
            extra_sources += not (set(item.get("systems", {})) & {"bm25", "e5", "bge", "e5-rerank"})
            if label not in [0, 1, 2]:
                invalid_pairs.append([qid, docid, label])
                clean = False
            if not text_is_nonempty(item):
                empty_pairs.append([qid, docid, label])
                clean = False
            truth = int(label in [1, 2])
            all_truth.append(truth)
            all_scores.append(raw[qid][docid])
            all_qids.append(qid)
            if label in [0, 1, 2] and text_is_nonempty(item):
                valid_truth.append(truth)
                valid_scores.append(raw[qid][docid])
        clean_query_mask.append(clean)
    clean_query_mask = np.array(clean_query_mask)
    rng = np.random.default_rng(20260914)
    metrics = {}
    for mi, model in enumerate(MODELS):
        metrics[model] = {
            **{k: float(v[:, mi].mean()) for k, v in arrays.items()},
            "human_minus_official": paired_stats(arrays["human"][:, mi]-arrays["official"][:, mi], rng),
            "clean_queries_human": float(arrays["human"][clean_query_mask, mi].mean()),
            "clean_queries_official": float(arrays["official"][clean_query_mask, mi].mean()),
        }
    comparisons = {}
    for model in ["bm25", "bge", "rrf3", "e5-rerank"]:
        mi = MODELS.index(model)
        comparisons[model+"_minus_e5"] = paired_stats(arrays["human"][:, mi]-arrays["human"][:, 1], rng)
    qarray = np.array(all_qids)
    tarray, sarray = np.array(all_truth), np.array(all_scores)
    split_results = {}
    for name, group in splits.items():
        mask = np.isin(qarray, list(group))
        split_results[name] = {"queries": len(group), **classifier_stats(tarray[mask], sarray[mask], tau)}
    derived = {(q, d) for q, ds in raw.items() for d, score in ds.items() if score >= tau}
    stored_set = {(q, d) for q, ds in stored.items() for d in ds}
    pool_sizes = [len(data[q]["documents"]) for q in qids]
    result = {
        "protocol": {"idcg": "common annotated-pool IDCG per query and label set", "zero_queries": "retained with NDCG=0",
                     "ranking_ties": "descending score then ascending numeric document ID", "rrf": "BM25+E5+BGE top10; c=60",
                     "unknown_manual_labels": "unjudged, zero gain at retained ranks", "seed": 20260914,
                     "bootstrap_resamples": 5000, "paired_sign_flips": 10000},
        "queries": len(qids), "pairs": sum(pool_sizes), "pool_mean": float(np.mean(pool_sizes)),
        "pool_max": max(pool_sizes), "pools_over_40": sum(n > 40 for n in pool_sizes),
        "label_counts": dict(labels), "channel_counts": dict(channel_counts), "extra_channel_only_pairs": extra_sources,
        "invalid_labels": invalid_pairs, "empty_texts": empty_pairs, "clean_queries": int(clean_query_mask.sum()),
        "density": {k: {"pairs": sum(v), "mean": float(np.mean(v)), "median": float(np.median(v)),
                          "queries_with_positive": sum(x > 0 for x in v)} for k, v in density.items()},
        "metrics": metrics, "paired_human_comparisons": comparisons,
        "judge_threshold": tau, "judge_recorded_training_results": config,
        "judge_rescored_split_metrics": split_results,
        "judge_rerank_heldout": {
            "queries": len(splits["test"]),
            **{name: float(values[np.isin(qids, list(splits["test"])), MODELS.index("judge-rerank")].mean())
               for name, values in arrays.items()},
            "setting": "Re-ranking all candidates in the answer-assisted manual pool on held-out queries; not first-stage retrieval",
        },
        "judge_valid_text_and_labels": classifier_stats(valid_truth, valid_scores, tau),
        "judge_artifact_reconciliation": {"old_summary_positive": previous["qrels_stats"]["judge"]["relevant_pairs"],
            "stored_positive": len(stored_set), "regenerated_positive": len(derived),
            "stored_only_pairs": len(stored_set-derived), "derived_only_pairs": len(derived-stored_set)},
        "provenance": provenance,
    }
    (args.output/"manual_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    (args.output/"manual_splits.json").write_text(json.dumps({k: sorted(v) for k, v in splits.items()}, indent=2)+"\n")
    (args.output/"manual_judge_qrels.json").write_text(json.dumps({q: {d: 1 for d, s in raw[q].items() if s >= tau} for q in qids})+"\n")
    np.savez_compressed(args.output/"manual_per_query.npz", qids=np.array(qids), models=np.array(MODELS),
                        clean=clean_query_mask, **arrays)
    np.savez_compressed(args.output/"manual_judge_diagnostics.npz", truth=np.array(valid_truth), scores=np.array(valid_scores))
    print(json.dumps({k: result[k] for k in ["queries", "pairs", "clean_queries", "density", "metrics", "judge_rescored_split_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
