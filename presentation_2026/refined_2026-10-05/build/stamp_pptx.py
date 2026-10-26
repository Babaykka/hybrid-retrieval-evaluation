"""Set scholarly metadata and deterministic chart formatting."""
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET

source = Path(sys.argv[1])
target = source.with_name(source.stem + '-stamped.pptx')
ns = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}
def node(prefix, name, **attrs):
    return ET.Element(f'{{{ns[prefix]}}}{name}', **attrs)

def literal(values):
    result = node('c', 'numLit')
    ET.SubElement(result, f'{{{ns["c"]}}}formatCode').text = '0.00000000'
    result.append(node('c', 'ptCount', val=str(len(values))))
    for i, value in enumerate(values):
        pt = node('c', 'pt', idx=str(i))
        ET.SubElement(pt, f'{{{ns["c"]}}}v').text = format(value, 'f')
        result.append(pt)
    return result

def error_bars(values, bounds, fill, direction):
    bars = node('c', 'errBars')
    bars.extend([node('c', 'errDir', val=direction), node('c', 'errBarType', val='both'), node('c', 'errValType', val='cust'), node('c', 'noEndCap', val='0')])
    for name, offsets in [('plus', [hi-v for v, (lo, hi) in zip(values, bounds)]), ('minus', [v-lo for v, (lo, hi) in zip(values, bounds)])]:
        child = node('c', name)
        child.append(literal(offsets))
        bars.append(child)
    style = node('c', 'spPr')
    line = node('a', 'ln', w='22860')
    line.append(deepcopy(fill))
    style.append(line)
    bars.append(style)
    return bars

