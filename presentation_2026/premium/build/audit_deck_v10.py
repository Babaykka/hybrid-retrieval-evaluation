"""Audit final scientific values, editable data, notes and rendered output."""
import os
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from lxml import etree as ET
from PIL import Image
from pypdf import PdfReader

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / 'presentation_2026/premium/build'
version = sys.argv[1] if len(sys.argv) > 1 else 'v4'
deck = BUILD / 'validated' / f'validated-{version}.pptx'
pdf = deck.with_suffix('.pdf')
m = json.loads((ROOT / 'revision_2026/results/manual_summary.json').read_text())
f = json.loads((ROOT / 'revision_2026/results/fullset_summary.json').read_text())
roc = json.loads((BUILD / '../reviews/test_roc.json').read_text())
d = f['populations']['all_queries']['depths']
ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def nums(ser, kind):
    return [float(v) for v in ser.xpath(f'./c:{kind}/c:numRef/c:numCache/c:pt/c:v/text() | ./c:{kind}/c:numLit/c:pt/c:v/text()', namespaces=ns)]

def near(actual, expected, tol=5.1e-9):
    assert len(actual) == len(expected), (len(actual), len(expected))
    assert all(abs(a-b) < tol for a, b in zip(actual, expected)), (actual, expected)

with ZipFile(deck) as z:
    assert z.testzip() is None
    charts = [ET.fromstring(z.read(f'ppt/slides/charts/chart{i}.xml')) for i in range(1, 6)]
    for c in charts:
        assert c.find('.//c:externalData', ns) is not None
    rev = ['rrf3', 'bge', 'e5', 'bm25']
    for ser, label in zip(charts[0].xpath('//c:ser', namespaces=ns), ['official', 'human']):
        near(nums(ser, 'val'), [m['metrics'][k][label] for k in rev])
    chance, curve, point = charts[1].xpath('//c:ser', namespaces=ns)
    near(nums(curve, 'xVal'), [p['fpr'] for p in roc['points']])
    near(nums(curve, 'yVal'), [p['tpr'] for p in roc['points']])
    near(nums(chance, 'xVal'), nums(chance, 'yVal'))
    near(nums(point, 'xVal'), [roc['operating_point']['fpr']]*80)
    near(nums(point, 'yVal'), [roc['operating_point']['tpr']]*80)
    assert all(n.get('formatCode') == '0.0' for n in charts[1].xpath('//c:valAx/c:numFmt', namespaces=ns))
    for ser, key in zip(charts[2].xpath('//c:ser', namespaces=ns), ['candidates_mean_all_queries', 'positives_mean_all_queries']):
        near(nums(ser, 'xVal'), [v['k'] for v in d])
        near(nums(ser, 'yVal'), [v[key] for v in d])
    for c, contrast in zip(charts[3:], ['rrf_variable_minus_e5', 'rrf_fixed200_minus_e5']):
        rows = [v for v in f['paired_inference']['all_queries'] if v['contrast'] == contrast]
        series = c.xpath('//c:ser', namespaces=ns)
        mean = series[-1]
        horizontal = (mean.findtext('c:tx/c:v', namespaces=ns) or mean.findtext('c:tx/c:strRef/c:strCache/c:pt/c:v', namespaces=ns) or '').endswith('(horizontal)')
        assert len(series) == (18 if horizontal else 2)
        if horizontal:
            near(nums(mean, 'yVal'), [5,4,3,2,1])
            for index, interval in enumerate(series[1:6]):
                lo, hi = rows[index]['bootstrap_ci95']
                near(nums(interval, 'xVal'), [lo,hi,hi,hi,hi])
                near(nums(interval, 'yVal'), [5-index]*5)
            depth_labels = series[-2].xpath('./c:dLbls/c:dLbl/c:tx/c:rich//a:t/text()', namespaces=ns)
            assert depth_labels == [f'K = {r["k"]}' for r in rows]
            near(nums(series[-2], 'yVal'), [5,4,3,2,1])
        else:
            near(nums(mean, 'xVal'), [v['k'] for v in rows])
        values = nums(mean, 'xVal' if horizontal else 'yVal')
        near(values, [v['mean_delta'] for v in rows])
        errors = mean.find('c:errBars', ns)
        assert errors.find('c:errValType', ns).get('val') == 'cust'
        assert errors.find('c:errDir', ns).get('val') == ('x' if horizontal else 'y')
        for side, sign, bound in [('plus', 1, 1), ('minus', -1, 0)]:
            offsets = [float(v) for v in errors.xpath(f'./c:{side}/c:numLit/c:pt/c:v/text() | ./c:{side}/c:numRef/c:numCache/c:pt/c:v/text()', namespaces=ns)]
            near([v+sign*e for v, e in zip(values, offsets)], [r['bootstrap_ci95'][bound] for r in rows])
    for c in charts[1:]:
        for ser in c.xpath('//c:scatterChart/c:ser', namespaces=ns):
            assert ser.find('c:smooth', ns).get('val') == '0'
            marker = ser.find('c:marker', ns)
            if marker is not None and marker.find('c:symbol', ns).get('val') != 'none':
                assert marker.find('c:spPr/a:solidFill', ns) is not None
    slides = sorted([p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', p)], key=lambda p: int(re.search(r'(\d+)\.xml', p).group(1)))
    notes = [p for p in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', p)]
    assert len(slides) == len(notes) == 18
    texts = [' '.join(ET.fromstring(z.read(p)).xpath('//a:t/text()', namespaces=ns)) for p in slides]
    visible = '\n'.join(texts)
    spoken = '\n'.join(' '.join(ET.fromstring(z.read(p)).xpath('//a:t/text()', namespaces=ns)) for p in notes)
    for bad in ['TODO', 'ChatGPT', 'oracle-assisted', '0.597', '0.967', 'ацона', 'Walnut Exporter', *PRIVATE_IDENTITY_TOKENS]:
        assert bad not in visible + spoken, bad
    assert not re.search(r'[А-Яа-яЁё]', visible)
    assert all((n not in texts[0] for n in PRIVATE_IDENTITY_TOKENS))
    assert all('Источники' in ' '.join(ET.fromstring(z.read(p)).xpath('//a:t/text()', namespaces=ns)) for p in notes)
    assert len([p for p in z.namelist() if p.startswith('ppt/embeddings/') and p.endswith('.xlsx')]) == 5

reader = PdfReader(pdf)
assert len(reader.pages) == 18
pdftexts = [p.extract_text() for p in reader.pages]
for value in ['0.248', '0.488', '0.433', '0.459', '0.644', '0.879', '0.828', '0.854']:
    assert value in pdftexts[5], value
assert '1.05' in pdftexts[4] and '17.47' in pdftexts[4]
assert '0.907' in pdftexts[7] and '0.875' in pdftexts[7]
assert all(v in pdftexts[7] for v in ['0.2', '0.4', '0.6', '0.8'])
assert '128.6' in pdftexts[8] and '14.4%' in pdftexts[10]
assert 'NDCG@10' in pdftexts[12]
assert all(f'K = {k}' in pdftexts[9] for k in [10,30,50,100,200])
assert all((token not in str(reader.metadata.author) for token in PRIVATE_IDENTITY_TOKENS))
for page in reader.pages:
    assert abs(float(page.mediabox.width)-float(page.mediabox.height)*16/9)<0.05

source_checks = {}
for name, expected in {
    'DAMDID_2026_Talk.pptx': '9e02be8176f1f6919afe98f1fb133e78345050ed57759c207d2abc040ba2c9ad',
    'DAMDID_2026_Talk.pdf': '99a89df8f9d4830fca3711a232b9bd2f5a7abcb451fb6112510ee5003874e71e',
}.items():
    actual = digest(ROOT / 'Презентация_DAMDID' / name)
    assert actual == expected, 'The preserved original changed'
    source_checks[name] = actual

preserved_v5 = {}
for name, expected in {
    'DAMDID_2026_Presentation.pptx': 'ab9f9c9fb2d0dce8cc6c82b3965e011254a856f05cc51bd7fd9fb797baf2a135',
    'DAMDID_2026_Presentation.pdf': '9a54a62c2ef0b23ae81f9524d7d2abaa10325a26bb48529437a284d847a4421d',
}.items():
    actual = digest(ROOT / 'Презентация_DAMDID_Новая' / name)
    assert actual == expected, 'The previously delivered v5 changed'
    preserved_v5[name] = actual

pixels = {}
for index, rgb in [(8, [0,127,120]), (9, [201,82,54]), (10, [201,82,54]), (11, [0,127,120])]:
    path = BUILD / 'pdf-render' / f'final-{index:02}.png'
    assert path.stat().st_mtime >= pdf.stat().st_mtime, 'Stale PDF rendering'
    im = np.asarray(Image.open(path).convert('RGB')).astype(int)
    crop = im[270:660,180:1100]
    count = int((np.abs(crop-np.array(rgb)).max(axis=2)<35).sum())
    assert count > 60, (index, count, 'missing chart evidence')
    pixels[index] = count

script = json.loads((BUILD / 'speaker_script.json').read_text())
assert sum(v['seconds'] for v in script) == 810
report = {
    'status': 'pass', 'version': version, 'slides': 18, 'main_slides': 13,
    'appendix_slides': 5, 'planned_seconds': 810,
    'native_charts_verified_against_source': 5, 'embedded_workbooks': 5,
    'custom_paired_error_bars_verified': 2, 'speaker_notes': 18,
    'pdf_plot_color_pixels': pixels, 'preserved_original_sha256': source_checks,
    'preserved_v5_sha256': preserved_v5,
    'sha256': {p.name: digest(p) for p in [deck, pdf]},
    'source_sha256': {n: digest(ROOT / 'revision_2026/results' / n) for n in ['manual_summary.json','fullset_summary.json']},
    'claim_boundary': 'Automated content and data audit. Visual/native application checks recorded separately.',
}
(BUILD / 'delivery_audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
