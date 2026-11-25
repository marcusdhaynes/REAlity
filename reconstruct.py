"""Explicit, separately launched Craft Anything reconstruction handoff."""
import json
import os
import shlex
import subprocess
from pathlib import Path
from recovery import locate, tool_command

def build_command(workspace):
    root=Path(workspace).resolve(strict=True)
    report=json.loads((root/'Analysis'/'report.json').read_text(encoding='utf-8'))
    if not report.get('status','').startswith('inspection complete'):
        raise ValueError('Finish static recovery before reconstruction.')
    original=root/'Original'
    if not original.is_dir():
        raise ValueError('Preserved input missing.')
    entries=list(original.iterdir())
    target=entries[0] if len(entries)==1 and entries[0].is_file() else original
    if not target.exists():
        raise ValueError('Preserved input missing.')
    project=root/'Reconstructed'/'CraftProject'
    if project.exists():
        raise ValueError('CraftProject already exists. Continue it inside Craft Anything.')
    exe=locate('craft')
    if not exe:
        raise FileNotFoundError('Install the official Craft Anything CLI and add it to PATH.')
    prefix=tool_command('craft',exe)
    if not prefix:
        raise ValueError('Unsupported Craft Anything launcher.')
    request=(
        'Recover my own lost software development project. Prioritize exact recoverable source, '
        'resources, dependencies and build manifests over speculative rewriting. '
        'Inspect the preserved target and read the recovery evidence at '+str(root/'Analysis'/'report.json')+
        ' and the recovered source under '+str(root/'Source')+
        '. Write editable source only inside the new project. Never modify the original evidence. '
        'Document recovered versus inferred code, unresolved components, build commands, '
        'and verified versus unverified behavior. Do not assume full equivalence. '
        'Do not run the original or use real credentials outside an isolated test environment.'
    )
    return [*prefix,'--deep','rebuild',str(target),request,'--project-folder',str(project),'--rounds','2']

def command_text(args):
    return subprocess.list2cmdline(args) if os.name=='nt' else shlex.join(args)

def launch_windows(args):
    if os.name!='nt':
        raise OSError('Use the displayed command in an interactive terminal.')
    return subprocess.Popen(args,creationflags=subprocess.CREATE_NEW_CONSOLE)
