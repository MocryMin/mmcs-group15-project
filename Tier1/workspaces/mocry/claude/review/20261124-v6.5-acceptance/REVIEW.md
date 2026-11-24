# 项目报告 v6.5：验收复审

2026-11-24 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `8fffc2dd58cb49d0bb43d4dfa77f69f1`。

- **标准**：`../20261122-tier1-independent-standard/STANDARD.md`（`9d86960`），未作修改。
- **对象**：`Tier1/workspaces/mocry/codex/technical-report-latex/20261124-v6.5/`（`3b0318e`，校验和更新于 `044f446`）。
  - `report.pdf`、`report-source.zip`、`display-table-evidence.json` 和 `tier1-site-evidence-v6.3.zip` 的哈希均与 `SHA256SUMS.txt` 一致。
  - A4 纸，共 15 页：正文 1–6 页，Tier 1 占第 2–5 页。
- **阅读方式**：按页序通读，并逐页看了正文 1–6 页的 90 dpi 渲染图。
- **一手材料**：题面 `Project_Brief.pdf` 第 18 行（"The main modelling work should be implemented in Python using the Xpress optimiser"）和第 110–111、240–241 行（"Assume that the electrolyser can operate between 20% and 100%"）；问答课第 86、119、125、128 行。
- **核对的证据**：
  - `display-table-evidence.json`；
  - `project-report-20261124-v6.3/{four-day-hydrogen-price.csv, surplus-spells.json, A-seven-module-xpress.json}`；
  - `tier1-commitment-20-20261124/{A-zero-finance.json, A-zero-verification.json}`；
  - v6.2 的 `A-7-finance.json`。
- **抽查结果**：以下数字全部一致：
  - 表 II.3、II.4、II.6、II.7；
  - 表 III.1 共 36 个格，以及合计行和去掉 2021/22 的行，手工逐列加总；
  - 两小时电池按 2.5% 运维计后的 −£0.24m 和 −£2.60m（£51.25m×2.5%=£1.28m）；
  - "about one-sixth"（19.53/118.90=0.164）；
  - 56 小时（两种下限都是 56 小时）。

## 0. 验收结论

**验收通过，可以作为提交候选。没有阻碍提交的问题。非官方估分约 78（区间 75–81），v6.2 约 75。**

v6.2 的 P0（题面规定的 20% 下限）已按实质要求解决：
- 表 II.3 有两行 20%；
- 表 II.7 并列给出 12.5% 和 20% 两套方案的全部财务指标；
- 摘要写明"The brief's 20% minimum reduces the plant to 30.2 MW"；
- §II.3 写明两个下限的来源。

第一次读这份报告的人，能在正文里找到严格按题面计算的答案和完整数字，所以不再构成阻碍。v6.2 的其他 P1 也基本关闭：
- Figure I.1 回到正文，并加了"连续盈余持续时间"图；
- 四天规则下 A 的氢价表（表 II.6）进入正文，包含 £9.50/kg；
- Tier 2B 的 A 改为与 Tier 1 一致的四天、12.5% 承诺，表 III.1 加入一块电池的一列；
- 推荐的 A 方案在两种下限下都由 Python Xpress 逐段复核，与 HiGHS 结果一致到 £0.000001（`A-zero-verification.json`、`A-seven-module-xpress.json`）；
- 符号表完整：$C^B_{ann}$、$W=0.60E$、$\eta=\sqrt{0.90}$、$L$、$N_D$、$x_+$、$\bar z_d$、$m_d$ 都有定义。

版面：正文 6 页没有孤立标题；表格没有跨页；图注、单位和比较基准都写在图注或表注里；Figure II.1 的负值刻度清楚。

## 1. 对 Codex 问题的回答：以 35.2 MW 为首推是否符合题面？

**不是提交阻碍，属于侧重问题。但我有决策分析上的理由，强烈建议把首推改为 30.2 MW（6 台、20%）。**

理由：题面下限为 20% 时，6 台是最优解；产品下限 12.5% 是放宽了约束，6 台的调度在它下面仍然可行。所以：
- **6 台**：在 12.5% 下至少有 £13.46m/年，在 20% 下正好是 £13.46m/年，**两种下限下都成立**。
- **7 台**：最多比 6 台多 £0.22m/年（1.6%）；如果实际下限是 20%，7 台不是最优，收益不会超过 £13.46m。

此外，6 台的资本少 £7.35m，回收期 2.56 年对 2.85 年；NPV 为 £206.9m 对 £210.3m，只差 1.6%。这时以题面下限为首推，既符合"Assume 20%–100%"，又是对下限不确定性稳健的选择。12.5% 下的 7 台降为"若供应商确认 12.5% 可持续运行，第 7 台的增量价值约 £0.22m/年"。

改动只涉及措辞：
- 摘要第二段和 §5.5 第一句换成 6 台；
- 表 II.7 两列交换次序，或给"Brief floor, 20%"列加粗。

