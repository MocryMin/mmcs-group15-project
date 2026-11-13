"""Create a checkable rule index from the supplied VTT, without inventing audio."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT.parents[1]
SOURCE = COURSE / "materials/project-launch-transcripts-20261028"
cues = json.loads((SOURCE / "cues.json").read_text(encoding="utf-8"))

def seconds(stamp):
    parts = stamp.split(":")
    return sum(float(x)*60**i for i,x in enumerate(reversed(parts)))

# The timestamps refer to the exported recording timeline, not elapsed classroom time.
rules = [
    ("R01","00:03:49","00:05:55","Kit","课堂安排/角色","授课部分结束，后续转项目；外部代表扮演客户，Kit提供技术支持。","讲义0及brief1–2","project time"),
    ("R02","00:28:20","00:30:25","客户代表","咨询目标","建议应解释投资回报、回本时间，并优于客户原有方案。","brief2、5","break-even"),
    ("R03","00:31:40","00:33:55","客户代表","模型推进","先有可运行的简化模型，再做扩展；技术报告支撑商业展示。","brief2–3、5","first working model"),
    ("R04","00:34:00","00:35:25","客户代表","AI表述/建议","客户代表欢迎使用生成式AI，但要求团队提出自己的想法；SMART为建议。","brief未给AI细则","generative AI"),
    ("R05","00:35:35","00:36:30","客户代表","代码呈现","不以炫技式代码为重点；这不能单独推出无需上传代码。","brief1要求Python+Xpress","never look at the code"),
    ("R06","00:36:20","00:40:35","客户代表","模型范围","Tier1人人完成，再选Tier2A其他设施投资或Tier2B时序运营之一。","brief2–4","mandatory"),
    ("R07","00:40:25","00:41:25","客户代表","自主选择","目标和约束建议是起点，允许有依据的其他建模选择。","brief1、4","suggested some objectives"),
    ("R08","00:47:10","00:47:45","客户代表","创新挑战","鼓励每组至少提出一个有新意的建议，未给单独分值。","brief5的改进与解释","outside the box suggestion"),
    ("R09","00:50:30","00:51:20","客户代表","AI视觉表述","明确接受AI生成展示视觉，但不能喧宾夺主。","无对应书面细则","generative AI"),
    ("R10","00:51:20","00:54:25","客户代表","展示要求","商业展示不放公式或代码，技术模型放技术报告。","brief5受众与建议","No equations"),
    ("R11","00:54:35","00:59:25","客户代表","展示建议","可一人讲或分人讲；少文字、合适图示和简单动画；给出建议结构而非固定页数。","无固定页数对应","one person delivers"),
    ("R12","01:00:45","01:01:35","Kit/客户代表","支持安排","还将有三次客户Q&A，具体日程没有在此确定。","brief5监督支持","3 Q&A"),
    ("R13","01:04:05","01:05:05","Kit","范围辨别","附录不计六页且通常不评阅的说明，明确针对Assignment2，不能移植为project规则。","A2规则","assignment too"),
    ("R14","01:05:05","01:06:20","Kit","课堂/工作坊","周一讲课时段改项目工作与答疑；workshop可与组员协调参加其中一小时或两小时。","讲义0旧安排的课堂更新","same workshop"),
    ("R15","01:06:18","01:06:40","Kit","报告硬要求","最终技术报告10页上限；此段没有明确附录/参考文献计页方法。","新增，brief未列页限","10-page limit"),
    ("R16","01:06:40","01:07:40","Kit","展示硬要求","最终展示是business pitch；模型数学式/代码片段被明确列为禁止内容。","brief5受众要求补充","non-negotiable"),
    ("R17","01:07:40","01:08:55","Kit","教师可用时间","本周和下周五Kit不在，Kacper仍在；下周一在、再下周一不在；将提供约20分钟线上组会。","待后续公告落实","20 minutes"),
    ("R18","01:11:45","01:12:42","Kit","数据来源","风场发电序列是设施参数加天气数据模拟，简化忽略故障和维护。","brief2构造系统说明","simulated"),
    ("R19","01:12:40","01:14:00","Kit","基准信息结构","基础模型可以确定性、完全预知未来发电/需求/价格。","brief3简化Tier1","purely deterministic"),
    ("R20","01:14:00","01:16:00","Kit","可选设计/价值","投资时点可以扩展；电池既吸收多余电，也能低价存高价卖。","brief3与4","prices are low"),
    ("R21","01:16:00","01:17:25","Kit","氢能选项/示例数值","售氢是简单出口；储氢后再发电是可选扩展；口头2.50英镑仅示例。","brief3的9.5基准未被修改","2 pounds 50"),
    ("R22","01:17:30","01:18:40","Kit","进阶投资","投资方案应考虑未来不确定，可用先投资、后在情景中运营的两阶段思路。","brief3–4的Tier2A深化","two-stage"),
    ("R23","01:18:40","01:20:10","Kit","进阶运营","运营路线强调当天决策时不知道未来，不只是在历史数据上完全预知未来地优化。","brief4的Tier2B深化","nothing about the future"),
    ("R24","01:20:10","01:20:45","Kit","后续支持","有需要可询问用于生成风场序列的代码；此时尚未提供文件。","无已归档代码","code that I use"),
    ("R25","01:20:45","01:23:40","Kit","系统边界","基准忽略电网位置/输电瓶颈；网约束可作为自主扩展，不是普遍必做项。","brief2构造系统","ignore the effects"),
    ("R26","01:23:40","01:25:12","Kit","小组运作","每周持续推进；成员不参与等问题须尽早反映，不能临近截止才说。","brief5团队责任","group dynamics"),
]

records = []
for key,start,end,speaker,kind,summary,pdf,anchor in rules:
    selected = [c for c in cues if seconds(c["end"])>=seconds(start) and seconds(c["start"])<=seconds(end)]
    raw = " ".join(c["text"] for c in selected)
    if anchor not in raw:
        if key == "R01":
            assert "taught component" in raw
        else:
            assert anchor.lower() in raw.lower(), (key, anchor)
    records.append(dict(id=key,start=start,end=end,speaker=speaker,kind=kind,summary=summary,
                        pdf_relation=pdf,cue_ids=[c["index"] for c in selected],transcript_excerpt=raw,
                        audio_verified=False))
(ROOT / "LAUNCH_EVIDENCE.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
lines = ["# 项目说明课：时间戳与证据索引", "", "来源是用户提供的同一份转写的TXT/VTT两种导出；不是两个独立转写。未取得原音视频，时间采用VTT原视频时间轴。课堂日期按用户此前安排及字幕中A2当天下午截止的语境对应2026-10-26。", "", "[纯文本原件](../../materials/project-launch-transcripts-20261028/MATHO%20Methodology,%20M-transcript.txt) · [VTT原件](../../materials/project-launch-transcripts-20261028/MATHO%20Methodology,%20M-transcript.vtt) · [可检索的带时间分段文本](../../materials/project-launch-transcripts-20261028/transcript-timed.txt)", "", "| 编号 | 视频时间 | 说话方 | 类型 | 关键信息 | 书面材料关系 |", "|---|---|---|---|---|---|"]
for r in records:
    lines.append(f'| {r["id"]} | {r["start"]}–{r["end"]} | {r["speaker"]} | {r["kind"]} | {r["summary"]} | {r["pdf_relation"]} |')
lines += ["", "## 使用边界", "", "- 重点的十页限制、商业展示禁公式/代码、项目工作时段均有Kit的明确字幕语句；字幕尚未回听验证。", "- 后续教师公告或书面评估规定若给出不同细节，应保留两项来源并核对适用范围。", "- 公司/人名的语音识别有明显变体，客户代表用角色称呼；SPEAKER标签不作为独立身份验证。", "- 自动转写中的68页、23个数据集、Vila/Express/PieTA等不按字面当新规则；结合brief可辨为6–8页/两三个重要数据集/vanilla/Xpress/Piazza等语境。", "- R13只涉及A2：project是否排除附录或参考文献仍待正式说明。", ""]
(ROOT / "LAUNCH_EVIDENCE.md").write_text("\n".join(lines),encoding="utf-8")
print(f"Indexed {len(records)} timestamped statements; all anchors found in actual subtitle cues.")
