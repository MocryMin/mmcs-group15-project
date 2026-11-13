"""Prepare a self-contained personal-workspace snapshot without public writes."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import re
import sys

PROJECT=Path(__file__).resolve().parent.parent
REPO=PROJECT/"group-collaboration"
SOURCE=PROJECT/"baseline-1104"
DEST=REPO/"Tier1/workspaces/mocry/codex/baseline-1104/20261104-v1"
REPAIR=REPO/"Tier1/public/data_quality/full_data_repair/20261104-v2"
RESEARCH=REPO/"Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1"
TEXT={".py",".md",".txt",".csv",".json",".jsonl",".yml",".yaml"}
COPIES=[]


def digest(data): return hashlib.sha256(data).hexdigest()


def put(path,data):
    target=DEST/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)


def put_text(path,text): put(path,text.replace("\r\n","\n").encode("utf-8"))


def copy_file(source,relative):
    raw=source.read_bytes()
    data=raw.replace(b"\r\n",b"\n") if source.suffix in TEXT else raw
    put(relative,data)
    COPIES.append(dict(source=source.relative_to(PROJECT.parent.parent).as_posix(),packaged=relative.as_posix(),
                       source_sha256=digest(raw),package_sha256=digest(data),newline_normalized=raw!=data))


def copy_tree(source,relative):
    for p in sorted(source.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc",".pyo"}:
            copy_file(p,relative/p.relative_to(source))


def main():
    if DEST.exists():
        assert not (DEST/"PACKAGE_MANIFEST.json").exists(),"Completed version already exists"
        assert (DEST/"calculation/results.json").read_bytes()==(SOURCE/"results.json").read_bytes().replace(b"\r\n",b"\n"),"Unexpected existing workspace content"
    DEST.mkdir(parents=True,exist_ok=True)
    copy_tree(SOURCE,Path("calculation"))
    # Preserve the local exact source and run metadata before portability edits.
    for name in ["run_baseline.py","verify_baseline.py","build_summary.py","RUN_MANIFEST.json","DELIVERY_MANIFEST.json"]:
        copy_file(SOURCE/name,Path("provenance/original")/name)
    copy_tree(REPAIR,Path("inputs/data_repair"))
    copy_tree(RESEARCH,Path("inputs/research"))
    copy_tree(REPO/"Tier1/public/baseline_1103",Path("inputs/assumptions_1103"))
    for name in ["daily_generation_by_fuel.csv","daily_generation_total.csv","daily_demand.csv","daily_market_index_price.csv","wind_farm_generation.csv"]:
        copy_file(REPO/name,Path("inputs/course_originals")/name)
    copy_file(PROJECT/"research-1103-controlled/control/browser_captures/R4/ONS-CPI-CSV.csv",Path("inputs/finance/ONS-CPI-CSV.csv"))
    for name in ["SOURCE-20261104-TIER1-BASELINE1104.json","SOURCE-20261104-FULL-DATA-REPAIR.json"]:
        copy_file(PROJECT.parent.parent/"materials"/name,Path("provenance")/name)

    calc=DEST/"calculation"
    p=calc/"run_baseline.py"
    code=p.read_text(encoding="utf-8")
    code=code.replace('REPO = PROJECT / "group-collaboration"','REPO = PROJECT / "inputs/course_originals"')
    code=code.replace('RELEASE = REPO / "Tier1/public/data_quality/full_data_repair/20261104-v2"','RELEASE = PROJECT / "inputs/data_repair"')
    code=code.replace('RESEARCH = REPO / "Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1"','RESEARCH = PROJECT / "inputs/research"')
    code=code.replace('PROJECT / "research-1103-controlled/control/browser_captures/R4/ONS-CPI-CSV.csv"','PROJECT / "inputs/finance/ONS-CPI-CSV.csv"')
    code=code.replace('str(p.relative_to(PROJECT)):hashlib.sha256','p.relative_to(PROJECT).as_posix():hashlib.sha256')
    old='    xp.init(os.environ.get("XPRESS_LICENSE_FILE","C:/xpressmp/bin/xpauth.xpr"))'
    assert old in code
    code=code.replace(old,'    init_xpress()')
    init='''def init_xpress():
    supplied=os.environ.get("XPRESS_LICENSE_FILE")
    windows_default=Path("C:/xpressmp/bin/xpauth.xpr")
    if supplied:
        xp.init(supplied)
    elif windows_default.exists():
        xp.init(str(windows_default))
    else:
        xp.init()


'''
    code=code.replace('def save_json(path, value):',init+'def save_json(path, value):')
    put_text(Path("calculation/run_baseline.py"),code)
    code=(calc/"verify_baseline.py").read_text(encoding="utf-8").replace('    rb.xp.init("C:/xpressmp/bin/xpauth.xpr")','    rb.init_xpress()')
    code=code.replace('(HERE.parent/name)','(Path(__file__).resolve().parent.parent/name)')
    put_text(Path("calculation/verify_baseline.py"),code)
    code=(calc/"build_summary.py").read_text(encoding="utf-8")
    code=code.replace('import hashlib\n','import hashlib\nimport os\n')
    code=code.replace('HERE=Path(__file__).resolve().parent','HERE=Path(os.environ.get("MMCS_BASELINE_OUTPUT",str(Path(__file__).resolve().parent)))')
    code=code.replace('../group-collaboration/Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1/README.md','../inputs/research/README.md')
    code=code.replace('../group-collaboration/Tier1/public/data_quality/full_data_repair/20261104-v2/README.md','../inputs/data_repair/README.md')
    put_text(Path("calculation/build_summary.py"),code)

    run=json.loads((calc/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    source_paths=[DEST/"inputs/research/BASELINE_CANDIDATE.json",DEST/"inputs/finance/ONS-CPI-CSV.csv"]+list((DEST/"inputs/data_repair/data").glob("*.csv"))
    run["source_files"]={p.relative_to(DEST).as_posix():digest(p.read_bytes()) for p in source_paths}
    run["publication"]="personal workspace snapshot; not a group-adopted baseline"
    put_text(Path("calculation/RUN_MANIFEST.json"),json.dumps(run,ensure_ascii=False,indent=2)+"\n")
    original_index=(calc/"README.md").read_text(encoding="utf-8")
    original_index=original_index.replace('../group-collaboration/Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1/README.md','../inputs/research/README.md')
    original_index=original_index.replace('../group-collaboration/Tier1/public/data_quality/full_data_repair/20261104-v2/README.md','../inputs/data_repair/README.md')
    put_text(Path("calculation/README.md"),original_index)

    versions={name:importlib.metadata.version(name) for name in ["xpress","numpy","pandas","scipy","matplotlib"]}
    put_text(Path("requirements.txt"),"\n".join(f"{name}=={version}" for name,version in versions.items())+"\n")
    put_text(Path(".gitignore"),"__pycache__/\n*.pyc\nreproduced/\n")
    put_text(Path("reproduce.py"),'''"""Re-run the packaged study into a fresh directory and compare saved results."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import runpy
import sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument("--output",type=Path)
args=parser.parse_args()
out=args.output.resolve() if args.output else ROOT/"reproduced"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
if out.exists() and any(out.iterdir()):
    raise SystemExit("Choose an empty output directory; archived results will not be overwritten.")
if out==ROOT or out.is_relative_to(ROOT/"calculation") or out.is_relative_to(ROOT/"inputs"):
    raise SystemExit("Choose a separate output directory.")
out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/"calculation"))
import run_baseline as rb
rb.HERE=out
sys.argv=[str(ROOT/"calculation/run_baseline.py")]
rb.main()
import verify_baseline as vb
vb.HERE=out
vb.main()
os.environ["MMCS_BASELINE_OUTPUT"]=str(out)
runpy.run_path(str(ROOT/"calculation/build_summary.py"),run_name="__main__")
original={r["case"]:r for r in json.loads((ROOT/"calculation/results.json").read_text(encoding="utf-8"))}
rerun={r["case"]:r for r in json.loads((out/"results.json").read_text(encoding="utf-8"))}
assert original.keys()==rerun.keys()
largest=0.
for name,ref in original.items():
    got=rerun[name]
    assert ref["battery_units"]==got["battery_units"] and ref["electrolyser_units"]==got["electrolyser_units"],name
    for key in ["net_profit_GBP2020_year","increment_GBP2020_year"]:
        error=abs(ref[key]-got[key]); largest=max(largest,error)
        assert error<1.,(name,key,error)
receipt={"cases":len(original),"same_installed_counts":True,"max_profit_difference_GBP2020":largest,"all_checks_passed":True}
(out/"REPRODUCTION_CHECK.json").write_text(json.dumps(receipt,indent=2)+"\\n",encoding="utf-8")
print(json.dumps(receipt,indent=2))
print("Reproduced outputs:",out)
''')

    readme='''# Ran Min 的 Tier1 Baseline 1104 完整计算包

版本 20261104-v1，2026 年 11 月 4 日。个人工作区实验与候选方案，由 mocry-codex 整理。

先读 [假设、分析与结论](calculation/README.md)，再按需要查看 [数学模型](calculation/MODEL.md)、[参数](calculation/parameters.json)、[全部案例结果](calculation/results.csv)和 [验证结果](calculation/VERIFICATION.json)。本包包括本轮计算使用的数据快照、代码、82 个案例的逐日计划、比较图与来源记录，可以在单独目录复算。它没有把 Baseline 1104 升格为小组已采纳的公共方案。

