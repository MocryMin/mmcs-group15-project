"""Package the audited local study and preserve MMCS state and its handoff."""
from pathlib import Path
from datetime import datetime,timezone
import json
import hashlib
import os
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110.zip"


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    audit=json.loads((ROOT/"results/AUDIT.json").read_text());assert audit["all_passed"] and not ARCHIVE.exists()
    files=[]
    for directory,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if not d.startswith(".venv") and d!="__pycache__"]
        for name in names:
            if name!="MANIFEST.json" and not name.endswith(".pyc"):files.append(Path(directory)/name)
    files=sorted(files);manifest={p.relative_to(ROOT).as_posix():{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size} for p in files}
    assert sum(v["bytes"] for v in manifest.values())<100_000_000
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[ROOT/"MANIFEST.json"]:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)|{"MANIFEST.json"}
        assert all(sha(z.read(n))==v["sha256"] for n,v in manifest.items())
    course=ROOT.parents[2];now=datetime.now(timezone.utc);sid="LOCAL-MMCS-JOINT-RNN-LSTM-10X-20261110"
    result=json.loads((ROOT/"results/RESULTS.json").read_text());summary=pd.read_csv(ROOT/"results/SUMMARY.csv");changes=pd.read_csv(ROOT/"results/LARGE_VS_SMALL.csv")
    joint=changes.loc[changes.target.eq("JOINT")&changes.split.eq("test")]
    description="；".join(f"{r.family}综合test{r.mean_loss_change_pct:+.2f}%、{r.large_better_seeds}/3 seed改善、SD{r.small_seed_sd:.6f}→{r.large_seed_sd:.6f}" for r in joint.itertuples())
    source={"source_id":sid,"recorded_at":now.isoformat(),"course":"MMCS","academic_year":"2026/27","evidence_status":"local_experiment_verified","folder":str(ROOT.relative_to(course)),
        "archive":str(ARCHIVE.relative_to(course)),"archive_sha256":sha(ARCHIVE.read_bytes()),"protocol":result["protocol"],"summary":summary.astype(object).where(pd.notna(summary),None).to_dict("records"),"changes":changes.to_dict("records"),"audit":audit,
        "remote_published":False,"formal_submission":False,"MPC_evaluated":False,"school_or_email_access":False}
    sourcepath=course/"materials/SOURCE-20261110-JOINT-RNN-LSTM-10X.json";assert not sourcepath.exists()
    sourcepath.write_text(json.dumps(source,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    path=course/"tasks.json";old=path.read_text(encoding="utf-8-sig");j=json.loads(old);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["forecast_joint_rnn_lstm_10x"]={"status":"completed_local_exploratory_not_published","source_id":sid,"folder":str(ROOT.relative_to(course)),"new_fits":12,"seeds":[17,29,43],
        "joint_nextday_outputs":3,"RNN":{"lookback":28,"lr":.003,"small_parameters":5511,"large_parameters":54951},"LSTM":{"lookback":56,"lr":.003,"small_parameters":5475,"large_parameters":54995},
        "data_features_splits_unchanged":True,"fresh_current_split_small_controls":True,"every_step_full_three_sets_and_components":True,"GPU_used":True,"audit_all_passed":True,"MPC_evaluated":False}
    task["next_action"]="完成联合次日RNN/LSTM约10倍扩宽，沿用旧联合val选窗RNN28/LSTM56、lr0.003；同当前train2022–24/val2025Jan–Aug/test2025Sep–2026Aug及8维输入，单模型同时输出三目标，综合val选一个checkpoint。补跑当前划分小模型对照，共12GPU拟合，seeds17/29/43，逐step全量三集综合与分项。"+description+"。RNN电价test差4.31%(3/3 seed变差)，LSTM电价改善2.40%(3/3 seed改善)；综合收益不大，LSTM种子波动增加。下一步模型/特征/控制由用户决定，未跑MPC、未上传或改正式v4.1，项目仍open。"
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-10 联合次日RNN/LSTM约10倍参数实验完成：`assignments/FinalProject/tier2b-joint-rnn-lstm-10x-20261110/REPORT_ZH.md`，包 `MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110.zip`。沿用旧联合val所选RNN28天/LSTM56天及lr0.003，输入L×8、同时输出次日3值，共享编码器，RNN5511→54951、LSTM5475→54995；原独立smoke六个按目标窗口不直接套用。当前冻结数据/三集/scaler同Transformer，旧联合划分不同，因此新训小模型对照，4配置×3seeds共12GPU fits。综合标准化MSE等权三目标，单一综合val选点/早停；每step完整三集综合和分项。"+description+"。RNN电价test差4.31%(3/3变差)，LSTM电价好2.40%(3/3改善)，综合收益仍小且LSTMtest波动增加。10548updates/10560评估行，12checkpoint与独立指标/覆盖/选点/停止/CPU-CUDA审计通过。固定窗口lr未重调，test已监测非盲测；无外部特征/MPC/远程上传，正式报告未改。源 `"+sid+"`。\n\n"
    path=course/"STATUS.md";old=path.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    handoff=course.parent/"global/handoffs"/f"{now:%Y-%m-%d-%H%M}-MMCS-joint-rnn-lstm-10x.md"
    handoff.write_text("# MMCS 联合次日RNN/LSTM扩宽实验完成\n\n"+entry+"MMCS-008仍open，无新增截止或课表变更。本轮仅本地实验，未查学校/邮件或网页，不代表课程同步。\n",encoding="utf-8")
    print(json.dumps({"archive":str(ARCHIVE),"files":len(files)+1,"bytes":ARCHIVE.stat().st_size,"sha256":sha(ARCHIVE.read_bytes()),"verified":True,"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
