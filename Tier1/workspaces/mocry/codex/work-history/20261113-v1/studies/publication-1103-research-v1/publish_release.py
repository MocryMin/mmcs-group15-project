"""Publish the prepared release with repository-native logs, archives and commits."""
from pathlib import Path
import datetime, hashlib, json, sys
from build_release import HERE, REPO, STAGE, PUBLIC, VERSION, BASE, run_child
sys.stdout.reconfigure(encoding='utf-8')
def cmd(*args):
    r=run_child(args,cwd=REPO,text=True,encoding='utf-8',capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()
def helper(*args):return cmd(sys.executable,'tools/collab.py',*args)
assert not cmd('git','status','--porcelain'), 'Preserve unrelated work before publishing'
assert cmd('git','rev-parse','HEAD')==BASE, 'Reconcile new base before publication'
helper('setup','--agent','mocry-codex')
records=[]
for p in sorted(STAGE.rglob('*')):
    if p.is_file():
        rel=p.relative_to(STAGE).as_posix()
        result=helper('publish','--tier','Tier1','--area','Tier1','--path',PUBLIC.split('/public/',1)[1]+'/'+rel,'--source',str(p),'--summary',f'Publish reviewed research {VERSION}: {rel}')
        records.append(json.loads(result))

# Navigation changes use exact preimages and the public helper, never direct edits.
draft=HERE/'navigation';draft.mkdir(exist_ok=True)
index_path=REPO/'Tier1/public/baseline_1103/INDEX.md'
index=index_path.read_text(encoding='utf-8')
old='Status: a proposed group baseline and research agenda, assembled from Ran Min\'s decisions and explicitly labelled operational defaults. Publication invites discussion; it does not claim that every member has agreed or that research/optimisation is complete.'
new='Status: a proposed group baseline, assembled from Ran Min\'s decisions and explicitly labelled operational defaults. One controller-led research round and review are now complete; group adoption and a final investment optimisation are not implied by publication.'
assert old in index
index=index.replace(old,new)
insert=f'''## Reviewed research now available

The [20261103-v1 controller research release](../research_1103/controller/mocry-codex/{VERSION}/README.md) contains four topic reports, saved first passes, source/parameter catalogues, three cross-reviews, the modern-electrolyser-cost follow-up,20 controller dispositions and the [recommended parameter family](../research_1103/controller/mocry-codex/{VERSION}/BASELINE_CANDIDATE.json). Open-ended searching for this controlled round is closed. Other members' independent contributions and challenges remain welcome.

The release is a reviewed proposal, not a silent revision of [BASELINE_1103.md](BASELINE_1103.md). Actual hydrogen contracts/eligibility, private discounting and identified source conflicts remain explicitly labelled scenarios. The original research request below remains as the historical agenda.

'''
index=index.replace('## Read in this order\n',insert+'## Read in this order\n',1)
(draft/'INDEX.md').write_text(index,encoding='utf-8')
records.append(json.loads(helper('publish','--tier','Tier1','--area','Tier1','--path','baseline_1103/INDEX.md','--source',str(draft/'INDEX.md'),'--summary','Link reviewed research v1; retain baseline proposal and original research agenda')))

manifest_hash=hashlib.sha256((STAGE/'RELEASE_MANIFEST.json').read_bytes()).hexdigest()
message=f'''# Reviewed Tier1 research release {VERSION}

Ran Min authorised publication of the completed controller-led research, review decisions and recommended parameter family. The release is now available at `{PUBLIC}/README.md`.

Start with `RESEARCH_SYNTHESIS.md` (Chinese) or `EXECUTIVE_SUMMARY_EN.md`, then `BASELINE_CANDIDATE.json`. The four topic folders contain market, battery, electrolyser/H2 and data/finance reports, source locators and parameter tables. Saved first passes, three cross-reviews and the targeted IEA follow-up preserve how the conclusions developed. `control/REVIEW_DECISIONS.json` records20 dispositions.

Key changes: retain the DEA battery maintenance factor-of-two conflict as two scenarios; use the sourced modern IEA outside-China installed electrolyser cost range with explicit units/price-base assumptions; do not double-charge EPC/maintenance/stack replacement or hydrogen support; retain negative prices and chronological storage boundaries. Actual H2offtake/netback/eligibility and private hurdle rates remain scenario conditions.

This completes one real research round requested in the earlier broadcast: one GPT6Astra market worker, two GPT6.1Sol equipment workers and the controller. No DS/Clever User result is claimed. A shared anonymous source broker was used during a browser conflict; independent analysis is not presented as independently repeated retrieval. The controller closed open-ended searching after reviewing results and one modern-cost follow-up. No new investment optimum is asserted.

Release ID: `{VERSION}`. Manifest SHA256: `{manifest_hash}`. Original local hashes and path-normalised public-copy hashes are distinguished. The version directory should remain a snapshot; publish corrections as v2 or a separately recorded correction. Existing navigation preimages were archived and logged. Baseline1103 assumption text, root originals, Tier2 and other members' workspaces were not changed.

All members/agents may add independent research or challenge teacher interpretations, gap definitions, assumptions, units or parameters. Reference this version, a C/BL/gap/parameter ID, source evidence and the model consequence. Independent additions are welcome; the closure of this round does not close participation. A publication is not group consensus. Acknowledgement is not required solely to mark receipt, and nobody is assumed to have read this broadcast before their next sync.

A separate self-contained Chinese/English Chat handoff bundle is being generated locally for Ran Min to forward to teammates who do not use coding agents. No Git or registration is required to contribute through those files.
'''
(HERE/'PUBLICATION_BROADCAST.md').write_text(message,encoding='utf-8')
msgpath=helper('message','--tier','Tier1','--area','Tier1','--broadcast','--body-file',str(HERE/'PUBLICATION_BROADCAST.md'),'--kind','status','--priority','info','--reply-to','9a14b411d65745efa6caec11dd8a8d69')
msgmeta=json.loads((REPO/msgpath).read_text(encoding='utf-8').split('<!-- MESSAGE ',1)[1].split(' -->',1)[0])

statep=REPO/'Tier1/workspaces/mocry/coordination_state.json'
state=json.loads(statep.read_text(encoding='utf-8'))
seen=list(state.get('seen_message_ids',[]))
for p in sorted((REPO/'Tier1/agent_message/messages').glob('*.md')):
    meta=json.loads(p.read_text(encoding='utf-8').split('<!-- MESSAGE ',1)[1].split(' -->',1)[0])
    if meta['id'] not in seen:seen.append(meta['id'])
state.update(seen_message_ids=seen,tasks=[],handoff=f'Reviewed research {VERSION} published as a proposal; open-ended searching closed. Start at {PUBLIC}/README.md. Do not infer group adoption or fresh optimum.',last_publication={'release':VERSION,'path':PUBLIC,'manifest_sha256':manifest_hash,'broadcast_id':msgmeta['id'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
statep.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=[r['path'] for r in records]+[r['archive'] for r in records if r.get('archive')]+['Tier1/public/logs/mocry-codex.jsonl',msgpath,'Tier1/agent_message/logs/mocry-codex.jsonl','Tier1/workspaces/mocry/coordination_state.json']
cmd('git','add','--',*paths)
out=helper('commit','--tier','Tier1','--message',f'Publish Tier1 reviewed research {VERSION}, parameter family and broadcast')
research_commit=cmd('git','rev-parse','HEAD')

# README is maintainer-controlled; publish it in a separate control commit.
rp=REPO/'Tier1/public/README.md';text=rp.read_text(encoding='utf-8')
newsection=f'''## Reviewed research release

The [20261103-v1 release](research_1103/controller/mocry-codex/{VERSION}/README.md) publishes the completed four-topic research, independent first passes, cross-reviews, controller dispositions and [recommended parameter family](research_1103/controller/mocry-codex/{VERSION}/BASELINE_CANDIDATE.json). The controller has closed this research round; substantive independent contributions remain welcome. It is a reviewed proposal, not group consensus or a replacement of Baseline1103 by implication.

'''
assert '## Reviewed research release' not in text
text=text.replace('## Suggested locations\n',newsection+'## Suggested locations\n',1) if '## Suggested locations\n' in text else text+'\n'+newsection
(draft/'PUBLIC_README.md').write_text(text,encoding='utf-8')
nav=json.loads(helper('publish','--tier','control','--area','Tier1','--path','README.md','--source',str(draft/'PUBLIC_README.md'),'--summary','Point Tier1 public navigation to reviewed research v1 while retaining prior guide'))
cmd('git','add','--',nav['path'],nav['archive'],'Tier1/public/logs/mocry-codex.jsonl')
helper('commit','--tier','control','--message','Link the reviewed Tier1 research release from public navigation')
finalcommit=cmd('git','rev-parse','HEAD')
receipt={'release_id':VERSION,'research_commit':research_commit,'final_commit':finalcommit,'public_path':PUBLIC,'manifest_sha256':manifest_hash,'broadcast_path':msgpath,'broadcast_id':msgmeta['id'],'archives':[r['archive'] for r in records if r.get('archive')]+[nav['archive']],'public_operations':len(records)+1,'published_to_remote':False,'status':'committed_local_pending_push'}
(HERE/'PUBLICATION_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
