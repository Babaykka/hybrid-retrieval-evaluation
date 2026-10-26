import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT = (process.env.PROJECT_ROOT||process.cwd());
const BUILD = path.join(ROOT, 'presentation_2026/build');
const OUT = path.join(ROOT, 'Презентация_DAMDID');
const SKILL = (process.env.PRESENTATIONS_SKILL||'');
const PYTHON = (process.env.PYTHON||'python3');
process.env.RUNTIME_NODE_MODULES=(process.env.RUNTIME_NODE_MODULES||'');
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(pathToFileURL(path.join(SKILL, 'container_tools/artifact_tool_utils.mjs')));
const font = resolvePresentationFont({ fontFamily: 'Arial' });
const C = { ink:'#172B32', teal:'#087F82', coral:'#C84F37', gray:'#83959D', muted:'#53676F', light:'#EDF5F4', rule:'#D7E2E4', white:'#FFFFFF' };
const pres = Presentation.create({ slideSize:{ width:1280, height:720 } });
const m = JSON.parse(await fs.readFile(path.join(ROOT, 'revision_2026/results/manual_summary.json'), 'utf8'));
const f = JSON.parse(await fs.readFile(path.join(ROOT, 'revision_2026/results/fullset_summary.json'), 'utf8'));
const depths = f.populations.all_queries.depths;
const models = ['bm25','e5','bge','rrf3'];
const modelLabels = ['BM25','E5','BGE','RRF (3)'];
const jt = m.judge_rescored_split_metrics.test;
const chartOwners = [], tableOwners = [], script = [];
const sources = {
  paper: '__REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__ and __REMOVED_IDENTIFIER__. Deep Re-annotation and Controlled Candidate Pools for Re-evaluating Ranking Models on MS MARCO. DAMDID 2026. Study data and recomputed pool-based analysis.',
  marco: 'Bajaj et al. (2016), https://arxiv.org/abs/1611.09268\nMS MARCO resources: https://microsoft.github.io/msmarco/Datasets',
  models: 'Robertson and Zaragoza (2009), The Probabilistic Relevance Framework: BM25 and Beyond.\nE5: https://arxiv.org/abs/2212.03533\nBGE full-set model: https://huggingface.co/BAAI/bge-small-en-v1.5',
  rrf: 'Cormack, Clarke and Buttcher (2009), Reciprocal Rank Fusion outperforms Condorcet and Individual Rank Learning Methods. SIGIR, pp. 758-759.',
  judge: 'MiniLM model: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2\nNogueira and Cho (2019), https://arxiv.org/abs/1901.04085',
};
const fmt = (v,n=3) => Number(v).toFixed(n);
const comma = v => Number(v).toLocaleString('en-US');

