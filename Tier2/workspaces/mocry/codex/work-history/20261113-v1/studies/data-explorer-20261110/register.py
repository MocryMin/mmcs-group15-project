"""Register the local explorer without changing model results or project state."""
from pathlib import Path
from datetime import datetime,timezone
import json
import hashlib

ROOT=Path(__file__).resolve().parent


def main():
    qa=json.loads((ROOT/"QA.json").read_text());assert all(v["pass"] for v in qa["results"])
    metadata=json.loads((ROOT/"SOURCE.json").read_text());html=ROOT/"MMCS-data-explorer.html"
    course=ROOT.parents[2];sid="LOCAL-MMCS-DATA-EXPLORER-20261110"
    record={"source_id":sid,"recorded_at":datetime.now(timezone.utc).isoformat(),"status":"local_interactive_explorer_verified",
        "folder":str(ROOT.relative_to(course)),"html":str(html.relative_to(course)),"html_sha256":hashlib.sha256(html.read_bytes()).hexdigest(),
        "metadata":metadata,"qa":qa,"remote_published":False,"model_data_or_results_changed":False}
    path=course/"materials/SOURCE-20261110-DATA-EXPLORER.json";assert not path.exists()
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    path=course/"tasks.json";old=path.read_text(encoding="utf-8-sig");j=json.loads(old);task=next(t for t in j["tasks"] if t["id"]=="MMCS-008")
    task["data_explorer"]={"status":"completed_local_not_published","source_id":sid,"html":str(html.relative_to(course)),"samples":metadata["rows"],
        "default_range":[metadata["default_start"],metadata["default_end"]],"date_range":[metadata["start"],metadata["end"]],"offline":True,"interaction_checks_passed":True}
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    path=course/"STATUS.md";old=path.read_text(encoding="utf-8-sig");assert "## 当前阶段\n" in old
    entry="2026-11-10 本地日度行情GUI完成：`assignments/FinalProject/data-explorer-20261110/MMCS-data-explorer.html`，数据同冻结预测实验(hash addc31ee...)，2021-01-01—2026-09-17共2086日，默认测试年2025-09-01—2026-08-31共365日。独立离线单HTML，供给/需求GW、净差GW、电价GBP/MWh联动面板；任意日期、年份/训练划分快捷选择、真鼠标滚轮/拖动/框选/底部滑块、散点折线切换、7/30日均线、自动Y轴、日期级估算标记、CSV/PNG导出。Playwright MCP可视与交互验收通过，含闰年/单日/错误范围/完整导出；无外部网络依赖。未改模型/数据/正式报告或上传，项目仍open。来源 `"+sid+"`。\n\n"
    assert path.read_text(encoding="utf-8-sig")==old;path.write_text(old.replace("## 当前阶段\n","## 当前阶段\n"+entry,1),encoding="utf-8")
    print(json.dumps({"html":str(html),"sha256":record["html_sha256"],"source_id":sid},ensure_ascii=False))


if __name__=="__main__":main()
