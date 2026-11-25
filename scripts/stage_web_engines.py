"""Stage pinned upstream browser engines; optional failures do not block Pages."""
import hashlib, json, pathlib, re, shutil, subprocess, tempfile, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
VENDOR=ROOT/'docs'/'vendor'
CRAFT='0.6.1'
V86='0.5.473'
BIOS_REF='9457e7a2f6890f3133bb6ac0f749e588f63c4c36'
def download(url,p,limit):
    with urllib.request.urlopen(url,timeout=90) as r,p.open('wb') as out:
        total=0
        while chunk:=r.read(1024*1024):
            total+=len(chunk)
            if total>limit:raise ValueError('Download exceeds limit')
            out.write(chunk)
def craft(tmp,dest):
    base=f'https://github.com/storytold/craft-anything/releases/download/v{CRAFT}/'
    name=f'craft-anything-web-{CRAFT}.zip'
    z=tmp/name; sums=tmp/'SHA256SUMS.txt'
    download(base+name,z,128*1024*1024)
    download(base+'SHA256SUMS.txt',sums,2*1024*1024)
    digest=None
    for line in sums.read_text().splitlines():
        m=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(.+)',line.strip())
        if m and m.group(2).removeprefix('./')==name:digest=m.group(1).lower()
    if not digest or hashlib.sha256(z.read_bytes()).hexdigest()!=digest:raise ValueError('Craft archive checksum mismatch')
    with zipfile.ZipFile(z) as archive:
        prefix=f'craft-anything-web-{CRAFT}/';seen=set();total=0
        for item in archive.infolist():
            if item.is_dir():continue
            if not item.filename.startswith(prefix):raise ValueError('Unexpected archive layout')
            rel=pathlib.PurePosixPath(item.filename[len(prefix):])
            if rel.is_absolute() or '..' in rel.parts or not rel.parts or '\\' in str(rel):raise ValueError('Unsafe archive path')
            if str(rel).casefold() in seen:raise ValueError('Duplicate archive path')
            seen.add(str(rel).casefold());total+=item.file_size
            if total>128*1024*1024:raise ValueError('Expanded archive too large')
            output=dest.joinpath(*rel.parts);output.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(item) as src,output.open('xb') as out:shutil.copyfileobj(src,out)
    if not (dest/'index.html').is_file() or not list(dest.glob('*.wasm')):raise ValueError('WASM viewer missing')
def emulator(tmp,dest):
    subprocess.run(['npm','install','--ignore-scripts','--no-audit','--no-fund','--no-package-lock','--prefix',str(tmp),f'v86@{V86}'],check=True,timeout=120)
    p=tmp/'node_modules'/'v86'
    for name in ('libv86.mjs','v86.wasm'):
        shutil.copyfile(p/'build'/name,dest/name)
    for name in ('LICENSE','Readme.md'):
        if (p/name).is_file():shutil.copyfile(p/name,dest/name)
    for name in ('seabios.bin','vgabios.bin'):
        download(f'https://raw.githubusercontent.com/copy/v86/{BIOS_REF}/bios/{name}',dest/name,2*1024*1024)
    download(f'https://raw.githubusercontent.com/copy/v86/{BIOS_REF}/src/iso9660.js',dest/'iso9660.mjs',256*1024)
    iso=dest/'iso9660.mjs'
    code=iso.read_text()
    expected='import { dbg_assert } from "./log.js";'
    if expected not in code:raise ValueError('Unexpected ISO generator source')
    iso.write_text(code.replace(expected,'function dbg_assert(ok){if(!ok)throw new Error("ISO generator assertion failed");}',1))
    # Preserve firmware notices and corresponding source references.
    (dest/'FIRMWARE-SOURCES.txt').write_text('SeaBIOS / VGA BIOS binaries from copy/v86 commit '+BIOS_REF+'\nhttps://github.com/copy/v86/tree/'+BIOS_REF+'/bios\nhttps://github.com/coreboot/seabios\nSee upstream BIOS directory and licenses.\n')
def main():
    VENDOR.mkdir(exist_ok=True)
    status={}
    for name,version,fn in [('craft',CRAFT,craft),('v86',V86,emulator)]:
        dest=VENDOR/name
        shutil.rmtree(dest,ignore_errors=True);dest.mkdir()
        try:
            with tempfile.TemporaryDirectory() as temp:fn(pathlib.Path(temp),dest)
            status[name]={'available':True,'version':version}
        except Exception as exc:
            shutil.rmtree(dest,ignore_errors=True)
            status[name]={'available':False,'version':version,'reason':str(exc)[:250]}
            print('::warning::'+name+' optional engine staging failed')
    (VENDOR/'status.json').write_text(json.dumps(status,indent=2))
if __name__=='__main__':main()
