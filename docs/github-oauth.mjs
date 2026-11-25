// GitHub Pages + dedicated Supabase Auth. No Vercel or custom OAuth relay.
const CALLBACK='https://marcusdhaynes.github.io/REAlity/';
const KEY='reality.supabase.oauth.pending.v2';
function b64(bytes){return btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
function validateConfig(c){
 if(!c||typeof c.supabaseUrl!=='string'||typeof c.publishableKey!=='string'||!c.supabaseUrl||!c.publishableKey)throw Error('GitHub sign-in is not configured: the REAlity administrator must activate its dedicated Supabase GitHub provider.');
 const u=new URL(c.supabaseUrl);
 if(u.protocol!=='https:'||!/^[-a-z0-9]+\.supabase\.co$/.test(u.hostname)||u.username||u.password||u.port||u.pathname!=='/'||u.search||u.hash)throw Error('Invalid Supabase project URL.');
 if(!/^sb_publishable_[A-Za-z0-9_-]+$/.test(c.publishableKey))throw Error('Use a Supabase publishable key, never a secret or service-role key.');
 return {url:u.origin,key:c.publishableKey};
}
async function config(){const r=await fetch('./auth-config.json',{cache:'no-store',redirect:'error'});if(!r.ok)throw Error('Authentication configuration unavailable.');return validateConfig(await r.json())}
export async function startGitHubLogin(){
 const c=await config(),verifier=b64(crypto.getRandomValues(new Uint8Array(48)));
 const challenge=b64(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))));
 sessionStorage.setItem(KEY,JSON.stringify({verifier,time:Date.now(),url:c.url}));
 const url=new URL(c.url+'/auth/v1/authorize');
 url.search=new URLSearchParams({provider:'github',redirect_to:CALLBACK,scopes:'public_repo workflow',code_challenge:challenge,code_challenge_method:'s256'}).toString();
 location.assign(url.href);
}
export async function finishGitHubLogin(){
 const url=new URL(location.href);if(!url.searchParams.has('code')&&!url.searchParams.has('error'))return null;
 const code=url.searchParams.get('code'),failure=url.searchParams.get('error');
 for(const k of ['code','state','error','error_code','error_description','error_uri'])url.searchParams.delete(k);
 history.replaceState(null,'',url.href);
 let pending;try{pending=JSON.parse(sessionStorage.getItem(KEY)||'null')}finally{clearPendingLogin()}
 if(failure)throw Error('GitHub authorization was cancelled or failed.');
 if(!pending||typeof pending.verifier!=='string'||Date.now()-pending.time>600000||!code)throw Error('Sign-in request missing or expired. Continue With GitHub again.');
 const c=await config();if(c.url!==pending.url)throw Error('Authentication project changed; sign in again.');
 const res=await fetch(c.url+'/auth/v1/token?grant_type=pkce',{method:'POST',headers:{apikey:c.key,'Content-Type':'application/json'},body:JSON.stringify({auth_code:code,code_verifier:pending.verifier}),credentials:'omit',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(20000)});
 const data=await res.json();
 if(!res.ok||typeof data.provider_token!=='string'||!data.provider_token)throw Error('GitHub authorization could not be completed or the provider token was not returned.');
 return data.provider_token;
}
export function clearPendingLogin(){sessionStorage.removeItem(KEY)}
