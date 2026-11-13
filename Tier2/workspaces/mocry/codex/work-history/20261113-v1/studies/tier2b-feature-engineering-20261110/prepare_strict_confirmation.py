"""Freeze six already selected candidates before a stricter input-scaler check."""
from pathlib import Path
import json,shutil,hashlib
import pandas as pd,numpy as np
from features import ROOT,load

dst=ROOT/'strict-confirmation'
for n in ['inputs','features','results','logs','models','predictions','step_logs','case_results']:(dst/n).mkdir(parents=True,exist_ok=True)
for p in (ROOT/'inputs').glob('*'):
    if p.is_file():shutil.copy2(p,dst/'inputs'/p.name)
for p in (ROOT/'features').glob('*'):
    if p.is_file():shutil.copy2(p,dst/'features'/p.name)
for name in ['fit.py','model.py']:shutil.copy2(ROOT/name,dst/name)
text=(ROOT/'features.py').read_text();needle="(f.index<='2024-12-31')";assert text.count(needle)==1
(dst/'features.py').write_text(text.replace(needle,"(f.index<='2024-12-30')"),encoding='utf-8')
cfg=json.loads((ROOT/'BASELINE_FROZEN.json').read_text());cfg['scaler']='Target scale remains2022-2024 labels; extra input statistics use2022-01-01 through2024-12-30 only, excluding the first validation origin.'
(dst/'BASELINE_FROZEN.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selections=pd.read_csv(ROOT/'results/VALIDATION_SELECTION.csv');plan=selections.loc[selections.selection_scope.eq('neural')&~selections.pool.eq('baseline'),['target','family','budget','groups','pool']].to_dict('records');assert len(plan)==6
(dst/'PLAN_FROZEN.json').write_text(json.dumps({'reason':'Verify final claims after excluding the boundary input token from extra-feature normalization; configurations frozen from original validation selection, no new features or model search.','original_input_fit':'2022-01-01 through2024-12-31; all input values known by end-of-training, but boundary row is also first validation origin.','strict_input_fit':'2022-01-01 through2024-12-30; only training-origin rows used.','target_scale_unchanged':True,'baseline_inputs_identical':True,'original_selection_sha256':hashlib.sha256((ROOT/'results/VALIDATION_SELECTION.csv').read_bytes()).hexdigest(),'plan':plan},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Frozen strict confirmation for6 candidates x3seeds.')
