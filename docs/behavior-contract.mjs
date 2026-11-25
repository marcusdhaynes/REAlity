// Shared native-to-web verification contract. No executable code in contracts.
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,80}$/.test(x)&&!['__proto__','constructor','prototype'].includes(x);
const str=x=>typeof x==='string'&&x.length<=4000;
const exact=(x,required,optional=[])=>x&&typeof x==='object'&&!Array.isArray(x)&&required.every(k=>Object.hasOwn(x,k))&&Object.keys(x).every(k=>required.includes(k)||optional.includes(k));
const ops=new Set(['click','fill','press','observeText','observeValue','observeVisible']);
export function validateContract(s){
 if(!exact(s,['version','cases'])||s.version!==1||!Array.isArray(s.cases)||!s.cases.length||s.cases.length>30)throw Error('Require version 1 and 1–30 cases');
 const cases=new Set();let observations=0;
 for(const c of s.cases){
  if(!exact(c,['id','steps'])||!id(c.id)||cases.has(c.id)||!Array.isArray(c.steps)||!c.steps.length||c.steps.length>40)throw Error('Invalid case');cases.add(c.id);const names=new Set();let observed=0;
  for(const t of c.steps){
   if(!exact(t,['id','op','targets'],['value','expected','settleMs'])||!id(t.id)||names.has(t.id)||!ops.has(t.op)||!exact(t.targets,['native','web'])||!str(t.targets.web)||!t.targets.web.trim())throw Error('Invalid or duplicate step');names.add(t.id);
   const n=t.targets.native;
   if(!exact(n,['by','value'],['controlType'])||!['auto_id','title'].includes(n.by)||!str(n.value)||!n.value.trim()||n.controlType!==undefined&&(!str(n.controlType)||!/^[A-Za-z]+$/.test(n.controlType)))throw Error('Invalid native selector');
   if(t.settleMs!==undefined&&(!Number.isInteger(t.settleMs)||t.settleMs<0||t.settleMs>5000))throw Error('Invalid settle interval');
   if(!['fill','press'].includes(t.op)&&t.value!==undefined||!t.op.startsWith('observe')&&t.expected!==undefined)throw Error('Unexpected step field');
   if(['fill','press'].includes(t.op)&&!str(t.value))throw Error('Missing input value');
   if(t.op==='press'&&!['Enter','Tab','Escape','Space','Backspace','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(t.value))throw Error('Unsupported portable key');
   if(t.op.startsWith('observe')){observed++;observations++;if(t.expected!==undefined&&(t.op==='observeVisible'?typeof t.expected!=='boolean':!str(t.expected)))throw Error('Invalid expected observation');}
  }
  if(!observed)throw Error('Every case needs an observable result');
 }
 return {contract:s,observations};
}
export async function contractDigest(contract){
 const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
 const data=new TextEncoder().encode(JSON.stringify(canonical(contract)));
 return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),b=>b.toString(16).padStart(2,'0')).join('');
}
export function compareEvidence(contract,native,web,digest){
 const {observations}=validateContract(contract);if(!/^[a-f0-9]{64}$/.test(digest))throw Error('Invalid contract digest');
 const validate=(e,side)=>{
  if(!e||e.version!==1||e.side!==side||e.contractSha256!==digest||!Array.isArray(e.cases)||e.cases.length>30)throw Error('Wrong evidence side or contract digest: '+side);
  const map=new Map();for(const c of e.cases){if(!id(c.id)||map.has(c.id)||!Array.isArray(c.steps)||c.steps.length>40)throw Error('Invalid evidence case');const steps=new Map();for(const s of c.steps){if(!id(s.id)||steps.has(s.id)||typeof s.ok!=='boolean')throw Error('Invalid evidence step');steps.set(s.id,s);}map.set(c.id,{steps,error:c.error});}return map;
 };
 const a=validate(native,'native'),b=validate(web,'web'),results=[];let matched=0,mismatched=0,unverified=0;
 for(const c of contract.cases){
  const left=a.get(c.id),right=b.get(c.id);const steps=[];let blocked=false;
  for(const t of c.steps){
   const l=left?.steps.get(t.id),r=right?.steps.get(t.id),observe=t.op.startsWith('observe');
   let status='matched',reason='';
   if(blocked||left?.error||right?.error||!l?.ok||!r?.ok){status='unverified';reason='Missing, failed or blocked execution';blocked=true;}
   else if(observe){const type=t.op==='observeVisible'?'boolean':'string';if(typeof l.value!==type||typeof r.value!==type){status='unverified';reason='Invalid or missing observation';}else if(l.value!==r.value||t.expected!==undefined&&(l.value!==t.expected||r.value!==t.expected)){status='mismatch';reason='Observed outputs or expected value differ';}}
   if(status==='unverified')unverified++;else if(status==='mismatch')mismatched++;else if(observe)matched++;
   steps.push({id:t.id,op:t.op,status,reason,native:l?.value,web:r?.value,expected:t.expected,nativeError:l?.error,webError:r?.error});
  }
  results.push({id:c.id,steps,status:steps.some(s=>s.status==='mismatch')?'mismatch':steps.some(s=>s.status==='unverified')?'unverified':'matched'});
 }
 return {version:1,contractSha256:digest,nativeTargetSha256:native.targetSha256||null,webTargetSha256:web.targetSha256||null,scope:'Declared observations only; evidence files are not independently authenticated and untested features remain unverified.',status:mismatched?'mismatch':unverified?'unverified':'matched-for-declared-tests',observations,matchedObservations:matched,mismatchedSteps:mismatched,unverifiedSteps:unverified,results};
}
