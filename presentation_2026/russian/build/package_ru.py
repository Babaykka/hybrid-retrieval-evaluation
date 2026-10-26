"""Package only the checked Russian deliverables and verify every archive byte."""
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pymupdf
from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / 'presentation_2026/russian/build'
OUT = ROOT / 'DAMDID_2026_Русский_доклад'
audit = json.loads((BUILD / 'delivery_audit_ru.json').read_text())
assert audit['status'] == 'pass' and audit['version'] == 'ru-v3'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old_pdf = pymupdf.open(BUILD / 'validated/validated-ru-v2.pdf')
new_pdf = pymupdf.open(BUILD / 'validated/validated-ru-v3.pdf')
changed = [i + 1 for i in range(20) if old_pdf[i].get_pixmap().samples != new_pdf[i].get_pixmap().samples]
assert changed == [4], changed
with ZipFile(BUILD / 'validated/validated-ru-v3.pptx') as z:
    note = ET.fromstring(z.read('ppt/notesSlides/notesSlide6.xml'))
    text = ' '.join(note.xpath('//*[local-name()="t"]/text()'))
    assert 'точная архитектура дополнительных каналов отбора не полностью установлена' in text

files = []
for suffix in ['pptx', 'pdf']:
    source = BUILD / 'validated' / f'validated-ru-v3.{suffix}'
    assert sha(source) == audit['sha256'][source.name]
    target = OUT / f'DAMDID_2026_Презентация_RU.{suffix}'
    shutil.copy2(source, target)
    assert sha(source) == sha(target)
    files.append(target)
for suffix in ['docx', 'txt']:
    target = OUT / f'DAMDID_2026_Текст_выступления_RU.{suffix}'
    assert sha(target) == audit['sha256'][target.name]
    files.append(target)
assert set(OUT.iterdir()) == set(files)
archive = ROOT / 'DAMDID_2026_Русский_доклад.zip'
assert not archive.exists(), 'Do not overwrite a previous package silently'
with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as z:
    for file in files:
        z.write(file, file.name)
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == {p.name for p in files}
    for file in files:
        assert z.read(file.name) == file.read_bytes()
report = {'status': 'pass', 'archive': str(archive), 'archive_sha256': sha(archive),
          'render_changes_from_native_reviewed_v2': changed,
          'files': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in files}}
(BUILD / 'package_audit_ru.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
