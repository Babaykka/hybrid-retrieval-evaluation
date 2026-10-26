"""Assemble a portable source package without including the original data archive."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PACKAGE = ROOT / "package"
SCRIPTS = ["manual_eval.py", "fullset_eval.py", "build_tables.py", "make_figures.py"]


def clean_provenance(obj):
    if isinstance(obj, dict):
        return {k: ("phd2.zip" if k == "zip_path" else "python3" if k == "executable" else
                    ["python3", "fullset_eval.py", "--zip", "phd2.zip"] if k == "command" else clean_provenance(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_provenance(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("/Users/"):
        return Path(obj).name
    return obj


def prepare():
    target = PACKAGE / "reproducibility"
    target.mkdir(exist_ok=True)
    for name in SCRIPTS:
        shutil.copy2(ROOT / name, target / name)
    shutil.copytree(ROOT / "results", target / "results", dirs_exist_ok=True)
    for path in (target / "results").glob("*.json"):
        data = clean_provenance(json.loads(path.read_text()))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    summary_path = target / "results/fullset_summary.json"
    summary = json.loads(summary_path.read_text())
    for name, artifact in summary["artifacts"].items():
        path = target / "results" / name
        if path.is_file():
            artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            artifact["bytes"] = path.stat().st_size
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    subprocess.run([sys.executable, str(target / "build_tables.py"), "--package", str(PACKAGE)], check=True)
    subprocess.run([sys.executable, str(target / "make_figures.py"), "--results", str(target / "results"),
                    "--output", str(PACKAGE / "figures")], check=True)


def deliver():
    for lang in ["en", "ru"]:
        shutil.copy2(ROOT / f"build/{lang}/manuscript_{lang}.pdf", PACKAGE / f"manuscript_{lang}.pdf")
    shutil.copy2(ROOT / "verification/verification_report.json", PACKAGE / "reproducibility/verification_report.json")
    archive = ROOT / "previous_versions"
    archive.mkdir(exist_ok=True)
    client = BASE / "delivery_revision"
    if not (archive / "delivery_revision").exists():
        shutil.move(str(client), str(archive / "delivery_revision"))
    shutil.copytree(PACKAGE, client, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".*", "__pycache__", "*.pyc"))
    damdid = BASE / "DAMDID"
    if not (archive / "DAMDID").exists():
        shutil.move(str(damdid), str(archive / "DAMDID"))
    damdid.mkdir(exist_ok=True)
    for name in ["figures", "tables"]:
        shutil.copytree(client / name, damdid / name, dirs_exist_ok=True)
    for path in client.iterdir():
        if path.is_file() and path.suffix in {".tex", ".cls", ".bst"} and not path.name.startswith("manuscript_"):
            shutil.copy2(path, damdid / path.name)
    for lang, old_name in [("en", "manuscript_damdid_en"), ("ru", "manuscript_damdid")]:
        for suffix in ["tex", "pdf"]:
            shutil.copy2(client / f"manuscript_{lang}.{suffix}", damdid / f"{old_name}.{suffix}")
    files = sorted(p for p in client.rglob("*") if p.is_file() and p.name != "SHA256SUMS.json")
    checksums = {str(p.relative_to(client)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (client / "SHA256SUMS.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2) + "\n")
    zip_path = BASE / "DAMDID_90_revision_2026-09-14.zip"
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(p for p in client.rglob("*") if p.is_file()):
            z.write(path, Path("DAMDID_90_revision") / path.relative_to(client))
    with ZipFile(zip_path) as z:
        assert z.testzip() is None
    print(json.dumps({"client": str(client), "zip": str(zip_path), "bytes": zip_path.stat().st_size,
                      "files": len(checksums) + 1}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "deliver"])
    args = parser.parse_args()
    prepare() if args.action == "prepare" else deliver()
