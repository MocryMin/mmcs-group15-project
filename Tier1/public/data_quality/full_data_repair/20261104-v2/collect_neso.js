async(page)=>{
 const ctx=await page.context().browser().newContext();
 try{
 const base="https://api.neso.energy/api/3/action/package_show?id=historic-demand-data",q=await ctx.request.get(base,{timeout:20000}),m=await q.json();
 const resources=m.result.resources.filter(r=>/Historic Demand Data 202[0-6]$/.test(r.name)),out={};
 let i=0;await Promise.all(Array.from({length:3},async()=>{while(i<resources.length){const r=resources[i++];const response=await ctx.request.get(r.url,{timeout:30000});out[r.name]={url:r.url,status:response.status(),text:await response.text()};}}));
 return {kind:"NESO_historic_demand",retrieved:new Date().toISOString(),metadata_notes:m.result.notes,resources:out};
 }finally{await ctx.close();}
}
