const cp=require('node:child_process');
const original=cp.spawn;
cp.spawn=function(command,args,options){return original.call(this,command,args,{...options,windowsHide:true});};
require('node:module').syncBuiltinESMExports();
