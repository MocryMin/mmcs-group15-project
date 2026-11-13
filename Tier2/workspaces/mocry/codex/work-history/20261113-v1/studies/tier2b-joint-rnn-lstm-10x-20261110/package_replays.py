"""Add requested loss replays as v1.1; retain the original v1 package unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import os
import zipfile

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110_v1.1.zip"


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert json.loads((ROOT/"results/AUDIT.json").read_text())["all_passed"] and not ARCHIVE.exists()
    old=ROOT.parent/"MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110.zip"
    assert sha(old)=="16361a271ee5c7eb5fb72e48b18197ae20ed92a5d7ad01fb6a7b15ba245181f6"
    files=[]
    for directory,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if not d.startswith(".venv") and d!="__pycache__"]
        files.extend(Path(directory)/n for n in names if n!="MANIFEST.json" and not n.endswith(".pyc"))
    files=sorted(files);manifest={p.relative_to(ROOT).as_posix():{"sha256":sha(p),"bytes":p.stat().st_size} for p in files}
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[ROOT/"MANIFEST.json"]:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)|{"MANIFEST.json"}
        for n,v in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==v["sha256"]
    course=ROOT.parents[2];sid="LOCAL-MMCS-JOINT-LOSS-REPLAYS-20261110"
    plots=["figures/joint_step_losses.png","figures/large_all_seed_joint_steps.png","figures/large_component_step_losses.png"]
    record={"source_id":sid,"recorded_at":datetime.now(timezone.utc).isoformat(),"parent_source":"LOCAL-MMCS-JOINT-RNN-LSTM-10X-20261110","version":"1.1",
        "archive":str(ARCHIVE.relative_to(course)),"archive_sha256":sha(ARCHIVE),"plots":{p:sha(ROOT/p) for p in plots},
        "from_unchanged_full_step_logs":True,"smoothing":False,"checkpoint_selection":"joint validation only; median-joint-val seed for representative plots; all three seeds also shown",
        "new_training":False,"remote_published":False}
    p=course/"materials/SOURCE-20261110-JOINT-LOSS-REPLAYS.json";assert not p.exists();p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    p=course/"tasks.json";oldtext=p.read_text(encoding="utf-8-sig");j=json.loads(oldtext);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["forecast_joint_rnn_lstm_10x"]["replays"]={"source_id":sid,"version":"1.1","archive":str(ARCHIVE.relative_to(course)),"plots":plots,"new_training":False}
    assert p.read_text(encoding="utf-8-sig")==oldtext;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    p=course/"STATUS.md";oldtext=p.read_text(encoding="utf-8-sig");entry="2026-11-10 应用户要求补充联合模型loss回放：大小模型4配置、两个大模型全部3seed、三个输出分项三组图，逐step完整三集原值，无平滑，综合val选点；新包v1.1 `MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110_v1.1.zip`，原v1保留，未重训或上传。入口仍为该实验REPORT_ZH.md，源 `"+sid+"`。\n\n"
    assert p.read_text(encoding="utf-8-sig")==oldtext;p.write_text(oldtext.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    print(json.dumps({"archive":str(ARCHIVE),"bytes":ARCHIVE.stat().st_size,"sha256":sha(ARCHIVE),"verified":True},ensure_ascii=False))


if __name__=="__main__":main()
