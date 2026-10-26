import {slide,chart,nativeTable,series,axis,grid,C,m,exportDraft} from './layout.mjs';
const s=slide('Manual NDCG@10','Probe',60);
chart(s,'bar',{position:{left:64,top:182,width:1152,height:420},categories:['BM25','E5','BGE','RRF (3)'],series:[series('Original',['bm25','e5','bge','rrf3'].map(k=>m.metrics[k].official),C.gray),series('Human',['bm25','e5','bge','rrf3'].map(k=>m.metrics[k].human),C.teal)],barOptions:{direction:'bar',grouping:'clustered',gapWidth:130},xAxis:{...axis,min:0,max:1,majorUnit:0.2,majorGridlines:grid,numberFormatCode:'0.0'},yAxis:{...axis,majorGridlines:null},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:24,fill:C.ink}}});
const t=slide('Table styling','Probe',60);
nativeTable(t,[['Passage','Original','Human'],['Salt raises the boiling point','Relevant','Relevant'],['Non-volatile solute','Unjudged','Relevant'],['Temperature of acetone','Unjudged','Not relevant']],[620,266,266],64,200,[64,90,90,90],{emphasis:[[2,2]]});
console.log(await exportDraft('probe'));
