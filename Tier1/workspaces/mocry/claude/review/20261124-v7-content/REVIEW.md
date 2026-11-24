# 项目报告 v7：内容审核

2026-11-24 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `2a8e5658a479411b8ba10a747cd8a43f`。

- **标准**：`../20261122-tier1-independent-standard/STANDARD.md`（`9d86960`），未作修改。
- **对象**：`Tier1/workspaces/mocry/codex/technical-report-latex/20261124-v7/`（`1bb26de`，校验和更新于 `2dfb603`）。
  - 7 个文件的哈希均与 `SHA256SUMS.txt` 一致。
  - 共 16 页：正文 1–6 页，Tier 1 占第 2–5 页。
- **阅读方式**：按页序通读，并逐页看了正文 1–6 页的 90 dpi 渲染图。
- **一手材料**：题面 `Project_Brief.pdf`。
  - 第 18 行要求主要建模用 Python 和 Xpress。
  - 第 91–98 行是 Tier 1 的题目"Making use of surplus renewable energy … how much otherwise unused renewable energy these technologies can capture"。
  - 第 138 行问"How much renewable generation could be produced but not usefully consumed?"
- **核对**：
  - `renewable-attribution.csv` 与表 C.3 九行逐格一致；
  - `xpress-comparison.csv` 与表 C.1 六行、§5.1 和 §C.2 的上界一致；
  - §5.4 的 −£0.23m 已按 CU 的意见修正；
  - 表 III.1 与 v6.5 相同。
  - 我还用 v7 半小时输入、日燃料表和 `A-zero-0.2-xpress.npz`、`A-zero-0.125-xpress.npz` 独立重算了推荐方案的输入构成（脚本在我的 scratchpad，未入库）。

## 0. 结论

**没有阻碍提交的问题。非官方估分约 79（区间 76–82），v6.5 约 78。**

v6.5 验收提出的四项全部采纳：
- 首推改为题面 20% 下限下的 6 台（30.2 MW）；
- §5.5 加了价格支持资格一句；
- 求解器措辞改为以 Xpress 为先；
- 电池建议引用了表 III.1 的一块电池结果。

此外有两项实质进步：
- **完整许可的 Python Xpress。** 用学院完整许可的 Python Xpress 独立完成了日参照和半小时两种政策的容量定容；A 的模型有 530,466 列、850,501 行，已超出 Community 版的规模。我的标准中 T1-14 的遗留问题至此关闭。
- **可再生盈余的捕获量。** §5.3 和表 C.3 首次回答了题面 Tier 1 的核心问题：可再生盈余有多少、被捕获了多少、还剩多少。

剩下一个**实质性的说明问题**（M1）：新加的可再生数字与 §5.5 的资格句放在一起，显示推荐方案几乎不使用可再生盈余，而资格句没有说明这一点。另有两项一致性和清晰度问题（M2、M3）。

## 1. 实质性说明问题（建议提交前改）

**M1 推荐方案的可再生盈余使用量与价格支持资格（第 4 页 §5.3；第 5 页 §5.5 "All-fuel surplus supplies 34% of their electricity"；附录 C.4 和 C.5）。**

- **事实。** 推荐的 6 台方案（20% 下限）年输入 190.4 GWh，其中：
  - 来自所有燃料的盈余约 33–34%；
  - 按日燃料份额折算的**可再生**盈余只有 28.1 GWh（表 C.3），即 **14.8%**。我独立重算得 14.8%；7 台（12.5%）为 16.5%。
  - 其余约 125 GWh 是从售电中挪来的电（§C.4 末段）。
  - 6 台只捕获了 2,432 GWh/年可再生盈余中的 **1.2%**。
- **问题。** §5.5 写"six break even if about 25% of output earns £7.80/kg … All-fuel surplus supplies 34%"，读者会理解为"即使只有盈余电制的氢拿到支持价也能保本"。但同一份报告在附录 C.5 中说低碳氢标准要求低于 20 gCO₂e/MJ 并有可核实的路径，而所有燃料的盈余里含燃气。如果支持价只适用于可再生盈余电，14.8% 低于所需的 25.5%，固定调度下 6 台**不能保本**。两处放在一起，有逻辑漏洞，细心的评分人能看出来。
- **为什么不是阻碍。** 建议本身是"assess … depends on the buyer's terms"，£7.80/kg 是写明的情景假设，§5.5 也写了"Support requires traceable supply"。所以结论不是错的，只是写得过于乐观。
- **修改：措辞，加一句结论。**
  1. §5.5 改为："All-fuel surplus supplies 34% of their electricity, but renewable surplus (by daily fuel share) only about 15%. If support were limited to renewable surplus, six modules would not break even at fixed dispatch; the case therefore needs a low-carbon supply arrangement for the diverted power."
  2. §5.3 加一句解读："The stand-alone plant captures about 1% of renewable surplus; its value comes mainly from electricity that would otherwise be sold. Batteries capture far more (883 GWh in joint A) but are not recommended at current costs." 这是对题面"how much otherwise unused renewable energy these technologies can capture"最直接的回答，而且是一个有洞见的结论：在四天运行规则下，单靠盈余电撑不起电解槽。
  3. 摘要可加半句可再生捕获量，因为这是题面 Tier 1 的标题问题。
  4. 如果时间允许，在四天规则下重跑一次两档价格（只给可再生盈余电制的氢支持价），替换附录 C.5 中半小时启停的 £6.06m。

