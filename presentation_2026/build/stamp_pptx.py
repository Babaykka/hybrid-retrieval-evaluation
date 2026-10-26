"""Set scholarly metadata and explicit straight-line chart interpolation."""
import sys
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET

source = Path(sys.argv[1])
target = source.with_name(source.stem + '-stamped.pptx')
ns = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
}
with ZipFile(source) as zin, ZipFile(target, 'w') as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'docProps/core.xml':
            root = ET.fromstring(data)
            properties = {
                'dc:creator': '',
                'cp:lastModifiedBy': '',
                'dc:title': 'Deep Re-annotation and Controlled Candidate Pools for Re-evaluating Ranking Models on MS MARCO',
                'dc:subject': 'DAMDID 2026 conference presentation',
                'dc:language': 'en-US',
            }
            for key, value in properties.items():
                prefix, local = key.split(':')
                tag = f'{{{ns[prefix]}}}{local}'
                element = root.find(tag)
                if element is None:
                    element = ET.SubElement(root, tag)
                element.text = value
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        elif item.filename.endswith('.xml') and '/charts/' in item.filename:
            root = ET.fromstring(data)
            for series in root.xpath('//c:scatterChart/c:ser', namespaces=ns):
                smooth = series.find(f'{{{ns["c"]}}}smooth')
                if smooth is None:
                    smooth = ET.SubElement(series, f'{{{ns["c"]}}}smooth')
                smooth.set('val', '0')
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        zout.writestr(item, data)
print(target)
