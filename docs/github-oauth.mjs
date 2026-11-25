// Standard GitHub OAuth with PKCE. Never save access tokens in storage.
const CALLBACK='https://marcusdhaynes.github.io/REAlity/';
const KEY='reality.oauth.pending.v1';
function random(){const b=crypto.getRandomValues(new Uint8Array(32));return btoa(String.fromCharCode(...b)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
function relayUrl(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash)throw Error('Invalid OAuth relay configuration');return u.href}
async function config(){const r=await fetch('./auth-config.json',{cache:'no-store'});if(!r.ok)throw Error('OAuth is not configured');const c=await r.json();if(!c.relay)throw Error('GitHub OAuth has not yet been activated by the app administrator.');return relayUrl(c.relay)}
export async function startGitHubLogin(){
 const relay=await config(),res=await fetch(relay,{credentials:'omit',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(10000)});if(!res.ok)throw Error('GitHub OAuth relay is not configured or available.');
 const c=await res.json();if(c.callback!==CALLBACK||!/^[-A-Za-z0-9_]{10,100}$/.test(c.clientId))throw Error('Invalid GitHub OAuth application configuration');
 const verifier=random(),state=random();const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier)));const challenge=btoa(String.fromCharCode(...hash)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 sessionStorage.setItem(KEY,JSON.stringify({state,verifier,time:Date.now(),relay}));
 const url=new URL('https://github.com/login/oauth/authorize');url.search=new URLSearchParams({client_id:c.clientId,redirect_uri:CALLBACK,scope:'public_repo workflow',state,code_challenge:challenge,code_challenge_method:'S256',allow_signup:'false'}).toString();location.assign(url.href);
}
export async function finishGitHubLogin(){
 const url=new URL(location.href);if(!url.searchParams.has('code')&&!url.searchParams.has('error'))return null;
 const code=url.searchParams.get('code'),state=url.searchParams.get('state'),failure=url.searchParams.get('error');
 url.searchParams.delete('code');url.searchParams.delete('state');url.searchParams.delete('error');url.searchParams.delete('error_description');url.searchParams.delete('error_uri');history.replaceState(null,'',url.href);
 let pending;try{pending=JSON.parse(sessionStorage.getItem(KEY)||'null')}finally{sessionStorage.removeItem(KEY)}
 if(!pending||state!==pending.state||Date.now()-pending.time>600000)throw Error('OAuth state is missing, expired or invalid. Sign in again.');
 if(failure||!code)throw Error('GitHub authorization was cancelled or denied.');
 const relay=await config();if(relay!==pending.relay)throw Error('OAuth configuration changed; sign in again.');
 const res=await fetch(relay,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,verifier:pending.verifier}),credentials:'omit',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(20000)});const d=await res.json();if(!res.ok||typeof d.access_token!=='string')throw Error(d.error||'GitHub authorization failed');return d.access_token;
}
export function clearPendingLogin(){sessionStorage.removeItem(KEY)}
