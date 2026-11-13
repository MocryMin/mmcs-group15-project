async(page)=>{
 const ctx=await page.context().browser().newContext();
 try {
 const B="https://data.elexon.co.uk/bmrs/api/v1";
 const paths=[
 "/balancing/settlement/market-index?from=2022-08-01T00%3A00Z&to=2022-08-02T00%3A00Z&format=json",
 "/datasets/MID?from=2022-08-01&to=2022-08-02&format=json",
 "/datasets/MID?settlementDate=2022-08-01&format=json",
 "/generation/actual/per-type/wind-and-solar?from=2022-04-04T00%3A00Z&to=2022-04-05T00%3A00Z&format=json",
 "/datasets/AGWS?publishDateTimeFrom=2022-04-04T00%3A00Z&publishDateTimeTo=2022-04-07T00%3A00Z&format=json"
 ];
 const out=await Promise.all(paths.map(async p=>{
  try {const q=await ctx.request.get(B+p,{timeout:14000}),s=await q.text();let j;try{j=JSON.parse(s);}catch{};
   const a=Array.isArray(j)?j:j?.data;
   return {url:B+p,status:q.status(),keys:j?Object.keys(j).slice(0,6):[],count:a?.length,sample:a?.slice(0,3),body:a?undefined:s.slice(0,650)};
  }catch(e){return {url:B+p,error:String(e)}}
 }));
 return out;
 }finally{await ctx.close();}
}
