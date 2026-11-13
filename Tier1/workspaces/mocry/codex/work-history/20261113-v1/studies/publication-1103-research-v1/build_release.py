"""Prepare a path-normalised, versioned research release and standalone Chat files."""
from pathlib import Path
import argparse, csv, datetime, hashlib, io, json, re, sys, zipfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SOURCE = PROJECT / 'research-1103-controlled'
REPO = PROJECT / 'group-collaboration'
sys.path.insert(0, str(REPO / 'tools'))
from collab import run_child

STAGE = HERE / 'staging'
VERSION = '20261103-v1'
PUBLIC = f'Tier1/public/research_1103/controller/mocry-codex/{VERSION}'
REPO_URL = 'https://github.com/MocryMin/mmcs-group15-project'
BASE = '64d2a9b697a0b80af4c3e062dea8cc7f5fca2ff4'
CHAT = PROJECT / 'chat-handoff-1103-research-v1'
PUBLIC_DIR = REPO / PUBLIC

def digest(data): return hashlib.sha256(data).hexdigest()
def dump(obj): return (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
def normal(s): return re.sub('/+', '/', s.replace('\\','/'))
def git_bytes(rel, data):
    blob=run_child(['git','hash-object','-w','--path='+PUBLIC+'/'+rel,'--stdin'],input=data,cwd=REPO,capture_output=True,check=True).stdout.strip().decode()
    return run_child(['git','cat-file','blob',blob],cwd=REPO,capture_output=True,check=True).stdout

capture_urls = {}
for path in (SOURCE/'control/browser_captures').rglob('*.json'):
    obj = json.loads(path.read_text(encoding='utf-8-sig'))
    if isinstance(obj, dict) and obj.get('url'):
        capture_urls[path.name] = obj['url']
        capture_urls[path.with_suffix('.csv').name] = obj['url']

def source_for_local(s, context=None):
    n = normal(s)
    if n.endswith('Project-brief-extracted.txt'):
        return f'{REPO_URL}/blob/{BASE}/Project_Brief.pdf'
    if 'group-collaboration/' in n:
        return f'{REPO_URL}/blob/{BASE}/'+n.split('group-collaboration/',1)[1]
    if context and context.get('url'): return context['url']
    return None

def transform_json(x):
    if isinstance(x, list): return [transform_json(y) for y in x]
    if not isinstance(x, dict):
        if isinstance(x,str):
            n=normal(x)
            if re.match(r'^[A-Za-z]:/',n):
                return source_for_local(x) or 'Controller-retained evidence: '+n.rsplit('/',1)[-1]
        return x
    out={}
    for k,y in x.items():
        if k in ('capture_path','capture'):
            out['retrieval_record']='Controller-retained source capture; not redistributed with this release'
            if isinstance(y,str):out['retrieval_record_id']=normal(y).rsplit('/',1)[-1]
        elif k=='local_path':
            if y is None:
                continue
            url=source_for_local(y,x)
            if url:out['public_source_url']=url
            else:out['retained_evidence_id']=normal(y).rsplit('/',1)[-1]
        else:out[k]=transform_json(y)
    return out

def transform_md(text):
    def link(m):
        label,target=m.group(1),m.group(2)
        if 'browser_captures/' in target:
            name=normal(target).rsplit('/',1)[-1]
            return f'[{label}]({capture_urls[name]})' if name in capture_urls else label+' (controller-retained capture)'
        return m.group(0)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,text)
    text=re.sub(r'`control/browser_captures/([^`]+)`',lambda m:'`controller-retained evidence: '+m.group(1)+'`',text)
    return text

def chosen_files():
    selected=['RESEARCH_SYNTHESIS.md','BASELINE_CANDIDATE.json',
      'control/REVIEW_DECISIONS.json','control/RUN.json','control/VALIDATION.json']
    for topic in ['R1-market','R2-battery','R3-hydrogen','R4-finance-data']:
        selected += [topic+'/'+name for name in ['REPORT.md','parameters.json','sources.json']]
    selected += ['R1-market/CROSS_REVIEW_R4.md','R2-battery/CROSS_REVIEW_R3.md',
      'R3-hydrogen/CROSS_REVIEW_R2.md','R3-hydrogen/CONTROLLER_FOLLOWUP_IEA.md',
      'R2-battery/calculations.json','R4-finance-data/data_audit.json',
      'R4-finance-data/financial_audit.json','R4-finance-data/prices_gbp2020.csv']
    selected += [p.relative_to(SOURCE).as_posix() for p in sorted(SOURCE.glob('*/FIRST_PASS/*')) if p.suffix in ('.md','.json')]
    return selected

