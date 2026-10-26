from pathlib import Path
from copy import deepcopy
import hashlib
import json
import math
from datetime import datetime, timezone
import re
import tarfile
import zipfile
import numpy as np
from lxml import etree as E
from docx import Document
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'presentation_2026/review_2026-10-12/build'
OUT = ROOT / 'DAMDID_2026_После_рецензии'
OUT.mkdir(exist_ok=True)
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
ORDER = list(range(1, 11)) + [21, 22, 11, 23, 12, 13, 14, 15, 24, 25, 26, 16, 17, 18, 19, 20]
SOURCES = {
 'study': '__REMOVED_IDENTIFIER__, G. __REMOVED_IDENTIFIER__, N. __REMOVED_IDENTIFIER__. Deep Re-annotation and Controlled Candidate Pools for Re-evaluating Ranking Models on MS MARCO. DAMDID 2026. Результаты экспериментов в контролируемых пулах.',
 'dev': 'MS MARCO Passage Ranking v1. https://ir-datasets.com/msmarco-passage.html#msmarco-passage/dev\nАрхив запросов: https://msmarco.z22.web.core.windows.net/msmarcoranking/queries.tar.gz',
 'small': 'MS MARCO Passage Ranking dev/small. https://ir-datasets.com/msmarco-passage.html#msmarco-passage/dev/small',
 'rrf': 'Cormack, Clarke, Büttcher. Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. SIGIR 2009. https://doi.org/10.1145/1571941.1572114',
 'minilm': 'Wang et al. MiniLM. 2020. https://arxiv.org/abs/2002.10957\nИсходная модель: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2',
 'retrieval': 'BM25: https://doi.org/10.1561/1500000019\nE5: https://arxiv.org/abs/2212.03533\nМодель E5: https://huggingface.co/intfloat/e5-small-v2\nМодель BGE: https://huggingface.co/BAAI/bge-small-en-v1.5',
 'datasets': 'MS MARCO: https://arxiv.org/abs/1611.09268\nNatural Questions: https://aclanthology.org/Q19-1026/\nBEIR: https://arxiv.org/abs/2104.08663',
 'leaderboard': 'Историческая таблица MS MARCO Passage Ranking, срез 30 ноября 2022 года. https://github.com/microsoft/MSMARCO-Passage-Ranking-Submissions/blob/abb44144f563e7972d5131f5d6acc2092877964c/leaderboard/leaderboard.csv\nПоказаны четыре лучшие именованные заявки по eval среди full ranking. Анонимные заявки не включены. Значения округлены как в официальном CSV. https://microsoft.github.io/msmarco/Submission.html',
}

# Establish the dataset provenance using identifiers rather than matching counts.
with tarfile.open(B / 'queries.tar.gz') as t:
    member = next(x for x in t.getnames() if x.endswith('queries.dev.tsv'))
    dev = {int(x.split(b'\t', 1)[0]) for x in t.extractfile(member)}
full = set(map(int, np.load(ROOT / 'revision_2026/cache/fullset_query_ids.npy')))
manual = set(map(int, np.load(ROOT / 'revision_2026/results/manual_per_query.npz')['qids']))
with zipfile.ZipFile(ROOT / 'phd2.zip') as z:
    lines = z.read('phd2/msmarco/qrels/dev.tsv').decode().splitlines()
    assert lines[0] == 'query-id\tcorpus-id\tscore'
    small = {int(x.split('\t')[0]) for x in lines[1:]}
assert dev == full and manual <= small <= dev
audit = {'official_dev_queries': len(dev), 'local_full_queries': len(full),
         'symmetric_difference': len(dev ^ full), 'dev_small_queries': len(small),
         'manual_queries': len(manual), 'manual_outside_dev_small': len(manual - small),
         'official_queries_archive_md5': hashlib.md5((B / 'queries.tar.gz').read_bytes()).hexdigest()}
