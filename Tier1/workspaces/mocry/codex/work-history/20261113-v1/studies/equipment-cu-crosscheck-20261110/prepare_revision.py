"""Prepare v3.1 without changing the delivered v3 snapshot."""
from pathlib import Path
import shutil

BASE=Path(__file__).resolve().parent
OLD=BASE.parent/'equipment-research-20261110-v3'
NEW=BASE.parent/'equipment-research-20261110-v3.1'

def replace(path,old,new):
    text=path.read_text(encoding='utf-8')
    assert old in text,(path.name,old)
    path.write_text(text.replace(old,new),encoding='utf-8')

def run():
    assert OLD.is_dir() and not NEW.exists()
    shutil.copytree(OLD,NEW,ignore=shutil.ignore_patterns('__pycache__','MANIFEST.json'))
    for name in ['Tesla-Megapack2XL-20230210.pdf','PNNL-Cost-Performance-2022.pdf',
                 'DESNZ-Hydrogen-Transport-Storage2023.pdf','DEA-Storage-Catalogue2025.pdf']:
        shutil.copy2(BASE/'evidence'/name,NEW/'evidence'/name)
    for p in (BASE/'evidence'/'visual').glob('*.png'):
        shutil.copy2(p,NEW/'evidence'/'visual'/p.name)
    shutil.copy2(BASE/'REVIEW_ZH.md',NEW/'CU_CROSSCHECK.md')
    replace(NEW/'CU_CROSSCHECK.md','本地`evidence/Tesla-Megapack2XL-20230210.pdf`','本地[evidence原件](evidence/Tesla-Megapack2XL-20230210.pdf)')
    p=NEW/'tools'/'build_catalogue.py'
    replace(p,'    # ITM values: outputs/power names are rounded; source flow and e are retained.',
'''    # Manufacturer sheet independently retrieved from the government filing cited by CU.
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
    # ITM values: outputs/power names are rounded; source flow and e are retained.''')
    p=NEW/'tools'/'build_reference_scenarios.py'
    replace(p,'DoD_life_reference=dict(primary_DoD=.8,cycles_at_primary=2400,secondary_DoD=.6,',
        'DoD_life_reference=dict(primary_DoD=.8,cycles_at_primary=2400,primary_terminal_capacity_fraction=.8,secondary_DoD=.6,')
    replace(p,'cycles_at_secondary=8000,calendar_years=16,EOL_SOH=.6,',
        'cycles_at_secondary=8000,secondary_terminal_capacity_fraction=.6,calendar_years=16,EOL_SOH=.6,')
    replace(p,"source='PNNL Database H6747:H6752;not supplier-specific'",
        "source='PNNL Database H6747:H6752 plus2022report printedpp19-22:2400cycles at80%DoD reaches80%remaining energy;ultimateEOL60%;not supplier-specific'")
    replace(p,"scope='generic3MWh/1.5MW reference;transfer to other vendors/sizes requires explicit scenario label',",
        "scope='generic3MWh/1.5MW reference;transfer to other vendors/sizes requires explicit scenario label',\n"+
        "            alternative_component_reconstruction=dict(formula_EUR2020='1.10*(228000*E_MWh+86000*P_MW)',two_hour_cost_EUR_MWh=298100,source='DEA cataloguePDF pp180-181 Tables8/10,CU lead independently checked'),")
    p=NEW/'tools'/'build_study_inputs.py'
    replace(p,'cycle_reference=2400,cycle_reference_DoD=.8,EOL_SOH=.60,',
        'cycle_reference=2400,cycle_reference_DoD=.8,cycle_reference_terminal_capacity_fraction=.80,EOL_SOH=.60,')
    replace(p,'alternative_depth_life=dict(study_DoD=.6,cycles=8000,usable_energy_kWh=.6*E)',
        'alternative_depth_life=dict(study_DoD=.6,cycles=8000,terminal_capacity_fraction=.6,usable_energy_kWh=.6*E)')
    replace(p,'PNNL H6748:H6752:80%/2400 or60%/8000; not a product-specific cycle guarantee',
        'PNNL H6748:H6752 plus2022report Table4.3:80%DoD/2400 reaches80%remaining capacity;60%/8000 reaches60%;not a product-specific guarantee')
    p=NEW/'tools'/'build_sources.py'
    replace(p,'URLS={',"""URLS={
'Tesla-Megapack2XL-20230210.pdf':'https://portal.ct.gov/-/media/csc/3_petitions-medialibrary/petitions_medialibrary/mediapetitionnos1601-1700/pe1607/petitionersubmissions/supplement-attachment-a---megapack_2_xl_datasheet.pdf',
'PNNL-Cost-Performance-2022.pdf':'https://www.pnnl.gov/sites/default/files/media/file/ESGC%20Cost%20Performance%20Report%202022%20PNNL-33283.pdf',
'DESNZ-Hydrogen-Transport-Storage2023.pdf':'https://assets.publishing.service.gov.uk/media/659e600b915e0b00135838a6/hydrogen-transport-and-storage-cost-report.pdf',
'DEA-Storage-Catalogue2025.pdf':'https://ens.dk/media/6588/download',""")
    replace(p,"('BEIS','DEA','PNNL','IRENA')","('BEIS','DEA','PNNL','IRENA','DESNZ')")
    p=NEW/'tools'/'verify_catalogue.py'
    replace(p,'visual_review=dict(pages=14,','visual_review=dict(pages=21,')
    replace(p,"status='rendered and inspected:manufacturer tables, Nexus2500duration footnote, CATLvariant/voltage columns, Huaweiauxiliary ratings'",
        "status='v3fourteenpages plusTesla,PNNL43-44,DEA180-181,DESNZ36-37 inspected'")
    replace(p,"study=json.loads((ROOT/'STUDY_INPUTS.json').read_text(encoding='utf-8'))",
        "refs=json.loads((ROOT/'reference_scenarios.json').read_text(encoding='utf-8'))\n    assert refs['battery']['DoD_life_reference']['primary_terminal_capacity_fraction']==.8\n    assert refs['battery']['DoD_life_reference']['secondary_terminal_capacity_fraction']==.6\n    study=json.loads((ROOT/'STUDY_INPUTS.json').read_text(encoding='utf-8'))")
    replace(NEW/'tools'/'package_research.py','MMCS_Equipment_Research_20261110_v3.zip','MMCS_Equipment_Research_20261110_v3_1.zip')
    for name in ['REPORT_ZH.md','README.md']:
        p=NEW/name
        text=p.read_text(encoding='utf-8').replace('12个电池配置','14个电池配置').replace('4家电池供应商','5家电池供应商').replace('全部27个配置','全部29个配置')
        text=text.replace('Tier1设备调研 v3','Tier1设备调研 v3.1').replace('TESVOLT/Sungrow/Huawei/CATL','TESVOLT/Sungrow/Huawei/CATL/Tesla')
        text=text.replace('所有公开事实、边界、缺项','所有公开事实、边界、缺项')
        p.write_text(text,encoding='utf-8')
    p=NEW/'REPORT_ZH.md'
    replace(p,'原件入口：[TESVOLT TALLON]',
        '| Tesla Megapack2XL，2h（2023版） | 3,854 kWh | 1,927 kW AC | 满深度循环92%，含内部转换/热管理；15年质保可延20年 | 新增竞品，运行深度/容量保证曲线及480V现场连接待匹配 |\n'+
        '| Tesla Megapack2XL，4h（2023版） | 3,916 kWh | 979 kW AC | 相同工况93.7%；同样质保范围 | 4小时扩展，原厂文件版本单列 |\n\n'+
        '原件入口：[Tesla Megapack2XL](evidence/Tesla-Megapack2XL-20230210.pdf)、[TESVOLT TALLON]')
    replace(p,'PNNL同一组数据中，80%DoD对应2,400循环，60%DoD对应8,000循环，日历16年，寿命终点SOH60%。',
        'PNNL的80%DoD/2,400循环对应剩余容量约80%的阶段；60%DoD/8,000循环对应剩余容量60%。最终EOL60%与前一阶段不可混为同一终点，日历参考16年。该含义已对照[2022完整报告第43–44页](evidence/PNNL-Cost-Performance-2022.pdf)核实。')
    replace(p,'研究日期：2026-11-10。',
        '版本v3.1：补入CU来源的Tesla两配置，纠正PNNL循环终点，保留v3原包。详[CU交叉核查](CU_CROSSCHECK.md)。\n\n研究日期：2026-11-10。')
    replace(NEW/'MODELLING_INTERFACE.md','PNNL示例中的80%DoD/2400循环与60%DoD/8000循环是两组配套数据。',
        'PNNL示例中的80%DoD/2400循环达到约80%剩余容量，60%DoD/8000循环达到60%剩余容量；两组终点也不同，不能都配到最终EOL60%。')
    p=NEW/'README.md'
    replace(p,'先读[中文调研报告](REPORT_ZH.md)。',
        'v3.1保留v3原件，补入CU的Tesla来源并修正循环寿命终点。增益与未采用项见[CU交叉核查](CU_CROSSCHECK.md)。\n\n先读[中文调研报告](REPORT_ZH.md)。')
    print('Prepared v3.1; v3 directory and archive unchanged')

if __name__=='__main__':run()
