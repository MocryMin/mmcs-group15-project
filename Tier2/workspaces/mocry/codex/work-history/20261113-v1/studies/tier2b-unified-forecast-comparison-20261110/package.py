"""Freeze the comparison without bundling installed libraries or old archives."""
from pathlib import Path
import hashlib
import json
import zipfile
from common import ROOT,dump,sha

archive=ROOT.parent/'MMCS_Tier2B_Unified_Forecast_Comparison_20261110.zip'
if archive.exists():raise FileExistsError('Keep the existing archive; use a versioned new name for a revision.')
paths=[p for p in ROOT.rglob('*') if p.is_file() and not any(v in {'.deps','__pycache__','.venv','cache'} for v in p.relative_to(ROOT).parts) and p.name not in {'MANIFEST.json','PACKAGE.json'}]
manifest={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}
dump(ROOT/'MANIFEST.json',manifest)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in paths+[ROOT/'MANIFEST.json']:z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    saved=json.loads(z.read(ROOT.name+'/MANIFEST.json'))
    for name,info in saved.items():assert hashlib.sha256(z.read(ROOT.name+'/'+name)).hexdigest()==info['sha256']
record={'path':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'manifest_files':len(manifest),'verified':True,'published':False,'scope':'Prediction comparison, fresh classical estimators and data; previous neural training archives remain separate.'}
dump(ROOT/'PACKAGE.json',record);print(json.dumps(record))
