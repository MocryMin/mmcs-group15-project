# v4.1 学术报告候选：独立审核

2026-11-10 · mocry-claude（应 mocry-codex 请求 `1bff0d2d1ba0416fa541b818d5c2012f`）· 个人工作区审核稿，不是组内决定

## 0. 审核对象与方法

- 对象：`Tier1/workspaces/mocry/codex/technical-report-latex/20261108-v4.1/`。`report.pdf` sha256 `416b9694…`、ZIP `8e027c74…`，与 `VERSION.json` 一致。
- 按 `REVIEW_REQUEST.md` 的六项检查进行：
  1. 10 页全文按顺序通读，并逐页查看渲染；
  2. 公式 (II.1)–(II.4) 与 `run_study.py` 的 `solve()`（L129–211）逐项对照；
  3. 表 II.3、II.4 及 §4.3 的全部数字，与 ZIP 内 `results/cases.csv`、`additional_cases.csv`、`annual_replay.csv`、`contract_grid.csv` 逐一核对；
  4. 评分按随包 `mmcs_25_26_reports_descriptors.pdf`：前六项权重 1，Presentation 权重 2。
- 第 III 章按请求只评设计，不当作已完成的 Tier 2B 结果打分。
- 尊重本人的框架要求：学术版式，不恢复 KPI 卡片、彩色标题和首页决策框。

## 1. 结论

**数学与数字：没有发现计算错误。** 公式与代码一致，单位、定义域、A/B 政策、年化成本和零投资对照都正确。抽查的 30 余个数字全部可从存档结果复现，包括 H₂ 吨数、六年均值、Table II.4 全部六行、£9.64m 差额、£96.4k 电池年成本、£13.3k → £4.3k 电池复核、£23.97m − 12.39 − 0.52 − 2.49 = £8.57m 分解，以及 NPV £131.8m 与回收期 2.64 年。

**建议：采纳为全组 Tier 1 的基础稿，但先修三处 P0。** P0 合计约半页改动，不涉及重算。

**预期得分（非官方内部估计）：** 仅就 Tier 1 部分按现稿约 **72 分**（A3，区间 68–76）；修完 P0 和 P1 后约 76–79 分。若全报告按现状提交（第 III 章只有规格），工作量和结果有效性两项会明显下降，但这不是本次评估的对象。

## 2. 按严重程度排列的问题

### P0：采纳前必须处理

**P0-1 页数风险（全文结构）。** 教师在启动课上只说"this has a 10-page limit"（`Project_Launch_Transcript_Timed.txt` L236），题面与评分说明都没有写封面、摘要、目录和参考文献是否计入。现稿已用满 10 个物理页，而第 III 章只有 1 页；按本人框架补足 4 页后将是 13 个物理页。`README.md` 也写明"不冒称取得了新学校条款"，即该排除规则尚未得到确认。
- 修改：向课程组书面确认（课程澄清通常由 Kit Searle 发布）。确认之前，按"10 个物理页"留后路：
  - 封面、摘要、目录合为一页。三级目录在 10 页报告中价值低，可压成 4 行或删去；
  - 回收第 2 页底部约 1/4 的空白；
  - Table II.3(a) 压缩为两行，见 P1-5；
  - 参考文献改为小号双栏。
  这几项合计可省出约 1.3 页。

**P0-2 结论没有给出决策（p.6 §4.3 末段）。** "Assess a 20 MW electrolyser against actual offtake and dispatch terms before committing £29.2m, retaining B's loss-year risk." 这不是对题面 "what to invest in, how much to invest and why … what could cause the recommendation to change" 的回答。所需数字报告里都已有，只是没有组织成结论。
- 建议改写为条件式建议，约 5 行：
  - 投资 1 个 20 MW 电解槽，不投电池。
  - 若取得转售授权（A）：六年均值 +£10.94m/年，最弱的 2021 年 +£6.29m。成立条件为 10 t/day 时净回值 ≥ £4.61/kg，或 £7.80/kg 时承购 ≥ 2.23 t/day。
  - 若无转售授权（B）：六年均值 +£2.12m/年，但 6 年中 3 年亏损；2023 年需净回值 ≥ £12.08/kg 才能保本。
  - 在 10 t/day 合同下不要扩到 40 MW（A 降到 £7.47m，B 为 −£3.75m）。
  - 电池即使免费充电，收入上限 £54.0k/模块·年，也只覆盖年成本 £96.4k 的 56%。
  - 会改变结论的是承购量、净回值和转售权利三项，见 Figure II.1 与 Table II.4。

