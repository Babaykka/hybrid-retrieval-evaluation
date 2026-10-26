"""Package the editorial sources and test compilation after clean extraction."""
import os
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
QA = ROOT / "verification"
ARCHIVE = ROOT.parent / "editorial_source_revision.zip"
HELPER = os.environ.get("LATEX_COMPILE_HELPER", "compile_latex.py")


def page_texts(path):
    with pdfplumber.open(path) as pdf:
        return [page.extract_text() for page in pdf.pages]


with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file():
            assert path.suffix in {".tex", ".pdf", ".cls", ".bst", ".md"}, path
            archive.write(path, path.relative_to(SOURCE))
    archive.write(ROOT / "ПОЯСНЕНИЕ.md", "ПОЯСНЕНИЕ.md")

report = {"archive": ARCHIVE.name, "languages": {}}
with tempfile.TemporaryDirectory(prefix="portable-", dir=QA) as temporary:
    unpacked = Path(temporary)
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None
        report["file_count"] = len(archive.namelist())
        archive.extractall(unpacked)
    for lang, engine in [("en", "pdflatex"), ("ru", "xelatex")]:
        build = unpacked / f"build_{lang}"
        result = subprocess.run(
            [sys.executable, HELPER, str(unpacked / f"manuscript_{lang}.tex"),
             "--compiler", "texlive", "--engine", engine,
             "--output-directory", str(build), "--json"],
            capture_output=True, text=True,
        )
        (QA / f"portable_compile_{lang}.json").write_text(result.stdout)
        assert result.returncode == 0, f"Portable build failed for {lang}"
        log = (build / f"manuscript_{lang}.log").read_text(errors="replace")
        assert not any(token in log.lower() for token in ["overfull", "undefined", "missing character"])
        expected = page_texts(SOURCE / f"manuscript_{lang}.pdf")
        actual = page_texts(build / f"manuscript_{lang}.pdf")
        assert expected == actual, f"Portable PDF content differs for {lang}"
        report["languages"][lang] = {"pages": len(actual), "fresh_build": "passed", "identical_page_text": True}

report["bytes"] = ARCHIVE.stat().st_size
report["sha256"] = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
(QA / "package_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