**M2 价格敏感性表与首推方案的下限不一致（第 5 页表 II.6）。** 首推已改为 20% 下的 6 台，但表 II.6 仍是 12.5% 下的 7 台（£7.80/kg 一列为 7 台、£13.68m）。读者会疑惑：在首推方案下，£5.00 和 £9.50 分别是什么结果？建议在 20% 下重跑这 4 个价格点（`four-day-hydrogen-price.csv` 只有 12.5%）；或者至少在表注里写明"12.5% product floor; the 20% plan's break-even is £3.85/kg (Table II.7)"。

**M3 Xpress 结果：区分"容量已认证"和"调度价值的剩余缺口"（第 4 页 §5.1 末句；第 A5 页表 C.1）。** 这是 Codex 专门问的。附录 C.2 正文写清楚了：最近的竞争组合（46/6）的上界比 45/6 的可行解低 £7,030/年（20% 下）或 £8,259/年（12.5% 下），所以容量已认证；45/6 自身仍有 £2,600 或 £1,999/年的调度缺口。但 §5.1 一句"Xpress certifies the 20% capacities, with gains within £2,600/year … of their upper bounds"把两件事合在一起，表 C.1 也只有被选方案自己的上界。建议：
- 表 C.1 加一列"Best other counts, upper bound"（数据就在 `xpress-comparison.csv` 的 `alternative_upper_mGBP`）；
- §5.1 改为两句："No other capacity can exceed the selected counts: the best alternative's upper bound is £7,030/year below the selected plan's feasible gain. The selected plan's dispatch is within £2,600/year of its own bound."

## 2. 小问题（P2）

- **第 2 页 §II.1** 先写"We first size two-hour batteries … using daily data (Table II.5)"，但两小时的结果在 §5.4，排在四小时结果之后。叙述顺序与结果顺序不一致。可改为"We report the four-hour half-hour model first and the daily two-hour benchmark in §5.4"。
- **第 4 页 §5.3** 首句的 2,432 GWh/年最好注明是 5,165 GWh/年总盈余中的可再生部分（约 47%），读者就能与第 1 页的数字对上。
- **第 A5 页表 C.1** 中 A 20% 的上界 118.820807 与正文"HiGHS … tighter 20% upper bound of £118.819824m"并存，且 CU 指出 HiGHS 证书里的这个字段自相矛盾。建议重新生成该证书字段，正文只用一个上界。
- **封面**没有作者姓名或学号。请确认课程提交要求；若需要，补上。
- **转入 Tier 2B（第 5–6 页）** 已很顺：§5.5 指向表 III.1，并写明"A uses six modules at 12.5% in the replay"。§III.1 第一句可加"(the recommended count, at the product floor)"。
- **版面**：没有孤立标题，表格没有跨页；第 5 页三张表略挤但清楚。正文仍只用了 10 页中的 6 页。

## 3. 必答项（标准 §1）对比

| 编号 | v6.5 | v7 |
|---|---|---|
| T1-3 盈余与可再生捕获 | 完成（只有全燃料盈余） | **完成，且有加强**：可再生盈余的存量、捕获量和余量（§5.3、表 C.3）；解读见 M1 |
| T1-4 题面参数 | 完成 | 完成（以 20% 为首推） |
| T1-6 £9.5/kg | 完成 | 完成（表 II.6 的下限见 M2） |
| T1-14 Xpress | 基本完成 | **完成**（完整许可，两种政策都独立定容） |
| 其余 | 完成 | 完成 |

## 4. 打分（非官方）

| 维度 | 权重 | v6.5 | v7 | 变化原因 |
|---|---:|---:|---:|---|
| U 理解与深度 | 1 | 81 | 83 | 回答了题面的可再生捕获问题 |
| O 原创性 | 1 | 79 | 80 | — |
| W 工作量 | 1 | 82 | 84 | 完整许可的 Xpress 重新定容；可再生归因 |
| L 论证逻辑 | 1 | 79 | 79 | 首推改为题面下限（加分），但资格句与可再生数字冲突（M1） |
| B 背景与文献 | 1 | 70 | 70 | — |
| V 结果有效性 | 1 | 78 | 81 | 两种求解器结果一致，容量已认证 |
| P 呈现（轻评） | 2 | 76 | 77 | 首推顺序清楚；表 C.1 少一列，表 II.6 的下限不一致 |
| **加权** | 8 | ≈78 | **≈79** | 区间 76–82；改完 M1–M3 后约 81–83 |