def build_release():
    assert not PUBLIC_DIR.exists(), 'Version already exists: create a new version rather than overwrite it'
    STAGE.mkdir(exist_ok=True)
    records=[]
    for rel in chosen_files():
        src=SOURCE/rel; raw=src.read_bytes()
        if src.suffix=='.json':
            obj=transform_json(json.loads(raw.decode('utf-8-sig')))
            if rel=='BASELINE_CANDIDATE.json':
                obj['status']='controller_reviewed_research_proposal_not_group_adopted'
                obj['publication']='Tier1 public research release '+VERSION
            if rel=='control/VALIDATION.json':
                obj['scope']='Original pre-publication research audit; public-copy hashes and links are covered separately by RELEASE_VALIDATION.json'
                obj['original_local_research_artifact_hashes']=obj.pop('final_artifact_hashes')
            data=dump(obj)
        elif src.suffix=='.md':
            text=transform_md(raw.decode('utf-8-sig'))
            if rel=='R3-hydrogen/REPORT.md':
                text=text.replace('PEM 2020投产参考（10 MW）','PEM 2020投产参考（10 MW H2 HHV输出）')
            if rel=='RESEARCH_SYNTHESIS.md':
                text=text.replace('本地推荐参数包','主控推荐参数包')
                text=text.replace('本轮没有更改课程原件、过往作业、小组远程仓库或正式提交。此处的采纳是主控本地研究处置；公共baseline的组级采纳仍走小组既定协作协议。',
                    '研究阶段未更改课程原件、过往作业或正式提交。本次将研究结果发布为独立v1；Baseline1103假设正文保持，公共baseline的组级采纳仍走小组既定协作协议。')
            data=text.encode('utf-8')
        else:data=raw
        data=git_bytes(rel,data)
        target=STAGE/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records.append({'path':rel,'source_research_relative_path':rel,'source_sha256':digest(raw),
                        'published_sha256':digest(data),'path_or_publication_metadata_normalised':raw!=data})
    summary=(HERE/'EXECUTIVE_SUMMARY_EN.md').read_text(encoding='utf-8').replace('Release 20261103-v1.','Release '+VERSION+'.').encode('utf-8')
    summary=git_bytes('EXECUTIVE_SUMMARY_EN.md',summary)
    (STAGE/'EXECUTIVE_SUMMARY_EN.md').write_bytes(summary)
    records.append({'path':'EXECUTIVE_SUMMARY_EN.md','source_research_relative_path':None,'published_sha256':digest(summary),'role':'English editorial synopsis, consistent with controller recommendation'})
    readme=f'''# Tier1 reviewed research release {VERSION}

Published by Ran Min's registered agent `mocry-codex` on 3 November 2026. Status: **controller-reviewed research and recommended parameters, open for group review**. This release does not replace the agreed/proposed model by implication. The original [Baseline 1103]({REPO_URL}/blob/{BASE}/Tier1/public/baseline_1103/BASELINE_1103.md) remains its source model family.

## Start here

|File|Purpose|
|---|---|
|[Research synthesis in Chinese](RESEARCH_SYNTHESIS.md)|Findings, controller dispositions, modelling consequences and closure criteria|
|[English synopsis](EXECUTIVE_SUMMARY_EN.md)|Readable account of the same main conclusions|
|[Recommended parameter package](BASELINE_CANDIDATE.json)|Typed values, units, scenario branches, assumptions and remaining conditions|
|[Review decisions](control/REVIEW_DECISIONS.json)|20 accept/reject/conditional/defer decisions|
|[Market](R1-market/REPORT.md), [battery](R2-battery/REPORT.md), [electrolyser and H2](R3-hydrogen/REPORT.md), [data and finance](R4-finance-data/REPORT.md)|Four full topic reports with parameter/source catalogues|
|[Release manifest](RELEASE_MANIFEST.json) and [release validation](RELEASE_VALIDATION.json)|Version, provenance, content hashes and public-copy checks|

The original first passes are preserved under each worker's `FIRST_PASS` directory as path-normalised public copies. Their original local-byte hashes and release-copy hashes are distinguished in the manifest. Later cross-reviews and the IEA follow-up do not rewrite those original local first passes.

## Decisions that matter

- The DEA battery maintenance source has a twofold formula/unit conflict. Keep both cases; the controller proposes the total-CAPEX2.9% interpretation as the main case.
- IEA2025's actual2024 outside-China installed-cost range replaces the old UK proxy as the modern electrolyser CAPEX reference. Keep the source's rawUSD, declared reporting assumptions and legacy sensitivity.
- Do not double-count PCS/EPC, inclusive maintenance, stack replacement/reserves, or supported hydrogen payments. Actual H2offtake, price/quality terms and support eligibility remain scenario conditions.
- Keep negative electricity prices, preserve state chronology and use a common currency/price-year/horizon across A0/A1/B0/B1. No new optimisation result is claimed by this release.

## Version and source policy

Version path: `{PUBLIC}`. Treat this directory as a release snapshot. Corrections should add another version or a separately recorded correction; do not silently replace release files. Existing public navigation updates are archived and logged through the collaboration helper. Other members' workspaces are untouched.

The five supplied CSVs, brief and complete lecture transcripts already exist at the repository root. External source URLs, read-depth and page/cell locators accompany the research. External full webpages, browser response/base64 files and third-party PDFs/XLSX binaries are retained by the controller and **not redistributed here**. Public copies remove machine-specific absolute paths; these transformations do not turn a modelling assumption into an observed fact.

The `control/RUN.json` and `control/VALIDATION.json` describe the completed research stage before publication; their no-push or local-only statements are historical stage metadata. This README and release manifest describe publication. Chat-only teammates receive separate self-contained Chinese/English files; they need no Git or agent registration to contribute.

All members/agents may challenge sources, units, gap definitions, assumptions or parameters. Publish independently under a unique path, reference this version or content hash, and send a new message. Publication and silence are not group agreement.
'''
    if VERSION!='20261103-v1':
        readme+='\n## Correction from v1\n\nVersion v1.1 corrects four Markdown hashes affected by Git CRLF-to-LF normalisation in v1. Research findings and all numerical recommendations are unchanged. This complete snapshot computes release hashes from Git-clean bytes before publication. The original v1 and its broadcast remain in history; navigation points here.\n'
    data=git_bytes('README.md',readme.encode('utf-8'));(STAGE/'README.md').write_bytes(data)
    records.append({'path':'README.md','published_sha256':digest(data),'role':'Release navigation and status'})
    manifest={'release_id':VERSION,'owner':'Ran Min','publisher_agent':'mocry-codex','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'public_path':PUBLIC,'research_run_id':'MMCS-TIER1-CONTROLLED-RESEARCH-20261103',
      'baseline_input_commit':BASE,'group_adoption':'not_established_by_publication',
      'transformation_policy':['Normalise controller-local absolute paths into public sourceURLs/evidenceIDs','Resolve omitted capturelinks to actualpublisherURLs','Clarify release status while preserving research-stage facts','Keep original and publiccopy hashes distinct','Compute released file hashes from exact Git-clean bytes including line-ending rules'],
      'excluded':['External complete webpages and response/base64 files','Third-party sourcePDF/XLSX binaries','Localbrowsertools and temporarydrafts','Unrelatedcourses/privateglobalrecords','Chat handoff files are distributed separately'],
      'files':records,'manifest_self_hash':'Excluded to avoid self-reference; Git commit pins all release files',
      'release_validation_hash':'Excluded; validation is produced after staging and is pinned by Git'}
    (STAGE/'RELEASE_MANIFEST.json').write_bytes(dump(manifest))
    print(json.dumps({'staged_files':len(records)+1,'version':VERSION,'manifest_sha256':digest(dump(manifest))}))