**P0-3 题面基准 £9.50/kg 的结果没有报告，且缺少与 £7.80 的对应关系（p.3 §2.2；Table II.4）。**
- 正文说 "The brief's £9.50/kg hydrogen benchmark has no explicit price base"，随即改用 HAR1 2012 价格 £175/MWh 换算出的 £7.80。但包内 `research/R3-hydrogen/REPORT.md` L61 已查明：£9.50 ≈ HAR1 加权平均执行价 £241/MWh × 39.4 kWh/kg，与 £175/MWh（2012 价格）出自同一份 DESNZ 公告，公告本身没有给出 £241 的价格基年。所以 £7.80 是对同一来源做了价格基年统一，并非改用别的假设。报告应写出这层关系，否则读者会以为偏离了题面。
- 题面明确要求以 £9.50 为初始情景。该结果已在 `contract_grid.csv` 中（2023、10 t/day）：A 选 20 MW，**+£13.88m/年**；B 不投资。正文没有这个数，Figure II.1 也只能看出等值线位置。
- 修改：§2.2 加一句写明上述对应关系；Table II.4 加一行"Brief benchmark £9.50/kg"，A +£13.88m，B 0。
- 定性：这是**有意的情景选择**，不是数值错误，但目前可追溯性不足，也缺少与题面基准的对照。

### P1：应修

**P1-1 销售下限约束不在公式里（p.4 (II.2) vs Table II.4 前两行）。** "Recover half of lost sales" 和 "Retain 99.99% of sales" 用的是 `run_study.py` L182 的 `Σ(q+r) ≥ service_floor`，(II.2a)–(II.2e) 中没有。建议补 (II.2f)：Σₜ(qₜ+rₜ) ≥ φ·Σₜ q⁰ₜ，其中 q⁰ 为同政策零投资解，φ ∈ [0,1]。
- 顺带：`cases.csv` 里还有 φ 对应 25% 和 75% 恢复的结果（£7.46m、£2.46m），可补一句：恢复少售电的边际代价不是常数：恢复最先 25% 时每 GWh 约损失 £0.028m，恢复 50%–75% 一段时每 GWh 约 £0.069m。这是"转售权利值多少钱"的直接定价，是可加的亮点。

**P1-2 标题数与敏感性的口径混用，且"stress year"的说法不准确（p.1、p.5 §4.1）。**
- 头条 £10.94m 是 2020–25 六年均值，而全部敏感性、盈亏平衡点、NPV 和回收期都基于 2023 单年。
- 2023 是盈余最少的年份，是 **B 的**压力年；对 A 而言，2023 的 £8.57m 是第二低，最弱的是 2021 年的 £6.29m。
- 修改：§4.1 写明"2023 是盈余最少、对 B 最不利的年份；对 A 而言最弱的是 2021 年"，并说明 NPV 用的单年口径相对六年均值偏保守。

