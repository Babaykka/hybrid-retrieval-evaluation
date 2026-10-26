"""Verify the single approved insertion and update the current delivery copies."""
import os
import hashlib
import json
import re
import shutil
from pathlib import Path
from zipfile import ZipFile

import pymupdf

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
SOURCE = ROOT / 'original_based_2026/source'
BEFORE = QA / 'before'
block = '\\section*{Acknowledgements}\n\nThe work is supported by the Russian Science Foundation under Agreement No.~__REMOVED_IDENTIFIER__.\n\n'
old = (BEFORE / 'original_based_2026/source/manuscript_en.tex').read_text()
new = (SOURCE / 'manuscript_en.tex').read_text()
assert block not in old and new.count(block) == 1
assert new == old.replace('\\begin{thebibliography}{99}', block + '\\begin{thebibliography}{99}')
for path in (BEFORE / 'original_based_2026/source').rglob('*'):
    if path.is_file() and path.name not in {'manuscript_en.tex', 'manuscript_en.pdf'}:
        assert path.read_bytes() == (SOURCE / path.relative_to(BEFORE / 'original_based_2026/source')).read_bytes()
log = (ROOT / 'original_based_2026/build/en/manuscript_en.log').read_text()
assert not re.search('Overfull|undefined|Missing character', log, re.I)
pdf = ROOT / 'original_based_2026/build/en/manuscript_en.pdf'
old_pdf = pymupdf.open(BEFORE / 'original_based_2026/source/manuscript_en.pdf')
new_pdf = pymupdf.open(pdf)
assert len(old_pdf) == len(new_pdf) == 16
changed_pages = [i + 1 for i in range(16) if old_pdf[i].get_pixmap().samples != new_pdf[i].get_pixmap().samples]
assert changed_pages == [14, 15]
page_text = ' '.join(new_pdf[13].get_text().split())
assert all((token not in str(page_text) for token in PRIVATE_IDENTITY_TOKENS))
shutil.copy2(pdf, SOURCE / pdf.name)
delivery = ROOT / 'delivery_editorial'
shutil.copy2(pdf, delivery / pdf.name)

def replace_entries(path, replacements):
    backup = BEFORE / path.relative_to(ROOT)
    with ZipFile(backup) as original, ZipFile(path, 'w') as updated:
        assert set(replacements) <= set(original.namelist())
        for info in original.infolist():
            updated.writestr(info, replacements.get(info.filename, original.read(info.filename)))
    with ZipFile(backup) as original, ZipFile(path) as updated:
        assert updated.testzip() is None
        assert updated.namelist() == original.namelist()
        for name in updated.namelist():
            assert updated.read(name) == replacements.get(name, original.read(name))

replace_entries(delivery / 'LaTeX_sources.zip', {'manuscript_en.tex': new.encode()})
replace_entries(ROOT / 'delivery_editorial.zip', {
    'manuscript_en.pdf': pdf.read_bytes(),
    'LaTeX_sources.zip': (delivery / 'LaTeX_sources.zip').read_bytes(),
})
replace_entries(ROOT / 'editorial_source_revision.zip', {
    'manuscript_en.tex': new.encode(), 'manuscript_en.pdf': pdf.read_bytes(),
})
paths = [SOURCE / 'manuscript_en.tex', delivery / pdf.name, delivery / 'LaTeX_sources.zip',
         ROOT / 'delivery_editorial.zip', ROOT / 'editorial_source_revision.zip']
report = {'status': 'pass', 'change': 'Acknowledgements inserted immediately before the bibliography',
          'pages': len(new_pdf), 'changed_pdf_pages': changed_pages,
          'other_source_files_unchanged': True, 'unchanged_archive_entries_preserved': True,
          'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(QA / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
