"""Archive the verified attention experiment and record course progress."""
from pathlib import Path
from datetime import datetime,timezone
import json
import pandas as pd
import package_artifacts
from fit_core import sha

ROOT=Path(__file__).resolve().parent


def main():
    result=json.loads((ROOT/"results/RESULTS.json").read_text())
    audit=json.loads((ROOT/"results/AUDIT.json").read_text());assert audit["all_passed"]
    selected=pd.read_csv(ROOT/"results/SELECTED_COMPARISON.csv")
    matched=pd.read_csv(ROOT/"results/MATCHED_WINDOW_COMPARISON.csv")
    package_artifacts.main();archive=package_artifacts.ARCHIVE
    course=ROOT.parents[2];now=datetime.now(timezone.utc);sid="LOCAL-MMCS-TEMPORAL-ATTENTION-GRID-20261109"
    windows="；".join(f"{r.target}/{r.family}={r.lookback}天" for r in selected.itertuples())
    valwins=int(selected.validation_change_pct.lt(0).sum());testwins=int(selected.test_change_pct.lt(0).sum())
    fixed_valwins=int(matched.loc[matched.split.eq("validation"),"loss_change_pct"].lt(0).sum())
    fixed_testwins=int(matched.loc[matched.split.eq("test"),"loss_change_pct"].lt(0).sum())
    source={"source_id":sid,"recorded_at":now.isoformat(),"course":"MMCS","academic_year":"2026/27","evidence_status":"local_experiment_verified",
        "folder":str(ROOT.relative_to(course)),"archive":str(archive.relative_to(course)),"archive_sha256":sha(archive),
        "architecture":result["protocol"]["architecture"],"parameters":{"RNN_attention":5441,"LSTM_attention":5441},"device":"CPU two threads per target process",
        "seed":17,"fresh_fits":42,"lookbacks_days":result["protocol"]["lookbacks_days"],"periods":result["protocol"]["periods"],"samples":result["protocol"]["samples"],
        "selected_by_validation":result["selected"],"same_window_val_improved_cases":fixed_valwins,"same_window_test_improved_cases":fixed_testwins,
        "independently_selected_val_improved_groups":valwins,"independently_selected_test_improved_groups":testwins,
        "every_step_full_three_set_eval":True,"validation_only_checkpoint_and_window_selection":True,"audit":audit,
        "single_seed_smoke":True,"test_is_monitored_not_blind":True,"data_vintage_audited":False,"MPC_evaluated":False,"remote_published":False,"formal_submission":False}
    (course/"materials/SOURCE-20261109-TEMPORAL-ATTENTION-GRID.json").write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    p=course/"tasks.json";old=p.read_text(encoding="utf-8-sig");j=json.loads(old);t=next(z for z in j["tasks"] if z["id"]=="MMCS-008")
    t["forecast_temporal_attention_grid"]={"status":"completed_local_single_seed_not_published","source_id":sid,"folder":str(ROOT.relative_to(course)),
        "fits":42,"seed":17,"lookbacks_days":result["protocol"]["lookbacks_days"],"selected_by_validation":result["selected"],
        "fixed_window_val_wins":fixed_valwins,"fixed_window_test_wins":fixed_testwins,"selected_groups_test_wins":testwins,
        "parameters_each":5441,"device":"CPU","every_step_full_three_set_eval":True,"audit_all_passed":True,"MPC_evaluated":False}
    t["next_action"]="完成独立RNN/LSTM+时间注意力七窗口seed17的42次拟合；原循环层不变、last-query缩放点积attention加context通道，每模型5441参数，逐step全量三集eval，仅val选checkpoint/窗口。候选："+windows+f"。同窗val/test改善{fixed_valwins}/42、{fixed_testwins}/42；双方各自选窗后test改善{testwins}/6。已导出权重分布及固定权重uniform/last读取诊断，重放审计通过；单种子探索结果，后续模型/特征/稳健性或MPC按用户决定，项目仍open，未上传或改正式v4.1。"
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-09 时间注意力七窗口对照完成，入口 `assignments/FinalProject/tier2b-temporal-attention-grid-20261109/REPORT_ZH.md`，完整包 `MMCS_Tier2B_Temporal_Attention_Grid_20261109.zip`。保留RNN68/LSTM32循环层，最后hidden query对全部历史hidden做scaled-dot-product聚合，与最后状态拼接输出；无独立QKV投影，每模型5441参数。固定seed17、365/182/91/56/30/14/7天×三目标×两家族，42新拟合；CPU三目标独立进程各两线程，逐step全量train/val/test评估，仅val选点/窗，原日期与scaler不变。Val候选："+windows+f"。同窗val/test改善{fixed_valwins}/42、{fixed_testwins}/42；各自选窗后test改善{testwins}/6。注意力NumPy独立计算、初始循环层/梯度/权重归一化、42checkpoint预测/分布/指标重放及训练/选点日志审计通过。单种子、test为已监测留出集；MPC/数据发布时点审计未做，未上传、未改正式报告。源 `"+sid+"`。\n\n"
    p=course/"STATUS.md";old=p.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    handoff=course.parent/"global/handoffs"/f"{now:%Y-%m-%d-%H%M}-MMCS-temporal-attention-grid.md"
    handoff.write_text("# MMCS 时间注意力对照完成\n\n"+entry+"MMCS-008保持open，无新增正式截止或课表变更。本轮没有学校平台/邮箱同步、正式报告更改、组仓库上传或提交。\n",encoding="utf-8")
    print(json.dumps({"source_id":sid,"archive":str(archive),"sha256":sha(archive),"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
