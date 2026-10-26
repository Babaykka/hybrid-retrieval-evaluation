# Data for the current project

The evaluation scripts read the matching research ZIP directly; extracted
embeddings are unnecessary. The [Telegram index](https://t.me/zzakazzy/37) links
all 25 parts. Exact sizes, SHA-256 values and message links are in
[data/retrieval-data.parts.json](data/retrieval-data.parts.json).

The joined ZIP is 26,770,669,571 bytes, with SHA-256
`b63423b94b75126a1ccccac898dacd48244e140791c7507ea900a8c4f0699141`.
Allow space for the downloaded parts and the joined ZIP, or use a separate disk.

## Download and join

Save the 25 named attachments in a new `release-downloads/` directory. Preserve
their filenames. From the repository root, this Python command checks each part
and writes a joined archive only to new paths:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path

manifest = json.loads(Path('data/retrieval-data.parts.json').read_text())
downloads = Path('release-downloads')
archive = Path('retrieval-data.zip')
partial = Path('retrieval-data.zip.partial')
if archive.exists() or partial.exists():
    raise FileExistsError('Use new paths; an archive or partial file already exists')
whole, offset = hashlib.sha256(), 0
with partial.open('xb') as output:
    for number, row in enumerate(manifest['parts'], 1):
        if row['number'] != number or row['offset'] != offset or row['filename'] != 'retrieval-data.zip.part%03d' % number:
            raise ValueError('Unexpected part order or filename')
        source = downloads / row['filename']
        if source.is_symlink() or not source.is_file() or source.stat().st_size != row['size']:
            raise ValueError('Missing part or unexpected file size: ' + row['filename'])
        part = hashlib.sha256()
        with source.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                part.update(block); whole.update(block); output.write(block); offset += len(block)
        if part.hexdigest() != row['sha256']:
            raise ValueError('Part checksum mismatch: ' + row['filename'])
if offset != manifest['archive_size'] or whole.hexdigest() != manifest['archive_sha256']:
    raise ValueError('Joined checksum mismatch; the partial file is not verified')
partial.rename(archive)
print('All parts and joined archive match the prepared-file manifest.')
PY
```

## Evaluate saved runs

Install [requirements.txt](requirements.txt) in a virtual environment. Obtain the
matching official reference qrels, then run the maintained scripts:

```sh
.venv/bin/python tools/fetch_upstream.py qrels --output data/qrels.dev.small.tsv
.venv/bin/python revision_2026/manual_eval.py \
  --archive retrieval-data.zip \
  --official-qrels data/qrels.dev.small.tsv \
  --output revision_2026/results
.venv/bin/python revision_2026/fullset_eval.py --zip retrieval-data.zip
```

These commands replace their corresponding result files and may create a local
cache. See [revision_2026/README.md](revision_2026/README.md) for inputs, outputs
and interpretation limits. The evaluator can regenerate full-set cache arrays
from the ZIP. The additional preserved arrays are
[fullset_labels.npy](https://t.me/zzakazzy/6) and
[fullset_runs.npy](https://t.me/zzakazzy/7); their original paths and hashes are in
[RELEASE_ARTIFACTS.json](RELEASE_ARTIFACTS.json).

## Upstream text and full historical snapshot

The upstream corpus, queries and official qrels are obtained using
`tools/fetch_upstream.py`; its subcommand help describes the pinned sources and
checks. `tools/hydrate_annotations.py` reconstructs annotation text from matching
upstream data and the hash recipes supplied in the archive. Source terms apply.

For historical deliveries and the old full-tree integrity check, use the archive
tag and [ARCHIVE.md](ARCHIVE.md). The old 2,266-file core manifest applies to that
snapshot. Prepared-file hashes are provided, but a complete download and
restoration of the Telegram archive has not been verified.
