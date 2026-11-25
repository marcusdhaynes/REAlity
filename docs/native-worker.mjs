let initPromise;
self.onmessage=async({data})=>{
 try{
  if(data.type!=='decompile')throw Error('Unknown operation');
  const m=await import('./vendor/native/reality_native.js');
  initPromise??=m.default();await initPromise;
  const report=JSON.parse(m.decompile_native(new Uint8Array(data.buffer),data.offset,data.count));
  self.postMessage({type:'result',report});
 }catch(e){self.postMessage({type:'error',message:String(e?.message||e)})}
};
