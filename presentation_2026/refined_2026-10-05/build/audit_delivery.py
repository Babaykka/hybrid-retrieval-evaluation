"""Check editable chart data, notes, rendered text and preserved deliverables."""
import os
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pymupdf
from docx import Document
from lxml import etree as ET

PRIVATE_IDENTITY_TOKENS = tuple(token.strip() for token in os.environ.get("PRIVATE_IDENTITY_TOKENS", "").split("|") if token.strip())

ROOT = Path(__file__).resolve().parents[3]
BUILD = Path(__file__).parent
OUT = ROOT / 'DAMDID_2026_Обновлённый_доклад'
OLD = ROOT / 'DAMDID_2026_Русский_доклад'
VERSION = sys.argv[1] if len(sys.argv) > 1 else 'refined-v4'
deck = BUILD / 'validated' / f'validated-{VERSION}.pptx'
pdf = deck.with_suffix('.pdf')
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
norm = lambda s: re.sub(r'\s+', '', s)
manual = json.loads((ROOT / 'revision_2026/results/manual_summary.json').read_text())
full = json.loads((ROOT / 'revision_2026/results/fullset_summary.json').read_text())
roc = json.loads((ROOT / 'presentation_2026/premium/reviews/test_roc.json').read_text())
scripts = json.loads((BUILD / 'speech_ru.json').read_text())
timing = json.loads((BUILD / 'script_audit_ru.json').read_text())


def near(actual, expected):
    assert len(actual) == len(expected), (actual, expected)
    assert np.allclose(actual, expected, rtol=0, atol=5.1e-9), (actual, expected)


def nums(node, kind):
    return [float(v) for v in node.xpath(
        f'./c:{kind}/c:numRef/c:numCache/c:pt/c:v/text() | ./c:{kind}/c:numLit/c:pt/c:v/text()',
        namespaces=ns)]


def table_values(root):
    return [[''.join(cell.xpath('.//a:t/text()', namespaces=ns))
             for cell in row.findall('a:tc', ns)]
            for row in root.xpath('//a:tbl/a:tr', namespaces=ns)]


def ru_num(v, decimals=3):
    return f'{v:.{decimals}f}'.replace('.', ',')


