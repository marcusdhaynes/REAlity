import test from 'node:test';
import assert from 'node:assert/strict';
import {validateContract,contractDigest,compareEvidence} from '../docs/behavior-contract.mjs';
const c={version:1,cases:[{id:'calc',steps:[{id:'click',op:'click',targets:{web:'#run',native:{by:'auto_id',value:'run'}}},{id:'result',op:'observeText',targets:{web:'#result',native:{by:'auto_id',value:'result'}},expected:'42'}]}]};
const hash=await contractDigest(c);
function e(side,value='42',ok=true){return {version:1,side,contractSha256:hash,cases:[{id:'calc',steps:[{id:'click',ok},{id:'result',ok:true,value}]}]}}
test('matching observations are scoped to the declared tests',()=>{let r=compareEvidence(c,e('native'),e('web'),hash);assert.equal(r.status,'matched-for-declared-tests');assert.equal(r.matchedObservations,1)});
test('different values fail',()=>assert.equal(compareEvidence(c,e('native'),e('web','43'),hash).status,'mismatch'));
test('matching but wrong values fail expected assertion',()=>assert.equal(compareEvidence(c,e('native','0'),e('web','0'),hash).status,'mismatch'));
test('failed earlier action blocks subsequent observations',()=>{const r=compareEvidence(c,e('native','42',false),e('web'),hash);assert.equal(r.status,'unverified');assert.equal(r.matchedObservations,0);assert.equal(r.unverifiedSteps,2)});
test('empty evidence never passes',()=>{let n=e('native');n.cases=[];assert.equal(compareEvidence(c,n,e('web'),hash).status,'unverified')});
test('wrong contract digest is rejected',()=>{let w=e('web');w.contractSha256='0'.repeat(64);assert.throws(()=>compareEvidence(c,e('native'),w,hash))});
test('arbitrary code and action-only cases are rejected',()=>{let x=structuredClone(c);x.cases[0].steps[0].op='eval';assert.throws(()=>validateContract(x));x=structuredClone(c);x.cases[0].steps.pop();assert.throws(()=>validateContract(x))});
test('canonical contract digest ignores property order',async()=>assert.equal(await contractDigest({cases:c.cases,version:1}),hash));
