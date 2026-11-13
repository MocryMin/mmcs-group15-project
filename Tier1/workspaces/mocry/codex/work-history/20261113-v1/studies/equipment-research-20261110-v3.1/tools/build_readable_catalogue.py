import csv
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LABELS={
'nominal_energy_kWh':'名义容量（kWh）','usable_energy_kWh':'厂家允许深度对应可用容量（kWh）',
'nominal_AC_power_kW':'额定交流功率（kW）','max_AC_charge_power_kW':'最大交流充电功率（kW）',
'max_AC_discharge_power_kW':'最大交流放电功率（kW）','battery_DC_charge_power_kW':'电池部分充电功率（kW）',
'battery_DC_discharge_power_kW':'电池部分放电功率（kW）','permitted_DoD':'厂家允许放电深度',
'normalized_SOC_operating_range':'对可用容量归一化的库存范围','roundtrip_AC':'交流往返效率及条件',
'roundtrip_DC':'直流往返效率及条件','one_way_efficiencies':'分别披露的单程效率',
'auxiliary_active_kW':'运行辅助功率（kW）','auxiliary_standby_kW':'待机辅助功率（kW）',
'self_discharge_per_day':'每日储存损耗','lifetime_years':'日历寿命（年）','cycle_life':'循环寿命及限定',
'EOL_SOH':'寿命终点健康状态','degradation_curve':'衰减曲线','availability':'可用率',
'parallel_limit':'并机数及适用边界','scope':'测量/供应范围','usable_definition':'可用容量定义',
'auxiliary_duty_reference':'辅助能耗的参考运行工况','lifetime_conditions':'寿命工况',
'marketed_energy_kWh':'名称中的容量（kWh）','rating_issue':'额定边界待确认事项',
'PCS_efficiency_max':'变流器最高效率','auxiliary_supply':'辅助供电方式','maintenance':'维护',
'apparent_power_kVA':'额定视在功率（kVA）','course_scope':'与课程时长参考的关系',
'auxiliary_supply_rating_kW_upper':'辅助电源额定上限（kW）','auxiliary_warning':'辅助负荷计量注意',
'PCS_model':'配套PCS型号','cell_capacity_Ah':'电芯配置（Ah）','voltage_nominal_DC_V':'额定直流电压（V）',
'optional_cycle_claim':'可选电芯循环宣传的边界','reliability_claim':'可靠性表述的边界',
'technology':'电解技术','marketing_class_MW':'产品MW等级',
'hydrogen_kg_per_hour':'产氢率（kg/h）','system_specific_kWh_per_kg':'整机比电耗（kWh/kg）',
'nominal_system_input_kW':'名义整机输入（kW）','nominal_stack_input_kW':'电堆输入（kW）',
'minimum_flow_fraction':'最低在线比例','minimum_transient_flow_fraction':'暂态最低比例',
'transient_limit_hours':'暂态持续时间上限（h）','minimum_steady_flow_fraction':'长期稳态最低比例',
'operating_range_basis':'运行范围所指对象','outlet_pressure_barg':'出口压力（barg）',
'base_purity':'基本气质','optional_purity':'可选气质','additional_purification_kW':'额外净化功率（kW）',
'water_litre_per_kg':'水耗（L/kg）','water_quality':'水质/原水或纯水边界','ramp':'爬坡',
'hot_start_seconds':'热启动（秒）','cold_start_seconds':'冷启动（秒）','standby_kW':'待机功率（kW）',
'minimum_up_time_hours':'最小连续运行（h）','minimum_down_time_hours':'最小连续停机（h）',
'stack_lifetime_hours':'电堆寿命（h）','plant_lifetime_years':'工厂寿命（年）',
'replacement_cost':'替换成本','power_origin':'输入功率是否推导',
'nominal_power_to_flow_ratio_kWh_per_kg':'名义输入/产出比（kWh/kg）',
'nominal_power_consistency_relative_error':'公开输入与比电耗乘产量的舍入差异',
'stack_specific_kWh_per_kg':'电堆比电耗（kWh/kg）','efficiency_conditions':'效率工况',
'startup_warning':'启动边界','low_load_rule':'特殊低负荷规则','warranty_years':'质保年限及性质',
'ambient_temperature_C':'环境温度范围（°C）','derating_above_C':'开始降额温度（°C）',
'water_flow_status':'数值水耗的披露情况','hydrogen_rate_kind':'产氢率的最大/额定性质',
}

def fmt(x):
    if x is None:return '未取得；不自动填零'
    if isinstance(x,(dict,list)):return json.dumps(x,ensure_ascii=False,sort_keys=True).replace('|','/').replace('\n',' ')
    return str(x).replace('|','/').replace('\n',' ')

def build():
    ps=json.loads((ROOT/'catalogue.json').read_text(encoding='utf-8'))['products']
    src=json.loads((ROOT/'SOURCES.json').read_text(encoding='utf-8'))
    files=sorted(src['files'],key=lambda x:len(Path(x['file']).name),reverse=True)
    docs=['# 逐产品参数卡片\n\n日期：2026-11-10。事实、推导、估计和研究协议分开保存；主说明见[调研报告](REPORT_ZH.md)。未取得项可由明确的行业情景补充，不能冒作厂商数据。\n']
    coverage=[]
    selected={x['id'] for x in json.loads((ROOT/'STUDY_INPUTS.json').read_text(encoding='utf-8'))['profiles']}
    for p in ps:
        lines=[f"## {p['manufacturer']} — {p['model']}",f"ID：`{p['id']}`。类型：{p['type']}。",f"来源定位：{p['source']}。"]
        links=[f"[{Path(s['file']).name}]({s['file']})（[原网址]({s['url']})）" for s in files if Path(s['file']).name in p['source']]
        lines.append('原件：'+'；'.join(links)+'。')
        lines.append('研究情景：'+('已列入[STUDY_INPUTS](STUDY_INPUTS.json)。' if p['id'] in selected else'保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。'))
        lines+=['\n| 指标 | 原始记录、条件或限定 |','|---|---|']
        for k,v in p['technical'].items():
            lines.append(f"| {LABELS.get(k,k)} | {fmt(v)} |")
            coverage.append(dict(id=p['id'],manufacturer=p['manufacturer'],model=p['model'],field=k,
                field_ZH=LABELS.get(k,k),public_record_status='not_obtained' if v is None else'recorded_with_qualifiers',
                value='' if v is None else fmt(v),source=p['source'],has_study_profile=p['id'] in selected))
        lines+=['\n价格证据：'+(fmt(p['public_prices']) if p['public_prices'] else'未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。'),
                '\n模型接入：'+fmt(p['model_view']), '\n公共资料剩余项：'+'；'.join(p['general_gaps'])+'。','']
        docs.append('\n\n'.join(lines))
    (ROOT/'PRODUCT_CARDS_ZH.md').write_text('\n\n'.join(docs)+'\n',encoding='utf-8')
    with (ROOT/'field_coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    print('Readable catalogue',len(ps),'cards;',len(coverage),'field records')

if __name__=='__main__':build()
