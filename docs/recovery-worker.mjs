import {recover,utf8} from './recovery-engine.mjs';
function nativePage(file){
 return new Promise((resolve,reject)=>{
  const w=new Worker('./native-worker.mjs',{type:'module'});
  const timeout=setTimeout(()=>{w.terminate();reject(Error('Native analysis time limit exceeded'))},45000);
  function finish(){clearTimeout(timeout);w.terminate()}
  w.onerror=e=>{finish();reject(Error(e.message||'Native worker failed'))};
  w.onmessage=({data})=>{finish();if(data.type==='result')resolve(data.report);else reject(Error(data.message))};
  const b=file.data.slice().buffer;
  w.postMessage({type:'decompile',buffer:b,offset:0,count:32},[b]);
 });
}
self.onmessage=async ({data})=>{try{
 const inputs=data.files.map((file,i)=>({name:file.name,size:file.size,webkitRelativePath:data.paths[i],arrayBuffer:()=>file.arrayBuffer()}));
 const progress=message=>self.postMessage({type:'progress',message});
 const result=await recover(inputs,progress);
 result.nativeEvidence=[];
 if(data.native!==false){
  const manifest=await fetch('./vendor/status.json',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({}));
  const candidates=result.report.inventory.filter(x=>['Windows PE','ELF'].includes(x.kind)&&x.size<=64*1024*1024);
  result.report.nativeAnalysis={available:!!manifest.native?.available,candidateCount:candidates.length,analyzed:[],scope:'First 32 discovered functions per selected native binary; full function pagination is available in Advanced Lab.'};
  if(candidates.length&&!manifest.native?.available)result.report.warnings.push('Native WASM module is not deployed; use Advanced Lab after successful engine build.');
  if(manifest.native?.available){
   const selected=candidates.slice(0,3);
   if(candidates.length>selected.length)result.report.warnings.push('Automatic native analysis limited to first three binaries; additional targets can be analyzed in Advanced Lab.');
   for(const [i,item] of selected.entries()){
    const f=result.files.find(x=>x.path===item.path);if(!f)continue;
    progress('Decompiling machine code: '+f.path);
    try{
     const report=await nativePage(f);
     const path='native-analysis/'+String(i+1).padStart(3,'0')+'.json';
     result.nativeEvidence.push({path,data:utf8(JSON.stringify({originalPath:f.path,sha256:item.sha256,...report},null,2))});
     result.report.nativeAnalysis.analyzed.push({path:f.path,evidence:path,totalFunctions:report.total_functions,returned:report.functions.length,nextOffset:report.next_offset});
    }catch(e){result.report.warnings.push(f.path+': native decompilation: '+e.message)}
   }
  }
 }
 const transfers=[...new Set([...result.files,...result.nativeEvidence].map(f=>f.data.buffer))];
 self.postMessage({type:'result',result},transfers)
}catch(e){self.postMessage({type:'error',message:e.message})}};