如果组里仍保留 35.2 MW 作首推，现稿的条件写法（"subject to … confirmation of operating limits from the supplier"）加上表 II.7 的并列，**也可以提交**。

## 2. 会改变读者理解的地方（建议提交前改）

**R1 补价格支持资格一句（第 5 页 §5.5，"Price support requires a qualifying agreement and traceable electricity inputs"）。**

推荐方案的收益建立在 £7.80/kg 支持价上。表 II.6 显示 £2.50/kg 时收益为零，£5.00/kg 时为 £4.52m。初读者会问：一个 97% 的天数在线、每年从售电中挪用约 120 GWh 的电厂，能否拿到支持价？证据已经回答了这个问题，但正文没有写：
- 6 台（20%）有 34.1% 的输入来自未售出的盈余电量，按盈亏平衡价 £3.85/kg 所需的支持份额是 (3.85−2.50)/(7.80−2.50)=25.5%；
- 7 台（12.5%）是 38.4% 对 24.9%。

也就是说，即使支持价只适用于盈余电量制的氢，推荐方案仍能盈亏平衡。建议加一句。

**R2 求解器角色的措辞（第 3 页 Verification 段）。** 现在第一句是"HiGHS bounds joint sizing in A"，而题面第 18 行要求主要建模用 Xpress。评分人先看到 HiGHS，容易误读为主模型没有用 Xpress。建议改为先写推荐方案："Python Xpress solves the recommended stand-alone A schedules in fixed-boundary subproblems and reproduces the dynamic-programming and HiGHS values at both load floors; HiGHS supplies bounds for the 45-block joint search." 能用完整许可在 Xpress 上解一遍 45/6 固定组合最好；不能也不构成阻碍。

**R3 电池建议应引用已有的一块电池证据（第 5 页 §5.5 Battery；第 6 页表 III.1）。** 现在 §5.5 只写"Obtain a site quote for one block and compare dispatch with and without it"，读起来像还没做。表 III.1 已经有结果：
- A 一块：六窗合计 +£4.65m，去掉 2021/22 为 −£1.54m；
- B 一块：六窗合计 +£7.58m，去掉 2021/22 为 −£1.23m。

建议 §5.5 和摘要第三段各加一句："One block recovers its cost over six windows only because of 2021/22 (A −£1.54m, B −£1.23m without it)."

## 3. 小问题（P2）

- **第 6 页最后一段**："the sum is highest at 11 blocks for each policy"，但表 III.1 没有 11 块这一列，读者无法核对。可以加一列，或者给出 11 块的合计值。
- **第 6 页 §III.1**：A 的回放固定为 6 台（12.5%）。如果按 §1 把首推改成 6 台（20%），台数一致，只是下限不同，加半句说明即可。
- **第 5 页表 II.5 的表注**写"upkeep excluded"，而表 II.3 含运维，正文紧接着给出了含运维的数字。初读者可能短暂困惑，但不影响理解。
- 正文仍只用了 10 页中的 6 页。这是篇幅上的选择，不影响验收。如果还有时间，最值得放入正文的是表 B.1（运行规则网格）或两档价格测试。

## 4. 必答项（标准 §1）对比

| 编号 | v6.2 | v6.5 |
|---|---|---|
| T1-3 盈余与可再生捕获 | 完成 | 完成（Figure I.1 和表 I.2 进入正文） |
| T1-4 题面参数 | 回退 | **完成**（20% 与 12.5% 并列；首推侧重见 §1） |
| T1-6 £9.5/kg | 回退 | **完成**（四天规则下的表 II.6） |
| T1-7 回答关键问题 | 完成 | 完成 |
| T1-11 可视化 | 部分 | **完成**（盈余日内分布、持续时间分布、逐年净增益） |
| T1-14 Xpress | 部分 | **基本完成**（推荐方案经 Xpress 复核；措辞见 R2） |
| T1-15 正文中的模型 | 完成 | 完成（符号完整） |
| 其余 | 完成 | 完成 |

## 5. 打分（非官方）

| 维度 | 权重 | v6.2 | v6.5 | 变化原因 |
|---|---:|---:|---:|---|
| U 理解与深度 | 1 | 79 | 81 | 下限、运行规则、窗口三个维度都在正文 |
| O 原创性 | 1 | 78 | 79 | 持续时间图直观解释 B 为何不可行 |
| W 工作量 | 1 | 80 | 82 | 20% 定容核验、四天 Tier 2B 重放、Xpress 复核 |
| L 论证逻辑 | 1 | 75 | 79 | 建议链完整；首推侧重与资格一句仍可加强 |
| B 背景与文献 | 1 | 70 | 70 | — |
| V 结果有效性 | 1 | 74 | 78 | 交接匹配；推荐方案的数值经两种求解器一致 |
| P 呈现（轻评） | 2 | 70 | 76 | 正文图表清楚，符号完整，版面干净 |
| **加权** | 8 | ≈75 | **≈78** | 区间 75–81；改完 §1 和 R1–R3 后约 79–82 |
