"""Validate both published tiers, including exact historical release payloads."""
from pathlib import Path
import json,hashlib,re
HERE=Path(__file__).resolve().parent
REPO=next((p for p in HERE.parents if (p/'agent_protocol.md').exists()),None)
if REPO is None:REPO=HERE.parent/'group-collaboration'
BASE='workspaces/mocry/codex/work-history/20261113-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
verified={};reports={}
for tier in ('Tier1','Tier2'):
    root=REPO/tier/BASE;m=json.loads((root/'CONTENT_MANIFEST.json').read_text(encoding='utf-8'));seen=set()
    for r in m['files']:
        assert r['path'] not in seen,r['path'];seen.add(r['path'])
        p=root/r['path'];assert p.resolve().is_relative_to(root.resolve())
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
        assert p.stat().st_size<100*1024**2,str(p)
        verified[p.relative_to(REPO).as_posix()]=r['sha256']
    reports[tier]={'files':len(seen),'bytes':sum(r['bytes'] for r in m['files']),'studies':len(m['studies'])}
for tier in ('Tier1','Tier2'):
    root=REPO/tier/BASE;entry_count=0;exclusions=0
    for p in (root/'release_manifests').glob('*.json'):
        for r in json.loads(p.read_text(encoding='utf-8'))['entries']:
            if 'excluded' in r:exclusions+=1;continue
            assert verified.get(r['repository_path'])==r['sha256'],str(p)+' '+r['entry'];entry_count+=1
    for ref in re.findall(r'\]\(([^)]+)\)',(root/'README.md').read_text(encoding='utf-8')):
        if '://' not in ref:assert (root/ref).exists(),'Broken reading-entry link: '+ref
    reports[tier].update({'release_entries_verified':entry_count,'release_entries_excluded':exclusions,'passed':True})
    (root/'PUBLICATION_AUDIT.json').write_text(json.dumps(reports[tier],indent=2)+'\n',encoding='utf-8')
print(json.dumps(reports,indent=2))
