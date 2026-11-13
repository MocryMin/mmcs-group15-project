"""Package verified outputs and register local course progress."""
from pathlib import Path
from datetime import datetime,timezone
import json
import shutil
import pandas as pd
import package_artifacts
from fit_core import sha

ROOT=Path(__file__).resolve().parent


def main():
    result=json.loads((ROOT/"results/RESULTS.json").read_text(encoding="utf-8"))
    audit=json.loads((ROOT/"results/AUDIT.json").read_text(encoding="utf-8"));assert audit["all_passed"]
    selected=pd.read_csv(ROOT/"results/SELECTED_SUMMARY.csv")
    previous=pd.read_csv(ROOT/"reference_previous/results/training_runs.csv")
    test_improved=sum(r.test_loss<previous.loc[previous.target.eq(r.target)&previous.family.eq(r.family)&previous.seed.eq(17)].iloc[0].test_loss_at_val_checkpoint for r in selected.itertuples())
    logs=ROOT/"execution_logs";logs.mkdir(exist_ok=True)
    for target in ("demand_MW","price_GBP_MWh"):
        for name in ("worker.log","COMPLETE.json"):
            shutil.copy2(ROOT/"parallel_jobs"/target/name,logs/(target+"_"+name))
    package_artifacts.main()
    archive=package_artifacts.ARCHIVE
    course=ROOT.parents[2];now=datetime.now(timezone.utc);sid="LOCAL-MMCS-LOOKBACK-GRID-SMOKE-20261109"
    source={"source_id":sid,"recorded_at":now.isoformat(),"course":"MMCS","academic_year":"2026/27",
        "evidence_status":"local_experiment_verified","folder":str(ROOT.relative_to(course)),"archive":str(archive.relative_to(course)),
        "archive_sha256":sha(archive),"lookbacks_days":result["protocol"]["lookbacks_days"],"seed":17,"cases":42,"fresh_completed_fits":39,"strictly_equivalent_reused_fits":3,
        "periods":result["protocol"]["periods"],"samples":result["protocol"]["samples"],"selected_by_validation":result["selected"],
        "checkpoint_and_early_stopping":"validation only","complete_three_split_eval":"every optimizer step","audit":audit,
        "test_improved_vs_previous_same_seed_cases":int(test_improved),"selected_windows_are_single_seed_candidates":True,
        "parallel_execution":"Independent target processes, two threads each; generation runner switched after its 14 completed cases; incomplete next-target attempt not used",
        "test_status":"monitored held-out, previously inspected; not blind","data_vintage_audited":False,"MPC_evaluated":False,"remote_published":False,"formal_submission":False}
    (course/"materials/SOURCE-20261109-LOOKBACK-GRID-SMOKE.json").write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    windows="；".join(f"{r.target}/{r.family}={r.lookback}天" for r in selected.itertuples())
    p=course/"tasks.json";old=p.read_text(encoding="utf-8-sig");j=json.loads(old)
    t=next(z for z in j["tasks"] if z["id"]=="MMCS-008")
    t["forecast_lookback_grid"]={"status":"completed_local_smoke_not_published","source_id":sid,"folder":str(ROOT.relative_to(course)),
        "cases":42,"seed":17,"lookbacks_days":result["protocol"]["lookbacks_days"],"selected_by_validation":result["selected"],
        "single_seed_not_stability_test":True,"every_step_full_three_set_eval":True,"audit_all_passed":True,"MPC_evaluated":False}
    t["next_action"]="完成输入历史7窗口×3目标×RNN/LSTM的42配置smoke，seed17，39新拟合+3等价复用；固定2022–24/2025Jan–Aug/2025Sep–2026Aug与学习率/架构，每step完整三集评估，仅val选checkpoint/窗口和早停。Val所选："+windows+f"。原同种子对照仅{test_improved}/6组test下降，未认定泛化改善。单种子结果已本地交付，后续稳健性复核、其他模型/特征或MPC按用户决定；项目仍open，正式v4.1未改，未上传。"
    assert p.read_text(encoding="utf-8-sig")==old
    p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-09 输入历史 grid smoke 完成，入口 `assignments/FinalProject/tier2b-lookback-grid-smoke-20261109/REPORT_ZH.md`，包 `MMCS_Tier2B_Lookback_Grid_Smoke_20261109.zip`。窗口365/182/91/56/30/14/7天，三目标独立RNN/LSTM，seed17共42配置（39次新拟合+3组56天严格等价复用）；训练目标1096/val243/test365保持一致，2021仅补历史，学习率/架构固定，每step完整三集eval且仅val选点/窗口/早停。Val所选："+windows+"。全部42个checkpoint、逐step日志、选择、边界/标化/复用审计通过。单种子smoke不代表稳定排名，test已反复监测非盲测；MPC/数据发布版本审计未做，未上传或改正式报告。源 `"+sid+"`。\n\n"
    p=course/"STATUS.md";old=p.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    assert p.read_text(encoding="utf-8-sig")==old
    p.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    handoff=course.parent/"global/handoffs"/f"{now:%Y-%m-%d-%H%M}-MMCS-lookback-grid-smoke.md"
    handoff.write_text("# MMCS 输入历史窗口 smoke 完成\n\n"+entry+"用户要求已完成；任务MMCS-008仍open，无新增正式截止或课表变更。未查学校平台/邮箱，未上传协作仓库、修改正式候选或提交。详见本课tasks/STATUS与报告。\n",encoding="utf-8")
    print(json.dumps({"source_id":sid,"archive":str(archive),"sha256":sha(archive),"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
