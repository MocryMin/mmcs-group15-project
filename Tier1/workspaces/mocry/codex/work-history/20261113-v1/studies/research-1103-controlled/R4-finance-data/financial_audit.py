"""Reproduce base-year FX/CPI and cost-unit checks; source workbooks stay read-only."""
import csv
import io
import json
import math
import re
from pathlib import Path
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
CAP = HERE.parent / 'control/browser_captures'

fx = json.loads((CAP/'R4/ECB-2020-CSV.json').read_text(encoding='utf-8'))
fx_text = fx.get('body', fx.get('text', ''))
fx_rows = list(csv.DictReader(io.StringIO(fx_text.replace('\r\r\n','\n'))))
fx_row = next(r for r in fx_rows if r['TIME_PERIOD']=='2020')
assert fx_row['CURRENCY']=='GBP' and fx_row['CURRENCY_DENOM']=='EUR'
q = float(fx_row['OBS_VALUE'])

cpi = {}
with (CAP/'R4/ONS-CPI-CSV.csv').open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.reader(stream):
        if len(row)>1 and (re.fullmatch(r'\d{4}',row[0]) or re.fullmatch(r'\d{4} [A-Z]{3}',row[0])):
            try: cpi[row[0]]=float(row[1])
            except ValueError: pass
assert cpi['2020']==108.7
monthnames=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
rawpath=HERE.parents[3]/'materials/sync-20261030/daily_market_index_price.csv'
normalised=[]
with rawpath.open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.DictReader(stream):
        ym=row['date'][:4]+' '+monthnames[int(row['date'][5:7])-1]
        index=cpi[ym]
        nominal=float(row['avg_price_£_per_MWh'])
        normalised.append({'date':row['date'],'nominal_GBP_per_MWh':nominal,'CPI_month':ym,'CPI':index,
                           'real_2020_GBP_per_MWh':nominal*cpi['2020']/index})
