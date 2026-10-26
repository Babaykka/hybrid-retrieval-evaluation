"""Verify the narrow editing scope against the supplied originals and compile."""
import os
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw
import pdfplumber

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
QA = ROOT / "verification"
LEGACY = ROOT.parent / "revision_2026/previous_versions/delivery_revision"
HELPER = os.environ.get("LATEX_COMPILE_HELPER", "compile_latex.py")
report = {}


def between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def bibliography_entries(text):
    matches = list(re.finditer(r"\\bibitem\{([^}]+)\}", text))
    entries = {}
    for i, match in enumerate(matches):
        key = match.group(1)
        assert key not in entries, key
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries[key] = text[match.start():end].strip()
    return entries


for lang in ["en", "ru"]:
    original = Path(f"[local-path]{lang}.tex").read_text()
    revised = (SOURCE / f"manuscript_{lang}.tex").read_text()
    assert original.split(r"\begin{document}")[0] == revised.split(r"\begin{document}")[0]
    keyword = lambda s: re.search(r"\\keywords\{(.+?)\}\s*\\end\{abstract\}", s, re.S).group(1)
    assert keyword(original) == keyword(revised)
    related = r"\section{" + ("Related Work" if lang == "en" else "Связанные работы") + "}"
    data = r"\section{" + ("Data, Pooling, and Manual Re-annotation" if lang == "en" else "Данные, пулинг и ручная доразметка") + "}"
    assert between(original, related, data) == between(revised, related, data)
    intro_tail = "We study this problem at two levels." if lang == "en" else "В данной работе изучаются два уровня переоценки."
    assert between(original, intro_tail, related) == between(revised, intro_tail, related)
    section4 = r"\section{" + ("Task Formulation and Experimental Protocol" if lang == "en" else "Постановка задачи и экспериментальный протокол") + "}"
    assert between(original, section4, r"\begin{thebibliography}") == between(revised, section4, r"\begin{thebibliography}")
    subsection32 = r"\subsection{" + ("Pooling Procedure" if lang == "en" else "Формирование ручной подвыборки") + "}"
    subsection33 = r"\subsection{" + ("Dataset Characteristics" if lang == "en" else "Характеристики нового датасета") + "}"
    assert between(original, subsection32, subsection33) == between(revised, subsection32, subsection33)
    subsection31 = r"\subsection{" + ("Source Collection" if lang == "en" else "Исходная коллекция") + "}"
    old31 = between(original, subsection31, subsection32).strip().split("\n\n")
    new31 = between(revised, subsection31, subsection32).strip().split("\n\n")
    assert len(old31) == 2 and len(new31) == 3
    assert old31[1] == new31[1]
    strip_added = lambda s: s.replace("\n\\label{sec:example}", "").replace(f"\\input{{example_{lang}.tex}}\n\n", "")
    assert between(original, subsection33, section4) == strip_added(between(revised, subsection33, section4))
    old_bib = between(original, r"\begin{thebibliography}{99}", r"\end{thebibliography}")
    new_bib = between(revised, r"\begin{thebibliography}{99}", r"\end{thebibliography}")
    added_bib = (SOURCE / "additional_references.tex").read_text()
    entries = bibliography_entries(new_bib.replace(r"\input{additional_references.tex}", added_bib))
    assert entries == bibliography_entries(old_bib) | bibliography_entries(added_bib)
    first_citations = list(dict.fromkeys(
        key.strip()
        for match in re.finditer(r"\\cite\{([^}]+)\}", revised.split(r"\begin{thebibliography}")[0])
        for key in match.group(1).split(",")
    ))
    assert list(entries) == first_citations, (lang, list(entries), first_citations)
    assert not re.search(r"\bs[1-3]\b", revised)
    definition = ("Here, deep re-annotation means judging multiple candidate answers within a defined pool, rather than assuming that the original positive passage exhausts the relevant answers. "
                  if lang == "en" else "Под углублённой доразметкой здесь понимается оценка нескольких ответов-кандидатов в заданном пуле без предположения, что исходный положительный фрагмент исчерпывает все релевантные ответы. ")
    assert between(original, r"\begin{abstract}", r"\keywords") == between(revised, r"\begin{abstract}", r"\keywords").replace(definition, "")
    intro_section = r"\section{" + ("Introduction" if lang == "en" else "Введение") + "}"
    old_intro = between(original, intro_section, related).strip().split("\n\n")
    new_intro = between(revised, intro_section, related).strip().split("\n\n")
    assert [new_intro[i] for i in [0, 3, 4]] == old_intro[:3]
    assert new_intro[7:] == old_intro[3:]
    (QA / f"changes_{lang}.diff").write_text("".join(difflib.unified_diff(original.splitlines(True), revised.splitlines(True),
                                                                      fromfile=f"original/manuscript_{lang}.tex", tofile=f"edited/manuscript_{lang}.tex")))
    graphics = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", revised)
    for name in graphics:
        assert (LEGACY / "figures" / name).is_file(), name
        if name == "protocol_schematic_en.pdf":
            subprocess.run([sys.executable, str(ROOT / "fix_protocol_arrows.py")], check=True)
        else:
            shutil.copy2(LEGACY / "figures" / name, SOURCE / "figures" / name)
    build = ROOT / "build" / lang
    result = subprocess.run([sys.executable, HELPER, str(SOURCE / f"manuscript_{lang}.tex"), "--compiler", "texlive",
                             "--engine", "pdflatex" if lang == "en" else "xelatex", "--output-directory", str(build), "--json"],
                            capture_output=True, text=True)
    (QA / f"compile_{lang}.json").write_text(result.stdout)
    assert result.returncode == 0, f"Build failed; see {QA / f'compile_{lang}.json'}"
    log = (build / f"manuscript_{lang}.log").read_text(errors="replace")
    failures = [line for line in log.splitlines() if "Overfull" in line or "Missing character" in line or "undefined" in line.lower()]
    assert not failures, failures
    aux = (build / f"manuscript_{lang}.aux").read_text()
    citation_numbers = {key: int(number) for key, number in re.findall(r"\\bibcite\{([^}]+)\}\{(\d+)\}", aux)}
    assert citation_numbers == {key: i for i, key in enumerate(first_citations, 1)}
    pdf = build / f"manuscript_{lang}.pdf"
    shutil.copy2(pdf, SOURCE / pdf.name)
    with pdfplumber.open(pdf) as doc:
        texts = [p.extract_text() or "" for p in doc.pages]
        assert all(texts)
        joined = "\n".join(texts)
        assert "??" not in joined and "ChatGPT" not in joined and "Codex" not in joined
        assert "3.3" in joined
        assert not re.search(r"\bs[1-3]\b", joined)
        assert "0.597" in joined and "0.877" in joined and "0.701" in joined and "0.967" in joined
        (QA / f"text_{lang}.txt").write_text("\n\n--- PAGE ---\n\n".join(texts))
        report[lang] = {"pages": len(doc.pages), "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
                       "keywords_unchanged": True, "related_work_unchanged": True, "intro_original_tail_unchanged": True,
                       "intro_paragraph_order_verified": True, "abstract_only_definition_added": True,
                       "sections_4_to_9_unchanged": True, "subsection_3_2_unchanged": True,
                       "subsection_3_1_original_example_unchanged": True,
                       "subsection_3_3_only_example_added": True, "original_bibliography_preserved": True,
                       "bibliography_entry_text_preserved": True, "bibliography_reordered_by_first_citation": True,
                       "compiled_citation_numbers": citation_numbers,
                       "original_figures_preserved": [name for name in graphics if name != "protocol_schematic_en.pdf"],
                       "figure_geometry_edits": [name for name in graphics if name == "protocol_schematic_en.pdf"],
                       "compiler": "pdflatex" if lang == "en" else "xelatex",
                       "numeric_validation": "Legacy values retained at author's request; NOT confirmed by corrected evaluation"}
    pages = QA / lang
    pages.mkdir(exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "80", "-png", str(pdf), str(pages / "page")], check=True, capture_output=True)
    files = sorted(pages.glob("page-*.png"))
    for start in range(0, len(files), 6):
        sheet = Image.new("RGB", (990, 990), "#dddfe2")
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(files[start:start+6]):
            im = Image.open(path).convert("RGB")
            im.thumbnail((310, 450))
            x, y = (i % 3)*330+10, (i // 3)*495+24
            sheet.paste(im, (x, y))
            draw.text((x, y-18), f"{lang.upper()} / {start+i+1}", fill="black")
        sheet.save(pages / f"contact-{start//6+1}.png")
    print(json.dumps({lang: report[lang]}, ensure_ascii=False), flush=True)
(QA / "scope_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
