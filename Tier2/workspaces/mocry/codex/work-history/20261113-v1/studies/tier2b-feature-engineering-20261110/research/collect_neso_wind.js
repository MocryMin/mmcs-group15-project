async (page) => {
 const c=await page.context().browser().newContext();
 try {
  const url='https://api.neso.energy/dataset/fbe3701d-1487-443e-abe9-47a6c01ecce2/resource/7524ec65-f782-4258-aaf8-5b926c17b966/download/7524ec65-f782-4258-aaf8-5b926c17b966-20261109084501.csv';
  const response=await c.request.get(url,{timeout:40000});const text=await response.text();
  if(response.status()!==200)return {status:response.status(),error:text.slice(0,1000)};
  const lines=text.trim().split(/\r?\n/);const clean=x=>x.replace(/^"|"$/g,'').replace(/""/g,'"');
  const header=lines.shift().split(',').map(clean);const selected=new Map();let futureRejected=0,otherRejected=0;
  const utc=s=>{if(!s)return NaN;const iso=s.replace(' ','T');return Date.parse(iso.endsWith('Z')?iso:iso+'Z');};
  for(const line of lines){const parts=line.split(',').map(clean);const r=Object.fromEntries(header.map((h,j)=>[h,parts[j]]));
   const valid=r.Datetime_GMT;const day=valid?.slice(0,10);const issue=r.Forecast_Timestamp;
   if(!valid||day<'2021-01-01'||day>'2026-09-18'){otherRejected++;continue;}
   if(!Number.isFinite(utc(issue))||utc(issue)>=Date.parse(day+'T00:00:00Z')){futureRejected++;continue;}
   const old=selected.get(valid);if(!old||utc(old.Forecast_Timestamp)<utc(issue))selected.set(valid,r);
  }
  const days={};for(const [valid,r] of selected){const day=valid.slice(0,10);(days[day]??=[]).push({valid,forecast:Number(r.Incentive_forecast),capacity:Number(r.Capacity),issue:r.Forecast_Timestamp});}
  const records=Object.entries(days).sort().map(([date,points])=>({date,n:points.length,mean:points.reduce((s,r)=>s+r.forecast,0)/points.length,capacity:points.reduce((s,r)=>s+r.capacity,0)/points.length,latest_issue:points.map(x=>x.issue).sort().at(-1),points}));
  return {status:200,raw:JSON.stringify({url,header,source_headers:response.headers(),source_rows:lines.length,source_bytes:text.length,selection:'Latest issue per valid UTC half-hour strictly before valid day00UTC; no future-issued BST tail periods',future_or_bad_issue_rejected:futureRejected,other_rejected:otherRejected,records})};
 } finally {await c.close();}
}
