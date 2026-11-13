"""One-time migration of the existing GUI, retaining its tested interactions."""
from pathlib import Path
R=Path(__file__).resolve().parent
s=(R/'src-template-original.html').read_text(encoding='utf-8')
def change(a,b):
    global s
    assert a in s,a[:100]
    s=s.replace(a,b,1)
change('<script>__PLOTLY_BUNDLE__</script>','<script src="assets/plotly.min.js"></script>')
change('<title>MMCS 日度数据行情</title>','<title>MMCS Energy Data Explorer · 需求与预测对照</title>')
change('MMCS · 日度数据行情','MMCS · Energy Data Explorer')
change('冻结修复数据 · 与预测实验一致','v2 · UTC 日均 · 可分享应用')
change('<label>显示 <select id="mode">','<label>视图 <select id="view"><option value="comparison">需求与官方预测对照</option><option value="overview">供需与电价总览</option></select></label>\n  <label>显示 <select id="mode">')
change(' <div id="error" class="error" role="status"></div>', ''' <div class="controls series-controls" id="seriesControls" aria-label="选择需求曲线">
  <span class="range-status">同图叠加</span>
  <label><input type="checkbox" data-series="course" checked><span class="swatch" style="--series:#f5b65c"></span>课程需求 VD</label>
  <label><input type="checkbox" data-series="nd" checked><span class="swatch" style="--series:#55b7ef"></span>NESO 实际 ND</label>
  <label><input type="checkbox" data-series="tsd" checked><span class="swatch" style="--series:#78d2b0"></span>NESO 实际 TSD</label>
  <label><input type="checkbox" data-series="ndf" checked><span class="swatch dashed" style="--series:#55b7ef"></span>NESO 预测 ND</label>
  <label><input type="checkbox" data-series="tsdf" checked><span class="swatch dashed" style="--series:#78d2b0"></span>NESO 预测 TSD</label>
  <label><input type="checkbox" data-series="cardinal"><span class="swatch dashed" style="--series:#c19bff"></span>原实验 ND 特征点均值</label>
 </div>
 <div id="error" class="error" role="status"></div>''')
change(' <div id="chart" role="img"', ''' <div class="comparison-readout" id="comparisonReadout" aria-live="off"><span>实际 ND <b id="qnd">—</b></span><span>实际 TSD <b id="qtsd">—</b></span><span>预测 ND <b id="qndf">—</b></span><span>预测 TSD <b id="qtsdf">—</b></span><span id="qforecastCoverage"></span></div>
 <div id="chart" role="img"''')
change(' <div class="source">日均功率', ''' <details class="definitions"><summary>口径、覆盖范围与更新说明</summary>
 <p>ND（National Demand，全国需求）与 TSD（Transmission System Demand，输电系统需求）分别展示原始实绩和对应官方预测。预测取目标日开始前 23:59:59 UTC 时已公开的 NDF / TSDF 全国版本，经 Elexon BMRS 提供；只对完整 48 个半小时求日均。缺失保留断线，不插值、不填零。实绩也按同一 UTC 日聚合。</p>
 <p>“原实验 ND 特征点均值”是此前模型输入的摘要，非全天时间加权均值，与新加入的半小时预测曲线分开显示。新数据仅加入可视化，既有训练结果保持原版本。</p>
 <p id="forecastCoverage"></p><p id="appVersion"></p>
 <p><a href="https://www.neso.energy/data-portal/historic-demand-data" target="_blank" rel="noopener">NESO 实绩来源</a> · <a href="https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/demand/day-ahead/history" target="_blank" rel="noopener">预测历史版本来源</a> · <a href="data/daily.csv" download>下载全量数据 CSV</a> · <a href="data/metadata.json">版本与数据来源</a> · <a href="data/forecast-gaps.json">预测缺口清单</a></p>
 </details>
 <div class="source">日均功率''')
