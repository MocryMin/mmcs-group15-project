# 逐产品参数卡片

日期：2026-11-10。事实、推导、估计和研究协议分开保存；主说明见[调研报告](REPORT_ZH.md)。未取得项可由明确的行业情景补充，不能冒作厂商数据。


## TESVOLT — TALLON

ID：`tesvolt-tallon`。类型：battery。

来源定位：TESVOLT-TALLON.pdf p1, revisionRD.TI.150.E.de-DE B.01。

原件：[TESVOLT-TALLON.pdf](evidence/TESVOLT-TALLON.pdf)（[原网址](https://www.tesvolt.com/_media/02%20PRODUKTE/11_Tallon/TESVOLT_TALLON-Technisches_Datenblatt-DE.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 5015 |

| 厂家允许深度对应可用容量（kWh） | 5015.0 |

| 额定交流功率（kW） | 2500 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 1.0 |

| 对可用容量归一化的库存范围 | [0, 1] |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | {"boundary": "DC connection point", "points": [{"efficiency": 0.937, "rate_Cp": 0.5}, {"efficiency": 0.952, "rate_C": 0.25}]} |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | {"peak": 36, "typical25C": 23, "typical45C": 33} |

| 待机辅助功率（kW） | {"kind": "stated standby", "value": 2} |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 15 |

| 循环寿命及限定 | 11000 |

| 寿命终点健康状态 | 0.6 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | {"kind": "combined product/performance, purchase terms control", "optional": 20, "standard": 15} |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-30, 55] |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DC battery container;needs matchingPCS and AC-system boundary |

| 辅助能耗的参考运行工况 | {"annual_MWh": 63.51, "cycles_day": 1.5, "warning": "not additive to all other auxiliary figures"} |

| 寿命工况 | average2cycles/day,100%DoD,max0.5Cp;optional20yearwarranty not automatic20yearconstantcapacity |

| 可用容量定义 | Derived within the manufacturer-defined permitted depth;not chemical-cell absolute0-100%. |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": 5015.0, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["roundtrip_AC"], "rated_AC_kW": 2500, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## TESVOLT — POWERCORE G2 IA-250kW/500kWh

ID：`tesvolt-powercore-g2`。类型：battery。

来源定位：TESVOLT-POWERCORE-G2.pdf p2; manufacturer product pageFAQ retained inlegacy sources。

原件：[TESVOLT-POWERCORE-G2.pdf](evidence/TESVOLT-POWERCORE-G2.pdf)（[原网址](https://www.tesvolt.com/_media/02%20PRODUKTE/12_Forton_XL_PCG2/PC-G2_datasheet_Tesvolt.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 509 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 250 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 244 |

| 电池部分放电功率（kW） | 254.8 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | {"conditions": "manufacturerFAQ:configurationandoperatingconditions", "maximum_approx": 0.92} |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | {"kind": "webpage>10000 cycles", "value": 10000} |

| 寿命终点健康状态 | {"at_year": 10, "kind": "webpage reference;detailed duty/contract not verified", "lower": 0.7} |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-20, 55] |

| 开始降额温度（°C） | 45 |

| 测量/供应范围 | battery plusPCS, but usable depth and rating boundaries not fully published |

| 名称中的容量（kWh） | 500 |

| 额定边界待确认事项 | Battery section and250kWACrating cannot be equated without conversion/boundary confirmation |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh"], "rated_AC_kW": 250, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": {"conditions": "manufacturerFAQ:configurationandoperatingconditions", "maximum_approx": 0.92}}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Sungrow — PowerStack ST255CS-2H

ID：`sungrow-st255cs-2h`。类型：battery。

来源定位：Sungrow-PowerStack255CS.pdf pp1-2V2(2025);pages-04.json;user manual。

原件：[Sungrow-PowerStack255CS.pdf](evidence/Sungrow-PowerStack255CS.pdf)（[原网址](https://info-support.sungrowpower.com/datasheet-materials/b4f56963-dbd2-4c43-8cbc-0808eb4cf083.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 257 |

| 厂家允许深度对应可用容量（kWh） | 257.0 |

| 额定交流功率（kW） | 125 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 1.0 |

| 对可用容量归一化的库存范围 | [0, 1] |

| 交流往返效率及条件 | {"kind": "productpage states consistentlyover90%;not a mean or point", "lower_exclusive": 0.9} |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | {"boundary": "one system group;not a global investment cap", "off_grid": 10, "on_grid": 25} |

| 环境温度范围（°C） | [-30, 50] |

| 开始降额温度（°C） | 45 |

| 测量/供应范围 | integratedACBESS, approximately2-hourclass |

| 变流器最高效率 | 0.985 |

| 辅助供电方式 | internal bydefault;external optional;quantified draw unpublished |

| 维护 | Usermanualp93:yearlyinspection and cell replacement when needed;no numeric service life guarantee |

| 可用容量定义 | Derived within the manufacturer-defined permitted depth;not chemical-cell absolute0-100%. |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": 257.0, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": [], "rated_AC_kW": 125, "reference_ready": "bounded/performance-referencepoint study only;do not treat maxima asaverage", "roundtrip": {"kind": "productpage states consistentlyover90%;not a mean or point", "lower_exclusive": 0.9}}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Sungrow — PowerTitan2.0 ST5015kWh-2500kW-2h

