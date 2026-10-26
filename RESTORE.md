# Restore the project

1. Clone or download this repository and the matching GitHub Release manifests.
2. Download every research-data part listed by that release. Compare each size
   and SHA-256, join the parts in the documented order, and verify the complete
   archive before extracting it. Reject absolute paths and parent traversal.
3. Restore the additional arrays listed in `RELEASE_ARTIFACTS.json` to their
   recorded relative paths. Compare their SHA-256 values before use.
4. Acquire the upstream MS MARCO sources and use the supplied hydration helper
   when a historical pipeline requires raw query/document text. Hydration must
   match the stored text hashes; do not silently replace official qrels with
   project-expanded judgments.
5. Install the relevant dependencies from `ENVIRONMENT.md`. Run the maintained
   evaluators with their documented archive and official-qrels arguments. Use
   their `--help` output to select the exact input paths for this release.
6. Open representative manuscripts/slides, load the saved numerical results, and
   compare the restored tree with the release manifest. Historical packaging and
   presentation scripts may require the optional toolchain described separately.

Keep the matching release version and manifests together. A missing upstream
download, release part, proprietary tool, or model checkpoint must be reported
explicitly rather than treated as a completed reproduction.
