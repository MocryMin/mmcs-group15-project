# 电池与电解槽产品调研

版本v3.1：补入CU来源的Tesla两配置，纠正PNNL循环终点，保留v3原包。详[CU交叉核查](CU_CROSSCHECK.md)。

研究日期：2026-11-10。适用范围：MMCS最终项目Tier1设备选择，以及Tier2B固定设备下的逐日调度。整理人：Ran Min的课程助手。

本轮整理了**14个电池配置、15个电解槽配置**，覆盖5家电池供应商与3家电解槽供应商。重点是把同一个商品的容量、功率、损耗、运行范围、寿命和经济边界放在一起，避免拼接不同商品的最佳数值。按用户最新决定，可靠的第三方研究和工程估计可以补充原厂未披露项；资料整体较完整的商品优先进入研究模型。

**研究输入已分两层交付：**全部29个配置保留原厂事实与缺项；其中3款交流一体电池和9款PEM电解槽另有数值化日级参考情景。参考情景补齐容量、效率、损耗、寿命、资本与维护口径，并标出迁移/估计来源。产品对应的实际安装报价、质保衰减曲线和服务合同仍未全部公开，不能把参考情景当成厂商承诺。POSEIDON的湿氢交付边界另需与净回价匹配。

## 1. 需要收集哪些指标

| 对象 | 技术输入 | 寿命与经济输入 |
|---|---|---|
| 电池 | 名义及可用容量；允许放电深度；充/放功率及交流/直流测量边界；往返效率及工况；自放电；运行/待机辅助用电；并机和配套变流器 | 日历寿命、指定深度下循环寿命、寿命终点容量、衰减/维护方式、质保；设备/安装成本、年维护、扩容或更换、退役 |
| 电解槽 | 交流整机功率、电堆功率、产氢率、整机/电堆比电耗；最低负荷和部分负荷性能；启动/待机/爬坡；水量水质；出口压力、纯度、干燥净化和供货范围 | 电堆小时寿命、工厂寿命、衰减、维护/停机、换堆；设备/安装价格、固定维护、变量成本及换堆储备 |

一天一个稳态、效率如何拆成两个方向、首末库存、是否展开分钟级启动属于模型协议。容量、允许深度和真实损耗则按设备证据取值。缺项不自动写成零。

## 2. 电池产品

AC是交流侧，DC是直流侧。PCS（Power Conversion System）是连接电池直流侧与电网交流侧的双向变流系统。DoD（Depth of Discharge）指放电深度；SOH（State of Health）指相对初始容量的健康状态。表中“未闭合”表示现有资料不能给出该配置的完整整站指标。

| 厂商、型号/配置 | 名义容量 | 功率 | 深度、效率和寿命证据 | 研究定位 |
|---|---:|---:|---|---|
| TESVOLT TALLON | 5,015 kWh | 2,500 kW，需统一PCS边界 | 允许100%DoD；DC往返93.7%@0.5Cp/95.2%@0.25C；11,000循环/15年，SOH60%，有工况 | 寿命和辅助用电资料最丰富；补配PCS后很有价值 |
| TESVOLT POWERCORE G2 | 509 kWh；名称500 | 250 kW AC；电池部分244/254.8 kW | FAQ最高约92% AC往返；网页>10,000循环/10年后SOH>70%；可用深度未给 | 额定边界和可用容量需补，暂作备选 |
| Sungrow ST255CS-2H | 257 kWh | 125 kW AC | 允许0%–100%；网页整站往返持续高于90%；循环/日历质保曲线未取得 | 主研究候选；寿命/成本用明确行业情景 |
| Sungrow PowerTitan2.0，2h | 5,015 kWh | 2,500 kW等级 | 资料给额定AC 2,520 kVA；深度/AC往返/生命周期未闭合 | 大型备选，不能移植同品牌小柜全部参数 |
| Sungrow PowerTitan2.0，4h | 5,015 kWh | 1,250 kW等级 | 额定AC 1,260 kVA；其他同上 | 4小时扩展，区别于课程2小时参考 |
| Huawei LUNA2000-215-2S10 | 215 kWh | 108 kW AC | 0%–100%；最高循环效率91.3%；待机≤150 W | 主研究候选 |
| Huawei LUNA2000-241-2S1 | 241 kWh | 108 kW AC | 0%–100%；最高循环效率91.3%；待机≤150 W | 同厂家不同容量主候选；版本单独保留 |
| Huawei LUNA2000-5015-2S | 5,015 kWh DC | ≤0.5Cp，约2,507.5 kW DC | 有独立PCS资料；实际配套数量、AC效率及可用深度未闭合 | 大型备选 |
| CATL EnerOne Plus，285 Ah | 379.4 kWh DC | 配套PCS未指定 | 1,361.2 V；深度、完整AC效率和具体电芯寿命未闭合 | 部件级备选 |
| CATL EnerOne Plus，306 Ah | 407.3 kWh DC | 配套PCS未指定 | 同系列不同电芯配置 | 部件级备选 |
| CATL EnerC Plus，280 Ah | 3,720 kWh DC | 配套PCS未指定 | 1,331.2 V；同类缺项 | 容器级备选 |
| CATL EnerC Plus，306 Ah | 4,070 kWh DC | 配套PCS未指定 | 同系列不同电芯配置 | 容器级备选 |
| Tesla Megapack2XL，2h（2023版） | 3,854 kWh | 1,927 kW AC | 满深度循环92%，含内部转换/热管理；15年质保可延20年 | 新增竞品，运行深度/容量保证曲线及480V现场连接待匹配 |
| Tesla Megapack2XL，4h（2023版） | 3,916 kWh | 979 kW AC | 相同工况93.7%；同样质保范围 | 4小时扩展，原厂文件版本单列 |

