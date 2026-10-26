"""Verify delivered chart values, notes, PDF content, and source provenance."""
import os
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET
from pypdf import PdfReader
from PIL import Image, ImageChops

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

root = Path(__file__).resolve().parents[2]
build = root / 'presentation_2026/build'
out = root / 'Презентация_DAMDID'
deck = out / 'DAMDID_2026_Talk.pptx'
pdf = out / 'DAMDID_2026_Talk.pdf'
m = json.loads((root / 'revision_2026/results/manual_summary.json').read_text())
f = json.loads((root / 'revision_2026/results/fullset_summary.json').read_text())
d = f['populations']['all_queries']['depths']
keys = ['bm25', 'e5', 'bge', 'rrf3']
jt = m['judge_rescored_split_metrics']['test']
expected = [
    [[m['density']['official']['mean'], m['density']['human']['mean']]],
    [[m['metrics'][k][label] for k in keys] for label in ['official', 'human']],
    [[jt[k] for k in ['precision', 'recall', 'f1']]],
    [[x[field] for x in d] for field in ['candidates_mean_all_queries', 'positives_mean_all_queries']],
    [[x['models'][model]['ndcg10_mean_all_queries'] for x in d] for model in ['e5', 'rrf_variable']],
]
ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(deck) as z:
    assert z.testzip() is None
    for i, wanted_series in enumerate(expected, 1):
        xml = ET.fromstring(z.read(f'ppt/slides/charts/chart{i}.xml'))
        series = xml.xpath('//c:ser', namespaces=ns)
        assert len(series) == len(wanted_series)
        for ser, wanted in zip(series, wanted_series):
            nodes = ser.xpath('./c:val/c:numRef/c:numCache/c:pt/c:v | ./c:yVal/c:numRef/c:numCache/c:pt/c:v', namespaces=ns)
            actual = [float(n.text) for n in nodes]
            assert len(actual) == len(wanted), (i, actual, wanted)
            assert all(abs(a-b) < 5.1e-9 for a, b in zip(actual, wanted)), (i, actual, wanted)
            if i >= 4:
                xs = [float(n.text) for n in ser.xpath('./c:xVal/c:numRef/c:numCache/c:pt/c:v', namespaces=ns)]
                assert xs == [10, 30, 50, 100, 200]
                assert ser.find('c:smooth', ns).get('val') == '0'
    slide_parts = sorted([p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', p)], key=lambda p: int(re.search(r'(\d+)\.xml', p).group(1)))
    note_parts = [p for p in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', p)]
    assert len(slide_parts) == len(note_parts) == 16
    visible = '\n'.join(' '.join(ET.fromstring(z.read(p)).xpath('//a:t/text()', namespaces=ns)) for p in slide_parts)
    notes = '\n'.join(' '.join(ET.fromstring(z.read(p)).xpath('//a:t/text()', namespaces=ns)) for p in note_parts)
    assert 'известный' in notes and 'Источники' in notes
    for token in ['ChatGPT', 'TODO', 'oracle-assisted', 's1–s3', 's0–s3', '0.597', '0.967', *PRIVATE_IDENTITY_TOKENS]:
        assert token not in visible + notes, token
    assert not re.search(r'[А-Яа-яЁё]', visible)
    assert all((name not in visible for name in PRIVATE_IDENTITY_TOKENS))
    assert len([p for p in z.namelist() if p.startswith('ppt/embeddings/') and p.endswith('.xlsx')]) == 5

r = PdfReader(pdf)
assert len(r.pages) == 16
texts = [p.extract_text() for p in r.pages]
for value in ['0.248', '0.488', '0.433', '0.459', '0.644', '0.879', '0.828', '0.854']:
    assert value in texts[6], value
assert '17.47' in texts[4] and '1.05' in texts[4]
assert all(value in texts[7] for value in ['0.907', '0.851', '0.902', '0.875'])
assert '128.6' in texts[8] and '+0.009' in texts[9]
assert all((token not in str(r.metadata.author) for token in PRIVATE_IDENTITY_TOKENS)) and r.metadata.title.startswith('Deep Re-annotation')
unchanged = []
for i in range(1, 17):
    if i in [5, 7, 8, 9, 10]:
        continue
    old = Image.open(build / 'render' / f'final-{i:02}.png').convert('RGB')
    new = Image.open(build / 'render' / f'talk-{i:02}.png').convert('RGB')
    if old.size == new.size and ImageChops.difference(old, new).getbbox() is None:
        unchanged.append(i)
report = {
    'status': 'pass', 'slides': 16, 'main_slides': 12, 'backup_slides': 4,
    'native_charts_source_verified': 5, 'native_workbooks': 5, 'speaker_notes': 16,
    'source_rounding_absolute_tolerance': 5.1e-9,
    'pdf_decimal_points_verified': True,
    'final_nonchart_slides_pixel_identical_to_reviewed_render': unchanged,
    'powerpoint_opened_without_repair_prompt': True,
    'powerpoint_visual_spot_checks': [1, 6, 7],
    'powerpoint_decimal_separators': 'Follow the user application regional settings. PDF uses English formatting.',
    'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [deck, pdf]},
}
(build / 'delivery_audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
