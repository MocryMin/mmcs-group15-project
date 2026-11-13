async (page) => {
 const c=await page.context().browser().newContext();
 try {
  const url='https://api.neso.energy/dataset/8fbc8a09-06af-4c90-886f-d3025d38a349/resource/9847e7bb-986e-49be-8138-717b25933fbb/download/archive_1dayahead.csv';
  const response=await c.request.get(url,{timeout:40000});const text=await response.text();
  if(response.status()!==200)return {status:response.status(),error:text.slice(0,1000)};
  const lines=text.trim().split(/\r?\n/);const clean=x=>x.replace(/^"|"$/g,'').replace(/""/g,'"');
  const header=lines.shift().split(',').map(clean);const selected=new Map();let futureRejected=0,otherRejected=0;
  for(const line of lines){const parts=line.split(',').map(clean);const r=Object.fromEntries(header.map((h,j)=>[h,parts[j]]));
   if(r.TARGETDATE<'2021-01-01'||r.TARGETDATE>'2026-09-18'||r.DAYSAHEAD!=='1'){otherRejected++;continue;}
   const issue=r.FORECAST_TIMESTAMP;const date=r.TARGETDATE;
   if(!issue||!issue.endsWith('Z')||issue>=date+'T00:00:00Z'){futureRejected++;continue;}
   const key=date+'|'+r.CARDINALPOINT;const old=selected.get(key);
   if(!old||old.FORECAST_TIMESTAMP<issue)selected.set(key,r);
  }
  const days={};for(const r of selected.values()){const a=(days[r.TARGETDATE]??=[]);a.push({cardinal:r.CARDINALPOINT,value:Number(r.FORECASTDEMAND),issue:r.FORECAST_TIMESTAMP,type:r.CP_TYPE,start:r.CP_ST_TIME,end:r.CP_END_TIME});}
  const records=Object.entries(days).sort().map(([date,points])=>({date,n:points.length,mean:points.reduce((s,r)=>s+r.value,0)/points.length,min:Math.min(...points.map(x=>x.value)),max:Math.max(...points.map(x=>x.value)),latest_issue:points.map(x=>x.issue).sort().at(-1),points}));
  return {status:200,raw:JSON.stringify({url,header,source_headers:response.headers(),source_rows:lines.length,source_bytes:text.length,selection:'Latest issue per target date and cardinal point strictly before target00UTC; DAYSAHEAD1',future_or_bad_issue_rejected:futureRejected,other_rejected:otherRejected,records})};
 } finally {await c.close();}
}