**P1-3 先用后定义（按顺序阅读）。**
- p.2："the two price-unit columns retain their factor of 24"：读者不知道价格文件有两个单位列。
- p.2："strict quality flag"：判定标准没有定义（1,929 天满足）。
- p.5 Table II.3(b)："Capture" 列在 §4.2 才定义为 Cₜ = min(hₜ, Sₜ)。可在表注写"Capture = Σₜ min(hₜ, Sₜ)"。
- p.4 (II.3) 之后没有给出 a_B、a_H 的数值：a_B = £96.4k/模块·年要到 p.6 才出现，a_H = £3.01m/模块·年全文没有出现。读者无法仅凭第 4 页复现 (II.1)。
- p.3 Table II.1："2.9% annual maintenance convention" 没有说明基数。按数值推算，基数是每 MW 两小时电池的资本（£256,235 × 2 × 2.9% = £14,862）。

**P1-4 图形缺陷。**
- Figure II.1 Policy B 面板右上角，"60 MW"、"40 MW"和等值线标签"2"互相重叠，无法辨认。
- Figure I.1 中"Known historical paths"、"Investment sensitivities"、"Sell / store / hydrogen"超出方框；"same formulation"标签位置不明，看不出它连接哪两个框。
- 两处都影响权重为 2 的 Presentation。

**P1-5 信息密度（本人优先项）。**
- Table II.3(a) 共 30 格，其中 22 格为 0，可改为两行（"Joint / electrolyser only"与"Fixed 20 MW"）加一句"battery-only and no-investment rows are zero in both policies"，省约 0.12 页。
- 第 2 页底部约 1/4 空白。
- 目录独占一页。

**P1-6 参考文献是六项中最弱的一项（Background & References）。**
- 共 10 条：3 条组内材料（[3][9][10]），2 条课程材料（[1][2]），5 条外部来源（[4]–[8]）都是参数来源；方法论文献为零。评分说明 A3 要求 "all sections … adequately supported by references to relevant background and precursor items"。
- 建议补 3–5 条：储能套利价值与时序（如 Sioshansi 等 2009，*Energy Economics*）、制氢与容量规划的 MILP 文献，以及第 III 章的电价预测基准（Lago 等 2021，*Applied Energy*）。
- 网页来源 [6] 和 [8] 应加 URL 和访问日期；[2] 中的 "documented discussion clarifications" 应指明文件。

### P2：小问题

- **P2-1** p.6 "All 60 exported Xpress schedules" 与包内 README/消息里的"64 方案"：实为 60 个 Xpress 求解加 4 个非 Xpress（2 个规则调度、2 个枚举）。一句话说明即可。
- **P2-2** L 的单位：Table II.2 为 kg/day，Table II.1 为 10,000 kg/day，正文和 Table II.4 为 t/day。建议统一用 t/day，κ 用 MWh/t。
- **P2-3** 第 III 章 (III.2) 说保留 Tier 1 的 throughput 约束。但 Tier 1 的电池时序复核代码在 `chronological=True` 时不加 (II.2b)，只受库存上限约束。结果不受影响，表述应与实现一致。
- **P2-4** Table II.4 用表注说明"sales floors/50 t 为优化容量，其余固定"，不如加一列"容量：固定/优化"直观。
- **P2-5** §4.3 标题"Validation and conclusion"把两件事合在一起，P0-2 的结论段宜单独成段。
- **P2-6** 数字精度可统一：£256,235/MWh 与 £14,862/MW-year 精确到个位，其余为三位有效数字。

## 3. 第 III 章：设计缺口（不计分）

1. **按现行信息结构，预测对决策没有价值。** 当天的 Gₜ、Dₜ、pₜ 已知，又没有电池，电解槽没有跨日状态，每天的最优动作只看当天。照此做完实验，结论只能是"预测无关"。§4 第二段已有意识地加入固定非零电池诊断；但我在 `1620bdc` 中按同样信息结构做的 7 日滚动电池实验显示，2024–25 完美预见的套利值也只有约 £1.5k/年·可用 MWh，与报告 §4.3 的时序复核（£4.3k/模块，约 £2.4k/可用 MWh）同一量级。建议由 Ran Min 决定加入一个跨期耦合：
   - 日前承诺：售电与启停提前一天确定，偏差按不利价格结算；
   - 氢气周度或月度交付合同（或氢储罐）；
   - 多年情景压力测试。
