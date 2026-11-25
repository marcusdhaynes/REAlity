export function validateGuestTrace(spec){
 if(!spec||!Array.isArray(spec.steps)||spec.steps.length<1||spec.steps.length>50)throw Error('Require 1–50 guest steps');
 let wait=0;const names=new Set();
 for(const s of spec.steps){
  if(!s||typeof s!=='object')throw Error('Invalid guest step');
  if(s.op==='wait'){if(!Number.isInteger(s.ms)||s.ms<0||s.ms>10000||(wait+=s.ms)>60000)throw Error('Wait budget exceeded');}
  else if(s.op==='text'){if(typeof s.value!=='string'||s.value.length>1000)throw Error('Invalid guest text');}
  else if(s.op==='keys'){if(!Array.isArray(s.codes)||!s.codes.length||s.codes.length>32||s.codes.some(x=>!Number.isInteger(x)||x<0||x>255))throw Error('Invalid keyboard codes');}
  else if(s.op==='snapshot'){if(!/^[A-Za-z0-9_-]{1,80}$/.test(s.name)||names.has(s.name)||names.size>=12)throw Error('Invalid or duplicate checkpoint');names.add(s.name);}
  else throw Error('Unsupported guest operation');
 }
 if(!names.size)throw Error('At least one screenshot checkpoint is required');
 return spec;
}
