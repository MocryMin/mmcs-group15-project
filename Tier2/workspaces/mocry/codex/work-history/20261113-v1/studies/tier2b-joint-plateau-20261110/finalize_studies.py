"""Package audited studies and record the read-only upstream research review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import os
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parent
COURSE=ROOT.parents[2]
REG=ROOT.parent/"tier2b-traditional-regression-20261110"
REVIEW=ROOT.parent/"fable-forecast-review-20261110"


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def records(frame):return frame.astype(object).where(pd.notna(frame),None).to_dict("records")


def package(folder,name):
    archive=folder.parent/name;assert not archive.exists()
    files=[]
    for directory,dirs,names in os.walk(folder):
        dirs[:]=[d for d in dirs if not d.startswith(".venv") and d!="__pycache__"]
        files.extend(Path(directory)/n for n in names if n!="MANIFEST.json" and not n.endswith(".pyc"))
    files=sorted(files);manifest={p.relative_to(folder).as_posix():{"sha256":sha(p),"bytes":p.stat().st_size} for p in files}
    assert sum(v["bytes"] for v in manifest.values())<150_000_000
    (folder/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[folder/"MANIFEST.json"]:z.write(p,p.relative_to(folder).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)|{"MANIFEST.json"}
        assert all(hashlib.sha256(z.read(n)).hexdigest()==v["sha256"] for n,v in manifest.items())
    return {"path":str(archive.relative_to(COURSE)),"sha256":sha(archive),"bytes":archive.stat().st_size,"files":len(files)+1,"verified":True}


def main():
    audit=json.loads((ROOT/"results/AUDIT.json").read_text());raudit=json.loads((REG/"results/INDEPENDENT_AUDIT.json").read_text())
    assert audit["all_passed"] and raudit["all_passed"]
    upstream=json.loads((REVIEW/"UPSTREAM.json").read_text())
    for f in upstream["files"]:
        b=(REVIEW/"upstream"/f["path"]).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()==f["git_blob_sha"]
    ppack=package(ROOT,"MMCS_Tier2B_Joint_Plateau_20261110.zip")
    rpack=package(REG,"MMCS_Tier2B_Traditional_Regression_20261110.zip")
    now=datetime.now(timezone.utc).isoformat();sid="LOCAL-MMCS-JOINT-PLATEAU-20261110";rsid="LOCAL-MMCS-TRADITIONAL-REGRESSION-20261110";fsid="GITHUB-MMCS-FABLE-FORECAST-REVIEW-20261110"
    result=json.loads((ROOT/"results/RESULTS.json").read_text());summary=pd.read_csv(ROOT/"results/SUMMARY.csv");changes=pd.read_csv(ROOT/"results/VERSUS_MATCHED_FIXED.csv");selection=json.loads((ROOT/"results/SELECTION_BY_VALIDATION.json").read_text())
    rmetrics=pd.read_csv(REG/"results/SELECTED_METRICS.csv");rchoice=json.loads((REG/"results/SELECTION.json").read_text())
    sources=[
        ("SOURCE-20261110-JOINT-PLATEAU.json",{"source_id":sid,"recorded_at":now,"evidence_status":"local_experiment_verified","folder":str(ROOT.relative_to(COURSE)),"archive":ppack,"protocol":result["protocol"],"summary":records(summary),"changes":records(changes),"selection":selection,"audit":audit,"remote_published":False,"MPC_evaluated":False}),
        ("SOURCE-20261110-TRADITIONAL-REGRESSION.json",{"source_id":rsid,"recorded_at":now,"evidence_status":"local_experiment_verified","folder":str(REG.relative_to(COURSE)),"archive":rpack,"protocol":json.loads((REG/"PROTOCOL.json").read_text()),"selection":rchoice,"metrics":records(rmetrics),"audit":raudit,"remote_published":False,"MPC_evaluated":False}),
        ("SOURCE-20261110-FABLE-FORECAST-REVIEW.json",{"source_id":fsid,"recorded_at":now,"evidence_status":"remote_material_read_and_code_reviewed","folder":str(REVIEW.relative_to(COURSE)),"upstream":upstream,"nine_git_blobs_verified":True,"independent_upstream_experiment_reproduction":False,
            "findings":["Traditional models accepted as candidates, not a reason to exclude neural families","Current nominal price/current split differs from upstream real2020 price/test2024-25/refit/features","Multi-step target-date refit blocks can train on labels after forecast origin; first k-1 predictions per block need corrected cutoffs","Decision diagnostic should align oracle and rolling terminal value before claiming a strict bound","No unsupported contract penalties adopted"],"remote_changed":False})]
    for filename,source in sources:
        p=COURSE/"materials"/filename;assert not p.exists();p.write_text(json.dumps(source,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    path=COURSE/"tasks.json";old=path.read_text(encoding="utf-8-sig");j=json.loads(old);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["forecast_joint_plateau"]={"status":"completed_local_exploratory_not_published","source_id":sid,"folder":str(ROOT.relative_to(COURSE)),"fits":24,"seeds":[17,29,43],"matched_patience":30,"policies":["fixed","lr_only","reg_only","combined"],"selected_by_validation":selection,"audit_all_passed":True,"archive":ppack}
    task["traditional_regression_pilot"]={"status":"completed_local_exploratory_not_published","source_id":rsid,"folder":str(REG.relative_to(COURSE)),"candidate_models":61,"deterministic":True,"same_current_split":True,"only_train_fit":True,"audit_all_passed":True,"best_joint_val_model":"CalendarResidualAR","best_joint_val_loss":0.113343,"corresponding_joint_test_loss":0.120560,"archive":rpack}
    task["fable_forecast_review"]={"source_id":fsid,"commit":upstream["commit"],"files_read_and_blob_verified":9,"review":str((REVIEW/"REVIEW_ZH.md").relative_to(COURSE)),"multistep_origin_cutoff_fix_needed":True,"upstream_modified":False}
    task["next_action"]="完成大联合RNN/LSTM平台期四策略消融24fits，统一早停30且val选择仍为fixed；降LR使RNN后期更稳，test小幅改善不能用于反选，LSTM降LR/联合策略均选调度前stage0。另完成同划分61个确定性传统回归候选，日历OLS+残差AR综合val/test=0.113343/0.120560，为具体强对照。已读Fable固定commit1620bdc3的9文件；多步按目标日分块重训存在起点后的标签边界问题，需改为按origin限制训练标签再复核，不直接套不同年份/real2020价/特征的排名。下一步统一固定/滚动和多步评价，保留线性/结构/神经候选；未MPC、未新合同或外部特征、未上传或改正式v4.1，项目仍open。"
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-10 平台期策略与传统方法对照完成。`assignments/FinalProject/tier2b-joint-plateau-20261110/REPORT_ZH.md`：RNN54951/LSTM54995、窗口28/56不变，固定/仅LR/仅正则/联合4策略×3seed，共24GPU拟合，平台5完整epoch分档，早停统一30、max120；27360updates、27384完整三集综合/分项评估行。全部调度/参数/选点/停止及24checkpoint核验通过，共同前缀与旧固定策略/调度前轨迹逐值一致。val仍选fixed两家族；LR-only RNN test相对匹配fixed好1.46%、combo好1.17%，LSTM LR-only/combo好1.48%却全选stage0，不能称调度后权重收益。包 `MMCS_Tier2B_Joint_Plateau_20261110.zip`，源 `"+sid+"`。\n\n"
    entry+="同日补做 `assignments/FinalProject/tier2b-traditional-regression-20261110/REPORT_ZH.md`：61个确定性OLS/Ridge/日历+残差AR与朴素候选，同原数据/目标日期/scaler、train-only系数/val选型；日历残差AR综合val/test=0.113343/0.120560，岭水平val0.114238/test0.126073、岭残差0.118118/0.123388。全部系数重放/正规方程/预测指标核验通过；OLS对float32近共线日历列使用精度感知截断并校验投影正规方程，记录OLS_PRECISION_NOTE。无神经式种子波动或滚动重估。包 `MMCS_Tier2B_Traditional_Regression_20261110.zip`，源 `"+rsid+"`。\n\n"
    entry+="已只读取得Fable提交1620bdc3的9文件并校验Git blob，审阅 `assignments/FinalProject/fable-forecast-review-20261110/REVIEW_ZH.md`。吸收传统回归、强朴素基准、决策价值评价；其多步按target-date重训在首k-1个origin可能含未来标签，需修正，oracle与滚动终值亦需统一；其real2020电价/2024–25测试/额外特征/滚动更新不能与当前排名直比。未复现其整套试验或逐篇核文献、未改/推送共享仓库。所有本轮工作未做MPC或更改正式报告；源 `"+fsid+"`。\n\n"
    path=COURSE/"STATUS.md";old=path.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M");handoff=COURSE.parent/"global/handoffs"/(stamp+"-MMCS-plateau-and-traditional.md")
    handoff.write_text("# MMCS 平台期与传统预测对照完成\n\n"+entry+"MMCS-008仍open，无新增DDL或课表变更。本轮除只读GitHub固定提交外未查学校/邮箱，不代表全面课程同步；远程材料通过GitHub连接器API取得，未读取网页HTML、未发送消息。\n",encoding="utf-8")
    print(json.dumps({"plateau":ppack,"traditional":rpack,"review":str(REVIEW/"REVIEW_ZH.md"),"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