ID：`sungrow-powertitan2-2h`。类型：battery。

来源定位：Sungrow-PowerTitan2-2H4H-V3.pdf pp1-2V3(2023)。

原件：[Sungrow-PowerTitan2-2H4H-V3.pdf](evidence/Sungrow-PowerTitan2-2H4H-V3.pdf)（[原网址](https://info-support.sungrowpower.com/application/pdf/2024/02/21/DS_20230925_ST5015kWh-2500kW-2h_1250kW-4h_V3_EN.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 5015 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 2500 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-30, 50] |

| 开始降额温度（°C） | 45 |

| 测量/供应范围 | integratedACblock;DoD and ACroundtrip not stated in retained sheet |

| 额定视在功率（kVA） | 2520 |

| 与课程时长参考的关系 | 2-hourreference |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "roundtrip_AC"], "rated_AC_kW": 2500, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Sungrow — PowerTitan2.0 ST5015kWh-1250kW-4h

ID：`sungrow-powertitan2-4h`。类型：battery。

来源定位：Sungrow-PowerTitan2-2H4H-V3.pdf pp1-2V3(2023)。

原件：[Sungrow-PowerTitan2-2H4H-V3.pdf](evidence/Sungrow-PowerTitan2-2H4H-V3.pdf)（[原网址](https://info-support.sungrowpower.com/application/pdf/2024/02/21/DS_20230925_ST5015kWh-2500kW-2h_1250kW-4h_V3_EN.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 5015 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 1250 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-30, 50] |

| 开始降额温度（°C） | 45 |

| 测量/供应范围 | integratedACblock;DoD and ACroundtrip not stated in retained sheet |

| 额定视在功率（kVA） | 1260 |

| 与课程时长参考的关系 | 4-hourextension;not silently a2-hourcandidate |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "roundtrip_AC"], "rated_AC_kW": 1250, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Huawei — LUNA2000-215-2S10

ID：`huawei-luna215`。类型：battery。

来源定位：Huawei-LUNA215-2S10.pdf p1;pages-12/13.json。

原件：[Huawei-LUNA215-2S10.pdf](evidence/Huawei-LUNA215-2S10.pdf)（[原网址](https://solar.huawei.com/dam/asset/view/135e950d5f0c40ffa317c4cd20554e08.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 215 |

| 厂家允许深度对应可用容量（kWh） | 215.0 |

| 额定交流功率（kW） | 108 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 1.0 |

| 对可用容量归一化的库存范围 | [0, 1] |

| 交流往返效率及条件 | {"kind": "maximumcycleefficiency;not routineaverage", "maximum": 0.913, "test_rate_C": 0.5} |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | {"kind": "standbyupperbound", "upper": 0.15} |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-30, 55] |

| 开始降额温度（°C） | 50 |

| 测量/供应范围 | integratedACBESS;productgrades/revisions keptseparate |

| 辅助电源额定上限（kW） | 5 |

| 辅助负荷计量注意 | 5kW is supply rating,not a constant parasitic load;avoid doublecounting cycleauxiliaries |

| 配套PCS型号 | PCS2000-108K-MB1 |

| 可用容量定义 | Derived within the manufacturer-defined permitted depth;not chemical-cell absolute0-100%. |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": 215.0, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": [], "rated_AC_kW": 108, "reference_ready": "bounded/performance-referencepoint study only;do not treat maxima asaverage", "roundtrip": {"kind": "maximumcycleefficiency;not routineaverage", "maximum": 0.913, "test_rate_C": 0.5}}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Huawei — LUNA2000-241-2S1

ID：`huawei-luna241`。类型：battery。

来源定位：Huawei-LUNA241-2S1.pdf p1;pages-12/13.json。

原件：[Huawei-LUNA241-2S1.pdf](evidence/Huawei-LUNA241-2S1.pdf)（[原网址](https://solar.huawei.com/dam/asset/view/91e4c6e06feb4284a0d71f515288352f.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 241 |

| 厂家允许深度对应可用容量（kWh） | 241.0 |

| 额定交流功率（kW） | 108 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 1.0 |

| 对可用容量归一化的库存范围 | [0, 1] |

| 交流往返效率及条件 | {"kind": "maximumcycleefficiency;not routineaverage", "maximum": 0.913, "test_rate_C": 0.25} |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | {"kind": "standbyupperbound", "upper": 0.15} |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-30, 55] |

| 开始降额温度（°C） | 50 |

| 测量/供应范围 | integratedACBESS;productgrades/revisions keptseparate |

| 辅助电源额定上限（kW） | 5 |

| 辅助负荷计量注意 | 5kW is supply rating,not a constant parasitic load;avoid doublecounting cycleauxiliaries |