function text(s, value, x, y, w, h, size=28, color=C.ink, bold=false, opts={}) {
  const sh = s.shapes.add({ geometry:'textbox', name:opts.name ?? String(value).slice(0,48), position:{left:x,top:y,width:w,height:h}, fill:'none', line:{fill:'none',width:0} });
  sh.text = value;
  sh.text.style = { typeface:font,fontSize:size,color,bold,autoFit:'none',wrap:'square',verticalAlignment:'top',insets:{left:0,right:0,top:0,bottom:0},...opts };
  return sh;
}
function rule(s,x,y,w,color=C.rule) {
  return s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:0},fill:'none',line:{fill:color,width:1.3}});
}
function slide(title, section, note, seconds, refs=sources.paper, backup=false) {
  const s = pres.slides.add(); const n=pres.slides.items.length;
  s.background.fill=C.white;
  if(title) text(s,title,64,74,1152,108,44,C.ink,true);
  text(s,section.toUpperCase(),64,30,1000,28,18,C.teal,true);
  rule(s,64,670,1152);
  text(s,'DAMDID 2026',64,683,900,22,15,C.muted);
  text(s,backup?`A${n-12}`:String(n).padStart(2,'0'),1160,680,56,26,18,C.muted,false,{alignment:'right'});
  const allNotes=`${backup?'Резервный слайд':`Ориентир: ${seconds} секунд`}.\n\n${note}\n\nИсточники:\n${refs}`;
  s.speakerNotes.textFrame.setText(allNotes);
  script.push({n,title,seconds:backup?0:seconds,note,refs,backup});
  return s;
}
function table(s,values,widths,x,y,height,{size=25,rowHeights=[],emphasis=[]}={}) {
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height,columnWidths:widths,values});
  t.styleOptions={headerRow:false,totalRow:false,firstColumn:false,lastColumn:false,bandedRows:false,bandedColumns:false};
  t.borders.assign({fill:C.rule,width:1});
  for(let r=0;r<values.length;r++) {
    if(rowHeights[r]) t.rows[r].height=rowHeights[r];
    for(let c=0;c<values[r].length;c++) {
      const cell=t.getCell(r,c);
      cell.fill=r===0?C.light:C.white;
      cell.text.style={typeface:font,fontSize:r===0?size-2:size,color:r===0?C.muted:C.ink,bold:r===0,autoFit:'none',verticalAlignment:'middle',insets:{left:18,right:18,top:12,bottom:12}};
    }
  }
  for(const [r,c] of emphasis) {t.getCell(r,c).text.style={typeface:font,fontSize:size,bold:true,color:C.teal};t.getCell(r,c).fill='#F2F8F7';}
  tableOwners.push(pres.slides.items.length);return t;
}
function nativeChart(s,type,config) {
  // Excel stores at most 15 significant digits. Eight decimal places exceed
  // the displayed precision and preserve the measured effects here.
  config.series=config.series.map(series=>({...series,values:series.values.map(v=>Number(v.toFixed(8)))}));
  if(type==='bar') config.series=config.series.map(series=>({...series,line:{fill:'none',width:0}}));
  const chart=s.charts.add(type,{
    chartFill:C.white,chartLine:{fill:'none',width:0},plotAreaFill:C.white,plotAreaLine:{fill:'none',width:0},
    hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{typeface:font,fontSize:24,fill:C.ink}},
    ...config,
  });
  applyPresentationChartFont(chart,{fontFamily:font});
  chartOwners.push(pres.slides.items.length);return chart;
}
const ax = {textStyle:{typeface:font,fontSize:23,fill:C.muted},line:{fill:C.rule,width:1}};
const grid = {fill:C.rule,width:1};
const ser=(name,values,color,extra={})=>({name,values,fill:color,line:{fill:color,width:3.5},valuesFormatCode:'0.000',...extra});
function node(s,label,x,y,w,h,{fill=C.light,color=C.ink,size=26}={}) {
  const sh=s.shapes.add({geometry:'rect',name:label,position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.rule,width:1.4}});
  sh.text=label;sh.text.style={typeface:font,fontSize:size,color,bold:false,alignment:'center',verticalAlignment:'middle',insets:{left:14,right:14,top:10,bottom:10},autoFit:'none'};return sh;
}
function arrow(s,a,b,fromSide='right',toSide='left',color=C.muted) {
  return s.shapes.connect(a,b,{kind:'straight',fromSide,toSide,line:{fill:color,width:2.2},tail:{type:'triangle',width:'sm',length:'sm'}});
}

