import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {ROOT,BUILD,OUT,SKILL,PY,FONT,C,pres,charts,tables,notes,m,f,d,fmt,util,txt,rule,slide,foot,nativeTable,axis,grid,series,chart,box,connect,exportDraft} from './layout.mjs';

const VERSION=process.env.DECK_VERSION||'refined-v1';
const models=['bm25','e5','bge','rrf3'];
const labels=['BM25','E5','BGE','RRF (3)'];
const roc=JSON.parse(await fs.readFile(path.join(ROOT,'presentation_2026/premium/reviews/test_roc.json'),'utf8'));
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
function effectSeries(contrast,{color=C.coral,connectPoints=false,horizontal=false}={}){
 const rows=f.paired_inference.all_queries.filter(v=>v.contrast===contrast);
 if(horizontal)return [
  series('Zero difference',[.5,5.5],C.gray,{xValues:[0,0],marker:{symbol:'none'},line:{fill:C.gray,width:1.6}}),
  ...rows.map((v,i)=>series(`95% paired CI at K=${v.k}`,[5-i,5-i],color,{xValues:v.bootstrap_ci95,marker:{symbol:'none'},line:{fill:color,width:2.6}})),
  ...rows.flatMap((v,i)=>v.bootstrap_ci95.map((bound,j)=>series(`CI ${j?'upper':'lower'} cap at K=${v.k}`,[5-i-.065,5-i+.065],color,{xValues:[bound,bound],marker:{symbol:'none'},line:{fill:color,width:1.8}}))),
  series('Pool depth',rows.map((_,i)=>5-i),C.muted,{xValues:rows.map(()=>-.03),marker:{symbol:'none'},line:{fill:'none',width:0},dataLabelOverrides:rows.map((v,idx)=>({idx,text:`K = ${v.k}`,position:'left',showValue:false,textStyle:{typeface:FONT,fontSize:26,fill:C.muted}}))}),
  dotSeries('RRF minus E5 (horizontal)',rows.map(v=>v.mean_delta),rows.map((_,i)=>5-i),color,{marker:{symbol:'circle',size:4},line:{fill:'none',width:0}}),
 ];
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
 s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'presentation_2026/premium/build/assets/cover.png'))),contentType:'image/png',alt:'Иллюстрация текстовых фрагментов с оценками релевантности',fit:'cover',position:{left:0,top:0,width:1280,height:720}});
 txt(s,'DAMDID 2026',64,49,650,35,23,{color:C.mint,bold:true});
 txt(s,'Оценка поиска\nна MS MARCO',64,145,815,180,68,{color:C.white,bold:true});
 txt(s,'Доразметка и контролируемые\nпулы кандидатов',64,367,790,98,35,{color:'#C9DDDA'});
 txt(s,'Как меняется оценка неизменной выдачи',64,478,790,39,27,{color:C.mint});
 txt(s,'__REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__,\n__REMOVED_IDENTIFIER__',64,557,795,68,25,{color:C.white});
 txt(s,'__REMOVED_IDENTIFIER__',64,647,920,30,21,{color:'#B7CBCB'});
}
// Dataset context and a dated, comparable external benchmark snapshot.
{
 const s=slide('Почему MS MARCO',
 'Для исследования поиска существуют разные коллекции. Natural Questions использует реальные запросы Google и разметку ответов в статьях Wikipedia. BEIR объединяет разнородные задачи для проверки переноса. Мы выбираем MS MARCO: это веб-поиск по реальным запросам Bing, открытые тексты и разреженные оценки релевантности. Такой набор позволяет исследовать влияние доразметки. Выбор не означает универсальности результатов.',55,{source:allsrc(src.marco,'Microsoft, MS MARCO datasets: https://microsoft.github.io/msmarco/Datasets.html','Kwiatkowski et al. (2019), Natural Questions: https://research.google/pubs/natural-questions-a-benchmark-for-question-answering-research/','Thakur et al. (2021), BEIR: https://arxiv.org/abs/2104.08663')});
 txt(s,'Разные коллекции отвечают на разные вопросы о качестве поиска',64,155,1152,42,27,{color:C.muted});
 nativeTable(s,[['Набор / бенчмарк','Что позволяет проверить'],['Natural Questions','Ответы на реальные запросы Google'],['BEIR','Перенос между задачами и доменами'],['MS MARCO','Ранжирование веб-фрагментов для запросов Bing']],[335,817],64,231,[55,70,70,88],{size:27,emphasis:[[3,0],[3,1]]});
 txt(s,'Открытые тексты + неполные оценки релевантности',64,548,1152,43,31,{color:C.teal,bold:true});
 txt(s,'Подходящая постановка для изучения эффекта доразметки',64,598,1152,37,26);
 foot(s,'Источники: Bajaj и др., 2016/2018; Kwiatkowski и др., 2019; Thakur и др., 2021.');
}
{
 const url='https://github.com/microsoft/MSMARCO-Passage-Ranking-Submissions/blob/abb44144f563e7972d5131f5d6acc2092877964c/leaderboard/leaderboard.csv';
 const s=slide('Близкие метрики в официальном лидерборде',
 'Это исторический срез MS MARCO Passage Ranking на 30 ноября 2022 года, а не текущий рейтинг 2026 года. Четыре ведущие именованные системы в режиме full ranking на закрытом eval получили MRR@10 от 0,436 до 0,450. Размах 0,014. Метрика усредняет обратную позицию первого релевантного результата в первой десятке. Близость опубликованных средних не доказывает статистического равенства систем или неполноты разметки. Наш отдельный вопрос: насколько сравнение зависит от покрытия оценками? Далее приведён конкретный пример. Внешний MRR не сопоставляется напрямую с NDCG в наших пулах.',55,{source:allsrc(url,'Microsoft, Submission: https://microsoft.github.io/msmarco/Submission.html','Показаны четыре лучшие именованные заявки по eval среди full ranking. Анонимные заявки не включены. Полные названия: AliceMind Search LM (SLM) + Hybird List Aware Reranking (HLAR); Listwise + Fusion reranker; CoT-MAE; Lichee-xxlarge + deberta_v3-large + Reranking. Значения округлены как в официальном CSV.')});
 txt(s,'MS MARCO Passage Ranking · полный поиск · закрытый eval',64,157,1152,39,26,{color:C.muted});
 chart(s,'bar',{position:{left:64,top:222,width:920,height:329},categories:['Lichee + DeBERTa','CoT-MAE','Listwise + Fusion','AliceMind SLM + HLAR'],series:[series('MRR@10',[.436,.438,.440,.450],C.teal)],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:90},xAxis:{...axis,majorGridlines:null},yAxis:{...axis,min:0,max:.5,majorUnit:.1,numberFormatCode:'0.0',majorGridlines:grid},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:FONT,fontSize:25,fill:C.ink}}});
 txt(s,'0,014',1002,248,214,83,66,{color:C.teal,bold:true});
 txt(s,'размах\nMRR@10',1002,343,214,88,28,{color:C.muted});
 txt(s,'Близкие средние не доказывают эквивалентность систем',64,559,1152,43,30,{bold:true});
 txt(s,'MRR@10 учитывает позицию первого найденного релевантного ответа.',64,613,1152,32,23,{color:C.muted});
 txt(s,'Последний официальный срез: 30.11.2022. Трек закрыт 01.01.2023. Четыре именованные заявки.',64,661,1152,26,19,{color:C.muted});
 notes.at(-1).source+='\nСтатус трека проверен 05.10.2026: https://microsoft.github.io/msmarco/ . Последнее обновление CSV: https://api.github.com/repos/microsoft/MSMARCO-Passage-Ranking-Submissions/commits?path=leaderboard%2Fleaderboard.csv&per_page=1 . Две анонимные заявки с 0,439 не показаны; это не первые четыре места общего рейтинга.';
}
// 2. An actual pool example, not an invented ranked list.
{
 const s=slide('Правильный ответ может остаться без оценки',
 'Запрос 1086224 спрашивает, что вызывает повышение температуры кипения. Фрагмент про соль есть в исходных положительных оценках. Другой фрагмент объясняет повышение температуры кипения через нелетучее растворённое вещество. Человек также считает его релевантным, но в исходной разметке он отсутствует. Третий фрагмент сообщает температуру кипения ацетона и не отвечает на вопрос о причине. Тексты здесь сокращены, а идентификаторы сохранены. Это пример релевантности в конкретном пуле, а не утверждение о частоте подобных случаев во всём корпусе. Qrels — оценки релевантности пар «запрос-фрагмент». Unjudged означает отсутствие оценки, а не подтверждённую нерелевантность.',65,{source:allsrc(src.manual,'Actual query 1086224 and passages 7112148, 7399382, 987600 in the paper, Section 3.3. Shortened paraphrases.')});
 txt(s,'«Что вызывает повышение температуры кипения?»',64,169,1152,51,33,{color:C.teal,bold:true});
 nativeTable(s,[['Passage (shortened paraphrase)','Original qrels','Human judgment'],['7112148   Adding salt raises the boiling point.','Relevant','Relevant'],['7399382   A non-volatile solute raises\nthe boiling point.','Unjudged','Relevant'],['987600   The boiling temperature of acetone.','Unjudged','Not relevant']],[672,232,248],64,266,[56,88,102,78],{size:24,emphasis:[[2,0],[2,2]]});
 txt(s,'Нет оценки ≠ нерелевантен',64,610,1135,39,29,{color:C.teal,bold:true});
 txt(s,'В метрике: нет оценки → нулевой вклад. Русский пересказ; метки относятся к оригиналам.',64,660,1135,25,19,{color:C.muted});
}
// 3. Clearly separate the two populations and evidence types.
{
 const s=slide('Две части эксперимента',
 'Мы работаем с английской коллекцией MS MARCO Passage Ranking: 8 841 823 коротких текстовых фрагмента. Первый этап охватывает 1179 запросов и 33667 различных пар запрос–фрагмент с ручными оценками. Второй использует модель-судью и 101093 запроса. Это разные основания для выводов: человеческие суждения и предсказания. Большой набор включает все ручные запросы; отдельная проверка чувствительности исключает это пересечение. Под deep re-annotation понимается увеличение покрытия оценок внутри заданного пула. Термин не означает глубину сети или исчерпывающую разметку корпуса.',45,{source:allsrc(src.manual,src.full,src.marco)});
 txt(s,'Английский MS MARCO: 8,84 млн текстовых фрагментов',64,160,1152,43,29,{color:C.muted});
 rule(s,64,222,1152);
 txt(s,'Ручные оценки',64,255,440,43,31,{color:C.teal,bold:true});
 txt(s,'1 179',64,310,460,86,70,{color:C.teal,bold:true});
 txt(s,'запросов · 33 667 пар',64,408,500,40,28);
 txt(s,'Что меняет доразметка\nпри той же выдаче?',64,493,515,88,31,{bold:true});
 txt(s,'Псевдометки судьи',704,255,512,43,31,{color:C.coral,bold:true});
 txt(s,'101 093',704,310,512,86,70,{color:C.coral,bold:true});
 txt(s,'запроса · пять глубин пула',704,408,512,40,28);
 txt(s,'Как покрытие оценками\nвлияет на сравнение систем?',704,493,512,88,31,{bold:true});
 foot(s,'Человеческие суждения и предсказания судьи анализируются отдельно.');
}
// 4. Technical pooling workflow with orthogonal connections.
{
 const s=slide('Как сформирован ручной пул',
 'Пулинг — известный подход: объединяем кандидатов нескольких источников и удаляем дубликаты, чтобы сосредоточить ручную оценку на вероятно полезных фрагментах. BM25 использует лексическое совпадение. E5 и BGE относятся к плотному поиску с отдельными векторными представлениями запроса и фрагмента. Каждая сохранённая выдача даёт десять результатов. Дополнительные каналы расширяют объединение, включая сходство E5 с уже известным релевантным ответом. Их точная архитектура полностью не установлена; не трактуем их как сопоставимые поисковые системы. Человек видит запрос, кандидата и известный релевантный ответ. Такая помощь может задавать интерпретацию запроса и обогащает пул. Средний размер пула 28,56 кандидата, максимум 63. Пул не является случайной выборкой корпуса.',65,{source:allsrc(src.manual,src.retrieval)});
 txt(s,'Пулинг: объединение результатов нескольких источников',64,158,1152,40,28,{color:C.muted});
 const retrieval=box(s,'BM25 · E5 · BGE\nПо 10 результатов',64,233,325,113,{size:27});
 const aux=box(s,'Дополнительный отбор\nвключая сходство E5\nс известным ответом',64,409,325,140,{size:24,fill:'#FAEFE9'});
 const pooled=box(s,'Объединение\nбез дубликатов',485,302,278,126,{size:29});
 const human=box(s,'Ручная\nоценка',861,302,295,126,{size:30,fill:'#E2F1ED'});
 connect(s,retrieval,pooled,{kind:'elbow',to:'top'});connect(s,aux,pooled,{kind:'elbow',color:C.coral});connect(s,pooled,human);
 txt(s,'Человек видит:\nзапрос, кандидата\nи известный ответ',861,470,327,114,25,{color:C.teal});
 txt(s,'В среднем 28,56\nкандидата; максимум 63',479,471,315,85,25,{color:C.muted});
 foot(s,'Пул обогащён с помощью известного ответа; это не случайная выборка корпуса.');
}
// Metric explanation precedes the results; this is an explicitly illustrative example.
{
 const s=slide('Что измеряет NDCG@10',
 'Учебный пример поясняет метрику, а не воспроизводит экспериментальные числа. NDCG оценивает релевантные результаты в первой десятке с большим весом на верхних позициях и нормирует сумму на идеальную выдачу. Неоценённый документ сохраняет позицию, но даёт нулевой вклад. Доразметка может изменить и вклад документов, и идеальный знаменатель. Для одного запроса и набора меток знаменатель общий у сравниваемых систем.',55,{source:allsrc(src.manual,'Metric definition and evaluation convention: revision_2026/results/manual_summary.json, protocol. Illustrative three-position diagram; no experimental score is claimed.')});
 txt(s,'Релевантные ответы ближе к началу выдачи получают больший вес',64,157,1152,78,30,{color:C.muted});
 nativeTable(s,[['Позиция в выдаче','1','2','3'],['Вес релевантного ответа','1,00','0,63','0,50']],[558,198,198,198],64,255,[66,92],{size:29});
 txt(s,'NDCG@10 =',64,456,352,58,45,{color:C.teal,bold:true});
 txt(s,'оценка выдачи / оценка идеальной выдачи',398,464,818,45,31);
 txt(s,'Разметка меняет оценку; поисковая выдача остаётся прежней',64,559,1152,80,34,{bold:true});
 foot(s,'Учебный пример весов 1 / log₂(позиция + 1). Для сравнения используется общий идеал.');
}
// 5. Coverage is a property of the selected judgment set.
{
 const s=slide('Доразметка раскрывает пропущенные ответы',
 'Сравним положительные оценки внутри одних и тех же ручных пулов. В пересечении с официальными qrels имеется 1243 положительные пары; после человеческой разметки — 20597. Среднее на запрос меняется с 1,05 до 17,47. Разность суммарных чисел составляет 19354 пары, но это не число всех релевантных ответов в коллекции. Четырнадцать исходно помеченных seed-пар отсутствуют в официальных qrels, поэтому нельзя подменять официальное число категорией seed. На следующем слайде мы не изменяем порядок выдачи поисковых систем и набор запросов. Меняется только набор оценок, по которому измеряется качество.',55,{source:allsrc(src.manual)});
 txt(s,'Релевантных фрагментов на запрос в тех же ручных пулах',64,166,1152,43,29,{color:C.muted});
 txt(s,fmt(m.density.official.mean,2),64,272,450,121,104,{color:C.gray,bold:true});
 txt(s,fmt(m.density.human.mean,2),704,272,500,121,104,{color:C.teal,bold:true});
 txt(s,'→',536,296,135,80,61,{color:C.muted,align:'center'});
 rule(s,64,428,1152);
 txt(s,'Original qrels',64,466,500,45,34,{bold:true});
 txt(s,'1,243 positive pairs',64,528,520,42,28,{color:C.muted});
 txt(s,'Extended human judgments',704,466,512,80,32,{bold:true});
 txt(s,'20,597 positive pairs',704,528,512,42,28,{color:C.muted});
 foot(s,'1,179 queries. Same candidate pools and retrieval rankings.');
}
// 6. Native chart: absolute scores stay on a 0–1 scale.
{
 const s=slide('Выдача та же. Измеренная оценка выше',
 'NDCG@10 — normalized discounted cumulative gain: релевантный фрагмент получает больший вес ближе к началу первой десятки, затем сумму нормируем на идеальную выдачу. Для данного запроса и набора меток идеальный знаменатель общий для всех систем и учитывает полный оценённый пул; при смене разметки он может меняться. Все 1179 запросов остаются в среднем, включая нулевые. На графике исходные и человеческие оценки для фиксированных ранжирований. У E5 среднее меняется с 0,488 до 0,879, парная разность 0,391 с 95% интервалом от 0,365 до 0,417. Все четыре средних изменения положительны, p < 0,001. Это изменение измеренной оценки, а не результат улучшения поисковой модели. Порядок систем сохраняется: E5, RRF, BGE, BM25. RRF объединяет ранги BM25, E5 и BGE; здесь входы top-10, константа 60. Добавление разметки не гарантирует рост NDCG для каждого запроса.',90,{source:allsrc(src.manual,src.rrf)});
 const rev=[...models].reverse();
 txt(s,'Бинарная NDCG@10 внутри пулов · 1 179 запросов',64,162,1152,35,26,{color:C.muted});
 chart(s,'bar',{position:{left:64,top:205,width:1152,height:367},categories:[...labels].reverse(),series:[series('Original qrels',rev.map(k=>m.metrics[k].official),C.gray),series('Human judgments',rev.map(k=>m.metrics[k].human),C.teal)],barOptions:{direction:'bar',grouping:'clustered',gapWidth:120},xAxis:{...axis,majorGridlines:null},yAxis:{...axis,min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',majorGridlines:grid},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:FONT,fontSize:23,fill:C.ink}}});
 txt(s,'Изменение E5: +0,391 · 95%-ный ДИ [0,365; 0,417]',64,594,1145,42,28,{color:C.teal,bold:true});
 foot(s,'NDCG@10 внутри пулов. RRF объединяет ранги BM25, E5 и BGE; это не новый поиск.');
}
// 7. Why the judge exists, and precisely which information it receives.
{
 const s=slide('Зачем нужна модель-судья',
 'Ручная оценка позволяет проверить смысл доразметки, но оценивать миллионы пар вручную дорого. Поэтому во втором этапе используем компактный MiniLM как дообученную базовую модель для псевдоразметки. Это cross-encoder: запрос и фрагмент подаются совместно. В отличие от биэнкодеров E5 и BGE, модель не сравнивает независимо полученные эмбеддинги. На входе текст запроса и текст кандидата. Известного релевантного ответа, рангов и оценок других поисковых моделей у неё нет. Обучение использует ручные оценки, а порог выбирается на отдельной валидации. Выходы судьи расширяют покрытие оценивания, но остаются предсказаниями. В будущей работе планируем проверить, улучшает ли качество судьи добавление эталонного фрагмента из исходной разметки.',60,{source:allsrc(src.manual,src.judge)});
 const inp=box(s,'Query text\nCandidate passage',64,240,321,142,{size:30});
 txt(s,'Ручные оценки позволяют обучить модель для массовой разметки',64,163,1152,42,29,{color:C.muted});
 const model=box(s,'MiniLM\ncross-encoder',483,240,321,142,{size:30,fill:'#E3F0ED'});
 const out=box(s,'Score\nPseudo-label',902,240,285,142,{size:30,fill:'#FAEFE9'});
 connect(s,inp,model);connect(s,model,out,{color:C.coral});
 txt(s,'Совместная обработка текстов',483,417,700,40,27,{color:C.teal});
 rule(s,64,492,1152);
 txt(s,'Нет эталонного ответа, рангов и баллов других моделей',64,534,1152,77,31,{bold:true});
 foot(s,'Судья создаёт псевдометки и не заменяет поисковые системы.');
}
// 8. Actual query-held-out ROC, with the operating point preserved.
{
 const s=slide('Проверка судьи на отложенных запросах',
 'Запросы разделены между обучением, валидацией и тестом: 825, 177 и 177. Здесь 5002 пары только тестовых запросов. По вертикали ROC — доля верно выявленных положительных пар среди всех положительных; по горизонтали — доля ложноположительных среди всех отрицательных. Точки соответствуют разным порогам. Площадь под полной эмпирической кривой составляет 0,907, F1 при выбранном на валидации пороге — 0,875. Precision составляет 0,851, recall 0,902. F1 равен их гармоническому среднему. AUC не является процентом правильных ответов или вероятностью релевантности. Унаследованное бинарное кодирование относит категории 1 и 2 к положительным, остальные к нулю. Тест включает шесть пар с метками, смысл которых не установлен и одну пару с пустым текстом; после их исключения AUC составляет 0,909 и F1 0,876. Основная оценка использует исходное бинарное кодирование меток. Это согласие на выбранных пулах, не независимая гарантия качества глубоких пулов.',65,{source:allsrc(src.manual,src.judge,'Empirical ROC from held-out saved scores. Plot: 80 retained observed vertices; reported AUC integrates the full curve. Provenance: presentation_2026/premium/reviews/test_roc.json.')});
 txt(s,'Разбиение по запросам: 825 обучение / 177 валидация / 177 тест',64,158,1152,38,25,{color:C.muted});
 xy(s,[series('Chance',[0,1],C.rule,{xValues:[0,1],marker:{symbol:'none'},line:{fill:C.gray,width:1.3}}),dotSeries('MiniLM ROC',roc.points.map(v=>v.fpr),roc.points.map(v=>v.tpr),C.teal,{marker:{symbol:'none'},line:{fill:C.teal,width:3.5}}),dotSeries('Validation threshold',[roc.operating_point.fpr],[roc.operating_point.tpr],C.coral,{marker:{symbol:'circle',size:11},line:{fill:'none',width:0}})],{x:64,y:210,w:742,h:386,xmin:0,xmax:1,xunit:.2,xformat:'0.0',xlabel:'False positive rate',ylabel:'True positive rate'});
 txt(s,fmt(jt.auc),874,217,320,80,68,{color:C.teal,bold:true});
 txt(s,'ROC-AUC',874,303,320,40,29,{color:C.muted});
 txt(s,fmt(jt.f1),874,397,320,70,60,{color:C.ink,bold:true});
 txt(s,'F1 at validation threshold',874,475,320,72,26,{color:C.muted});
 txt(s,'Тест: 5 002 пары · precision 0,851 · recall 0,902',64,597,1152,34,25,{color:C.teal,bold:true});
 txt(s,'Точка: порог по валидации. Глубокие пулы не имеют независимой ручной проверки.',64,647,1135,42,21,{color:C.muted});
}
// 9. Counts, not corpus prevalence.
{
 const s=slide('Глубина пула меняет число псевдометок',
 'На большом наборе для каждого запроса объединяем первые K результатов BM25, E5 и BGE. K — длина каждой исходной выдачи, а не число уникальных кандидатов после удаления дубликатов. Используем одни и те же сохранённые оценки судьи и фиксированный порог. Средний пул растёт с 21,9 до 451,5 кандидата, а число положительных предсказаний с 14,2 до 128,6 на запрос. Все 101093 запроса остаются в знаменателе, включая 1592 запроса без положительного предсказания при K=200. Условное среднее только по положительным пулам было бы 130,7; его здесь не смешиваем с основным. Это число предсказанных релевантных фрагментов внутри выбранного пула, а не оценка количества всех релевантных ответов в корпусе.',60,{source:allsrc(src.full)});
 txt(s,'K: сколько результатов каждой модели получит оценку судьи',64,162,1152,36,27,{color:C.muted});
 txt(s,'Mean passages per query',64,205,850,34,25,{color:C.muted});
 xy(s,[dotSeries('All candidates',ks,d.map(v=>v.candidates_mean_all_queries),C.gray),dotSeries('Predicted relevant',ks,d.map(v=>v.positives_mean_all_queries),C.coral)],{x:64,y:249,w:873,h:347,min:0,max:500,unit:100,format:'0',legend:true,xlabel:'Top-K results per retriever'});
 txt(s,'451.5',976,248,225,72,59,{color:C.gray,bold:true});
 txt(s,'candidates',976,325,228,42,27,{color:C.muted});
 txt(s,'128.6',976,427,225,72,59,{color:C.coral,bold:true});
 txt(s,'predicted relevant\nat K = 200',976,505,228,81,25,{color:C.muted});
 foot(s,'101,093 queries, including zero-positive pools. Same judge and threshold.');
}
// 10. A signed paired effect makes the null comparison visible.
{
 const s=slide('Совместное изменение глубин пула и RRF',
 'RRF — reciprocal rank fusion, объединение по обратным рангам. Суммируем вклад BM25, E5 и BGE с константой 60, без использования их несопоставимых абсолютных оценок. Горизонтальная ось показывает разность NDCG RRF минус E5; каждой глубине пула соответствует отдельная строка. Ноль означает равенство. При K=10 разность отрицательна: -0,0195. В четырёх более глубоких настройках небольшая положительная разность, от 0,0077 до 0,0109. При K=200 она 0,0088 с 95% интервалом от 0,0082 до 0,0095. Здесь одновременно меняется глубина оценочного пула K и глубина входов RRF L, равная K. Поэтому результат нельзя объяснять только полнотой оценивания или объявлять универсальным превосходством RRF. Это сравнение по меткам одного судьи. Следующий слайд отделяет влияние покрытия при фиксированных выдачах. Для каждого full-set сравнения рассчитан отдельный 95%-ный интервал по 2000 парным bootstrap-перевыборкам запросов. Интервалы рассчитаны при фиксированных выдачах, баллах судьи и пороге. Неопределённость обучения судьи и ошибки разметки в них не учтены.',70,{source:allsrc(src.full,src.rrf)});
 txt(s,'K: документы для оценки       L: документы для слияния рангов',64,156,1152,38,26,{color:C.muted});
 txt(s,'L = K: это совместное изменение двух параметров',64,201,1152,42,29,{color:C.coral,bold:true});
 chart(s,'scatter',{position:{left:64,top:252,width:1152,height:323},hasLegend:false,scatterOptions:{style:'lineWithMarkers'},series:effectSeries('rrf_variable_minus_e5',{horizontal:true}),dataLabels:{showValue:false},xAxis:{...axis,min:-.03,max:.02,majorUnit:.01,numberFormatCode:'+0.00;-0.00;0',majorGridlines:null,title:'NDCG@10 difference (RRF minus E5)'},yAxis:{...axis,min:.5,max:5.5,majorUnit:1,tickLabelPosition:'none',majorGridlines:null,line:{fill:'none',width:0}}});
 txt(s,'K = 200: +0,0088 NDCG@10, небольшой абсолютный выигрыш',64,588,1152,38,28,{color:C.coral,bold:true});
 txt(s,'95%-ный парный ДИ [0,0082; 0,0095]. Ошибки и неопределённость судьи не учтены.\nСтатистическая различимость не устанавливает полезность для пользователя.',64,636,1110,53,21,{color:C.muted});
}
// 11. Fixed-output control is evidence, not merely a verbal caveat.
{
 const s=slide('Ключевой опыт: выдача зафиксирована',
 'Теперь глубина входов RRF зафиксирована на 200: при изменении K первая десятка каждой системы остаётся неизменной. Несмотря на это, разность меняется с -0,0661 при K=10 на +0,0080 при K=30. При K=10 вне пула остаются 145643 возвращённые пары запрос–фрагмент, или 14,4% первой десятки RRF по всем запросам. Они получают нулевой вклад; это не означает, что все они релевантны. При K=30 вне пула остаются 3555 пар, примерно 0,35%. Расширение покрытия добавляет оценки и может изменить идеальный знаменатель. Поэтому кривая далее не обязана расти монотонно. Здесь контроль показывает влияние оценочного покрытия при фиксированных ранжированиях, а не улучшение моделей. Это не полное причинное разложение двух механизмов.',90,{source:allsrc(src.full)});
 txt(s,'L = 200. У каждой системы топ-10 неизменен при любом K',64,156,1152,40,27,{color:C.muted});
 txt(s,'Меняются только доступные оценки релевантности',64,204,1152,44,31,{color:C.teal,bold:true});
 xy(s,effectSeries('rrf_fixed200_minus_e5',{color:C.teal,connectPoints:true}),{x:64,y:270,w:822,h:303,min:-.08,max:.02,unit:.02,format:'+0.00;-0.00;0',xlabel:'Assessment pool depth K',ylabel:'NDCG@10 gap'});
 txt(s,'14.4%',941,286,275,83,66,{color:C.teal,bold:true});
 txt(s,'of RRF top-10 pairs\noutside the pool\nat K = 10',941,369,275,126,24);
 txt(s,'Топ-10 E5 уже\nцеликом внутри пула',941,515,275,75,24,{color:C.muted});
 txt(s,'K = 10: −0.0661',91,594,378,38,25,{color:C.teal,bold:true});
 txt(s,'K = 30: +0.0080',486,594,378,38,25,{color:C.teal,bold:true});
 txt(s,'Разность RRF − E5 по псевдометкам. Расширение пула меняет покрытие и нормировку.',64,642,1135,45,22,{color:C.muted});
}
// 12. Scope and robustness should be visible, but not dominate every figure.
{
 const s=slide('Что проверено, а что ещё нет',
 'После исключения 23 запросов с неразрешёнными категориями или пустыми текстами остаются 1156 запросов: порядок систем в ручном сравнении сохраняется. После исключения всех 1179 ручных запросов из большого набора остаются 99914: направления различий RRF и E5 по глубинам также сохраняются. Эти проверки полезны, но не заменяют независимую ручную оценку большого набора. Межэкспертное согласие не измерено; ручной пул обогащён через известный ответ, а псевдометки даёт один компактный судья. Поэтому выводы ограничены исследованными пулами английского MS MARCO. Их перенос на другие языки, домены и поисковые системы в этой работе не проверяется.',65,{source:allsrc(src.manual,src.full)});
 txt(s,'Проверки устойчивости',64,172,540,43,31,{color:C.teal,bold:true});
 txt(s,'1 156 запросов',64,250,540,49,39,{bold:true});
 txt(s,'После исключения 23 проблемных:\nпорядок систем сохранён',64,311,540,84,27);
 txt(s,'99 914 запросов',64,429,540,49,39,{bold:true});
 txt(s,'Без всех ручных запросов:\nзнаки различий RRF − E5 сохранены',64,490,540,90,27);
 txt(s,'Границы выводов',704,172,512,43,31,{color:C.coral,bold:true});
 txt(s,'Ручной пул обогащён\nизвестным ответом',704,252,512,78,29);
 txt(s,'Согласие разметчиков\nне измерено',704,370,512,78,29);
 txt(s,'Один судья; глубокие пулы\nне проверены людьми',704,488,512,78,29);
 foot(s,'Переносимость на другие модели, языки и домены требует отдельного эксперимента.');
}
// 13. Leave the actual contribution on screen during questions.
{
 const s=slide('Главные выводы',
 'Наш основной результат — измерение эффекта разметки на оценку неизменной выдачи. В ручных пулах среднее число положительных оценок растёт с 1,05 до 17,47, а NDCG E5 — с 0,488 до 0,879 при том же ранжировании. В большом эксперименте контроль с фиксированными входами RRF показывает, что расширение оценочного покрытия может поменять порядок сравниваемых систем. Поэтому вместе с метрикой важно описывать оценённый пул, источник суждений и глубину списков объединения. Это выводы по английскому MS MARCO и исследованным пулам. Далее планируем проверить более сильных судей и судей с доступом к эталонному фрагменту, используя независимые человеческие оценки. Спасибо, готов ответить на вопросы.',55,{dark:true,source:allsrc(src.manual,src.full)});
 txt(s,'Ручная доразметка',64,169,1130,43,29,{color:C.mint,bold:true});
 txt(s,'E5: 0,488 → 0,879',64,225,1130,69,54,{color:C.white,bold:true});
 txt(s,'Ранжирование неизменно; оценка по более полным меткам выше',64,307,1130,44,28,{color:'#BED3D1'});
 rule(s,64,373,1152,'#3F5558');
 txt(s,'Оценка по псевдометкам',64,399,1152,44,29,{color:C.mint,bold:true});
 txt(s,'Покрытие пула может поменять порядок систем',64,455,1152,62,38,{color:C.white,bold:true});
 txt(s,'Вместе с метрикой нужны источник меток, состав пула и настройки RRF',64,529,1152,46,27,{color:'#BED3D1'});
 txt(s,'Далее: более сильные судьи и независимая ручная проверка',64,602,1152,40,25,{color:C.mint});
 txt(s,'При поддержке Российского научного фонда, соглашение № __REMOVED_IDENTIFIER__',64,658,1135,25,19,{color:'#BED3D1'});
}
// 14. Backup: exact uncertainty belongs to the paired effect.
{
 const s=slide('NDCG@10 and paired annotation effects',
 'Для бинарной релевантности DCG@10 — сумма rel_i / log2(i+1) по первым десяти позициям. NDCG делит DCG на идеальную сумму IDCG. Все системы делят на общий IDCG внутри запроса и конкретного набора меток; при доразметке этот знаменатель может изменяться. Неразмеченные фрагменты остаются на своих позициях с нулевым вкладом. Нулевой IDCG даёт нулевой NDCG, запрос остаётся в среднем. Интервалы относятся к парным изменениям human minus original, а не к отдельным средним. 5000 bootstrap-перевыборок по запросам, 10000 парных sign-flip рандомизаций, seed 20260914. Все четыре различия статистически значимы после поправки Бонферрони. Для каждого эффекта рассчитан отдельный 95%-ный интервал; совместное покрытие всех эффектов не оценивается. Эти интервалы не учитывают повторное обучение или неопределённость разметки.',0,{backup:true,source:allsrc(src.manual)});
 txt(s,'Парное изменение: ручные оценки минус исходные',64,182,1152,52,32,{color:C.teal,bold:true});
 nativeTable(s,[['Ranking','Human − original','95% paired CI'],...models.map((k,i)=>[labels[i],`+${fmt(m.metrics[k].human_minus_official.mean)}`,m.metrics[k].human_minus_official.ci95.map(v=>fmt(v).replace('.',',')).join(' ... ')])],[340,362,450],64,266,[55,58,58,58,58],{size:27});
 txt(s,'95%-ные ДИ: 5 000 парных bootstrap-выборок. p < 0,001: sign-flip тест.\nБинарный gain, общий IDCG по пулу; нулевые запросы остаются в среднем.',64,631,1135,57,22,{color:C.muted});
}
// 15. Backup: native confusion matrix and complete split context.
{
 const s=slide('Judge test protocol and observed errors',
 'Train/validation/test: 825/177/177 запросов и 23543/5122/5002 пары. Две эпохи, batch 16, maximum length 512, warmup 100. Разбиение по запросам использует seed 42. Базовый checkpoint — cross-encoder/ms-marco-MiniLM-L6-v2. Порог -0,2187178284 по выходным баллам модели до порогового преобразования выбран на валидации. Тестовая матрица TN=1300, FP=506, FN=314, TP=2882. Точность классификации 0,836, precision 0,851, recall 0,902, F1 0,875. Унаследованное кодирование относит все категории кроме 1 и 2 к нулю. Тест включает шесть пар с метками, смысл которых не установлен и одну запись с пустым текстом. Исключение этих семи записей оставляет 4995 пар и даёт AUC 0,909, F1 0,876; это чувствительность, а не новый обученный судья. Метрики рассчитаны по сохранённым выходным баллам одной дообученной модели.',0,{backup:true,source:allsrc(src.manual,src.judge)});
 for(const [i,label,value] of [[0,'Train queries','825'],[1,'Validation queries','177'],[2,'Test queries','177']]){txt(s,label,64+i*400,172,352,36,26,{color:C.muted});txt(s,value,64+i*400,218,352,66,48,{color:C.teal,bold:true});}
 const matrix=nativeTable(s,[['Test target','Predicted negative','Predicted positive'],['Coded negative','1,300','506'],['Coded positive','314','2,882']],[470,341,341],64,315,[59,94,75],{size:27,emphasis:[[1,1],[2,2]]});
 for(const [r,c]of [[1,2],[2,1]]){matrix.getCell(r,c).fill='#FAEFE9';matrix.getCell(r,c).text.style={typeface:FONT,fontSize:27,bold:true,color:C.coral};}
 txt(s,'Precision 0.851',64,580,364,40,29,{bold:true});
 txt(s,'Recall 0.902',463,580,332,40,29,{bold:true});
 txt(s,'F1 0.875',850,580,354,40,29,{bold:true});
 foot(s,'5,002 pairs; six unresolved targets mapped to zero and one empty-text record.');
}
// 16. Backup: precise full-set settings and denominators.
{
 const s=slide('Full-set depth results',
 'Таблица показывает средние по всем 101093 запросам. K — глубина пула, L — глубина входных списков RRF. RRF(L=K) меняет входы вместе с пулом. RRF(L=200) сохраняет одни и те же входы и выдачу во всех строках. При K=200 обе конфигурации совпадают. Здесь predicted relevant — положительные предсказания судьи, не человеческие подтверждения. Средние не исключают запросы без положительных предсказаний. При K=200 имеется 13004336 положительных предсказаний и 45647587 пар кандидатов.',0,{backup:true,source:allsrc(src.full)});
 const results=nativeTable(s,[['K','Candidates /\nquery','Predicted relevant /\nquery','E5\nNDCG@10','RRF L=K\nNDCG@10','RRF L=200\nNDCG@10'],...d.map(v=>[String(v.k),fmt(v.candidates_mean_all_queries,1),fmt(v.positives_mean_all_queries,1),fmt(metric(v,'e5')),fmt(metric(v,'rrf_variable')),fmt(metric(v,'rrf_fixed200'))])],[83,193,245,188,216,227],64,195,[100,61,61,61,61,61],{size:24,numericCols:[1,2,3,4,5]});
 for(const [c,color] of [[4,C.coral],[5,C.teal]])results.getCell(0,c).text.style={typeface:FONT,fontSize:22,color,bold:true,verticalAlignment:'middle',autoFit:'none',insets:{left:18,right:18,top:10,bottom:10}};
 txt(s,'При K = 200 RRF против E5: 26 241 победа / 21 042 поражения / 53 810 равенств.\nПсевдометки одного судьи. Все 101 093 запроса остаются в среднем.',64,631,1135,56,21,{color:C.muted});
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
// The corrected evaluation rules are explicit for discussion of the manuscript.
{
 const s=slide('Протокол уточнённого расчёта',
 'В докладе представлены уточнённые расчёты по сохранённым результатам. Единый набор запросов, общий IDCG для всех систем при заданных метках и явные настройки RRF отличаются от раннего расчёта. Поэтому и числа, и вывод о RRF отличаются от редакторской версии статьи. Ручные категории 1 и 2 бинаризуются как положительные; остальные не дают положительного вклада. Неоценённые документы не удаляются из выдачи. При нулевом IDCG NDCG равна нулю, запрос остаётся в среднем. Ручные входы RRF top-10, большой эксперимент сравнивает L=K и L=200, константа c=60. Ретриверы e5-small-v2 и bge-small-en-v1.5. Пересчёт проверяет сохранённые ранги и баллы; новое обучение судьи не выполнялось.',0,{backup:true,source:allsrc(src.manual,src.full,'Revision scope: original_based_2026/ПОЯСНЕНИЕ.md. Corrected protocol: revision_2026/manual_eval.py and revision_2026/fullset_eval.py.')});
 nativeTable(s,[['Правило','Применение в докладе'],['Состав запросов','Один и тот же набор для всех сравниваемых систем'],['Релевантность','Бинарная: ручные категории 1 и 2 положительные'],['Нормировка','Общий IDCG по пулу; при IDCG = 0 метрика равна 0'],['Нет оценки','Нулевой вклад без удаления позиции из выдачи'],['Слияние RRF','Константа 60; глубины входов L = K и L = 200']],[316,836],64,177,[54,67,67,78,73,70],{size:25});
 txt(s,'Модели: BM25 · e5-small-v2 · bge-small-en-v1.5',64,616,1152,34,24,{color:C.teal,bold:true});
 txt(s,'Уточнённые числа и вывод о RRF отличаются от редакторской версии рукописи.',64,663,1152,26,19,{color:C.muted});
}
{
 const s=slide('Судья как переранжировщик',
 'Дополнительная диагностика отвечает на вопрос о судье как ранжирующей модели. На 177 отложенных запросах сортируем все кандидаты ручного пула по сохранённым баллам судьи. NDCG по исходным меткам равна 0,5118, по человеческим 0,9384. Это переупорядочивание уже отобранного, обогащённого с помощью известного ответа пула, а не первый этап поиска по корпусу. Поэтому эти значения нельзя сопоставлять с полно-корпусным leaderboard или средними других моделей на 1179 запросах. Этим результатом нельзя обосновать качество судьи в новых глубоких пулах.',0,{backup:true,source:allsrc(src.manual,src.judge,'Held-out reranking values: manual_summary.json, judge_rerank_heldout. These diagnostics use saved scores, not a fresh model run.')});
 txt(s,'177 тестовых запросов · переранжирование кандидатов ручного пула',64,164,1152,73,28,{color:C.muted});
 txt(s,'0,512',64,289,492,99,86,{color:C.gray,bold:true});
 txt(s,'NDCG@10\nпо исходным меткам',64,410,502,90,31);
 txt(s,'0,938',704,289,512,99,86,{color:C.teal,bold:true});
 txt(s,'NDCG@10\nпо человеческим меткам',704,410,512,90,31);
 txt(s,'Отобранный пул, не поиск по полному корпусу',64,560,1152,51,36,{bold:true});
 foot(s,'Нельзя напрямую сравнивать с другими моделями на всех 1 179 запросах.');
}

// Keep the spoken script, note numbering and rehearsal estimates synchronized.
const speech=JSON.parse(await fs.readFile(path.join(BUILD,'speech_ru.json'),'utf8'));
const speechAudit=JSON.parse(await fs.readFile(path.join(BUILD,'script_audit_ru.json'),'utf8'));
for(const item of speech){
 const meta=notes[item.slide-1];
 meta.note=item.paragraphs.join('\n\n');
 meta.seconds=speechAudit.timings.find(t=>t.slide===item.slide).duration_seconds;
 if(item.slide===6)meta.source+='\nМетодическое уточнение: точная архитектура дополнительных каналов отбора не полностью установлена. Они не рассматриваются как отдельные сопоставимые поисковые системы.';
 pres.slides.items[item.slide-1].speakerNotes.textFrame.setText(`Ориентир: ${meta.seconds} секунд.\n\n${meta.note}\n\nИсточники и пояснения:\n${meta.source}`);
}
const draft=await exportDraft(`candidate-${VERSION}`);
await fs.writeFile(path.join(BUILD,`native-owners-${VERSION}.json`),JSON.stringify({charts,tables,mainSlides:notes.filter(v=>!v.backup).length,plannedSeconds:notes.reduce((a,v)=>a+v.seconds,0)},null,2));
const stamped=execFileSync(PY,[path.join(BUILD,'stamp_pptx.py'),draft],{encoding:'utf8'}).trim();
await fs.mkdir(path.join(BUILD,'validated'),{recursive:true});
const finalPath=path.join(BUILD,'validated',`validated-${VERSION}.pptx`);
await util.finalizePresentation({workspaceDir:ROOT,candidatePath:stamped,finalPath,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:charts,materializeLiteralChartWorkbooks:true,layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,`validation-${VERSION}.json`)});
console.log(JSON.stringify({finalPath,slides:notes.length,core:notes.filter(v=>!v.backup).length,seconds:notes.reduce((a,v)=>a+v.seconds,0),charts,tables}));
