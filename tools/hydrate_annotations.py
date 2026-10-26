#!/usr/bin/env python3
"""Reattach official query/passage text locally, verifying historical text hashes.

Accepts MS MARCO two-column TSV or BEIR-style JSONL. Reads the corpus as a stream;
only texts needed by the annotation batches are held in memory. No downloads.
"""
import argparse
import hashlib
import json
from pathlib import Path


def pairs(path):
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if line.lstrip().startswith("{"):
                record = json.loads(line)
                identifier = str(record.get("_id", record.get("doc_id", record.get("query_id", ""))))
                text = record.get("text")
            else:
                identifier, text = line.split("\t", 1)
            if not identifier.isdecimal() or not isinstance(text, str):
                raise ValueError("expected numeric ID plus text in source")
            yield identifier, text


def hydrate(annotation_dir, receipt_dir, corpus, queries, output_dir):
    annotation_dir, receipt_dir, output_dir = map(Path, (annotation_dir, receipt_dir, output_dir))
    if output_dir.exists():
        raise FileExistsError("use a new output directory")
    batches = {}
    required_queries, required_documents = set(), set()
    for path in sorted(annotation_dir.glob("batch_*.json")):
        annotations = json.loads(path.read_text())
        receipts = json.loads((receipt_dir / path.name).read_text())
        if set(annotations) != set(receipts):
            raise ValueError("query receipt mismatch")
        batches[path.name] = (annotations, receipts)
        for qid, query in annotations.items():
            required_queries.add(qid)
            required_documents.update(query["documents"])
            if set(query["documents"]) != set(receipts[qid]["documents"]):
                raise ValueError("document receipt mismatch")
    if not batches:
        raise ValueError("no neutral batch files")
    qtexts = {qid: text for qid, text in pairs(queries) if qid in required_queries}
    dtexts = {did: text for did, text in pairs(corpus) if did in required_documents}
    if set(qtexts) != required_queries or set(dtexts) != required_documents:
        raise ValueError("official source is missing required query/passage IDs")
    mismatch_count = 0
    for annotations, receipts in batches.values():
        for qid, query in annotations.items():
            text = qtexts[qid]
            if (hashlib.sha256(text.encode()).hexdigest() != receipts[qid]["query_text_sha256"]
                    or len(text) != receipts[qid]["query_text_length"]):
                mismatch_count += 1
            query["query_text"] = text
            for did, document in query["documents"].items():
                text = dtexts[did]
                receipt = receipts[qid]["documents"][did]
                if hashlib.sha256(text.encode()).hexdigest() != receipt["sha256"] or len(text) != receipt["length"]:
                    mismatch_count += 1
                document["text"] = text
                document.pop("text_length", None)
                document.pop("text_present", None)
    if mismatch_count:
        raise ValueError("historical text hash mismatch count=%d; no output written. Reconcile source version/encoding explicitly." % mismatch_count)
    output_dir.mkdir(parents=True)
    for name, (annotations, _receipts) in batches.items():
        with (output_dir / name).open("w", encoding="utf-8") as handle:
            json.dump(annotations, handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
            handle.write("\n")
    return {"batches": len(batches), "queries": len(required_queries),
            "documents": len(required_documents), "text_hashes_verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotation-dir", required=True, type=Path)
    parser.add_argument("--receipt-dir", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(hydrate(args.annotation_dir, args.receipt_dir, args.corpus, args.queries, args.output_dir)))


if __name__ == "__main__":
    main()
