import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {ROOT,BUILD,OUT,SKILL,PY,FONT,C,pres,charts,tables,notes,m,f,d,fmt,util,txt,rule,slide,foot,nativeTable,axis,grid,series,chart,box,connect,exportDraft} from './layout.mjs';

const VERSION=process.env.DECK_VERSION||'v1';
const models=['bm25','e5','bge','rrf3'];
const labels=['BM25','E5','BGE','RRF (3)'];
const roc=JSON.parse(await fs.readFile(path.join(BUILD,'../reviews/test_roc.json'),'utf8'));
const jt=m.judge_rescored_split_metrics.test;
const ks=d.map(v=>v.k);
const src={
 paper:'__REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__ and __REMOVED_IDENTIFIER__. Deep Re-annotation and Controlled Candidate Pools for Re-evaluating Ranking Models on MS MARCO. DAMDID 2026. Pool-based evaluation.',
 manual:'Study results: revision_2026/results/manual_summary.json and manual_per_query.npz.',
 full:'Study results: revision_2026/results/fullset_summary.json and fullset_perquery.npz; fixed-input analysis in fullset_interpretation_en.tex.',
 marco:'Bajaj et al. (2016), MS MARCO: A Human Generated MAchine Reading COmprehension Dataset. https://arxiv.org/abs/1611.09268',
 retrieval:'Robertson and Zaragoza (2009), The Probabilistic Relevance Framework: BM25 and Beyond. E5: https://arxiv.org/abs/2212.03533. BGE: https://huggingface.co/BAAI/bge-small-en-v1.5',
 judge:'MiniLM cross-encoder: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2. Nogueira and Cho (2019): https://arxiv.org/abs/1901.04085',
 rrf:'Cormack, Clarke and Buttcher (2009), Reciprocal Rank Fusion outperforms Condorcet and Individual Rank Learning Methods. SIGIR, pp. 758-759.',
};
const allsrc=(...v)=>[src.paper,...v].join('\n');
const metric=(v,k)=>v.models[k].ndcg10_mean_all_queries;
function xy(s,values,{x=64,y=210,w=1120,h=390,min=0,max=1,unit=.2,format='0.0',legend=false,xmin=0,xmax=210,xunit=50,xformat='0',xlabel='Assessment pool depth K',ylabel,extra=[]}={}){
 const ch=chart(s,'scatter',{position:{left:x,top:y,width:w,height:h},hasLegend:legend,scatterOptions:{style:'lineWithMarkers'},series:[...values,...extra],xAxis:{...axis,min:xmin,max:xmax,majorUnit:xunit,numberFormatCode:xformat,majorGridlines:null,title:xlabel},yAxis:{...axis,min,max,majorUnit:unit,numberFormatCode:format,majorGridlines:grid,...(ylabel?{title:ylabel}:{})}});
 return ch;
}
function dotSeries(name,x,y,color,rest={}){return series(name,y,color,{xValues:x,marker:{symbol:'circle',size:8},...rest});}
function effectSeries(contrast,{color=C.coral,connectPoints=false}={}){
 const rows=f.paired_inference.all_queries.filter(v=>v.contrast===contrast);
 return [
  series('Zero difference',[0,0],C.gray,{xValues:[0,210],marker:{symbol:'none'},line:{fill:C.gray,width:1.4}}),
  ...rows.map(v=>series(`95% paired CI at K=${v.k}`,v.bootstrap_ci95,color,{xValues:[v.k,v.k],marker:{symbol:'none'},line:{fill:color,width:2.6}})),
  ...rows.flatMap(v=>v.bootstrap_ci95.map((bound,i)=>series(`CI ${i?'upper':'lower'} cap at K=${v.k}`,[bound,bound],color,{xValues:[v.k-1.4,v.k+1.4],marker:{symbol:'none'},line:{fill:color,width:1.8}}))),
  dotSeries('RRF minus E5',rows.map(v=>v.k),rows.map(v=>v.mean_delta),color,{marker:{symbol:'circle',size:3},line:{fill:connectPoints?color:'none',width:connectPoints?3:0}}),
 ];
}

