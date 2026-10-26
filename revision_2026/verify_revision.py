"""Verify evaluation invariants and render page contact sheets for visual review."""
import os
import csv
import io
import json
import math
import subprocess
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parent
QA = ROOT / "verification"
QA.mkdir(exist_ok=True)
report = {}
manual = json.loads((ROOT / "results/manual_summary.json").read_text())
rerun = json.loads((QA / "manual/manual_summary.json").read_text())
assert manual == rerun
report["manual_rerun_exact"] = True
with np.load(ROOT / "results/manual_per_query.npz") as a:
    for key in ["official", "human", "judge"]:
        assert a[key].shape == (1179, 6)
        assert np.isfinite(a[key]).all()
        assert ((a[key] >= 0) & (a[key] <= 1)).all()
        for i, model in enumerate(a["models"]):
            assert np.isclose(a[key][:, i].mean(), manual["metrics"][str(model)][key])
    assert a["clean"].sum() == 1156
report["manual_array_invariants"] = True
with ZipFile(ROOT.parent / "phd2.zip") as z:
    data = {}
    for name in sorted(p for p in z.namelist() if p.startswith("phd2/new_data/") and p.endswith(".json")):
        data.update(json.loads(z.read(name)))
    dev = {(r["query-id"], r["corpus-id"]) for r in csv.DictReader(
        io.StringIO(z.read("phd2/msmarco/qrels/dev.tsv").decode()), delimiter="\t") if float(r["score"]) > 0}
    docs = data["1086224"]["documents"]
    for docid, is_official, human in [("7112148", True, True), ("7399382", False, True), ("987600", False, False)]:
        assert (("1086224", docid) in dev) == is_official
        assert (docs[docid]["true relevant"] in [1, 2]) == human
    report["example_verified"] = {d: docs[d]["text"] for d in ["7112148", "7399382", "987600"]}

for lang in ["en", "ru"]:
    pdf = ROOT / f"build/{lang}/manuscript_{lang}.pdf"
    output = QA / lang
    output.mkdir(exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "80", "-png", str(pdf), str(output / "page")], check=True, capture_output=True)
    with pdfplumber.open(pdf) as doc:
        texts = [page.extract_text() or "" for page in doc.pages]
        assert all(text.strip() for text in texts)
        assert all((token not in str('\n'.join(texts)) for token in PRIVATE_IDENTITY_TOKENS))
        assert "oracle-assisted" not in "\n".join(texts)
        assert "??" not in "\n".join(texts)
        assert all((token not in str(texts[0]) for token in PRIVATE_IDENTITY_TOKENS)) and all((token not in str(texts[0]) for token in PRIVATE_IDENTITY_TOKENS))
        report[lang] = {"pages": len(doc.pages), "page_text_lengths": [len(t) for t in texts],
                       "outside_page_characters": sum(c["x0"] < 0 or c["x1"] > p.width + 1 or c["top"] < 0 or c["bottom"] > p.height + 1 for p in doc.pages for c in p.chars)}
        (output / "extracted.txt").write_text("\n\n--- PAGE ---\n\n".join(texts))
    images = sorted(output.glob("page-*.png"))
    for start in range(0, len(images), 6):
        sheet = Image.new("RGB", (990, 990), "#dddfe2")
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(images[start:start+6]):
            img = Image.open(path).convert("RGB")
            img.thumbnail((310, 450))
            x, y = (i % 3) * 330 + 10, (i // 3) * 495 + 24
            sheet.paste(img, (x, y))
            draw.text((x, y-18), f"{lang.upper()} / {start+i+1}", fill="black")
        sheet.save(output / f"contact-{start//6+1}.png")
(QA / "verification_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
