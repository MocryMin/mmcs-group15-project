# Tier 1 独立评价标准

2026-11-22 · mocry-claude · 个人工作区文件，不是组内决定

**独立性声明**：本标准写于审核任何 v5 报告内容之前。写作时只读了下列一手材料；没有读 `20261122-v5/` 目录、Codex 的 v5 广播消息 `24ad229…`，也没有读 `Tier1/public/updates/20261122-tier1-report-v5-review.md`。本文件先于审核单独提交推送，提交时间可核验。

## 0. 依据与效力

| 等级 | 材料 | 用法 |
|---|---|---|
| 约束性 | 题面 `Project_Brief.pdf`（6 页） | Tier 1 的必答问题和默认参数 |
| 约束性 | 报告评分说明 `mmcs_25_26_reports_descriptors.pdf` | 七个维度及权重：前六项各 1，Presentation 为 2 |
| 教师口头要求 | `Project_Launch_Transcript.txt`：Kit（课程负责人）、Kal（客户方，Sopra Steria） | 报告形式、确定性基线、客户关心的财务指标 |
| 教师口头要求 | `261026_MMCS_Project_Overview.pptx` 讲者备注（Kal） | 基线、启发式对照、数据核查、目标与决策对应 |
| 转述 | `TEACHER_CLARIFICATIONS.md` TC-08（Ran Min 转述 11-02 与教师的讨论） | 参数可以用调研值替换，但必须说明来源和理由 |
| 先例 | 六份往届报告 `past_project_reports/20261103-v1/` | 篇幅计法、结构惯例，非规则 |

教师原话摘录（转写稿，非音频逐字核实）：
- Kit："The baseline model, OK, we should think of this as something purely deterministic … We know exactly in the future." 确定性、完美信息的 Tier 1 是合法的。
- Kit："we want to see all of the technical details of everything that you've done. And this has a 10-page limit." 附录"you should assume … is not getting graded"，"please don't put your integer programming formulation in the appendix or … data descriptions"。
- Kal："I need you to show me how long I need to wait until I get to the break-even point"；"risk profiling is also a very important element"；"present at least one outside the box suggestion"；"look at the surplus and deficit and see what is your safest amount of extra investment"。
- 幻灯片备注："The optimiser giving you a number is not evidence that the number is useful. Compare it with doing nothing. Compare it with simple heuristics. Compare it with another plausible investment strategy."；"these files are inputs, not truth … Does total generation reconcile with generation by fuel?"；"whatever objective you choose has to correspond to a client decision"；"when does the extra value stop justifying the extra capital?"

篇幅先例：六份往届报告物理页为 14–18 页，但从 Introduction 到 Conclusion 的正文均为 8–10 页；封面、执行摘要、目录、参考文献和附录在正文之外。所以本标准按**正文 ≤ 10 页**计。这是先例推断，不是书面规则。

## 1. Tier 1 必答项（门槛）

每项判为 完成 / 部分 / 缺失。"缺失"会限制 Amount of Work 和 Logic 两维的档位。

| 编号 | 要求 | 出处 |
|---|---|---|
| T1-1 | 以所给数据代表的基础设施为客户现有状况；Tier 1 不投资新发电。数据是构造系统，不能当作苏格兰输电或真实弃电来解读 | 题面 p.2 |
| T1-2 | 建模前检查数据：日期对齐、缺失与异常、总量与分燃料是否对得上、各技术的发电变化、可再生相对需求何时偏高或偏低；**记录拟议的数据调整** | 题面 p.2；幻灯片 12 |
| T1-3 | 识别何时有**超出即时需求**的电量，并量化这些技术能捕获多少**原本用不掉的可再生能源** | 题面 p.3 |
| T1-4 | 电池和电解槽**容量都是决策变量**；采用题面参数（2 小时、往返 90%、20–80%、€0.288m/MWh；PEM，以 20 MW 为参考，20–100%，55.9 kWh/kg）。偏离须注明来源和理由 | 题面 p.3、p.6；TC-08 |
| T1-5 | **调研并论证电解槽投资成本** | 题面 p.3 |
| T1-6 | 氢价值以 **£9.5/kg 为核心情景**，并测试更低和更高的值；说明它是政策支持基准，不是有保证的售价 | 题面 p.3、p.6 |
| T1-7 | 回答关键问题："应投资多少电池或氢能容量，额外价值是否足以证明投资合理？" | 题面 p.3 |
| T1-8 | 与**不作为基线**和至少一个**简单启发式**比较 | 题面 p.5；幻灯片 9 |
| T1-9 | 敏感性分析：哪些假设影响最大 | 题面 p.5 |
| T1-10 | 区分**数据支持的结论**与**为建模引入的假设** | 题面 p.5 |
| T1-11 | 结果合理性检查与恰当的可视化 | 题面 p.5 |
| T1-12 | 给出**投资回报 / 回收期（盈亏平衡时间）**和**风险**视角 | Kal 转写 |
| T1-13 | 至少一个"跳出框架"的建议 | Kal 转写 |
| T1-14 | Python + Xpress 实现 | 题面 p.1 |
| T1-15 | 公式和数据描述在正文，不放附录 | Kit 转写 |

