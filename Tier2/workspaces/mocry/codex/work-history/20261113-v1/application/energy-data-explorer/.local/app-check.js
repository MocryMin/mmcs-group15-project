
/* Daily data explorer. Canvas rendering; no network requests or model inference. */
(()=>{
 'use strict';
 const source=JSON.parse(document.getElementById('mmcs-data').textContent),rows=source.rows;
 const $=id=>document.getElementById(id),DAY=86400000,HALF=DAY/2;
 const dates=rows.map(r=>r[0]),times=dates.map(d=>Date.parse(d+'T00:00:00Z'));
 const power=i=>rows.map(r=>r[i]===null?null:r[i]/1000);
 const generation=power(1),demand=power(2),price=rows.map(r=>r[3]),gap=generation.map((v,i)=>v-demand[i]);
 const colors={course:'#f2f4f8',nd:'#22d3ee',tsd:'#34d399',ndf:'#fb7185',tsdf:'#facc15',cardinal:'#e879f9',generation:'#4d8bd5',price:'#b39ddb',positive:'#39b598',negative:'#de7b78'};
 const compare={course:{name:'课程需求 VD',values:demand},nd:{name:'NESO 实际 ND',values:power(7)},tsd:{name:'NESO 实际 TSD',values:power(8)},ndf:{name:'NESO 预测 ND',values:power(9)},tsdf:{name:'NESO 预测 TSD',values:power(10)},cardinal:{name:'原实验 ND 特征点均值',values:power(11)}};
 const boxes=Object.fromEntries([...document.querySelectorAll('[data-series]')].map(x=>[x.dataset.series,x]));
 const MIN=times[0],MAX=times.at(-1),fmt=[2,3].reduce((o,n)=>(o[n]=new Intl.NumberFormat('en-GB',{minimumFractionDigits:n,maximumFractionDigits:n}),o),{});
 const dateString=t=>new Date(t).toISOString().slice(0,10),toMs=v=>typeof v==='number'?v:Date.parse(String(v).slice(0,10)+'T00:00:00Z');
 const splits={train:['2022-01-01','2024-12-31'],validation:['2025-01-01','2025-08-31'],test:['2025-09-01','2026-08-31']};
 const state={lo:toMs(splits.test[0])-HALF,hi:toMs(splits.test[1])+HALF,first:0,last:0,autoY:true,ma:0,mode:'lines',bands:false,quality:false,dragmode:'pan',view:'comparison'};
 const host=$('chart'),chart=echarts.init(host,null,{renderer:'canvas',devicePixelRatio:Math.min(devicePixelRatio||1,2)});
 let frame=0,quoteFrame=0,pendingQuote=0,lastQuote=-1,pendingRange=null,selection=null;
 const maCache=new Map(),pairs=v=>v.map((x,i)=>[times[i],x]);
 function lowerBound(value){let a=0,b=times.length;while(a<b){const m=(a+b)>>1;if(times[m]<value)a=m+1;else b=m;}return a;}
 function indices(lo,hi){return [Math.max(0,Math.min(rows.length-1,lowerBound(lo))),Math.max(0,Math.min(rows.length-1,lowerBound(hi+1)-1))];}
 function showQuote(i){if(i===lastQuote)return;lastQuote=i;
  $('qdate').textContent=dates[i];$('qg').textContent=fmt[3].format(generation[i]);$('qd').textContent=fmt[3].format(demand[i]);$('qp').textContent=fmt[2].format(price[i]);$('qgap').textContent=(gap[i]>0?'+':'')+fmt[3].format(gap[i]);$('qgap').style.color=gap[i]>=0?colors.positive:colors.negative;
  for(const [id,key]of[['qnd','nd'],['qtsd','tsd'],['qndf','ndf'],['qtsdf','tsdf']]){const v=compare[key].values[i];$(id).textContent=v===null?'缺失':fmt[3].format(v)+' GW';}
  $('qforecastCoverage').textContent=`预测覆盖 ND ${rows[i][12]}/48 · TSD ${rows[i][13]}/48${rows[i][14]?' · 最近发布 '+rows[i][14]:''}`;
  $('qquality').textContent=rows[i][6]?'当日未标记估算/插值':'当日含估算/插值修复';
 }
 function currentRangeUI(){[state.first,state.last]=indices(state.lo,state.hi);$('from').value=dates[state.first];$('to').value=dates[state.last];$('status').textContent=`${dates[state.first]} — ${dates[state.last]} · ${state.last-state.first+1} 天`;
  for(const b of document.querySelectorAll('[data-split]')){const s=splits[b.dataset.split];b.classList.toggle('active',dates[state.first]===s[0]&&dates[state.last]===s[1]);}$('error').textContent='';$('year').value='';showQuote(state.last);
 }
 function normalizedRange(lo,hi){if(!Number.isFinite(lo)||!Number.isFinite(hi)||lo>hi)return null;lo=Math.max(MIN-HALF,lo);hi=Math.min(MAX+HALF,hi);if(hi-lo<DAY){const m=(lo+hi)/2;lo=Math.max(MIN-HALF,m-HALF);hi=Math.min(MAX+HALF,lo+DAY);lo=Math.max(MIN-HALF,hi-DAY);}return [lo,hi];}
 function applyRange(lo,hi){const r=normalizedRange(lo,hi);if(!r){$('error').textContent='请选择有效的日期区间，开始日期应不晚于结束日期。';return false;}state.lo=r[0];state.hi=r[1];chart.dispatchAction({type:'dataZoom',startValue:state.lo,endValue:state.hi});currentRangeUI();return true;}
 function queueRange(lo,hi){pendingRange=[lo,hi];if(!frame)frame=requestAnimationFrame(()=>{frame=0;const r=pendingRange;pendingRange=null;applyRange(...r);});}
 function averages(){if(!state.ma)return null;if(!maCache.has(state.ma)){const n=state.ma;maCache.set(n,[generation,demand,price].map(v=>{let sum=0;return v.map((x,i)=>{sum+=x;if(i>=n)sum-=v[i-n];return i>=n-1?sum/n:null;});}));}return maCache.get(state.ma);}
 function extent(values,zero=false){let lo=zero?0:Infinity,hi=zero?0:-Infinity;for(const x of values)if(Number.isFinite(x)){lo=Math.min(lo,x);hi=Math.max(hi,x);}if(!Number.isFinite(lo))return[0,1];const pad=Math.max((hi-lo)*.1,Math.abs(hi)*.005,.05);return[lo-pad,hi+pad];}
 function allExtents(){const a=[];if(state.view==='overview')a.push(...generation);for(const[k,c]of Object.entries(compare))if(boxes[k].checked)a.push(...c.values);return[extent(a),extent(gap,true),extent(price),[-1,1]];}
 function markAreas(){if(!state.bands)return undefined;return{silent:true,itemStyle:{opacity:.055},data:Object.entries(splits).map(([name,d],i)=>[{name,xAxis:toMs(d[0])-HALF,itemStyle:{color:['#55b7ef','#f5b65c','#c19bff'][i]}},{xAxis:toMs(d[1])+HALF}])};}
 function line(id,name,v,color,axis=0,dashed=false){return{id,name,type:'line',data:pairs(v),xAxisIndex:axis,yAxisIndex:axis,animation:false,showSymbol:state.mode!=='lines',showAllSymbol:true,symbolSize:state.mode==='markers'?4:3,lineStyle:{color,width:state.mode==='markers'?0:1.3,type:dashed?'dashed':'solid'},itemStyle:{color},connectNulls:false,emphasis:{disabled:true},clip:true};}
 function option(){const overview=state.view==='overview',a=averages(),series=[];
  series.push(line('generation','供给',generation,colors.generation));
  for(const[k,c]of Object.entries(compare))series.push(line(k,c.name,c.values,colors[k],0,['ndf','tsdf','cardinal'].includes(k)));
  series.push({id:'gap',name:'供需差',type:'bar',xAxisIndex:1,yAxisIndex:1,data:gap.map((v,i)=>({value:[times[i],v],itemStyle:{color:v>=0?colors.positive:colors.negative}})),barMaxWidth:8,animation:false,emphasis:{disabled:true}});
  series.push(line('price','电价',price,colors.price,2));
  if(a){for(const[j,id,name,color,axis]of[[0,'gma','供给均线',colors.generation,0],[1,'dma','需求均线',colors.course,0],[2,'pma','电价均线',colors.price,2]])series.push({...line(id,name,a[j],color,axis),showSymbol:false,lineStyle:{color,width:2.5}});}
  series.push({id:'quality',name:'估算/插值日',type:'scatter',xAxisIndex:3,yAxisIndex:3,data:rows.flatMap((r,i)=>r[6]?[]:[[times[i],0]]),symbol:'triangle',symbolSize:5,itemStyle:{color:'#91a5bd'},animation:false});
  if(state.bands){const area=markAreas();for(let i=0;i<3;i++)series.push({id:'bands'+i,name:'划分'+i,type:'line',xAxisIndex:i,yAxisIndex:i,data:[],markArea:area,silent:true,animation:false});}
  const selected={'供给':overview,'供需差':overview,'电价':overview,'供给均线':overview,'需求均线':boxes.course.checked,'电价均线':overview,'估算/插值日':state.quality};for(const[k,c]of Object.entries(compare))selected[c.name]=boxes[k].checked;
  const grids=overview?[{top:'8%',height:'36%'},{top:'49%',height:'12%'},{top:'67%',height:'19%'},{top:'88%',height:'2%'}]:[{top:'8%',height:'76%'},{top:'88%',height:0},{top:'88%',height:0},{top:'87%',height:'2%'}];
  const grid=grids.map(x=>({...x,left:60,right:24,containLabel:false}));const bounds=allExtents();
  const axes=grid.map((g,i)=>({type:'time',gridIndex:i,min:MIN-HALF,max:MAX+HALF,show:overview?i===2:i===0,axisLabel:{color:'#a9bad0',hideOverlap:true,formatter:value=>dateString(value),fontSize:11},axisLine:{lineStyle:{color:'#34465f'}},axisTick:{show:false},splitLine:{show:true,lineStyle:{color:'#202c3e'}},axisPointer:{show:true,label:{formatter:p=>dateString(p.value)}}}));
  const yAxis=grid.map((g,i)=>({type:'value',gridIndex:i,scale:true,show:i===0||(overview&&i<3),min:state.autoY?(i===3?-1:undefined):bounds[i][0],max:state.autoY?(i===3?1:undefined):bounds[i][1],name:i===2?'£/MWh':i===3?'':'GW',nameTextStyle:{color:'#a9bad0'},axisLabel:{color:'#a9bad0',fontSize:11},axisLine:{show:false},axisTick:{show:false},splitLine:{show:i<3,lineStyle:{color:'#202c3e'}}}));
  const title=[{text:overview?'供给 / 需求与官方预测 · GW':'日均需求与日初可得官方预测 · GW · 同一 UTC 日期',left:60,top:0,textStyle:{color:'#c4d2e5',fontSize:12,fontWeight:400}}];if(overview)title.push({text:'供需差 · GW',left:60,top:'45%',textStyle:{color:'#aebed2',fontSize:11,fontWeight:400}},{text:'日均电价 · £/MWh',left:60,top:'63%',textStyle:{color:'#aebed2',fontSize:11,fontWeight:400}});
  return{animation:false,useUTC:true,backgroundColor:'#0d131e',textStyle:{fontFamily:'Segoe UI, Microsoft YaHei, sans-serif'},title,grid,xAxis:axes,yAxis,series,legend:{show:false,selected},axisPointer:{link:[{xAxisIndex:'all'}],label:{backgroundColor:'#1c2a3f'}},tooltip:{trigger:'axis',confine:true,animation:false,backgroundColor:'#1c2a3f',borderColor:'#4b607d',textStyle:{color:'#eef4fd',fontSize:12},formatter:params=>{const a=params.filter(x=>x.seriesId!=='quality'&&!x.seriesId.startsWith('bands'));return a.length?dateString(a[0].value[0])+'<br>'+a.map(x=>x.marker+x.seriesName+' '+(x.value[1]===null?'缺失':fmt[x.seriesId==='price'||x.seriesId==='pma'?2:3].format(x.value[1]))+(x.seriesId==='price'||x.seriesId==='pma'?' £/MWh':' GW')).join('<br>'):'';}},dataZoom:[{id:'inside',type:'inside',xAxisIndex:[0,1,2,3],filterMode:'filter',startValue:state.lo,endValue:state.hi,minValueSpan:DAY,zoomOnMouseWheel:true,moveOnMouseWheel:false,moveOnMouseMove:state.dragmode==='pan',preventDefaultMouseMove:true,throttle:32},{id:'slider',type:'slider',xAxisIndex:[0,1,2,3],filterMode:'filter',startValue:state.lo,endValue:state.hi,minValueSpan:DAY,bottom:7,height:36,left:60,right:24,showDetail:false,borderColor:'#34465f',backgroundColor:'#172235',fillerColor:'rgba(135,171,205,.16)',dataBackground:{lineStyle:{color:'#5d9ca6',width:1},areaStyle:{color:'#5d9ca6',opacity:.1}},selectedDataBackground:{lineStyle:{color:'#8dc9cf'},areaStyle:{color:'#6eb3b9',opacity:.15}},handleStyle:{color:'#a9bad0',borderWidth:0},moveHandleSize:0,throttle:32}],toolbox:{show:false}};
 }
 function render(){document.body.classList.toggle('comparison',state.view==='comparison');chart.setOption(option(),{notMerge:true,lazyUpdate:false,silent:true});currentRangeUI();}
 function saveChoices(){try{localStorage.setItem('mmcs-explorer-v2',JSON.stringify({series:Object.fromEntries(Object.entries(boxes).map(([k,b])=>[k,b.checked]))}));}catch{}}
 for(const[k,b]of Object.entries(boxes)){b.nextElementSibling.style.setProperty('--series',colors[k]);b.addEventListener('change',()=>{chart.dispatchAction({type:b.checked?'legendSelect':'legendUnSelect',name:compare[k].name});if(k==='course'&&state.ma)chart.dispatchAction({type:b.checked?'legendSelect':'legendUnSelect',name:'需求均线'});saveChoices();});}
 try{const saved=JSON.parse(localStorage.getItem('mmcs-explorer-v2')||'null');for(const[k,v]of Object.entries(saved?.series||{}))if(boxes[k])boxes[k].checked=!!v;}catch{}
 chart.on('datazoom',()=>{const z=chart.getOption().dataZoom[0];const r=normalizedRange(Number(z.startValue),Number(z.endValue));if(r){state.lo=r[0];state.hi=r[1];currentRangeUI();}});
 chart.on('updateAxisPointer',event=>{const value=event.axesInfo?.[0]?.value;if(value===undefined)return;let i=lowerBound(value);if(i>=rows.length)i=rows.length-1;if(i>0&&Math.abs(times[i-1]-value)<Math.abs(times[i]-value))i--;pendingQuote=i;if(!quoteFrame)quoteFrame=requestAnimationFrame(()=>{quoteFrame=0;showQuote(pendingQuote);});});
 const resize=new ResizeObserver(()=>{chart.resize({animation:{duration:0}});});resize.observe(host);
 host.addEventListener('dblclick',()=>applyRange(MIN-HALF,MAX+HALF));
 // Box selection is handled once at pointer-up, without re-rendering while dragging.
 host.style.position='relative';
 host.addEventListener('pointerdown',e=>{if(state.dragmode!=='zoom'||e.button!==0)return;const rect=host.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;if(x<60||x>rect.width-24||y<rect.height*.08||y>rect.height*.87)return;
  e.preventDefault();e.stopPropagation();const box=document.createElement('div');Object.assign(box.style,{position:'absolute',pointerEvents:'none',zIndex:'10',border:'1px solid #a9bad0',background:'rgba(135,171,205,.15)',left:x+'px',top:y+'px'});host.appendChild(box);selection={x,y,box,rect,id:e.pointerId};host.setPointerCapture(e.pointerId);
 },true);
 host.addEventListener('pointermove',e=>{if(!selection)return;e.preventDefault();const s=selection,x=Math.max(60,Math.min(s.rect.width-24,e.clientX-s.rect.left)),y=Math.max(s.rect.height*.08,Math.min(s.rect.height*.87,e.clientY-s.rect.top));Object.assign(s.box.style,{left:Math.min(s.x,x)+'px',top:Math.min(s.y,y)+'px',width:Math.abs(s.x-x)+'px',height:Math.abs(s.y-y)+'px'});},true);
 host.addEventListener('pointerup',e=>{if(!selection)return;e.preventDefault();e.stopPropagation();const s=selection;selection=null;s.box.remove();const x=Math.max(60,Math.min(s.rect.width-24,e.clientX-s.rect.left));if(Math.abs(x-s.x)>4){const a=chart.convertFromPixel({xAxisIndex:0},Math.min(x,s.x)),b=chart.convertFromPixel({xAxisIndex:0},Math.max(x,s.x));queueRange(a,b);}if(host.hasPointerCapture(e.pointerId))host.releasePointerCapture(e.pointerId);},true);
 host.addEventListener('pointercancel',()=>{if(selection){selection.box.remove();selection=null;}},true);
 $('coverage').textContent=`数据范围 ${dates[0]} — ${dates.at(-1)} · ${rows.length.toLocaleString()} 个日观测 · 默认显示测试年份`;
 for(const e of[$('from'),$('to')]){e.min=dates[0];e.max=dates.at(-1);e.addEventListener('keydown',x=>{if(x.key==='Enter')$('apply').click();});}
 for(let y=Number(dates[0].slice(0,4));y<=Number(dates.at(-1).slice(0,4));y++)$('year').add(new Option(String(y),String(y)));
 for(const b of document.querySelectorAll('[data-days]'))b.onclick=()=>{const last=times[state.last];applyRange(last-(Number(b.dataset.days)-1)*DAY-HALF,last+HALF);};
 for(const b of document.querySelectorAll('[data-split]'))b.onclick=()=>applyRange(toMs(splits[b.dataset.split][0])-HALF,toMs(splits[b.dataset.split][1])+HALF);
 $('all').onclick=()=>applyRange(MIN-HALF,MAX+HALF);$('default').onclick=()=>applyRange(toMs(splits.test[0])-HALF,toMs(splits.test[1])+HALF);
 $('apply').onclick=()=>{const a=toMs($('from').value),b=toMs($('to').value);if(!Number.isFinite(a)||!Number.isFinite(b)||a>b||a<MIN||b>MAX){$('error').textContent=`请选择 ${dates[0]} 至 ${dates.at(-1)} 内的有效日期。`;return;}applyRange(a-HALF,b+HALF);};
 $('year').onchange=()=>{const y=$('year').value;if(y)applyRange(Math.max(MIN,toMs(y+'-01-01'))-HALF,Math.min(MAX,toMs(y+'-12-31'))+HALF);};
 $('view').onchange=()=>{state.view=$('view').value;render();};$('mode').value=state.mode;$('mode').onchange=()=>{state.mode=$('mode').value;render();};
 $('ma').onchange=()=>{state.ma=Number($('ma').value);render();};$('autoY').onchange=()=>{state.autoY=$('autoY').checked;render();};$('splitBands').onchange=()=>{state.bands=$('splitBands').checked;render();};$('qualityMarks').onchange=()=>{state.quality=$('qualityMarks').checked;chart.dispatchAction({type:state.quality?'legendSelect':'legendUnSelect',name:'估算/插值日'});};
 function dragMode(mode){state.dragmode=mode;$('pan').setAttribute('aria-pressed',String(mode==='pan'));$('zoom').setAttribute('aria-pressed',String(mode==='zoom'));host.style.cursor=mode==='zoom'?'crosshair':'default';chart.setOption({dataZoom:[{id:'inside',moveOnMouseMove:mode==='pan'}]});}
 $('pan').onclick=()=>dragMode('pan');$('zoom').onclick=()=>dragMode('zoom');
 function download(url,name){const a=document.createElement('a');a.href=url;a.download=name;a.click();}
 $('csv').onclick=()=>{const content='\uFEFF'+source.metadata.column_order.join(',')+'\r\n'+rows.slice(state.first,state.last+1).map(r=>r.map((v,i)=>i===6?(v?'True':'False'):(v===null?'':v)).join(',')).join('\r\n');const url=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8;'}));download(url,`MMCS_${dates[state.first]}_${dates[state.last]}.csv`);setTimeout(()=>URL.revokeObjectURL(url),1000);};
 $('png').onclick=()=>download(chart.getDataURL({type:'png',pixelRatio:2,backgroundColor:'#0d131e'}),`MMCS_${dates[state.first]}_${dates[state.last]}.png`);
 $('forecastCoverage').textContent=`全部 ${rows.length} 天：实际 ND / TSD ${source.metadata.coverage.ND_actual} / ${source.metadata.coverage.TSD_actual} 天；完整预测 ND / TSD ${source.metadata.coverage.ND_forecast} / ${source.metadata.coverage.TSD_forecast} 天。缺失区间显示断线。`;
 $('appVersion').textContent=`应用版本 ${source.metadata.version} · 数据生成 ${source.metadata.updated_at} · 预测采集 ${source.metadata.forecast_retrieved_at}`;
 render();window.MMCS_VIEW={ready:true,source:source.metadata,renderer:'canvas',chart,colors,getState:()=>({...state,firstDate:dates[state.first],lastDate:dates[state.last],count:state.last-state.first+1}),setDates:async(a,b)=>applyRange(toMs(a)-HALF,toMs(b)+HALF),getVisibleRows:()=>rows.slice(state.first,state.last+1),getComparison:()=>Object.fromEntries(Object.keys(compare).map(k=>[k,{name:compare[k].name,checked:boxes[k].checked,color:colors[k]}])),resetDefault:()=>applyRange(toMs(splits.test[0])-HALF,toMs(splits.test[1])+HALF)};
})();