with ZipFile(deck) as z, ZipFile(OLD / 'DAMDID_2026_Презентация_RU.pptx') as old:
    assert z.testzip() is None
    assert len([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]) == 22
    assert len([n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', n)]) == 22
    charts = [ET.fromstring(z.read(f'ppt/slides/charts/chart{i}.xml')) for i in range(1, 7)]
    assert len([n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]) == 6
    for i, chart in enumerate(charts[1:], 1):
        original = ET.fromstring(old.read(f'ppt/slides/charts/chart{i}.xml'))
        for path in ['//c:ser//c:numCache/c:pt/c:v/text()', '//c:ser//c:numLit/c:pt/c:v/text()']:
            near([float(v) for v in chart.xpath(path, namespaces=ns)],
                 [float(v) for v in original.xpath(path, namespaces=ns)])
    for chart in charts:
        assert chart.find('.//c:externalData', ns) is not None
    near(nums(charts[0].find('.//c:ser', ns), 'val'), [.436, .438, .440, .450])
    for ser, label in zip(charts[1].xpath('//c:ser', namespaces=ns), ['official', 'human']):
        near(nums(ser, 'val'), [manual['metrics'][k][label] for k in ['rrf3', 'bge', 'e5', 'bm25']])
    curve = charts[2].xpath('//c:ser', namespaces=ns)[1]
    near(nums(curve, 'xVal'), [p['fpr'] for p in roc['points']])
    near(nums(curve, 'yVal'), [p['tpr'] for p in roc['points']])
    depths = full['populations']['all_queries']['depths']
    for ser, key in zip(charts[3].xpath('//c:ser', namespaces=ns), ['candidates_mean_all_queries', 'positives_mean_all_queries']):
        near(nums(ser, 'xVal'), [p['k'] for p in depths])
        near(nums(ser, 'yVal'), [p[key] for p in depths])
    for chart, contrast, horizontal in zip(charts[4:], ['rrf_variable_minus_e5', 'rrf_fixed200_minus_e5'], [True, False]):
        rows = [r for r in full['paired_inference']['all_queries'] if r['contrast'] == contrast]
        series = chart.xpath('//c:ser', namespaces=ns)[-1]
        values = nums(series, 'xVal' if horizontal else 'yVal')
        near(values, [r['mean_delta'] for r in rows])
        err = series.find('c:errBars', ns)
        assert err.find('c:errDir', ns).get('val') == ('x' if horizontal else 'y')
        for side, sign, bound in [('plus', 1, 1), ('minus', -1, 0)]:
            near([v + sign * e for v, e in zip(values, nums(err, side))],
                 [r['bootstrap_ci95'][bound] for r in rows])
    text, notes, tables = [], [], {}
    for i in range(1, 23):
        root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        text.append(' '.join(root.xpath('//a:t/text()', namespaces=ns)))
        assert re.search('[А-Яа-яЁё]', text[-1])
        if root.xpath('//a:tbl', namespaces=ns):
            tables[i] = table_values(root)
        notes.append(' '.join(ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml')).xpath('//a:t/text()', namespaces=ns)))
    assert list(tables) == [2, 4, 7, 17, 18, 19, 20, 21]
    for i, item in enumerate(scripts):
        assert all(norm(p) in norm(notes[i]) for p in item['paragraphs']), i + 1
        assert 'Источники' in notes[i]
    for row, k in zip(tables[17][1:], ['bm25', 'e5', 'bge', 'rrf3']):
        assert row[1] == '+' + ru_num(manual['metrics'][k]['human_minus_official']['mean'])
        assert row[2] == ' ... '.join(ru_num(v) for v in manual['metrics'][k]['human_minus_official']['ci95'])
    assert [row[1:] for row in tables[18][1:]] == [['1 300', '506'], ['314', '2 882']]
    for row, data in zip(tables[19][1:], depths):
        expected = [str(data['k']), ru_num(data['candidates_mean_all_queries'], 1),
                    ru_num(data['positives_mean_all_queries'], 1)]
        for model in ['e5', 'rrf_variable', 'rrf_fixed200']:
            expected.append(ru_num(data['models'][model]['ndcg10_mean_all_queries']))
        assert row == expected, (row, expected)
    for row, k in zip(tables[20][1:], ['bm25', 'e5', 'bge', 'rrf3']):
        assert row[1:] == [ru_num(manual['metrics'][k]['human']), ru_num(manual['metrics'][k]['clean_queries_human'])]
    for key in ['official', 'human']:
        assert ru_num(manual['judge_rerank_heldout'][key]) in text[21]
    assert all((name not in text[0] for name in PRIVATE_IDENTITY_TOKENS))
    xml_text = '\n'.join(z.read(n).decode(errors='replace') for n in z.namelist() if n.endswith('.xml'))
    for bad in ['Грач', 'Бабаян', 'TODO', 'ChatGPT', *PRIVATE_IDENTITY_TOKENS]:
        assert bad not in xml_text, bad
    for bad in ['oracle-assisted', '0.597', '0.967', '0,597', '0,967']:
        assert bad not in '\n'.join(text), bad

csv_url = 'https://raw.githubusercontent.com/microsoft/MSMARCO-Passage-Ranking-Submissions/abb44144f563e7972d5131f5d6acc2092877964c/leaderboard/leaderboard.csv'
source_csv = urllib.request.urlopen(csv_url).read().decode()
rows = {r['id']: r for r in csv.DictReader(io.StringIO(source_csv))}
for key, value in [('20220317-SLM', .450), ('20220602-fusion', .440), ('20220919-cotmae', .438), ('20211210-lichee-feeds', .436)]:
    assert rows[key]['type'] == 'full ranking' and float(rows[key]['eval']) == value

pdfdoc = pymupdf.open(pdf)
assert len(pdfdoc) == 22
pdftexts = [p.get_text() for p in pdfdoc]
for i, page in enumerate(pdfdoc):
    assert abs(page.rect.width / page.rect.height - 16 / 9) < .0001
    for word in page.get_text('words'):
        assert word[0] >= -1 and word[1] >= -1 and word[2] <= page.rect.width + 1 and word[3] <= page.rect.height + 1, (i + 1, word)
    # Native table text and headings must survive the final PowerPoint export.
    if i + 1 in tables:
        for row in tables[i + 1]:
            for cell in row:
                assert norm(cell) in norm(pdftexts[i]), (i + 1, cell)
assert all(v in pdftexts[2] for v in ['30.11.2022', '01.01.2023', '0,450', '0,440', '0,438', '0,436'])
assert all(v in pdftexts[8] for v in ['0,248', '0,488', '0,433', '0,459', '0,644', '0,879', '0,828', '0,854'])
assert '1,05' in pdftexts[7] and '17,47' in pdftexts[7]
assert '0,907' in pdftexts[10] and '0,875' in pdftexts[10]
assert '128,6' in pdftexts[11] and '14,4%' in pdftexts[13]
assert all((token not in str(pdftexts[15]) for token in PRIVATE_IDENTITY_TOKENS))

docx = OUT / 'DAMDID_2026_Текст_выступления_RU.docx'
txt = OUT / 'DAMDID_2026_Текст_выступления_RU.txt'
document = Document(docx)
assert len([p for p in document.paragraphs if p.style.name == 'Heading 1']) == 16
docx_text = '\n'.join(p.text for p in document.paragraphs)
speech_pdf = pymupdf.open(BUILD / 'speech-render-v2/DAMDID_2026_Текст_выступления_RU.pdf')
speech_pdf_text = norm('\n'.join(p.get_text() for p in speech_pdf))
for item in scripts:
    for paragraph in item['paragraphs']:
        assert paragraph in docx_text and paragraph in txt.read_text()
        assert norm(paragraph) in speech_pdf_text, paragraph
with ZipFile(docx) as z:
    for part in ['word/document.xml', 'word/styles.xml']:
        assert not ET.fromstring(z.read(part)).xpath('//*[local-name()="pBdr"]')
    for name in z.namelist():
        if name.endswith('.xml'):
            contents = z.read(name).decode(errors='replace')
            assert not all((v not in contents for v in PRIVATE_IDENTITY_TOKENS))

old_hashes = {
    'DAMDID_2026_Презентация_RU.pptx': 'f75bc5677f974d9ebdea6690db8c3e22ed602df05795c410498d43f17804df75',
    'DAMDID_2026_Презентация_RU.pdf': 'da839a70d6731f7fe949e04678c6f10f91663da3984852f8d449e591dbed1426',
    'DAMDID_2026_Текст_выступления_RU.txt': '55e5bdb07125fd0321cde2c0c041a5aa248edb1b7ef893b9de1ae66f62756c82',
}
for name, expected in old_hashes.items():
    assert sha(OLD / name) == expected, name
report = {
    'status': 'pass', 'version': VERSION, 'slides': 22, 'main_slides': 16,
    'appendix_slides': 6, 'native_charts': 6, 'preserved_research_charts': 5,
    'table_owner_slides': list(tables), 'speaker_notes_synchronized': 16,
    'speech_pages': len(speech_pdf), 'estimated_seconds': timing['estimated_seconds'],
    'timing_rehearsed': False, 'leaderboard_source': csv_url,
    'previous_presentation_and_plain_speech_unchanged': True,
    'previous_docx_mtime': (OLD / 'DAMDID_2026_Текст_выступления_RU.docx').stat().st_mtime,
    'sha256': {p.name: sha(p) for p in [deck, pdf, docx, txt]},
}
(BUILD / 'delivery-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