原件入口：[Tesla Megapack2XL](evidence/Tesla-Megapack2XL-20230210.pdf)、[TESVOLT TALLON](evidence/TESVOLT-TALLON.pdf)、[POWERCORE G2](evidence/TESVOLT-POWERCORE-G2.pdf)、[Sungrow ST255](evidence/Sungrow-PowerStack255CS.pdf)、[PowerTitan2](evidence/Sungrow-PowerTitan2-2H4H-V3.pdf)、[Huawei 215](evidence/Huawei-LUNA215-2S10.pdf)、[Huawei 241](evidence/Huawei-LUNA241-2S1.pdf)、[CATL目录PDF第16–17页](evidence/CATL-ESS-202406.pdf)。全部原始网址见[SOURCES.json](SOURCES.json)。

TALLON还明确给出运行辅助功率：25°C典型23 kW、45°C典型33 kW、待机2 kW、峰值36 kW，以及特定1.5循环/日下63.51 MWh/年的辅助能耗。这些是不同工况描述，不能全部相加。其15年组合产品/性能质保可选延长至20年，但不能据此假设20年容量不衰减。

Huawei的“辅助电源≤5 kW”是电源容量，不是持续耗电5 kW；最高91.3%也不是全部工况的日均效率。CATL的“可选电芯最高12,000循环”和“20年可靠性”不能自动成为四个配置共同的循环/日历保证。Sungrow最多25台并机指一个系统组，不是整个项目最多买25台。

## 3. 电解槽产品

PEM为Proton Exchange Membrane（质子交换膜）；AEM为Anion Exchange Membrane（阴离子交换膜）。表中整机电耗为额定工况、寿命初期的公开值，部分负荷可不同。“MW等级”保留产品名称；不能据此覆盖精确输入和产氢率。