def markdown_to_text(text):
    text=re.sub(r'^#{1,6}\s+', '',text, flags=re.M)
    text=text.replace('**','').replace('`','').replace('$$','')
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 — \2',text)
    return text

def build_chat(commit):
    CHAT.mkdir(exist_ok=True)
    published=f'{REPO_URL}/tree/{commit}/{PUBLIC}'
    raw=f'{REPO_URL}/blob/{commit}/{PUBLIC}'
    params=json.loads((STAGE/'BASELINE_CANDIDATE.json').read_text(encoding='utf-8'))
    f=json.loads((STAGE/'R4-finance-data/financial_audit.json').read_text(encoding='utf-8'))
    old=PROJECT/'chat-handoff-1103'
    cn=(old/'TIER1.txt').read_text(encoding='utf-8-sig').split('6. 四类 research：')[0].rstrip('=\n ')
    en=(old/'TIER1_CHAT_CONTEXT_1103_EN.txt').read_text(encoding='utf-8-sig').split('6. Four research packages:')[0].rstrip('=\n ')
    cn=cn.replace('版本：2026-11-03 / Baseline 1103','版本：2026-11-03 / 已审核研究同步 v1 / Baseline 1103')
    cn=cn.replace('背景来源版本：共享仓库提交 64d2a9b697a0b80af4c3e062dea8cc7f5fca2ff4。',f'本次发布提交：{commit}。\n研究版本入口：{published}')
    cn=cn.replace('这是当前已共享讨论内容的独立背景快照。Baseline 是拟供全组评议的假设族，research 参数和小组整体采纳仍待完成；本文件不声称已经完成优化或得到最终投资结论。','这是独立完整的最新背景及研究同步文件，取代旧Chat背景包的“研究尚未开展”状态。首轮研究及审核已完成；推荐参数仍是主控建议，尚不代表全组采纳。本轮没有新投资最优解。')
    cn=cn.replace('当前进展：教师依据、缺口、Baseline 1103 和研究请求已共享；市场／设备／财务研究待开展，Baseline 参数未齐，不声称已有小组最终模型或数值答案。','当前进展：四主题研究、三项交叉审核和现代电解槽成本定向补查已完成。主控已关闭开放式搜索，推荐参数与明确情景条件见第6节及之后。小组最终模型和投资结果尚未由本轮确定。')
    cn=cn.replace('单列详细 rubric 和最终代码提交规则尚未收齐。','11月3日另读到报告/展示descriptor预览：报告只取得部分viewer文本，原件和最终代码提交规则仍未齐全。')
    en=en.replace('Version: 2026-11-03 / Baseline 1103','Version: 2026-11-03 / reviewed research sync v1 / Baseline 1103')
    en=en.replace('Source snapshot: shared repository commit 64d2a9b697a0b80af4c3e062dea8cc7f5fca2ff4.',f'Published commit: {commit}.\nResearch release: {published}')
    en=en.replace('This is a self-contained snapshot of the shared discussion. The baseline is a proposed assumption family for team review; research-dependent parameters and team-wide adoption are pending. No completed optimisation or final investment result is claimed.','This self-contained file supersedes the old Chat context\'s pending-research status. The first research round and review are complete. The controller recommends a parameter family; group adoption and a final investment result are not established.')
    en=en.replace('Progress: teacher evidence, gaps, Baseline 1103 and research requests have been shared. Market/equipment/financial research is still pending; parameters are incomplete. There is no claimed final group model or numerical answer.','Progress: four topics, three cross-reviews and a targeted modern electrolyser cost follow-up are complete. Open-ended searching is closed. Section6onwards contains findings and model-ready recommendations. No new investment optimisation was performed in this research round.')
    en=en.replace('A separate detailed rubric and final code-submission rules have not yet been collected.','On3November report/presentation descriptor previews were partially collected: the report viewer was incomplete, and original descriptors/final code-submission rules remain incomplete.')
    cn_add=markdown_to_text((STAGE/'RESEARCH_SYNTHESIS.md').read_text(encoding='utf-8'))
    # Convert release-relative Markdown links before converting prose toplain text.
    def expand_links(t):
        def link(m):
            target=m.group(2)
            return m.group(0) if target.startswith('https://') else f'[{m.group(1)}]({raw}/{target})'
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
    cn_add=markdown_to_text(expand_links((STAGE/'RESEARCH_SYNTHESIS.md').read_text(encoding='utf-8')))
    en_add=markdown_to_text((STAGE/'EXECUTIVE_SUMMARY_EN.md').read_text(encoding='utf-8'))
    shared_table=f'''\n\nNUMERIC INPUTS / 数值接口（all money below GBP2020 unless explicitly labelled）\nBattery nominal duration:2h; reference unit3MWh/1.5MW; integer unit counts are an analytical choice.\nSOC min/max:0.2/0.8; ACroundtrip0.9; symmetriceta_c=eta_d={params['battery']['eta_charge']:.12f}.\nSelfdischarge0.001/day: DEAtechnical scenario, distinguish from briefdefault.\nBattery CAPEX:{f['battery']['CAPEX_GBP2020_per_MWh']:.8f}/nameplateMWh.\nBattery FOM main:{f['battery']['FOM_capexcase_GBP2020_per_MWyr']:.8f}/MW/year; source-label alternative:{f['battery']['FOM_table_GBP2020_per_MWyr']:.8f}/MW/year.\nBattery reference calendar life15years; cycle/DoD and maintenance scope qualify this reference.\nElectrolyser module20MW; on range20–100%, off allowed;55.9ACkWh/kgBOL.\nModern installedCAPEX USD2000/2300/2600 perassumedelectricalkW;2300is analystmidpoint.\nModern rebasedCAPEX GBP2020:{f['modern_H2_CAPEX_reporting_scenario']['CAPEX_GBP2020_per_kW_assumed_electrical']['low']:.8f}/{f['modern_H2_CAPEX_reporting_scenario']['CAPEX_GBP2020_per_kW_assumed_electrical']['analyst_midpoint']:.8f}/{f['modern_H2_CAPEX_reporting_scenario']['CAPEX_GBP2020_per_kW_assumed_electrical']['high']:.8f}/kW under declared2024USD/electrical assumptions.\nOld hybridCAPEX:{f['hydrogen']['proxy_CAPEX_GBP2020_per_kWe']['central']:.8f}/kWe, historical sensitivityonly.\nOld absoluteFOMproxy:{f['hydrogen']['proxy_FOM_GBP2020_per_kWe_yr']:.8f}/kWe/year.\nOld absolute stackreplacementproxy:{params['hydrogen']['replacement_absolute_proxy_GBP2020_kWe']:.8f}/kWe/event atyear11/22 OR reserve:{f['hydrogen']['variable_reserve_GBP2020_per_kg']:.6f}/kg, notboth. Not60%ofmodernIEAcapex.\nWaterexample15L/kg atGBP2/m3 ->GBP0.03/kg: analyst scenario, notsupplierquote;55.9alreadyincludes statedBOPenergy.\nBriefH2benchmark GBP9.5/kg: originalpricebase unspecified.\nHAR1reportingreference:{f['supported_H2_reference']['GBP2020_per_kg']:.9f}/kg, supportedvalue ratherthanmerchantcontract.\nH2buyer scenarios0/2000/10000/50000kg/day; noactualbuyer confirmed.\nPlantlife30years and11yearstackinterval: oldtechnology scenario, notITMwarranty.\nPrimaryrealdiscount0.05; sensitivity0/0.03/0.05/0.08/0.12: analyst scenarios.\nECB2020GBP/EUR:{f['GBP_per_EUR_2020']:.13f}; ONSCPI2012={f['CPI_2012_annual']},2020={f['CPI_2020_annual']},2024={f['modern_H2_CAPEX_reporting_scenario']['CPI_2024_annual']}.\n\nExact reviewed machine parameter file: {raw}/BASELINE_CANDIDATE.json\nParameter file SHA256: {digest((STAGE/'BASELINE_CANDIDATE.json').read_bytes())}\n'''
    cn_end=f'''\n\n7. 组员可以怎样继续\n\n把这一份中文TXT上传或粘贴给自己的Chat即可，不需要Git和coding agent。请先让它解释已确定主干、主控建议和仍需情景化的内容；然后只选择一个贡献，例如核查FOM、改进日粒度电池近似、为实际氢买方补净回值来源，或提出新的证据/替代参数。请返回“问题或参数ID—来源—单位/价格年/边界—建议—对模型影响”。新增独立研究仍欢迎；这一轮搜索关闭不禁止他人补充。无需只为标记收到而回复。\n\n原始CSV不嵌入此TXT。若要统计或求解，另提供仓库根目录对应CSV和原题PDF。未实际读数据/联网/运行时不要编造验证。研究发布不会自动让教师原话、组内提案或任何参数变成全组已同意事实。\n\n固定版本入口：{published}\n四主题报告、三项交叉审核、IEA补查、20项主控处置、原始首轮快照和推荐JSON都在该入口。\n'''
    en_end=f'''\n\n7. Contributing through ordinary Chat\n\nUpload or paste this EnglishTXT alone. NoGit, terminal, codingagent orregistration isneeded. Askforan explanation, thenpickone scopedcontribution: reviewFOM, improve thedailybatteryapproximation, researchanactualH2netback, orchallengeasource/parameter. ReturnparameterorissueID, source, unit/priceyear/scope, recommendation andmodelconsequence. Furtherindependentcontributionsremainwelcome; endingthiscontrolledsearchdoesnotforbidnewresearch. Noacknowledgementisrequiredsolelytomarkreceipt.\n\nRawCSVrowsarenotembedded. Obtain thesuppliedCSVandbriefPDF separatelyforstatisticsoroptimisation. Do notfabricatefileaccess, webverification, solverresultsorgroupconsensus. Thisversion containsprojectcontext, teacher-evidence distinctions, theA/Bfamily, reviewedfindingsandnumericalconditions withoutrequiring another contextfile.\n\nPinnedrelease: {published}\nThefourreports, cross-reviews, IEAfollow-up,20controllerdispositions, first-passsnapshots andexactJSON arelinkedthere.\n'''
    # Editorial spaces for these newly authored closing paragraphs only.
    en_end='''\n\n7. Contributing through ordinary Chat\n\nUpload or paste this English TXT alone. No Git, terminal, coding agent or registration is needed. Ask for an explanation, then pick one scoped contribution: review FOM, improve the daily battery approximation, research an actual H2 netback, or challenge a source or parameter. Return the parameter or issue ID, source, unit/price year/scope, recommendation and model consequence. Further independent contributions remain welcome; ending this controlled search does not forbid new research. No acknowledgement is required solely to mark receipt.\n\nRaw CSV rows are not embedded. Obtain the supplied CSVs and brief PDF separately for statistics or optimisation. Do not fabricate file access, web verification, solver results or group consensus. This file contains project context, teacher-evidence distinctions, the A/B family, reviewed findings and numerical conditions without requiring another context file.\n\nPinned release: '''+published+'\nThe four reports, cross-reviews, IEA follow-up,20 controller dispositions, first-pass snapshots and exact JSON are linked there.\n'
    label=VERSION.split('-',1)[1].upper().replace('.','_')
    cn=cn.replace('已审核研究同步 v1 /','已审核研究同步 '+VERSION.split('-',1)[1]+' /')
    en=en.replace('reviewed research sync v1 /','reviewed research sync '+VERSION.split('-',1)[1]+' /')
    outputs={f'TIER1_RESEARCH_SYNC_1103_{label}_CN.txt':cn+'\n\n6. 已完成研究和主控审核\n\n'+cn_add+shared_table+cn_end,
      f'TIER1_RESEARCH_SYNC_1103_{label}_EN.txt':en+'\n\n6. Completed research and controller review\n\n'+en_add+shared_table+en_end}
    for name,text in outputs.items(): (CHAT/name).write_text(text,encoding='utf-8')
    (CHAT/'BASELINE_CANDIDATE.json').write_bytes((STAGE/'BASELINE_CANDIDATE.json').read_bytes())
    instruction='''使用方法 / How to use\n\n中文和英文TXT各自独立完整，只上传其中一份到新Chat即可。JSON是可选精确参数附件，不需要组员使用Git或codingagent。\nChoose either the Chinese or English TXT; each is self-contained. TheJSON is an optional exact parameter attachment.\n\n原题PDF和原始CSV已在仓库根目录；要进行统计或求解时另提供。这个便捷包没有重复装入原始CSV。\nSupply original courseCSV/PDF files separately when asking for calculations or optimisation.\n\n研究发布版本：'''+VERSION+'\nVerified repository commit: '+commit+'\nPinned release: '+published+'\n\n此同步包仅在本地生成供本人转发；本次未将它另外发布到仓库。\nThis Chat bundle is generated locally for forwarding, separately from the public research release.\n'
    (CHAT/'START_HERE.txt').write_text(instruction,encoding='utf-8')
    inventory={'release':VERSION,'commit':commit,'release_url':published,'files':[{'name':p.name,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(CHAT.iterdir()) if p.is_file() and p.suffix!='.zip' and p.name!='CHAT_MANIFEST.json']}
    (CHAT/'CHAT_MANIFEST.json').write_bytes(dump(inventory))
    zpath=CHAT/('Tier1_Research_Sync_1103_'+VERSION.split('-',1)[1].replace('.','_')+'.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(CHAT.iterdir()):
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    print(json.dumps({'chat_files':len(inventory['files']),'zip':str(zpath),'CN_chars':len(outputs[f'TIER1_RESEARCH_SYNC_1103_{label}_CN.txt']),'EN_chars':len(outputs[f'TIER1_RESEARCH_SYNC_1103_{label}_EN.txt'])},ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--chat-commit');args=parser.parse_args()
    if args.chat_commit:build_chat(args.chat_commit)
    else:build_release()
