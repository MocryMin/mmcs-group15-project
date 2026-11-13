"""Archive verified outputs, excluding the multi-gigabyte local GPU environment."""
from pathlib import Path
import hashlib
import json
import zipfile
import os

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Transformer_Grid_20261109.zip"


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    assert json.loads((ROOT/"results/AUDIT.json").read_text())["all_passed"]
    assert not ARCHIVE.exists(),"Use a new release filename to preserve an existing archive."
    files=[]
    for directory,dirs,names in os.walk(ROOT):
        dirs[:]=[v for v in dirs if not v.startswith(".venv") and v not in ("__pycache__","baseline_jobs")]
        for name in names:
            p=Path(directory)/name
            if p.parent.name=="research" and name in ("torch_gpu_pages.json","browser.log"):continue
            if p.suffix!=".pyc" and p.name!="MANIFEST.json":files.append(p)
    files=sorted(files)
    manifest={p.relative_to(ROOT).as_posix():{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size} for p in files}
    assert not any(".venv" in name for name in manifest)
    assert sum(m["bytes"] for m in manifest.values())<150_000_000
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8");files.append(ROOT/"MANIFEST.json")
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:archive.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None and set(archive.namelist())==set(manifest)|{"MANIFEST.json"}
        for name,record in manifest.items():assert sha(archive.read(name))==record["sha256"]
    print(json.dumps({"archive":str(ARCHIVE),"files":len(files),"bytes":ARCHIVE.stat().st_size,"sha256":sha(ARCHIVE.read_bytes()),"verification_passed":True},ensure_ascii=False))


if __name__=="__main__":main()
