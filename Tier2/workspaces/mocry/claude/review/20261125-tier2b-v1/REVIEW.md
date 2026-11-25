# Tier 2B v1 及合并报告：复审

2026-11-25 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `f292eca3a4c1421e8b58b923fce572c8`。

## 依据与核对范围

- **对比基准**：我对预览版的审核 `../20261125-tier2b-preview/REVIEW.md`（`84471f6`）。
- **对象**：`Tier2/workspaces/mocry/codex/technical-report/20261125-v1/`（`c5f9b68`）。
  - 四个文件的哈希均与 `SHA256SUMS.txt` 一致。
  - 单章 PDF 共 5 页（页码 6–10）。
  - 合并报告共 21 页：正文 1–10 页，参考文献 R1，附录 A1–A8。
- **阅读方式**：读完单章全文和合并报告全文（文本），逐页看了合并报告正文第 5–10 页的渲染图。
- **核对的证据**：`tier2b-report-v1-review.zip` 中的 `plant-information.csv`（2×2 信息组合，24 行）和 `replays.csv`。
- **复算结果**：

  | 复算项 | 结果 |
  |---|---|
  | 92.4% | 11.95/12.93 |
  | 分配与承诺的 Shapley 分解 | 分配 ½[(12.80−11.95)+(12.93−12.11)]=0.83；承诺 ½[(12.11−11.95)+(12.93−12.80)]=0.15 |
  | 附录 D 中直接售电的信息价值 | 均值 £38.47m = (12.31+20.39+46.17+65.11+34.88+51.99)/6。2020/21 的 12.31 与我在预览审核中独立算出的负电价售电损失完全一致 |
  | B 的上一时段规则 | 六窗合计 1.46×6=8.77，去掉 2021/22 为 −0.55 |
  | 保本价 | £127 和 £94/kWh |
  | 可再生盈余 | 2,911 GWh/窗，为六窗 `renewable_surplus_MWh` 的均值 |
  | 交付率 | +0.21 个百分点 = 91.147−90.934 |

## 0. 结论

**可以进入下一轮整份报告审核。** 我在预览审核中提的 F1 和 P1-1 至 P1-5 全部解决，没有会改变结果或建议的遗留问题。

- 本章非官方估分约 80（区间 77–83），预览版约 77。
- 合并报告整体约 80（区间 77–83）。

## 1. 逐项对照

| 预览审核的项 | v1 中的位置 | 核对 | 状态 |
|---|---|---|---|
| **F1** 完美预知的口径 | 合并报告第 7 页表 III.1 第 2 行为 12.93，§2.1 首段；第 8 页表 III.2 "A: plant oracle"列为 15.26 … 16.35；附录 D.1 | 每一行都用信息匹配的直接售电作对照，2×2 组合保留在证据里；售电信号价值 £38.47m 单列于附录 D.1，并说明是"market information affecting the whole constructed system" | **解决** |
| **P1-1** 与 Tier 1 的数值衔接 | 第 7 页 §2.1：保留 92.4%，并对照 Tier 1 的 £13.46m（窗口口径不同）；第 9 页表 III.4：£4.28 对 £3.85/kg；摘要也写了"retains about 92%" | 一致 | **解决** |
| **P1-2** B 的控制器口径 | 表 III.2 B 一块列、表 III.3 的 B 列、图 III.3、表 III.4 都改为上一时段规则；判别器的 £123/£92 并列；§5 加了完美判别下 +£1.86m 的发现；§1.1 写明扫描用判别器、一块用上一时段规则 | 一致 | **解决**。口径边界清楚：一块 = 上一时段规则，扫描和 11 块 = 判别器 |
| **P1-3** 电池成本基准 | 第 9 页表 III.4 下方："The brief's two-hour unit cost is about £256/kWh on the comparison basis" | 一致 | **解决**。可再加半句"so a hedge needs a quote below half the brief's cost"，可选 |
| **P1-4** 第 7 页空白与 §2.2 的结论 | 第 7 页 §2.2 给出 28.7/2,911 GWh（约 1%）、约 190 GWh 的输入大多不来自可再生盈余、11 块时的捕获量、B 交付率 +0.21 个百分点 | 一致；第 7 页已排满 | **解决** |
| **P1-5** 合并稿中 Tier 1 的旧引用 | 合并报告第 5 页 §5.5 Battery："£4.63m in A and £8.77m in B with the prior-slot rule … losses of £1.55m and £0.55m (Table III.2). Price one block separately if protection in high-price years is valuable"；附录 C 中 11 块为 £22.84m（20%），12.5% 写成"floor sensitivity £22.99m"；旧 Chapter III 已被替换 | 正文第 5 页已没有"12.5% in the replay"一类说法 | **解决** |
| P2 图 III.2 的标签和点 | 第 8 页：A 面板 45 处、B 面板 9 处都有竖虚线；图注加了"Dots mark the reference and six-window peaks" | 渲染图确认 | 解决 |
| P2 售电信号来自预测 | 第 6 页 §1.1："a sale-price signal available before delivery … published day-ahead quote or a historical fallback" | — | 解决 |
| P2 早期窗口的训练泄漏 | 表 III.2 表注："The first five forecast fits may use later years" | — | 解决 |
| P2 需求与供给情景 | 表 III.4 加了"Demand and supply"行 | — | 解决 |
| P2 压缩 §5 首段，删掉小字证据段 | §5 首段约 90 词；小字段已删 | — | 解决 |
| P2 电厂本身的季节表现 | 第 9 页：冬季平均在线 5.56 台，夏季 6.00 台 | — | 解决 |
| P2 说明为何这个目标代表客户利益 | §1 仍只写各自的目标 | — | **未改**，见 §2 第 2 项 |

