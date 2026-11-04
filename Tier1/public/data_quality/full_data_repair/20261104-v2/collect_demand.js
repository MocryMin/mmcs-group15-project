async(page)=>{
 const ctx=await page.context().browser().newContext();
 try{
 const START="2020-01-01",END="2026-09-18",B="https://data.elexon.co.uk/bmrs/api/v1";
const shift=(d,n)=>new Date(Date.parse(d)+n*86400000).toISOString().slice(0,10);
const iso=()=>new Date().toISOString();
const summary={started:iso(),queries:[],errors:[]},days={};
 const ranges=[];for(let d=START;d<END;){let e=shift(d,1);if(e>END)e=END;ranges.push([d,e]);d=e;}
 let index=0;await Promise.all(Array.from({length:4},async()=>{
 while(index<ranges.length){const [a,z]=ranges[index++],url=B+"/demand/outturn/summary?from="+a+"T00%3A00Z&to="+z+"T00%3A00Z&format=json";
 try{
 const response=await ctx.request.get(url,{timeout:25000}),json=await response.json();
 if(!response.ok()){summary.errors.push({from:a,to:z,status:response.status(),error:json});continue;}
 const records=Array.isArray(json)?json:(json.data||[]);
 summary.queries.push([a,z,response.status(),records.length,url]);
 for(const row of records){const stamp=row.startTime,date=stamp?.slice(0,10);if(!date||date<a||date>=z)continue;
 if(row.recordType==="VD")(days[date]??={})[stamp]=row.demand;
 }
 }catch(error){summary.errors.push({from:a,to:z,error:String(error)});}
 }
 }));
 summary.finished=iso();
 return {kind:"VD",summary,days};
 }finally{await ctx.close();}
}
