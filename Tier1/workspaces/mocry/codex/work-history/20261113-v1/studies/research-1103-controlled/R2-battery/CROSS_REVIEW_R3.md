# R2 对 R3 的定向单位与成本边界复核

日期：2026-11-03，Europe/London。按root指派，在R2正式首轮与FIRST_PASS快照保存之后进行。只读R3原始捕获和正式报告/参数，不修改R3文件。本轮没有新增网络访问。

**结论：R3所用BEIS历史成本到ITM电输入口径的换算方向、数值、价格年和主要范围标签通过定向复核；未发现需要阻塞情景基线的单位错误。** 现代厂商全安装价格仍未取得，R3已明确采用旧情景代理；此结论不构成采购价验证。建议将“参考10MW”明确补成10MW_H2_HHV，避免读者与20MW电输入模块混淆。

## 实际独立读取的原件

- BEIS Annex实物：`control/browser_captures/R3/H2-ANNEX.xlsx`，`Technical and cost assumptions` A1、A3、A4/B4/K4、A10:B12/K10:L12、B14/K14:L16、B21/K21:K23、B24/K24:K26、A28；另读取K14:K25的原始公式模式，均为数值常量。[官方XLSX](https://assets.publishing.service.gov.uk/media/611a706ed3bf7f63a7b29216/Hydrogen_Production_Cost_2021_Annex.xlsx)。
- BEIS实物PDF：`control/browser_captures/R3/H2-COSTS-2021.pdf`，完整相关p8、9、16、17、19–21。[官方PDF](https://assets.publishing.service.gov.uk/media/611b710e8fa8f53dc994e59d/Hydrogen_Production_Costs_2021.pdf)。
- ITM实物PDF：`control/browser_captures/R3/POSEIDON.pdf`，完整4页，重点p2脚注和p3核心供应。[官方技术表](https://itm-power-assets.s3.eu-west-2.amazonaws.com/POSEIDON_DATA_SHEET_2_7_2e1f89da3f.pdf)。
- DOE原始正文：`control/browser_captures/R3/W04.json`，技术表2022 Status/2026 Targets和脚注a–i，重点h。[官方页](https://www.energy.gov/cmei/fuels/technical-targets-proton-exchange-membrane-electrolysis)。
- 随后对照R3正式REPORT.md与parameters.json，重点H01-CAPEX-RAW、H01-CAPEX-HYBRID、H03-FOM、H03-STACK-BASE/ALT。

## 1. 价格基年、技术时点与容量分母

Annex A1明确“2020 real prices”；K3为2020投产技术，L3为2025投产技术。K列并不是2021/2026现价；L列是旧研究的2025技术预测，不因当前日期晚于2025而升级成实测成交价。BEIS p16说明主要依据2018证据；R3保留`UK2020_legacy_proxy`标签正确。

BEIS p8声明未特别说明的MW/MWh都是氢输出高位热值口径。故K4=10MW参考厂是10MW_H2_HHV，**不是10MWe**。K14:K16为953.59/1158.63/1887.51 GBP2020/kW_H2_HHV。R3按电输入kWe转换后再乘电输入容量，做法正确。建议R3表头把“10MW”补全为“10MW_H2_HHV”；按所用ITM性能，这一参考输出约相当14.20MWe，不能在口头说明中称直接把10MWe厂放大为20MWe厂。

## 2. £/kW_H2_HHV → £/kWe

BEIS p8列£/MWh_H2_HHV转£/kg的系数0.03937，即39.37kWh_HHV/kg。设ITM全系统电耗$e=55.9$kWhe/kg，则：

$$
\eta_{HHV}=39.37/55.9=0.704293381,
\qquad C_{kWe}=C_{kW_{H2,HHV}}\,\eta_{HHV}.
$$

这里应乘效率，不能除效率。一个kWe输入仅对应约0.704kW_H2_HHV输出。R3数值复算一致：

|源参数|low|medium|high|换算结果单位|
|---|---:|---:|---:|---|
|K14:K16 CAPEX×39.37/55.9|671.607125|816.015440|1329.360800|GBP2020/kWe|
|K21:K23 固定OPEX×39.37/55.9|22.805020|25.861653|30.094456|GBP2020/kWe/year|
|K24:K26 变量替换储备×39.37|0.114173|0.153543|0.350393|GBP2020/kg_H2|

题设39.4四舍五入版本使中值资本816.637245GBP2020/kWe，较R3约高0.076%；这是明示热值精度差异，不是方向错误。建议币值/参数清单一处记录39.37（BEIS换算）与39.4（brief支持价换算）的区别，勿在同一等式中混用。

R3没有假称BEIS直接提供ITM价格，明确把BEIS资本结构投射到ITM55.9；这是混合技术代理。若复现BEIS自己的2020中效技术，K11=1.397 kWhe/kWh_H2_HHV，应为1158.63/1.397=829.370079GBP2020/kWe；它与816.015440不同并不构成错误，因为效率已换。2025预测的L15=730.29若使用L11=1.3208则552.914900GBP2020/kWe；若仍混用ITM55.9则514.338413。两者都不能称2025实价。

Annex A28说明高成本应配低效率才是原来源完整技术情景。R3将成本low/medium/high与同一55.9配对，已标为刻意单因素压力测试，标签足够，不应重新包装成原报告整套概率情景。

## 3. ITM55.9耗电、360kg/h与供应边界

POSEIDON p2脚注明确55.9为寿命初期全系统AC耗电，包括水净化、堆和BoP。20,000kW÷55.9=357.781753kg/h；360kg/h反推为20.124MW，相差0.62%，R3把额定营销数视为舍入而采用能量转换式正确。不能同时强制两条精确等式。

全系统耗电边界并不证明产品核心报价覆盖同一组设备；p3列核心供应，p2流程图区分BoP/optional scope。R3没有将55.9当堆耗电后再加一遍水处理/BoP电耗，亦没有把核心设备说成全站交付，这两项通过。工况为beginning of life，尚无整寿命退化/部分负荷曲线保证。

## 4. BEIS安装范围、DOE未安装范围与替换重复计费

BEIS p16的电解资本范围包括堆、必要BoP、干燥/脱氧/水去离子、土建和电网连接；p9/19排除产后储运与氢压缩，前期开发/退役证据有限。可称范围明确的历史场站安装成本代理，不能称当前ITM厂商EPC固定总价。R3这一限制准确。

DOE技术表“System Uninstalled Capital Cost”2022 Status=$1000/kW；脚注h明确系统成本不含安装所需工程、采购、施工、许可。2026的$250/kW与80,000h是研发目标，2022堆40,000h是状态参考；均不能当现成产品报价/质保。R3已分清。未发现将DOE未安装价替换BEIS全安装价的错误。

BEIS p19明确变量OPEX为已经年化的堆替换，PEM堆占60%场站资本、假设每11年替换、场站30年。R3选择11/22年显式更换时移除每kg年化储备，避免重复收费，方向正确。DOE运行小时替换只能是另一情景，不能和同一设备11年事件各计一次。30年场站寿命亦不能用作同一堆无需更新的寿命。

## 审核处置

无必须修正的计算项。保留三项限制：10MW参考容量分母在表头写全；混合效率/成本代理和2025旧预测标签持续保留；在R4统一币值前不把GBP2020、DOE基年未确认的USD及题设£9.5/kg放进同一“现价利润”。本审查没有验证真实买方、完整保修、现代安装成本或电力支持资格，不扩大为全项目审计。