## 内容

| 目录或文件 | 内容 |
|---|---|
| calculation/ | 完整假设与分析、数学定义、参数、主模型/校验/汇总代码、82 案例结果、逐日计划和比较图。 |
| inputs/data_repair/ | 完整修复 20261104-v2：五份模型输入、质量与修改审计、原始公开来源快照、修复和检验代码。 |
| inputs/course_originals/ | 五份课程原始 CSV，供对照与价格消融。 |
| inputs/research/ | 本轮采用的已审核研究 v1.1、推荐参数及其来源说明。 |
| inputs/finance/ | 实际使用的 ONS 月 CPI 快照。 |
| inputs/assumptions_1103/ | 教师澄清、解释、缺口与 1103 假设族的来源快照。 |
| provenance/ | 原计算代码/清单、文件复制及相对路径调整记录、课程内来源记录。 |
| requirements.txt | 本次复算环境的 Python 库版本。许可证不随包分发。 |
| reproduce.py | 使用包内输入，在新目录重跑、验证并与归档结果比较。 |
| PACKAGE_MANIFEST.json | 本包所有文件的提交形式 SHA-256，不包含自身。 |

## 复算

使用 Python 3.12 与 requirements.txt 所列库，并使 Xpress 许可证可用。在本文件夹运行：

```text
python reproduce.py
```

默认写入 reproduced/ 下的全新时间目录，保留 calculation/ 的归档。可以使用 --output 指定另一个空目录。Xpress 优先使用 XPRESS_LICENSE_FILE 环境变量，其次检查 Windows 常见安装位置，最后使用优化器默认许可证发现。主计算为 Python/Xpress，全样本 oracle 以 SciPy/HiGHS 求解。

程序核对全部 82 个案例的安装数量与年度收益，收益允许 £1 以下的数值差异。它同时执行能量、费用、设备与非零电池顺序检查。运行时长和迭代细节可能随求解器与机器变化。原始本地计算代码与路径调整列表位于 provenance/，模型系数、假设和归档数值不因打包改变。

## 条件与来源

参考情景的 £7.7990/kg 氢净回值及 10 吨/日承购量是明确的高价值条件。A/B 规则、零投资可选、年度设计/回放与价格修复影响均在分析中说明。年度外回放是固定容量的全知运营，不称为未知未来的因果策略测试。

修复数据固定于源发布提交 0a821eaf61a2b552682e185c137d98c5a9bffc93。这里的研究和澄清是来源快照，各自原说明保留其当时状态。它们之间的历史导航在原仓库可用，实际复算只使用包内配置和输入。ONS CPI 原公开入口为 https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23 。
'''
    put_text(Path("README.md"),readme)
    put_text(Path("provenance/COPY_RECORD.json"),json.dumps(COPIES,ensure_ascii=False,indent=2)+"\n")
    portability=dict(
        version="20261104-v1",prepared_at_UTC=datetime.now(timezone.utc).isoformat(),
        owner="Ran Min",agent="mocry-codex",python=sys.version,library_versions=versions,
        numerical_model_changed=False,
        adjustments=["Source locations use snapshots under inputs/.","Source-manifest keys use portable relative paths.","License lookup accepts an environment override and default discovery.","Reproduction uses a new output directory and preserves archived results.","Text newlines are normalized to Git LF; original byte hashes are recorded.","Build helper accepts the new output directory; local navigation points to snapshots."],
        original_local_directory="baseline-1104",publication="personal workspace only, one pointer notice")
    put_text(Path("provenance/PACKAGING.json"),json.dumps(portability,ensure_ascii=False,indent=2)+"\n")
    for p in DEST.rglob("*.py"): ast.parse(p.read_text(encoding="utf-8"))
    # Replaced manifests describe the packaged representation, not another run.
    calc_files=[p for p in calc.rglob("*") if p.is_file() and p.name!="DELIVERY_MANIFEST.json"]
    put_text(Path("calculation/DELIVERY_MANIFEST.json"),json.dumps({p.relative_to(calc).as_posix():digest(p.read_bytes()) for p in sorted(calc_files)},indent=2)+"\n")
    manifest={p.relative_to(DEST).as_posix():dict(sha256=digest(p.read_bytes()),bytes=p.stat().st_size)
              for p in sorted(DEST.rglob("*")) if p.is_file() and p.name!="PACKAGE_MANIFEST.json"}
    put_text(Path("PACKAGE_MANIFEST.json"),json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(folder=DEST.relative_to(REPO).as_posix(),files=len(manifest)+1,bytes=sum(x["bytes"] for x in manifest.values())),indent=2))


if __name__=="__main__": main()
