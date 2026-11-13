"""Archive the local research and verify every archived byte."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT.parent/'MMCS_Equipment_Research_20261110_v3_1.zip'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run():
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in p.parts)
    manifest=dict(as_of='2026-11-10',files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in paths])
    (ROOT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths.append(ROOT/'MANIFEST.json')
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        assert len(z.infolist())==len(paths)
        for rec in manifest['files']:
            data=z.read(ROOT.name+'/'+rec['path'])
            assert len(data)==rec['bytes'] and hashlib.sha256(data).hexdigest()==rec['sha256']
    print(json.dumps(dict(archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,
        sha256=digest(ARCHIVE),files=len(paths),CRC='pass',all_member_hashes='pass'),ensure_ascii=False))

if __name__=='__main__':run()