| 厂商、型号 | 技术 | MW等级 | 产氢 kg/h | 整机 kWh/kg | 持续在线最低比例 | 压力/气质要点 |
|---|---|---:|---:|---:|---:|---|
| ITM NEPTUNE II | PEM | 2.00 | 35.00 | 57.00 | 25.0% | 30 barg；水/氧各<5 ppm |
| ITM NEPTUNE V | PEM | 5.00 | 90.00 | 55.90 | 12.5% | 30 barg；水/氧各<5 ppm |
| ITM POSEIDON | PEM | 20.00 | 360.00 | 55.90 | 20.0% | 31 barg；饱和湿氢、痕量氧，净化供货边界需匹配 |
| ITM ALPHA50 | PEM | 50.00 | 900.00 | 55.90 | 12.5% | 30 barg；水/氧各<5 ppm |
| Nel MC250 | PEM | 1.25 | 22.13 | 59.00 | 10.0% | 30 barg；99.95%，可选高纯干燥 |
| Nel MC500 | PEM | 2.50 | 44.25 | 57.30 | 10.0% | 同上 |
| Nel MC1000 | PEM | 5.00 | 88.50 | 56.77 | 20.0% | 同上；大系统最低比例不同 |
| Nel MC2000 | PEM | 10.00 | 177.00 | 56.77 | 20.0% | 同上 |
| Nel MC4000 | PEM | 20.00 | 354.00 | 56.77 | 20.0% | 同上 |
| Nel A485 | 碱性 | 2.20，电堆 | 43.58，最大 | 未给；电堆50±1.1 | 15.0% | 0.03 barg；99+%湿氢，属于电堆/电解液模块 |
| Enapter Flex120 | AEM | 0.12 | 2.16 | 51.30 | 12.0% | ≤31 barg；基本99.5%，可选干燥至99.999% |
| Enapter Nexus500 | AEM | 0.50 | 9.10 | 51.30 | 17.0% | 同上 |
| Enapter Nexus1000 | AEM | 1.00 | 18.20 | 51.30 | 8.5% | 同上 |
| Enapter Nexus2500 | AEM | 2.50 | 44.20 | 51.30 | 10.0%，有暂态例外 | 3.5%–10%最多连续24小时，之后10%–100% |
| Enapter Rheos20 | AEM | 20.00 | 约362.00 | 51.40 | 1.0% | ≤31 barg；99.999%净化已在整机内 |

原件入口：[ITM 2MW](evidence/neptune-2.pdf)、[5MW](evidence/neptune-5.pdf)、[20MW](evidence/ITM-Poseidon20-2-7.pdf)、[50MW](evidence/alpha-50.pdf)、[Nel小型MC](evidence/Nel-MC-Series-RevJ.pdf)、[模块化MC](evidence/Nel-MC-Modular-RevA.pdf)、[A485](evidence/Nel-A485-Rev03.pdf)、[Enapter Nexus2500](evidence/Enapter-Nexus2500-202606.pdf)。其余Enapter原件见evidence及逐产品卡片。

### 3.1 电耗、功率和运行状态

Nel MC250按公开产氢率和整机比电耗换算，满产需要约1.305 MW，不能把名称1.25 MW当成精确上限。Enapter的Flex120、Nexus500、Nexus1000、Nexus2500、Rheos20分别给出112、467、933.2、2,266、18,590 kW的名义整机输入。这些与型号中的120/500/1000/2500/20000不同。原始输入、产氢率和比电耗有舍入残差时，同时保留，建模时声明所用校准方式。

Nel的53.2 kWh/kg是电堆值，完整MC系统应使用59、57.3或56.77。A485的50 kWh/kg也是电堆值；还缺交流整流器、其余辅助系统及交付气质匹配，不能据此判定它整体最省电。

ITM公开爬坡上调10%/秒、下调50%/秒。Nel从待机启动<8分钟、最低至满负荷<15秒；这不是冷启动保证。Enapter Flex/Nexus的225秒热启动要求电解液至少45°C且已循环。日级模型可以忽略分钟级过程，但应保留这些原始指标，以便评估更细时间步。

### 3.2 水、气质和额外处理

Nel MC公开原水需求15.9 L/kg并包含RO/EDI水处理。Enapter Flex/Nexus/Rheos给出的纯化水约9 L/kg，原水还取决于现场水质和回收率；这些数不能直接当成同口径原水量比较。ITM原件给了进水水质，但未披露数值水耗，保留为公用工程接口。

Enapter Flex/Nexus的51.3 kWh/kg针对99.5%基本配置。高纯干燥版另增加约3/12/12/18 kW，分别对应Flex120/Nexus500/Nexus1000/Nexus2500；不能以基本版电耗搭配高纯版售价。Rheos20净化后的99.999%已包括在整机配置里。ITM POSEIDON核心出口为湿氢，比较统一售氢收益前需补处理或采用与其气质匹配的净回价。

## 4. 成本、寿命和维护如何补齐

### 4.1 有产品指向的价格证据

