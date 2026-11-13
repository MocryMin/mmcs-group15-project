from pathlib import Path
import datetime,hashlib,json,re,sys
from build_release import HERE,REPO,run_child
sys.stdout.reconfigure(encoding='utf-8')
V='20261103-v1.1';PUBLIC=f'Tier1/public/research_1103/controller/mocry-codex/{V}';STAGE=HERE/'staging-v1.1'
def cmd(*args):
 r=run_child(args,cwd=REPO,text=True,encoding='utf-8',capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr or r.stdout)
 return r.stdout.strip()
def helper(*args):return cmd(sys.executable,'tools/collab.py',*args)
assert not cmd('git','status','--porcelain')
assert cmd('git','rev-parse','HEAD')=='c52abb0fa126e928bae6c81693dddfc3de572072'
records=[]
for p in sorted(STAGE.rglob('*')):
 if p.is_file():
  rel=p.relative_to(STAGE).as_posix()
  records.append(json.loads(helper('publish','--tier','Tier1','--area','Tier1','--path',PUBLIC.split('/public/',1)[1]+'/'+rel,'--source',str(p),'--summary',f'Publish corrected research snapshot {V}: {rel}')))
# Verify repository bytes BEFORE making any commit or remote push.
manifest=json.loads((REPO/PUBLIC/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
for item in manifest['files']:
 assert hashlib.sha256((REPO/PUBLIC/item['path']).read_bytes()).hexdigest()==item['published_sha256'],item['path']
candidate=json.loads((REPO/PUBLIC/'BASELINE_CANDIDATE.json').read_text(encoding='utf-8'))
previous=json.loads((REPO/PUBLIC.replace('v1.1','v1')/'BASELINE_CANDIDATE.json').read_text(encoding='utf-8'))
for k in ['policy','data','market','battery','hydrogen','finance']:assert candidate[k]==previous[k],k
draft=HERE/'navigation'
ip=REPO/'Tier1/public/baseline_1103/INDEX.md';text=ip.read_text(encoding='utf-8')
text=text.replace('20261103-v1 controller research release','20261103-v1.1 controller research release').replace('/20261103-v1/','/20261103-v1.1/')
text=text.replace('The release is a reviewed proposal,', 'The v1.1 snapshot corrects four line-ending-dependent manifest hashes in v1; findings and numerical recommendations are unchanged. The original v1 remains preserved. The release is a reviewed proposal,')
(draft/'INDEX_CORRECTED.md').write_text(text,encoding='utf-8')
records.append(json.loads(helper('publish','--tier','Tier1','--area','Tier1','--path','baseline_1103/INDEX.md','--source',str(draft/'INDEX_CORRECTED.md'),'--summary','Point to v1.1 Git-byte-verified snapshot; preserve v1 and explain hash-only correction')))
mh=hashlib.sha256((STAGE/'RELEASE_MANIFEST.json').read_bytes()).hexdigest()
body=f'''# Correction and verified research release {V}

The complete reviewed research package is at `{PUBLIC}/README.md`. Recommended parameters: `{PUBLIC}/BASELINE_CANDIDATE.json`. The earlier v1 snapshot and broadcast remain unchanged in history.

Post-push verification found four v1 Markdown manifest hashes had been calculated before Git converted CRLF to LF. The actual research text and all numerical recommendations were unchanged. This v1.1 snapshot computes every listed release hash from exact Git-clean bytes and verifies it against the written repository files before committing. No research finding or investment result changed. Source-local and public-copy hashes remain distinct.

Manifest SHA256: `{mh}`. Start with the Chinese synthesis or English synopsis, then the four reports, source/parameter catalogues,20 controller dispositions, first-pass snapshots and cross-reviews. All substantive discussion and independent research remain welcome. This is a controller-reviewed proposal, not group adoption; actual H2contracts/eligibility and other declared scenario conditions remain open. No acknowledgement is required solely for receipt.

Use v1.1 for further references. The ordinary-Chat handoff is being generated from this corrected snapshot with the final verified commit pinned. This correction was published under Ran Min's explicit request to share the research and maintain version control.
'''
(HERE/'CORRECTION_BROADCAST.md').write_text(body,encoding='utf-8')
msgpath=helper('message','--tier','Tier1','--area','Tier1','--broadcast','--body-file',str(HERE/'CORRECTION_BROADCAST.md'),'--kind','correction','--priority','info','--reply-to','f5bee2e6ae1c4cee93a6ba845d0b07cc')
meta=json.loads((REPO/msgpath).read_text(encoding='utf-8').split('<!-- MESSAGE ',1)[1].split(' -->',1)[0])
sp=REPO/'Tier1/workspaces/mocry/coordination_state.json';s=json.loads(sp.read_text(encoding='utf-8'))
s['seen_message_ids'].append(meta['id']);s['handoff']=f'Use corrected release {V} at {PUBLIC}/README.md. Original v1 preserved; hash-only lineending correction. Research conclusions unchanged.'
s['last_publication']={'release':V,'path':PUBLIC,'manifest_sha256':mh,'broadcast_id':meta['id'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
sp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=[r['path'] for r in records]+[r['archive'] for r in records if r.get('archive')]+['Tier1/public/logs/mocry-codex.jsonl',msgpath,'Tier1/agent_message/logs/mocry-codex.jsonl','Tier1/workspaces/mocry/coordination_state.json']
cmd('git','add','--',*paths);helper('commit','--tier','Tier1','--message','Publish Tier1 research v1.1 with exact Git-byte hashes and correction broadcast')
research_commit=cmd('git','rev-parse','HEAD')
rp=REPO/'Tier1/public/README.md';t=rp.read_text(encoding='utf-8').replace('20261103-v1 release','20261103-v1.1 release').replace('/20261103-v1/','/20261103-v1.1/')
t+='\nThe original v1 is preserved. Version v1.1 corrects four Markdown manifest hashes after Git line-ending conversion; research text and numerical recommendations are unchanged.\n'
(draft/'PUBLIC_README_CORRECTED.md').write_text(t,encoding='utf-8')
nav=json.loads(helper('publish','--tier','control','--area','Tier1','--path','README.md','--source',str(draft/'PUBLIC_README_CORRECTED.md'),'--summary','Select Git-byte-verified research v1.1 and disclose hash-only correction'))
cmd('git','add','--',nav['path'],nav['archive'],'Tier1/public/logs/mocry-codex.jsonl');helper('commit','--tier','control','--message','Point Tier1 public guide to corrected research v1.1')
receipt={'release_id':V,'supersedes':'20261103-v1','research_commit':research_commit,'final_commit':cmd('git','rev-parse','HEAD'),'public_path':PUBLIC,'manifest_sha256':mh,'broadcast_path':msgpath,'broadcast_id':meta['id'],'archives':[r['archive'] for r in records if r.get('archive')]+[nav['archive']],'public_operations':len(records)+1,'published_to_remote':False,'status':'committed_local_pending_push','hashes_verified_in_repository':len(manifest['files']),'numeric_sections_identical_to_v1':6}
(HERE/'PUBLICATION_RECEIPT_V1_1.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
