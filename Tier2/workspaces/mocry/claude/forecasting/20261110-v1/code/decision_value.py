import sys,os,json,math,numpy as np,pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE,'backtest_ml.py')).read().split("import os\nVAL=")[0])
from scipy.optimize import linprog
from scipy.stats import kendalltau
TEST=('2024-01-01','2025-12-31'); H=7
b=json.load(open('best_p.json'))
P={}
for m,fn in [('ridge',lambda k:run('ridge','p',k,*TEST,params=b['ridge'])),('hgb',lambda k:run('hgb','p',k,*TEST))]:
    for k in range(1,H+1):
        f=f'pred_p_{k}_{m}_exp.csv'
        r=pd.read_csv(f,index_col=0,parse_dates=['tgt']) if os.path.exists(f) else fn(k)
        if not os.path.exists(f): r.to_csv(f)
        P[(m,k)]=r.set_index('tgt').f
p=d.p
# level x weekday (multiplicative), alpha=0.2 ; and pure weekday profile on 28d mean
def lvlwd(alpha):
    y=p.values; n=len(y); dow=idx.dayofweek.values; out={k:pd.Series(np.nan,index=idx) for k in range(1,H+1)}; Lv=None
    for t in range(364,n):
        w=np.array([y[t-364:t][dow[t-364:t]==j].mean() for j in range(7)])/y[t-364:t].mean()
        x=y[t]/w[dow[t]]; Lv=x if Lv is None else alpha*x+(1-alpha)*Lv
        for k in range(1,H+1):
            if t+k<n: out[k].iloc[t+k]=Lv*w[dow[t+k]]
    return out
lw=lvlwd(0.2); lw05=lvlwd(0.05)
days=pd.date_range(*TEST)
def fc(model,t,k):
    tg=t+pd.Timedelta(days=k)
    if tg>p.index[-1]: return np.nan
    if model=='perfect': return p[tg]
    if model=='pers': return p[t]
    if model=='sn7': return p[tg-pd.Timedelta(days=7)]
    if model=='lvlwd': return lw[k][tg]
    if model=='lvlwd05': return lw05[k][tg]
    return P[(model,k)].get(tg,np.nan)
E=1.0; eta=math.sqrt(0.9)   # 1 MWh usable energy; results per MWh usable
def solve(prices,s0,term):
    n=len(prices)  # vars: c(n), r(n), s(n)
    c=np.concatenate([prices,-prices,np.zeros(n)]); c[3*n-1]-=term   # minimise cost - revenue - terminal value
    Aeq=np.zeros((n,3*n)); beq=np.zeros(n)
    for i in range(n):
        Aeq[i,2*n+i]=1; Aeq[i,i]=-eta; Aeq[i,n+i]=1/eta
        if i>0: Aeq[i,2*n+i-1]=-1
        else: beq[i]=s0
    bounds=[(0,E/eta)]*n+[(0,eta*E)]*n+[(0,E)]*n
    r=linprog(c,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs')
    return r.x[0],r.x[n],r.x[2*n]
actual=p.reindex(days).values
# full perfect foresight over the whole test period
n=len(days); 
def full():
    c=np.concatenate([actual,-actual,np.zeros(n)])
    Aeq=np.zeros((n,3*n)); beq=np.zeros(n)
    for i in range(n):
        Aeq[i,2*n+i]=1; Aeq[i,i]=-eta; Aeq[i,n+i]=1/eta
        if i>0: Aeq[i,2*n+i-1]=-1
    r=linprog(c,A_eq=Aeq,b_eq=beq,bounds=[(0,E/eta)]*n+[(0,eta*E)]*n+[(0,E)]*n,method='highs'); return -r.fun
vfull=full()
res={}
for model in ['perfect','ridge','hgb','lvlwd','lvlwd05','sn7','pers']:
    s=0.0; profit=0.0; taus=[]; cyc=0.0
    for i,t in enumerate(days):
        f=[actual[i]]+[fc(model,t,k) for k in range(1,H+1)]
        f=np.array([x for x in f if x==x])
        if len(f)>2 and model!='perfect':
            a=actual[i+1:i+len(f)]; 
            if len(a)==len(f)-1 and len(a)>2 and np.std(f[1:])>0: taus.append(kendalltau(f[1:],a)[0])
        term=eta*np.mean(f)   # stored MWh valued at mean forecast price net of discharge loss
        cc,rr,s=solve(f,s,term)
        profit+=actual[i]*(rr-cc); cyc+=rr/eta
    profit+=eta*s*actual[-28:].mean()   # residual stock valued identically for all policies
    res[model]=(profit, profit/vfull, float(np.nanmean(taus)) if taus else float('nan'), cyc/2)
print('full-period perfect foresight value per MWh usable over 2 years: £%.0f (%.0f per year)'%(vfull,vfull/2))
for m,(v,sh,tau,cy) in res.items(): print(f'{m:9s} realised £{v:8.0f}  share of full-PF {sh:5.2f}  mean Kendall tau (next 7d) {tau:5.2f}  full cycles/yr {cy:5.1f}')
