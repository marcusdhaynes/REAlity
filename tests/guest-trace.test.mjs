import test from 'node:test';
import assert from 'node:assert/strict';
import {validateGuestTrace} from '../docs/guest-trace.mjs';
test('allows bounded named checkpoint trace',()=>{const s={steps:[{op:'text',value:'sample'},{op:'wait',ms:500},{op:'snapshot',name:'initial'}]};assert.equal(validateGuestTrace(s),s)});
test('rejects arbitrary execution and missing checkpoints',()=>{assert.throws(()=>validateGuestTrace({steps:[{op:'eval',value:'1'}]}));assert.throws(()=>validateGuestTrace({steps:[{op:'wait',ms:10}]}))});
test('rejects duplicate checkpoint and excess wait',()=>{assert.throws(()=>validateGuestTrace({steps:[{op:'snapshot',name:'a'},{op:'snapshot',name:'a'}]}));assert.throws(()=>validateGuestTrace({steps:[...Array.from({length:7},()=>({op:'wait',ms:10000})),{op:'snapshot',name:'x'}]}))});
