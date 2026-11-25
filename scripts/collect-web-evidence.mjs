// Run only in a disposable network-restricted browser worker.
import { chromium } from 'playwright';
import { readFile, realpath, writeFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { validateContract,contractDigest } from '../docs/behavior-contract.mjs';
const MIME={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.woff2':'font/woff2','.wasm':'application/wasm'};
const ORIGIN='http://reality-test.invalid';
async function mount(context,root){const base=await realpath(root);await context.route('**/*',async route=>{try{const req=route.request(),url=new URL(req.url());if(url.origin!==ORIGIN||req.method()!=='GET')return route.abort();const rel=decodeURIComponent(url.pathname).replace(/^\/+/,'')||'index.html';if(rel.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')||x.includes('\\')))return route.abort();const target=await realpath(path.join(base,rel));if(!target.startsWith(base+path.sep))return route.abort();const info=await stat(target);if(!info.isFile()||info.size>20*1024*1024)return route.abort();const body=await readFile(target);return route.fulfill({status:200,body,contentType:MIME[path.extname(target).toLowerCase()]||'application/octet-stream',headers:{'Content-Security-Policy':"default-src 'self' data: blob:; connect-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; object-src 'none'; form-action 'none'; base-uri 'none'; frame-src 'none'",'Cache-Control':'no-store'}})}catch{return route.abort()}})}

async function runCase(browser,root,c){
 const context=await browser.newContext({viewport:{width:1280,height:800},deviceScaleFactor:1,locale:'en-US',timezoneId:'UTC',serviceWorkers:'block',acceptDownloads:false});
 const steps=[];let error=null;
 try{
  await mount(context,root);const page=await context.newPage();page.setDefaultTimeout(5000);
  const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,300)));page.on('popup',p=>p.close());
  await page.goto(ORIGIN+'/index.html',{waitUntil:'domcontentloaded',timeout:8000});
  for(const t of c.steps){
   try{
    const loc=page.locator(t.targets.web);let value;
    if(t.op==='observeVisible'){const count=await loc.count();if(count>1)throw Error('Ambiguous web selector');value=count===1&&await loc.isVisible();}
    else{
     await loc.waitFor({state:'attached'});if(await loc.count()!==1)throw Error('Ambiguous web selector');
     if(t.op==='click')await loc.click();
     else if(t.op==='fill')await loc.fill(t.value);
     else if(t.op==='press')await loc.press(t.value);
     else if(t.op==='observeText')value=await loc.innerText();
     else if(t.op==='observeValue')value=await loc.inputValue();
    }
    steps.push({id:t.id,ok:true,...(t.op.startsWith('observe')?{value}:{})});
   }catch(e){steps.push({id:t.id,ok:false,error:String(e).slice(0,400)});break;}
  }
  if(errors.length)error=errors.join('; ').slice(0,400);
 }catch(e){error=String(e).slice(0,400)}finally{await context.close()}
 return {id:c.id,steps,...(error?{error}:{})};
}
const [root,contractPath,output]=process.argv.slice(2);
if(!output)throw Error('Usage: node scripts/collect-web-evidence.mjs SITE CONTRACT.json NEW_EVIDENCE.json');
if((await stat(contractPath)).size>512*1024)throw Error('Contract exceeds limit');
const {contract}=validateContract(JSON.parse(await readFile(contractPath,'utf8')));
const browser=await chromium.launch({headless:true,chromiumSandbox:true,args:['--disable-background-networking']});
const cases=[];
try{for(const c of contract.cases)cases.push(await runCase(browser,root,c));}finally{await browser.close()}
const evidence={version:1,side:'web',adapter:'Playwright Chromium',contractSha256:await contractDigest(contract),cases};
await writeFile(output,JSON.stringify(evidence,null,2),{flag:'wx'});
if(cases.some(c=>c.error||c.steps.some(s=>!s.ok)))process.exitCode=1;
