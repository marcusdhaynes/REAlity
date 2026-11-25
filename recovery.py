"""Local-first recovery workbench. No target execution in static mode."""
import argparse, hashlib, json, os, re, shutil, stat, struct, subprocess, zipfile
from datetime import datetime, timezone
from pathlib import Path
from embedded import extract_asar, recover_sourcemap
MAX_FILES=20000
MAX_EXPAND=4*1024**3
MAX_DEPTH=3
SOURCE={'.cs','.vb','.fs','.java','.kt','.js','.mjs','.cjs','.ts','.tsx','.jsx','.html','.css','.scss','.py','.rs','.c','.cpp','.h','.hpp','.go','.lua','.qml','.xaml','.svelte','.vue','.sln','.csproj','.fsproj','.vbproj','.toml','.json','.map','.gradle'}
ASSETS={'.png','.jpg','.jpeg','.svg','.ico','.gif','.webp','.bmp','.ttf','.otf','.woff','.woff2','.wav','.mp3','.ogg','.mp4','.glb','.gltf'}
TOOLS={'rea':['rea'],'craft':['craft-anything-cli'],'ilspy':['ilspycmd'],'asar':['asar'],'jadx':['jadx'],'7zip':['7z','7za'],'die':['diec'],'pyinstxtractor':['pyinstxtractor-ng']}

def locate(name):
    for n in TOOLS[name]:
        found=shutil.which(n)
        if found:return found
    if name=='7zip' and os.name=='nt':
        p=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'7-Zip/7z.exe'
        if p.is_file():return str(p)
    return None

def hashfile(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def inspect(p):
    with p.open('rb') as f:
        b=f.read(8*1024*1024)
        result={'format':'unknown','markers':[],'size':p.stat().st_size}
        if b[:2]==b'MZ' and len(b)>=64:
            off=struct.unpack_from('<I',b,60)[0]
            if off+24<=len(b) and b[off:off+4]==b'PE\0\0':
                machine,n=struct.unpack_from('<HH',b,off+4); optlen=struct.unpack_from('<H',b,off+20)[0]; opt=off+24
                result.update(format='PE',architecture={0x14c:'x86',0x8664:'x64',0xaa64:'ARM64'}.get(machine,hex(machine)),sections=n)
                if opt+2<=len(b):
                    magic=struct.unpack_from('<H',b,opt)[0]; dd={0x10b:96,0x20b:112}.get(magic)
                    if dd is not None and optlen>=dd+15*8 and opt+dd+15*8<=len(b):
                        rva,size=struct.unpack_from('<II',b,opt+dd+14*8)
                        if rva and size:result['markers'].append('managed CLR directory')
        elif b.startswith(b'\x7fELF'):result['format']='ELF'
        elif b.startswith(b'PK\x03\x04'):result['format']='ZIP'
        elif b.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):result['format']='OLE compound file (possibly MSI)'
        elif p.suffix.lower()=='.asar':result['format']='ASAR candidate'
        elif b.startswith(b'dex\n'):result['format']='DEX'
        elif b.startswith(b'\xca\xfe\xba\xbe'):result['format']='Java class or fat Mach-O'
        lower=b.lower()
        for needle,label in [(b'PyInstaller','PyInstaller marker'),(b'python3','Python marker'),(b'WebView2','WebView2 marker'),(b'electron','Electron marker'),(b'UPX!','UPX marker'),(b'Go build ID','Go marker'),(b'UnityPlayer','Unity marker')]:
            if needle.lower() in lower:result['markers'].append(label)
        f.seek(max(0,result['size']-1024*1024)); tail=f.read()
        if b'MEI\x0c\x0b\x0a\x0b\x0e' in tail:result['markers'].append('PyInstaller archive cookie')
        result['strings_sample']=[s.decode('ascii') for s in re.findall(rb'[ -~]{8,}',b)[:300]]
        return result

def safe_name(name):
    name=name.replace('\\','/'); parts=name.split('/')
    if name.startswith('/') or any(x in ('..','.') or ':' in x or '\x00' in x or x.endswith(('.', ' ')) or x.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for x in parts if x):raise ValueError('unsafe archive member: '+name)
    if not any(parts):raise ValueError('empty archive member')
    return Path(*[x for x in parts if x])

