import fs from 'node:fs/promises';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
const B='./presentation_2026/review_2026-10-12/build';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#182B30',teal:'#007F78',muted:'#526970',rule:'#D4E1E0',pale:'#EFF5F5',mint:'#E3F1EF',coral:'#C64F37',white:'#FFFFFF'};
function text(s,t,x,y,w,h,size=28,{color=C.ink,bold=false,align='left'}={}){
 const a=s.shapes.add({geometry:'textbox',name:t.slice(0,70),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};return a;
}
function line(s,x,y,w){s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:0},line:{fill:C.rule,width:1.3},fill:'none'});}
function slide(title,num){const s=p.slides.add();s.background.fill=C.white;text(s,title,64,48,1152,112,43,{bold:true});text(s,num,1104,681,112,22,15,{color:C.muted,align:'right'});return s;}
function foot(s,t){text(s,t,64,642,1152,40,21,{color:C.muted});}
function box(s,t,x,y,w,h,fill=C.pale,size=28){const a=s.shapes.add({geometry:'rect',name:t,position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.rule,width:1.2}});a.text=t;a.text.style={typeface:'Arial',fontSize:size,color:C.ink,alignment:'center',verticalAlignment:'middle',autoFit:'none',insets:{left:16,right:16,top:12,bottom:12}};return a;}
function arrow(s,a,b,from='right',to='left'){return s.shapes.connect(a,b,{kind:'straight',fromSide:from,toSide:to,line:{fill:C.muted,width:2.5},tail:{type:'triangle',width:'med',length:'med'}});}
// Replacement for the original data slide: only human annotation at this point.
{
 const s=slide('Данные для ручной доразметки','05');
 text(s,'MS MARCO Passage Ranking: 8 841 823 англоязычных фрагмента',64,169,1152,48,28,{color:C.muted});
 text(s,'dev/small',64,260,480,45,30,{bold:true});
 text(s,'6 980',64,311,460,81,66,{color:C.teal,bold:true});
 text(s,'запросов в стандартной\nоценочной подвыборке',64,404,480,80,28);
 text(s,'7 437 исходных положительных пар',64,525,500,70,26,{color:C.muted});
 text(s,'Ручная подвыборка из dev/small',654,260,562,45,30,{bold:true});
 text(s,'1 179',654,311,460,81,66,{color:C.teal,bold:true});
 text(s,'запросов с дополнительными\nчеловеческими оценками',654,404,560,80,28);
 text(s,'33 667 пар «запрос – фрагмент»',654,525,562,70,26,{color:C.muted});
 line(s,64,233,1152);
 foot(s,'Доразметка охватывает отобранных кандидатов для каждого запроса.');
}
{
 const s=slide('Полная dev-часть для масштабной оценки','11');
 text(s,'101 093',64,178,620,110,88,{bold:true,color:C.teal});
 text(s,'запроса в queries.dev.tsv',64,300,760,55,35,{bold:true});
 text(s,'MS MARCO Passage Ranking v1',64,363,850,45,28,{color:C.muted});
 line(s,64,432,1152);
 text(s,'Для этих запросов подготовили поисковые выдачи.\nПосле обучения судья оценивает найденные фрагменты.',64,465,1152,94,30);
 foot(s,'101 093 запроса в эксперименте совпадают с полной dev-частью по идентификаторам.');
}
{
 const s=slide('Пулы кандидатов для модели-судьи','12');
 text(s,'K задаёт число результатов от каждого поискового метода',64,162,1152,45,29,{color:C.muted});
 const a=box(s,'BM25\nпервые K',64,235,230,82);
 const b=box(s,'E5\nпервые K',64,333,230,82);
 const c=box(s,'BGE\nпервые K',64,431,230,82);
 const pool=box(s,'Общий пул\nбез дубликатов',382,314,270,120);
 const judge=box(s,'Судья\nMiniLM',725,314,200,120,C.mint);
 const labels=box(s,'Псевдометки\n0 или 1',998,314,218,120,C.mint);
 arrow(s,a,pool);arrow(s,b,pool);arrow(s,c,pool);arrow(s,pool,judge);arrow(s,judge,labels);
 text(s,'K = 10, 30, 50, 100, 200',64,558,680,47,34,{bold:true,color:C.teal});
 foot(s,'Судья и порог −0,2187 фиксированы. Размер пула может быть меньше 3K.');
}
{
 const s=slide('Зачем объединять результаты с помощью RRF','14');
 text(s,'Проверяем, дополняют ли друг друга разные способы поиска',64,161,1152,48,29,{color:C.muted});
 const a=box(s,'BM25',64,242,225,70),b=box(s,'E5',64,327,225,70),c=box(s,'BGE',64,412,225,70);
 const r=box(s,'RRF\nслияние по позициям',391,306,362,130,C.mint,29);
 const out=box(s,'Один итоговый\nсписок фрагментов',861,306,355,130);
 arrow(s,a,r);arrow(s,b,r);arrow(s,c,r);arrow(s,r,out);
 text(s,'RRF(d) = Σ 1 / (60 + rankᵢ(d))',64,526,810,52,35,{bold:true,color:C.teal});
 text(s,'Равный вес трёх источников. Исходные баллы моделей не суммируются.',64,586,1152,44,26);
 foot(s,'Cormack, Clarke, Büttcher, SIGIR 2009. Оценки судьи не входят в формулу RRF.');
}
{
 const s=slide('Литература и ресурсы','19');
 const refs=[
 ['MS MARCO','Bajaj et al., 2016','arxiv.org/abs/1611.09268'],
 ['Natural Questions','Kwiatkowski et al., 2019','aclanthology.org/Q19-1026'],
 ['BEIR','Thakur et al., 2021','arxiv.org/abs/2104.08663'],
 ['BM25','Robertson & Zaragoza, 2009','doi.org/10.1561/1500000019'],
 ['E5','Wang et al., 2022','arxiv.org/abs/2212.03533'],
 ['BGE / FlagEmbedding','Модель bge-small-en-v1.5','huggingface.co/BAAI/bge-small-en-v1.5'],
 ['MiniLM','Wang et al., 2020','arxiv.org/abs/2002.10957'],
 ['Reciprocal Rank Fusion','Cormack et al., 2009','doi.org/10.1145/1571941.1572114']
 ];
 for(let i=0;i<refs.length;i++){const x=i<4?64:674,y=165+(i%4)*112;const [name,author,url]=refs[i];text(s,name,x,y,540,34,28,{bold:true});text(s,author,x,y+35,540,30,23,{color:C.muted});text(s,url,x,y+67,542,29,21,{color:C.teal});}
 foot(s,'Спецификация dev и dev/small: ir-datasets.com/msmarco-passage.html');
}
{
 const s=slide('', '20');
 text(s,'Спасибо за внимание',64,224,1152,94,66,{bold:true});
 text(s,'Вопросы и обсуждение',64,346,1152,52,34,{color:C.teal});
 line(s,64,463,1152);
 text(s,'__REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__',64,499,1152,43,28);
 text(s,'__REMOVED_IDENTIFIER__',64,547,1152,40,26,{color:C.muted});
 foot(s,'Работа поддержана Российским научным фондом, соглашение № __REMOVED_IDENTIFIER__.');
}
{
 const s=slide('Какие части данных мы использовали','РЕЗЕРВ 1');
 const rows=[['Набор','Запросы','Роль в исследовании'],['Полная dev-часть','101 093','Масштабная оценка судьёй'],['dev/small','6 980','Исходная оценочная подвыборка'],['Ручная подвыборка','1 179','Доразметка 33 667 пар'],['Обучение судьи','825','Дообучение на ручных метках'],['Валидация судьи','177','Выбор порога'],['Тест судьи','177','Проверка на отложенных запросах']];
 const t=s.tables.add({rows:rows.length,columns:3,left:64,top:172,width:1152,height:406,columnWidths:[350,200,602],values:rows});
 t.styleOptions={headerRow:false,bandedRows:false};t.borders.assign({fill:C.rule,width:0.7});
 t.cells.block({row:0,column:0,rowCount:rows.length,columnCount:3}).assign({borders:{top:{width:0,color:C.white},bottom:{width:0.8,color:C.rule},left:{width:0,color:C.white},right:{width:0,color:C.white}}});
 for(let r=0;r<rows.length;r++){t.rows[r].height=58;for(let c=0;c<3;c++){const a=t.getCell(r,c);a.fill=r===0?C.pale:C.white;a.text.style={typeface:'Arial',fontSize:r===0?24:25,color:r===0?C.muted:C.ink,bold:r===0,verticalAlignment:'middle',autoFit:'none',insets:{left:12,right:12,top:8,bottom:8}};}}
 foot(s,'Ручная подвыборка входит в dev/small, а dev/small входит в полную dev-часть.');
}
await (await PresentationFile.exportPptx(p)).save(B+'/additions.pptx');
console.log('Exported 7 editable addition/replacement slides');
