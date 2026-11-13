# 小型 Transformer 与外部特征：2026-11-09

这是用户询问后的模型及数据来源分析。当前未训练任何新模型、未下载完整外部特征归档、未修改 v4.1 报告或远程仓库。用户尚未选定最终预测器。

## 同参数 Transformer 的可行性

小型 Transformer 值得与 LSTM 进行同规模对照。约 2,452 个总日观测、约 1,096 个初始训练日，不足以预先证明任一架构必胜或必败。参数相近时，归纳偏好、可用特征、正则化、优化过程及市场状态变化仍然不同。多窗口重叠不增加同等数量的独立观测。

用于说明参数匹配的可计算例子：每个历史日 8 个输入特征，直接输出未来 7 日的 3 个量，共 21 个输出；两者使用相同长度的历史窗口。

| 架构 | 配置 | 可训练参数数 |
|---|---|---:|
| 一层 LSTM | hidden size 32，末隐藏状态接线性预测头 | 6,069 |
| 一层 Transformer encoder | d_model 24，3 heads，FFN width 56，均值池化后接线性头 | 6,005 |

以上为按标准层形状作的参数核算，不是已训练网络。LSTM 启用两组偏置；Transformer 包含输入线性投影、多头注意力、两层 FFN、两个 LayerNorm 和输出头，使用固定正弦位置编码，没有额外末端 LayerNorm 或可训练嵌入；池化无参数。实际代码若改变这些组件须重新统计。计算公式：LSTM 为 `4*h*F+4*h*h+8*h+h*O+O`；Transformer 为 `(F*d+d)+(4*d*d+2*d*ff+9*d+ff)+(d*O+O)`。

不直接使用默认大尺寸编码器。匹配完整网络参数，包括投影、位置嵌入和输出头。固定相同信息截止、输入历史、预测跨度、目标缩放、调参预算与控制器规则，在验证期选参数，最终测试不用于反复选架构。重复随机种子，分别检查预测误差、实际 MPC 收益和压力时段。固定日历位置/已知日历输入为时序编码提供顺序信息；没有额外未验证的合同罚则。

论文依据仅用于支持需要实测，而非证明本课程结果：LTSF-Linear 论文报告其长期预测基准中简单线性模型表现很强；PatchTST 说明针对时序设计的 patch Transformer 也可以有效。两篇都不能直接证明本项目从零训练的六千参数 Transformer 优于 LSTM。

## 特征优先级

1. **先使用课内已给信息和可提前知道的日历。** 现有分燃料发电、独立风场、总供给/需求/价格的滞后与过去滚动统计，及净需求、风光占比、星期、季节和银行假日。不要只使用最简三列而忽略已有燃料分解。任何滚动统计仅使用截至当日的数据。
2. **优先核查 NESO 当时已经公布的需求及风光预测。** 可作外部输入或独立预测基准，而非直接替换课程目标。它们的信息包含专业预测流程；模型改进要区分外部信息增益与架构增益。
3. **有针对性地核查天气特征。** 温度、轮毂附近高度的风速和辐照度可构成候选。全国序列需匹配区域尺度；独立模拟风场只有确认位置/模拟定义后才能声称对应当地天气。历史观测作为过去特征还须考虑发布时间；预测未来天气应使用当时发布的预报，不能使用未来实测或事后重分析当成实时已知值。
4. **燃气、碳价等市场特征为后续候选。** 只取当时已知的滞后/报价，先核查定义、可得性和历史覆盖；本轮未验证适用的完整价格数据来源。

新特征增加输入信息，不自动增加目标训练样本数。外部预测和课程构造序列的定义可能不同，需训练期校准和验证。A/B 资产边界及决策约束不随特征变化。

## 本轮已核实的数据入口与限制

- [NESO 日前需求预测](https://www.neso.energy/data-portal/1-day-ahead-demand-forecast)：已读网页与官方 CKAN 元数据。历史归档描述从 2018 年开始；当前发布通常每天两次。元数据将 National Demand 定义为 GB generation requirement，排除站用、抽蓄泵用电及互联出口。尚未逐行核查其与课程需求列的口径和完整性。
- [NESO 2–14 天需求预测](https://www.neso.energy/data-portal/2-14-days-ahead-national-demand-forecast)：已读网页与元数据，历史归档描述从 2020 年开始；当前另有半小时预测与 cardinal-point 文件。不能未经格式核查把 cardinal points 当成全天平均。
- [NESO 嵌入式风电和光伏预测](https://www.neso.energy/data-portal/embedded-wind-and-solar-forecasts)：页面有逐年历史归档，官方元数据包含 2019/2020/2021 等归档及 0–14 天预测说明。Embedded 的范围不同于全部风电/太阳能，也不同于独立模拟风场，不能直接当成其真值或完整替代预测。
- [Open-Meteo Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api)：连续序列由各次运行的最初几小时拼接，不等同在某个历史时点取得完整未来七天预测。
- [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api)：按固定提前量提供预测。多数模型归档自 2024 年，个别模型/变量更早；须按变量核覆盖。
- [Open-Meteo Single Runs](https://open-meteo.com/en/docs/single-runs-api)：可按运行初始化时刻取得完整预报；当前说明 ECMWF IFS 自 2024-03，多数其他模型自 2026-04-02。初始化时间不等于实际公开时间，仍需考虑运算/发布延迟。这一个接口不能直接覆盖既定 2020–22 训练期；不据此断言其他来源没有更早的归档。
- [英国银行假日官方入口](https://www.gov.uk/bank-holidays)：地区日历不同。历史日期及特殊临时假日的宣布时间仍需按年份核对。

所有在线访问为匿名隔离 Playwright MCP。仅核入口和文档/元数据，没有声称已取得全部历史特征数据。

## 可解释的对照设计

以 LSTM 和等参数小型 Transformer，各比较基础特征与增强特征。增强组先增加日历/课内燃料信息，再单独检查外部官方预测的增益。Ridge 和季节朴素继续作基准；LSTM+attention 为此前提出的模块消融候选。需要保持预测器/特征改进能够独立归因，不预设复杂模型一定最佳。

当前推荐资产仍为零电池；非零电池诊断中才有待管理的跨日库存。更强的预测器不改变无库存且无跨期限制时的按日可分离性质。

## 方法来源

- [Are Transformers Effective for Time Series Forecasting?](https://arxiv.org/abs/2205.13504)，本轮读取摘要。
- [A Time Series is Worth 64 Words: Long-term Forecasting with Transformers](https://arxiv.org/abs/2211.14730)，本轮读取摘要。
- [PyTorch TransformerEncoderLayer](https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html)，本轮读取官方结构及参数定义。