| 配套PCS型号 | PCS2000-108K-MB1 |

| 可用容量定义 | Derived within the manufacturer-defined permitted depth;not chemical-cell absolute0-100%. |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": 241.0, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": [], "rated_AC_kW": 108, "reference_ready": "bounded/performance-referencepoint study only;do not treat maxima asaverage", "roundtrip": {"kind": "maximumcycleefficiency;not routineaverage", "maximum": 0.913, "test_rate_C": 0.25}}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## Huawei — LUNA2000-5015-2S

ID：`huawei-luna5015`。类型：battery。

来源定位：Huawei-LUNA5015-2S.pdf p1;PCS213KTL-H0 is a separate component。

原件：[Huawei-LUNA5015-2S.pdf](evidence/Huawei-LUNA5015-2S.pdf)（[原网址](https://solar.huawei.com/dam/asset/view/e9bb9b1319904298949861cb2d7c94ac.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 5015 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 未取得；不自动填零 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 2507.5 |

| 电池部分放电功率（kW） | 2507.5 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DCcontainer,not an integrated2507.5kWACsystem;needsPCS and efficiency closure |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "nominal_AC_power_kW", "roundtrip_AC"], "rated_AC_kW": null, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## CATL — EnerOne Plus 285Ah

ID：`catl-enerone-plus-285`。类型：battery。

来源定位：CATL-ESS-202406.pdf p17。

原件：[CATL-ESS-202406.pdf](evidence/CATL-ESS-202406.pdf)（[原网址](https://www.catl.com/en/uploads/1/file/public/202406/20240624152558_qft6x51t14.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 379.4 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 未取得；不自动填零 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DCbatteryunit;no same-sheetPCS power,DoD,ACefficiency or sitecost |

| 电芯配置（Ah） | 285 |

| 额定直流电压（V） | 1361.2 |

| 可选电芯循环宣传的边界 | up to12000cycles for optionalcells;not guaranteed for everyconfiguration |

| 可靠性表述的边界 | 20yearreliability claim,not a verifiedconstantcapacitylifetime/warranty |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "nominal_AC_power_kW", "roundtrip_AC"], "rated_AC_kW": null, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## CATL — EnerOne Plus 306Ah

ID：`catl-enerone-plus-306`。类型：battery。

来源定位：CATL-ESS-202406.pdf p17。

原件：[CATL-ESS-202406.pdf](evidence/CATL-ESS-202406.pdf)（[原网址](https://www.catl.com/en/uploads/1/file/public/202406/20240624152558_qft6x51t14.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 407.3 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 未取得；不自动填零 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DCbatteryunit;no same-sheetPCS power,DoD,ACefficiency or sitecost |

| 电芯配置（Ah） | 306 |

| 额定直流电压（V） | 1361.2 |

| 可选电芯循环宣传的边界 | up to12000cycles for optionalcells;not guaranteed for everyconfiguration |

| 可靠性表述的边界 | 20yearreliability claim,not a verifiedconstantcapacitylifetime/warranty |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "nominal_AC_power_kW", "roundtrip_AC"], "rated_AC_kW": null, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## CATL — EnerC Plus 280Ah

ID：`catl-enerc-plus-280`。类型：battery。

来源定位：CATL-ESS-202406.pdf p16。

原件：[CATL-ESS-202406.pdf](evidence/CATL-ESS-202406.pdf)（[原网址](https://www.catl.com/en/uploads/1/file/public/202406/20240624152558_qft6x51t14.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 3720 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 未取得；不自动填零 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DCbatteryunit;no same-sheetPCS power,DoD,ACefficiency or sitecost |

| 电芯配置（Ah） | 280 |

| 额定直流电压（V） | 1331.2 |

| 可选电芯循环宣传的边界 | up to12000cycles for optionalcells;not guaranteed for everyconfiguration |

| 可靠性表述的边界 | 20yearreliability claim,not a verifiedconstantcapacitylifetime/warranty |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "nominal_AC_power_kW", "roundtrip_AC"], "rated_AC_kW": null, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## CATL — EnerC Plus 306Ah

ID：`catl-enerc-plus-306`。类型：battery。

来源定位：CATL-ESS-202406.pdf p16。