def extract_zip(src,dest,budget):
    dest.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(src) as z:
        seen=set(); plan=[]; size=0
        for i in z.infolist():
            rel=safe_name(i.filename); key=str(rel).casefold()
            if key in seen:raise ValueError('duplicate archive member: '+i.filename)
            seen.add(key)
            if stat.S_ISLNK(i.external_attr>>16):raise ValueError('archive symlink rejected')
            if i.flag_bits&1:raise ValueError('encrypted member: '+i.filename)
            size+=i.file_size; plan.append((i,rel))
        if budget['files']+len(plan)>MAX_FILES or budget['bytes']+size>MAX_EXPAND:raise ValueError('archive expansion budget exceeded')
        budget['files']+=len(plan);budget['bytes']+=size
        for i,rel in plan:
            out=dest/rel
            if i.is_dir():out.mkdir(parents=True,exist_ok=True);continue
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(i) as a,out.open('xb') as b:shutil.copyfileobj(a,b,1024*1024)

def walk(p):
    if p.is_file():yield p;return
    for root,dirs,files in os.walk(p,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not Path(root,d).is_symlink() and not getattr(Path(root,d).lstat(),'st_file_attributes',0)&0x400)
        for name in sorted(files):
            f=Path(root,name)
            if not f.is_symlink() and f.is_file() and not getattr(f.lstat(),'st_file_attributes',0)&0x400:yield f

def tool_command(name, exe):
    """Resolve known npm shims to their installed Node entry point without a shell."""
    p=Path(exe).resolve()
    if p.suffix.lower() not in {'.cmd','.bat'}:return [str(p)]
    packages={'rea':('rea-agents',),'asar':('@electron/asar','asar')}
    node=shutil.which('node')
    if not node:return None
    for package in packages.get(name,()):
        for base in (p.parent/'node_modules',p.parent.parent/'node_modules'):
            root=(base/package).resolve()
            try:
                meta=json.loads((root/'package.json').read_text(encoding='utf-8'))
                if meta.get('name')!=package:continue
                entry=meta.get('bin')
                if isinstance(entry,dict):entry=entry.get(p.stem) or entry.get(name)
                if not isinstance(entry,str):continue
                script=(root/entry).resolve()
                if root in script.parents and script.is_file():return [node,str(script)]
            except (OSError,ValueError):continue
    return None

def run_tool(name,args,log,cwd,timeout=600):
    exe=locate(name)
    if not exe:return {'tool':name,'status':'not installed','arguments':args}
    prefix=tool_command(name,exe)
    if not prefix:return {'tool':name,'status':'unsupported launcher; install native CLI or supported npm package','arguments':args}
    command=[*prefix,*map(str,args)]
    with log.open('wb') as f:
        try:
            proc=subprocess.run(command,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,check=False,stdin=subprocess.DEVNULL)
            return {'tool':name,'status':'completed' if proc.returncode==0 else 'failed','exit':proc.returncode,'log':str(log),'arguments':args}
        except (OSError,subprocess.TimeoutExpired) as e:return {'tool':name,'status':'failed','error':str(e),'log':str(log)}

