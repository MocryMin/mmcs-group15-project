# 整合报告 v1.2：全文审核

2026-11-25 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `ccd85f77bfe643aca26c93f8d3adb800`。

## 依据与核对范围

- **对象**：`Tier2/workspaces/mocry/codex/technical-report/20261125-integrated-v1.2/`（`e4e0759`）。
  - `project-report-v1.2.pdf` 和 `project-report-v1.2-review.zip` 的哈希与 `SHA256SUMS.txt` 一致。
  - 共 26 页：i–ii，正文 1–10，参考文献 R1，附录 A1–A13。
- **阅读方式**：对照题面 `Project_Brief.pdf` 按页序通读全文；看了 i、1、7、10、A9、A10 页的渲染图，其余页按文本版面核查。
- **核对的证据**：
  - `evidence/six-fold-capacity-replay.csv`（20% 账本）；
  - `model-evidence/tier2b-a-learned-24h-20261123/comparison.csv`。
- **标准**：我的 Tier 1 独立标准（`9d86960`），以及此前 Tier 2B 结构和 v1 审核中引用的题面条目。

## 0. 结论

**整体论证和版面已接近可提交。有两处会改变结果解读的问题，建议提交前处理（R1、R2）。** 两者都不推翻电解槽的建议。

- R1 涉及电池建议的稳健性；
- R2 是 Tier 1 到 Tier 2B 最关键的那句话没有写出来。

非官方估分：整份报告约 80（区间 77–83）；处理 R1、R2 和 §2 中的高影响修改后，约 82–84。

## 1. 会改变结果解读的问题

### R1 电池价值受 12 小时规划视野限制，而附录 D.6.1 自己的数据显示这个影响很大（第 6 页 §1.1；第 8 页 §3 末句；第 9 页表 III.4 "Without 2021/22"行；第 A13 页 §D.6.1）

- **事实。** `tier2b-a-learned-24h-20261123/comparison.csv` 是 A 在 2025/26 窗口、同一套设置下的对比。"old12"是正文用的 12 小时预测和 12 小时规划；"seasonal24"是 12 小时预测再加 12 小时历史均值，规划 24 小时：

  | 块数 | 12 小时（正文） | 24 小时（12h 预测 + 12h 历史均值） | 差 |
  |---:|---:|---:|---:|
  | 25 | −0.05 | **+4.96** | +5.01 |
  | 30 | −2.52 | +3.29 | +5.81 |
  | 35 | −7.52 | +1.50 | +9.02 |
  | 40 | −13.17 | −0.83 | +12.35 |
  | 45 | −21.26 | −6.97 | +14.28 |

  单位为 £m/窗，已扣电池成本。
- **问题。**
  - 4 小时电池做的是日内套利，一个完整的充放循环通常跨越 24 小时；而控制器只看 12 小时，且期末库存价值为零（§1.1"zero terminal value"）。这会系统性低估储能价值，块数越多低估越大。
  - 报告已经承认期末零价值"can depress estimated storage gains"（附录 D.2），但没有给出影响的大小。
  - §D.6.1 的结论"These outcomes support retaining the 12-hour rolling controller"与上表相反：24 小时方案在每个规模都更好。
- **影响。**
  - 第 8 页"With that window omitted, each positive capacity tested has a negative aggregate net gain in both policies"，以及表 III.4 的"Every positive size … loses money at the base cost"，都是**针对 12 小时控制器**的结论。2025/26 不是高价年，24 小时规划下 25 块却为 +£4.96m。
  - 所以"推迟电池"的建议可能仍然成立，但"去掉 2021/22 后任何规模都亏"这个强断言没有证据支撑。
  - 电厂本身的结论不受影响：零电池时没有库存可规划。
- **修改，二选一。**
  1. **（首选）** 用 seasonal24 重跑六窗的 1 块、11 块和 25 块（A），更新表 III.2、表 III.4，以及第 8 页那句话。
  2. **（最低限度）** 在 §1.1 写明视野限制，并给出 2025/26 窗口的量级（25 块时 +£5.0m，45 块时 +£14.3m）；把第 8 页和表 III.4 的断言限定为"with the 12-hour controller"；§5.1 的"Basis of the recommendation"加一句"Battery values are lower bounds for this controller"；§D.6.1 的结论改为如实描述。

### R2 摘要和第 1 页没有给出 Tier 1 电池组合在实际运行中的结果（第 i 页摘要第 3 段；第 1 页 §1 第 3 段）

Codex 问摘要和第 1 页能否让读者跟上"Tier 1 完美预知定容 → Tier 2B 实际运行"的转换。**电厂部分可以**：摘要写了 £11.95m，占完美预知的 92%。**电池部分不行**：摘要第 2 段说 Tier 1 选了 45 块（A）和 9 块（B），第 3 段却只讲一块电池，读者不知道 45 块和 9 块在实际运行中怎样。

