"""Build per-product records from the retained manufacturer documents.

Unknown values stay null. Industry reference scenarios are kept separately
from manufacturer facts and are never silently merged into an active model.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def battery(identifier,brand,name,energy,power,source,**kw):
    technical=dict(nominal_energy_kWh=energy,usable_energy_kWh=None,
                   nominal_AC_power_kW=power,max_AC_charge_power_kW=None,max_AC_discharge_power_kW=None,
                   battery_DC_charge_power_kW=None,battery_DC_discharge_power_kW=None,
                   permitted_DoD=None,normalized_SOC_operating_range=None,
                   roundtrip_AC=None,roundtrip_DC=None,one_way_efficiencies=None,
                   auxiliary_active_kW=None,auxiliary_standby_kW=None,self_discharge_per_day=None,
                   lifetime_years=None,cycle_life=None,EOL_SOH=None,degradation_curve=None,warranty_years=None,
                   availability=None,parallel_limit=None,ambient_temperature_C=None,derating_above_C=None,scope=None)
    technical.update(kw)
    if technical['permitted_DoD'] is not None:
        technical['usable_energy_kWh']=energy*technical['permitted_DoD']
        technical['normalized_SOC_operating_range']=[0,1]
        technical['usable_definition']='Derived within the manufacturer-defined permitted depth;not chemical-cell absolute0-100%.'
    return dict(id=identifier,type='battery',manufacturer=brand,model=name,
                source=source,technical=technical,public_prices=[],
                investment_reference='BATTERY-DECOMPOSITION-2020; transfer scenario, not a supplier quotation',
                model_protocol=['daily net charge or discharge','daily stock carryover','declared initial and terminal usable stock',
                                'declare any one-way efficiency split','do not apply60%usable multiplier toalreadyusableenergy',
                                'separate group/controller parallel limit from project-wide capacity'],
                general_gaps=['Matched installed price and site scope','Maintenance/renewal/disposal contract',
                              'Duty-dependent whole-system performance and degradation, if not explicitly supplied'])


def electrolyser(identifier,brand,name,technology,marketing_mw,q,e,minimum,source,**kw):
    technical=dict(technology=technology,marketing_class_MW=marketing_mw,
                   hydrogen_kg_per_hour=q,system_specific_kWh_per_kg=e,
                   nominal_system_input_kW=None,nominal_stack_input_kW=None,
                   minimum_flow_fraction=minimum,minimum_transient_flow_fraction=None,
                   transient_limit_hours=None,minimum_steady_flow_fraction=minimum,
                   operating_range_basis='flow fraction unless datasheet explicitly says power',
                   outlet_pressure_barg=None,base_purity=None,optional_purity=None,
                   additional_purification_kW=None,water_litre_per_kg=None,water_quality=None,
                   ramp=None,hot_start_seconds=None,cold_start_seconds=None,
                   standby_kW=None,minimum_up_time_hours=None,minimum_down_time_hours=None,
                   stack_lifetime_hours=None,plant_lifetime_years=None,warranty_years=None,ambient_temperature_C=None,
                   degradation_curve=None,replacement_cost=None,maintenance=None,scope=None)
    technical.update(kw)
    if q is not None and e is not None:
        derived=q*e
        if technical['nominal_system_input_kW'] is None:
            technical['nominal_system_input_kW']=derived
            technical['power_origin']='Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum.'
        technical['nominal_power_to_flow_ratio_kWh_per_kg']=technical['nominal_system_input_kW']/q
        technical['nominal_power_consistency_relative_error']=abs(technical['nominal_system_input_kW']-derived)/derived
    return dict(id=identifier,type='electrolyser',manufacturer=brand,model=name,
                source=source,technical=technical,public_prices=[],
                investment_reference='PEM/alkaline generic references separated by technology;AEMlifecycle not silently borrowed fromPEM',
                model_protocol=['daily steady-state and shutdown convention','preserve both nominal output and input definitions',
                                'part-load curve approximation must be declared','common delivered hydrogen grade before applying equal netback',
                                'use one consistent stack-replacement accounting route'],
                general_gaps=['Current full installed project price','Product-specific lifetime/renewal cost and downtime',
                              'Off/standby/start energy and full partial-load curves where unpublished'])


def build():
    products=[]
    products.append(battery('tesvolt-tallon','TESVOLT','TALLON',5015,2500,
        'TESVOLT-TALLON.pdf p1, revisionRD.TI.150.E.de-DE B.01',permitted_DoD=1.,
        roundtrip_DC=dict(points=[dict(rate_Cp=.5,efficiency=.937),dict(rate_C=.25,efficiency=.952)],boundary='DC connection point'),
        auxiliary_active_kW=dict(typical25C=23,typical45C=33,peak=36),
        auxiliary_standby_kW=dict(value=2,kind='stated standby'),
        auxiliary_duty_reference=dict(annual_MWh=63.51,cycles_day=1.5,warning='not additive to all other auxiliary figures'),
        lifetime_years=15,cycle_life=11000,EOL_SOH=.60,warranty_years=dict(standard=15,optional=20,kind='combined product/performance, purchase terms control'),
        ambient_temperature_C=[-30,55],
        lifetime_conditions='average2cycles/day,100%DoD,max0.5Cp;optional20yearwarranty not automatic20yearconstantcapacity',
        scope='DC battery container;needs matchingPCS and AC-system boundary'))
    products.append(battery('tesvolt-powercore-g2','TESVOLT','POWERCORE G2 IA-250kW/500kWh',509,250,
        'TESVOLT-POWERCORE-G2.pdf p2; manufacturer product pageFAQ retained inlegacy sources',
        marketed_energy_kWh=500,battery_DC_charge_power_kW=244,battery_DC_discharge_power_kW=254.8,
        ambient_temperature_C=[-20,55],derating_above_C=45,
        roundtrip_AC=dict(maximum_approx=.92,conditions='manufacturerFAQ:configurationandoperatingconditions'),
        cycle_life=dict(value=10000,kind='webpage>10000 cycles'),
        EOL_SOH=dict(lower=.70,at_year=10,kind='webpage reference;detailed duty/contract not verified'),
        rating_issue='Battery section and250kWACrating cannot be equated without conversion/boundary confirmation',
        scope='battery plusPCS, but usable depth and rating boundaries not fully published'))
    products.append(battery('sungrow-st255cs-2h','Sungrow','PowerStack ST255CS-2H',257,125,
        'Sungrow-PowerStack255CS.pdf pp1-2V2(2025);pages-04.json;user manual',
        permitted_DoD=1.,roundtrip_AC=dict(lower_exclusive=.90,kind='productpage states consistentlyover90%;not a mean or point'),
        ambient_temperature_C=[-30,50],derating_above_C=45,
        PCS_efficiency_max=.985,parallel_limit=dict(on_grid=25,off_grid=10,boundary='one system group;not a global investment cap'),
        auxiliary_supply='internal bydefault;external optional;quantified draw unpublished',
        maintenance='Usermanualp93:yearlyinspection and cell replacement when needed;no numeric service life guarantee',
        scope='integratedACBESS, approximately2-hourclass'))
    for hours,power in [(2,2500),(4,1250)]:
        products.append(battery(f'sungrow-powertitan2-{hours}h','Sungrow',f'PowerTitan2.0 ST5015kWh-{power}kW-{hours}h',5015,power,
            'Sungrow-PowerTitan2-2H4H-V3.pdf pp1-2V3(2023)',
            apparent_power_kVA=2520 if hours==2 else 1260,ambient_temperature_C=[-30,50],derating_above_C=45,
            course_scope='2-hourreference' if hours==2 else'4-hourextension;not silently a2-hourcandidate',
            scope='integratedACblock;DoD and ACroundtrip not stated in retained sheet'))
    for energy,model in [(215,'LUNA2000-215-2S10'),(241,'LUNA2000-241-2S1')]:
        products.append(battery('huawei-luna'+str(energy),'Huawei',model,energy,108,
            f'Huawei-LUNA{energy}-'+('2S10' if energy==215 else'2S1')+'.pdf p1;pages-12/13.json',
            permitted_DoD=1.,ambient_temperature_C=[-30,55],derating_above_C=50,
            roundtrip_AC=dict(maximum=.913,kind='maximumcycleefficiency;not routineaverage',
                                            test_rate_C=.25 if energy==241 else .5),
            auxiliary_standby_kW=dict(upper=.15,kind='standbyupperbound'),
            auxiliary_supply_rating_kW_upper=5,
            auxiliary_warning='5kW is supply rating,not a constant parasitic load;avoid doublecounting cycleauxiliaries',
            PCS_model='PCS2000-108K-MB1',scope='integratedACBESS;productgrades/revisions keptseparate'))
    products.append(battery('huawei-luna5015','Huawei','LUNA2000-5015-2S',5015,None,
        'Huawei-LUNA5015-2S.pdf p1;PCS213KTL-H0 is a separate component',
        battery_DC_charge_power_kW=2507.5,battery_DC_discharge_power_kW=2507.5,
        scope='DCcontainer,not an integrated2507.5kWACsystem;needsPCS and efficiency closure'))
    for family,energies,capacities in [('EnerOne Plus',[379.4,407.3],[285,306]),('EnerC Plus',[3720,4070],[280,306])]:
        for energy,cell in zip(energies,capacities):
            products.append(battery('catl-'+family.lower().replace(' ','-')+'-'+str(cell),'CATL',family+' '+str(cell)+'Ah',energy,None,
                'CATL-ESS-202406.pdf '+('p17' if family=='EnerOne Plus' else'p16'),
                cell_capacity_Ah=cell,voltage_nominal_DC_V=1361.2 if family=='EnerOne Plus' else 1331.2,
                optional_cycle_claim='up to12000cycles for optionalcells;not guaranteed for everyconfiguration',
                reliability_claim='20yearreliability claim,not a verifiedconstantcapacitylifetime/warranty',
                scope='DCbatteryunit;no same-sheetPCS power,DoD,ACefficiency or sitecost'))
    # Manufacturer sheet independently retrieved from the government filing cited by CU.
    for hours,energy,power,rte,kva in [(2,3854,1927,.920,2400),(4,3916,979,.937,1320)]:
        products.append(battery(f'tesla-megapack2xl-{hours}h','Tesla',f'Megapack2XL {hours}-hour (Rev1.5.1,2023)',energy,power,
            'Tesla-Megapack2XL-20230210.pdf p1,CU source lead independently retrieved2026-11-10',
            roundtrip_AC=dict(value=rte,conditions='full-depth cycle at25C',
                boundary='includes product power conversion and thermal system losses; external site MV transformer not explicitly covered'),
            warranty_years=dict(standard=15,optional=20,coverage='equipment and energy retention;retention curve not published in this sheet'),
            ambient_temperature_C=[-30,50],apparent_power_kVA=kva,
            inverter_apparent_configuration=dict(minimum_kVA=400,step_kVA=50),
            nominal_AC_voltage_V=480,
            cell_chemistry='not stated in retained sheet;do not silently assign LFP/NMC life',
            course_scope='2-hour reference-compatible' if hours==2 else'4-hour extension',
            site_interface='480VAC product interface requires matched UKsite transformer/grid equipment',
            scope='integrated product;published nominal energy,allowed DoD/usable energy and external connection efficiency require declared assumptions'))
    # ITM values: outputs/power names are rounded; source flow and e are retained.
    itm=[('neptune-ii','NEPTUNE II',2,35,57,.25,'neptune-2.pdf',30,'<5ppmH2O,<5ppmO2'),
         ('neptune-v','NEPTUNE V',5,90,55.9,.125,'neptune-5.pdf',30,'<5ppmH2O,<5ppmO2'),
         ('poseidon','POSEIDON',20,360,55.9,.20,'ITM-Poseidon20-2-7.pdf',31,'fullysaturatedwithtraceO2'),
         ('alpha50','ALPHA50',50,900,55.9,.125,'alpha-50.pdf',30,'<5ppmH2O,<5ppmO2')]
    for slug,name,mw,q,e,minimum,file,pressure,purity in itm:
        rec=electrolyser('itm-'+slug,'ITM',name,'PEM',mw,q,e,minimum,file+' p2',
            operating_range_basis='operating range of installed/online reference product as specified',
            ambient_temperature_C=[-20,40 if slug=='neptune-ii' else 45],
            water_flow_status='Input water quality is stated; no numerical water-consumption rate published in retained product sheet',
            outlet_pressure_barg=pressure,base_purity=purity,water_quality='DI forPOSEIDON;potableinput forotherfullscopepackages',
            ramp=dict(up_fraction_per_second=.10,down_fraction_per_second=.50),
            scope='POSEIDONcoremodulewithoptionalBoP;systemenergyalreadyincludesBoP' if slug=='poseidon'
                  else'fullsystemenergyatBoL;suppliedpackage and siteinstallationcoststilldistinct')
        if slug in ('neptune-v','alpha50'):
            rec['public_prices'].append(dict(currency='EUR',value=5_000_000 if slug=='neptune-v' else 50_000_000,
                  price_basis='manufactureradvertisedprice subjecttostandardterms',price_year=None,
                  observed_at='2026-11-10',source='pages-08.json',scope='suppliedpackage;not verifiedsite-totalcost'))
        products.append(rec)
    for count,mw,q,e,minimum,file in [(250,1.25,531/24,59.,.10,'Nel-MC-Series-RevJ.pdf'),
                  (500,2.5,1062/24,57.3,.10,'Nel-MC-Series-RevJ.pdf'),
                  (1000,5,2124/24,56.77,.20,'Nel-MC-Modular-RevA.pdf'),
                  (2000,10,4248/24,56.77,.20,'Nel-MC-Modular-RevA.pdf'),
                  (4000,20,8496/24,56.77,.20,'Nel-MC-Modular-RevA.pdf')]:
        rec=electrolyser('nel-mc'+str(count),'Nel','MC'+str(count),'PEM',mw,q,e,minimum,file+' pp1-2',
            outlet_pressure_barg=30,base_purity=.9995,optional_purity=.99999,
            water_litre_per_kg=15.9,water_quality='potable subjecttositeanalysis;RO/EDIincluded',
            hot_start_seconds=dict(upper=480,source_wording='fromstandby;not proof ofcoldstart'),
            ramp=dict(min_to_full_seconds_upper=15,max_fraction_per_second=.074),
            scope='containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption',
            scope_warning='MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow')
        if count==250:
            rec['public_prices'].append(dict(currency='USD',value=2_000_000,year=2020,
                kind='approximatehistoricalpurchaseorder',scope='1.25MWcontainerandresearchcollaboration;not currentquote',source='pages-09.json:NRELorder'))
        if count==500:
            rec['public_prices'].append(dict(currency='USD',value=3_500_000,year=2025,
                kind='derivedmeanperunitfromtwo-unitUSD7morder',source='pages-09.json:2025-01-21',
                scope='equipmentpurchaseorder;not UKsiteinstallationquote'))
        products.append(rec)
    products.append(electrolyser('nel-a485','Nel','A485','alkaline',2.2,1046/24,None,.15,
        'Nel-A485-Rev03.pdf pp1-2;pages-08.json',nominal_stack_input_kW=(1046/24)*50,
        stack_specific_kWh_per_kg=dict(value=50,tolerance=1.1),outlet_pressure_barg=.03,
        hydrogen_rate_kind='maximum production; source tolerance +0/-3%, not a guaranteed mean',
        base_purity='99+% saturatedwithliquidwater,O2<1%',water_litre_per_kg=10,
        water_quality='DI<1uScm',ramp=dict(min_fraction_per_minute=.10),plant_lifetime_years='20+webclaim;not full-servicewarranty',
        scope='stackandelectrolyteonly;notfullACplant;requiresrectifier,BoP,quality/pressurematching'))
    enapter=[('flex120','AEM Flex120',.120,2.16,112.,.12,19.4,'Enapter-Flex120-202606.pdf',3.),
             ('nexus500','AEM Nexus500',.5,9.1,467.,.17,81.5,'Enapter-Nexus500-202606.pdf',12.),
             ('nexus1000','AEM Nexus1000',1.,18.2,933.2,.085,163.,'Enapter-Nexus1000-202606.pdf',12.),
             ('nexus2500','AEM Nexus2500',2.5,44.2,2266.,.10,396.,'Enapter-Nexus2500-202606.pdf',18.),
             ('rheos20','AEM Rheos20',20.,362.,18590.,.01,3242.,'Enapter-Rheos20-202606.pdf',None)]
    for slug,name,mw,q,p,minimum,water,file,dryer in enapter:
        rec=electrolyser('enapter-'+slug,'Enapter',name,'AEM',mw,q,51.4 if slug=='rheos20' else 51.3,minimum,file+' p2rev08(2026-06-15)',
            nominal_system_input_kW=p,outlet_pressure_barg=31,base_purity=.99999 if slug=='rheos20' else.995,
            optional_purity=None if slug=='rheos20' else.99999,additional_purification_kW=dryer,
            water_litre_per_kg=water/q,water_quality='TypeIIpurifiedwater;rawrequirementdependsontreatment',
            hot_start_seconds=225 if slug!='rheos20' else None,
            scope='systemBoLfull-loadbasegradeincludesutilitiesinsidebatterylimits',
            efficiency_conditions='55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata',
            startup_warning='225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee')
        if slug=='nexus2500':
            rec['technical'].update(minimum_transient_flow_fraction=.035,transient_limit_hours=24,
                minimum_steady_flow_fraction=.10,low_load_rule='3.5-10%atmost24h;then10-100%;shutdown/reset details require confirmation;notconstant3.5%forever')
        if slug=='rheos20':
            rec['technical']['scope']='full-scopeplant,includingpurificationto99.999%,transformers,rectifiers,waterconditioning'
        products.append(rec)
    # Derive transparent core-model views; the original observations stay above.
    for rec in products:
        t=rec['technical']; kind=rec['type']
        if kind=='battery':
            needed=['usable_energy_kWh','nominal_AC_power_kW','roundtrip_AC']
            missing=[k for k in needed if t.get(k) is None]
            view=dict(energy_kWh=t.get('usable_energy_kWh'),rated_AC_kW=t.get('nominal_AC_power_kW'),
                      roundtrip=t.get('roundtrip_AC'),loss_boundary='ACreferencepoint,ifprovided',
                      missing_core_fields=missing)
            if not missing:
                view['reference_ready']='bounded/performance-referencepoint study only;do not treat maxima asaverage'
            else:
                view['reference_ready']='requires stated engineering assumptions or more supplier evidence'
        else:
            needed=['hydrogen_kg_per_hour','system_specific_kWh_per_kg','minimum_steady_flow_fraction']
            missing=[k for k in needed if t.get(k) is None]
            view=dict(hydrogen_kg_day=t['hydrogen_kg_per_hour']*24,
                      system_kWh_kg=t.get('system_specific_kWh_per_kg'),
                      full_load_input_MWh_day=t['nominal_system_input_kW']*24/1000 if t.get('nominal_system_input_kW') else None,
                      minimum_flow_fraction=t.get('minimum_steady_flow_fraction'),missing_core_fields=missing,
                      reference_ready='nominal-point operating study;investment needslifecycle/cost assumptions' if not missing
                                      else'not a complete ACplantcandidate')
        rec['model_view']=view
        rec['readiness']=dict(unconditional_full_investment_ready=False,
            technical_reference_core_known=not bool(view['missing_core_fields']),
            reason='No product has a complete public siteinstalledprice+lifecycle+all-dutycontract;see per-field gaps and research-only proxysets')
        write(ROOT/'products'/(rec['id']+'.json'),rec)
    write(ROOT/'catalogue.json',dict(as_of='2026-11-10',products=products,
        principle='Manufacturer observations, derived nominal ratios, engineering references and model protocols remain distinct',
        counts=dict(battery=sum(p['type']=='battery' for p in products),electrolyser=sum(p['type']=='electrolyser' for p in products))))
    fields=['id','type','manufacturer','model','energy_kWh','AC_power_kW','H2_kg_day','system_kWh_kg','minimum_steady_fraction','core_reference_known','unconditional_investment_ready']
    with (ROOT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for rec in products:
            t=rec['technical'];writer.writerow(dict(id=rec['id'],type=rec['type'],manufacturer=rec['manufacturer'],model=rec['model'],
                energy_kWh=t.get('nominal_energy_kWh'),AC_power_kW=t.get('nominal_AC_power_kW'),
                H2_kg_day=t['hydrogen_kg_per_hour']*24 if rec['type']=='electrolyser' else None,
                system_kWh_kg=t.get('system_specific_kWh_per_kg'),minimum_steady_fraction=t.get('minimum_steady_flow_fraction'),
                core_reference_known=rec['readiness']['technical_reference_core_known'],unconditional_investment_ready=False))
    print('CATALOGUE',len(products),'products;',sum(p['type']=='battery' for p in products),'battery;',sum(p['type']=='electrolyser' for p in products),'electrolyser')
    return products


if __name__=='__main__':
    build()