// 1. Editable title over a restrained photographic background.
{
 const s=slide('',
 'Сегодня мы рассматриваем, как полнота оценок релевантности меняет оценку уже существующей поисковой выдачи. Наш вклад экспериментальный: сравнение фиксированных ранжирований до и после человеческой доразметки и отдельный анализ глубины пулов с автоматическим судьёй. Начнём с конкретного запроса, для которого исходная разметка не охватывает несколько релевантных ответов.',25,{dark:true,source:allsrc(src.marco,'Conference: https://damdid.unn.ru/overview/. Cover photograph is illustrative, not experimental evidence.')});
 s.images.add({blob:new Uint8Array(await fs.readFile(path.join(BUILD,'assets/cover.png'))),contentType:'image/png',alt:'Illustrative printed passage slips with relevance annotations on a graphite surface',fit:'cover',position:{left:0,top:0,width:1280,height:720}});
 txt(s,'DAMDID 2026',64,49,650,35,23,{color:C.mint,bold:true});
 txt(s,'Deep Re-annotation\nand Controlled\nCandidate Pools',64,131,830,230,62,{color:C.white,bold:true});
 txt(s,'Re-evaluating ranking models\non MS MARCO',64,395,790,85,34,{color:'#C9DDDA'});
 txt(s,'__REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__,\n__REMOVED_IDENTIFIER__',64,557,795,68,25,{color:C.white});
 txt(s,'__REMOVED_IDENTIFIER__',64,647,920,30,21,{color:'#B7CBCB'});
}
// 2. An actual pool example, not an invented ranked list.
{
 const s=slide('A relevant passage can receive zero gain',
 'Запрос 1086224 спрашивает, что вызывает повышение температуры кипения. Фрагмент про соль есть в исходных положительных оценках. Другой фрагмент объясняет повышение температуры кипения через нелетучее растворённое вещество. Человек также считает его релевантным, но в исходной разметке он отсутствует. Третий фрагмент сообщает температуру кипения ацетона и не отвечает на вопрос о причине. Тексты здесь сокращены, а идентификаторы сохранены. Это пример релевантности в конкретном пуле, а не утверждение о частоте подобных случаев во всём корпусе. Qrels — оценки релевантности пар «запрос-фрагмент». Unjudged означает отсутствие оценки, а не подтверждённую нерелевантность.',65,{source:allsrc(src.manual,'Actual query 1086224 and passages 7112148, 7399382, 987600 in the paper, Section 3.3. Shortened paraphrases.')});
 txt(s,'“what causes boiling point to increase”',64,185,1152,51,34,{color:C.teal,bold:true});
 nativeTable(s,[['Passage (shortened paraphrase)','Original qrels','Human judgment'],['7112148   Adding salt raises the boiling point.','Relevant','Relevant'],['7399382   A non-volatile solute raises\nthe boiling point.','Unjudged','Relevant'],['987600   The boiling temperature of acetone.','Unjudged','Not relevant']],[672,232,248],64,266,[56,78,102,78],{size:25,emphasis:[[2,0],[2,2]]});
 foot(s,'qrels: query relevance judgments. Unjudged passages receive zero gain.');
}
// 3. Clearly separate the two populations and evidence types.
{
 const s=slide('Human judgments and a larger pool experiment',
 'Мы работаем с английской коллекцией MS MARCO Passage Ranking: 8 841 823 коротких текстовых фрагмента. Первый этап охватывает 1179 запросов и 33667 различных пар запрос–фрагмент с ручными оценками. Второй использует модель-судью и 101093 запроса. Это разные основания для выводов: человеческие суждения и предсказания. Большой набор включает все ручные запросы; отдельная проверка чувствительности исключает это пересечение. Под deep re-annotation понимается увеличение покрытия оценок внутри заданного пула. Термин не означает глубину сети или исчерпывающую разметку корпуса.',45,{source:allsrc(src.manual,src.full,src.marco)});
 txt(s,'English MS MARCO',64,182,900,40,30,{color:C.muted});
 txt(s,'8.84 million passages',64,230,1000,54,42,{bold:true});
 rule(s,64,317,1152);
 txt(s,'Human judgments',64,353,505,42,31,{color:C.teal,bold:true});
 txt(s,'1,179',64,414,510,87,76,{color:C.teal,bold:true});
 txt(s,'queries; 33,667 pairs',64,518,510,43,28);
 txt(s,'Judge predictions',704,353,512,42,31,{color:C.coral,bold:true});
 txt(s,'101,093',704,414,512,87,76,{color:C.coral,bold:true});
 txt(s,'queries; varying pool depths',704,518,512,43,28);
 foot(s,'“Deep” describes judgment coverage within selected candidate pools.');
}
// 4. Technical pooling workflow with orthogonal connections.
{
 const s=slide('Reference-assisted manual annotation',
 'Пулинг — известный подход: объединяем кандидатов нескольких источников и удаляем дубликаты, чтобы сосредоточить ручную оценку на вероятно полезных фрагментах. BM25 использует лексическое совпадение. E5 и BGE относятся к плотному поиску с отдельными векторными представлениями запроса и фрагмента. Каждая сохранённая выдача даёт десять результатов. Дополнительные каналы расширяют объединение, включая сходство E5 с уже известным релевантным ответом. Их точная архитектура полностью не установлена; не трактуем их как сопоставимые поисковые системы. Человек видит запрос, кандидата и известный релевантный ответ. Такая помощь может задавать интерпретацию запроса и обогащает пул. Средний размер пула 28,56 кандидата, максимум 63. Пул не является случайной выборкой корпуса.',65,{source:allsrc(src.manual,src.retrieval)});
 const retrieval=box(s,'BM25   E5   BGE\nTop 10 per retriever',64,198,325,120,{size:28});
 const aux=box(s,'Auxiliary candidates\nE5 reference similarity',64,409,325,128,{size:25,fill:'#FAEFE9'});
 const pooled=box(s,'Deduplicated\ncandidate pool',485,287,278,128,{size:30});
 const human=box(s,'Human\nassessment',861,287,295,128,{size:30,fill:'#E2F1ED'});
 connect(s,retrieval,pooled,{kind:'elbow'});connect(s,aux,pooled,{kind:'elbow',color:C.coral});connect(s,pooled,human);
 txt(s,'Query + candidate +\nknown relevant answer',861,470,327,84,27,{color:C.teal});
 txt(s,'28.56 candidates\nper query on average',479,467,300,86,25,{color:C.muted});
 foot(s,'Reference information supports candidate preparation and human assessment.');
}
// 5. Coverage is a property of the selected judgment set.
{
 const s=slide('More relevant passages within the same pools',
 'Сравним положительные оценки внутри одних и тех же ручных пулов. В пересечении с официальными qrels имеется 1243 положительные пары; после человеческой разметки — 20597. Среднее на запрос меняется с 1,05 до 17,47. Разность суммарных чисел составляет 19354 пары, но это не число всех релевантных ответов в коллекции. Четырнадцать исходно помеченных seed-пар отсутствуют в официальных qrels, поэтому нельзя подменять официальное число категорией seed. На следующем слайде мы не изменяем порядок выдачи поисковых систем и набор запросов. Меняется только набор оценок, по которому измеряется качество.',55,{source:allsrc(src.manual)});
 txt(s,'Mean passages judged relevant per query',64,187,1100,43,30,{color:C.muted});
 txt(s,fmt(m.density.official.mean,2),64,272,450,121,104,{color:C.gray,bold:true});
 txt(s,fmt(m.density.human.mean,2),704,272,500,121,104,{color:C.teal,bold:true});
 rule(s,64,428,1152);
 txt(s,'Original qrels',64,466,500,45,34,{bold:true});
 txt(s,'1,243 positive pairs',64,528,520,42,28,{color:C.muted});
 txt(s,'Extended human judgments',704,466,512,80,32,{bold:true});
 txt(s,'20,597 positive pairs',704,528,512,42,28,{color:C.muted});
 foot(s,'1,179 queries. Same candidate pools and retrieval rankings.');
}
// 6. Native chart: absolute scores stay on a 0–1 scale.
{
 const s=slide('Denser judgments change measured NDCG',
 'NDCG@10 — normalized discounted cumulative gain: релевантный фрагмент получает больший вес ближе к началу первой десятки, затем сумму нормируем на идеальную выдачу. Для данного запроса и набора меток идеальный знаменатель общий для всех систем и учитывает полный оценённый пул; при смене разметки он может меняться. Все 1179 запросов остаются в среднем, включая нулевые. На графике исходные и человеческие оценки для фиксированных ранжирований. У E5 среднее меняется с 0,488 до 0,879, парная разность 0,391 с 95% интервалом от 0,365 до 0,417. Все четыре средних изменения положительны, p < 0,001. Это изменение измеренной оценки, а не результат улучшения поисковой модели. Порядок систем сохраняется: E5, RRF, BGE, BM25. RRF объединяет ранги BM25, E5 и BGE; здесь входы top-10, константа 60. Добавление разметки не гарантирует рост NDCG для каждого запроса.',90,{source:allsrc(src.manual,src.rrf)});
 const rev=[...models].reverse();
 chart(s,'bar',{position:{left:64,top:178,width:1152,height:395},categories:[...labels].reverse(),series:[series('Original qrels',rev.map(k=>m.metrics[k].official),C.gray),series('Human judgments',rev.map(k=>m.metrics[k].human),C.teal)],barOptions:{direction:'bar',grouping:'clustered',gapWidth:120},xAxis:{...axis,majorGridlines:null},yAxis:{...axis,min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',majorGridlines:grid},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:FONT,fontSize:23,fill:C.ink}}});
 txt(s,'E5 paired change: +0.391   95% CI [0.365, 0.417]',64,594,1145,42,28,{color:C.teal,bold:true});
 foot(s,'Pooled NDCG@10. Same rankings; shared ideal denominator within each query and label set.');
}
// 7. Why the judge exists, and precisely which information it receives.
{
 const s=slide('A compact judge extends label coverage',
 'Ручная оценка позволяет проверить смысл доразметки, но оценивать миллионы пар вручную дорого. Поэтому во втором этапе используем компактный MiniLM как дообученную базовую модель для псевдоразметки. Это cross-encoder: запрос и фрагмент подаются совместно. В отличие от биэнкодеров E5 и BGE, модель не сравнивает независимо полученные эмбеддинги. На входе текст запроса и текст кандидата. Известного релевантного ответа, рангов и оценок других поисковых моделей у неё нет. Обучение использует ручные оценки, а порог выбирается на отдельной валидации. Выходы судьи расширяют покрытие оценивания, но остаются предсказаниями. В следующем эксперименте проверим, улучшает ли качество судьи добавление эталонного фрагмента из исходной разметки.',60,{source:allsrc(src.manual,src.judge)});
 const inp=box(s,'Query text\nCandidate passage',64,240,321,142,{size:30});
 const model=box(s,'MiniLM\ncross-encoder',483,240,321,142,{size:30,fill:'#E3F0ED'});
 const out=box(s,'Score\nPseudo-label',902,240,285,142,{size:30,fill:'#FAEFE9'});
 connect(s,inp,model);connect(s,model,out,{color:C.coral});
 txt(s,'Jointly scores the two texts',483,417,650,40,27,{color:C.teal});
 rule(s,64,492,1152);
 txt(s,'Inputs exclude the reference answer, ranks and retrieval scores.',64,535,1152,74,30);
 foot(s,'Pseudo-labels are model predictions. The original retrieval rankings remain available.');
}
// 8. Actual query-held-out ROC, with the operating point preserved.
{
 const s=slide('Judge agreement on held-out queries',
 'Запросы разделены между обучением, валидацией и тестом: 825, 177 и 177. Здесь 5002 пары только тестовых запросов. По вертикали ROC — доля верно выявленных положительных пар среди всех положительных; по горизонтали — доля ложноположительных среди всех отрицательных. Точки соответствуют разным порогам. Площадь под полной эмпирической кривой составляет 0,907, F1 при выбранном на валидации пороге — 0,875. Precision 0,851: доля подтверждённых положительных среди предсказанных. Recall 0,902: доля найденных положительных среди размеченных. F1 — их гармоническое среднее. AUC не является процентом правильных ответов или вероятностью релевантности. Унаследованное бинарное кодирование относит категории 1 и 2 к положительным, остальные к нулю. Тест включает шесть пар с метками, смысл которых не установлен и одну пару с пустым текстом; после их исключения AUC составляет 0,909 и F1 0,876. Основная оценка использует исходное бинарное кодирование меток. Это согласие на выбранных пулах, не независимая гарантия качества глубоких пулов.',65,{source:allsrc(src.manual,src.judge,'Empirical ROC from held-out saved scores. Plot: 80 retained observed vertices; reported AUC integrates the full curve. Provenance: presentation_2026/premium/reviews/test_roc.json.')});
 xy(s,[series('Chance',[0,1],C.rule,{xValues:[0,1],marker:{symbol:'none'},line:{fill:C.gray,width:1.3}}),dotSeries('MiniLM ROC',roc.points.map(v=>v.fpr),roc.points.map(v=>v.tpr),C.teal,{marker:{symbol:'none'},line:{fill:C.teal,width:3.5}}),dotSeries('Validation threshold',[roc.operating_point.fpr],[roc.operating_point.tpr],C.coral,{marker:{symbol:'circle',size:11},line:{fill:'none',width:0}})],{x:64,y:185,w:742,h:411,xmin:0,xmax:1,xunit:.2,xformat:'0.0',xlabel:'False positive rate',ylabel:'True positive rate'});
 txt(s,fmt(jt.auc),874,217,320,80,68,{color:C.teal,bold:true});
 txt(s,'ROC-AUC',874,303,320,40,29,{color:C.muted});
 txt(s,fmt(jt.f1),874,397,320,70,60,{color:C.ink,bold:true});
 txt(s,'F1 at validation threshold',874,475,320,72,26,{color:C.muted});
 txt(s,'Coral marker: validation-selected threshold',64,597,760,34,24,{color:C.coral});
 foot(s,'177 held-out manual-pool queries; 5,002 pairs. Deeper pools lack human validation.');
}
// 9. Counts, not corpus prevalence.
{
 const s=slide('Larger pools contain more predicted positives',
 'На большом наборе для каждого запроса объединяем первые K результатов BM25, E5 и BGE. K — длина каждой исходной выдачи, а не число уникальных кандидатов после удаления дубликатов. Используем одни и те же сохранённые оценки судьи и фиксированный порог. Средний пул растёт с 21,9 до 451,5 кандидата, а число положительных предсказаний с 14,2 до 128,6 на запрос. Все 101093 запроса остаются в знаменателе, включая 1592 запроса без положительного предсказания при K=200. Условное среднее только по положительным пулам было бы 130,7; его здесь не смешиваем с основным. Это число предсказанных релевантных фрагментов внутри выбранного пула, а не оценка количества всех релевантных ответов в корпусе.',60,{source:allsrc(src.full)});
 txt(s,'Mean passages per query',64,171,850,38,28,{color:C.muted});
 xy(s,[dotSeries('All candidates',ks,d.map(v=>v.candidates_mean_all_queries),C.gray),dotSeries('Predicted relevant',ks,d.map(v=>v.positives_mean_all_queries),C.coral)],{x:64,y:221,w:873,h:375,min:0,max:500,unit:100,format:'0',legend:true,xlabel:'Top-K results per retriever'});
 txt(s,'451.5',976,248,225,72,59,{color:C.gray,bold:true});
 txt(s,'candidates',976,325,228,42,27,{color:C.muted});
 txt(s,'128.6',976,427,225,72,59,{color:C.coral,bold:true});
 txt(s,'predicted relevant\nat K = 200',976,505,228,81,25,{color:C.muted});
 foot(s,'101,093 queries, including zero-positive pools. Same judge and threshold.');
}
// 10. A signed paired effect makes the null comparison visible.
{
 const s=slide('RRF changes position relative to E5',
 'RRF — reciprocal rank fusion, объединение по обратным рангам. Суммируем вклад BM25, E5 и BGE с константой 60, без использования их несопоставимых абсолютных оценок. На вертикальной оси разность NDCG RRF минус E5. Ноль означает равенство. При K=10 разность отрицательна: -0,0195. В четырёх более глубоких настройках небольшая положительная разность, от 0,0077 до 0,0109. При K=200 она 0,0088 с 95% интервалом от 0,0082 до 0,0095. Здесь одновременно меняется глубина оценочного пула K и глубина входов RRF L, равная K. Поэтому результат нельзя объяснять только полнотой оценивания или объявлять универсальным превосходством RRF. Это сравнение по меткам одного судьи. Следующий слайд отделяет влияние покрытия при фиксированных выдачах. Для каждого full-set сравнения рассчитан отдельный 95%-ный интервал по 2000 парным bootstrap-перевыборкам запросов. Интервалы условны на сохранённые выдачи, баллы судьи и фиксированный порог; они не учитывают обучение судьи и ошибки разметки.',70,{source:allsrc(src.full,src.rrf)});
 txt(s,'RRF(L = K) minus E5; assessment depth K = fusion input depth L',64,176,1152,44,29,{color:C.muted});
 xy(s,effectSeries('rrf_variable_minus_e5'),{x:64,y:242,w:1152,h:339,min:-.03,max:.02,unit:.01,format:'+0.000;-0.000;0',xlabel:'Assessment pool depth K',ylabel:'NDCG@10 difference'});
 txt(s,'K = 200: +0.0088   95% CI [0.0082, 0.0095]',64,593,1152,40,28,{color:C.coral,bold:true});
 foot(s,'Single-judge pseudo-labels. Points with 95% paired query-bootstrap intervals.');
}
// 11. Fixed-output control is evidence, not merely a verbal caveat.
{
 const s=slide('Assessment coverage can reverse a comparison',
 'Теперь глубина входов RRF зафиксирована на 200: при изменении K первая десятка каждой системы остаётся неизменной. Несмотря на это, разность меняется с -0,0661 при K=10 на +0,0080 при K=30. При K=10 вне пула остаются 145643 возвращённые пары запрос–фрагмент, или 14,4% первой десятки RRF по всем запросам. Они получают нулевой вклад; это не означает, что все они релевантны. При K=30 вне пула остаются 3555 пар, примерно 0,35%. Расширение покрытия добавляет оценки и может изменить идеальный знаменатель. Поэтому кривая далее не обязана расти монотонно. Здесь контроль показывает влияние оценочного покрытия при фиксированных ранжированиях, а не улучшение моделей. Это не полное причинное разложение двух механизмов.',90,{source:allsrc(src.full)});
 txt(s,'Fixed RRF inputs: top 200. Both output rankings stay unchanged.',64,176,1152,79,29,{color:C.teal,bold:true});
 xy(s,effectSeries('rrf_fixed200_minus_e5',{color:C.teal,connectPoints:true}),{x:64,y:270,w:822,h:303,min:-.08,max:.02,unit:.02,format:'+0.00;-0.00;0',xlabel:'Assessment pool depth K',ylabel:'NDCG@10 gap'});
 txt(s,'14.4%',941,286,275,83,66,{color:C.teal,bold:true});
 txt(s,'of RRF top-10 pairs\noutside the pool\nat K = 10',941,389,275,126,27);
 txt(s,'145,643 query–passage pairs',941,543,275,73,23,{color:C.muted});
 txt(s,'K = 10: −0.0661',91,594,378,38,25,{color:C.teal,bold:true});
 txt(s,'K = 30: +0.0080',486,594,378,38,25,{color:C.teal,bold:true});
 foot(s,'RRF minus E5 under pseudo-labels. Unjudged returned passages receive zero gain.');
}
// 12. Scope and robustness should be visible, but not dominate every figure.
{
 const s=slide('Scope and robustness',
 'После исключения 23 запросов с неразрешёнными категориями или пустыми текстами остаются 1156 запросов: порядок систем в ручном сравнении сохраняется. После исключения всех 1179 ручных запросов из большого набора остаются 99914: направления различий RRF и E5 по глубинам также сохраняются. Эти проверки полезны, но не заменяют независимую независимую ручную оценку большого набора. Межэкспертное согласие не измерено; ручной пул обогащён через известный ответ, а псевдометки даёт один компактный судья. Поэтому выводы ограничены исследованными пулами английского MS MARCO. Их перенос на другие языки, домены и поисковые системы в этой работе не проверяется.',65,{source:allsrc(src.manual,src.full)});
 txt(s,'Sensitivity checks',64,185,1100,44,31,{color:C.teal,bold:true});
 nativeTable(s,[['Evaluation','Remaining queries','Observed result'],['Manual labels\n23 affected queries excluded','1,156','System order unchanged'],['Full-set pseudo-labels\nManual queries excluded','99,914','Signs of RRF–E5 differences unchanged']],[455,257,440],64,250,[53,88,88],{size:25});
 rule(s,64,517,1152);
 txt(s,'Inter-assessor agreement is unmeasured.\nFull-set results lack independent human validation.',64,550,1152,82,28);
 foot(s,'Evidence concerns selected English MS MARCO pools and one judge.');
}
// 13. Leave the actual contribution on screen during questions.
{
 const s=slide('Judgment coverage affects retrieval evaluation',
 'Наш основной результат — измерение эффекта разметки на оценку неизменной выдачи. В ручных пулах среднее число положительных оценок растёт с 1,05 до 17,47, а NDCG E5 — с 0,488 до 0,879 при том же ранжировании. В большом эксперименте контроль с фиксированными входами RRF показывает, что расширение оценочного покрытия может поменять порядок сравниваемых систем. Поэтому вместе с метрикой важно описывать оценённый пул, источник суждений и глубину списков объединения. Это выводы по английскому MS MARCO и исследованным пулам. Следующая проверка — более сильные и судьи с доступом к эталонному фрагменту на независимых человеческих оценках. Спасибо, готов ответить на вопросы.',55,{dark:true,source:allsrc(src.manual,src.full)});
 txt(s,'Human judgments',64,232,440,46,32,{color:C.mint,bold:true});
 txt(s,'E5 NDCG@10: 0.488 to 0.879',64,302,1130,71,53,{color:C.white,bold:true});
 txt(s,'Same ranking; more complete relevance judgments',64,389,1130,48,31,{color:'#BED3D1'});
 rule(s,64,471,1152,'#3F5558');
 txt(s,'Fixed rankings; single-judge pseudo-labels',64,511,1152,48,34,{color:C.mint,bold:true});
 txt(s,'The judgment pool can change which system scores higher',64,577,1152,53,34,{color:C.white});
 foot(s,'Evidence from selected English MS MARCO candidate pools.',{dark:true});
}
// 14. Backup: exact uncertainty belongs to the paired effect.
{
 const s=slide('NDCG@10 and paired annotation effects',
 'Для бинарной релевантности DCG@10 — сумма rel_i / log2(i+1) по первым десяти позициям. NDCG делит DCG на идеальную сумму IDCG. Все системы делят на общий IDCG внутри запроса и конкретного набора меток; при доразметке этот знаменатель может изменяться. Неразмеченные фрагменты остаются на своих позициях с нулевым вкладом. Нулевой IDCG даёт нулевой NDCG, запрос остаётся в среднем. Интервалы относятся к парным изменениям human minus original, а не к отдельным средним. 5000 bootstrap-перевыборок по запросам, 10000 парных sign-flip рандомизаций, seed 20260914. Все четыре различия статистически значимы после поправки Бонферрони. Для каждого эффекта рассчитан отдельный 95%-ный интервал; совместное покрытие всех эффектов не оценивается. Эти интервалы не учитывают повторное обучение или неопределённость разметки.',0,{backup:true,source:allsrc(src.manual)});
 txt(s,'NDCG@10 = DCG@10 / ideal DCG@10',64,182,1152,52,34,{color:C.teal,bold:true});
 nativeTable(s,[['Ranking','Human − original','95% paired CI'],...models.map((k,i)=>[labels[i],`+${fmt(m.metrics[k].human_minus_official.mean)}`,m.metrics[k].human_minus_official.ci95.map(v=>fmt(v)).join(' to ')])],[340,362,450],64,266,[55,58,58,58,58],{size:27});
 foot(s,'5,000 paired query bootstraps. All four annotation effects: p < 0.001.');
}
// 15. Backup: native confusion matrix and complete split context.
{
 const s=slide('Judge test protocol and observed errors',
 'Train/validation/test: 825/177/177 запросов и 23543/5122/5002 пары. Две эпохи, batch 16, maximum length 512, warmup 100. Разбиение по запросам использует seed 42. Базовый checkpoint — cross-encoder/ms-marco-MiniLM-L6-v2. Порог -0,2187178284 по выходным баллам модели до порогового преобразования выбран на валидации. Тестовая матрица TN=1300, FP=506, FN=314, TP=2882. Точность классификации 0,836, precision 0,851, recall 0,902, F1 0,875. Унаследованное кодирование относит все категории кроме 1 и 2 к нулю. Тест включает шесть пар с метками, смысл которых не установлен и одну запись с пустым текстом. Исключение этих семи записей оставляет 4995 пар и даёт AUC 0,909, F1 0,876; это чувствительность, а не новый обученный судья. Метрики рассчитаны по сохранённым выходным баллам одной дообученной модели.',0,{backup:true,source:allsrc(src.manual,src.judge)});
 txt(s,'825 / 177 / 177 queries',64,184,1152,48,35,{color:C.teal,bold:true});
 txt(s,'Train / validation / test',64,240,1152,40,27,{color:C.muted});
 nativeTable(s,[['Test target','Predicted negative','Predicted positive'],['Negative under inherited mapping','1,300','506'],['Positive','314','2,882']],[470,341,341],64,315,[59,94,75],{size:27,emphasis:[[1,1],[2,2]]});
 txt(s,'Precision 0.851',64,580,364,40,29,{bold:true});
 txt(s,'Recall 0.902',463,580,332,40,29,{bold:true});
 txt(s,'F1 0.875',850,580,354,40,29,{bold:true});
 foot(s,'5,002 pairs; six unresolved targets mapped to zero and one empty-text record.');
}
// 16. Backup: precise full-set settings and denominators.
{
 const s=slide('Full-set depth results',
 'Таблица показывает средние по всем 101093 запросам. K — глубина пула, L — глубина входных списков RRF. RRF(L=K) меняет входы вместе с пулом. RRF(L=200) сохраняет одни и те же входы и выдачу во всех строках. При K=200 обе конфигурации совпадают. Здесь predicted relevant — положительные предсказания судьи, не человеческие подтверждения. Средние не исключают запросы без положительных предсказаний. При K=200 имеется 13004336 положительных предсказаний и 45647587 пар кандидатов.',0,{backup:true,source:allsrc(src.full)});
 nativeTable(s,[['K','Candidates /\nquery','Predicted relevant /\nquery','E5\nNDCG@10','RRF L=K\nNDCG@10','RRF L=200\nNDCG@10'],...d.map(v=>[String(v.k),fmt(v.candidates_mean_all_queries,1),fmt(v.positives_mean_all_queries,1),fmt(metric(v,'e5')),fmt(metric(v,'rrf_variable')),fmt(metric(v,'rrf_fixed200'))])],[83,193,245,188,216,227],64,207,[84,61,61,61,61,61],{size:24});
 foot(s,'Single-judge pseudo-labels. All 101,093 queries remain in every average.');
}
// 17. Backup: sensitivity cannot remove all sources of bias.
{
 const s=slide('Sensitivity to query exclusions',
 'В ручном пуле 29 пар с метками, смысл которых не установлен и пять пустых текстов затрагивают 23 запроса. Основная оценка сохраняет все 1179, а в проверке устойчивости исключаем затронутые запросы целиком. В таблице значения human NDCG на 1179 и 1156 запросах. Различия малы, порядок систем сохраняется. Для большого набора исключены все 1179 ручных запросов, включая train, validation и test судьи. Остаётся 99914. При K=200 разность RRF минус E5 составляет 0,00877 с интервалом [0,00804; 0,00944], направления сравнений на всех пяти глубинах сохраняются. Это проверка пересечения выборок, не доказательство проверки на независимой ручной разметке.',0,{backup:true,source:allsrc(src.manual,src.full)});
 txt(s,'Human-label NDCG@10',64,166,1152,40,27,{color:C.muted});
 nativeTable(s,[['Ranking','All 1,179 queries','1,156 after exclusions'],...models.map((k,i)=>[labels[i],fmt(m.metrics[k].human),fmt(m.metrics[k].clean_queries_human)])],[340,406,406],64,221,[56,57,57,57,57],{size:27});
 txt(s,'Full set without manual queries: N = 99,914',64,533,1152,45,30,{color:C.teal,bold:true});
 txt(s,'At K = 200: RRF − E5 = +0.00877',64,591,1152,42,28);
 foot(s,'Exclusion checks do not replace independent human assessment.');
}
// 18. Backup: an explicit future experiment, not a completed architecture claim.
{
 const s=slide('Next validation: reference-conditioned judging',
 'Следующий шаг — сравнить более сильные кросс-энкодеры и формат, в котором судья дополнительно видит известный релевантный ответ. Человек уже использует этот сигнал, поэтому такое сравнение мотивировано текущим дизайном разметки. На схеме предлагаемый вход: запрос, эталонный фрагмент из исходной разметки, оцениваемый фрагмент. Для проверки нужны независимые человеческие оценки на новых запросах, оценка согласия экспертов и проверка на других коллекциях. Никаких результатов для такого судьи здесь не заявляется. Работа измеряет влияние покрытия разметки и глубины пулов, отдельно сравнивая изменяемые и фиксированные входы RRF.',0,{backup:true,source:allsrc(src.judge,src.marco,'Research direction only; no reference-conditioned judge experiment reported.')} );
 txt(s,'Proposed input',64,184,1100,44,30,{color:C.muted});
 const inputs=box(s,'Query\nKnown relevant answer\nCandidate passage',64,260,493,176,{size:31});
 const future=box(s,'Reference-conditioned\ncross-encoder',682,260,503,176,{size:31,fill:'#E3F0ED'});
 connect(s,inputs,future);
 txt(s,'Compare stronger judges against independent human assessments.',64,509,1152,85,33,{color:C.teal,bold:true});
 foot(s,'Planned evaluation. No results for this model are reported in the present study.');
}

const draft=await exportDraft(`candidate-${VERSION}`);
await fs.writeFile(path.join(BUILD,`native-owners-${VERSION}.json`),JSON.stringify({charts,tables,mainSlides:notes.filter(v=>!v.backup).length,plannedSeconds:notes.reduce((a,v)=>a+v.seconds,0)},null,2));
const stamped=execFileSync(PY,[path.join(BUILD,'stamp_pptx.py'),draft],{encoding:'utf8'}).trim();
await fs.mkdir(path.join(BUILD,'validated'),{recursive:true});
const finalPath=path.join(BUILD,'validated',`validated-${VERSION}.pptx`);
await util.finalizePresentation({workspaceDir:ROOT,candidatePath:stamped,finalPath,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:charts,materializeLiteralChartWorkbooks:true,layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,`validation-${VERSION}.json`)});
console.log(JSON.stringify({finalPath,slides:notes.length,core:notes.filter(v=>!v.backup).length,seconds:notes.reduce((a,v)=>a+v.seconds,0),charts,tables}));