原件：[CATL-ESS-202406.pdf](evidence/CATL-ESS-202406.pdf)（[原网址](https://www.catl.com/en/uploads/1/file/public/202406/20240624152558_qft6x51t14.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 名义容量（kWh） | 4070 |

| 厂家允许深度对应可用容量（kWh） | 未取得；不自动填零 |

| 额定交流功率（kW） | 未取得；不自动填零 |

| 最大交流充电功率（kW） | 未取得；不自动填零 |

| 最大交流放电功率（kW） | 未取得；不自动填零 |

| 电池部分充电功率（kW） | 未取得；不自动填零 |

| 电池部分放电功率（kW） | 未取得；不自动填零 |

| 厂家允许放电深度 | 未取得；不自动填零 |

| 对可用容量归一化的库存范围 | 未取得；不自动填零 |

| 交流往返效率及条件 | 未取得；不自动填零 |

| 直流往返效率及条件 | 未取得；不自动填零 |

| 分别披露的单程效率 | 未取得；不自动填零 |

| 运行辅助功率（kW） | 未取得；不自动填零 |

| 待机辅助功率（kW） | 未取得；不自动填零 |

| 每日储存损耗 | 未取得；不自动填零 |

| 日历寿命（年） | 未取得；不自动填零 |

| 循环寿命及限定 | 未取得；不自动填零 |

| 寿命终点健康状态 | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 可用率 | 未取得；不自动填零 |

| 并机数及适用边界 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 开始降额温度（°C） | 未取得；不自动填零 |

| 测量/供应范围 | DCbatteryunit;no same-sheetPCS power,DoD,ACefficiency or sitecost |

| 电芯配置（Ah） | 306 |

| 额定直流电压（V） | 1331.2 |

| 可选电芯循环宣传的边界 | up to12000cycles for optionalcells;not guaranteed for everyconfiguration |

| 可靠性表述的边界 | 20yearreliability claim,not a verifiedconstantcapacitylifetime/warranty |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"energy_kWh": null, "loss_boundary": "ACreferencepoint,ifprovided", "missing_core_fields": ["usable_energy_kWh", "nominal_AC_power_kW", "roundtrip_AC"], "rated_AC_kW": null, "reference_ready": "requires stated engineering assumptions or more supplier evidence", "roundtrip": null}


公共资料剩余项：Matched installed price and site scope；Maintenance/renewal/disposal contract；Duty-dependent whole-system performance and degradation, if not explicitly supplied。



## ITM — NEPTUNE II

ID：`itm-neptune-ii`。类型：electrolyser。

来源定位：neptune-2.pdf p2。

原件：[neptune-2.pdf](evidence/neptune-2.pdf)（[原网址](https://itm-power-assets.s3.eu-west-2.amazonaws.com/Neptune_II_Spec_Sheet_2_15_e7016ca8f8.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 2 |

| 产氢率（kg/h） | 35 |

| 整机比电耗（kWh/kg） | 57 |

| 名义整机输入（kW） | 1995 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.25 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.25 |

| 运行范围所指对象 | operating range of installed/online reference product as specified |

| 出口压力（barg） | 30 |

| 基本气质 | <5ppmH2O,<5ppmO2 |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 未取得；不自动填零 |

| 水质/原水或纯水边界 | DI forPOSEIDON;potableinput forotherfullscopepackages |

| 爬坡 | {"down_fraction_per_second": 0.5, "up_fraction_per_second": 0.1} |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-20, 40] |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | fullsystemenergyatBoL;suppliedpackage and siteinstallationcoststilldistinct |

| 数值水耗的披露情况 | Input water quality is stated; no numerical water-consumption rate published in retained product sheet |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 57.0 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 47.88, "hydrogen_kg_day": 840, "minimum_flow_fraction": 0.25, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 57}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## ITM — NEPTUNE V

ID：`itm-neptune-v`。类型：electrolyser。

来源定位：neptune-5.pdf p2。

原件：[neptune-5.pdf](evidence/neptune-5.pdf)（[原网址](https://itm-power-assets.s3.eu-west-2.amazonaws.com/Neptune_V_Spec_Sheet_2_8_a3f68d4e43.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 5 |

| 产氢率（kg/h） | 90 |

| 整机比电耗（kWh/kg） | 55.9 |

| 名义整机输入（kW） | 5031.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.125 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.125 |

| 运行范围所指对象 | operating range of installed/online reference product as specified |

| 出口压力（barg） | 30 |

| 基本气质 | <5ppmH2O,<5ppmO2 |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 未取得；不自动填零 |

| 水质/原水或纯水边界 | DI forPOSEIDON;potableinput forotherfullscopepackages |

| 爬坡 | {"down_fraction_per_second": 0.5, "up_fraction_per_second": 0.1} |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-20, 45] |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | fullsystemenergyatBoL;suppliedpackage and siteinstallationcoststilldistinct |

| 数值水耗的披露情况 | Input water quality is stated; no numerical water-consumption rate published in retained product sheet |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 55.9 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：[{"currency": "EUR", "observed_at": "2026-11-10", "price_basis": "manufactureradvertisedprice subjecttostandardterms", "price_year": null, "scope": "suppliedpackage;not verifiedsite-totalcost", "source": "pages-08.json", "value": 5000000}]


模型接入：{"full_load_input_MWh_day": 120.744, "hydrogen_kg_day": 2160, "minimum_flow_fraction": 0.125, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 55.9}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## ITM — POSEIDON

ID：`itm-poseidon`。类型：electrolyser。

来源定位：ITM-Poseidon20-2-7.pdf p2。