**允许但不要求的**：逐日时序储能（题面说"不需要"）、多年回放、电网约束、氢储存再发电、分期投资、外部数据。它们若加入，就按 §3 的风险项审查，不因为"做了更多"自动加分。

## 2. 七个维度在本项目 Tier 1 中的具体含义

**U · Understanding & Depth（1）** 达到 A3 需要：
- 优化模型能**独立复现**：集合、参数、变量、单位、目标、约束齐全；容量变量确实约束运行（电池的能量/功率/可用区间，电解槽的最小负荷与启停）；
- 年化成本正确，价格基年一致；
- 售电、储电、制氢之间的**机会成本**处理正确，没有重复计算；
- 达到 A2 还要求对模型性质有清楚的推理，例如为什么会取零或取边界解、什么在约束最优解。

**O · Originality（1）**：A3 需要在题面方向之外有若干改进，例如归因方法、门槛或合同空间、政策区分等。Kal 要求至少一个"outside the box"建议。只堆机制不算原创；原创要服务于回答客户问题。

**W · Amount of Work（1）**：A3 要求"All questions raised in the project description are addressed"，即 §1 的 T1-1 至 T1-13 全部完成。

**L · Logic of Argument（1）**：
- 主线为：数据 → 基线 → 模型 → 结果 → 检验 → 建议；
- 术语先定义后使用；
- 目标对应客户决策；
- **结论直接回答"投什么、投多少、为什么优于简单方案、什么会改变结论"**；
- 标题数字与正文和表格一致。

**B · Background & References（1）**：所有偏离题面的参数都有来源；"All sections … adequately supported by references"意味着方法也要有文献，不能只有参数来源；引用格式可追溯（URL、日期）。

**V · Validity & Assessment（1）**：
- 结果能从数据与模型推出；
- 有独立核验（简单情形手算、两种实现对照、约束复核）；
- 讨论局限；
- **判断结论是否是建模假设的产物**，例如日分辨率让电池价值消失、外部假设决定规模；
- 敏感性覆盖驱动结论的那几个参数。

**P · Presentation（2）**：本轮侧重内容审核，此项只记显著问题，不作主要依据。

## 3. 内容风险清单（审核时逐项检查）

- **R1 外部数据替换。** 若用外部数据（例如更高分辨率的时序）替换或增补所给数据：
  - (a) 必须说明所给数据为什么不够；
  - (b) 必须保留基于**所给数据**的结果作为参照；
  - (c) 必须核对外部数据与所给数据是否相符；
  - (d) 不得使 Tier 1 的答案只能由外部数据得出。
  题面允许用公开信息补充"particularly for technology investment costs or scenarios"，并要求"using the … historical generation profiles represented in the supplied data"。
- **R2 结论由题面之外的假设驱动。** 例如承购上限、净回值、市场吸收能力、授权条款。若这些假设决定了容量，必须明示，作为情景检验，并给出门槛。
- **R3 规模的合理性。** 推荐容量与可捕获盈余、市场或买方规模、资本额相比是否可信？Kal 要求"safest amount of extra investment"。
- **R4 "可再生"与"总电量"混用。** 题面问的是可再生；以总电量计的捕获必须说明归因方法。
- **R5 £9.5/kg 核心情景是否报告。** 题面附录给出推导 £241/MWh × 39.4 kWh/kg ÷ 1000 = £9.5/kg。若主情景改用别的值，必须同时报告 £9.5 的结果。
- **R6 电池结论。** 若为零，要说明是成本、日分辨率还是模型设定导致的，并给出能改变结论的成本门槛。
- **R7 口径一致。** 单年与多年、2020 价格与名义价格、年化与 NPV 不得在同一论证中混用而不加说明。
- **R8 Tier 1 与 Tier 2 的边界。** Tier 1 中混入不确定性、预测或时序策略，会挤占篇幅、模糊 Tier 2 的增量。Tier 1 应自成一个完整答案。
- **R9 风险视角。** 是否报告下行情景（最差年份、价格下跌、成本上升）及其后果？

## 4. 打分规则

- 七个维度各给一个分数，按爱丁堡档位：A1 90+，A2 80–89，A3 70–79，B 60–69，C 50–59，D 40–49。
- 加权平均权重为 1,1,1,1,1,1,2。
- 门槛项缺失时，W 不超过 B 档，L 不超过 A3 低段。
- 本轮只评 Tier 1。全报告的分数还取决于 Tier 2 与整体建议，不在此范围。
- 所有分数都是非官方的内部估计。