def recover(target,out,external=False,emit=print):
    target=Path(target).resolve(strict=True);out=Path(out).resolve()
    if target.is_dir() and (out==target or target in out.parents):raise ValueError('Choose output outside target directory')
    out.mkdir(parents=True,exist_ok=False)
    for n in ('Original','Extracted','Source','Assets','Dependencies','Analysis','Reconstructed','Tests'): (out/n).mkdir()
    report={'schema':1,'target':str(target),'created':datetime.now(timezone.utc).isoformat(),'files':[],'tools':[],'warnings':[],'validation':'not run','ai_used':False,'provider_availability':{k:bool(locate(k)) for k in TOOLS}}
    original=out/'Original'; roots=[];budget={'files':0,'bytes':0}
    def save():
        (out/'Analysis/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    try:
        for i,p in enumerate(walk(target)):
            if i>=MAX_FILES:raise ValueError('input file count exceeds limit')
            rel=p.relative_to(target) if target.is_dir() else Path(p.name); dest=original/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            before=hashfile(p);shutil.copy2(p,dest);after=hashfile(dest)
            if before!=after:raise ValueError('file changed while preserving: '+str(p))
            roots.append((dest,0));report['files'].append({'path':str(dest.relative_to(out)),'sha256':after,'kind':'original'})
        emit(f'Preserved {len(roots)} original files.'); save()
        j=0
        while j<len(roots):
            p,depth=roots[j];j+=1
            if zipfile.is_zipfile(p) and depth<MAX_DEPTH:
                d=out/'Extracted'/f'{j:05d}-{p.stem}'
                try:
                    extract_zip(p,d,budget);roots.extend((q,depth+1) for q in walk(d));emit('Extracted '+p.name)
                except Exception as e:report['warnings'].append(f'{p.name}: {e}');shutil.rmtree(d,ignore_errors=True)
            elif zipfile.is_zipfile(p):report['warnings'].append('Nested archive depth limit: '+p.name)
            ext=p.suffix.lower(); rel=p.relative_to(out)
            if ext=='.asar' and depth<MAX_DEPTH:
                d=out/'Extracted'/f'{j:05d}-asar'
                try:
                    warnings=extract_asar(p,d,budget,MAX_FILES,MAX_EXPAND)
                    report['warnings'].extend(f'{p.name}: {w}' for w in warnings)
                    roots.extend((q,depth+1) for q in walk(d));emit('Extracted packed ASAR '+p.name)
                except Exception as e:
                    report['warnings'].append(f'{p.name}: {e}');shutil.rmtree(d,ignore_errors=True)
            elif ext=='.asar':report['warnings'].append('ASAR depth limit: '+p.name)
            if ext=='.map':
                d=out/'Source'/f'{j:05d}-embedded-sources'
                try:
                    result=recover_sourcemap(p,d,budget,MAX_FILES,MAX_EXPAND)
                    report.setdefault('source_maps',[]).append({'origin':str(rel),'output':str(d.relative_to(out)),**result})
                    for item in result['recovered']:
                        f=d/item['file'];report['files'].append({'path':str(f.relative_to(out)),'sha256':hashfile(f),'kind':'embedded source map text','origin':str(rel),'source_name':item['original_source']})
                except Exception as e:
                    report['warnings'].append(f'{p.name}: {e}');shutil.rmtree(d,ignore_errors=True)
            if ext in SOURCE or ext in ASSETS or ext in {'.dll','.so','.dylib','.lib','.pdb','.jar'}:
                cat='Source' if ext in SOURCE else 'Assets' if ext in ASSETS else 'Dependencies'; d=out/cat/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
                report['files'].append({'path':str(d.relative_to(out)),'sha256':hashfile(d),'kind':'copied candidate','origin':str(rel)})
            if ext not in {'.exe','.dll','.msi','.asar','.apk','.jar','.zip','.pyc','.so','.dylib','.ipa'}:continue
            meta=inspect(p);report['files'].append({'path':str(rel),'sha256':hashfile(p),'kind':'inspection','metadata':meta})
            emit(f'Inspecting {p.name}: {meta["format"]}'); tag=f'{j:05d}'
            jobs=[]
            if 'managed CLR directory' in meta['markers']:
                d=out/'Source'/('decompiled-'+tag);d.mkdir();jobs.append(('ilspy',['-p','-o',str(d),str(p)]))
            elif meta['format']=='PE':jobs.append(('rea',['analyze',str(p),'--provider','ghidra','--json']))
            if ext=='.asar':
                jobs.append(('rea',['analyze-javascript-application',str(p),'--json']))
            if ext in {'.apk','.jar'}:
                d=out/'Source'/('jadx-'+tag);d.mkdir();jobs.append(('jadx',['-d',str(d),str(p)]))
            if any('PyInstaller' in m for m in meta['markers']):jobs.append(('pyinstxtractor',[str(p)]))
            if ext in {'.exe','.msi'}:jobs.append(('die',[str(p)]))
            for name,args in jobs:
                if external:
                    emit('Running '+name+' on '+p.name);result=run_tool(name,args,out/'Analysis'/f'{tag}-{name}.log',out/'Extracted')
                else:result={'tool':name,'status':'not run (static mode)','arguments':args}
                report['tools'].append(result)
            save()
        report['status']='inspection complete; source reconstruction and behavioral validation not performed'
    except Exception as e:
        report['status']='partial';report['warnings'].append(str(e));save();raise
    finally:
        save()
        (out/'README.md').write_text('# REAlity Recovery Workspace\n\nOriginal contains hash-verified copies. Source contains source candidates and any provider output; it is not necessarily buildable. Analysis/report.json records evidence, warnings, and provider results. Reconstructed and Tests are reserved for agent-generated work. Never execute an unknown target outside isolation.\n\nStatus: '+report.get('status','partial')+'\n',encoding='utf-8')
        (out/'Reconstructed/RECOVERY_TASK.md').write_text('Reconstruct only from the preserved evidence. Keep Original immutable. First inventory recoverable source and build manifests; record unknowns; rebuild in this folder, never overwrite evidence. Test against the original in an isolated VM with non-production data. Report compilation and behavioral differences separately. Do not claim parity without tests.\n',encoding='utf-8')
    emit('Workspace ready: '+str(out));return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('target',nargs='?');ap.add_argument('output',nargs='?');ap.add_argument('--external',action='store_true');ap.add_argument('--doctor',action='store_true');a=ap.parse_args()
    if a.doctor:print(json.dumps({k:locate(k) for k in TOOLS},indent=2));return
    if not a.target or not a.output:ap.error('target and output required')
    recover(a.target,a.output,a.external)
if __name__=='__main__':main()