with ZipFile(source) as zin, ZipFile(target, 'w') as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'docProps/core.xml':
            root = ET.fromstring(data)
            for key, value in {
                'dc:creator': '',
                'cp:lastModifiedBy': '',
                'dc:title': 'Deep Re-annotation and Controlled Candidate Pools for Re-evaluating Ranking Models on MS MARCO',
                'dc:subject': 'Доклад на конференции DAMDID 2026',
                'dc:language': 'ru-RU',
            }.items():
                prefix, local = key.split(':')
                tag = f'{{{ns[prefix]}}}{local}'
                element = root.find(tag)
                if element is None:
                    element = ET.SubElement(root, tag)
                element.text = value
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        elif item.filename.endswith('.xml') and '/theme/' in item.filename:
            root = ET.fromstring(data)
            for element in root.iter():
                if element.get('name') == 'ChatGPT':
                    element.set('name', 'DAMDID 2026')
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        elif item.filename.endswith('.xml') and '/charts/' in item.filename:
            root = ET.fromstring(data)
            # Some Office renderers inherit a missing marker fill as transparent.
            for series in root.xpath('//c:scatterChart/c:ser', namespaces=ns):
                smooth = series.find(f'{{{ns["c"]}}}smooth')
                if smooth is None:
                    smooth = ET.SubElement(series, f'{{{ns["c"]}}}smooth')
                smooth.set('val', '0')
                marker = series.find('c:marker', ns)
                if marker is not None and marker.find('c:symbol', ns).get('val') != 'none':
                    old = marker.find('c:spPr', ns)
                    if old is not None:
                        marker.remove(old)
                    style = node('c', 'spPr')
                    fill = series.find('c:spPr/a:solidFill', ns)
                    if fill is not None:
                        style.append(deepcopy(fill))
                    outline = node('a', 'ln', w='0')
                    outline.append(node('a', 'noFill'))
                    style.append(outline)
                    marker.append(style)
            # Encode exact paired intervals as native custom error bars.
            for scatter in root.xpath('//c:scatterChart', namespaces=ns):
                items = list(scatter.findall('c:ser', ns))
                mean = next((s for s in items if (s.findtext('c:tx/c:v', namespaces=ns) or '').startswith('RRF minus E5')), None)
                intervals = [s for s in items if (s.findtext('c:tx/c:v', namespaces=ns) or '').startswith('95% paired CI at')]
                if mean is not None and intervals:
                    horizontal = mean.findtext('c:tx/c:v', namespaces=ns).endswith('(horizontal)')
                    coord = 'xVal' if horizontal else 'yVal'
                    ys = [Decimal(v) for v in mean.xpath(f'./c:{coord}/c:numLit/c:pt/c:v/text()', namespaces=ns)]
                    bounds = [[Decimal(v) for v in s.xpath(f'./c:{coord}/c:numLit/c:pt/c:v/text()', namespaces=ns)] for s in intervals]
                    assert len(ys) == len(bounds) == 5
                    bars = error_bars(ys, bounds, mean.find('c:spPr/a:solidFill', ns), 'x' if horizontal else 'y')
                    mean.insert(mean.index(mean.find('c:xVal', ns)), bars)
                    # Exact helper series preserve horizontal intervals in
                    # renderers that omit native X error bars during import.
                    if not horizontal:
                        for s in items:
                            label = s.findtext('c:tx/c:v', namespaces=ns) or ''
                            if label.startswith('95% paired CI at') or label.startswith('CI '):
                                scatter.remove(s)
                    for i, s in enumerate(scatter.findall('c:ser', ns)):
                        s.find('c:idx', ns).set('val', str(i))
                        s.find('c:order', ns).set('val', str(i))
                # LibreOffice pads short XY series with zero-valued points.
                # Repeating their last coordinate preserves their exact geometry.
                current = scatter.findall('c:ser', ns)
                lengths = [len(s.xpath('./c:yVal/c:numLit/c:pt', namespaces=ns)) for s in current]
                longest = max(lengths)
                for s, length in zip(current, lengths):
                    if 0 < length < longest:
                        for coords in s.xpath('./c:xVal/c:numLit | ./c:yVal/c:numLit', namespaces=ns):
                            last = coords.findall('c:pt', ns)[-1]
                            for idx in range(length, longest):
                                repeated = deepcopy(last)
                                repeated.set('idx', str(idx))
                                coords.append(repeated)
                            coords.find('c:ptCount', ns).set('val', str(longest))
            for axis in root.xpath('//c:catAx', namespaces=ns):
                tick = axis.find('c:tickLblPos', ns)
                if tick is None:
                    tick = node('c', 'tickLblPos')
                    axis.insert(axis.index(axis.find('c:spPr', ns)), tick)
                tick.set('val', 'low')
            for axis in root.xpath('//c:valAx', namespaces=ns):
                if axis.find('c:axPos', ns).get('val') == 'b':
                    tick = axis.find('c:tickLblPos', ns)
                    if tick is None:
                        tick = node('c', 'tickLblPos')
                        axis.insert(axis.index(axis.find('c:spPr', ns)), tick)
                    tick.set('val', 'low')
                if axis.find('c:axPos', ns).get('val') == 'l':
                    cross = axis.find('c:crosses', ns)
                    if cross is None:
                        cross = node('c', 'crosses')
                        axis.insert(axis.index(axis.find('c:crossAx', ns))+1, cross)
                    cross.set('val', 'min')
                for props in axis.xpath('./c:title//a:defRPr | ./c:title//a:rPr | ./c:title//a:endParaRPr', namespaces=ns):
                    props.set('sz', '1800')
                    props.set('b', '0')
                    for fill in props.findall('a:solidFill', ns):
                        props.remove(fill)
                    fill = node('a', 'solidFill')
                    fill.append(node('a', 'srgbClr', val='526970'))
                    props.insert(0, fill)
            for numfmt in root.xpath('//c:numFmt', namespaces=ns):
                numfmt.set('sourceLinked', '0')
            for label in root.xpath('//c:ser/c:tx/c:v', namespaces=ns):
                label.text = (label.text or '').replace('RRF minus E5', 'RRF минус E5').replace(' (horizontal)', ' по горизонтали').replace('Zero difference', 'Нулевая разность').replace('Pool depth', 'Глубина пула').replace('95% paired CI at', '95%-ный парный ДИ при').replace('CI upper cap at', 'Верхняя граница ДИ при').replace('CI lower cap at', 'Нижняя граница ДИ при')
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        elif item.filename.startswith('ppt/slides/slide') and item.filename.endswith('.xml'):
            root = ET.fromstring(data)
            for cell in root.xpath('//a:tcPr', namespaces=ns):
                for side in ['lnL', 'lnR', 'lnT', 'lnB']:
                    old = cell.find(f'a:{side}', ns)
                    if old is not None:
                        cell.remove(old)
                for i, side in enumerate(['lnL', 'lnR', 'lnT', 'lnB']):
                    line = node('a', side, w='7620' if side == 'lnB' else '0')
                    if side == 'lnB':
                        fill = node('a', 'solidFill')
                        fill.append(node('a', 'srgbClr', val='D4E1E0'))
                        line.append(fill)
                    else:
                        line.append(node('a', 'noFill'))
                    cell.insert(i, line)
            data = ET.tostring(root, xml_declaration=True, encoding='UTF-8')
        zout.writestr(item, data)
print(target)