with (HERE/'prices_gbp2020.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(normalised[0]));writer.writeheader();writer.writerows(normalised)

bf=load_workbook(CAP/'R2/DEA-DATASHEET.xlsx',data_only=False,read_only=True)
bv=load_workbook(CAP/'R2/DEA-DATASHEET.xlsx',data_only=True,read_only=True)
s=bf['180 Lithium Ion Battery'];v=bv[s.title]
E=float(v['D8'].value);P=float(v['D9'].value)
components={k:float(v[k].value) for k in ['D25','D26','D27']}
c_eur=(components['D25']+components['D27']+components['D26']*P/E)*1e6
assert abs(c_eur-float(v['D24'].value)*1e6)<1e-7
fom_table=float(v['D28'].value)*1000
fom_capex=.029*c_eur*E/P
assert abs(fom_capex/fom_table-2)<1e-10

h=load_workbook(CAP/'R3/H2-ANNEX.xlsx',data_only=True,read_only=True)['Technical and cost assumptions']
eta_hhv=39.37/55.9
capex_h={name:float(h[cell].value)*eta_hhv for name,cell in [('low','K14'),('central','K15'),('high','K16')]}
fx2024={}
for currency in ['GBP','USD']:
    capture=json.loads((CAP/f'R4/ECB-2024-{currency}.json').read_text(encoding='utf-8'))
    row=next(csv.DictReader(io.StringIO(capture['text'])))
    assert row['TIME_PERIOD']=='2024' and row['CURRENCY']==currency and row['CURRENCY_DENOM']=='EUR'
    fx2024[currency]=float(row['OBS_VALUE'])
gbp_per_usd2024=fx2024['GBP']/fx2024['USD']
iea_conversion=gbp_per_usd2024*cpi['2020']/cpi['2024']
iea_raw={'low':2000,'analyst_midpoint':2300,'high':2600}
result={
 'price_basis_recommendation':'Use constant2020 GBP for the source-reference comparison; current-technology/historical-condition counterfactual, not a nominal2026 supplier quote',
 'GBP_per_EUR_2020':q,'fx_key':'EXR.A.GBP.EUR.SP00.A',
 'CPI_2020_annual':cpi['2020'],'CPI_2012_annual':cpi.get('2012'),'CPI_2026_Sep':cpi.get('2026 SEP'),
 'deflation_formula':'p_real2020(day)=p_nominal(day)*CPI_annual2020/CPI_month(day)',
 'normalised_price_rows':len(normalised),'all_price_months_have_CPI':True,
 'battery':{'reference_energy_MWh':E,'reference_power_MW':P,'CAPEX_EUR2020_per_MWh':c_eur,
   'CAPEX_GBP2020_per_MWh':c_eur*q,'CAPEX_GBP2020_per_MW_at2h':c_eur*q*E/P,
   'FOM_table_EUR2020_per_MWyr':fom_table,'FOM_2point9percent_CAPEX_EUR2020_per_MWyr':fom_capex,
   'FOM_table_GBP2020_per_MWyr':fom_table*q,'FOM_capexcase_GBP2020_per_MWyr':fom_capex*q,
   'FOM_ratio':fom_capex/fom_table,'source_formula_D24':s['D24'].value,'source_formula_D28':s['D28'].value,
   'review':'Unit conflict retained as two cases; do not rewrite source or double count maintenance/replacement included by footnoteO'},
 'hydrogen':{'HHV_kWh_kg':39.37,'electricity_kWh_kg':55.9,'hybrid_HHV_output_to_electric_input_ratio':eta_hhv,
   'proxy_CAPEX_GBP2020_per_kWe':capex_h,'proxy_FOM_GBP2020_per_kWe_yr':float(h['K22'].value)*eta_hhv,
   'variable_reserve_GBP2020_per_kg':float(h['K25'].value)*39.37,
   'scope':'Old reference output-capacity costs adapted to ITM BOL consumption; hybrid modelling proxy, not modern ITM quotation. Do not combine reserve with explicit replacement.'},
 'supported_H2_reference':{'GBP2012_per_MWh_HHV':175,'brief_HHV_kWh_per_kg':39.4,'GBP2012_per_kg':175*39.4/1000,
   'GBP2020_per_kg':(175*39.4/1000)*cpi['2020']/cpi['2012'] if cpi.get('2012') else None,
   'scope':'Supported strike-value reference only; not a commercial sale or eligibility guarantee'},
 'modern_H2_CAPEX_reporting_scenario':{
   'source':'IEA Global Hydrogen Review2025 executive summary; manufacture and install outside China in2024',
   'raw_USD_per_kW':iea_raw,'GBP_per_EUR_2024':fx2024['GBP'],'USD_per_EUR_2024':fx2024['USD'],
   'GBP_per_USD_cross_of_annual_reference_rates_2024':gbp_per_usd2024,'CPI_2024_annual':cpi['2024'],
   'GBP2020_per_assumed_USD2024':iea_conversion,
   'CAPEX_GBP2020_per_kW_assumed_electrical':{k:v*iea_conversion for k,v in iea_raw.items()},
   'price_base_assumption':'Treat the2024 observed USD costs as nominalUSD2024 for this reporting scenario; constant-dollar base not explicitly given in IEA summary',
   'denominator_assumption':'Electrical capacity inferred from electrolyser context; summary does not label kWe or AC/DC',
   'FX_scope':'Ratio of annual EUR-base reference rates; not independently computed annual average of dailyGBP/USD nor executable quotation',
   'cost_scope':'Modern generic non-China installed reference, not ITM/UK site quotation; EPC+contingency already included',
   'replacement_rule':'Do not multiply this installed cost by old BEIS60% stack share; use separately labelled absolute old-cost proxy or separate reserve scenario'
 },
 'discount':{'empirically_verified_private_rate':None,'analyst_sensitivity_real_rates':[0,.03,.05,.08,.12],
   'scope':'No private investor hurdle inferred from public STPR; no risk-free point estimate invented after BoE403',
   'CRF_formula':'r*(1+r)^L/((1+r)^L-1), limit1/L at r=0; apply only with common cost/horizon convention'},
 'cautions':['CPI is a general purchasing-power deflator, not a battery equipment cost forecast',
             '2020 annual FX is a reporting conversion, not future transaction FX guarantee',
             'Use contemporaneously available information for causal actions; ex-post deflation is a reporting adjustment',
             'Do not treat 2012-supported H2 reference as merchant netback or combine mixed price bases']
}
(HERE/'financial_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'q2020':q,'CPI2020':cpi['2020'],'price_rows':len(normalised),'battery':result['battery'],
                 'H2':result['hydrogen'],'supported_reference':result['supported_H2_reference']},ensure_ascii=True))
