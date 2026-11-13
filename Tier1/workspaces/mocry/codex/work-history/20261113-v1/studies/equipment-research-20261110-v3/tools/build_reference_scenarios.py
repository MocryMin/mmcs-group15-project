"""Research-derived reference scenarios, deliberately separate from product facts."""
import json
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parents[1]


def build():
    w=openpyxl.load_workbook(ROOT/'evidence'/'DEA-storage.xlsx',read_only=False,data_only=True)
    s=w['180 Lithium Ion Battery']
    cells={f'D{row}':s[f'D{row}'].value for row in [8,9,10,11,12,15,18,24,25,26,27,28,29,33,34]}
    assert cells['D8']==3 and cells['D9']==1.5 and abs(cells['D24']-.288)<1e-10
    assert abs(cells['D25']+cells['D26']/2+cells['D27']-cells['D24'])<1e-10
    legacy=openpyxl.load_workbook(ROOT/'evidence'/'BEIS-Hydrogen-Costs2021-Annex.xlsx',read_only=False,data_only=True)
    c=legacy['Technical and cost assumptions']
    technology={}
    for name,col in [('alkaline','D'),('PEM','K')]:
        technology[name]={
            'commissioning_reference_year':c[f'{col}3'].value,
            'reference_electrical_efficiency_input_kWhe_per_kWhHHV':c[f'{col}11'].value,
            'plant_lifetime_years':c[f'{col}13'].value,
            'legacy_capex_GBP2020_per_kWHHV':dict(zip(['low','central','high'],[c[f'{col}{r}'].value for r in [14,15,16]])),
            'fixed_opex_GBP2020_per_kWHHV_year':dict(zip(['low','central','high'],[c[f'{col}{r}'].value for r in [21,22,23]])),
            'variable_opex_stack_reserve_GBP2020_per_kWhHHV':dict(zip(['low','central','high'],[c[f'{col}{r}'].value for r in [24,25,26]])),
            'replacement_fraction_of_legacy_capex':.5 if name=='alkaline' else .6,
            'replacement_calendar_years':9 if name=='alkaline' else 11}
    refs=dict(
        status='optional research reference scenarios;not manufacturer specifications or automatically adopted baseline',
        battery=dict(source='DEA-storage.xlsx 180 Lithium Ion Battery D-column2025;currencyEUR2020',
            verified_cells=cells,
            installed_cost_formula_EUR2020='95000*nominal_MWh + 86000*AC_MW + 150000*nominal_MWh',
            scope='generic3MWh/1.5MW reference;transfer to other vendors/sizes requires explicit scenario label',
            fixed_maintenance_cases=dict(literal_EUR2020_per_MW_year=8352,
                                         alternative_fraction_of_total_capex_per_year=.029),
            maintenance_warning='source formula/unit conflict;do not claim either interpretation is supplier-confirmed',
            AC_roundtrip_reference=.91,DC_roundtrip_reference=.95,
            whole_AC_roundtrip_independent_PNNL_LFP2023=.83,
            lifetime_calendar_years=15,self_discharge_fraction_day=.001,
            storage_loss_sensitivity=[.0005,.001,.002],
            DoD_life_reference=dict(primary_DoD=.8,cycles_at_primary=2400,secondary_DoD=.6,
                                    cycles_at_secondary=8000,calendar_years=16,EOL_SOH=.6,
                                    source='PNNL Database H6747:H6752;not supplier-specific'),
            auxiliary_rule='Do not add a second copy of auxiliaries already in a whole-system RTE. '
                           'Retain documented standby bounds;unpublished standby is not asserted zero.',
            open_physical_fields='No unverified product DoD,PCS compatibility or mean efficiency is filled from these references'),
        electrolysis=dict(
            modern_installed_cost=dict(currency='USD',observation_year=2024,
                                       non_China_per_kW=[2000,2600],
                                       source='IEA GHR2025 executive summary;not vendorquotation or all-scaleAEMestimate'),
            old_UK2020_packages=technology,
            HHV_kWh_kg=39.37,
            fixed_opex_conversion='GBP_per_kWHHV_year * nominal_H2_kg_hour *39.37',
            replacement_conversion='fraction *legacy_capex_GBP_per_kWHHV *nominal_H2_kg_hour*39.37',
            no_double_count='Choose explicit replacements OR the annuitised stack-reserve VOM,not both.',
            do_not_scale_old_fraction_to_modern_capex='Old stack fraction belongs to the old plant package;do not multiply it by a different modern total installed price.',
            DOE_operating_hour_reference=dict(PEM_2022_status=40000,alkaline_2022_status=60000,
                                              target_80000_is_not_current_product_warranty=True,
                                              EOL_performance_loss=.10),
            AEM_legacy_2022_reference=dict(EL21_assumed_operating_hours=30000,
                                         ModelT_forward_looking_assumption=40000,
                                         source='Enapter-2022-pricing-assumptions.pdf',
                                         warning='Legacyassumptions,not aFlex/Nexus/Rheoslife guarantee;use only declared AEM-family sensitivity'),
            water_rule='Apply product raw/purified flow definitions separately;site water price/RO recovery are external project inputs.',
            finance_rule='Keep quote currency,year and scope;do not compare an uninstalled EURprice directly with GBP2020 installedcost.',
            missing_product_quotes='Native supplier prices/historical orders stay in each product record. No invented product-specific quotation.'
        ))
    (ROOT/'reference_scenarios.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    catalogue=json.loads((ROOT/'catalogue.json').read_text(encoding='utf-8'))
    examples=[]
    for item in catalogue['products']:
        t=item['technical']
        if item['type']=='battery':
            energy=t['nominal_energy_kWh']/1000
            power=t['nominal_AC_power_kW']
            if power is None:
                examples.append(dict(id=item['id'],status='requires externalPCS definition;no installedcost assigned'))
                continue
            power/=1000
            examples.append(dict(id=item['id'],status='illustrative transferred generic cost,not supplier quote',
                capex_EUR2020=95000*energy+86000*power+150000*energy,
                fixed_OM_EUR2020_year_literal=8352*power,
                fixed_OM_EUR2020_year_alternative=.029*(95000*energy+86000*power+150000*energy),
                lifetime_reference_years=15,source='DEA reference;scaleandbrandtransfer'))
        else:
            q=t['hydrogen_kg_per_hour']
            if t['technology'] in technology:
                family=technology[t['technology']]
                examples.append(dict(id=item['id'],status='legacy UK generic life/maintenance reference,not a supplier promise',
                    annual_fixed_OM_GBP2020_range={k:v*q*39.37 for k,v in family['fixed_opex_GBP2020_per_kWHHV_year'].items()},
                    explicit_stack_replacement_GBP2020=family['replacement_fraction_of_legacy_capex']*
                        family['legacy_capex_GBP2020_per_kWHHV']['central']*q*39.37,
                    replacement_calendar_interval_years=family['replacement_calendar_years'],
                    plant_lifetime_years=30,source='BEIS2021annex2020column;standalonegenericcostscenario'))
            else:
                examples.append(dict(id=item['id'],status='AEM product-specific lifecycle and costs unresolved',
                    optional_legacy_AEM_operating_hours_cases=[30000,40000],
                    warning='Neither value is a verified lifetime of this modern product;no PEMreplacementcost copied'))
    (ROOT/'illustrative_cost_inputs.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('REFERENCE_SCENARIOS',len(examples),'product entries; source and transfer labels retained')


if __name__=='__main__':build()
