"""Apply narrow language fixes without changing the numerical evidence."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path(__file__).parent
SOURCE = ROOT / 'DAMDID_2026_Уточненная_версия 2'
OUT = ROOT / 'DAMDID_2026_Проверено_13-10'
PPT = 'DAMDID_2026_Презентация_RU.pptx'
DOC = 'DAMDID_2026_Текст_выступления_RU.docx'
OUT.mkdir(exist_ok=True)

replacements = {
    'не достаточны, чтобы считать системы равноценными': 'недостаточны, чтобы считать системы равноценными',
    '2\u00a0882 верных положительных и 1\u00a0300 верных отрицательных решения, 506 ложноположительных и 314 ложноотрицательных.': '2\u00a0882 верных положительных решения и 1\u00a0300 верных отрицательных решений. Ошибок двух типов соответственно 506 и 314: ложноположительные и ложноотрицательные.',
    'Сравнивали ли другие cross-encoder?': 'Сравнивали ли другие кросс-энкодеры?',
    'Поэтому выросла измеренная оценка качества, а не возможности самой поисковой модели.': 'Поэтому выросла оценка качества, а возможности самой поисковой модели остались прежними.',
}
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
counts = {}
hashes = {}
for name, dest in [(PPT, BUILD / 'candidate.pptx'), (DOC, OUT / DOC)]:
    data = (SOURCE / name).read_bytes()
    hashes[name] = hashlib.sha256(data).hexdigest()
    changed = []
    with ZipFile(SOURCE / name) as src, ZipFile(dest, 'x', ZIP_DEFLATED) as dst:
        for info in src.infolist():
            value = src.read(info.filename)
            if info.filename.endswith('.xml'):
                tree = E.fromstring(value)
                dirty = False
                if info.filename == 'docProps/core.xml':
                    for node in tree:
                        if E.QName(node).localname == 'lastModifiedBy':
                            node.text = ''
                            dirty = True
                paragraphs = tree.xpath('//a:p | //w:p', namespaces=ns)
                for p in paragraphs:
                    texts = p.xpath('.//a:t | .//w:t', namespaces=ns)
                    original = ''.join(t.text or '' for t in texts)
                    revised = original
                    for old, new in replacements.items():
                        if old in revised:
                            revised = revised.replace(old, new)
                            counts[old] = counts.get(old, 0) + 1
                    if revised != original:
                        texts[0].text = revised
                        for t in texts[1:]:
                            t.text = ''
                        dirty = True
                for node in tree.xpath('//a:t | //w:t', namespaces=ns):
                    if node.text and ('ё' in node.text or 'Ё' in node.text):
                        node.text = node.text.replace('ё', 'е').replace('Ё', 'Е')
                        dirty = True
                if dirty:
                    value = E.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
                    changed.append(info.filename)
            dst.writestr(info, value)
    print(name, 'changed parts:', changed)
assert all(counts.get(old, 0) >= 1 for old in replacements), counts
(BUILD / 'edits.json').write_text(json.dumps({'replacements': replacements, 'counts': counts, 'source_sha256': hashes}, ensure_ascii=False, indent=2))
