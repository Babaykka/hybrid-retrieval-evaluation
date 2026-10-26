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
import zipfile
from pathlib import Path

BASE_URL = "https://msmarco.z22.web.core.windows.net/msmarcoranking/"
DEV_SMALL_SHA256 = "ddc607dbe7b748d7168e8675a242f0811d47febaa2e69d3af09d7ab249c68d7e"
DEV_SMALL_PAIR_SHA256 = "59c979e9e648a775f15559113907a416884bff67863a22e8b1a4c109a21b07aa"
BEIR_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/msmarco.zip"
BEIR_MD5 = "444067daf65d982533ea17ebd59501e4"
BEIR_BYTES = 1082258632
BEIR_MEMBERS = {
    "corpus.jsonl": {"size": 3568655380, "crc32": "69c3dbae"},
    "queries.jsonl": {"size": 40420611, "crc32": "fc79aeda"},
    "qrels/dev.tsv": {"size": 135889, "crc32": "fe55a486"},
    "qrels/test.tsv": {"size": 168598, "crc32": "77a34bda"},
    "qrels/train.tsv": {"size": 9523856, "crc32": "01ca36e4"},
}


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
    if kind == "beir":
        url = BEIR_URL
        md5, sha, count = hashlib.md5(), hashlib.sha256(), 0
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open("xb") as output:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                count += len(block)
                if count > BEIR_BYTES:
                    raise ValueError("BEIR archive exceeds pinned version size")
                md5.update(block)
                sha.update(block)
                output.write(block)
        if count != BEIR_BYTES or md5.hexdigest() != BEIR_MD5:
            raise ValueError("BEIR package does not match the publisher's pinned MD5/size; do not extract")
        result = {"size": count, "md5": md5.hexdigest(), "sha256": sha.hexdigest(),
                  "format": "original BEIR MSMARCO combined ZIP",
                  "provider_card": "https://huggingface.co/datasets/BeIR/msmarco/blob/main/README.md"}
    elif kind == "qrels":
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
    receipt = {"source": url, "member": member if kind in {"queries", "corpus"} else None, **result,
               "dataset_terms": "https://microsoft.github.io/msmarco/Notice.html"}
    destination.with_name(destination.name + ".source.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def extract_beir(archive_path, output_dir, expected_manifest=None,
                 expected_md5=BEIR_MD5, expected_members=None):
    """Extract only the five pinned source files, with no path traversal."""
    archive_path, output_dir = Path(archive_path), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError("use a new output directory")
    members = BEIR_MEMBERS if expected_members is None else expected_members
    md5 = hashlib.md5()
    with archive_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(block)
    if md5.hexdigest() != expected_md5:
        raise ValueError("BEIR package MD5 mismatch")
    expected_sha = {}
    if expected_manifest:
        manifest = json.loads(Path(expected_manifest).read_text())
        for row in manifest["excluded"]:
            relative = row["path"].split("/msmarco/", 1)[-1]
            expected_sha[relative] = row.get("sha256_uncompressed")
        if set(expected_sha) != set(members) or not all(expected_sha.values()):
            raise ValueError("expected manifest must contain all five original source SHA256s")
    receipt = {"package_md5": md5.hexdigest(), "files": [], "whole_project_restore_verified": False}
    with zipfile.ZipFile(archive_path) as source:
        selected = {}
        for relative, expected in members.items():
            match = [i for i in source.infolist() if i.filename == "msmarco/" + relative]
            if len(match) != 1:
                raise ValueError("missing/duplicate pinned BEIR source member")
            info = match[0]
            if info.is_dir() or info.flag_bits & 1 or info.file_size != expected["size"] or "%08x" % info.CRC != expected["crc32"]:
                raise ValueError("BEIR member differs from pinned source packaging")
            selected[relative] = info
        output_dir.mkdir(parents=True)
        for relative, info in selected.items():
            # The output path comes exclusively from the fixed member table.
            target = output_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_name(target.name + ".partial")
            sha, total = hashlib.sha256(), 0
            with source.open(info) as reader, partial.open("xb") as output:
                for block in iter(lambda: reader.read(1024 * 1024), b""):
                    sha.update(block)
                    output.write(block)
                    total += len(block)
            if total != info.file_size or expected_sha and sha.hexdigest() != expected_sha[relative]:
                raise ValueError("restored raw source SHA256/size mismatch")
            os.replace(partial, target)
            receipt["files"].append({"path": relative, "size": total, "sha256": sha.hexdigest(),
                                     "crc32": "%08x" % info.CRC,
                                     "historical_source_sha256_verified": bool(expected_sha)})
    (output_dir / "source-restoration.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["beir", "extract-beir", "qrels", "queries", "corpus"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-manifest", type=Path)
    parser.add_argument("--split", choices=["train", "dev", "eval"], default="dev")
    args = parser.parse_args()
    if args.kind == "extract-beir":
        if args.archive is None or args.output_dir is None:
            parser.error("extract-beir requires --archive and --output-dir")
        result = extract_beir(args.archive, args.output_dir, args.expected_manifest)
    else:
        if args.output is None:
            parser.error("download requires --output")
        result = fetch(args.kind, args.output, args.split)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
