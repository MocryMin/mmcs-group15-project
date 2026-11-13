from pathlib import Path
import hashlib
import importlib.util
import json
import re

PROJECT=Path(__file__).resolve().parent.parent
REPO=PROJECT/"group-collaboration"
REL="Tier1/workspaces/mocry/codex/baseline-1104/20261104-v1"
ROOT=REPO/REL

def sha(data): return hashlib.sha256(data).hexdigest()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def files(root): return [p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc" and "reproduced" not in p.parts]

receipt=json.loads((PROJECT/"baseline-1104-publication/reproduction-check-v2/REPRODUCTION_CHECK.json").read_text())
assert receipt["all_checks_passed"] and receipt["cases"]==82
write(ROOT/"provenance/REPRODUCTION_CHECK.json",receipt)
readme=ROOT/"README.md"
body=readme.read_text(encoding="utf-8")
body+="\n打包版已在新的空目录重新求解并验证全部 82 个案例，安装数量全部一致，年度收益差值为零。见 [打包复算核对](provenance/REPRODUCTION_CHECK.json)。\n"
readme.write_text(body,encoding="utf-8",newline="\n")
copied=json.loads((ROOT/"provenance/COPY_RECORD.json").read_text(encoding="utf-8"))
for record in copied:
    original_copy=record["package_sha256"]
    current=sha((ROOT/record["packaged"]).read_bytes())
    record["copied_sha256"]=original_copy
    record["package_sha256"]=current
    record["portability_edit"]=current!=original_copy
write(ROOT/"provenance/COPY_RECORD.json",copied)
calc=ROOT/"calculation"
write(calc/"DELIVERY_MANIFEST.json",{p.relative_to(calc).as_posix():sha(p.read_bytes()) for p in files(calc) if p.name!="DELIVERY_MANIFEST.json"})
manifest={p.relative_to(ROOT).as_posix():dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in files(ROOT) if p.name!="PACKAGE_MANIFEST.json"}
write(ROOT/"PACKAGE_MANIFEST.json",manifest)
for name,meta in manifest.items(): assert sha((ROOT/name).read_bytes())==meta["sha256"]
for name in ["README.md","calculation/README.md","calculation/MODEL.md"]:
    p=ROOT/name
    for link in re.findall(r"\]\(([^)]+)\)",p.read_text(encoding="utf-8")):
        if not link.startswith(("http:","https:")):
            assert (p.parent/link).exists(),(name,link)
print("Package file count:",len(manifest)+1)
print("Archived numerical reproduction:",receipt)
spec=importlib.util.spec_from_file_location("collab",REPO/"tools/collab.py")
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
assert not c.git_text("diff","--name-only",cwd=REPO),"Unexpected tracked worktree edits before staging"
c.git("add","--",REL,cwd=REPO)
staged=c.tree(c.git_text("write-tree",cwd=REPO),REPO)
for name,meta in manifest.items():
    data=staged[REL+"/"+name]
    assert sha(data)==meta["sha256"],"Git conversion changed "+name
paths=c.git("diff","--cached","--name-only","-z",cwd=REPO).stdout.split(b"\0")
assert all(not p or p.decode().startswith(REL+"/") for p in paths)
c.commit(type("Args",(),dict(tier="Tier1",message="Archive Baseline1104 complete calculation in Ran Min workspace"))(),REPO)
commit=c.git_text("rev-parse","HEAD",cwd=REPO)
write(PROJECT/"baseline-1104-publication/WORKSPACE_COMMIT.json",dict(commit=commit,path=REL,files=len(manifest)+1,reproduction=receipt))
print("Workspace commit:",commit)
