"""Package frozen, reproducible inputs and checked outputs without local runtimes."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/'MMCS_Tier1_Multiproduct_20261110_v6.zip'

def pack():
    verification=json.loads((ROOT/'results/verification_summary.json').read_text(encoding='utf-8'))
    assert verification['study_cases']==14 and verification['all_optimal']
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
                 p.name!='PACKAGE_MANIFEST.json' and p.suffix not in ('.pyc','.log'))
    manifest={p.relative_to(ROOT).as_posix():dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in files}
    index=ROOT/'PACKAGE_MANIFEST.json'
    index.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with ZipFile(ARCHIVE,'w',compression=ZIP_DEFLATED,compresslevel=6) as f:
        for p in files+[index]:f.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as f:
        assert f.testzip() is None and len(f.namelist())==len(files)+1
        for name,item in manifest.items():assert hashlib.sha256(f.read(ROOT.name+'/'+name)).hexdigest()==item['sha256']
    print(len(files)+1,'files',ARCHIVE.stat().st_size,'bytes',hashlib.sha256(ARCHIVE.read_bytes()).hexdigest())

if __name__=='__main__':pack()
