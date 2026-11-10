import glob,os,numpy as np,pandas as pd
pd.set_option('display.width',250)
st=pd.read_csv('struct_results.csv')
allr={}
for ser in ['p','D','G','ren','oth','S']:
    rows={}
    for f in sorted(glob.glob(f'pred_{ser}_*_*.csv')):
        b=os.path.basename(f)[5+len(ser)+1:-4]; k,m=b.split('_',1)
        r=pd.read_csv(f); rows.setdefault(m,{})[int(k)]=(r.y-r.f).abs().mean()
    t=pd.DataFrame(rows).T.sort_index(axis=1)
    for m in ['lvlwd','calar_exp']:
        t.loc[m]=st[st.ser==ser].set_index('k')[m]
    order=['pers','sn7','ma28','clim','lvlwd','calar_exp','ridge_fixed2022','ridge_roll730','ridge_exp','lasso_roll730','hgb_exp','ens3']
    t=t.loc[[o for o in order if o in t.index]]
    allr[ser]=t
    print('=====',ser,'MAE (test 2024-25)');print(t.round(2).to_string())
    print('rMAE vs sn7');print((t/t.loc['sn7']).round(2).to_string())
    print('best per horizon:',{k:(t[k].idxmin(),round(t[k].min(),2)) for k in t.columns})
pd.concat(allr).to_csv('table_mae.csv')
