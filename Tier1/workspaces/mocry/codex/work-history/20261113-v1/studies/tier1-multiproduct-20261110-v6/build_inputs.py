"""Freeze product inputs and keep comparable and research-cost cases separate."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'tier1-strengthened-20261110-v5'
RESEARCH = ROOT.parent / 'equipment-research-20261110-v3.1'
TESLA = ROOT.parent / 'tesla-lazard-economics-20261110'

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def build():
    for name in ('inputs', 'research', 'results'):
        (ROOT/name).mkdir(exist_ok=True)
    for source in (BASE/'inputs').iterdir():
        if source.is_file(): shutil.copy2(source, ROOT/'inputs'/source.name)
    for source, name in [(RESEARCH/'STUDY_INPUTS.json','equipment_study_inputs.json'),
                         (TESLA/'ECONOMIC_INPUTS.json','tesla_economic_inputs.json'),
                         (TESLA/'ELIGIBILITY_ASSESSMENT.json','eligibility.json'),
                         (BASE/'configuration.json','v5_configuration.json')]:
        shutil.copy2(source, ROOT/'research'/name)
    for name in ('legacy_model.py',):
        shutil.copy2(BASE/name, ROOT/name)
    p = json.loads((ROOT/'inputs/parameters.json').read_text(encoding='utf-8'))
    profiles = json.loads((RESEARCH/'STUDY_INPUTS.json').read_text(encoding='utf-8'))['profiles']
    eur = p['battery_cost_MWh']/288000
    usd2024 = p['hydrogen_cost_MW']/2300000
    batteries, electrolysers = [], []
    for v in profiles:
        e = v['electrical']
        if v['kind']=='battery':
            K = v['costs']['installed_reference']*eur
            batteries.append(dict(id=v['id'], E_MWh=e['nominal_energy_kWh']/1000,
                P_MW=e['discharge_AC_kW']/1000, rte=e['roundtrip_AC'], life=15,
                capital_GBP=K, fom_GBP=K*.029,
                fom_literal_GBP=v['costs']['fixed_OM_cases_per_year']['literal_per_MW']*eur,
                reference_idle_kW=e['standby_kW'], research_self_discharge=.001,
                source='equipment_study_inputs.json', cost_kind='DEA total installed industry transfer EUR2020'))
        elif v['id']!='itm-poseidon':
            c = v['costs']['packages']
            MW = e['full_load_AC_kW']/1000
            electrolysers.append(dict(id=v['id'], MW=MW, kg_hour=e['H2_kg_hour'],
                kWh_kg=e['system_kWh_kg'], minimum=e['minimum_online_fraction'],
                grade=e['base_gas_grade'], life=30,
                comparable=dict(capital_GBP=MW*p['hydrogen_cost_MW'],
                    fom_GBP=MW*p['hydrogen_FOM_MW'],
                    replacement_GBP=MW*p['hydrogen_replacement_MW'],
                    replacement_years=p['hydrogen_replacement_years'], variable_GBP_kg=0),
                research={level:dict(capital_GBP=r['installed'], fom_GBP=r['fixed_OM_year'],
                    replacement_GBP=0, replacement_years=[], variable_GBP_kg=r['variable_stack_reserve_per_kg'])
                    for level,r in c.items()}, source='equipment_study_inputs.json'))
    tesla = json.loads((TESLA/'ECONOMIC_INPUTS.json').read_text(encoding='utf-8'))['profiles']
    # The historical installed quote is the main reference. The current equipment
    # plus EPC case is a separate 2% US inflation transfer, not a UK firm quote.
    for v in tesla:
        if v['id']=='tesla2xl_2h_2024_installed_reference':
            K=v['capital_K']*usd2024
            batteries.append(dict(id='tesla-megapack2xl-2h', E_MWh=v['E_kWh']/1000,
                P_MW=v['P_kW']/1000, rte=.92, life=15, capital_GBP=K,
                fom_GBP=.025*K, fom_literal_GBP=.025*K, reference_idle_kW=None,
                research_self_discharge=.001, source='tesla_economic_inputs.json',
                cost_kind='2024 US installation-included estimate; NREL total maintained-capacity FOM'))
        elif v['id']=='tesla2xl_2h_2026_equipment_plus_EPC_proxy':
            # Values in this profile are a 2026 USD quote plus year-adjusted EPC.
            current_K=v['capital_K']*usd2024/(1.02**2)
    assert len(batteries)==4 and len(electrolysers)==8
    for b in batteries:
        # SOC20--80 remains the common daily model protocol, rather than an
        # assertion that factory permitted depth is only60%.
        b['soc_lower']=.2; b['soc_upper']=.8
        b['self_discharge']=0.
        b['loss_boundary']='Nominal whole-AC cycle factor; no additional idle fee/energy is stacked onto it. Isolated standby at zero throughput is not resolved in the retained daily protocol.'
        b['capacity_accounting']='Maintained available capacity; maintenance budget includes renewal, no second explicit cell bill.'
    cap=json.loads((BASE/'configuration.json').read_text(encoding='utf-8'))['overrides']['hydrogen_limit_kg']
    config=dict(version='v6-multiproduct-20261110', r=p['rate'], netback=p['hydrogen_price'],
        cap_kg_day=cap, commission_price=p['commission_price_GBP_MWh'],
        years=[2020,2025], batteries=batteries, electrolysers=electrolysers,
        alternatives=dict(tesla2026_proxy_capital_GBP=current_K),
        normalization=dict(EUR2020_to_GBP2020=eur, USD2024_to_GBP2020=usd2024,
            USD2026_to_USD2024_reference=1/(1.02**2)),
        preserved=['same repaired daily panel and historical real electricity prices',
            'total generation plus independent wind farm; inflexible background',
            'constant H2 netback and national upper-envelope acceptance case',
            'no H2 inventory, no grid electricity imports, no shortfall penalty',
            'A economic dispatch; B direct generation then battery inventory serves demand first',
            'chronological daily SOC; battery discharge can feed electrolysers',
            'one net charge/discharge direction per battery type/day; SOC20--80',
            'zero initial/terminal usable inventory; lowerSOC commissioning separately valued',
            '5% real discount,15/30year lives and annual-equivalent cash accounting'],
        product_cost_cases=dict(comparable='v5 electrolyser costs per actual AC inputMW; replacement years11/22 unchanged',
            research='whole BEIS2020 central/low/high cost packages; stack reserve charged perkg, no second replacement'),
        other_interfaces=['Industrial-grade H2 accepted at the retained common netback; no additional wet-gas POSEIDON product in the main pool.',
            'Factory RTE is a nominal point, not a site guarantee; external transformer loss unresolved.',
            'No inferred one-unit quote or volume discount from the Tesla five-unit quote. One-unit granularity is a study transfer.'])
    write(ROOT/'configuration.json', config)
    write(ROOT/'research/SOURCE_HASHES.json', {str(q):hashlib.sha256(q.read_bytes()).hexdigest()
        for q in (RESEARCH/'STUDY_INPUTS.json',TESLA/'ECONOMIC_INPUTS.json',BASE/'configuration.json')})
    return config

if __name__=='__main__': build()
