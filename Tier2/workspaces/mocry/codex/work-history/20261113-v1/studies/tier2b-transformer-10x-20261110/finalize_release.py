"""Create an immutable local package and update only MMCS and its own handoff."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import os
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Transformer_10x_20261110.zip"


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    audit=json.loads((ROOT/"results/AUDIT.json").read_text());assert audit["all_passed"]
    assert not ARCHIVE.exists(),"Preserve previous releases; use a new release name."
    files=[]
    for directory,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if not d.startswith(".venv") and d!="__pycache__"]
        for name in names:
            if name!="MANIFEST.json" and not name.endswith(".pyc"):files.append(Path(directory)/name)
    files=sorted(files);manifest={p.relative_to(ROOT).as_posix():{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size} for p in files}
    assert sum(r["bytes"] for r in manifest.values())<100_000_000
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[ROOT/"MANIFEST.json"]:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)|{"MANIFEST.json"}
        assert all(sha(z.read(n))==r["sha256"] for n,r in manifest.items())
    result=json.loads((ROOT/"results/RESULTS.json").read_text());summary=pd.read_csv(ROOT/"results/SUMMARY.csv");changes=pd.read_csv(ROOT/"results/LARGE_VS_SMALL.csv")
    course=ROOT.parents[2];now=datetime.now(timezone.utc);sid="LOCAL-MMCS-TRANSFORMER-10X-20261110"
    test=changes.loc[changes.split.eq("test")]
    description="；".join(f"{r.target} test{r.mean_loss_change_pct:+.2f}%、{r.large_better_seeds}/3 seed改善、SD{r.small_seed_sd:.6f}→{r.large_seed_sd:.6f}" for r in test.itertuples())
    source={"source_id":sid,"recorded_at":now.isoformat(),"course":"MMCS","academic_year":"2026/27","evidence_status":"local_experiment_verified",
        "folder":str(ROOT.relative_to(course)),"archive":str(ARCHIVE.relative_to(course)),"archive_sha256":sha(ARCHIVE.read_bytes()),
        "new_fits":9,"seeds":[17,29,43],"parameters":54005,"prior_parameters":5407,"ratio":54005/5407,
        "protocol":result["protocol"],"summary":summary.to_dict("records"),"large_vs_small":changes.to_dict("records"),"audit":audit,
        "remote_published":False,"formal_submission":False,"MPC_evaluated":False,"school_or_mail_access":False}
    source_path=course/"materials/SOURCE-20261110-TRANSFORMER-10X.json"
    assert not source_path.exists();source_path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    p=course/"tasks.json";old=p.read_text(encoding="utf-8-sig");j=json.loads(old);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["forecast_transformer_10x"]={"status":"completed_local_exploratory_not_published","source_id":sid,"folder":str(ROOT.relative_to(course)),
        "parameters":54005,"prior_parameters":5407,"fits":9,"seeds":[17,29,43],"GPU_used":True,"data_features_splits_unchanged":True,
        "windows_lr_frozen":True,"every_step_full_three_set_eval":True,"audit_all_passed":True,"MPC_evaluated":False,"test_changes":test.to_dict("records")}
    task["next_action"]="完成Transformer扩宽5407→54005参数(9.988倍)，层数1/heads3/输入8维/划分/标化/优化与全step评估完全沿用；G/D=7天、price=182天、lr0.001冻结，三种子共9新GPU拟合。"+description+"。电价train/val均值降低25.82%/6.44%但test升0.99%，未见扩大容量的明确测试收益。保留小模型默认候选与RNN电价强对照，下一步模型/特征/控制由用户决定；未跑MPC、未上传或改正式v4.1，项目仍open。"
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-10 Transformer扩宽约10倍完成：`assignments/FinalProject/tier2b-transformer-10x-20261110/REPORT_ZH.md`，包 `MMCS_Tier2B_Transformer_10x_20261110.zip`。5407→54005参数，d24→72/FFN54→220，一层/3heads；原数据/8特征/划分/scaler/训练代码不变，仅改模型宽度和参数校验；冻结G/D7天、price182天/lr0.001，seeds17/29/43，9新GPU拟合，逐step完整三集评估。"+description+"。电价train/val均值降25.82%/6.44%，test未改善；9checkpoint/原始单位预测/逐step选点早停/旧release333文件和CPU-CUDA核验通过。训练6138updates，6147评估行。三种子范围重叠，test已监测非盲测；无新调参、外部特征、MPC或远程上传，正式报告未改。源 `"+sid+"`。\n\n"
    p=course/"STATUS.md";old=p.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    handoff=course.parent/"global/handoffs"/f"{now:%Y-%m-%d-%H%M}-MMCS-transformer-10x.md"
    handoff.write_text("# MMCS Transformer扩宽实验完成\n\n"+entry+"MMCS-008仍open，无新增截止或课表变更。本轮仅本地实验，未查学校平台/邮箱，也未访问网页，不代表课程全面同步。\n",encoding="utf-8")
    print(json.dumps({"archive":str(ARCHIVE),"bytes":ARCHIVE.stat().st_size,"files":len(files)+1,"sha256":sha(ARCHIVE.read_bytes()),"verified":True,"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
