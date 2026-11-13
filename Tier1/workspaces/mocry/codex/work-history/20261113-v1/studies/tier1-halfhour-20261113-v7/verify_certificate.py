"""Check saved master duals and per-battery Lagrangian lower bounds."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent

def check(policy):
    meta=json.loads((ROOT/'results'/f'certificate_{policy}.json').read_text())
    z=np.load(ROOT/'results'/f'certificate_{policy}_certificate.npz')
    s=pd.read_csv(ROOT/'results'/f'certificate_{policy}_schedule.csv.gz')
    cfg=json.loads((ROOT/'configuration.json').read_text());T=len(s);Y=meta['years'];du=z['master_row_dual']
    gen,sale,hbal,limit=du[:T],du[T:2*T],du[2*T:3*T],du[3*T:4*T]
    capdual=du[4*T:];days,codes=np.unique(s.date,return_inverse=True)
    h=min(meta['active_products']['electrolysers'],key=lambda h:h['kWh_kg'])
    rq=-s.price.to_numpy()/(1000*Y)-gen-sale
    rh=-(cfg['netback']-h['variable_GBP_kg'])/(h['kWh_kg']*Y)-gen-hbal-limit-capdual[codes]/h['kWh_kg']
    rn=h['annual']+h['unit_GWh']*limit.sum()
    errors={'master_h_reduced_cost_negative':float(max(0,-rh.min())),
            'master_capacity_reduced_cost_negative':float(max(0,-rn)),
            'master_row_sign':float(max(0,gen.max(),sale.max(),limit.max(),capdual.max(),-hbal.min()))}
    if policy=='A':errors['master_sales_reduced_cost_negative']=float(max(0,-rq.min()))
    dualobj=np.dot(gen,s.g)+np.dot(sale,s.d)+capdual.sum()*meta['cap_kg_day']/1e6
    if policy=='B':dualobj+=np.dot(rq,np.minimum(s.g,s.d))
    dualupper=-dualobj-meta['annual_reference_mGBP']
    errors['master_primal_dual_GBP']=float(abs(dualupper-meta['annual_increment_mGBP'])*1e6)
    batteries=[]
    for j,b in enumerate(meta['active_products']['batteries']):
        eta=b['eta'];W=b['usable'];P=.5*b['P_MW']/1000
        ch,rs,hy,stock=(z[f'b{j}_{key}'] for key in ('charge','sale','hydrogen','stock'))
        prior=np.r_[0,stock[:-1]]
        residual=stock-b['retention']*prior-eta*ch+(rs+hy)/eta
        error=max(abs(residual).max(),max(0,stock.max()-W,ch.max()-P,(rs+hy).max()-P),abs(stock[-1]))
        pi=z[f'b{j}_row_dual'];cc=z['charge_opportunity']*1000*Y;dv=np.maximum(z['sale_value'],z['hydrogen_value'])*1000*Y
        rc=cc+eta*pi[:T];rd=-dv-pi[:T]/eta;rz=-pi[:T].copy()
        rz[:-1]+=b['retention']*pi[1:T];rz[-1]-=pi[-1]
        cbound=np.full(T,P*1000)
        if policy=='B':
            cbound=np.where(s.g>s.d,cbound,0)
            assert np.max(ch[np.asarray(s.g<=s.d)])<1e-8
            assert np.max(rs[np.asarray(s.d<=s.g)])<1e-8
        lower=(np.dot(cbound,np.minimum(rc,0))+P*1000*np.minimum(rd,0).sum()+W*1000*np.minimum(rz,0).sum())/(1e6*Y)+b['annual']
        assert abs(lower-meta['pricing_audit'][j]['reduced_cost_lower'])<1e-10
        assert lower>0 and error<1e-8
        batteries.append({'id':b['id'],'reduced_cost_lower_GBP':float(lower*1e6),'max_trajectory_error_GWh':float(error)})
    assert errors['master_primal_dual_GBP']<1
    assert max(v for k,v in errors.items() if not k.endswith('_GBP'))<1e-8
    result={'policy':policy,'passed':True,'master_errors':errors,'battery_dual_lower_bounds':batteries,
            'upper_increment_mGBP_from_duals':float(dualupper)}
    (ROOT/'results'/f'certificate_{policy}_independent_audit.json').write_text(json.dumps(result,indent=2))
    print('CERTIFICATE',policy,'PASS',errors)
    return result
if __name__=='__main__':
    for policy in ('A','B'):check(policy)
