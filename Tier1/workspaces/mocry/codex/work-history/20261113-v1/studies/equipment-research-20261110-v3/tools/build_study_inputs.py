"""Daily reference scenarios for the candidates with sufficient system-level facts.

Every transfer is labelled. These profiles do not change an active baseline.
"""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build():
    ps=json.loads((ROOT/'catalogue.json').read_text(encoding='utf-8'))['products']
    refs=json.loads((ROOT/'reference_scenarios.json').read_text(encoding='utf-8'))
    records=[]
    for p in ps:
        t=p['technical']
        if p['id'] in ('sungrow-st255cs-2h','huawei-luna215','huawei-luna241'):
            E=t['nominal_energy_kWh'];P=t['nominal_AC_power_kW']
            capex=245*E+86*P
            idle=P*(2/2500) if p['manufacturer']=='Sungrow' else .075
            records.append(dict(id=p['id'],kind='battery',mode='daily nominal reference scenario',
                facts_record='products/'+p['id']+'.json',
                electrical=dict(nominal_energy_kWh=E,permitted_DoD=t['permitted_DoD'],
                    study_DoD=.8,usable_energy_kWh=.8*E,charge_AC_kW=P,discharge_AC_kW=P,
                    roundtrip_AC=.90,eta_charge=math.sqrt(.90),eta_discharge=math.sqrt(.90),
                    self_discharge_fraction_day=.001,standby_kW=idle),
                lifecycle=dict(calendar_reference_years=15,cycle_reference=2400,cycle_reference_DoD=.8,EOL_SOH=.60,
                    service_convention='Maintained available capacity in the annual cost reference; no separate augmentation charge or simultaneous uncompensated capacity decay is imposed.',
                    alternative_depth_life=dict(study_DoD=.6,cycles=8000,usable_energy_kWh=.6*E)),
                costs=dict(currency='EUR',price_year=2020,installed_reference=capex,
                    fixed_OM_cases_per_year=dict(literal_per_MW=8352*P/1000,alternative_capex_fraction=.029*capex),
                    additional_explicit_stack_or_cell_replacement=0,
                    replacement_zero_reason='Already represented by the selected maintenance/maintained-capacity accounting convention; not a claim that physical replacement is free.'),
                field_sources=dict(nominal_energy_and_permitted_depth='Manufacturer product sheet',
                    charge_discharge_power='Equal bidirectional nominal rating is a study interpretation; charging maximum is not separately guaranteed in every retained sheet.',
                    operating_DoD_and_cycles='PNNL H6748:H6752:80%/2400 or60%/8000; not a product-specific cycle guarantee',
                    roundtrip='0.90 operating reference; DEA AC reference0.91 and supplier maximum/bound retained separately',
                    efficiency_split='Model protocol: symmetric square-root split',
                    self_discharge='DEA D15:0.1%/day, transferred lithium-ion reference',
                    standby='Sungrow: engineering size transfer from TALLON2kW/2500kW; Huawei: midpoint of published0..0.15kW bound, not a measured mean',
                    cost_and_fixed_OM='DEA D24:D28; decomposition and unresolved FOM unit interpretation retained',
                    calendar_life='DEA15years;PNNL16year alternative',
                    EOL='PNNL LFP reference60%; maintained-output scenario rather than a manufacturer fade guarantee'),
                sensitivity=dict(whole_plant_roundtrip=[.83,.90,.913 if p['manufacturer']=='Huawei' else .91],
                    storage_loss_per_day=[.0005,.001,.002],
                    standby_kW=[0,.2] if p['manufacturer']=='Sungrow' else[0,.15],
                    capex_source_alternative='PNNL LFP2023 10MW/2h:USD452.22/kWh (range407..497.44),FOM USD2.79/kW-year; switch entire currency/scope package before comparing'),
                readiness='Numeric inputs complete for a declared daily maintained-capacity reference scenario; not a supplier quote/warranty'))
        elif p['type']=='electrolyser' and t['technology']=='PEM' and p['readiness']['technical_reference_core_known']:
            q=t['hydrogen_kg_per_hour'];e=t['system_specific_kWh_per_kg'];power=q*e
            hhv=q*39.37
            package=refs['electrolysis']['old_UK2020_packages']['PEM']
            cost={level:dict(installed=package['legacy_capex_GBP2020_per_kWHHV'][level]*hhv,
                       fixed_OM_year=package['fixed_opex_GBP2020_per_kWHHV_year'][level]*hhv,
                       variable_stack_reserve_per_kg=package['variable_opex_stack_reserve_GBP2020_per_kWhHHV'][level]*39.37)
                  for level in ('low','central','high')}
            records.append(dict(id=p['id'],kind='electrolyser',mode='daily nominal reference scenario',
                facts_record='products/'+p['id']+'.json',
                electrical=dict(H2_kg_hour=q,H2_kg_day=q*24,system_kWh_kg=e,
                    full_load_AC_kW=power,full_load_MWh_day=power*24/1000,
                    minimum_online_fraction=t['minimum_steady_flow_fraction'],
                    outlet_pressure_barg=t['outlet_pressure_barg'],base_gas_grade=t['base_purity']),
                lifecycle=dict(plant_calendar_years=30,
                    stack_operating_hour_reference=40000,EOL_performance_loss_reference=.10,
                    cost_convention='BEIS variable OM is the stack-renewal reserve; keep nominal operating efficiency and account for renewal here, without another explicit replacement bill.',
                    hourly_life_role='DOE2022 status for lifecycle sensitivity; not an additional mandatory replacement schedule in the reserve case'),
                costs=dict(currency='GBP',price_year=2020,packages=cost,
                    additional_explicit_stack_replacement=0,
                    modern_total_installation_sensitivity_USD2024=dict(low=power*2000,high=power*2600),
                    modern_scope='IEA2025 non-China observations; alternative cost envelope, not added to the BEIS capital cost'),
                partial_load_convention='Constant nominal specific energy when online; manufacturer full partial-load curve not available in retained public sheets.',
                off_start_convention='Daily single steady state or shutdown; minute-scale start energy and warm standby are not resolved. No physical zero-start claim.',
                water=dict(litre_per_kg=t['water_litre_per_kg'],quality=t['water_quality'],
                    treatment='Nel15.9L/kg raw potable input is published. ITM volume remains a site utility input, not invented here.'),
                hydrogen_sale_boundary='Netback must use this delivered grade; POSEIDON wet core output requires a purification/compression allowance or matching wet-gas buyer.',
                field_sources=dict(flow_energy_load_pressure_grade='Manufacturer per-model data sheet',
                    plant_life_and_cost='BEIS2021 Annex PEM2020 complete reference cost package, on H2-HHV output basis',
                    stack_hours_and_EOL='DOE2022 PEM status40000h at10% performance loss; benchmark not product guarantee',
                    partial_load_and_start='Explicit daily model conventions',
                    modern_capex='IEA GHR2025 executive summary:2024 non-China installed cost USD2000..2600/kW'),
                readiness='Numeric daily power/flow/capital/FOM/renewal-reserve reference inputs complete; market grade and local water remain project interfaces'))
    result=dict(as_of='2026-11-10',primary_candidates=len(records),
        user_direction='Prefer products with high overall completeness; credible non-manufacturer evidence and estimates are acceptable.',
        status='Research reference inputs for evaluation; no automatic baseline adoption',profiles=records,
        shared_project_interfaces=['Currency and price-year normalisation from project finance research',
            'Actual site grid/land and water-service conditions',
            'Delivered H2 grade and matching netback; unchanged constant price is not evidence of identical buyer acceptance',
            'Existing daily initial/terminal inventory and A/B operating protocols'],
        reserve_candidates=[p['id'] for p in ps if p['id'] not in {r['id'] for r in records}],
        AEM_role='2026 full-system operation is well documented; legacy30k/40kh evidence retained, but a matched current installation/lifecycle-cost package is weaker. Keep AEM as sensitivity/research competitor instead of silently assigning PEM maintenance.',
        no_automatic_merge=True)
    assert len(records)==12
    (ROOT/'STUDY_INPUTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('STUDY_INPUTS',len(records),'primary profiles:3battery+9PEM; other15 retained as research/reserve candidates')

if __name__=='__main__':build()
