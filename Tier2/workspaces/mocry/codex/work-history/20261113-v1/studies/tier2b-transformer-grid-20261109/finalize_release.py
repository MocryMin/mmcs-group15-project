"""Package verified Transformer experiments and retain a dated course handoff."""
from pathlib import Path
from datetime import datetime,timezone
import json
import pandas as pd
import package_artifacts
from fit_core import sha

ROOT=Path(__file__).resolve().parent


def main():
    result=json.loads((ROOT/"results/RESULTS.json").read_text());audit=json.loads((ROOT/"results/AUDIT.json").read_text());assert audit["all_passed"]
    summary=pd.read_csv(ROOT/"results/THREE_SEED_SUMMARY.csv");comparison=pd.read_csv(ROOT/"results/TRANSFORMER_VS_RECURRENT.csv")
    package_artifacts.main();archive=package_artifacts.ARCHIVE
    course=ROOT.parents[2];now=datetime.now(timezone.utc);sid="LOCAL-MMCS-TRANSFORMER-THREESEED-20261110"
    windows="；".join(f"{t}={c['lookback']}天/lr{c['lr']:g}" for t,c in result["selection"].items())
    changes="；".join(f"{r.target}相对{r.baseline_family}均值test{r.mean_loss_ratio_change_pct:+.2f}%({r.seeds_transformer_better}/3种子更好)" for r in comparison.itertuples() if r.baseline_chosen_by_mean_val)
    source={"source_id":sid,"recorded_at":now.isoformat(),"course":"MMCS","academic_year":"2026/27","evidence_status":"local_experiment_verified",
        "folder":str(ROOT.relative_to(course)),"archive":str(archive.relative_to(course)),"archive_sha256":sha(archive),"unique_fits":66,
        "screen_fits":42,"confirmation_models":27,"seeds":[17,29,43],"transformer_parameters":5407,"recurrent_parameters":{"RNN":5373,"LSTM":5409},
        "periods":result["protocol"]["periods"],"samples":result["protocol"]["samples"],"selected_transformer_configs":result["selection"],
        "software":result["protocol"]["torch"],"devices":result["protocol"]["device"],"confirmation_summary":summary.to_dict("records"),
        "comparisons":comparison.to_dict("records"),"audit":audit,"metadata_recovery":"Four completed fits preserved; only version string metadata changed; numeric hashes verified",
        "test_is_monitored_not_blind":True,"data_vintage_audited":False,"MPC_evaluated":False,"external_features_added":False,"remote_published":False,"formal_submission":False}
    (course/"materials/SOURCE-20261110-TRANSFORMER-THREESEED.json").write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    p=course/"tasks.json";old=p.read_text(encoding="utf-8-sig");j=json.loads(old);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["forecast_transformer_threeseed"]={"status":"completed_local_exploratory_not_published","source_id":sid,"folder":str(ROOT.relative_to(course)),
        "unique_fits":66,"screen_fits":42,"confirmation_models":27,"seeds":[17,29,43],"parameters":5407,"selected_transformer_configs":result["selection"],
        "GPU_used":True,"same_environment_recurrent_controls":True,"every_step_full_three_set_eval":True,"audit_all_passed":True,"MPC_evaluated":False}
    task["next_action"]="完成5407参数小Transformer：seed17七窗口×两学习率×三目标初筛42次，选定配置补至三种子9模型；原RNN/LSTM配置在相同2.14.1+cu130环境重训三种子18模型，共66唯一拟合。Transformer用5090GPU、对照CPU；每step完整三集eval，仅val选点/窗/lr。候选："+windows+"。"+changes+"。重复种子检验训练随机性，不是数据重采样或盲测。模型/特征/控制器下一步由用户决定，MPC仍未执行，项目open，未上传或改正式v4.1。"
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    entry="2026-11-10 完成11-09启动的约5.4k参数Transformer试验，入口 `assignments/FinalProject/tier2b-transformer-grid-20261109/REPORT_ZH.md`，包 `MMCS_Tier2B_Transformer_Grid_20261109.zip`。一层encoder，d24/head3/FFN54、固定相对位置、pre-LN/GELU，5407参数；日期/输入/标化同前，七窗口×两lr×三目标seed17初筛42，val选定后补29/43形成9个TF确认模型，原RNN5373/LSTM5409候选同新环境重训18个对照，共66唯一拟合。CUDA环境独立，TF用5090、CPU对照，逐step全量三集评估；候选："+windows+"。"+changes+"。电价相对RNN平均test差4.70%，已完整保留该更强对照；供给/需求相对LSTM均值小幅改善，种子范围重叠。已报告均值/种子SD/逐seed差、简单周基准和过拟合曲线；66checkpoint/划分/参数/源哈希/元数据恢复/选点/停止核验通过。初始4个训练仅修复版本号元数据并保持数值权重哈希不变。Test已监测非盲测，种子重复不覆盖未来年不确定性；MPC/数据发布版本审计未做、无外部特征、未上传或改正式报告。源 `"+sid+"`。\n\n"
    p=course/"STATUS.md";old=p.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    updated=old.replace("更新：2026-11-09","更新：2026-11-10",1).replace("## 当前阶段\n","## 当前阶段\n"+entry,1)
    assert p.read_text(encoding="utf-8-sig")==old;p.write_text(updated,encoding="utf-8")
    handoff=course.parent/"global/handoffs"/f"{now:%Y-%m-%d-%H%M}-MMCS-transformer-threeseed.md"
    handoff.write_text("# MMCS 小型Transformer三种子复核完成\n\n"+entry+"MMCS-008仍open，无新增截止或课表变更。仅匿名隔离Playwright MCP核官方PyTorch索引/文档，未查学校平台/邮箱；本轮不代表全面课程同步，未上传或提交。\n",encoding="utf-8")
    print(json.dumps({"source_id":sid,"archive":str(archive),"sha256":sha(archive),"handoff":str(handoff)},ensure_ascii=False))


if __name__=="__main__":main()