**12.5% 的标注。** 合并报告中，12.5% 只出现在 Tier 1 的产品下限敏感性里：摘要、§II.3、表 II.3、图 II.1、表 II.4、表 II.7、§5.5 Electrolysis，以及附录 B.1、C.2、C.4、C.5。附录 C 的 11 块一处已写成"corresponding 12.5% floor sensitivity"。参考文献 [25] 的标题写明是"12.5% four-day replay ledgers"，只在附录 C 那句和附录 D.2 的证据列表中引用。**正文第 6–10 页没有任何 12.5% 的字样。** 标注清楚。

**版面。** 第 5 页到第 6 页的章节切换干净。第 7、8、9 页排满，没有跨页的表或孤立标题。第 10 页下部约 1/3 空白，见 §2 第 1 项。单章 PDF 中的 `[equipment and cost basis]`、`[equipment costs]`、`[model documentation]`、`[N2EX price archive]` 是单独编译时的占位符，在合并报告中已解析为 [12, 9]、[30]、[29]，不影响提交。

## 2. 进入整份报告审核前可做的小修改（都不影响结论）

1. **用第 10 页的空白区分数据与假设。** 题面要求"distinguish conclusions supported by data from conclusions that depend mainly on modelling assumptions"。预览版末尾的小字证据段原本承担这个作用，删掉后正文没有替代。建议在 §5.1 之后加 3–4 行"What rests on data and what on assumptions"：
   - 有数据支撑的：逐窗回放的价值、对冲关系、B 的上一时段规则胜出；
   - 依赖假设的：£7.80/kg 和价格支持资格、四天运行与 20% 下限、平坦风电廓线的重构、全系统售电的设定、电池成本基准。
2. **目标为何代表客户利益（第 6 页 §1）。** 一句即可："A represents an investor maximising value; B represents a supplier obliged to meet demand first."
3. **可再生盈余的基数（第 7 页 §2.2）。** "2,911 GWh per window"与 Tier 1 的"2,432 GWh/year"（2020–25 年，§II.5.3 和表 C.3）不同，原因是六窗包含 2025/26（6,467 GWh）。加半句说明即可。
4. **表 III.1 的表注。** A 完美预知行的 Served（89.506%）和 Unused（9,167 GWh）反映的是它自己的完美售电信号，而 Gross 和 Net 是按信息匹配计算的。§2.2 末句已说明，但表注可以加半句"Served and unused reflect each case's own sale signal"。
5. **第 6 页 §1.1 的用词。** "A ranks uses using a sale-price signal"读起来不顺，可改为"A ranks electricity uses by a sale-price signal"。

## 3. 打分（非官方）

| 维度 | 预览 | v1 | 变化原因 |
|---|---:|---:|---:|
| 理解与深度 | 81 | 83 | 2×2 信息分解（承诺 0.15、分配 0.83） |
| 原创性 | 80 | 81 | 售电信号价值单列；B 完美判别的发现 |
| 工作量 | 82 | 83 | — |
| 论证逻辑 | 74 | 81 | F1 关闭；B 的口径一致 |
| 背景与文献 | 70 | 71 | 模型和数据来源可溯 |
| 结果有效性 | 76 | 82 | 信息匹配的对照，与 Tier 1 交叉核验 |
| 呈现（权重 2） | 77 | 80 | 图例、竖线、§2.2 补齐；第 10 页仍有空白 |
| **加权** | ≈77 | **≈80** | 区间 77–83 |
