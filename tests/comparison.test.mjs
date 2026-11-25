import test from 'node:test';
import assert from 'node:assert/strict';
import {comparePixels} from '../docs/comparison.mjs';
test('identical pixels are unchanged',()=>{let a=new Uint8ClampedArray([12,34,56,255]);let x=comparePixels(a,a,1,1);assert.equal(x.report.changedPixels,0);assert.equal(x.report.meanAbsoluteChannelError,0)});
test('changes and tolerance are measured',()=>{let a=new Uint8ClampedArray([0,0,0,255,10,10,10,255]),b=new Uint8ClampedArray([13,0,0,255,20,10,10,255]);let x=comparePixels(a,b,2,1,12);assert.equal(x.report.changedPixels,1);assert.equal(x.report.changedPercent,50);assert.deepEqual([...x.diff.slice(0,4)],[255,40,110,255])});
test('invalid pixel shape or tolerance is rejected',()=>{let a=new Uint8ClampedArray(4);assert.throws(()=>comparePixels(a,a,2,1));assert.throws(()=>comparePixels(a,a,1,1,-1));assert.throws(()=>comparePixels(a,a,1,1,256))});