(B / 'dataset_provenance.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))

source_doc = Document(B / 'source/speech.docx')
old = {}
section = None
for para in source_doc.paragraphs:
    if para.style.name == 'Heading 1':
        section = int(re.search(r'Слайд (\d+)', para.text)[1])
        old[section] = []
    elif section and para.style.name == 'Normal' and para.text:
        old[section].append(para.text)

speech = {i: list(v) for i, v in old.items()}
speech[5] = [
 'Сначала рассмотрим человеческие оценки. В англоязычном корпусе MS MARCO около 8,84 миллиона фрагментов. Стандартная оценочная подвыборка dev/small содержит 6 980 запросов и 7 437 исходных положительных пар. Пара здесь означает один запрос и один фрагмент, связанный с ним оценкой релевантности.',
 'Из dev/small взяты 1 179 запросов для расширенной ручной разметки. Для них оценены 33 667 различных пар. Под углублённой доразметкой мы понимаем оценку нескольких кандидатов для каждого запроса внутри заданного пула. Речь идёт об охвате разметки, а не о глубине нейросети или полной разметке всего корпуса.'
]
speech[9][0] = 'Человеческие оценки позволили измерить эффект доразметки. Но проверять вручную гораздо более крупные пулы дорого. Поэтому мы дообучили компактный кросс-энкодер MiniLM на этих оценках и используем его как модель-судью. Он предсказывает релевантность пары из запроса и фрагмента. Такие предсказания называем псевдометками, чтобы отличать их от человеческих оценок.'
speech[9][2] = 'Ручная разметка нужна и для дообучения судьи, и для проверки его ошибок на отложенных запросах. Поисковые модели при этом сохраняют свою роль: они находят кандидатов, которых затем оценивает судья. Сначала покажу, насколько его предсказания согласуются с человеческими оценками.'
speech[10] = [
 'Всю ручную подвыборку разделили по запросам: 825 для дообучения, 177 для валидации и 177 для теста. Все пары одного запроса остаются в одной части. Это наше внутреннее разбиение для судьи внутри dev/small, а не исходные train и test всего MS MARCO.',
 'На валидационной части выбрали порог минус 0,2187. Если выходной балл судьи не ниже этого порога, присваиваем положительную псевдометку. Отрицательный порог допустим: модель выдаёт балл, а не вероятность. После выбора порога его фиксируем.',
 'На тестовых 177 запросах и 5 002 парах площадь под ROC-кривой составляет 0,907, а F1 при выбранном пороге равна 0,875. Точность составляет 0,851, полнота 0,902. Это согласие с человеческими оценками в ручных пулах. Проверка не гарантирует такого же качества на более глубоких пулах.'
]
speech[21] = [
 'Теперь переходим к масштабному эксперименту. Число 101 093 имеет конкретное происхождение: столько запросов содержит полная dev-часть MS MARCO Passage Ranking, файл queries.dev.tsv. Набор идентификаторов в наших результатах полностью совпадает с этим файлом. Это количество запросов, а не ответов или пар.',
 'Важно различать полную dev-часть из 101 093 запросов и её стандартную подвыборку dev/small из 6 980. Ручная разметка охватывает 1 179 запросов из dev/small. Для полной dev-части заранее получили поисковые выдачи, а теперь применяем обученного судью к найденным кандидатам. Сам судья не обучается на всех 101 тысяче запросов.'
]
speech[22] = [
 'Пул для судьи строится так. Для каждого запроса берём первые K результатов BM25, E5 и BGE, объединяем их и удаляем повторяющиеся фрагменты. Затем судья получает каждую пару из запроса и кандидата и присваивает ей псевдометку.',
 'K называют глубиной пула: это число результатов от одного метода до объединения. Например, при K, равном десяти, три списка дают не более тридцати уникальных кандидатов. После удаления повторов их обычно меньше. Мы проверяем K от десяти до двухсот. Модель и порог минус 0,2187 остаются прежними, меняется только набор оцениваемых кандидатов.'
]
speech[11] = [old[11][1], old[11][2]]
speech[23] = [
 'Зачем здесь RRF? Лексический поиск BM25 и векторные модели E5 и BGE могут находить разные полезные фрагменты. Мы хотим проверить, помогает ли простое объединение их выдач, и насколько ответ зависит от полноты разметки.',
 'RRF означает слияние по обратным рангам. Каждый источник добавляет документу величину один, делённый на шестьдесят плюс его место в списке. Складываем эти величины для BM25, E5 и BGE и сортируем документы по сумме. У источников одинаковый вес. Если документа нет в используемом списке, вклад этого источника равен нулю.',
 'Поэтому RRF объединяет позиции, а не усредняет исходные баллы трёх моделей. Это удобно, потому что их баллы имеют разные шкалы. На выходе получаем один итоговый ранжированный список. Оценки судьи не участвуют в его построении, они нужны для последующего сравнения качества.'
]
speech[15] = old[15][:-1]
speech[24] = ['На слайде приведены основные работы и ссылки на использованные методы и наборы данных.']
speech[25] = ['Спасибо за внимание! Буду рад вашим вопросам.']

qa = [
 ('Почему именно 101 093 запроса, а не 140 тысяч?',
  'Это полный набор запросов dev в MS MARCO Passage Ranking v1, файл queries.dev.tsv. Совпадает не только количество: множество идентификаторов в результатах эксперимента полностью совпадает с официальным файлом. Поэтому говорить об отборе 101 тысячи из 140 тысяч оснований нет. Число около 140 тысяч к этой части данных не относится.', 21),
 ('101 093, 6 980 и 1 179: как эти числа связаны?',
  '101 093 запроса входят в полную dev-часть. dev/small содержит 6 980 из них и исходные оценки релевантности для стандартного оценивания. Ручная подвыборка содержит 1 179 запросов из dev/small. Один запрос может иметь много кандидатов, поэтому в ручной части 33 667 пар. Размер корпуса другой: 8 841 823 фрагмента.', 21),
 ('Мы учились и тестировались на dev MS MARCO?',
  'Дообучение нашего судьи и его локальная проверка выполнялись на ручной подвыборке из dev/small. Мы отдельно разделили её на 825 обучающих, 177 валидационных и 177 тестовых запросов. Это внутренние части эксперимента, а не официальный закрытый test MS MARCO. Исходный MiniLM уже был предварительно обучен; проверка исключает пересечение запросов в нашем дообучении, но сама по себе не доказывает отсутствие пересечений с его предобучением.', 23),
 ('Почему для ручной разметки выбраны именно 1 179 запросов?',
  'Это объём подготовленной ручной подвыборки, на которой выполнен эксперимент. Её принадлежность dev/small проверена по идентификаторам. Мы не рассматриваем её как случайную или репрезентативную выборку из всего MS MARCO. Выводы ручного эксперимента относятся к этой подвыборке и её кандидатным пулам.', 21),
 ('Что видел человек и что получает модель-судья?',
  'Человек видел запрос, оцениваемый фрагмент и известный релевантный ответ. Подготовка ручных кандидатов также использовала сходство E5 с этим ответом. Судья получает только тексты запроса и кандидата. Он не получает известного ответа, позиций, баллов BM25, E5 или BGE и заранее рассчитанных эмбеддингов. Добавление эталонного ответа ко входу судьи предложено как следующий эксперимент.', 26),
 ('Судья может быть слабее поисковых моделей. Зачем тогда он нужен?',
  'Судья нужен как доступный способ получить много дополнительных оценок и исследовать зависимость метрик от охвата. Он не заменяет поисковые системы и не считается безошибочным эталоном. BM25, E5 и BGE по-прежнему находят и ранжируют кандидатов. На ручных данных их сравнение опирается на человеческие оценки. Масштабные выводы с MiniLM условны и требуют проверки более сильными судьями и независимой ручной разметкой.', 23),
 ('Почему выбран MiniLM? Сравнивали ли другие cross-encoder?',
  'Это компактная исходная модель cross-encoder/ms-marco-MiniLM-L6-v2, пригодная для оценки большого числа пар. В представленном эксперименте её дообучили на ручных оценках. Сравнения нескольких судей и модели со входом «запрос, эталонный ответ, кандидат» пока не выполнены. Результаты таких сравнений не заявляются.', 26),
 ('Почему порог отрицательный и как его выбрали?',
  'Используется ненормированный выходной балл модели. Его шкала допускает отрицательные числа и не совпадает со шкалой вероятностей от нуля до единицы. Порог −0,2187178284 выбрали на 177 валидационных запросах и затем не меняли ни для теста, ни для разных K. На слайдах значение округлено до −0,2187. Тестовая F1 при этом пороге равна 0,875.', 23),
 ('Насколько часто судья ошибается?',
  'На 5 002 тестовых парах получены 2 882 верных положительных и 1 300 верных отрицательных решения, 506 ложноположительных и 314 ложноотрицательных. Точность 0,851 означает, что около 85% положительных предсказаний совпали с целевыми ручными метками на этом тесте. Эти доли нельзя автоматически переносить на все более глубокие пулы.', 23),
 ('Что такое K и чем оно отличается от L?',
  'K определяет, сколько результатов от каждой системы попадает в пул разметки. L определяет, сколько результатов от каждой системы поступает на слияние RRF. В первом сравнении L равно K, поэтому меняются и пул, и итоговое ранжирование. В контрольном сравнении L всегда равно 200: выдача фиксирована, меняется только пул с оценками. Повторяющиеся кандидаты учитываются один раз.', 24),
 ('У каждого из 101 093 запросов есть все три поисковых списка?',
  'Для E5 и BGE сохранены выдачи для всех 101 093 запросов. У BM25 отсутствуют списки для трёх запросов, а некоторые списки короче заданной глубины. Пулы строятся из доступных результатов. Для отсутствующего документа вклад соответствующего источника в RRF равен нулю. Число 101 093 описывает весь набор запросов, а не гарантию трёх полных списков у каждого.', 21),
 ('RRF усредняет предсказания моделей или ответы судьи?',
  'Нет. RRF суммирует величины, зависящие от места документа в списках BM25, E5 и BGE: 1/(60 + место). Веса источников одинаковы. Сырые поисковые баллы и оценки судьи в формулу не входят. Например, первое место у любого источника даёт вклад 1/61. Судья используется отдельно для оценки полученного списка.', 24),
 ('Если NDCG выросла, значит поиск стал лучше?',
  'В ручном сравнении поисковая выдача не менялась. Изменились метки, по которым мы её оцениваем: ранее неоценённые полезные ответы стали давать вклад в метрику. Поэтому выросла измеренная оценка качества, а не возможности самой поисковой модели. NDCG@10 учитывает релевантность в первой десятке с большим весом верхних позиций и нормирует её относительно идеальной выдачи.', 22),
 ('Ручные запросы входят в масштабный эксперимент. Это утечка?',
  'Полная dev-часть действительно включает ручные запросы, в том числе использованные для дообучения судьи. Поэтому все 101 093 запроса нельзя называть независимым тестом судьи. Мы отдельно исключили все 1 179 ручных запросов: осталось 99 914. Знаки различий RRF и E5 сохранились на проверенных глубинах. Это проверка устойчивости сравнения, а не замена независимой человеческой оценки глубоких пулов.', 25),
 ('Значит, на каждый запрос есть 17 или 129 правильных ответов?',
  '17,47 относится к среднему числу положительных человеческих оценок внутри ручных пулов. 128,6 относится к положительным предсказаниям одного судьи при K = 200 на полной dev-части. Пулы целенаправленно отобраны поисковыми методами. Ни одно число не оценивает полное количество релевантных ответов во всём корпусе.', 24),
 ('Какие выводы можно переносить на другие данные?',
  'Эксперимент показывает, что неполные оценки и выбранный пул могут существенно влиять на измеряемое качество. Конкретные численные эффекты получены на англоязычных пулах MS MARCO. Их перенос на другие языки, предметные области и поисковые сервисы нужно проверять отдельно.', 25),
]

backup_notes = {
 26: qa[0][1] + '\n\n' + qa[1][1] + '\n\n' + qa[2][1] + '\n\n' + qa[3][1] + '\n\n' + qa[10][1],
 16: qa[12][1], 17: qa[7][1] + '\n\n' + qa[8][1],
 18: qa[9][1] + '\n\n' + qa[11][1] + '\n\n' + qa[14][1],
 19: qa[13][1] + '\n\n' + qa[15][1], 20: qa[4][1] + '\n\n' + qa[5][1] + '\n\n' + qa[6][1],
}
duration = [5 * math.ceil((sum(len(p.split()) for p in speech[k]) / 125 * 60 + 3) / 5) for k in ORDER[:20]]

with zipfile.ZipFile(B / 'source/presentation.pptx') as z:
    files = {name: z.read(name) for name in z.namelist()}
with zipfile.ZipFile(B / 'additions.pptx') as z:
    additions = {name: z.read(name) for name in z.namelist()}

def xml(data): return E.fromstring(data)
def data(el): return E.tostring(el, xml_declaration=True, encoding='UTF-8', standalone=True)
def relation(rid, kind, target, external=False):
    el = E.Element(f'{{{REL}}}Relationship', Id=rid, Type=NS['r'] + '/' + kind, Target=target)
    if external: el.set('TargetMode', 'External')
    return el

files['ppt/slides/slide5.xml'] = additions['ppt/slides/slide1.xml']
for actual, donor in [(21,2),(22,3),(23,4),(24,5),(25,6),(26,7)]:
    files[f'ppt/slides/slide{actual}.xml'] = additions[f'ppt/slides/slide{donor}.xml']
    rels = E.Element(f'{{{REL}}}Relationships', nsmap={None: REL})
    rels.append(relation('rLayout', 'slideLayout', '/ppt/slideLayouts/slideLayout1.xml'))
    rels.append(relation('rNotes', 'notesSlide', f'/ppt/notesSlides/notesSlide{actual}.xml'))
    files[f'ppt/slides/_rels/slide{actual}.xml.rels'] = data(rels)
    rels = E.Element(f'{{{REL}}}Relationships', nsmap={None: REL})
    rels.append(relation('rSlide', 'slide', f'/ppt/slides/slide{actual}.xml'))
    rels.append(relation('rMaster', 'notesMaster', '/ppt/notesMasters/notesMaster1.xml'))
    files[f'ppt/notesSlides/_rels/notesSlide{actual}.xml.rels'] = data(rels)

def replace_text(tree, before, after):
    found = 0
    for t in tree.findall('.//a:t', NS):
        if before in (t.text or ''):
            t.text = t.text.replace(before, after)
            found += 1
    assert found, before

t = xml(files['ppt/slides/slide10.xml'])
# Replace the point label in place, leaving the editable ROC chart unchanged.
labels = [e for e in t.findall('.//a:t', NS) if 'Точка:' in (e.text or '')]
assert len(labels) == 1
labels[0].text = 'Порог −0,2187 выбран на валидационных запросах'
files['ppt/slides/slide10.xml'] = data(t)

titles = []
for num, actual in enumerate(ORDER, 1):
    tree = xml(files[f'ppt/slides/slide{actual}.xml'])
    # Only the bottom-right page marker may be renumbered, never table values.
    for sp in tree.findall('.//p:sp', NS):
        offset = sp.find('p:spPr/a:xfrm/a:off', NS)
        if offset is None or int(offset.get('y')) < 650 * 9525 or int(offset.get('x')) < 1050 * 9525:
            continue
        for el in sp.findall('.//a:t', NS):
            value = el.text or ''
            if re.fullmatch(r'\d{2}', value) or re.fullmatch(r'РЕЗЕРВ \d+', value):
                el.text = f'{num:02d}' if num <= 20 else f'РЕЗЕРВ {num - 20}'
    texts = [el.text for el in tree.findall('.//a:t', NS) if el.text]
    title = texts[0] if num not in [1,20] else ('Доразметка и контролируемые пулы кандидатов' if num == 1 else 'Спасибо за внимание')
    titles.append(title)
    if actual == 26:
        # Apply explicit native borders to match the supplied deck across renderers.
        for props in tree.findall('.//a:tcPr', NS):
            for child in list(props):
                if E.QName(child).localname in ['lnL','lnR','lnT','lnB']:
                    props.remove(child)
            for idx, side in enumerate(['lnL','lnR','lnT','lnB']):
                border = E.Element(f'{{{NS["a"]}}}{side}', w='7620' if side == 'lnB' else '0')
                if side == 'lnB':
                    fill = E.SubElement(border, f'{{{NS["a"]}}}solidFill')
                    E.SubElement(fill, f'{{{NS["a"]}}}srgbClr', val='D4E1E0')
                else:
                    E.SubElement(border, f'{{{NS["a"]}}}noFill')
                props.insert(idx, border)
    if actual == 24:
        rels = xml(files[f'ppt/slides/_rels/slide{actual}.xml.rels'])
        for i, tx in enumerate(tree.findall('.//a:t', NS)):
            val = tx.text or ''
            if re.match(r'(arxiv.org|aclanthology.org|doi.org|huggingface.co)', val):
                rid = f'rLink{i}'
                rels.append(relation(rid, 'hyperlink', 'https://' + val, True))
                run = tx.getparent()
                rp = run.find('a:rPr', NS)
                if rp is None: rp = E.Element(f'{{{NS["a"]}}}rPr'); run.insert(0, rp)
                E.SubElement(rp, f'{{{NS["a"]}}}hlinkClick', {f'{{{NS["r"]}}}id': rid})
        files[f'ppt/slides/_rels/slide{actual}.xml.rels'] = data(rels)
    files[f'ppt/slides/slide{actual}.xml'] = data(tree)

    notes = xml(files.get(f'ppt/notesSlides/notesSlide{actual}.xml', files['ppt/notesSlides/notesSlide5.xml']))
    body = notes.find('.//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]', NS) if False else None
    for sp in notes.findall('.//p:sp', NS):
        ph = sp.find('p:nvSpPr/p:nvPr/p:ph', NS)
        if ph is not None and ph.get('type') == 'body': body = sp.find('p:txBody', NS)
    assert body is not None
    for child in list(body):
        if child.tag == f'{{{NS["a"]}}}p': body.remove(child)
    paragraphs = speech[actual] if num <= 20 else backup_notes[actual].split('\n\n')
    keys = ['study']
    if actual in [5,21,26]: keys += ['dev','small']
    if actual in [6,8,22,23]: keys += ['retrieval']
    if actual in [8,12,13,18,23]: keys += ['rrf']
    if actual in [9,10,17,20]: keys += ['minilm']
    if actual in [2,24]: keys += ['datasets']
    if actual == 3:
        original_notes = xml(files['ppt/notesSlides/notesSlide3.xml'])
        raw = '\n'.join(original_notes.findall('.//a:t', NS)[i].text or '' for i in range(len(original_notes.findall('.//a:t', NS))))
        urls = re.findall(r'https?://[^\s]+', raw)
        keys += ['leaderboard']
    if actual == 24: keys += ['retrieval','minilm','rrf','dev']
    for line in paragraphs + ['', 'Источники'] + [SOURCES[k] for k in dict.fromkeys(keys)]:
        for part in line.split('\n'):
            para = E.SubElement(body, f'{{{NS["a"]}}}p')
            run = E.SubElement(para, f'{{{NS["a"]}}}r')
            E.SubElement(run, f'{{{NS["a"]}}}t').text = part
    files[f'ppt/notesSlides/notesSlide{actual}.xml'] = data(notes)

presentation = xml(files['ppt/presentation.xml'])
rels = xml(files['ppt/_rels/presentation.xml.rels'])
slid_rels = {int(re.search(r'slide(\d+)\.xml', r.get('Target'))[1]): r.get('Id') for r in rels if r.get('Type').endswith('/slide')}
ids = presentation.find('p:sldIdLst', NS)
max_id = max(int(x.get('id')) for x in ids)
for actual in range(21,27):
    rid = f'rAddedSlide{actual}'
    rels.append(relation(rid, 'slide', f'/ppt/slides/slide{actual}.xml'))
    slid_rels[actual] = rid
for child in list(ids): ids.remove(child)
for i, actual in enumerate(ORDER):
    E.SubElement(ids, f'{{{NS["p"]}}}sldId', id=str(max_id + i + 1), attrib={f'{{{NS["r"]}}}id': slid_rels[actual]})
files['ppt/presentation.xml'] = data(presentation)
files['ppt/_rels/presentation.xml.rels'] = data(rels)
types = xml(files['[Content_Types].xml'])
for actual in range(21,27):
    for folder,base,ctype in [('slides','slide','slide'),('notesSlides','notesSlide','notesSlide')]:
        E.SubElement(types, f'{{{CT}}}Override', PartName=f'/ppt/{folder}/{base}{actual}.xml', ContentType=f'application/vnd.openxmlformats-officedocument.presentationml.{ctype}+xml')
files['[Content_Types].xml'] = data(types)
app = xml(files['docProps/app.xml'])
for el in app:
    if E.QName(el).localname == 'Slides': el.text = '26'
    if E.QName(el).localname == 'Notes': el.text = '26'
files['docProps/app.xml'] = data(app)
core = xml(files['docProps/core.xml'])
for el in core:
    if E.QName(el).localname == 'lastModifiedBy': el.text = ''
    if E.QName(el).localname == 'modified': el.text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
files['docProps/core.xml'] = data(core)
with zipfile.ZipFile(B / 'candidate.pptx', 'w', zipfile.ZIP_DEFLATED) as z:
    for name, payload in files.items(): z.writestr(name, payload)

# Keep the supplied document's page setup and text styles, replace its aligned script.
doc = source_doc
body = doc._element.body
for child in list(body):
    if E.QName(child).localname != 'sectPr': body.remove(child)
for name in ['Title','Heading 1','Heading 2','Subtitle','Normal']:
    doc.styles[name].font.name = 'Arial'
    doc.styles[name].font.color.rgb = RGBColor(0,0,0)
doc.styles['Title'].font.size = Pt(22)
doc.styles['Heading 1'].font.size = Pt(15)
doc.styles['Heading 2'].font.size = Pt(12)
doc.styles['Heading 1'].paragraph_format.keep_with_next = True
doc.styles['Heading 2'].paragraph_format.keep_with_next = True
doc.styles['Heading 2'].paragraph_format.space_before = Pt(8)
doc.styles['Heading 2'].paragraph_format.space_after = Pt(4)
doc.styles['Subtitle'].paragraph_format.keep_with_next = True
doc.styles['Subtitle'].paragraph_format.space_before = Pt(0)
doc.styles['Subtitle'].paragraph_format.space_after = Pt(7)
doc.styles['Normal'].font.size = Pt(12)
doc.styles['Normal'].paragraph_format.line_spacing = 1.1
doc.styles['Normal'].paragraph_format.space_after = Pt(7)
doc.add_paragraph('Текст выступления DAMDID 2026', 'Title')
doc.add_paragraph('__REMOVED_IDENTIFIER__\nДоразметка и контролируемые пулы кандидатов', 'Subtitle')
doc.add_paragraph('Основной доклад: слайды 1–20, ориентировочно 16–18 минут. Резервные слайды 21–26 предназначены для ответов на вопросы.')
elapsed = 0
for num, actual in enumerate(ORDER[:20],1):
    doc.add_paragraph(f'Слайд {num}  {titles[num-1]}', 'Heading 1')
    end = elapsed + duration[num-1]
    tm = lambda t: f'{t//60}:{t%60:02d}'
    doc.add_paragraph(f'{tm(elapsed)}–{tm(end)}', 'Subtitle')
    elapsed = end
    for line in speech[actual]: doc.add_paragraph(line)
doc.add_page_break()
doc.add_paragraph('Ответы на возможные вопросы', 'Title')
doc.add_paragraph('Развёрнутые пояснения к данным, модели-судье и сравнению поисковых систем. Под каждым вопросом указан номер соответствующего резервного слайда в презентации.')
for i, (question, answer, slide_no) in enumerate(qa,1):
    doc.add_paragraph(question, 'Heading 2')
    p = doc.add_paragraph(f'Резервный слайд {slide_no}', 'Subtitle')
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(answer)
doc.core_properties.author = ''
doc.core_properties.last_modified_by = ''
doc.core_properties.title = 'Текст выступления DAMDID 2026'
doc.core_properties.subject = 'Доразметка MS MARCO и контролируемые пулы кандидатов'
doc.save(OUT / 'DAMDID_2026_Текст_выступления_RU.docx')
manifest = [{'slide':i, 'source_part':actual, 'title':titles[i-1], 'speech':speech.get(actual,[]), 'reserve':i>20} for i,actual in enumerate(ORDER,1)]
(B / 'slide_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'slides':len(ORDER),'main_slides':20,'speech_words':sum(len(p.split()) for k in ORDER[:20] for p in speech[k]),'speech_seconds':sum(duration),'qa_questions':len(qa),'dataset':audit},ensure_ascii=False,indent=2))