| 证据 | 数值与年份 | 可支持的使用方式 |
|---|---|---|
| ITM NEPTUNE V公开产品资料 | €5,000,000；本次2026-11-10取得，价格基年未写明 | 标准条款下供货包参考；不等于客户场址完整建造成本 |
| ITM ALPHA50公开产品资料 | €50,000,000；同上 | 同上；不能简单认定大型号单位价更低 |
| Nel两台MC500订单，2025-01-21 | 5MW合计约US$7m，平均约US$3.5m/台 | 真实设备订单锚点；不是英国现场报价 |
| Nel NREL 1.25MW订单，2020-10-22 | 约US$2m，含特定研究/扩展供货 | 较旧小型项目锚点，不能冒充当前MC250标价 |
| Nel Aberdeen MC500，2025-03-20 | 型号与英国集成方明确；未披露价 | 支持MC500存在英国实际项目，不能推导价格 |
| Enapter两份订单，2024-09-05 | 总5MW，订单额为七位数欧元的高位；无精确型号单价 | 商业规模旁证，不反算伪精确单台价格 |

来源：[ITM NEPTUNE V](https://itm-power.com/products/neptune-5)、[ITM ALPHA50](https://itm-power.com/products/alpha)、[Nel 2025年MC500订单](https://nelhydrogen.com/press-release/nel-asa-receives-purchase-order-for-5-mw-of-containerized-pem-electrolysers/)、[Nel英国项目](https://nelhydrogen.com/press-release/nel-asa-receives-purchase-order-for-one-mc500-containerized-pem-electrolyser/)、[Nel NREL订单](https://nelhydrogen.com/press-release/nel-asa-receives-purchase-order-for-a-1-25-mw-containerized-pem-electrolyser-from-nrel/)、[Enapter订单](https://enapter.com/en/press-release/enapter-receives-biggest-single-order-from-europe-to-date/)。

### 4.2 电池行业参考

[DEA储能工作簿](evidence/DEA-storage.xlsx)的锂电章节给出2025参考配置3 MWh/1.5 MW，AC往返91%、DC95%、日储存损耗0.1%、日历寿命15年。以2020年欧元计，总安装参考可拆为

$$
C^{inst}=245000E_{MWh}+86000P_{MW}.
$$

这让容量和功率不同的商品有一个明确的共同成本情景，而不需要强行保留旧3 MWh投资网格。迁移到厂商产品或更大场站仍是研究估计。

工作簿固定维护存在单位/公式冲突：字面是€8,352/MW-year，而按总资本成本2.9%解释，在2小时系统上会得到约两倍费用。两种解释都保留，不擅自解决。[PNNL独立工作簿](evidence/PNNL-cost-performance-2024.xlsx)给出的2023年10 MW/2h LFP示例是US$452.22/kWh、固定维护US$2.79/kW-year、AC往返83%，提供另一套完整边界，而非只挑便宜成本搭配另一套最佳性能。

PNNL的80%DoD/2,400循环对应剩余容量约80%的阶段；60%DoD/8,000循环对应剩余容量60%。最终EOL60%与前一阶段不可混为同一终点，日历参考16年。该含义已对照[2022完整报告第43–44页](evidence/PNNL-Cost-Performance-2022.pdf)核实。这些是相互配套的行业假设，不是刚调研的每款商品保证。主参考输入选80%深度，并保留60%深度替代情景；厂家允许100%的原始事实继续保留。寿命曲线和厂家售后条款仍可继续改善估计。

### 4.3 电解槽行业参考

[BEIS成本报告](evidence/BEIS-Hydrogen-Costs2021.pdf)及[原始工作簿](evidence/BEIS-Hydrogen-Costs2021-Annex.xlsx)提供英国2020成本包：PEM低/中/高资本成本£953.59/£1,158.63/£1,887.51每kW-H2-HHV，固定维护£32.38/£36.72/£42.73每kW-H2-HHV-year；工厂寿命30年。该单位以氢的高位热值输出功率为分母，需要用产氢kg/h乘39.37 kWh/kg换算，不能直接乘输入电功率。

其变量运维已是换堆的年化储备。选择这一成本包时，不能再额外收一遍同样换堆费用。若采用显式换堆，则改走独立路线，保留原报告PEM约11年、旧资本包60%的换堆假设，且不将旧比例乘到另一套现代总安装成本。

[IEA Global Hydrogen Review 2025](https://www.iea.org/reports/global-hydrogen-review-2025/executive-summary)给出2024年中国以外实际安装观察约US$2,000–2,600/kW，可用于现代安装成本的独立敏感性包。其地域、规模和工程范围不代表每款产品逐一成交价，也不能未经换汇/价格基年统一就与BEIS数值直接比较。

[DOE PEM技术状态](https://www.energy.gov/cmei/fuels/technical-targets-proton-exchange-membrane-electrolysis)给出2022年40,000小时及10%性能损失寿命判据；碱性参考为60,000小时。80,000小时是目标，不能写成已调研商品的已达保证。Enapter另有[2022官方价格假设](evidence/Enapter-2022-pricing-assumptions.pdf)，EL2.1假设30,000小时、当时面向未来的ModelT假设40,000小时。它们可以形成AEM寿命敏感性，但不能代替2026年Nexus平台的产品质保。AEM的安装/换堆成本仍比PEM参考包弱，因此当前保留为研究竞品，不无标识套用PEM维护成本。

## 5. 本次优先研究输入

[STUDY_INPUTS.json](STUDY_INPUTS.json)含12套数值化日级情景：Sungrow ST255、Huawei 215/241，以及ITM四型号、Nel MC五型号。电池采用厂家容量和允许深度、明确的研究运行深度及效率/损耗估计、配套寿命参考和DEA成本两种维护解释；PEM采用逐型号完整整机性能与BEIS成套资本/维护/换堆储备，并附现代安装成本范围。

三款优先电池的共同成本公式结果为：

| 型号 | 研究可用容量，80%深度 | 安装参考，EUR2020 | 固定维护：字面单位/2.9%资本，每年 |
|---|---:|---:|---:|
| Sungrow ST255CS-2H | 205.60 kWh | €73,715.00 | €1,044.00 / €2,137.74 |
| Huawei 215 | 172.00 kWh | €61,963.00 | €902.02 / €1,796.93 |
| Huawei 241 | 192.80 kWh | €68,333.00 | €902.02 / €1,981.66 |

表中价格是行业公式估计，不能据此宣布Huawei真实报价比Sungrow便宜。Huawei待机用公开0–150 W范围的中点作研究值；Sungrow缺待机值，采用TALLON“2 kW/2.5 MW”的按功率缩放工程估计，约100 W，并测试0–200 W。两者均有明确标记，后续若找到更匹配计量可替换。

研究情景采用“维护预算维持可用容量/额定输出”的会计口径。电池维护和PEM变量换堆储备已覆盖对应更新时，不再额外收同一费用；原始循环/小时寿命继续保留为生命周期敏感性。若要模拟容量或比电耗逐年衰减，需要改成显式衰减与更新流程，而不是同时假设维护完全恢复又扣一次同样的衰减。

**推荐顺序：**先用这三款电池检验真实设备规格对旧“零电池”结论的影响；PEM优先比较有标价的NEPTUNE V、有英国实际项目及订单价锚点的MC500，再比较ITM/Nel的大型和小型梯度。TALLON值得补配PCS；AEM值得做效率/最低负荷的竞争情景。CATL与大型DC电池需先完成整站组合，暂不参与一个声称完全同口径的供应商排名。

## 6. 文件与核验

- [README](README.md)：阅读和接入入口。
- [逐产品卡片](PRODUCT_CARDS_ZH.md)、[catalogue.json](catalogue.json)、[products目录](products/)：所有公开事实、边界、缺项。
- [STUDY_INPUTS.json](STUDY_INPUTS.json)：优先12套研究情景，含估计与来源。
- [reference_scenarios.json](reference_scenarios.json)：行业参考，不覆盖原厂记录。
- [field_coverage.csv](field_coverage.csv)：逐项覆盖；空缺不伪装成已知值。
- [MODELLING_INTERFACE](MODELLING_INTERFACE.md)：单位、交流/直流、逐日SOC、产氢关系和成本接法。
- [VENDOR_GAPS](VENDOR_GAPS.md)：剩余产品/场址询证清单。
- [SOURCES.json](SOURCES.json)：原网址、本地文件、SHA256、PDF页数和采集范围。
- [QA.json](QA.json)：目录与单位、名义输入/产出关系、特殊运行规则核验；原件表格关键页另有渲染图。

全部原始下载由Playwright MCP完成，原厂数据表、手册、成本工作簿在evidence。搜索引擎存在空结果和验证限制，已记录；未把搜索失败当作“市场没有产品”。本轮未向厂家发信或提交询价；未改变已有baseline、未重算投资结论，未发布远程仓库。
