// Vercel Node function: exchange only codes for this registered OAuth app.
const ORIGIN='https://marcusdhaynes.github.io';
const CALLBACK=ORIGIN+'/REAlity/';
export default async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('Vary','Origin');
 if(req.headers.origin!==ORIGIN)return res.status(403).json({error:'Origin refused'});
 res.setHeader('Access-Control-Allow-Origin',ORIGIN);
 res.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');
 res.setHeader('Access-Control-Allow-Headers','Content-Type');
 if(req.method==='OPTIONS')return res.status(204).end();
 const clientId=process.env.GITHUB_OAUTH_CLIENT_ID,secret=process.env.GITHUB_OAUTH_CLIENT_SECRET;
 if(!clientId||!secret)return res.status(503).json({error:'OAuth app has not been configured'});
 if(req.method==='GET')return res.status(200).json({clientId,callback:CALLBACK});
 if(req.method!=='POST')return res.status(405).end();
 try{
  const b=typeof req.body==='string'?JSON.parse(req.body):req.body;
  if(!b||typeof b.code!=='string'||!/^[A-Za-z0-9_-]{1,256}$/.test(b.code)||typeof b.verifier!=='string'||!/^[A-Za-z0-9._~-]{43,128}$/.test(b.verifier))return res.status(400).json({error:'Invalid OAuth exchange'});
  const r=await fetch('https://github.com/login/oauth/access_token',{method:'POST',headers:{Accept:'application/json','Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({client_id:clientId,client_secret:secret,code:b.code,code_verifier:b.verifier,redirect_uri:CALLBACK}),redirect:'error',signal:AbortSignal.timeout(15000)});
  const d=await r.json();if(!r.ok||!d.access_token)return res.status(400).json({error:'GitHub authorization failed or expired'});
  return res.status(200).json({access_token:d.access_token});
 }catch{return res.status(502).json({error:'OAuth exchange unavailable'});}
}
