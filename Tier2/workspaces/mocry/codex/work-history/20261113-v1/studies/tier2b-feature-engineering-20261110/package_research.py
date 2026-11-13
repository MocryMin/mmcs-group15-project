from pathlib import Path
import json,zipfile,hashlib
from features import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((ROOT/'STOP_REASON.json').read_text())['criteria_met']
for p in [ROOT/'results/AUDIT_NEURAL.json',ROOT/'results/AUDIT_CLASSICAL.json',ROOT/'strict-confirmation/results/AUDIT_NEURAL.json']:assert json.loads(p.read_text())['passed']
archive=ROOT.parent/'MMCS_Tier2B_Feature_Engineering_20261110_v1.2.zip'
if archive.exists():raise FileExistsError('Version rather than overwrite the frozen archive')
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(n in {'__pycache__','.deps','.venv','tmp'} for n in p.relative_to(ROOT).parts) and p.name not in {'MANIFEST.json','PACKAGE.json'}]
manifest={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}
(ROOT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[ROOT/'MANIFEST.json']:z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,m in manifest.items():assert hashlib.sha256(z.read(ROOT.name+'/'+name)).hexdigest()==m['sha256']
record={'path':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'manifest_files':len(manifest),'verified':True,'published':False,'version':'v1.2 portable reference bundle; v1.1 strict-confirmation predictions unchanged'}
(ROOT/'PACKAGE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
