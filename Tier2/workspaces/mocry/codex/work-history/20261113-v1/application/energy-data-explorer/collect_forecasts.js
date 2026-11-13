// Run with Playwright MCP browser_run_code_unsafe. No credentials required.
// The caller may replace START and END for an incremental update.
async (page) => {
 const START='2021-01-01',END='2026-09-17',DAY=86400000;
 const c=await page.context().browser().newContext();
 try {
  const days=[];for(let t=Date.parse(START);t<=Date.parse(END);t+=DAY)days.push(new Date(t).toISOString().slice(0,10));
  const records=new Array(days.length);let next=0;
  async function worker(){while(next<days.length){const i=next++,day=days[i],cutoff=new Date(Date.parse(day)-1000).toISOString();
   const url='https://data.elexon.co.uk/bmrs/api/v1/forecast/demand/day-ahead/history?publishTime='+encodeURIComponent(cutoff)+'&format=json';
   let error=null;
   for(let attempt=0;attempt<3;attempt++)try{
    const r=await c.request.get(url,{timeout:20000});if(!r.ok())throw new Error('HTTP '+r.status());
    const body=await r.json();const slots=new Map();let late=0;
    for(const x of body.data||[]){if(x.startTime?.slice(0,10)!==day||x.boundary!=='N')continue;
     if(Date.parse(x.publishTime)>=Date.parse(day+'T00:00:00Z')){late++;continue;}
     if(!slots.has(x.startTime)||slots.get(x.startTime).publishTime<x.publishTime)slots.set(x.startTime,x);}
    const a=[...slots.values()].sort((a,b)=>a.startTime.localeCompare(b.startTime));
    const validND=a.filter(x=>Number.isFinite(x.nationalDemand)&&x.nationalDemand>0),validTSD=a.filter(x=>Number.isFinite(x.transmissionSystemDemand)&&x.transmissionSystemDemand>0);
    const avg=(a,k)=>a.reduce((s,x)=>s+x[k],0)/a.length;
    records[i]={date:day,nd_forecast_MW:validND.length===48?avg(validND,'nationalDemand'):null,tsd_forecast_MW:validTSD.length===48?avg(validTSD,'transmissionSystemDemand'):null,nd_periods:validND.length,tsd_periods:validTSD.length,latest_issue:a.map(x=>x.publishTime).sort().at(-1)||null,late_rejected:late,cutoff,url,slots:a};error=null;break;
   }catch(e){error=String(e);if(attempt<2)await new Promise(r=>setTimeout(r,400*(attempt+1)));}
   if(error)records[i]={date:day,error,url,nd_forecast_MW:null,tsd_forecast_MW:null,nd_periods:0,tsd_periods:0};
  }}
  await Promise.all(Array.from({length:6},worker));
  const snapshot={retrieved_at:new Date().toISOString(),source:'NGESO/NESO forecasts distributed by Elexon BMRS NDF and TSDF',method:'National boundaryN snapshot at23:59:59UTC before targetday; only exact48 distinct halfhours and issue before targetday accepted; missing leftnull',records};
  const p=await c.newPage();
  const gzip=await p.evaluate(async(data)=>{const bytes=new Uint8Array(await new Response(new Blob([JSON.stringify(data)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());let text='';for(let i=0;i<bytes.length;i+=32768)text+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(text);},snapshot);
  return {count:records.length,completeND:records.filter(x=>x.nd_forecast_MW!==null).length,completeTSD:records.filter(x=>x.tsd_forecast_MW!==null).length,errors:records.filter(x=>x.error).length,gzip};
 }finally{await c.close();}
}
