# Controller定向复核：IEA现代电解槽安装成本

日期：2026-11-03，Europe/London。此为root在R3首轮结束后指定的有界本地复核。实际读取root通过匿名Playwright取得的IEA2024及2025官方Executive summary完整正文；没有新增网络访问，未改FIRST_PASS。

**判断：IEA2025的实际2024成本观察应取代UK2020旧模型，作为现代场站CAPEX的优先行业参考；UK2020仅保留为有年份与范围标签的旧成本情景。** 这不等于IEA提供了ITM、PEM专项或英国某场址的报价。

## 实际证据与定位

[Global Hydrogen Review2025 Executive summary](https://www.iea.org/reports/global-hydrogen-review-2025/executive-summary)，小节“China leads on electrolyser deployment and manufacturing capacity, but overseas sales face barriers”，成本段实际给出：

|制造/安装情形|实际范围|建模用途|
|---|---:|---|
|中国以外制造并在中国以外安装，2024观察|USD2,000–2,600/kW|与英国ITM参考设备最接近的通用行业CAPEX代理|
|中国制造、在中国以外安装，包含所述运输/关税影响|USD1,500–2,400/kW|采购来源变化的另行情景；不是同一性能设备的无条件折扣|
|中国制造并安装在中国|USD600–1,200/kW|不能直接移用为英国进口后的已安装成本|

原文明确设备仅为总安装投资的一部分，工程、采购、施工与预备费合计超过总额一半，且依赖项目地点。总安装范围已经包含所述支出，不能把同一EPC费用再乘一遍。摘要没有列出场址所有分项，不证明高压氢压缩、储氢、对外输送、土地、特定并网强化、融资或全部税费已完整覆盖。所述Chinese设备出口情景的运输/关税口径不等于氢产品下游运输。

[Global Hydrogen Review2024 Executive summary](https://www.iea.org/reports/global-hydrogen-review-2024/executive-summary)，小节“Low-emissions hydrogen will remain expensive in the short term, but costs are expected to fall significantly”，说明依据较成熟项目新增资料上调电解槽成本。它为旧成本模型需要重评提供方向证据，不在本次已读摘要中提供上述数值范围，也不构成另一组独立数值验证。

## 分母、年份和技术范围

- 原文单位写per kW，所在上下文是水电解槽GW容量，**将其映射为电输入kW是有上下文依据的推定**。摘要未显式标kWe，更未区分AC/DC或是否为堆/系统电输入点。因此参数保留`electrical_input_inferred`标签，不再按HHV氢输出功率乘一次效率。
- 原文写2024年的制造和安装成本，**2024是成本观察年份**；摘要没有另行说明“constant2024USD”或其他不变美元基年。保留原始USD数值，不替机构补写实值定义。
- 范围描述电解槽一般情况，没有按PEM/碱性、规模、厂家或英国场址逐项拆分。将其用于20MW ITM/PEM方案属于分析者的通用行业代理选择，不应改写成厂商成本事实。
- 可选中点USD2,300/kW为R3自选中心情景；2,000/2,600为实际来源端点。中点不是IEA另给的点估计。

## 对R3参数包的修改

现代CAPEX主情景改为`IEA2024_observed_nonChina_installed`，保持原USD2,000/2,300/2,600每kW电解槽容量。暂不数值转GBP。root/R4后续若采用“2024观察约按nominalUSD2024报告”及某年度汇率，应把它们单列为财务统一假设；不得称该实值基年由IEA确认。

UK2020成本包及其671.61/816.02/1,329.36£2020/kWe转换值继续保留，角色改为legacy/sensitivity，不再作为现代主CAPEX。BEIS固定运维中值£2020 25.86165/kWe/year也保留为独立旧绝对费用代理，**不能因新CAPEX较高就按旧比例自动放大**；IEA摘要没有提供相应现代OPEX。

BEIS旧模型把堆成本设为旧场站CAPEX60%。若把这一比例直接乘IEA现代整站总投资，会与IEA超过一半为工程安装/预备费的组成明显冲突。修改为：

1. `UK2020_legacy_package`内部仍可使用每11年0.60×旧CAPEX，且不再加旧变量堆替换储备。
2. 现代CAPEX情景若必须用公开旧数据完成敏感性，可保留**独立绝对堆替换代理**：旧£2020 816.01544/kWe×60%=£2020 489.60926/kWe，于第11/22年（若在期限内）计费。它是跨模型的不确定性情景，不是IEA或ITM现代替换报价。不得乘USD2,300，更不得冒充新场站中60%份额。
3. 已年化£2020 0.153543/kg堆储备仍仅为另一替代方案，不与显式替换双计。低负荷时是否足额覆盖大修保持未证。

## 条件关闭

现代安装成本不再是“完全无公开证据”的缺口。剩余为明确的代理适用性/财务口径条件：电输入分母推定、AC/DC边界未明、USD实值基年未单独说明、无公司报价、现代OPEX/堆替换没有同边界原件。将这些写进run manifest后，可以关闭为课堂情景基线研究；不能据此声称采购预算、支持资格或真实承购已保证。根已要求停止扩展来源，本定向复核后R3主题关闭。