20% 账本中的数字（£m/窗，已扣电池成本）：
- **A 45 块：** 六窗均值 **−£22.24m**（−140.23、145.32、−20.46、−65.90、−28.23、−23.96）。而 Tier 1 完美预知下的电池增量约为 +£105m/年（118.82 − 13.46）。
- **B 9 块（判别器）：** 六窗均值 **+£6.57m**，与 Tier 1 的 £6.07m 接近，因为 B 的调度基本由规则决定；去掉 2021/22 后合计为负。

建议摘要第 3 段加一句："Operated with forecasts, A's 45-block fleet loses £22m per window on average and B's nine blocks earn £6.6m, almost all from 2021/22." 第 1 页 §1 第 3 段也加同样一句。这是两层分析之间最有力的连接；按 R1，A 的数字要注明是 12 小时控制器下的结果。

## 2. 最有价值的修改（按影响排序）

1. **R1 和 R2**，见上。
2. **补投资预算的敏感性（第 9 页表 III.4）。** 题面 Tier 2B 点名要测"investment budgets"，目前全篇没有。加一行即可：推荐电厂资本为 £44.1m；电池推迟时没有预算约束；如果预算低于 £44.1m，可以少装几台，并给出 4 台或 5 台的收益（Tier 1 模型可以直接算）；45 块电池需要 £1.79bn。
3. **Tier 1 §5.5 Battery 的单位（第 5 页）。** "One block gains £4.63m in A and £8.77m in B"是六窗合计，不是年值，读者容易与上面表格中的 £m/年混淆。改为"in total over the six replay windows (£0.77m and £1.46m per window)"。
4. **表 III.1 和表 III.5 第一列折行（第 7、10 页）。** "A: 12 h truth / paths""B: true surplus / sign""Case and / controller""A: v2 plus auction / mix"都折成两行，是正文里最明显的版面瑕疵。可以缩短标签（如"A: 12 h truth""B: true sign""A: v2 + auction"）或加宽第一列。
5. **§5.3 的 56 小时论证依赖附录图（第 4 页）。** Figure A.1 已移到附录；讲座说附录可能不读。§5.3 的文字已经足以独立成立，所以可以接受；如果第 1 页底部或第 5 页还有空间，可以放回一张小图。

## 3. 对 Codex 所提各点的回答

- **两项建议是否都由证据及其局限推出？**
  - **电解槽建议：是。** 92%、每窗都为正、2×2 信息分解、£4.28/kg 保本，以及资格条件（第 5 页、附录 C.5）都已写清。
  - **电池建议：结论可以成立，但部分理由过强。** 见 R1。
- **附录 D.3–D.6 的模型和训练图表。** 结构清楚：Figure D.1 的路由图、Table D.1 的分支规模、Table D.2 的规模与模型族筛选、Figure D.2 的训练轨迹、Table D.4 和 D.5 的匹配消融都有配对区间。问题有三点：
  - §D.6.1 的结论与其数据相反（R1）。
  - §D.4 末段说"Ridge gives lower first-slot error than the 4×768 and 8×768 models in both periods"，但 Table D.2 只有 12 小时路径的 MSE，没有首时段误差，读者无法核对。应补一列，或删去这句。
  - 附录 D 共 6 页，与正文 Tier 2B 的 5 页篇幅相当，而且以神经网络规模筛选为主（最大到 1B 参数）。讲座说附录不计分，所以不影响分数，但会给读者"重模型、轻决策"的印象。可以考虑压缩 D.4，只保留 D.2(b) 与 Figure D.2。
- **版面、图注和引用跳转。**
  - 第 i 页摘要分四段，结构清楚。
  - 第 1 页 Table I.1 正常。
  - 第 7–10 页没有跨页的表；表注写明了口径（20%、上一时段规则或判别器、训练泄漏）。
  - 引用跳转核对无误：Table II.5 ↔ §II.1；Table III.2 ↔ §5.5；Appendix C.1 ↔ §5.4；Section D.5 ↔ Figure D.1 的图注；参考文献 [29]–[31] 已解析。
  - 12.5% 的引用只出现在 Tier 1 的产品下限敏感性，以及附录 B.1、C.2–C.5 和 [25] 中，标注清楚。
- **对照题面，全文还缺什么。**
  - 投资预算情景（§2 第 2 项）。
  - "为什么这个目标代表客户利益"仍只有描述（第 6 页 §1："A allocates power to maximise operating receipts … B gives priority to meeting electricity demand"）。加一句即可：A 代表追求回报的投资者，B 代表有保供义务的供电方。
  - 其余题面条目都已覆盖：数据问题、Python 和 Xpress、可再生捕获量、简单策略对照、敏感性、可视化、数据与假设的区分（第 10 页"Basis of the recommendation"）、时间顺序与压力期。

## 4. 最值得修改的页

| 页 | 修改 |
|---|---|
| i（摘要） | R2 那一句；按 R1 限定电池的说法 |
| 6 | §1.1 补视野限制及其量级（R1）；一句目标理由 |
| 8 | §3 末段"each positive capacity … negative"限定为 12 小时控制器，或用重跑结果替换（R1） |
| 9 | 表 III.4 加预算行；"Without 2021/22"行加控制器限定 |
| 5 | §5.5 Battery 的单位 |
| 7、10 | 表格第一列折行 |
| A13 | §D.6.1 的结论 |
