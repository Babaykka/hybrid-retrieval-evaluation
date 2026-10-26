"""Compile both languages from a fresh extraction of the deliverable ZIP."""
import os
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pdfplumber

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parent
OUT = Path(tempfile.mkdtemp(prefix="archive_build_", dir=ROOT / "verification"))
with ZipFile(ROOT.parent / "DAMDID_90_revision_2026-09-14.zip") as z:
    assert z.testzip() is None
    z.extractall(OUT)
PACKAGE = OUT / "DAMDID_90_revision"
manifest = json.loads((PACKAGE / "SHA256SUMS.json").read_text())
for name, checksum in manifest.items():
    assert hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() == checksum, name
summary = json.loads((PACKAGE / "reproducibility/results/fullset_summary.json").read_text())
for name, artifact in summary["artifacts"].items():
    path = PACKAGE / "reproducibility/results" / name
    assert path.stat().st_size == artifact["bytes"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
for path in PACKAGE.rglob("*.tex"):
    content = path.read_text()
    for target in re.findall(r"\\input\{([^}]+)\}", content):
        assert (PACKAGE / target).is_file(), (path, target)
    for target in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", content):
        assert (PACKAGE / "figures" / target).is_file(), (path, target)
    assert not all((term not in content for term in PRIVATE_IDENTITY_TOKENS))

subprocess.run([sys.executable, str(PACKAGE / "reproducibility/build_tables.py"), "--package", str(PACKAGE)], check=True)
subprocess.run([sys.executable, str(PACKAGE / "reproducibility/make_figures.py"),
                "--results", str(PACKAGE / "reproducibility/results"), "--output", str(PACKAGE / "figures")], check=True)
for name, checksum in manifest.items():
    if name.endswith((".tex", ".pdf", ".svg", ".png")):
        assert hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() == checksum, ("regenerated", name)

compile_script = Path(os.environ.get("LATEX_COMPILE_HELPER", "compile_latex.py"))
report = {"zip_integrity": True, "files_verified": len(manifest), "regeneration_exact": True, "languages": {}}
for lang in ["en", "ru"]:
    build = OUT / ("build_" + lang)
    result = subprocess.run([sys.executable, str(compile_script), str(PACKAGE / f"manuscript_{lang}.tex"),
                             "--compiler", "texlive", "--engine", "xelatex", "--output-directory", str(build), "--json"],
                            capture_output=True, text=True, check=True)
    (OUT / f"compile_{lang}.json").write_text(result.stdout)
    log = (build / f"manuscript_{lang}.log").read_text()
    assert not any(token in log for token in ["Overfull", "Missing character", "There were undefined references"])
    with pdfplumber.open(PACKAGE / f"manuscript_{lang}.pdf") as expected, pdfplumber.open(build / f"manuscript_{lang}.pdf") as actual:
        expected_text = [p.extract_text() for p in expected.pages]
        actual_text = [p.extract_text() for p in actual.pages]
        assert expected_text == actual_text
        report["languages"][lang] = {"pages": len(actual.pages), "text_matches": True, "compile": "passed"}
        if lang == "en":
            assert 12 <= len(actual.pages) <= 15
(ROOT / "verification/archive_verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
