async(page)=>{
 const c=await page.context().browser().newContext();
 try{
 const B="https://data.elexon.co.uk/bmrs/api/v1",out=[];
 for(const d of ["2022-04-04","2020-11-09","2022-01-03"]){
 const e=new Date(Date.parse(d)+3*86400000).toISOString().slice(0,10),u=B+"/datasets/AGWS?publishDateTimeFrom="+d+"T00%3A00Z&publishDateTimeTo="+e+"T00%3A00Z&format=json",q=await c.request.get(u,{timeout:16000}),j=await q.json(),a=(j.data||[]).filter(x=>x.startTime?.startsWith(d)),g={};
 for(const r of a)(g[r.psrType]??=[]).push(r);
 out.push({date:d,url:u,status:q.status(),counts:Object.fromEntries(Object.entries(g).map(([k,v])=>[k,[v.length,new Set(v.map(x=>x.startTime)).size,Math.max(...v.map(x=>x.quantity)),v[0]]]))});
 }
 for(const d of ["2020-01-01","2022-08-01","2025-07-01"]){
 const e=new Date(Date.parse(d)+86400000).toISOString().slice(0,10),u=B+"/datasets/MID?from="+d+"T00%3A00Z&to="+e+"T00%3A00Z&format=json",q=await c.request.get(u,{timeout:14000}),j=await q.json(),a=(j.data||[]).filter(x=>x.startTime?.startsWith(d)),g={};
 for(const r of a)(g[r.dataProvider]??=[]).push(r);
 out.push({date:d,kind:"price",status:q.status(),allMean:a.reduce((s,x)=>s+x.price,0)/a.length,providers:Object.fromEntries(Object.entries(g).map(([k,v])=>[k,{n:v.length,mean:v.reduce((s,x)=>s+x.price,0)/v.length,weighted:v.reduce((s,x)=>s+x.price*x.volume,0)/v.reduce((s,x)=>s+x.volume,0)}]))});
 }
 return out;
 }finally{await c.close();}
}
