# R1 对 R4 财务来源的定向交叉审核

2026-11-03，Europe/London。独立读取主控指定的原始捕获，不修改 R4 或根报告。本页只审核汇率方向和贴现率适用范围，并记录最后一次 ONS 下载结果。

**汇率：通过。** [ECB 原始年度 CSV](https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?startPeriod=2020&endPeriod=2020&format=csvdata) 的行明确为 `FREQ=A, CURRENCY=GBP, CURRENCY_DENOM=EUR, TIME_PERIOD=2020, OBS_VALUE=0.8897040856031, UNIT=GBP`，系列键 `EXR.A.GBP.EUR.SP00.A`。独立读取 [ECB 定义正文](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)，其表明所有货币以欧元为基础货币报价。因此 2020 年该年度系列为 **0.8897040856031 GBP / EUR**；欧元数额转英镑须乘该数，不能倒用。该值是参考汇率，用于建模换算，不是已取得的可执行银行报价。将 EUR2020 成本依该汇率转为 GBP2020 是清楚的统一计价约定；不能因此把其他年份的欧元报价自动当成 EUR2020。

**Green Book：适用范围判断通过。** 独立读取 [Green Book 2026 正文](https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026) 的 “Discounting” 与 Annex A “Additional sensitivity analysis”。前者明确是社会成本与社会收益的 Social Time Preference Rate（STPR，社会时间偏好率），应先去除一般物价变化，再采用实质贴现率；本轮捕获的2026版具体写 **1–30年3.00%、31–75年2.50%、76年起2.25%**，不能把旧版3.5%当成本次来源的数值。Annex A 另外区分以政府成本比较为目的、匹配合同久期的实质无风险国债利率敏感性分析。这些均不能直接确定假想私人新能源投资者的资本成本或最低回报要求。私人项目门槛率应另作透明假设及敏感性，不能以“Green Book规定”证明该值。

**ONS 最后下载：成功。** 指定的公开 generator URL 经匿名 Playwright request 返回200，响应 MIME 为 `application/octet-stream;charset=utf-8`，实际正文经读取确认是标题为 `CPI INDEX 00: ALL ITEMS 2015=100`、CDID=`D7BT`、dataset=`MM23` 的 CSV。原始响应保存在 [JSON](https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23)，正文另存为 [CSV](https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23)。发布时间字段为2026-10-21，下一次发布2026-11-18。该指数可以支持统一购买力计价的明确代理选择，但不是工业设备价格指数；不得把未发布的2026年末月份或全年平均补作官方观测。完整时期/缺失处理由 R4 自行验收。

补充直接读取所需行：2020年年均指数为 **108.7**；月度行覆盖 **2020 JAN 至2026 SEP**，其中2026 SEP为 **144.1**。2026 OCT–DEC及2026全年平均未出现。若选择2020年平均购买力为基准，对月度名义英镑采用 `nominal_GBP × 108.7 / CPI_month`；这只是通胀归一化，不同时完成折现或设备相对价格调整。

本次两项核心结论无阻塞分歧。首轮 R1 快照保持不变；浏览器锁已释放，按主控指令停止进一步来源扩展。
