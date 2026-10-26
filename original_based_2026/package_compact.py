"""Repackage the verified editorial edition without changing its contents."""
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
DELIVERY = ROOT.parent / "delivery_editorial"
COMPLETE = ROOT.parent / "editorial_source_revision.zip"
ARCHIVE = ROOT.parent / "delivery_editorial.zip"


def digest(data):
    return hashlib.sha256(data).hexdigest()


verified = json.loads((ROOT / "verification/package_verification.json").read_text())
assert digest(COMPLETE.read_bytes()) == verified["sha256"]
with zipfile.ZipFile(COMPLETE) as original:
    assert original.testzip() is None
    for path in SOURCE.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == original.read(path.relative_to(SOURCE).as_posix())

for lang in ("en", "ru"):
    shutil.copy2(SOURCE / f"manuscript_{lang}.pdf", DELIVERY / f"manuscript_{lang}.pdf")

source_archive = DELIVERY / "LaTeX_sources.zip"
with zipfile.ZipFile(source_archive, "w", compression=zipfile.ZIP_DEFLATED) as packed:
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file() or (path.parent == SOURCE and path.suffix == ".pdf"):
            continue
        packed.write(path, path.relative_to(SOURCE).as_posix())
    packed.write(ROOT / "ПОЯСНЕНИЕ.md", "ПОЯСНЕНИЕ.md")

expected = {"manuscript_en.pdf", "manuscript_ru.pdf", "LaTeX_sources.zip", "Пояснение.txt"}
assert {path.name for path in DELIVERY.iterdir()} == expected
with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as packed:
    for path in sorted(DELIVERY.iterdir()):
        packed.write(path, path.name)

with zipfile.ZipFile(ARCHIVE) as packed, zipfile.ZipFile(COMPLETE) as original:
    assert packed.testzip() is None
    assert set(packed.namelist()) == expected
    for lang in ("en", "ru"):
        name = f"manuscript_{lang}.pdf"
        assert packed.read(name) == original.read(name)
    with zipfile.ZipFile(io.BytesIO(packed.read("LaTeX_sources.zip"))) as sources:
        assert sources.testzip() is None
        names = set(original.namelist()) - {"manuscript_en.pdf", "manuscript_ru.pdf"}
        assert set(sources.namelist()) == names
        for name in sources.namelist():
            assert sources.read(name) == original.read(name)

report = {
    "archive": str(ARCHIVE),
    "top_level_files": sorted(expected),
    "identical_to_compiled_original_based_edition": True,
    "both_zip_integrity_checks": "passed",
    "bytes": ARCHIVE.stat().st_size,
    "sha256": digest(ARCHIVE.read_bytes()),
}
(ROOT / "verification/compact_package_verification.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