change('</style>', '''.swatch{display:inline-block;width:17px;height:0;border-top:2px solid var(--series);margin-left:-3px}.swatch.dashed{border-top-style:dashed}.series-controls{gap:12px;margin:12px 0}.comparison-readout{display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;padding-top:9px}.comparison-readout b{color:var(--text);font-weight:500}.definitions{font-size:12px;line-height:1.7;color:var(--muted);margin-top:10px}.definitions summary{cursor:pointer;color:var(--text)}.definitions p{max-width:1200px;margin:7px 0}.source{max-width:1400px}body.comparison #chart{height:calc(100vh - 340px);min-height:510px}body.comparison #qg,body.comparison #qgap,body.comparison #qp{color:var(--muted)}.comparison-readout span{white-space:nowrap}@media(max-width:600px){.series-controls{gap:8px}.comparison-readout{gap:8px 16px}body.comparison #chart{height:560px;min-height:460px}main{padding:12px 8px}input[type=date]{min-width:135px}.series-controls label{white-space:normal}}
</style>''')
change(" const MIN=times[0]",''' const nd=rows.map(r=>r[7]===null?null:r[7]/1000),tsd=rows.map(r=>r[8]===null?null:r[8]/1000),ndf=rows.map(r=>r[9]===null?null:r[9]/1000),tsdf=rows.map(r=>r[10]===null?null:r[10]/1000),cardinal=rows.map(r=>r[11]===null?null:r[11]/1000);
 const compare={course:{index:1,values:demand},nd:{index:8,values:nd},tsd:{index:9,values:tsd},ndf:{index:10,values:ndf},tsdf:{index:11,values:tsdf},cardinal:{index:12,values:cardinal}};
 const MIN=times[0]''')
change("dragmode:'pan'};","dragmode:'pan',view:'comparison'};")
change("  $('qquality').textContent=rows[i][6]?",'''  for(const [id,values] of [['qnd',nd],['qtsd',tsd],['qndf',ndf],['qtsdf',tsdf]])$(id).textContent=values[i]===null?'缺失':fixed(values[i])+' GW';
  $('qforecastCoverage').textContent=`预测覆盖 ND ${rows[i][12]}/48 · TSD ${rows[i][13]}/48${rows[i][14]?' · 最近发布 '+rows[i][14]:''}`;
  $('qquality').textContent=rows[i][6]?''')
change('let lo=Math.min(...values),hi=Math.max(...values);','values=values.filter(Number.isFinite);if(!values.length)return [0,1];let lo=Math.min(...values),hi=Math.max(...values);')
a=s.index(' function yRanges()');b=s.index(' function bandShapes()',a)
s=s[:a]+''' function yRanges(){const a=state.first,b=state.last+1;let power=state.view==='overview'?generation.slice(a,b):[];for(const [key,c] of Object.entries(compare))if(document.querySelector(`[data-series="${key}"]`).checked)power.push(...c.values.slice(a,b).filter(Number.isFinite));let prices=price.slice(a,b);if(state.ma){if(state.view==='overview')power.push(...trailingMean(generation,state.ma).slice(a,b).filter(Number.isFinite));if(document.querySelector('[data-series="course"]').checked)power.push(...trailingMean(demand,state.ma).slice(a,b).filter(Number.isFinite));prices.push(...trailingMean(price,state.ma).slice(a,b).filter(Number.isFinite));}return {'yaxis.range':extent(power),'yaxis2.range':extent(gap.slice(a,b),true),'yaxis3.range':extent(prices)};}
'''+s[b:]
change(" function annotations(){return [", " function annotations(){if(state.view==='comparison')return [{text:'日均需求与日初可得官方预测 · GW · 同一 UTC 日期',x:0,y:1.065,xref:'paper',yref:'paper',showarrow:false,xanchor:'left',font:{color:'#c4d2e5',size:12}}];return [")
change(" const axisStyle=",''' for(const [name,values,color,dash] of [['NESO 实际 ND',nd,'#55b7ef','solid'],['NESO 实际 TSD',tsd,'#78d2b0','solid'],['NESO 预测 ND',ndf,'#55b7ef','dash'],['NESO 预测 TSD',tsdf,'#78d2b0','dash'],['原实验 ND 特征点均值',cardinal,'#c19bff','dot']]){const t=trace(name,values,color,'y');t.line.dash=dash;t.line.width=1.3;t.connectgaps=false;traces.push(t);}
 const axisStyle=''')
