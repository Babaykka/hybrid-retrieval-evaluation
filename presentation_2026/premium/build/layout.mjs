import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

export const ROOT=(process.env.PROJECT_ROOT||process.cwd());
export const BUILD=path.join(ROOT,'presentation_2026/premium/build');
export const OUT=path.join(ROOT,'Презентация_DAMDID_Новая');
export const SKILL=(process.env.PRESENTATIONS_SKILL||'');
export const PY=(process.env.PYTHON||'python3');
process.env.RUNTIME_NODE_MODULES=(process.env.RUNTIME_NODE_MODULES||'');
const util=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
export const FONT=util.resolvePresentationFont({fontFamily:'Arial'});
export const C={ink:'#182B30',teal:'#007F78',mint:'#8ACEC4',coral:'#C95236',muted:'#526970',gray:'#70858A',pale:'#EFF5F4',rule:'#D4E1E0',white:'#FFFFFF',dark:'#182326'};
export const pres=Presentation.create({slideSize:{width:1280,height:720}});
export const charts=[],tables=[],notes=[];
export const m=JSON.parse(await fs.readFile(path.join(ROOT,'revision_2026/results/manual_summary.json'),'utf8'));
export const f=JSON.parse(await fs.readFile(path.join(ROOT,'revision_2026/results/fullset_summary.json'),'utf8'));
export const d=f.populations.all_queries.depths;
export const fmt=(x,n=3)=>Number(x).toFixed(n);

export function txt(s,v,x,y,w,h,size=28,{color=C.ink,bold=false,align='left',...rest}={}) {
 const shape=s.shapes.add({geometry:'textbox',name:String(v).slice(0,48),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=v;shape.text.style={typeface:FONT,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:{top:0,right:0,bottom:0,left:0},...rest};return shape;
}
export function rule(s,x,y,w,color=C.rule,weight=1.2) {return s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:0},fill:'none',line:{fill:color,width:weight}});}
export function slide(title,note,sec=60,{dark=false,backup=false,source='Study data and corrected pool-based analysis, __REMOVED_IDENTIFIER__, __REMOVED_IDENTIFIER__ and __REMOVED_IDENTIFIER__, DAMDID 2026.'}={}) {
 const s=pres.slides.add();const n=pres.slides.items.length;s.background.fill=dark?C.dark:C.white;
 if(title)txt(s,title,64,48,1152,119,46,{bold:true,color:dark?C.white:C.ink});
 txt(s,backup?'APPENDIX '+String.fromCharCode(65+notes.filter(v=>v.backup).length):String(n).padStart(2,'0'),1104,681,112,22,15,{color:dark?'#B3C7C9':C.muted,align:'right'});
 const item={slide:n,title,seconds:backup?0:sec,note,source,backup};notes.push(item);
 s.speakerNotes.textFrame.setText(`${backup?'Резервный слайд':`Ориентир: ${sec} секунд`}.\n\n${note}\n\nИсточники:\n${source}`);return s;
}
export function foot(s,v,{dark=false}={}) {return txt(s,v,64,642,1135,38,21,{color:dark?'#BDCECE':C.muted});}
export function nativeTable(s,values,widths,x,y,rowHeights,{size=25,header=true,emphasis=[],numericCols=[]}={}) {
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height:rowHeights.reduce((a,b)=>a+b,0),columnWidths:widths,values});
 t.styleOptions={headerRow:false,bandedRows:false,bandedColumns:false};
 t.borders.assign({fill:C.rule,width:0.7});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({borders:{top:{width:0,color:C.white},bottom:{width:0.8,color:C.rule},left:{width:0,color:C.white},right:{width:0,color:C.white}}});
 for(let r=0;r<values.length;r++){t.rows[r].height=rowHeights[r];for(let c=0;c<values[r].length;c++){const cl=t.getCell(r,c);cl.fill=r===0&&header?C.pale:C.white;cl.text.style={typeface:FONT,fontSize:size-(r===0&&header?2:0),color:r===0&&header?C.muted:C.ink,bold:r===0&&header,verticalAlignment:'middle',autoFit:'none',insets:{left:18,right:18,top:10,bottom:10}};}}
 for(const [r,c]of emphasis){t.getCell(r,c).fill='#E4F2ED';t.getCell(r,c).text.style={typeface:FONT,fontSize:size,bold:true,color:C.teal};}
 for(let r=1;r<values.length;r++)for(const c of numericCols)t.getCell(r,c).text.style={typeface:FONT,fontSize:size,color:C.ink,alignment:'right',verticalAlignment:'middle',autoFit:'none',insets:{left:18,right:18,top:10,bottom:10}};
 tables.push(pres.slides.items.length);return t;
}
export const axis={textStyle:{typeface:FONT,fontSize:23,fill:C.muted},line:{fill:C.rule,width:1}};
export const grid={fill:C.rule,width:1};
export const series=(name,values,color,rest={})=>({name,values,fill:color,line:{fill:color,width:3},valuesFormatCode:'0.000',...rest});
export function chart(s,type,conf){
 conf.series=conf.series.map(v=>({...v,values:v.values.map(x=>Number(x.toFixed(8))),...(v.xValues?{xValues:v.xValues.map(x=>Number(x.toFixed(8)))}:{})}));
 if(type==='bar')conf.series=conf.series.map(v=>({...v,line:{fill:'none',width:0}}));
 const ch=s.charts.add(type,{chartFill:C.white,plotAreaFill:C.white,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{typeface:FONT,fontSize:24,fill:C.ink}},...conf});
 util.applyPresentationChartFont(ch,{fontFamily:FONT});charts.push(pres.slides.items.length);return ch;
}
export function box(s,label,x,y,w,h,{fill=C.pale,color=C.ink,size=28,bold=false}={}){
 const sh=s.shapes.add({geometry:'rect',name:label,position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.rule,width:1.2}});
 sh.text=label;sh.text.style={typeface:FONT,fontSize:size,bold,color,alignment:'center',verticalAlignment:'middle',autoFit:'none',insets:{left:14,right:14,top:12,bottom:12}};return sh;
}
export function connect(s,a,b,{from='right',to='left',kind='straight',color=C.muted}={}){return s.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:color,width:3},tail:{type:'triangle',width:'med',length:'med'}});}
export async function exportDraft(name='candidate'){
 await fs.mkdir(path.join(BUILD,'render'),{recursive:true});
 for(let i=0;i<pres.slides.items.length;i++){const s=pres.slides.items[i];const b=await pres.export({slide:s,format:'png',scale:1.2});await fs.writeFile(path.join(BUILD,'render',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));const layout=await s.export({format:'layout'});await fs.writeFile(path.join(BUILD,'render',`slide-${String(i+1).padStart(2,'0')}.json`),await layout.text());}
 await fs.writeFile(path.join(BUILD,'speaker_script.json'),JSON.stringify(notes,null,2));
 const output=path.join(BUILD,`${name}.pptx`);await (await PresentationFile.exportPptx(pres)).save(output);return output;
}
export {util};