// 1. The cover title remains editable. The photograph is illustrative only.
{
 const s=slide('', 'DAMDID 2026',
 'Сегодня я расскажу, как неполная разметка влияет на оценку поиска. Мы исследуем MS MARCO, где у запроса часто указан только один правильный фрагмент, хотя подходящих ответов может быть несколько. Работа состоит из ручной доразметки и отдельного эксперимента с автоматическим судьёй. Основной вопрос: как меняется оценка уже существующей выдачи, когда мы расширяем набор известных релевантных ответов?',35,
 sources.paper+'\nConference: https://damdid.unn.ru/overview/\nCover: editorial illustration of passage annotation, not experimental evidence.');
 s.images.add({blob:new Uint8Array(await fs.readFile(path.join(BUILD,'assets/annotation-cover.png'))),contentType:'image/png',alt:'Illustrative printed passages with annotation highlights',position:{left:690,top:190,width:590,height:450},fit:'cover'});
 text(s,'Deep Re-annotation\nand Controlled\nCandidate Pools',64,126,840,230,62,C.ink,true);
 text(s,'Re-evaluating ranking models\non MS MARCO',64,376,740,100,32,C.teal);
 text(s,'__REMOVED_IDENTIFIER__\n__REMOVED_IDENTIFIER__ and __REMOVED_IDENTIFIER__',64,535,760,64,23,C.ink);
 text(s,'__REMOVED_IDENTIFIER__',64,612,760,32,21,C.muted);
}
// 2. Actual example, shortened paraphrases.
{
 const s=slide('One query can have several correct answers','The problem',
 'Начнём с реального примера. Запрос спрашивает, что вызывает повышение температуры кипения. Исходная разметка содержит фрагмент про добавление соли. Другой фрагмент объясняет тот же эффект через нелетучее растворённое вещество. Человек считает его релевантным, однако в исходных qrels он отсутствует. Qrels означает query relevance judgments, то есть оценки релевантности документов запросам. Отсутствие записи даёт нулевой вклад в метрику, хотя ответ может быть правильным. Третий фрагмент сообщает температуру кипения ацетона и на вопрос о причине не отвечает. Тексты здесь сокращены, идентификаторы сохранены. Это пример конкретной ошибки оценки, а не оценка частоты таких ошибок во всём корпусе.',75);
 text(s,'“what causes boiling point to increase”',64,183,1152,52,33,C.teal,true);
 table(s,[['Passage (shortened)','Original qrels','Human label'],['7112148  Adding salt raises the boiling point.','Relevant','Relevant'],['7399382  A non-volatile solute raises the boiling point.','Unjudged','Relevant'],['987600  The boiling temperature of acetone.','Unjudged','Not relevant']],[694,222,236],64,258,294,{size:25,rowHeights:[54,80,80,80],emphasis:[[2,2]]});
 text(s,'qrels = query relevance judgments. Unjudged passages receive zero gain.',64,592,1140,44,26,C.ink);
}
// 3. Separate populations and interpretation.
{
 const s=slide('Annotation coverage at two scales','Study design',
 'Исходный материал представляет собой англоязычную коллекцию MS MARCO Passage Ranking из примерно 8,84 миллиона фрагментов. В ручной части мы анализируем 1179 запросов и 33667 различных пар запрос–фрагмент. Затем применяем обученного судью к пулам для 101093 запросов. Это две разные основы оценки: ручные суждения и предсказания модели. Под deep re-annotation понимается более полное покрытие кандидатов внутри выбранного пула. Слово deep не означает глубину нейросети или полную разметку корпуса. Размер ручного пула в среднем составляет 28,56 кандидата на запрос, максимум 63. Коллекцию MS MARCO мы используем как воспроизводимую исследовательскую среду, не утверждая её универсальность для всех поисковых систем и аудиторий.',65,sources.paper+'\n'+sources.marco);
 text(s,'MS MARCO Passage Ranking',64,190,1000,44,30,C.muted);
 text(s,'8.84 million English passages',64,239,1100,56,39,C.ink,true);
 rule(s,64,329,1152);
 text(s,'1,179',64,368,500,90,74,C.teal,true);
 text(s,'queries with human judgments',64,465,500,42,28,C.ink);
 text(s,'33,667 query–passage pairs',64,519,510,40,25,C.muted);
 text(s,'101,093',700,368,516,90,74,C.coral,true);
 text(s,'queries with judge predictions',700,465,516,42,28,C.ink);
 text(s,'Candidate depth varies from 10 to 200',700,519,516,68,25,C.muted);
 text(s,'“Deep” refers to judgment coverage within a defined candidate pool.',64,612,1145,37,25,C.ink);
}
// 4. Editable technical flow.
{
 const s=slide('Pooling and human assessment','Manual annotation',
 'Для ручной разметки сначала выполняется пулинг: объединение кандидатов из нескольких источников с удалением дубликатов. Поиск по запросу представлен BM25, который сопоставляет термы, и плотными биэнкодерами E5 и BGE. Для каждого из трёх источников сохранены первые десять результатов. Дополнительные каналы включают сходство, вычисленное E5 между кандидатом и известным правильным ответом. Поэтому ручной пул содержит больше кандидатов, чем объединение только трёх выдач. Человек видит запрос, кандидата и исходный релевантный ответ. Это помогает согласовать доразметку с исходным пониманием релевантности. Сигнал известного ответа используется для подготовки и оценки кандидатов, но недоступен обычной модели поиска, работающей только по запросу. В сравнении систем участвуют три источника поиска и их RRF.',75,sources.paper+'\n'+sources.models);
 const a=node(s,'Query-based retrieval\nBM25, E5, BGE\nTop 10 from each',64,215,320,160);
 const b=node(s,'Auxiliary candidates\nincluding E5 similarity\nto a known relevant answer',64,425,320,150,{fill:'#FAF0EC',size:25});
 const c=node(s,'Deduplicated\ncandidate pool',502,293,246,154);
 const d=node(s,'Human judgments',878,293,338,154,{fill:'#DDEFEA'});
 arrow(s,a,c);arrow(s,b,c);arrow(s,c,d);
 text(s,'28.56 candidates/query\n63 at most',502,479,270,80,25,C.muted);
 text(s,'Assessor sees:\nquery, candidate,\nknown relevant answer',878,479,338,112,25,C.ink);
 text(s,'BM25: term matching. E5 and BGE: dense bi-encoder retrieval.',64,615,1150,34,24,C.muted);
}
// 5. Native bar chart and clear denominator.
{
 const s=slide('Human judgments reveal many more positives','Manual results',
 'На одном и том же наборе из 1179 запросов число положительных пар увеличивается с 1243 до 20597. В среднем это переход с 1,05 до 17,47 релевантного фрагмента на запрос. Доразметка обнаруживает ещё 19354 положительные пары относительно пересечения исходных qrels с ручным пулом. Здесь важно точно понимать знаменатель: мы считаем документы внутри подготовленных пулов. Это не утверждение, что во всей коллекции у каждого запроса ровно семнадцать правильных ответов. Пул специально обогащён вероятно релевантными кандидатами, в том числе с использованием известного ответа. Результат показывает, насколько неполными были исходные оценки именно для этих кандидатов.',60);
 nativeChart(s,'bar',{position:{left:64,top:202,width:768,height:410},categories:['Original','Human'],series:[ser('Relevant passages/query',[m.density.official.mean,m.density.human.mean],C.teal,{valuesFormatCode:'0.00',points:[{idx:0,fill:C.gray},{idx:1,fill:C.teal}]})],hasLegend:false,barOptions:{direction:'column',grouping:'clustered',gapWidth:110},xAxis:{...ax,majorGridlines:null},yAxis:{...ax,min:0,max:20,majorUnit:5,majorGridlines:grid,numberFormatCode:'0'},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:32,fill:C.ink,bold:true}}});
 text(s,'20,597',914,278,300,95,58,C.teal,true);
 text(s,'human-positive pairs',914,374,300,80,27,C.ink);
 text(s,'1,243 original positives\nin the same pool',914,479,300,82,24,C.muted);
 text(s,'1,179 queries. Counts describe selected candidate pools.',64,617,1150,36,24,C.muted);
}
// 6. Define the evaluation before reporting numbers.
{
 const s=slide('Fixed rankings, different relevance labels','Evaluation',
 'Чтобы оценить влияние доразметки, мы сохраняем выдачи систем и меняем только оценки релевантности. Используется NDCG@10: нормированная мера качества первых десяти результатов, где релевантный документ на более высокой позиции даёт больший вклад. Для каждого запроса и набора разметки идеальный знаменатель рассчитывается по всему пулу и одинаков для всех систем. Он может измениться после доразметки. Все 1179 запросов входят в среднее, даже если система не нашла ни одного положительного документа. RRF, Reciprocal Rank Fusion, объединяет ранги BM25, E5 и BGE. В ручной части у каждого источника берём десять позиций, константа RRF равна 60. Рост метрики в таком сравнении означает более полную оценку существующих ответов, а не улучшение модели после обучения.',70,sources.paper+'\n'+sources.rrf);
 const ranking=node(s,'Same ranked results\nBM25, E5, BGE, RRF',64,257,360,158,{fill:C.white});
 const original=node(s,'Original qrels',572,219,268,97,{fill:'#EEF1F3'});
 const human=node(s,'Human judgments',572,373,268,97,{fill:'#DDEFEA'});
 const score=node(s,'NDCG@10\nQuality of the top 10',940,294,276,125,{fill:C.white,size:27});
 text(s,'NDCG: normalized discounted cumulative gain',64,180,1150,38,27,C.muted);
 arrow(s,ranking,original);arrow(s,ranking,human);arrow(s,original,score);arrow(s,human,score);
 text(s,'One ideal denominator per query and label set, shared by all systems.',64,528,1150,50,29,C.ink);
 text(s,'RRF = Reciprocal Rank Fusion. Here: BM25 + E5 + BGE, c = 60.',64,606,1150,38,24,C.muted);
}
// 7. Paired changes with native chart data.
{
 const s=slide('NDCG rises with denser human judgments','Manual results',
 'На графике показаны результаты для одинаковых выдач под исходной и ручной разметкой. Например, BM25 меняется с 0,248 до 0,644, а E5 с 0,488 до 0,879. Для всех четырёх вариантов средний прирост составляет около 0,39. Парные проверки по запросам дают p меньше 0,001, в том числе после поправки на множественные сравнения. Это сильный эффект полноты разметки, но не результат повторного обучения поисковых систем. E5 остаётся лучшей из трёх сравниваемых моделей поиска. Их объединение RRF находится между E5 и BGE и в ручном эксперименте не превосходит E5. Числа относятся к оценке внутри размеченных пулов с общим IDCG, поэтому их нельзя напрямую сравнивать с полнокорпусным лидербордом.',80);
 nativeChart(s,'bar',{position:{left:58,top:193,width:1158,height:412},categories:modelLabels,series:[ser('Original qrels',models.map(k=>m.metrics[k].official),C.gray),ser('Human judgments',models.map(k=>m.metrics[k].human),C.teal)],barOptions:{direction:'column',grouping:'clustered',gapWidth:115},xAxis:{...ax,majorGridlines:null},yAxis:{...ax,min:0,max:1,majorUnit:0.2,majorGridlines:grid,numberFormatCode:'0.0'},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:24,fill:C.ink}}});
 text(s,'All 1,179 queries. Common pool-based IDCG. Paired changes: p < 0.001.',64,616,1150,34,23,C.muted);
}
// 8. Judge architecture and truly held-out agreement.
{
 const s=slide('MiniLM cross-encoder as a relevance judge','Automatic annotation',
 'Ручная разметка остаётся основой для проверки качества судьи, а модель нужна для расширения эксперимента на гораздо большее число пар. Судья представляет собой компактный cross-encoder MiniLM: он совместно обрабатывает текст запроса и кандидата. Это отличается от биэнкодеров E5 и BGE, которые получают отдельные векторные представления. Судья не получает готовые эмбеддинги, оценки и ранги других моделей или правильный ответ. На отложенных 177 запросах, содержащих 5002 пары, ROC-AUC равен 0,907, precision 0,851, recall 0,902 и F1 0,875. Порог выбирается на валидации и фиксируется до теста. Это свидетельство согласия с ручной разметкой выбранных кандидатов, а не доказательство, что судья сильнее всех моделей поиска.',80,sources.paper+'\n'+sources.judge);
 text(s,'Input: query text + candidate text',64,182,1130,48,31,C.ink);
 text(s,fmt(jt.auc),64,279,414,117,91,C.teal,true);
 text(s,'ROC-AUC on held-out queries',64,406,470,88,28,C.ink);
 text(s,'177 queries\n5,002 query–passage pairs',64,520,470,86,26,C.muted);
 nativeChart(s,'bar',{position:{left:568,top:259,width:648,height:337},categories:['Precision','Recall','F1'],series:[ser('Held-out agreement',[jt.precision,jt.recall,jt.f1],C.teal)],hasLegend:false,barOptions:{direction:'column',grouping:'clustered',gapWidth:100},xAxis:{...ax,majorGridlines:null},yAxis:{...ax,min:0,max:1,majorUnit:0.25,majorGridlines:grid,numberFormatCode:'0.00'},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:26,fill:C.ink}}});
 text(s,'No reference answer or retrieval scores. Threshold selected on validation.',64,619,1150,34,23,C.muted);
}
// 9. Pool depth and pseudo-positive counts share one population.
{
 const s=slide('Pseudo-label counts depend on pool depth','Larger experiment',
 'Во второй части берём 101093 запроса и объединяем первые K результатов BM25, E5 и BGE. Для всех глубин используется один судья и один порог. По мере расширения пула среднее число кандидатов растёт примерно с 22 до 452. Среднее число положительных предсказаний растёт с 14,2 до 128,6. На графике все средние рассчитаны по полному набору запросов, включая запросы без положительных предсказаний. Следовательно, утверждение о примерно 129 релевантных документах без описания метода было бы некорректным. Мы наблюдаем плотность положительных предсказаний конкретного судьи в конкретном пуле. Ошибки судьи и целенаправленный отбор кандидатов не позволяют интерпретировать эту величину как истинную релевантность всего корпуса.',75);
 nativeChart(s,'scatter',{position:{left:58,top:185,width:833,height:413},series:[ser('Candidates',depths.map(d=>d.candidates_mean_all_queries),C.gray,{xValues:depths.map(d=>d.k),valuesFormatCode:'0.0',marker:{symbol:'circle',size:8}}),ser('Pseudo-positive',depths.map(d=>d.positives_mean_all_queries),C.teal,{xValues:depths.map(d=>d.k),valuesFormatCode:'0.0',marker:{symbol:'circle',size:8}})],xAxis:{...ax,min:0,max:210,majorUnit:50,numberFormatCode:'0',title:{text:'Top K per retrieval source',textStyle:{typeface:font,fontSize:23,fill:C.muted}},majorGridlines:null},yAxis:{...ax,min:0,max:500,majorUnit:100,numberFormatCode:'0',majorGridlines:grid,title:{text:'Mean passages per query',textStyle:{typeface:font,fontSize:22,fill:C.muted}}},scatterOptions:{style:'lineWithMarkers'}});
 text(s,'128.6',946,274,270,95,67,C.teal,true);
 text(s,'pseudo-positive\npassages per query\nat K = 200',946,379,270,128,27,C.ink);
 text(s,'All 101,093 queries. Same judge and threshold at every depth.',64,617,1150,35,24,C.muted);
}
// 10. RRF and E5 comparison. Categorical depths are explicit.
{
 const s=slide('RRF depends on the depth of its input lists','Larger experiment',
 'Теперь сравним RRF и E5 под псевдоразметкой. При K, равном 10, RRF уступает E5 примерно на 0,020 NDCG. На четырёх более глубоких вариантах RRF немного выше E5. При K, равном 200, разница составляет около 0,009, а 95-процентный доверительный интервал примерно от 0,0082 до 0,0095. Здесь одновременно меняются пул оценки и глубина входных списков RRF. Поэтому наблюдение нельзя объяснять только расширением разметки. Выдача E5 в первых десяти позициях остаётся той же, но нормировка может изменяться. У RRF может изменяться и сама выдача. Наконец, оба результата измеряют согласие с этим судьёй. Это условный результат данного эксперимента, а не доказательство универсального превосходства RRF.',85,sources.paper+'\n'+sources.rrf);
 nativeChart(s,'scatter',{position:{left:58,top:190,width:849,height:406},series:[ser('E5',depths.map(d=>d.models.e5.ndcg10_mean_all_queries),C.teal,{xValues:depths.map(d=>d.k),marker:{symbol:'circle',size:9}}),ser('RRF (3)',depths.map(d=>d.models.rrf_variable.ndcg10_mean_all_queries),C.coral,{xValues:depths.map(d=>d.k),marker:{symbol:'square',size:9}})],xAxis:{...ax,min:0,max:210,majorUnit:50,numberFormatCode:'0',title:{text:'Top K for pooling and RRF inputs',textStyle:{typeface:font,fontSize:23,fill:C.muted}},majorGridlines:null},yAxis:{...ax,min:0.82,max:0.89,majorUnit:0.01,numberFormatCode:'0.00',majorGridlines:grid,title:{text:'NDCG@10 under pseudo-labels',textStyle:{typeface:font,fontSize:22,fill:C.muted}}},scatterOptions:{style:'lineWithMarkers'}});
 text(s,'RRF minus E5',942,213,274,40,26,C.ink,true);
 text(s,'−0.020',942,286,274,85,54,C.muted,true);
 text(s,'at K = 10',942,369,274,36,26,C.muted);
 text(s,'+0.009',942,439,274,85,54,C.coral,true);
 text(s,'at K = 200',942,522,274,36,26,C.muted);
 text(s,'Pool depth and RRF input depth both vary. Vertical axis shows a narrow range.',64,616,1150,35,23,C.muted);
}
// 11. Future work is visibly prospective.
{
 const s=slide('A judge with access to the known answer','Limitations and next experiment',
 'Текущий судья намеренно ограничен двумя текстами: запросом и кандидатом. Это простой базовый эксперимент, а не оптимальный способ аннотирования. У человека уже есть известный правильный ответ, и естественный следующий шаг состоит в том, чтобы дать эту информацию модели-судье. Планируемый формат входа: запрос, известный релевантный ответ и оцениваемый фрагмент. Такую модель следует сравнить с текущей и более сильными cross-encoder моделями на отложенной ручной разметке. В этой работе такого сравнения ещё нет. Важно также проверить перенос на другие коллекции: наши выводы ограничены английским MS MARCO, выбранными пулами и одним судьёй. Это особенно существенно для обобщений на другие языки, поисковые системы и типы запросов.',65,sources.paper+'\n'+sources.judge);
 text(s,'Current baseline',64,224,510,44,30,C.muted,true);
 text(s,'Query\nCandidate passage',64,299,510,133,40,C.ink);
 text(s,'Planned comparison',690,224,526,44,30,C.teal,true);
 text(s,'Query\nKnown relevant answer\nCandidate passage',690,299,526,187,40,C.ink);
 rule(s,64,534,1152);
 text(s,'Stronger cross-encoders and held-out human evaluation',64,571,1152,46,31,C.ink);
 text(s,'Evidence here is limited to English MS MARCO, selected pools and one judge.',64,623,1150,30,23,C.muted);
}
// 12. Closing slide doubles as the questions screen.
{
 const s=slide('Conclusions','Discussion',
 'Подведу итог. Ручная доразметка обнаруживает много подходящих ответов, которые отсутствовали в исходных qrels: в среднем 17,47 положительного фрагмента вместо 1,05 в наших пулах. Более полные оценки заметно повышают NDCG неизменных выдач. MiniLM позволяет расширить исследование, но его предсказания нужно отличать от человеческих суждений. Для интерпретации RRF необходимо одновременно указывать глубину пула и глубину входных списков. На более глубоких списках мы видим небольшой выигрыш относительно E5 под псевдоразметкой. Следующий эксперимент должен проверить более сильных судей и использование известного ответа. Спасибо, я готов к вопросам.',45);
 text(s,'1.05 to 17.47',64,208,442,78,54,C.teal,true);
 text(s,'Human positives per query\ninside the annotated pools',555,212,630,93,30,C.ink);
 rule(s,64,334,1152);
 text(s,'Higher NDCG',64,375,442,75,44,C.ink,true);
 text(s,'More complete judgments\nfor the same ranked results',555,375,630,96,30,C.ink);
 rule(s,64,498,1152);
 text(s,'Conditional RRF gain',64,537,442,87,38,C.coral,true);
 text(s,'A small advantage at deeper inputs\nunder the judge’s pseudo-labels',555,535,630,101,30,C.ink);
}
// 13. Denominator details for technical questions.
{
 const s=slide('NDCG@10 and aggregation rules','Appendix A',
 'В расчёте используется бинарная релевантность. DCG@10 суммирует релевантности с логарифмическим дисконтированием позиции. IDCG@10 строится из всех положительных оценок пула, а не только из найденных системой документов. Для одного запроса и набора меток IDCG одинаков для всех сравниваемых систем. Если положительных оценок в пуле нет, NDCG задаётся равным нулю. Такие запросы не исключаются из среднего. Неразмеченные документы сохраняют позиции и получают нулевой вклад. В ручной части различия проверены парным бутстрэпом по запросам и sign-flip тестом. Полный набор использует те же принципы агрегации.',0,sources.paper,true);
 text(s,'NDCG@10 = DCG@10 / IDCG@10',64,205,1150,79,48,C.teal,true);
 table(s,[['Rule','Definition'],['Ideal ranking','All positives in the query’s candidate pool'],['No positive judgments','NDCG = 0, query remains in the mean'],['Unjudged passage','Zero gain, original rank retained'],['Aggregation','Same query set for every system']],[335,817],64,313,284,{size:25,rowHeights:[48,59,59,59,59]});
 text(s,'Manual uncertainty: 5,000 bootstrap resamples and 10,000 paired sign flips.',64,620,1150,34,23,C.muted);
}
// 14. Training and evidence boundaries.
{
 const s=slide('Judge training and held-out evaluation','Appendix B',
 'Разбиение выполняется по запросам, чтобы пары одного запроса не попадали одновременно в обучающую и тестовую части. Использованы 825 обучающих, 177 валидационных и 177 тестовых запросов. После двух эпох дообучения порог выбирается на валидации. Значение примерно минус 0,2187 относится к сырому выходному баллу модели, а не к вероятности. Дополнительная проверка с переранжированием полного ручного пула на 177 тестовых запросах даёт NDCG@10 0,512 под исходными метками и 0,938 под человеческими. Это условное переранжирование заранее обогащённого пула. Его нельзя трактовать как качество первоначального поиска по всему корпусу или доказательство превосходства над всеми генераторами кандидатов.',0,sources.paper+'\n'+sources.judge,true);
 table(s,[['Split by query','Queries','Pairs'],['Train','825','23,543'],['Validation','177','5,122'],['Test','177','5,002']],[502,270,380],64,207,266,{size:27,rowHeights:[55,70,70,71],emphasis:[[3,1],[3,2]]});
 text(s,'MiniLM-L6 cross-encoder, 2 epochs\nValidation-selected raw-score threshold: −0.2187',64,508,1150,89,28,C.ink);
 text(s,'Held-out pool reranking: NDCG@10 = 0.512 (original), 0.938 (human).',64,620,1150,34,23,C.muted);
}
// 15. Sensitivity uses source values rather than copied rounded prose.
{
 const ex=f.populations.excluding_manual_queries.depths;
 const delta=d=>d.models.rrf_variable.ndcg10_mean_all_queries-d.models.e5.ndcg10_mean_all_queries;
 const s=slide('Sensitivity to query selection','Appendix C',
 'Ручной анализ повторён после исключения 23 запросов с нестандартными значениями меток или отсутствующим текстом кандидата. На оставшихся 1156 запросах порядок систем сохраняется, а округлённые оценки почти не меняются. Для большого эксперимента отдельно исключены все 1179 запросов ручной части. На оставшихся 99914 запросах знак разницы RRF и E5 сохраняется как на глубине 10, так и на глубине 200. Это снижает влияние пересечения ручной и автоматической частей, но не превращает псевдоразметку в независимую человеческую оценку. Также возможны общие смещения одного и того же судьи.',0,sources.paper,true);
 table(s,[['Human NDCG@10','All 1,179','Clean 1,156'],...models.map((k,i)=>[modelLabels[i],fmt(m.metrics[k].human),fmt(m.metrics[k].clean_queries_human)])],[550,301,301],64,193,284,{size:25,rowHeights:[48,59,59,59,59]});
 text(s,'After excluding all manual queries: 99,914 queries',64,510,1150,41,30,C.ink,true);
 text(s,`RRF minus E5: ${fmt(delta(ex[0]))} at K = 10, +${fmt(delta(ex[4]))} at K = 200`,64,567,1150,44,29,C.teal);
 text(s,'Pseudo-label dependence remains after this exclusion.',64,627,1150,30,23,C.muted);
}
// 16. Concise academic references, with the complete identifiers in notes.
{
 const s=slide('Selected references','Appendix D',
 'Основные источники для вопросов о коллекции, способах поиска, RRF и архитектуре судьи. Неполные релевантностные оценки и пулинг являются давно известной проблемой информационного поиска. Вклад данной работы состоит в экспериментальной оценке конкретной доразметки и явном контроле условий сравнения. Полные ссылки и дополнительные источники приведены в статье.',0,[sources.marco,sources.models,sources.rrf,sources.judge].join('\n\n'),true);
 const entries=[['MS MARCO','Bajaj et al., 2016. arXiv:1611.09268'],['BM25','Robertson and Zaragoza, 2009. BM25 and Beyond'],['E5 and BGE','Wang et al., 2022. E5\nBAAI/bge-small-en-v1.5 model card'],['Rank fusion','Cormack, Clarke and Buttcher, 2009. SIGIR'],['Cross-encoder judge','Nogueira and Cho, 2019. Passage Re-ranking with BERT\ncross-encoder/ms-marco-MiniLM-L6-v2']];
 let y=195;
 for(const [label,detail] of entries) {text(s,label,64,y,300,66,27,C.teal,true);text(s,detail,403,y,813,73,25,C.ink);if(y<535)rule(s,64,y+78,1152);y+=91;}
}

