"""Windows UI Automation evidence collector. Run ONLY in a disposable interactive VM.
Requires Python 3.12 and pywinauto. Launches an explicitly selected local EXE
once per case; never executes code or command lines from a contract.
"""
import argparse, hashlib, json, os, re, subprocess, time
from pathlib import Path

KEYS={'Enter':'{ENTER}','Tab':'{TAB}','Escape':'{ESC}','Space':'{SPACE}','Backspace':'{BACKSPACE}','ArrowUp':'{UP}','ArrowDown':'{DOWN}','ArrowLeft':'{LEFT}','ArrowRight':'{RIGHT}'}
OPS={'click','fill','press','observeText','observeValue','observeVisible'}
def identifier(x):
    return isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}',x) and x not in ('__proto__','constructor','prototype')
def string(x):
    return isinstance(x,str) and len(x)<=4000
def exact(x,required,optional=()):
    return isinstance(x,dict) and set(required)<=x.keys() and x.keys()<=set(required)|set(optional)
def validate(s):
    if not exact(s,('version','cases')) or s.get('version')!=1 or not isinstance(s.get('cases'),list) or not 1<=len(s['cases'])<=30:raise ValueError('Invalid contract')
    cases=set()
    for c in s['cases']:
        if not exact(c,('id','steps')) or not identifier(c.get('id')) or c['id'] in cases or not isinstance(c.get('steps'),list) or not 1<=len(c['steps'])<=40:raise ValueError('Invalid case')
        cases.add(c['id']);steps=set();observed=0
        for t in c['steps']:
            if not exact(t,('id','op','targets'),('value','expected','settleMs')) or not identifier(t.get('id')) or t['id'] in steps or t.get('op') not in OPS:raise ValueError('Invalid step')
            steps.add(t['id'])
            if not exact(t['targets'],('native','web')):raise ValueError('Invalid targets')
            n=t['targets']['native'];w=t['targets']['web']
            if not exact(n,('by','value'),('controlType',)) or n.get('by') not in ('auto_id','title') or not string(n.get('value')) or not n['value'].strip() or not string(w) or not w.strip():raise ValueError('Invalid selector')
            if 'controlType' in n and (not string(n['controlType']) or not re.fullmatch('[A-Za-z]+',n['controlType'])):raise ValueError('Invalid control type')
            if 'settleMs' in t and (type(t['settleMs']) is not int or not 0<=t['settleMs']<=5000):raise ValueError('Invalid settle interval')
            if (t['op'] not in ('fill','press') and 'value' in t) or (not t['op'].startswith('observe') and 'expected' in t):raise ValueError('Unexpected field')
            if t['op'] in ('fill','press') and not string(t.get('value')):raise ValueError('Invalid input')
            if t['op']=='press' and t['value'] not in KEYS:raise ValueError('Invalid portable key')
            if t['op'].startswith('observe'):
                observed+=1
                if 'expected' in t and (not isinstance(t['expected'],bool) if t['op']=='observeVisible' else not string(t['expected'])):raise ValueError('Invalid expected value')
        if not observed:raise ValueError('Missing observation')
    return s
def digest(s):
    # Canonical UTF-8 JSON; contract field names are ASCII.
    return hashlib.sha256(json.dumps(s,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
def locate(app,selector,allow_missing=False):
    deadline=time.monotonic()+5
    while True:
        matches=[]
        for window in app.windows():
            for element in [window,*window.descendants()]:
                info=element.element_info
                if selector.get('controlType') and info.control_type!=selector['controlType']:continue
                value=info.automation_id if selector['by']=='auto_id' else info.name
                if value==selector['value']:matches.append(element)
        if len(matches)==1:return matches[0]
        if len(matches)>1:raise ValueError('Ambiguous native selector; refine automation ID or control type')
        if time.monotonic()>=deadline:
            if allow_missing:return None
            raise ValueError('Native control not found')
        time.sleep(.2)
def perform(app,t):
    op=t['op'];element=locate(app,t['targets']['native'],op=='observeVisible')
    if op=='observeVisible':return bool(element is not None and element.is_visible())
    if op=='click':
        # UIA InvokePattern, not arbitrary coordinates or global shell commands.
        element.invoke()
    elif op=='fill':element.set_edit_text(t['value'])
    elif op=='press':element.type_keys(KEYS[t['value']],set_foreground=True)
    elif op=='observeText':return str(element.window_text())
    elif op=='observeValue':return str(element.iface_value.CurrentValue)
    return None
def run_case(exe,c):
    from pywinauto import Application
    observations=[];error=None;process=None
    try:
        process=subprocess.Popen([str(exe)],cwd=str(exe.parent),shell=False)
        app=Application(backend='uia').connect(process=process.pid,timeout=15)
        for t in c['steps']:
            try:
                if process.poll() is not None:raise RuntimeError('Original process exited')
                if t.get('settleMs'):time.sleep(t['settleMs']/1000)
                value=perform(app,t)
                observations.append({'id':t['id'],'ok':True,**({'value':value} if t['op'].startswith('observe') else {})})
            except Exception as e:
                observations.append({'id':t['id'],'ok':False,'error':str(e)[:400]})
                break # Do not measure subsequent state after failed interaction.
    except Exception as e:error=str(e)[:400]
    finally:
        if process is not None and process.poll() is None:
            # Stop this instance only. Dispose the entire VM after the run.
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    return {'id':c['id'],'steps':observations,**({'error':error} if error else {})}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe');p.add_argument('contract');p.add_argument('output');p.add_argument('--authorized-isolated-vm',action='store_true',required=True);a=p.parse_args()
    if os.name!='nt':raise SystemExit('Windows interactive VM required')
    exe=Path(a.exe).resolve(strict=True);contract=Path(a.contract);out=Path(a.output)
    if not exe.is_file() or exe.suffix.lower()!='.exe' or contract.stat().st_size>512*1024 or out.exists():raise SystemExit('Select an EXE, bounded contract, and new output file')
    s=validate(json.loads(contract.read_text(encoding='utf-8')))
    with exe.open('rb') as f:target_hash=hashlib.file_digest(f,'sha256').hexdigest()
    evidence={'version':1,'side':'native','adapter':'Windows UI Automation (pywinauto)','targetSha256':target_hash,'contractSha256':digest(s),'cases':[run_case(exe,c) for c in s['cases']]}
    with out.open('x',encoding='utf-8') as f:json.dump(evidence,f,ensure_ascii=False,indent=2)
    if any(c.get('error') or any(not x['ok'] for x in c['steps']) for c in evidence['cases']):raise SystemExit(1)
if __name__=='__main__':main()