原件：[ITM-Poseidon20-2-7.pdf](evidence/ITM-Poseidon20-2-7.pdf)（[原网址](https://itm-power-assets.s3.eu-west-2.amazonaws.com/POSEIDON_DATA_SHEET_2_7_2e1f89da3f.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 20 |

| 产氢率（kg/h） | 360 |

| 整机比电耗（kWh/kg） | 55.9 |

| 名义整机输入（kW） | 20124.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.2 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.2 |

| 运行范围所指对象 | operating range of installed/online reference product as specified |

| 出口压力（barg） | 31 |

| 基本气质 | fullysaturatedwithtraceO2 |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 未取得；不自动填零 |

| 水质/原水或纯水边界 | DI forPOSEIDON;potableinput forotherfullscopepackages |

| 爬坡 | {"down_fraction_per_second": 0.5, "up_fraction_per_second": 0.1} |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-20, 45] |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | POSEIDONcoremodulewithoptionalBoP;systemenergyalreadyincludesBoP |

| 数值水耗的披露情况 | Input water quality is stated; no numerical water-consumption rate published in retained product sheet |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 55.9 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 482.976, "hydrogen_kg_day": 8640, "minimum_flow_fraction": 0.2, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 55.9}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## ITM — ALPHA50

ID：`itm-alpha50`。类型：electrolyser。

来源定位：alpha-50.pdf p2。

