"""Build research inputs from retained primary-source snapshots; no network."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
E=ROOT/'evidence'

def write(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def build_quotes():
    rows=[]
    raw=json.loads((E/'pages-06-static-archive.json').read_text(encoding='utf-8'))
    for page in raw:
        for s in page.get('scripts',[]):
            if s.get('type')!='application/json':continue
            j=json.loads(s['text'])
            for q in j.get('props',{}).get('pageProps',{}).get('dehydratedState',{}).get('queries',[]):
                if not any(x in str(q.get('queryKey')) for x in ['megapackPricing','quoteConfigs']):continue
                key=q['queryKey'];v=q['state']['data']['data']
                old=key[0]=='quoteConfigs'
                n=key[4] if old else key[1]
                quarter=key[5] if old else key[2]
                installed=key[6] if old else(key[3] if isinstance(key[3],bool) else False)
                rows.append(dict(snapshot=page['url'].split('/web/')[1].split('id_')[0],url=page['url'],
                    origin='Tesla public page server-rendered __NEXT_DATA__',currency='USD',site='California,US',
                    quantity=n,configuration='2hXL',delivery_quarter=quarter,installation_included=installed,
                    total_price=v['totalPrice'],maintenance_first_year=v['annualMaintenancePrice'],
                    price_per_unit=v['totalPrice']/n,maintenance_per_unit_year1=v['annualMaintenancePrice']/n,
                    price_status='non-final estimate;taxes excluded;unit figure is five-unit average,not an independent one-unit quote',
                    quote_query_key=key,source_file='evidence/pages-06-static-archive.json'))
    for page in json.loads((E/'pages-09-latest-quotes.json').read_text(encoding='utf-8')):
        for rec in page.get('data',[]):
            if 'quote' not in rec:continue
            key=rec['query_key'];v=rec['quote'];n=key[1]
            rows.append(dict(snapshot=page['url'].split('/web/')[1].split('id_')[0],url=page['url'],
                origin='Tesla public page server-rendered __NEXT_DATA__',currency='USD',site='California,US',
                quantity=n,configuration='2hXL',delivery_quarter=key[2],installation_included=False,
                total_price=v['totalPrice'],maintenance_first_year=v['annualMaintenancePrice'],
                price_per_unit=v['totalPrice']/n,maintenance_per_unit_year1=v['annualMaintenancePrice']/n,
                price_status='non-final estimate;taxes and installation excluded;five-unit average',quote_query_key=key,
                source_file='evidence/pages-09-latest-quotes.json'))
    write('TESLA_QUOTES.json',dict(records=rows,monthly_unit_price_trend='Not inferred:installation scope and delivery quarters differ',
        quantity_discount_curve='Not identified;all recovered price points are five-unit configurations',
        four_hour_specific_quote='Not recovered;industry reference profiles separately labelled'))
    return rows

def build_lazard():
    cases={
        'utility_2h':dict(P_MW=100,E_MWh=200,DC_USD_kWh=[113,244],AC_USD_kW=[26,70],EPC_USD_kWh=[29,122],
            installed_total_mUSD_reported=[34,88],OM_USD_kWh_year=[3,8.2],warranty_fraction_K=[.0065,.015],RTE=[.91,.87],charging_USD_MWh=33),
        'utility_4h':dict(P_MW=100,E_MWh=400,DC_USD_kWh=[107,232],AC_USD_kW=[25,67],EPC_USD_kWh=[28,116],
            installed_total_mUSD_reported=[62,160],OM_USD_kWh_year=[3,8],warranty_fraction_K=[.0066,.0185],RTE=[.92,.86],charging_USD_MWh=27),
        'CI_2h':dict(P_MW=1,E_MWh=2,DC_USD_kWh=[238,445],AC_USD_kW=[40,80],EPC_USD_kWh=[56,168],
            installed_total_mUSD_reported=[1,1],OM_USD_kWh_year=[7.3,9.1],warranty_fraction_K=[.005,.013],RTE=[.92,.88],charging_USD_MWh=111)
    }
    for c in cases.values():
        k=[c['DC_USD_kWh'][i]*c['E_MWh']*1000+c['AC_USD_kW'][i]*c['P_MW']*1000+
           c['EPC_USD_kWh'][i]*c['E_MWh']*1000 for i in [0,1]]
        c['reconstructed_K_before_overbuild']=k
        c['reconstructed_K_with10pct_overbuild']=[1.1*x for x in k]
        c['reconstructed_installed_USD_per_reference_kWh']=[x*1.1/(c['E_MWh']*1000) for x in k]
        c['first_year_general_OM_USD']=[x*c['E_MWh']*1000 for x in c['OM_USD_kWh_year']]
    out=dict(source_pdf='evidence/Lazard-LCOEplus-202506-archived20251025.pdf',physical_pages=[19,42,43],
        original_url='https://www.lazard.com/media/5tlbhyla/lazards-lcoeplus-june-2025-_vf.pdf',
        archive_url='https://web.archive.org/web/20251025104311id_/https://www.lazard.com/media/5tlbhyla/lazards-lcoeplus-june-2025-_vf.pdf',
        report_year=2025,currency='USD',price_year_assumption=2025,
        price_year_note='Report presents USD;using2025pricebase is a modelling interpretation,not an independently stated real-dollar index',
        cases=cases,general_OM_escalator=.025,warranty_start_year=3,project_years=20,depth=.9,initial_overbuild=.10,
        cycles_per_operating_day=1,operating_days_year=350,
        general_OM_row_scope='General O&M only;warranty and augmentation separately enter total operating-cost line',
        augmentation_scope='Not in initial capital cost;incurred later to restore usable energy,valued at original module cost in methodology',
        charging_scope='LCOS already includes charging and financing/tax assumptions;not an additional cash charge in a separate dispatch model',
        transfer_rules=['Do not add10%overbuild again to alreadyoverbuilt installed totals',
            'Do not add general O&M,warranty and augmentation twice by reading the total cost line as another fee',
            'Year3warranty is a Lazard scenario,not Tesla15year warranty terms',
            'Scale endpoints are scenario types,not a supplier quantity-discount curve',
            'Do not add a standalonePCS charge to the integratedTesla equipment quote',
            'UKproject does not inherit USITC,MACRS,leverage or charging tariff automatically'])
    write('LAZARD_BOUNDARIES.json',out)
    return out

def build_profiles(quotes,lazard):
    old=next(x for x in quotes if x['snapshot']=='20240106085048')
    new=next(x for x in quotes if x['snapshot']=='20261011091248')
    E2=3854.4;P2=1927.2;E4=3916;P4=979
    oldK=old['price_per_unit'];routine=old['maintenance_per_unit_year1']
    epc=[x*E2*1.02 for x in lazard['cases']['CI_2h']['EPC_USD_kWh']]
    currentK=[new['price_per_unit']+x for x in epc]
    four=lazard['cases']['utility_4h']
    fourK=[four['DC_USD_kWh'][i]*E4+four['AC_USD_kW'][i]*P4+four['EPC_USD_kWh'][i]*E4 for i in [0,1]]
    four_small=lazard['cases']['CI_2h']
    four_smallK=[four_small['DC_USD_kWh'][i]*E4+four_small['AC_USD_kW'][i]*P4+four_small['EPC_USD_kWh'][i]*E4 for i in [0,1]]
    common=dict(horizon_years=15,standard_warranty_years=15,extended_warranty_purchased=False,
        extension_cost_in_base=0,extension_zero_reason='Horizon ends within standard warranty;no20year extension is purchased or claimed free',
        net_terminal_value=0,terminal_assumption='Financial reference only,no evidenced positive resale credit;site removal needs a separate project allowance if required',
        normalised_currency='Native USD at each declared year;projectGBP2020 conversion is a separate shared-finance interface',
        finance=dict(real_discount_reference=.05,general_inflation_reference=.02,
                     nominal_discount_reference=1.05*1.02-1,source='project/reference financial conventions,not aTesla quoted hurdle rate'),
        maintenance_nominal_escalator=.02,capacity_accounting='NREL-style15year maintained-capacity reference,with augmentation budget included in totalFOM',
        monetary_year_note='Quote/report observation year treated as the native nominal price base for research;not a separately certifiedconstant-dollarindex',
        reservation_fee_rule='Base assumes credited against final contract or immaterial within scope estimate;credit not explicitly established by publictemplate,so test non-credit sensitivity',
        total_FOM_reference_fraction_K=.025,
        total_FOM_source='NREL ATB2024:includes augmentation to maintain rated capacity15years;transfer toTesla/site size is an explicit engineering estimate',
        no_double_count='RoutineTesla fee is included within totalFOM reference,not added on top;no separate normal-aging replacement bill in the same case',
        project_scope_assumptions=['Existing suitable site and interconnection;no new land purchase or major network reinforcement',
            'Pre-tax and pre-financing incremental equipment study;VAT/ownerfinance not added as vendor fees',
            'No optionalAutobidder revenue contract or subscription purchased;our own control model used',
            'No invented bulk discount;five-unit average transferred only as an explicitly identified price hypothesis'],
        physical_gaps_unchanged='Product permittedDoD/retention curve not fully public;economic study inputs do not manufacture a warranty curve')
    profiles=[dict(common,id='tesla2xl_2h_2024_installed_reference',product_id='tesla-megapack2xl-2h',
        evidence_strength='Manufacturerfive-unitUSinstalled estimate plus explicitNRELlifecycle transfer',
        currency='USD',price_year=2024,E_kWh=E2,P_kW=P2,RTE_product=.92,
        capital_K=oldK,general_maintenance_first_year=routine,total_FOM_year=.025*oldK,
        remaining_lifecycle_budget_year=.025*oldK-routine,
        source_quote=old,noncredited_reservation_fee_per_quoted_five_unit_batch=1000,
        capital_scope='Installation included in selectedTeslaoption;taxesexcluded;localUKsite adaptation remains a transfer',
        scenario_role='Primaryinstalled-price reference;not a currentUKfirmquote'),
        dict(common,id='tesla2xl_2h_2026_equipment_plus_EPC_proxy',product_id='tesla-megapack2xl-2h',
        evidence_strength='Manufacturer2026equipment estimate plus adjacent-scaleEPC estimate',
        currency='USD',price_year=2026,E_kWh=E2,P_kW=P2,RTE_product=.92,
        equipment_K=new['price_per_unit'],EPC_proxy_range=epc,capital_K_range=currentK,capital_K=sum(currentK)/2,
        general_maintenance_first_year=new['maintenance_per_unit_year1'],
        total_FOM_year=.025*sum(currentK)/2,total_FOM_year_range=[.025*x for x in currentK],
        remaining_lifecycle_budget_year=.025*sum(currentK)/2-new['maintenance_per_unit_year1'],
        source_quote=new,noncredited_reservation_fee_per_quoted_five_unit_batch=10000,
        EPC_source='LazardCI2h56..168USD/kWh transferred to9.6MWfleet;2025to2026 inflation2%assumption',
        capital_scope='IntegratedequipmentplusEPCproxy;no extraPCS;site and owner exclusions in common assumptions',
        scenario_role='Currentequipmentanchored research estimate with range'),
        dict(common,id='tesla2xl_4h_industry_cost_reference',product_id='tesla-megapack2xl-4h',
        evidence_strength='Producttechnicalfacts;financialcosts industry-only,no recovered4hTeslaquote',
        currency='USD',price_year=2025,E_kWh=E4,P_kW=P4,RTE_product=.937,
        capital_K=sum(fourK)/2,capital_K_range=fourK,alternative_small_site_capital_range=four_smallK,
        total_FOM_year=.025*sum(fourK)/2,total_FOM_year_range=[.025*x for x in fourK],
        general_maintenance_first_year=None,
        general_maintenance_note='No4hTesla-specific quote;wholeFOMreference covers maintenance and capacity renewal',
        capital_scope='Lazardutility4hcomponentrates on physicalTeslaE/P,no extra10%initialoverbuild;smallsite2hcoefficienttransfer is an explicit separate sensitivity',
        scenario_role='Competition/sensitivity;not supplier-price ranking')]
    ext=dict(actual_Tesla_extension_price=None,
        optional_20year_sensitivity=dict(warranty_fraction_K=[.0065,.015],first_paid_year=16,last_year=20,
            source='Lazard2hgenericpricefraction transferred,notTeslaquote;year16 chosen because standardTesla15years',
            note='15yearNRELmaintained-capacitycase is not automatically extrapolated to20years;service/augmentation budget must also be specified'))
    write('ECONOMIC_INPUTS.json',dict(version='1.0',as_of='2026-11-10',profiles=profiles,extension=ext,
        baseline_adoption=False,research_stage='Complete numerical15year economic-reference inputs within declared scope;unpublishedactualcosts explicitly estimated',
        not_claimed=['UKfirmquotation','Actualsingleunitprice','Actualquantitydiscountcurve','Manufacturerfundedagingaugmentation','Freeextensionto20years']))
    return profiles

def verify(quotes,lazard,profiles):
    flag=json.loads((E/'2024-ui-selection.json').read_text(encoding='utf-8'))
    assert flag['installation_yes_selected']=='true' and flag['state']=='CA'
    assert len(quotes)==6 and all(q['quantity']==5 for q in quotes)
    for q in quotes:
        assert q['price_per_unit']*5==q['total_price']
        assert q['maintenance_per_unit_year1']*5==q['maintenance_first_year']
    old=profiles[0];assert old['capital_K']==1951954 and old['general_maintenance_first_year']==5922
    assert next(q for q in quotes if q['snapshot']=='20261011091248')['price_per_unit']==1009080
    assert math.isclose(old['total_FOM_year'],48798.85)
    assert math.isclose(lazard['cases']['utility_2h']['reconstructed_K_with10pct_overbuild'][0],34100000)
    assert math.isclose(lazard['cases']['CI_2h']['reconstructed_K_with10pct_overbuild'][1],1436600)
    for p in profiles:
        assert p['capital_K']>0 and p['total_FOM_year']>0
        assert not p['extended_warranty_purchased'] and p['horizon_years']==15
        if p.get('general_maintenance_first_year') is not None:
            assert math.isclose(p['remaining_lifecycle_budget_year']+p['general_maintenance_first_year'],p['total_FOM_year'])
    write('QA.json',dict(status='pass',quote_snapshots=6,profiles=3,
        checks=['ArchivedSSRquantities/configurations/currency matched','InstallationYesverified in archivedDOM',
            'Equipment-only and installedprices not treated as a common-scope trend','Maintenance divided byfive,not confused as perunit',
            'LazardO&M,warranty andaugmentation separated','10%overbuild counted only in benchmarkreconstruction',
            'Tesla routinefee not added on top of NRELwholeFOM','NoextraPCSchargeforintegratedequipment',
            'Tesla4hcostproxy not labelled amanufacturerquote','NoUSD/GBP or real/nominalsilentmix'],
        visual_pages=['Lazard42','Lazard43','TeslaMaintenance1','TeslaMaintenance2','TeslaInstallation2'],
        no_new_optimization=True,no_remote_publication=True))

if __name__=='__main__':
    q=build_quotes();l=build_lazard();p=build_profiles(q,l);verify(q,l,p)
    print('PASS:6 first-party archivedquotes,3economicprofiles;15yearscope and source/estimate boundaries explicit')
