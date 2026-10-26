# Full development snapshot

The current `main` branch contains the canonical evaluation code, saved results,
two distinct manuscript versions and one final presentation/speech set.

The earlier complete development snapshot is preserved at
[archive-2026-10-26](https://github.com/Babaykka/hybrid-retrieval-evaluation/tree/archive-2026-10-26),
commit `c5d6a263f60656ffbc9ce1f2f96f4b3f098f56dd`.
It contains 2,266 files, including historical deliveries and intermediate builds.
Its dated [release](https://github.com/Babaykka/hybrid-retrieval-evaluation/releases/tag/archive-2026-10-26)
has the matching `core-files.sha256.json`; that manifest describes the archived
snapshot, rather than the cleaned current branch.

The [Telegram index](https://t.me/zzakazzy/37) links the full development tarball,
all 25 research-data parts, additional arrays and restoration files.
The original [full-snapshot restoration guide](https://t.me/zzakazzy/34) assumes
the archived 2,266-file checkout. For that workflow, start from the archive tag:

```sh
git clone --branch archive-2026-10-26 --single-branch \
  https://github.com/Babaykka/hybrid-retrieval-evaluation.git full-snapshot
```

Use the root [RESTORE.md](RESTORE.md) for data used by the current evaluation.
Prepared-file hashes and published message links are available; downloading the
entire Telegram archive and restoring the full project have not been verified.
