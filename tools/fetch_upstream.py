#!/usr/bin/env python3
"""Download excluded source data directly from official MS MARCO endpoints.

Corpus/query archives are streamed through tar/gzip, without a second local copy.
Use storage with enough free space for the uncompressed JSONL output. Dataset
terms remain at https://microsoft.github.io/msmarco/Notice.html.
"""
import argparse
import hashlib
import io
import json
import os
import tarfile
import urllib.request
from pathlib import Path

BASE_URL = "https://msmarco.z22.web.core.windows.net/msmarcoranking/"
DEV_SMALL_SHA256 = "ddc607dbe7b748d7168e8675a242f0811d47febaa2e69d3af09d7ab249c68d7e"
DEV_SMALL_PAIR_SHA256 = "59c979e9e648a775f15559113907a416884bff67863a22e8b1a4c109a21b07aa"


class NonSeekingReader(io.RawIOBase):
    def __init__(self, source):
        self.source = source

    def readable(self):
        return True

    def seekable(self):
        return False

    def readinto(self, buffer):
        raw = self.source.read(len(buffer))
        buffer[:len(raw)] = raw
        return len(raw)


def qrel_pairs(content):
    result = set()
    for line in content.decode("ascii").splitlines():
        fields = line.split()
        if len(fields) != 4 or fields[1] != "0" or not fields[0].isdecimal() or not fields[2].isdecimal():
            raise ValueError("unexpected official qrels format")
        if float(fields[3]) > 0:
            result.add((fields[0], fields[2]))
    return result


def convert_tar_tsv(response, member_basename, output, corpus=False):
    """TSV -> JSONL, safe member selection, bounded memory and no extraction."""
    rows, digest, found = 0, hashlib.sha256(), False
    with tarfile.open(fileobj=response, mode="r|gz") as archive:
        for member in archive:
            if Path(member.name).name != member_basename:
                continue
            if found or not member.isfile():
                raise ValueError("unexpected source member type/duplicate")
            found = True
            source = archive.extractfile(member)
            for line in io.TextIOWrapper(io.BufferedReader(NonSeekingReader(source)), encoding="utf-8", newline=""):
                line = line.rstrip("\r\n")
                identifier, text = line.split("\t", 1)
                if not identifier.isdecimal():
                    raise ValueError("non-numeric official ID")
                record = {"_id": identifier, "text": text}
                if corpus:
                    record["title"] = ""
                raw = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
                output.write(raw)
                digest.update(raw)
                rows += 1
            # The requested member was completely consumed. No other dataset is
            # needed, and the streaming response closes in the caller.
            break
    if not found:
        raise ValueError("official archive does not contain requested member")
    return {"rows": rows, "sha256": digest.hexdigest(), "format": "BEIR-style JSONL"}


def fetch(kind, destination, split="dev"):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("refusing to overwrite existing source file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    if temporary.exists():
        raise FileExistsError("remove or move the explicitly identified previous partial download first")
    if kind == "qrels":
        url = BASE_URL + "qrels.dev.small.tsv"
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read(2 * 1024 * 1024)
            if response.read(1):
                raise ValueError("unexpected oversized small-dev qrels")
        if hashlib.sha256(raw).hexdigest() != DEV_SMALL_SHA256:
            raise ValueError("official qrels bytes changed; explicit source-version review required")
        pairs = qrel_pairs(raw)
        pairhash = hashlib.sha256(json.dumps(sorted(pairs), separators=(",", ":")).encode()).hexdigest()
        if pairhash != DEV_SMALL_PAIR_SHA256:
            raise ValueError("qrels differs from historical 7,437-pair reference")
        with temporary.open("xb") as output:
            output.write(raw)
        result = {"rows": len(pairs), "sha256": DEV_SMALL_SHA256, "canonical_pair_sha256": pairhash,
                  "format": "official four-column TREC qrels"}
    else:
        url = BASE_URL + ("collection.tar.gz" if kind == "corpus" else "queries.tar.gz")
        member = "collection.tsv" if kind == "corpus" else "queries.%s.tsv" % split
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open("xb") as output:
            result = convert_tar_tsv(response, member, output, corpus=(kind == "corpus"))
    os.replace(temporary, destination)
    receipt = {"source": url, "member": member if kind != "qrels" else None, **result,
               "dataset_terms": "https://microsoft.github.io/msmarco/Notice.html"}
    destination.with_name(destination.name + ".source.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["qrels", "queries", "corpus"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--split", choices=["train", "dev", "eval"], default="dev")
    args = parser.parse_args()
    print(json.dumps(fetch(args.kind, args.output, args.split)))


if __name__ == "__main__":
    main()
