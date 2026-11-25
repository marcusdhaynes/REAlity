"""Offline extraction of ASAR bundles and embedded source-map text.

No target execution, network access, or external dependencies.
"""
import json
import re
import struct
from pathlib import Path

MAX_HEADER = 32 * 1024 * 1024
MAX_MAP = 64 * 1024 * 1024

def _component(name):
    if not isinstance(name, str) or not name or name in ('.', '..') or re.search(r'[\\/:*?"<>|\x00-\x1f]', name) or name.endswith(('.', ' ')):
        raise ValueError('unsafe bundle member: ' + repr(name))
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
        raise ValueError('reserved bundle member: ' + name)
    return name

def _reserve(budget, count, size, max_files, max_bytes):
    if budget['files'] + count > max_files or budget['bytes'] + size > max_bytes:
        raise ValueError('extraction budget exceeded')
    budget['files'] += count
    budget['bytes'] += size

def extract_asar(src, dest, budget, max_files, max_bytes):
    """Extract packed entries only; report links and unpacked companions separately."""
    src, dest = Path(src), Path(dest)
    warnings, plan, seen = [], [], set()
    with src.open('rb') as f:
        prefix = f.read(8)
        if len(prefix) != 8:
            raise ValueError('truncated ASAR prefix')
        payload, header_size = struct.unpack('<II', prefix)
        if payload != 4 or not 8 <= header_size <= MAX_HEADER:
            raise ValueError('invalid ASAR header size')
        header = f.read(header_size)
        if len(header) != header_size:
            raise ValueError('truncated ASAR header')
        payload_size, text_size = struct.unpack_from('<II', header)
        if payload_size + 4 != header_size or text_size > payload_size - 4:
            raise ValueError('invalid ASAR pickle')
        root = json.loads(header[8:8+text_size])
        base = 8 + header_size
        available = src.stat().st_size - base
        def visit(nodes, parts=()):
            if not isinstance(nodes, dict) or len(parts) > 64:
                raise ValueError('invalid or deeply nested ASAR directory')
            for name, node in nodes.items():
                path = (*parts, _component(name))
                key = '/'.join(path).casefold()
                if key in seen or len(seen) >= max_files:
                    raise ValueError('duplicate member or member limit exceeded')
                seen.add(key)
                if not isinstance(node, dict):
                    raise ValueError('invalid ASAR entry')
                if 'files' in node:
                    visit(node['files'], path)
                elif node.get('unpacked') or 'link' in node:
                    warnings.append('Skipped unpacked or linked member: ' + '/'.join(path))
                else:
                    size = node.get('size')
                    offset = node.get('offset')
                    if not isinstance(size, int) or isinstance(size, bool) or size < 0 or not isinstance(offset, str) or not re.fullmatch(r'[0-9]{1,20}', offset):
                        raise ValueError('invalid ASAR file range')
                    offset = int(offset)
                    if offset + size > available:
                        raise ValueError('ASAR entry outside archive')
                    plan.append((path, offset, size))
        visit(root['files'])
        _reserve(budget, len(seen), sum(size for _,_,size in plan), max_files, max_bytes)
        dest.mkdir(parents=True, exist_ok=False)
        for parts, offset, size in plan:
            out = dest.joinpath(*parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            f.seek(base + offset)
            with out.open('xb') as target:
                remaining = size
                while remaining:
                    chunk = f.read(min(remaining, 1024*1024))
                    if not chunk:
                        raise ValueError('truncated ASAR member')
                    target.write(chunk)
                    remaining -= len(chunk)
    return warnings

def recover_sourcemap(src, dest, budget, max_files, max_bytes):
    """Recover embedded sourcesContent verbatim; never follow URLs or disk paths."""
    src, dest = Path(src), Path(dest)
    if src.stat().st_size > MAX_MAP:
        raise ValueError('source map exceeds size limit')
    with src.open(encoding='utf-8-sig') as f:
        data = json.load(f)
    if not isinstance(data, dict) or data.get('version') != 3:
        raise ValueError('not a version 3 source map')
    plan, missing = [], []
    def visit(obj, depth=0):
        if depth > 16 or not isinstance(obj, dict):
            raise ValueError('invalid indexed map')
        if 'sections' in obj:
            for section in obj['sections']:
                if 'map' in section:
                    visit(section['map'], depth+1)
                else:
                    missing.append('external indexed section (not fetched)')
            return
        names, contents = obj.get('sources', []), obj.get('sourcesContent') or []
        if not isinstance(names, list) or not isinstance(contents, list):
            raise ValueError('invalid source map lists')
        for i, name in enumerate(names):
            if len(plan) + len(missing) >= max_files:
                raise ValueError('source map file limit exceeded')
            name = str(name)
            if i >= len(contents) or not isinstance(contents[i], str):
                missing.append(name)
                continue
            leaf = re.split(r'[/\\]', name)[-1].split('?')[0]
            leaf = re.sub(r'[^a-zA-Z0-9_.-]', '_', leaf)[:120].strip('. ') or 'source.txt'
            path = f'{len(plan):06d}-{leaf}'
            plan.append((path, name, contents[i].encode('utf-8')))
    visit(data)
    _reserve(budget, len(plan), sum(len(b) for _,_,b in plan), max_files, max_bytes)
    if not plan:
        return {'recovered': [], 'missing': missing}
    dest.mkdir(parents=True, exist_ok=False)
    manifest = []
    for path, name, content in plan:
        with (dest/path).open('xb') as f:
            f.write(content)
        manifest.append({'file': path, 'original_source': name})
    return {'recovered': manifest, 'missing': missing}
