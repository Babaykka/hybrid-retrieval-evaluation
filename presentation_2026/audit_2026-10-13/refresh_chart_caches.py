"""Remove floating-point serialization noise from PowerPoint chart caches."""
import io
from copy import copy
import posixpath
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E
from openpyxl.utils.cell import range_boundaries, get_column_letter

B = Path(__file__).parent
NS = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def resolve(part, target):
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


count = 0
with ZipFile(B / 'candidate.pptx') as src, ZipFile(B / 'candidate_refreshed.pptx', 'w', ZIP_DEFLATED) as dst:
    for info in src.infolist():
        data = src.read(info.filename)
        if info.filename.startswith('ppt/charts/chart') and info.filename.endswith('.xml'):
            chart = E.fromstring(data)
            relpath = posixpath.join(posixpath.dirname(info.filename), '_rels', posixpath.basename(info.filename) + '.rels')
            rels = {r.get('Id'): resolve(info.filename, r.get('Target')) for r in E.fromstring(src.read(relpath))}
            rid = chart.find('c:externalData', NS).get('{' + NS['r'] + '}id')
            with ZipFile(io.BytesIO(src.read(rels[rid]))) as wb:
                wr = {r.get('Id'): resolve('xl/workbook.xml', r.get('Target')) for r in E.fromstring(wb.read('xl/_rels/workbook.xml.rels'))}
                sheets = {s.get('name'): wr[s.get('{' + NS['r'] + '}id')] for s in E.fromstring(wb.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS)}
                for ref in chart.findall('.//c:numRef', NS):
                    sheet, cell_range = ref.findtext('c:f', namespaces=NS).rsplit('!', 1)
                    sheet = sheet.strip("'").replace("''", "'")
                    cells = {c.get('r'): c.findtext('s:v', namespaces=NS) for c in E.fromstring(wb.read(sheets[sheet])).findall('.//s:c', NS)}
                    c1, r1, c2, r2 = range_boundaries(cell_range.replace('$', ''))
                    values = [cells[get_column_letter(c) + str(r)] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
                    for point in ref.findall('c:numCache/c:pt', NS):
                        node = point.find('c:v', NS)
                        value = values[int(point.get('idx'))]
                        assert abs(float(node.text) - float(value)) < 1e-12
                        if node.text != value:
                            node.text = value
                            count += 1
            data = E.tostring(chart, xml_declaration=True, encoding='UTF-8', standalone=True)
        dst.writestr(copy(info), data)
print('Cache values refreshed from unchanged workbooks:', count)
