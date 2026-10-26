import os
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from lxml import etree as E
from pypdf import PdfReader

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'presentation_2026/review_2026-10-12/build'
OUT = ROOT / 'DAMDID_2026_После_рецензии'
hashof = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pptx = OUT / 'DAMDID_2026_Презентация_RU.pptx'
assert hashof(pptx) == '7fd2b2a5e3edb0cbd30ee467f0033aea34068482a7a828c0064c3de78578c2b3'
shutil.copy2(B / 'validated/validated_v3.pptx', pptx)
pdf = OUT / 'DAMDID_2026_Презентация_RU.pdf'
shutil.copy2(B / 'render_v3/validated_v3.pdf', pdf)
docx = OUT / 'DAMDID_2026_Текст_выступления_RU.docx'
files = [pptx, pdf, docx]
for file in [pptx, docx]:
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        text = '\n'.join('\n'.join(E.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.endswith('.xml'))
        for forbidden in ['Грач Бабаян', 'ChatGPT', 'TODO', '/Users/', 'Study results:', *PRIVATE_IDENTITY_TOKENS]:
            assert forbidden.casefold() not in text.casefold(), (file.name,forbidden)
r = PdfReader(pdf)
assert len(r.pages) == 26
uris = [str(a.get_object().get('/A',{}).get('/URI','')) for a in r.pages[18].get('/Annots',[])]
assert len([u for u in uris if u.startswith('https://')]) == 8
assert '101 093' in r.pages[10].extract_text()
assert '6 980' in r.pages[4].extract_text()
for value in (list(r.metadata.values()) + [p.extract_text() for p in r.pages]):
    assert not all((x not in str(value).casefold() for x in PRIVATE_IDENTITY_TOKENS))
archive = ROOT / 'DAMDID_2026_После_рецензии.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for file in files: z.write(file, file.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == {p.name for p in files}
    for file in files: assert hashlib.sha256(z.read(file.name)).hexdigest() == hashof(file)
report = {'archive':str(archive),'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashof(p)} for p in files},'pdf_slides':26,'bibliography_hyperlinks':8,'zip_integrity':'pass','packaged_files_match':'pass'}
(B / 'delivery.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
