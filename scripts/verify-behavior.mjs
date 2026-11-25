import {readFile,writeFile,stat} from 'node:fs/promises';
import {contractDigest,compareEvidence} from '../docs/behavior-contract.mjs';
const [contractPath,nativePath,webPath,output]=process.argv.slice(2);
if(!output)throw Error('Usage: node scripts/verify-behavior.mjs CONTRACT NATIVE_EVIDENCE WEB_EVIDENCE NEW_REPORT');
async function load(p){if((await stat(p)).size>8*1024*1024)throw Error('Evidence exceeds limit');return JSON.parse(await readFile(p,'utf8'))}
const [contract,native,web]=await Promise.all([contractPath,nativePath,webPath].map(load));
const report=compareEvidence(contract,native,web,await contractDigest(contract));
await writeFile(output,JSON.stringify(report,null,2),{flag:'wx'});
console.log(report.status+'; '+report.matchedObservations+'/'+report.observations+' observations matched');
if(report.status!=='matched-for-declared-tests')process.exitCode=1;