change("uirevision:'mmcs-explorer-v1'","uirevision:'mmcs-explorer-v2'")
change("  await Plotly.newPlot(chart,traces,layout,config);",'''  for(const c of Object.values(compare))traces[c.index].showlegend=false;
  try{const saved=JSON.parse(localStorage.getItem('mmcs-explorer-v2')||'null');if(saved?.series)for(const [k,v] of Object.entries(saved.series)){const input=document.querySelector(`[data-series="${k}"]`);if(input)input.checked=!!v;}}catch{}
  for(const [k,c] of Object.entries(compare))traces[c.index].visible=document.querySelector(`[data-series="${k}"]`).checked;
  for(const i of [0,2,3])traces[i].visible=false;
  layout.yaxis.domain=[.10,1];layout.yaxis2.visible=false;layout.yaxis3.visible=false;layout.showlegend=false;
  Object.entries(yRanges()).forEach(([key,value])=>{const [axis,prop]=key.split('.');layout[axis][prop]=value;});
  document.body.classList.add('comparison');
  await Plotly.newPlot(chart,traces,layout,config);
  function saveChoices(){try{localStorage.setItem('mmcs-explorer-v2',JSON.stringify({series:Object.fromEntries([...document.querySelectorAll('[data-series]')].map(x=>[x.dataset.series,x.checked]))}));}catch{}}
  for(const input of document.querySelectorAll('[data-series]'))input.addEventListener('change',async()=>{await Plotly.restyle(chart,{visible:input.checked},[compare[input.dataset.series].index]);if(input.dataset.series==='course'&&state.ma)await Plotly.restyle(chart,{visible:input.checked},[5]);if(state.autoY)await Plotly.relayout(chart,yRanges());saveChoices();});
  $('view').onchange=async()=>{state.view=$('view').value;const overview=state.view==='overview';document.body.classList.toggle('comparison',!overview);await Plotly.restyle(chart,{visible:overview},[0,2,3]);if(state.ma)await Plotly.restyle(chart,{visible:overview},[4,6]);await Plotly.relayout(chart,{'yaxis.domain':overview?[.64,1]:[.10,1],'yaxis2.visible':overview,'yaxis3.visible':overview,showlegend:overview,annotations:annotations(),...yRanges()});Plotly.Plots.resize(chart);};
  $('forecastCoverage').textContent=`全部 ${rows.length} 天：实际 ND / TSD ${source.metadata.coverage.ND_actual} / ${source.metadata.coverage.TSD_actual} 天；完整预测 ND / TSD ${source.metadata.coverage.ND_forecast} / ${source.metadata.coverage.TSD_forecast} 天。缺失区间显示断线。`;
  $('appVersion').textContent=`应用版本 ${source.metadata.version} · 数据生成 ${source.metadata.updated_at} · 预测采集 ${source.metadata.forecast_retrieved_at}`;''')
change('event.points.find(p=>p.curveNumber<4)','event.points.find(p=>p.curveNumber<4||p.curveNumber>=8)')
change("Plotly.restyle(chart,{mode:state.mode},[0,1,3]);","Plotly.restyle(chart,{mode:state.mode},[0,1,3,8,9,10,11,12]);")
change("visible:true,name:[`供给 MA${state.ma}`", "visible:[state.view==='overview',document.querySelector('[data-series=\"course\"]').checked,state.view==='overview'],name:[`供给 MA${state.ma}`")
change("const header='date,generation_MW,demand_MW,price_GBP_MWh,source_total_MW,wind_farm_MW,strict_no_imputation';","const header=source.metadata.column_order.join(',');")
change("(v?'True':'False'):v", "(v?'True':'False'):(v===null?'':v)")
change("getVisibleRows:()=>rows.slice(state.first,state.last+1)","getVisibleRows:()=>rows.slice(state.first,state.last+1),getComparison:()=>Object.fromEntries(Object.entries(compare).map(([k,c])=>[k,{trace:c.index,checked:document.querySelector(`[data-series=\"${k}\"]`).checked}]))")
change("new Blob([content],{type:'text/csv;charset=utf-8;'})","new Blob([content],{type:'text/csv;charset=utf-8;'})")
(R/'src').mkdir(exist_ok=True);(R/'src/index.html').write_text(s,encoding='utf-8')
print('Migrated existing interactions to maintained application source.')
