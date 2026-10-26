"""Create a concise client handoff with PDFs and a self-contained LaTeX ZIP."""
import os
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pdfplumber

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
SOURCE = BASE / "delivery_revision"
TARGET = BASE / "delivery_submission"
TARGET.mkdir(exist_ok=True)
NOTES = """Редакция статьи DAMDID 2026, заявка 90

Представлены английский и русский PDF и полный комплект исходников LaTeX.
Замечания рецензентов и ответы авторов включены в конец обеих версий.

Добавлены определение углублённой доразметки и конкретный пример запроса
с метками до и после разметки. Во введении рассмотрены наборы Google,
Yahoo! и Yandex, обоснован выбор MS MARCO и уточнены границы обобщения.

Проверка расчётов выявила ошибки прежней нормировки NDCG и исключение
неуспешных запросов. Таблицы и графики пересчитаны с общим IDCG по пулу
и единым набором запросов. Вывод о влиянии доразметки сохраняется.
Сравнение RRF изменилось: он ниже E5 при глубине 10, но выше при четырёх
больших проверенных глубинах. Это изменение раскрыто в ответах рецензентам.

Точная привязка вспомогательных каналов e5-rerank и s0–s3 к моделям
пока не подтверждена авторами подготовки данных. В статье они описаны
без предположений об архитектуре и не включены в сравнение систем.

Новое обучение моделей не проводилось. Сравнение более сильных судей
и обучение судьи с известным релевантным ответом оставлены будущей работой.
"""
BUILD = """LaTeX sources: DAMDID 2026, submission 90

Main files: manuscript_en.tex and manuscript_ru.tex.
Compile with XeLaTeX (TeX Live/MacTeX, Computer Modern Unicode fonts):

latexmk -xelatex manuscript_en.tex
latexmk -xelatex manuscript_ru.tex

Without latexmk, run xelatex twice for each main file.
Keep the tables and figures folders beside the main files.
Bibliography: references.tex; BibTeX is not required.
No Python, model downloads or original data archive are needed to compile.
The reviewers' responses are already included at the end of each paper.
"""
for lang in ["en", "ru"]:
    shutil.copy2(SOURCE / f"manuscript_{lang}.pdf", TARGET / f"manuscript_{lang}.pdf")
(TARGET / "Изменения_редакции.txt").write_text(NOTES, encoding="utf-8")
source_zip = TARGET / "LaTeX_sources.zip"
with ZipFile(source_zip, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(SOURCE.glob("*")):
        if path.is_file() and path.suffix in {".tex", ".cls", ".bst"}:
            z.write(path, path.name)
    for path in sorted((SOURCE / "tables").glob("*.tex")):
        z.write(path, path.relative_to(SOURCE))
    for stem in ["protocol", "manual_effect", "judge_diagnostics", "fullset_pooling"]:
        for lang in ["en", "ru"]:
            for suffix in ["pdf", "png", "svg"]:
                path = SOURCE / "figures" / f"{stem}_{lang}.{suffix}"
                z.write(path, path.relative_to(SOURCE))
    z.writestr("BUILD.txt", BUILD)

temporary = Path(tempfile.mkdtemp(prefix="client_sources_", dir=ROOT / "verification"))
with ZipFile(source_zip) as z:
    assert z.testzip() is None
    z.extractall(temporary)
helper = os.environ.get("LATEX_COMPILE_HELPER", "compile_latex.py")
report = {"languages": {}, "source_zip_files": len(z.namelist())}
for lang in ["en", "ru"]:
    build = temporary / ("build_" + lang)
    result = subprocess.run([sys.executable, helper, str(temporary / f"manuscript_{lang}.tex"),
                             "--compiler", "texlive", "--engine", "xelatex", "--output-directory", str(build), "--json"],
                            capture_output=True, text=True, check=True)
    log = (build / f"manuscript_{lang}.log").read_text()
    assert not any(s in log for s in ["Overfull", "Missing character", "There were undefined references"])
    with pdfplumber.open(TARGET / f"manuscript_{lang}.pdf") as expected, pdfplumber.open(build / f"manuscript_{lang}.pdf") as actual:
        assert [p.extract_text() for p in expected.pages] == [p.extract_text() for p in actual.pages]
        report["languages"][lang] = {"pages": len(actual.pages), "source_compile": "passed", "text_matches": True}
outer = BASE / "delivery_revision_90.zip"
with ZipFile(outer, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(TARGET.iterdir()):
        if path.is_file():
            z.write(path, path.name)
with ZipFile(outer) as z:
    assert z.testzip() is None
report.update(archive=str(outer), bytes=outer.stat().st_size, files=sorted(p.name for p in TARGET.iterdir()))
(ROOT / "verification/client_handoff_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
