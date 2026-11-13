import numpy as np,pandas as pd,math
HS=[1,2,3,7,14]
def L(ser,k,m): 
    r=pd.read_csv(f'pred_{ser}_{k}_{m}.csv',parse_dates=['tgt']).set_index('tgt'); return r
def dm(e1,e2,k):
    dl=np.abs(e1)-np.abs(e2); n=len(dl); m=dl.mean(); q=k+6
    g=[np.sum((dl[j:]-m)*(dl[:n-j]-m))/n for j in range(q+1)]
    v=(g[0]+2*sum((1-j/(q+1))*g[j] for j in range(1,q+1)))/n
    z=m/math.sqrt(v); p=math.erfc(abs(z)/math.sqrt(2)); return z,p
print('--- series scale in test (2024-25)')
for ser in ['p','D','G','ren','oth','S']:
    r=L(ser,1,'pers'); print(ser,'mean %.1f sd %.1f'%(r.y.mean(),r.y.std()))
print('--- derived targets, MAE')
for k in HS:
    g,dd,s=L('G',k,'ridge_exp'),L('D',k,'ridge_exp'),L('S',k,'ridge_exp')
    j=g.join(dd,lsuffix='_g',rsuffix='_d').join(s)
    ren,oth=L('ren',k,'ridge_exp'),L('oth',k,'ridge_exp'); j2=g.join(ren,lsuffix='_g',rsuffix='_r').join(oth)
    print(k,'S direct %.2f | S=G-D %.2f || G direct %.2f | G=ren+oth %.2f'%((j.y-j.f).abs().mean(),(j.y-(j.f_g-j.f_d)).abs().mean(),(j2.y_g-j2.f_g).abs().mean(),(j2.y_g-(j2.f_r+j2.f)).abs().mean()))
print('--- surplus event S>0, test 2024-25')
for k in HS:
    s=L('S',k,'ridge_exp'); p_=L('S',k,'pers'); j=s.join(p_,rsuffix='_p').dropna()
    y=(j.y>0).values; base=y.mean()
    # probability via Gaussian with sd from first-year residuals rolling: use trailing 365d residual sd (causal, lagged by k)
    res=(j.y-j.f); sd=res.shift(k).rolling(365,min_periods=120).std()
    ok=sd.notna().values
    from math import erf
    pr=np.array([0.5*(1+erf(f/(s_*math.sqrt(2)))) if s_==s_ else np.nan for f,s_ in zip(j.f.values,sd.values)])
    def stats(pred):
        tp=(pred&y).sum(); return tp/max(pred.sum(),1), tp/max(y.sum(),1)
    pm,rm=stats((j.f>0).values); pp,rp=stats((j.f_p>0).values)
    brier=np.mean((pr[ok]-y[ok])**2); bref=np.mean((y[ok].mean()-y[ok])**2)
    bpers=np.mean(((j.f_p>0).values[ok].astype(float)-y[ok])**2)
    print(k,'base %.3f | model precision %.2f recall %.2f | persistence precision %.2f recall %.2f | Brier model %.3f clim %.3f pers %.3f  BSS %.2f'%(base,pm,rm,pp,rp,brier,bref,bpers,1-brier/bref))
print('--- 80% interval coverage using trailing-365d absolute-residual quantile (split-conformal style), ens3')
for ser in ['p','D','G','ren','S']:
    out=[]
    for k in (1,3,7):
        r=L(ser,k,'ens3' ); a=(r.y-r.f).abs(); q=a.shift(k).rolling(365,min_periods=120).quantile(0.8)
        ok=q.notna(); out.append((k,round(float((a[ok]<=q[ok]).mean()),3),round(float(q[ok].mean()),1)))
    print(ser,out)
print('--- DM tests (abs loss), negative z => first is better')
tests=[('p',1,'hgb_exp','pers'),('p',1,'hgb_exp','ridge_exp'),('p',7,'hgb_exp','ma28'),('p',14,'hgb_exp','ma28'),('p',7,'ridge_exp','ma28'),
       ('D',1,'ens3','ridge_exp'),('D',7,'ens3','sn7'),('ren',1,'ridge_exp','pers'),('ren',3,'ridge_exp','ma28'),('ren',7,'ridge_exp','ma28'),('ren',14,'ridge_exp','ma28'),
       ('S',1,'ridge_exp','pers'),('S',3,'ridge_exp','ma28'),('S',7,'ridge_exp','ma28'),('S',14,'ridge_exp','ma28'),('G',7,'ridge_exp','hgb_exp')]
for ser,k,a,b in tests:
    ra,rb=L(ser,k,a),L(ser,k,b); j=ra.join(rb,lsuffix='_a',rsuffix='_b').dropna()
    z,p=dm((j.y_a-j.f_a).values,(j.y_b-j.f_b).values,k)
    print(ser,k,a,'vs',b,'MAE %.2f vs %.2f  z=%.2f p=%.3f'%((j.y_a-j.f_a).abs().mean(),(j.y_b-j.f_b).abs().mean(),z,p))
print('--- by test year (MAE h=1,7): ')
for ser,ms in [('p',['pers','ma28','ridge_exp','hgb_exp']),('D',['sn7','ridge_exp','ens3']),('ren',['pers','ma28','ridge_exp']),('S',['pers','ma28','ridge_exp'])]:
    for k in (1,7):
        o={}
        for m in ms:
            r=L(ser,k,m); o[m]={y:round(float((g.y-g.f).abs().mean()),1) for y,g in r.groupby(r.index.year)}
        print(ser,k,o)
