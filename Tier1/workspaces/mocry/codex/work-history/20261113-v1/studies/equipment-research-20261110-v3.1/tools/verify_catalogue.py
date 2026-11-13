"""Check units, source locators, model gates and source-derived quantities."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run():
    data=json.loads((ROOT/'catalogue.json').read_text(encoding='utf-8'))
    records=data['products'];assert len({x['id'] for x in records})==len(records)
    assert len({x['manufacturer'] for x in records if x['type']=='battery'})>=3
    assert len({x['manufacturer'] for x in records if x['type']=='electrolyser'})>=3
    notes=[]
    for rec in records:
        technical=rec['technical']
        assert (ROOT/'products'/(rec['id']+'.json')).exists()
        assert rec['source'] and rec['readiness']['unconditional_full_investment_ready'] is False
        if rec['type']=='battery':
            assert technical['nominal_energy_kWh']>0
            if technical.get('permitted_DoD') is not None:
                assert 0<technical['permitted_DoD']<=1
                assert abs(technical['usable_energy_kWh']-technical['nominal_energy_kWh']*technical['permitted_DoD'])<1e-8
            if technical['nominal_AC_power_kW'] is None:
                assert not rec['readiness']['technical_reference_core_known']
        elif technical['system_specific_kWh_per_kg'] is not None:
            q=technical['hydrogen_kg_per_hour'];power=technical['nominal_system_input_kW']
            assert q>0 and power>0
            error=abs(power/q-technical['system_specific_kWh_per_kg'])/technical['system_specific_kWh_per_kg']
            assert error<.025,(rec['id'],error)
            if abs(power/1000-technical['marketing_class_MW'])/technical['marketing_class_MW']>.02:
                notes.append(dict(id=rec['id'],marketing_MW=technical['marketing_class_MW'],
                                  source_or_derived_input_MW=power/1000,
                                  interpretation='Keep source input/flow;marketing label is not exact input power'))
    nexus=next(x for x in records if x['id']=='enapter-nexus2500')['technical']
    assert nexus['minimum_transient_flow_fraction']==.035 and nexus['minimum_steady_flow_fraction']==.1 and nexus['transient_limit_hours']==24
    assert next(x for x in records if x['id']=='nel-a485')['technical']['system_specific_kWh_per_kg'] is None
    assert next(x for x in records if x['id']=='itm-poseidon')['technical']['base_purity']=='fullysaturatedwithtraceO2'
    assert next(x for x in records if x['id']=='catl-enerone-plus-285')['technical']['voltage_nominal_DC_V']==1361.2
    assert next(x for x in records if x['id']=='catl-enerc-plus-280')['technical']['voltage_nominal_DC_V']==1331.2
    refs=json.loads((ROOT/'reference_scenarios.json').read_text(encoding='utf-8'))
    assert refs['battery']['DoD_life_reference']['primary_terminal_capacity_fraction']==.8
    assert refs['battery']['DoD_life_reference']['secondary_terminal_capacity_fraction']==.6
    study=json.loads((ROOT/'STUDY_INPUTS.json').read_text(encoding='utf-8'))
    assert study['primary_candidates']==len(study['profiles'])==12 and study['no_automatic_merge']
    assert len({x['id'] for x in study['profiles']})==12
    for x in study['profiles']:
        assert (ROOT/x['facts_record']).is_file()
        d=x['electrical']; c=x['costs']
        assert c['currency'] and c['price_year']==2020 and x['field_sources']
        if x['kind']=='battery':
            assert math.isclose(d['eta_charge']*d['eta_discharge'],d['roundtrip_AC'])
            assert 0<d['study_DoD']<=d['permitted_DoD']
            assert math.isclose(d['usable_energy_kWh'],d['nominal_energy_kWh']*d['study_DoD'])
            assert math.isclose(c['installed_reference'],245*d['nominal_energy_kWh']+86*d['charge_AC_kW'])
            assert d['standby_kW']>=0 and 0<=d['self_discharge_fraction_day']<1
        else:
            assert math.isclose(d['H2_kg_day'],24*d['H2_kg_hour'])
            assert math.isclose(d['full_load_MWh_day'],d['H2_kg_day']*d['system_kWh_kg']/1000)
            assert 0<d['minimum_online_fraction']<=1
            for level in ('low','central','high'):
                assert all(v>0 for v in c['packages'][level].values())
    sources=json.loads((ROOT/'SOURCES.json').read_text(encoding='utf-8'))
    for s in sources['files']:
        assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256']
        assert s['url'].startswith('https://')
    coverage=list(csv.DictReader((ROOT/'field_coverage.csv').open(encoding='utf-8-sig',newline='')))
    assert len(coverage)==sum(len(x['technical']) for x in records)
    broken=[]
    for md in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            if not (md.parent/target.split('#')[0]).exists():broken.append([md.name,target])
    assert not broken,broken
    ready=sum(x['readiness']['technical_reference_core_known'] for x in records)
    report=dict(products=len(records),counts=data['counts'],
                battery_brands=sorted({x['manufacturer'] for x in records if x['type']=='battery'}),
                electrolyser_brands=sorted({x['manufacturer'] for x in records if x['type']=='electrolyser'}),
                nominal_operating_reference_core_known=ready,
                unconditional_full_investment_ready=0,
                declared_daily_reference_profiles=len(study['profiles']),
                field_coverage_records=len(coverage),
                raw_documents_hashed=len(sources['files']),
                local_markdown_links_checked=True,
                visual_review=dict(pages=21,status='v3fourteenpages plusTesla,PNNL43-44,DEA180-181,DESNZ36-37 inspected',
                    correction='CATLEnerOnePlus1361.2V differs from EnerCPlus1331.2V; catalogue corrected before release'),
                power_definition_warnings=notes,
                findings='Raw unknowns remain null;public references and engineering scenarios do not overwrite manufacturer fields.')
    (ROOT/'QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':run()
