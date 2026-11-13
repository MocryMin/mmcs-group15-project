"""Package audited numerical outputs, source evidence and executable source."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
names={'full_A_candidate','full_B_candidate','certificate_A','certificate_B','proxy_A_candidate','proxy_B_candidate',
       'wind_proxy_A','wind_proxy_B','test_halfhour_power_and_intraday','test_B_power_limited_priority','test_H2_daily_cap'}
files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.py','.md','.txt','.json') and p.name!='PACKAGE_MANIFEST.json']
files += [p for d in ('inputs','source_data') for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
for p in (ROOT/'results').iterdir():
    if not p.is_file():continue
    if p.stem in ('comparison','annual_results','global_certificates','annual_comparison') or any(p.name==n+'.json' or p.name.startswith(n+'_') or p.name==n+'.log' for n in names):
        files.append(p)
files=sorted(set(files));manifest={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
(ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=ROOT.parent/'MMCS_Tier1_HalfHour_20261113_v7.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[ROOT/'PACKAGE_MANIFEST.json']:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,item in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==item['sha256']
print(archive,archive.stat().st_size,'bytes;',len(manifest),'verified files')