await fs.mkdir(path.join(BUILD,'render'),{recursive:true});
await fs.mkdir(OUT,{recursive:true});
const snapshot={manual:m,full:f,source_sha256:{}};
for(const name of ['manual_summary.json','fullset_summary.json']) snapshot.source_sha256[name]=createHash('sha256').update(await fs.readFile(path.join(ROOT,'revision_2026/results',name))).digest('hex');
await fs.writeFile(path.join(BUILD,'data_snapshot.json'),JSON.stringify(snapshot,null,2));
await fs.writeFile(path.join(BUILD,'speaker_script.json'),JSON.stringify(script,null,2));
for(let i=0;i<pres.slides.items.length;i++) {
 const s=pres.slides.items[i];
 const png=await pres.export({slide:s,format:'png',scale:1.2});
 await fs.writeFile(path.join(BUILD,'render',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
 const layout=await s.export({format:'layout'});
 await fs.writeFile(path.join(BUILD,'render',`slide-${String(i+1).padStart(2,'0')}.json`),await layout.text());
 console.log(`Rendered ${i+1}/${pres.slides.items.length}`);
}
const candidate=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidate);
const stamped=execFileSync(PYTHON,[path.join(BUILD,'stamp_pptx.py'),candidate],{encoding:'utf8'}).trim();
const finalPath=path.join(OUT,process.env.DECK_FILENAME??'DAMDID_2026___REMOVED_IDENTIFIER__.pptx');
const receipt=await finalizePresentation({
 workspaceDir:ROOT,candidatePath:stamped,finalPath,pythonExecutable:PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:chartOwners,
 materializeLiteralChartWorkbooks:true,
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(BUILD,`${path.basename(finalPath)}.validation.json`),
});
console.log(JSON.stringify({finalPath,slides:pres.slides.items.length,mainSeconds:script.reduce((a,b)=>a+b.seconds,0),chartOwners,tableOwners,receipt},null,2));
