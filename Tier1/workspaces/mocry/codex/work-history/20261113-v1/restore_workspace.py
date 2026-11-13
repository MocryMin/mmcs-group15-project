"""Restore original course-relative study layout or a historical release's payloads.

python restore_workspace.py --destination NEW_EMPTY_DIRECTORY
python restore_workspace.py --release ORIGINAL_ZIP_NAME --destination NEW_EMPTY_DIRECTORY
No existing destination file is overwritten. The original ZIP container is not recreated.
"""
from pathlib import Path,PurePosixPath
import argparse,json,hashlib
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--destination',required=True)
parser.add_argument('--release')
args=parser.parse_args()
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'agent_protocol.md').exists())
BASE='workspaces/mocry/codex/work-history/20261113-v1'
out=Path(args.destination).resolve()
if out.exists() and any(out.iterdir()):raise SystemExit('Choose an empty destination directory.')
out.mkdir(parents=True,exist_ok=True);tasks=[]
for tier in ('Tier1','Tier2'):
    root=REPO/tier/BASE
    if args.release:
        manifest=root/'release_manifests'/(args.release+'.json')
        if manifest.exists():
            for r in json.loads(manifest.read_text(encoding='utf-8'))['entries']:
                if 'excluded' not in r:tasks.append((REPO/r['repository_path'],r['entry'],r['sha256']))
    else:
        for r in json.loads((root/'CONTENT_MANIFEST.json').read_text(encoding='utf-8'))['files']:
            if '!' in r['source'] or r['source'].endswith(' (entry manifest)'):continue
            tasks.append((root/r['path'],r['source'],r['sha256']))
if not tasks:raise SystemExit('No matching payloads found.')
for source,name,h in tasks:
    rel=PurePosixPath(name)
    assert not rel.is_absolute() and '..' not in rel.parts
    dest=out/name;assert dest.resolve().is_relative_to(out)
    data=source.read_bytes();assert hashlib.sha256(data).hexdigest()==h
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert dest.read_bytes()==data
    else:dest.write_bytes(data)
print(f'Restored {len(tasks)} payloads to {out}; consult the manifest for exclusions.')
