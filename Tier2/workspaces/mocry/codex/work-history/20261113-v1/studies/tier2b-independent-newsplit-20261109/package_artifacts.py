"""Archive a completed experiment and verify every archived file."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Monitored_Train_Val_Test_20261109.zip"


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    assert json.loads((ROOT/"results/AUDIT.json").read_text())["all_passed"]
    assert not ARCHIVE.exists(),"Use a new release name to preserve an existing archive."
    files=sorted(p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".venv" not in p.parts and p.suffix!=".pyc" and p.name!="MANIFEST.json")
    manifest={p.relative_to(ROOT).as_posix():{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size} for p in files}
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    files.append(ROOT/"MANIFEST.json")
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(manifest)|{"MANIFEST.json"}
        assert json.loads(z.read("MANIFEST.json"))==manifest
        for name,item in manifest.items():assert sha(z.read(name))==item["sha256"]
    print(json.dumps({"archive":str(ARCHIVE),"files":len(files),"bytes":ARCHIVE.stat().st_size,"sha256":sha(ARCHIVE.read_bytes()),"archive_verification_passed":True},ensure_ascii=False))


if __name__=="__main__":main()