2. **"2020–22 训练"必须明确为滚动重估。** 在 `1620bdc` 的回测中，只在 2020–22 拟合一次的岭回归在 2024–25 上的电价误差是七日季节朴素的 0.88–1.58 倍，可再生发电 7 日为 1.30 倍，原因是 2022 年危机价格水平。
3. **基线太弱。** 只和七日季节朴素比会高估模型价值，应加入持续值和 28 日均值；电价超过 3 天后没有模型显著优于 28 日均值。
4. **按序列选模型。** 需求用日历回归加残差修正最好（1 日 MAE 20.7 GWh，优于岭回归的 23.1），发电用岭回归，电价分段处理。详见 `Tier2/workspaces/mocry/claude/forecasting/20261110-v1/REPORT.md`。
5. **评价指标。** 加 Diebold–Mariano 检验、盈余日事件评分，以及"占完美信息价值的比例"。MAE 与决策价值的排序不一致。
6. **题面 2B 的另一半要求没有设计。** 题面要求考察季节性、持续高低可再生时期、异常高需求或高价，说明目标函数为何代表客户利益（ROI、可再生利用、韧性），并找出会改变策略的假设。第 III 章目前只有预测与控制，应加入压力测试设计和目标讨论。
7. **容量选择窗口。** 2020–22 包含 2022 年危机价格，用它选出的容量应与六年选择对照报告。

## 4. 评分（非官方内部估计，按随包评分说明）

| 维度 | 权重 | 分数 | 依据 |
|---|---:|---:|---|
| Understanding & depth | 1 | 76 | 模型完整正确，整数模块，两种政策，年化成本，归因区间，时序复核 |
| Originality | 1 | 75 | A/B 政策区分、7,930 点合同图、销售下限、从上游重建数据 |
| Amount of work | 1 | 78 | 数据重建、64 个调度、六年回放、独立实现对照 |
| Logic of argument | 1 | 70 | 顺序与先定义后使用总体好；结论不成决策（P0-2），口径混用（P1-2），约束缺式（P1-1） |
| Background & references | 1 | 64 | 仅参数来源，无方法论文献（P1-6） |
| Validity & assessment | 1 | 75 | 核对充分；缺题面基准对照（P0-3） |
| Presentation | 2 | 70 | 版式干净；两图有缺陷（P1-4），信息密度可提升（P1-5） |
| **加权平均** | 8 | **≈72** | A3 档；修完 P0 和 P1 后约 76–79 |

分数是我对评分说明各档描述的判断，不代表官方成绩。

## 5. 复核记录

- 公式 ↔ 代码：(II.1) 对应 `revenue - reference_revenue - battery_annual·n_b - hydrogen_annual·n_h`，按 `years` 归一。(II.2a) 对应 L163/L167；(II.2b) 对应 L174；(II.2c) 对应 L180；(II.2d) 对应 L165 与 `h` 的上界 `offtake/kg_per_gwh`；政策 B 对应 `q` 的下界 `min(g,d)`。A 的零投资对照只在 pₜ ≥ 0 时售电（L126），与 "B sells even at negative prices" 一致。
- 电池：€288,000 × 0.8897 = £256,235/MWh；a_B = 3 × 256,235 × CRF(5%, 15 年) + 1.5 × 14,862 ≈ £96.4k。
- 电解槽：a_H = 29.209 × CRF(5%, 30 年) + 9.792 × (1.05⁻¹¹ + 1.05⁻²²) × CRF + 0.517 ≈ £3.01m；NPV = 11.06 × 15.372 − 29.21 − 9.07 ≈ £131.8m。
- 氢气：£175 × 39.4/1000 × 108.7/96.1 = £7.799/kg；171.84 GWh / 55.9 = 3,074 t。
- 承购上限：2023 年 29 个盈余日的最小盈余为 0.742 GWh > 0.559，所以 16.21 GWh 的上界成立。
