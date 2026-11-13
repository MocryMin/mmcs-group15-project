from pathlib import Path
import json,shutil,hashlib
from features import ROOT

meta=json.loads((ROOT/'BASELINE_REFERENCES.json').read_text());folder=ROOT/'inputs/reference_predictions';folder.mkdir(exist_ok=True)
for r in meta:
    source=Path(r['source']);dest=folder/source.name;shutil.copy2(source,dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==r['sha256']
    r['bundled_path']=dest.relative_to(ROOT).as_posix()
(ROOT/'BASELINE_REFERENCES.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=json.loads((ROOT/'results/AUDIT_CLASSICAL.json').read_text());audit['portable_original_reference_files_verified']=len(meta)
(ROOT/'results/AUDIT_CLASSICAL.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Bundled and hash-verified',len(meta),'exact original reference prediction files; numerical results unchanged.')
