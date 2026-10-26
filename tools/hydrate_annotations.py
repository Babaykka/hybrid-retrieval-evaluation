#!/usr/bin/env python3
"""Reattach official query/passage text locally, verifying historical text hashes.

Accepts MS MARCO two-column TSV or BEIR-style JSONL. Reads the corpus as a stream;
only texts needed by the annotation batches are held in memory. No downloads.
"""
import argparse
import hashlib
import html
import json
import unicodedata
from pathlib import Path


def cp1252_controls(text):
    """Map defined C1 bytes to their historical Windows-1252 characters."""
    replacements = {}
    for value in range(128, 160):
        try:
            replacements[value] = bytes([value]).decode("cp1252")
        except UnicodeDecodeError:
            pass
    return text.translate(replacements)


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


def apply_recipe(text, recipe):
    """Reproduce recorded historical encoding/empty-text preprocessing exactly."""
    operations = {
        "empty": lambda x: "",
        "utf8_as_latin1": lambda x: x.encode("utf-8").decode("latin-1"),
        "utf8_as_cp1252": lambda x: x.encode("utf-8").decode("cp1252"),
        "latin1_as_utf8": lambda x: x.encode("latin-1").decode("utf-8"),
        "cp1252_as_utf8": lambda x: x.encode("cp1252").decode("utf-8"),
        "strip": str.strip, "html_unescape": html.unescape,
        "normalize_nfc": lambda x: unicodedata.normalize("NFC", x),
        "normalize_nfkc": lambda x: unicodedata.normalize("NFKC", x),
        "nbsp_as_space": lambda x: x.replace("\xa0", " "),
        "newlines_as_spaces": lambda x: x.replace("\r", " ").replace("\n", " "),
        "cp1252_controls": cp1252_controls,
    }
    if not isinstance(recipe, list) or len(recipe) > 4:
        raise ValueError("unrecognized bounded text reconstruction recipe")
    for step in recipe:
        if isinstance(step, str) and step in operations:
            text = operations[step](text)
        elif isinstance(step, dict) and set(step) == {"delete_whitespace"}:
            indexes = step["delete_whitespace"]
            if (not isinstance(indexes, list) or len(indexes) > len(text)
                    or any(type(index) is not int or index < 0 or index >= len(text)
                           or not text[index].isspace() for index in indexes)
                    or indexes != sorted(set(indexes))):
                raise ValueError("invalid whitespace-only reconstruction positions")
            omitted = set(indexes)
            text = "".join(char for index, char in enumerate(text) if index not in omitted)
        elif isinstance(step, dict) and set(step) == {"cp1252_controls_at"}:
            indexes = step["cp1252_controls_at"]
            if (not isinstance(indexes, list) or indexes != sorted(set(indexes))
                    or any(type(index) is not int or index < 0 or index >= len(text)
                           or not 128 <= ord(text[index]) < 160
                           or cp1252_controls(text[index]) == text[index] for index in indexes)):
                raise ValueError("invalid bounded character reconstruction positions")
            selected = set(indexes)
            text = "".join(cp1252_controls(char) if index in selected else char
                           for index, char in enumerate(text))
        elif isinstance(step, dict) and set(step) == {"select_source_ranges"}:
            ranges = step["select_source_ranges"]
            if (not isinstance(ranges, list) or not 1 <= len(ranges) <= 64
                    or any(not isinstance(span, list) or len(span) != 2
                           or any(type(value) is not int for value in span)
                           or not 0 <= span[0] < span[1] <= len(text) for span in ranges)
                    or sum(end - start for start, end in ranges) > 2 * len(text)):
                raise ValueError("invalid bounded historical source ranges")
            text = "".join(text[start:end] for start, end in ranges)
        else:
            raise ValueError("unrecognized bounded text reconstruction operation")
    return text


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
            text = apply_recipe(qtexts[qid], receipts[qid].get("query_text_recipe", []))
            if (hashlib.sha256(text.encode()).hexdigest() != receipts[qid]["query_text_sha256"]
                    or len(text) != receipts[qid]["query_text_length"]):
                mismatch_count += 1
            query["query_text"] = text
            for did, document in query["documents"].items():
                receipt = receipts[qid]["documents"][did]
                text = apply_recipe(dtexts[did], receipt.get("recipe", []))
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
