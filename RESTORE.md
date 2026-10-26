# Restore and verify the project

Use this repository for development sources, documents and the retained result
files. The full research-data archive and additional large arrays are distributed
through [the project Telegram channel](https://t.me/zzakazzy). The research-data
archive is not a GitHub download.

Allow at least 100 GB of free space on a separate disk for the downloaded parts,
joined ZIP64 archive, extracted data and upstream reconstruction. Optional model
downloads and historical runtime environments require additional space.

## Download the matching files

Clone this repository into a new directory and enter it. Obtain the matching
`core-files.sha256.json` from the code release when available:

```sh
mkdir release-downloads
gh release download archive-2026-10-26 --dir release-downloads \
  --pattern 'core-files.sha256.json'
```

From the matching archive entry in the Telegram channel, save
`retrieval-data.parts.json`, every part it lists, `fullset_runs.npy` and
`fullset_labels.npy` into `release-downloads/`. Preserve the attachment filenames.
The part count, ordering, sizes, SHA-256 values and message links come from that
manifest; do not combine parts from different versions. A complete archive is
available only once all listed attachments and the manifest have been posted.

The joined archive is
26,770,669,571 bytes, with SHA-256
`b63423b94b75126a1ccccac898dacd48244e140791c7507ea900a8c4f0699141`.
Use the per-part sizes and SHA-256 values in `retrieval-data.parts.json`.

## Check the checkout, join the parts and extract safely

Run the following Python 3 command from the repository root. It uses bounded
reads, verifies the core files and additional arrays, and writes the joined ZIP
and extracted data only to new paths. Archive paths, duplicate files, file/parent
conflicts and links are checked before extraction. Each extracted member is read
to its end, which also verifies its ZIP CRC; the content manifest then verifies
the recorded member sizes and SHA-256 values.

```sh
python3 - <<'PY'
import hashlib, json, re, shutil, stat, zipfile
from pathlib import Path, PurePosixPath

downloads = Path('release-downloads')
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def relative(value):
    q = PurePosixPath(value)
    if (not value or '\\' in value or '\0' in value or q.is_absolute()
            or value != q.as_posix() or ':' in q.parts[0]
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('unsafe relative path')
    return Path(*q.parts)
def check(path, size, sha):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != size or digest(path) != sha:
        raise ValueError('size/SHA-256 mismatch: ' + str(path))

core = json.loads((downloads / 'core-files.sha256.json').read_text())
for row in core['files']:
    check(relative(row['path']), row['size'], row['sha256'])
parts = json.loads((downloads / 'retrieval-data.parts.json').read_text())
if parts['archive_size'] != 26770669571 or parts['archive_sha256'] != 'b63423b94b75126a1ccccac898dacd48244e140791c7507ea900a8c4f0699141':
    raise ValueError('wrong research-data release')
part_bytes = parts.get('part_bytes', parts.get('part_size'))
if (type(part_bytes) is not int or part_bytes < 1
        or len(parts['parts']) != (parts['archive_size'] + part_bytes - 1) // part_bytes):
    raise ValueError('incomplete part list')
archive = downloads / 'retrieval-data.zip'
partial = downloads / 'retrieval-data.zip.partial'
if archive.exists() or partial.exists():
    raise FileExistsError('use new paths; do not overwrite an existing archive')
whole, offset = hashlib.sha256(), 0
with partial.open('xb') as output:
    for number, row in enumerate(parts['parts'], 1):
        expected_size = min(part_bytes, parts['archive_size'] - offset)
        if (row['number'] != number or row['offset'] != offset
                or row['filename'] != 'retrieval-data.zip.part%03d' % number
                or row['size'] != expected_size):
            raise ValueError('wrong part order or geometry')
        source = downloads / row['filename']
        check(source, row['size'], row['sha256'])
        with source.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                output.write(block); whole.update(block); offset += len(block)
if offset != parts['archive_size'] or whole.hexdigest() != parts['archive_sha256']:
    raise ValueError('joined archive mismatch; the partial file is not verified')
partial.rename(archive)

out = Path('restored-data')
if out.exists():
    raise FileExistsError('extract into a new directory')
written = {}
with zipfile.ZipFile(archive) as source:
    members, names, files = [], set(), set()
    for info in source.infolist():
        name = info.filename[:-1] if info.is_dir() else info.filename
        path = relative(name)
        mode = info.external_attr >> 16
        if (name in names or info.flag_bits & 1
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                or path.parts[0] != 'retrieval-data'):
            raise ValueError('duplicate, encrypted or unsupported ZIP member')
        names.add(name)
        if not info.is_dir():
            files.add(name)
        members.append((info, path))
    for name in names:
        pieces = name.split('/')
        if any('/'.join(pieces[:i]) in files for i in range(1, len(pieces))):
            raise ValueError('ZIP file conflicts with parent directory')
    out.mkdir()
    for info, path in members:
        target = out / path
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True); continue
        target.parent.mkdir(parents=True, exist_ok=True)
        h, size = hashlib.sha256(), 0
        with source.open(info) as handle, target.open('xb') as output:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                output.write(block); h.update(block); size += len(block)
        written[info.filename] = (size, h.hexdigest())
content = json.loads((out / 'retrieval-data/CONTENT_MANIFEST.json').read_text())
expected = {row['path'] for row in content['files']}
if set(written) != expected | {'retrieval-data/CONTENT_MANIFEST.json'}:
    raise ValueError('content manifest does not cover extracted files')
for row in content['files']:
    if written[row['path']] != (row['size'], row['sha256_uncompressed']):
        raise ValueError('extracted member differs: ' + row['path'])

arrays = json.loads(Path('RELEASE_ARTIFACTS.json').read_text())
for row in arrays['files']:
    source = downloads / relative(row['asset_name'])
    check(source, row['bytes'], row['sha256'])
    target = relative(row['path']); target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with source.open('rb') as handle, target.open('xb') as output:
            shutil.copyfileobj(handle, output, 1024 * 1024)
    check(target, row['bytes'], row['sha256'])
print('Core files, all parts, joined ZIP, extracted members and additional arrays verified.')
PY
```

The two additional arrays restore to `revision_2026/cache/fullset_runs.npy`
(242,623,328 bytes) and `revision_2026/cache/fullset_labels.npy` (60,655,928 bytes).
Their SHA-256 values and destination paths are in `RELEASE_ARTIFACTS.json`.

## Reconstruct excluded upstream text when needed

The five original corpus/query/qrel files come from the matching BEIR MSMARCO
package. The downloader verifies its pinned size and publisher MD5; extraction
checks the five expected members, their CRCs, sizes and historical SHA-256 values.
The hydration helper applies the recorded historical reconstruction recipes and
checks every restored query/passage text against its stored SHA-256 and length.
Run these commands from the repository root:

```sh
python3 tools/fetch_upstream.py beir --output release-downloads/upstream/msmarco.zip
python3 tools/fetch_upstream.py extract-beir \
  --archive release-downloads/upstream/msmarco.zip \
  --output-dir release-downloads/upstream/beir \
  --expected-manifest restored-data/retrieval-data/UPSTREAM_SOURCES.json
python3 tools/hydrate_annotations.py \
  --annotation-dir restored-data/retrieval-data/new_data \
  --receipt-dir restored-data/retrieval-data/provenance/annotation-text-hashes \
  --corpus release-downloads/upstream/beir/corpus.jsonl \
  --queries release-downloads/upstream/beir/queries.jsonl \
  --output-dir restored-data/new_data_hydrated
```

Point historical notebook inputs at the reconstructed files. A text hash mismatch
requires a source-version/encoding investigation; do not silently normalize it.
The [MS MARCO source terms](https://microsoft.github.io/msmarco/Notice.html) apply.

## Recompute the maintained evaluations

Install the dependencies in `ENVIRONMENT.md`. For the manual evaluator, download
the exact small-dev official qrels; the helper verifies the historical 7,437
positive pairs. Keep them separate from project-expanded judgments.

```sh
python3 tools/fetch_upstream.py qrels --output release-downloads/upstream/qrels.dev.small.tsv
python3 revision_2026/manual_eval.py --archive release-downloads/retrieval-data.zip \
  --official-qrels release-downloads/upstream/qrels.dev.small.tsv \
  --output recalculated/manual
mkdir -p recalculated/fullset
cp revision_2026/fullset_eval.py recalculated/fullset/fullset_eval.py
python3 recalculated/fullset/fullset_eval.py --zip release-downloads/retrieval-data.zip
```

The full-set evaluator writes new caches and results beside its copied script.
It reuses saved retrieval runs and judge scores; it does not rerun model training
or inference. Historical manuscript/presentation builds may need the optional
toolchains in `ENVIRONMENT.md`.

## Historical packaging checksums

`SHA256SUMS.json` inside historical delivery packages records an earlier packaging
stage. Personal metadata removal and portability changes altered some file bytes,
so those historical checksums are retained as provenance and cannot validate the
current public files. For this publication, use the matching
`core-files.sha256.json`, the Telegram `retrieval-data.parts.json`, the extracted
`CONTENT_MANIFEST.json` and `RELEASE_ARTIFACTS.json`. Keep them with the matching
repository commit and archive version.