原件：[alpha-50.pdf](evidence/alpha-50.pdf)（[原网址](https://itm-power-assets.s3.eu-west-2.amazonaws.com/14299_ITM_Alpha_Spec_Sheet_1_7_5db44f3d20.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 50 |

| 产氢率（kg/h） | 900 |

| 整机比电耗（kWh/kg） | 55.9 |

| 名义整机输入（kW） | 50310.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.125 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.125 |

| 运行范围所指对象 | operating range of installed/online reference product as specified |

| 出口压力（barg） | 30 |

| 基本气质 | <5ppmH2O,<5ppmO2 |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 未取得；不自动填零 |

| 水质/原水或纯水边界 | DI forPOSEIDON;potableinput forotherfullscopepackages |

| 爬坡 | {"down_fraction_per_second": 0.5, "up_fraction_per_second": 0.1} |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | [-20, 45] |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | fullsystemenergyatBoL;suppliedpackage and siteinstallationcoststilldistinct |

| 数值水耗的披露情况 | Input water quality is stated; no numerical water-consumption rate published in retained product sheet |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 55.9 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：[{"currency": "EUR", "observed_at": "2026-11-10", "price_basis": "manufactureradvertisedprice subjecttostandardterms", "price_year": null, "scope": "suppliedpackage;not verifiedsite-totalcost", "source": "pages-08.json", "value": 50000000}]


模型接入：{"full_load_input_MWh_day": 1207.44, "hydrogen_kg_day": 21600, "minimum_flow_fraction": 0.125, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 55.9}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — MC250

ID：`nel-mc250`。类型：electrolyser。

来源定位：Nel-MC-Series-RevJ.pdf pp1-2。

原件：[Nel-MC-Series-RevJ.pdf](evidence/Nel-MC-Series-RevJ.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2021/01/MC-Series_PD-0600-0136-Rev-J.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 1.25 |

| 产氢率（kg/h） | 22.125 |

| 整机比电耗（kWh/kg） | 59.0 |

| 名义整机输入（kW） | 1305.375 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.1 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.1 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 30 |

| 基本气质 | 0.9995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 15.9 |

| 水质/原水或纯水边界 | potable subjecttositeanalysis;RO/EDIincluded |

| 爬坡 | {"max_fraction_per_second": 0.074, "min_to_full_seconds_upper": 15} |

| 热启动（秒） | {"source_wording": "fromstandby;not proof ofcoldstart", "upper": 480} |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption |

| scope_warning | MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 59.0 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：[{"currency": "USD", "kind": "approximatehistoricalpurchaseorder", "scope": "1.25MWcontainerandresearchcollaboration;not currentquote", "source": "pages-09.json:NRELorder", "value": 2000000, "year": 2020}]


模型接入：{"full_load_input_MWh_day": 31.329, "hydrogen_kg_day": 531.0, "minimum_flow_fraction": 0.1, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 59.0}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — MC500

ID：`nel-mc500`。类型：electrolyser。

来源定位：Nel-MC-Series-RevJ.pdf pp1-2。

原件：[Nel-MC-Series-RevJ.pdf](evidence/Nel-MC-Series-RevJ.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2021/01/MC-Series_PD-0600-0136-Rev-J.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 2.5 |

| 产氢率（kg/h） | 44.25 |

| 整机比电耗（kWh/kg） | 57.3 |

| 名义整机输入（kW） | 2535.525 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.1 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.1 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 30 |

| 基本气质 | 0.9995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 15.9 |

| 水质/原水或纯水边界 | potable subjecttositeanalysis;RO/EDIincluded |

| 爬坡 | {"max_fraction_per_second": 0.074, "min_to_full_seconds_upper": 15} |

| 热启动（秒） | {"source_wording": "fromstandby;not proof ofcoldstart", "upper": 480} |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption |

| scope_warning | MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 57.300000000000004 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：[{"currency": "USD", "kind": "derivedmeanperunitfromtwo-unitUSD7morder", "scope": "equipmentpurchaseorder;not UKsiteinstallationquote", "source": "pages-09.json:2025-01-21", "value": 3500000, "year": 2025}]


模型接入：{"full_load_input_MWh_day": 60.8526, "hydrogen_kg_day": 1062.0, "minimum_flow_fraction": 0.1, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 57.3}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — MC1000

ID：`nel-mc1000`。类型：electrolyser。

来源定位：Nel-MC-Modular-RevA.pdf pp1-2。

原件：[Nel-MC-Modular-RevA.pdf](evidence/Nel-MC-Modular-RevA.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/10/MC-Series-Modular-Plants-PD-0600-0145-Rev-A-1.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 5 |

| 产氢率（kg/h） | 88.5 |

| 整机比电耗（kWh/kg） | 56.77 |

| 名义整机输入（kW） | 5024.145 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.2 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.2 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 30 |

| 基本气质 | 0.9995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 15.9 |

| 水质/原水或纯水边界 | potable subjecttositeanalysis;RO/EDIincluded |

| 爬坡 | {"max_fraction_per_second": 0.074, "min_to_full_seconds_upper": 15} |

| 热启动（秒） | {"source_wording": "fromstandby;not proof ofcoldstart", "upper": 480} |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption |

| scope_warning | MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 56.77 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 120.57948, "hydrogen_kg_day": 2124.0, "minimum_flow_fraction": 0.2, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 56.77}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — MC2000

ID：`nel-mc2000`。类型：electrolyser。

来源定位：Nel-MC-Modular-RevA.pdf pp1-2。

原件：[Nel-MC-Modular-RevA.pdf](evidence/Nel-MC-Modular-RevA.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/10/MC-Series-Modular-Plants-PD-0600-0145-Rev-A-1.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 10 |

| 产氢率（kg/h） | 177.0 |

| 整机比电耗（kWh/kg） | 56.77 |

| 名义整机输入（kW） | 10048.29 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.2 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.2 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 30 |

| 基本气质 | 0.9995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 15.9 |

| 水质/原水或纯水边界 | potable subjecttositeanalysis;RO/EDIincluded |

| 爬坡 | {"max_fraction_per_second": 0.074, "min_to_full_seconds_upper": 15} |

| 热启动（秒） | {"source_wording": "fromstandby;not proof ofcoldstart", "upper": 480} |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption |

| scope_warning | MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 56.77 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 241.15896, "hydrogen_kg_day": 4248.0, "minimum_flow_fraction": 0.2, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 56.77}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — MC4000

ID：`nel-mc4000`。类型：electrolyser。

来源定位：Nel-MC-Modular-RevA.pdf pp1-2。

原件：[Nel-MC-Modular-RevA.pdf](evidence/Nel-MC-Modular-RevA.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/10/MC-Series-Modular-Plants-PD-0600-0145-Rev-A-1.pdf)）。

研究情景：已列入[STUDY_INPUTS](STUDY_INPUTS.json)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | PEM |

| 产品MW等级 | 20 |

| 产氢率（kg/h） | 354.0 |

| 整机比电耗（kWh/kg） | 56.77 |

| 名义整机输入（kW） | 20096.58 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.2 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.2 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 30 |

| 基本气质 | 0.9995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 15.9 |

| 水质/原水或纯水边界 | potable subjecttositeanalysis;RO/EDIincluded |

| 爬坡 | {"max_fraction_per_second": 0.074, "min_to_full_seconds_upper": 15} |

| 热启动（秒） | {"source_wording": "fromstandby;not proof ofcoldstart", "upper": 480} |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | containerizedsystem;stackenergy53.2kWhkgnot substituted forsystemconsumption |

| scope_warning | MarketingclassMW is not proof of exact ACinput ceiling;use derived nominal input and recordedflow |

| 输入功率是否推导 | Derived from quoted nominal production and full-system specific energy;not an independent electrical maximum. |

| 名义输入/产出比（kWh/kg） | 56.77 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 482.31792, "hydrogen_kg_day": 8496.0, "minimum_flow_fraction": 0.2, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 56.77}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Nel — A485

ID：`nel-a485`。类型：electrolyser。

来源定位：Nel-A485-Rev03.pdf pp1-2;pages-08.json。

原件：[Nel-A485-Rev03.pdf](evidence/Nel-A485-Rev03.pdf)（[原网址](https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2024/08/A-Series-Spec-Sheet%E2%80%93DOC001974_03.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | alkaline |

| 产品MW等级 | 2.2 |

| 产氢率（kg/h） | 43.583333333333336 |

| 整机比电耗（kWh/kg） | 未取得；不自动填零 |

| 名义整机输入（kW） | 未取得；不自动填零 |

| 电堆输入（kW） | 2179.166666666667 |

| 最低在线比例 | 0.15 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.15 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 0.03 |

| 基本气质 | 99+% saturatedwithliquidwater,O2<1% |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 10 |

| 水质/原水或纯水边界 | DI<1uScm |

| 爬坡 | {"min_fraction_per_minute": 0.1} |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 20+webclaim;not full-servicewarranty |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | stackandelectrolyteonly;notfullACplant;requiresrectifier,BoP,quality/pressurematching |

| 电堆比电耗（kWh/kg） | {"tolerance": 1.1, "value": 50} |

| 产氢率的最大/额定性质 | maximum production; source tolerance +0/-3%, not a guaranteed mean |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": null, "hydrogen_kg_day": 1046.0, "minimum_flow_fraction": 0.15, "missing_core_fields": ["system_specific_kWh_per_kg"], "reference_ready": "not a complete ACplantcandidate", "system_kWh_kg": null}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Enapter — AEM Flex120

ID：`enapter-flex120`。类型：electrolyser。

来源定位：Enapter-Flex120-202606.pdf p2rev08(2026-06-15)。

原件：[Enapter-Flex120-202606.pdf](evidence/Enapter-Flex120-202606.pdf)（[原网址](https://enapter.com/wp-content/uploads/2025/05/2026-06-15_Datasheet_AEM-Flex120.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | AEM |

| 产品MW等级 | 0.12 |

| 产氢率（kg/h） | 2.16 |

| 整机比电耗（kWh/kg） | 51.3 |

| 名义整机输入（kW） | 112.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.12 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.12 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 31 |

| 基本气质 | 0.995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 3.0 |

| 水耗（L/kg） | 8.981481481481481 |

| 水质/原水或纯水边界 | TypeIIpurifiedwater;rawrequirementdependsontreatment |

| 爬坡 | 未取得；不自动填零 |

| 热启动（秒） | 225 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | systemBoLfull-loadbasegradeincludesutilitiesinsidebatterylimits |

| 效率工况 | 55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata |

| 启动边界 | 225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee |

| 名义输入/产出比（kWh/kg） | 51.85185185185185 |

| 公开输入与比电耗乘产量的舍入差异 | 0.010757346039997048 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 2.688, "hydrogen_kg_day": 51.84, "minimum_flow_fraction": 0.12, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 51.3}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Enapter — AEM Nexus500

ID：`enapter-nexus500`。类型：electrolyser。

来源定位：Enapter-Nexus500-202606.pdf p2rev08(2026-06-15)。

原件：[Enapter-Nexus500-202606.pdf](evidence/Enapter-Nexus500-202606.pdf)（[原网址](https://enapter.com/wp-content/uploads/2025/05/Datasheet_AEM-Nexus-500_15.06.2026.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | AEM |

| 产品MW等级 | 0.5 |

| 产氢率（kg/h） | 9.1 |

| 整机比电耗（kWh/kg） | 51.3 |

| 名义整机输入（kW） | 467.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.17 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.17 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 31 |

| 基本气质 | 0.995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 12.0 |

| 水耗（L/kg） | 8.956043956043956 |

| 水质/原水或纯水边界 | TypeIIpurifiedwater;rawrequirementdependsontreatment |

| 爬坡 | 未取得；不自动填零 |

| 热启动（秒） | 225 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | systemBoLfull-loadbasegradeincludesutilitiesinsidebatterylimits |

| 效率工况 | 55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata |

| 启动边界 | 225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee |

| 名义输入/产出比（kWh/kg） | 51.31868131868132 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0003641582588951351 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 11.208, "hydrogen_kg_day": 218.39999999999998, "minimum_flow_fraction": 0.17, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 51.3}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Enapter — AEM Nexus1000

ID：`enapter-nexus1000`。类型：electrolyser。

来源定位：Enapter-Nexus1000-202606.pdf p2rev08(2026-06-15)。

原件：[Enapter-Nexus1000-202606.pdf](evidence/Enapter-Nexus1000-202606.pdf)（[原网址](https://enapter.com/wp-content/uploads/2021/06/Datasheet_AEM-Nexus-1000_15.06.2026-1.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | AEM |

| 产品MW等级 | 1.0 |

| 产氢率（kg/h） | 18.2 |

| 整机比电耗（kWh/kg） | 51.3 |

| 名义整机输入（kW） | 933.2 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.085 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.085 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 31 |

| 基本气质 | 0.995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 12.0 |

| 水耗（L/kg） | 8.956043956043956 |

| 水质/原水或纯水边界 | TypeIIpurifiedwater;rawrequirementdependsontreatment |

| 爬坡 | 未取得；不自动填零 |

| 热启动（秒） | 225 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | systemBoLfull-loadbasegradeincludesutilitiesinsidebatterylimits |

| 效率工况 | 55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata |

| 启动边界 | 225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee |

| 名义输入/产出比（kWh/kg） | 51.27472527472528 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0004926847032109362 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 22.396800000000002, "hydrogen_kg_day": 436.79999999999995, "minimum_flow_fraction": 0.085, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 51.3}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Enapter — AEM Nexus2500

ID：`enapter-nexus2500`。类型：electrolyser。

来源定位：Enapter-Nexus2500-202606.pdf p2rev08(2026-06-15)。

原件：[Enapter-Nexus2500-202606.pdf](evidence/Enapter-Nexus2500-202606.pdf)（[原网址](https://enapter.com/wp-content/uploads/2026/07/Datasheet_AEM-Nexus2500_15.06.2026.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | AEM |

| 产品MW等级 | 2.5 |

| 产氢率（kg/h） | 44.2 |

| 整机比电耗（kWh/kg） | 51.3 |

| 名义整机输入（kW） | 2266.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.1 |

| 暂态最低比例 | 0.035 |

| 暂态持续时间上限（h） | 24 |

| 长期稳态最低比例 | 0.1 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 31 |

| 基本气质 | 0.995 |

| 可选气质 | 0.99999 |

| 额外净化功率（kW） | 18.0 |

| 水耗（L/kg） | 8.959276018099548 |

| 水质/原水或纯水边界 | TypeIIpurifiedwater;rawrequirementdependsontreatment |

| 爬坡 | 未取得；不自动填零 |

| 热启动（秒） | 225 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | systemBoLfull-loadbasegradeincludesutilitiesinsidebatterylimits |

| 效率工况 | 55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata |

| 启动边界 | 225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee |

| 名义输入/产出比（kWh/kg） | 51.26696832579185 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0006438922847591739 |

| 特殊低负荷规则 | 3.5-10%atmost24h;then10-100%;shutdown/reset details require confirmation;notconstant3.5%forever |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 54.384, "hydrogen_kg_day": 1060.8000000000002, "minimum_flow_fraction": 0.1, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 51.3}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。



## Enapter — AEM Rheos20

ID：`enapter-rheos20`。类型：electrolyser。

来源定位：Enapter-Rheos20-202606.pdf p2rev08(2026-06-15)。

原件：[Enapter-Rheos20-202606.pdf](evidence/Enapter-Rheos20-202606.pdf)（[原网址](https://enapter.com/wp-content/uploads/2026/07/2026-06-15_Datasheet_AEM-RHEOS20.pdf)）。

研究情景：保留为备选/敏感性对象，详[缺项清单](VENDOR_GAPS.md)。


| 指标 | 原始记录、条件或限定 |

|---|---|

| 电解技术 | AEM |

| 产品MW等级 | 20.0 |

| 产氢率（kg/h） | 362.0 |

| 整机比电耗（kWh/kg） | 51.4 |

| 名义整机输入（kW） | 18590.0 |

| 电堆输入（kW） | 未取得；不自动填零 |

| 最低在线比例 | 0.01 |

| 暂态最低比例 | 未取得；不自动填零 |

| 暂态持续时间上限（h） | 未取得；不自动填零 |

| 长期稳态最低比例 | 0.01 |

| 运行范围所指对象 | flow fraction unless datasheet explicitly says power |

| 出口压力（barg） | 31 |

| 基本气质 | 0.99999 |

| 可选气质 | 未取得；不自动填零 |

| 额外净化功率（kW） | 未取得；不自动填零 |

| 水耗（L/kg） | 8.955801104972375 |

| 水质/原水或纯水边界 | TypeIIpurifiedwater;rawrequirementdependsontreatment |

| 爬坡 | 未取得；不自动填零 |

| 热启动（秒） | 未取得；不自动填零 |

| 冷启动（秒） | 未取得；不自动填零 |

| 待机功率（kW） | 未取得；不自动填零 |

| 最小连续运行（h） | 未取得；不自动填零 |

| 最小连续停机（h） | 未取得；不自动填零 |

| 电堆寿命（h） | 未取得；不自动填零 |

| 工厂寿命（年） | 未取得；不自动填零 |

| 质保年限及性质 | 未取得；不自动填零 |

| 环境温度范围（°C） | 未取得；不自动填零 |

| 衰减曲线 | 未取得；不自动填零 |

| 替换成本 | 未取得；不自动填零 |

| 维护 | 未取得；不自动填零 |

| 测量/供应范围 | full-scopeplant,includingpurificationto99.999%,transformers,rectifiers,waterconditioning |

| 效率工况 | 55Celectrolyte,15Cambient;do not borrowPEMlife/cost asmanufacturerAEMdata |

| 启动边界 | 225s requires warmcirculatingelectrolyte>=45C;not acoldstartguarantee |

| 名义输入/产出比（kWh/kg） | 51.353591160220994 |

| 公开输入与比电耗乘产量的舍入差异 | 0.0009028957155448155 |


价格证据：未取得型号对应的公开原厂完整安装报价；行业参考另见情景文件。


模型接入：{"full_load_input_MWh_day": 446.16, "hydrogen_kg_day": 8688.0, "minimum_flow_fraction": 0.01, "missing_core_fields": [], "reference_ready": "nominal-point operating study;investment needslifecycle/cost assumptions", "system_kWh_kg": 51.4}


公共资料剩余项：Current full installed project price；Product-specific lifetime/renewal cost and downtime；Off/standby/start energy and full partial-load curves where unpublished。


