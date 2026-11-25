# Tier 2B 五页预览：验收审核

2026-11-25 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `537a9b2fa5d5444394821c1db6028853`。

## 依据与核对范围

- **对象**：`Tier2/workspaces/mocry/codex/technical-report/20261125-preview/`（`067a317`）。
  - `tier2b-report-preview.pdf` 和 `…-source-and-evidence.zip` 的哈希与 `SHA256SUMS.txt` 一致。
  - A4 纸，5 页，页码为 6–10。
- **阅读方式**：按页序通读，并逐页看了 100 dpi 渲染图。
- **对照材料**：
  - 题面的 Tier 2B 一节和"What the client expects"；
  - 我的结构评审 `../20261125-tier2b-outline/REVIEW.md`（`f4636ad`）；
  - Tier 1 v7.1 `report.pdf`（`68d378a`）。
- **核对的证据**：`replays.csv`、`plant-oracle.csv`、`break-even.csv`，以及 v7 半小时输入 `tier1-halfhour-20261113-v7/inputs/halfhour.csv.gz`（只覆盖到 2025 年底）。

**按标签标注的数字全部一致：**
- Table III.1、III.2、III.5；
- 18% = 0.77/4.29，69% = 1.46/2.13；
- 保本资本价 £113 和 £123/kWh：(0.77+4.695)/4.695×96.72，以及 (1.26+4.695)/4.695×96.72；
- B 的上一时段规则在六个窗口里全部优于判别器。

问题不在数字本身，而在 §0 指出的那一项比较口径。

## 0. 结论

**结构验收通过。内容有条件通过：有一项会改变结果解读的问题必须先修（F1），另有五项 P1。修完后可以进入合并稿。**

我在结构评审里提的要点基本都已落实：
- 以 Tier 1 推荐的 6 台、20% 电厂为主角（§1）；
- 一张信息与时序图（Figure III.1）；
- 滚动决策公式写在正文；
- 主对照表同时给出简单规则、预测控制器和完美信息（Table III.1）；
- 规模 × 窗口图（Figure III.2）；
- 季节和压力周（Figure III.3、Table III.3）；
- 决策边界表（Table III.4）；
- 预测按已实现价值衡量（Table III.5）；
- 对冲关系也写进了 §3 和建议。

叙事从 Tier 1 到可执行的运行、再到逐窗表现和客户建议，是连贯的，也对得上评分标准（理解、有效性、呈现）。

## 1. 会改变结果解读的问题（必须修）

### F1 "A: plant oracle" 的 £51.40m 不是电厂的完美预知价值，而主要是售电信号的价值（第 7 页 Table III.1 第 2 行、§2.1 首段；第 8 页 Table III.2 第 2 列）

- **现象。** 完美预知的均值是 £51.40m/窗，单窗最高 £80.72m（2023/24）。Tier 1 对同一电厂、同一规则做的全期完美预知只有 £13.46m/年，最差 £8.67m。两者差了约 4 倍，不可能都是电厂的价值。
- **原因（已用证据核实）。**
  - 在 `plant-oracle.csv` 和 `replays.csv` 中，完美预知比预测运行每窗少卖 0.3–1.8 TWh 电，未用电相应增加（Table III.1：9,167 GWh 对 7,962 GWh；需求满足率 89.506% 对 89.980%）。产氢量几乎相同。
  - 我用 v7 半小时数据计算了"负电价时段照常售电"的损失，Σ max(−p,0)·min(G,D)，与完美预知和预测运行之差逐窗对比：

    | 窗口 | 负电价时段数 | 负电价售电损失 £m | 完美预知 − 预测 £m |
    |---|---:|---:|---:|
    | 2020/21 | 88 | 12.31 | 13.11 |
    | 2021/22 | 74 | 19.64 | 21.99 |
    | 2022/23 | 294 | 51.77 | 46.99 |
    | 2023/24 | 636 | 67.60 | 65.91 |
    | 2024/25 | 438 | 38.37 | 35.74 |

    2025/26 窗不在 v7 数据范围内。
  - 也就是说，这个差距几乎全部来自完美预知能准确避开全系统规模的负电价售电，而不是电厂本身的调度。§1 写"Sales stop when the sale signal is non-positive"，§2 写"The reference is direct sales under the same policy"：完美预知这一行的对照仍是按预测售电信号的直接售电。售电信号本身的信息价值因此被算进了电厂。
- **影响。** §2.1 写"Full foresight raises the mean to £51.40m"，读者会得出"预测运行只拿到电厂价值的 23%，电厂极度依赖预测"的错误结论。同时，Tier 2B 与 Tier 1 之间最关键的衔接（预测运行能保留多少 Tier 1 的价值）被这个数字遮住了。
- **修改。**
  1. 让完美预知行的对照也用完美信息：对照组改为按实际电价售电的直接售电（负电价不卖）。或者固定售电信号，只让承诺和分配使用完美信息，这与电池的 truth diagnostic "holds … the sale signal fixed" 同口径。修正后的均值应与 Tier 1 的约 £13–15m 相当，可以用作交叉核验。
  2. §2.1 改为："Forecast-operated, the plant retains about X% of its full-foresight value (Tier 1: £13.46m/year), with a gain in every window."
  3. 售电信号的价值（每窗约 £12–68m）作为单独一句发现：这是全系统售电的模型设定带来的，与本次投资无关。可以放在附录。
  4. Table III.2 的"A: plant oracle"列按修正后的口径重算。

## 2. 应修（P1）

**P1-1 把 Tier 2B 与 Tier 1 的数字直接接上（第 7 页 §2.1）。** 修完 F1 后，用一句话说明：预测运行的电厂均值 £11.95m/窗，最差 £5.32m（2021/22）；Tier 1 全期完美预知为 £13.46m/年，最差 £8.67m；氢价保本点从 £3.85 升到 £4.28/kg（Table III.4 已有 £4.28）。这样"可执行的运行损失多少"一目了然，是 Tier 1 → Tier 2B 最重要的一个数。

**P1-2 B 的电池结论与推荐的控制器不一致（第 8 页 Table III.2 "B: 1 block"列；第 9 页 Table III.4；第 10 页 §5.1 B 段）。** 建议给一块电池试点用上一时段规则，但 Table III.2 的 B 一块列（均值 1.26）和 Table III.4 的 B 保本价（£123/£92）都用的是判别器。按上一时段规则：
- 逐窗为 −0.01、9.32、0.37、−1.51、−0.73、1.33；
- 均值 1.46，去掉 2021/22 为 −£0.55m（判别器为 −£1.23m）；
- 保本价约 £127/kWh，去掉 2021/22 约 £94/kWh。

建议在 Table III.2 加一列"B: 1 block, prior-slot"，或把 B 一块列换成上一时段规则；Table III.4 给出两种控制器的保本价。

另一个值得写进正文的发现：完美判别（truth gate）的一块电池，去掉 2021/22 后仍为 **+£1.86m**。这说明对 B 来说，提高判别质量本身就有实际价值，可以放进 §5 的预测讨论。

**P1-3 电池成本基准要和题面对照（第 9 页 Table III.4 第一行）。** "At the £97/kWh base cost"中的 £97 是 Tier 1 的低成本四小时参考（Lazard 低值），题面给的两小时电池成本约 £256/kWh。初读者看到"保本 £113/kWh 高于基准 £97"，会以为一块电池稍有余量。正确的读法是：只有报价比题面成本低一半以上，才值得作为对冲买入。建议在表中或下方补一句："the brief's two-hour cost is about £256/kWh"。

**P1-4 第 7 页下部约 1/3 空白，而 §2.2 没有给结论。** §2.2 只有定义，没有发现，读者得不到题面可持续指标"good use of renewable energy"的结论。用这块空白写三四句，数字都在 Table III.1 里：
- A 的电厂只捕获可再生盈余 28.7 GWh，与 Tier 1 的约 1% 一致；加 1 块电池后为 44.7 GWh，11 块为 182 GWh；
- B 的 9 块电池使需求满足率提高 0.18 个百分点，未用发电减少 503 GWh，捕获可再生 226 GWh；
- 修完 F1 后，再加上 P1-1 那一句。

**P1-5 合并稿中需要同步修改的 Tier 1 v7.1 内容。** v7.1 中仍在引用旧的 12.5% 回放、或与本章不一致的地方：
- **§5.5 Battery（v7.1 第 5 页）。**
  - "One block gains £4.65m in A and £7.58m in B … losses of £1.54m and £1.23m without 2021/22. A uses six modules at 12.5% in the replay." 改为 20% 下的数字：A 为 £4.63m 和 −£1.55m；B 按 P1-2 的选择写。删掉"12.5% in the replay"。
  - "Obtain a site quote before reconsidering one block" 与本章的"price one block as a separate option if limiting bad-year exposure"不一致，应统一为对冲选项的表述。
  - "(Table III.1)" 的引用要改为本章的 Table III.2。
- **v7.1 的整个 Chapter III（旧的 Table III.1，"A, six modules at 12.5%"）。** 由本章替换。
- **v7.1 附录 C。** 关于 11 块（£22.99m 和 £40.97m）及其他基于 12.5% 回放的叙述，要么改为 20% 下的数字（A 11 块为 £22.84m），要么明确标注为"separate 12.5% comparison"。
- Tier 1 中 12.5% 作为产品下限敏感性的部分（Table II.3、II.7、C.5）**保留**，那些不属于回放。

## 3. 对 Codex 所提问题的回答

- **从 Tier 1 的 6 台 20% 到可执行运行的衔接。** 设备和规则已对齐：§1 写明 30.186 MW、20%、午夜启停、四天最短运行，(III.1)–(III.2) 给出可执行约束。缺的是数值衔接（F1、P1-1）。
- **能否解释跨时间的表现。** 可以。
  - Table III.2 逐窗给出数字，并指出电厂与电池的对冲关系；
  - Figure III.3 按季节拆分；
  - Table III.3 的高价周（A −£134k，B +£773k）配合文字，解释了 A 与 B 的机制差异：A 充电要放弃有价值的售电或制氢，B 充电只用本来浪费的电。这是本章最好的一处分析。
  - 还缺电厂本身的季节表现（在线台数或月度净值）。Figure III.3 只画了电池，这是 P2。
- **能否区分下单前已知的信息与交割时才用的数据。** 基本清楚：Figure III.1 的三栏，加上"Realised delivery then updates the remaining daily quota"和"Only u_t is submitted"。有两处可以更明确：
  - §1.1 的"Given a positive sale price signal"应写明售电信号来自预测（$\hat p$），不是实际电价。
  - "Earlier fits can use later years"目前只在 §2 第一段出现。Table III.2 的表注应加半句"2020/21–2024/25 forecast fits may use later years"，避免读者把六窗结果当作严格的样本外检验。
- **五页结构与评分标准。**
  - 对照（简单规则、预测、完美信息）、敏感性（Table III.4）、可视化（3 张图）和建议都已具备。
  - 题面要求说明为什么选这个目标，现在 §1 只写了 A、B 各自的目标。加一句即可："A represents an investor maximising value; B represents a supplier obliged to meet demand first."
  - 题面列出的需求和可再生出力水平敏感性，目前只有历史压力周。§4 末段已承认这一点，可在 Table III.4 加一行"Demand and renewable scenarios: not re-optimised; historical stress weeks only"。

## 4. 版面与文字（P2）

- **第 8 页 Figure III.2。**
  - A 面板的"Tier 1: 45"标签浮在面板中部，没有对应的竖线；B 面板在 9 处有虚线。建议在 A 面板 45 处也画虚线，或把标签移到右边缘。
  - 两面板上的黑点（A 的 7 和 11 块，B 的 11 和 22 块）在图注和图例里都没有解释。建议在图注加一句"Dots mark the reference-window and six-window maxima"。
- **第 7 页 Table III.1。** A 行的"Served (%)"指售电满足的需求。初读者会疑惑：为什么完美预知的满足率更低？F1 修完后这一点会自然消失，但仍建议在表注说明 A 的 Served 指售电满足的需求。
- **第 10 页 §5 第一段**约 180 词全是预测实现细节，Ridge、Transformer、竞价混合、Huber、回退规则都在里面。可以压到约 90 词，把细节移到附录，腾出空间写 P1-2 中完美判别的发现。
- **第 9 页 Table III.4 "Hydrogen receipt"行。** 可以注明 £4.28/kg 是预测运行下的保本点，Tier 1 完美预知下为 £3.85/kg。
- **第 10 页"Evidence."段**是小号字。如果是脚注性质，在合并稿中改为正文脚注或删去；"192 sampled Xpress solutions and 48 enumerations"可移到附录。

## 5. 打分（仅本章，非官方）

| 维度 | 评价 |
|---|---|
| 理解与深度 | 对照设计完整；A 与 B 的机制解释有洞见 |
| 原创性 | 电厂与电池的对冲视角；预测按决策价值评价；B 的简单规则胜过判别器的坦率报告 |
| 论证逻辑 | F1 会误导预测价值的结论；修后很强 |
| 结果有效性 | 数字可复现；F1 的口径问题；早期窗口的训练泄漏已披露 |
| 呈现 | 版面整洁，3 张图和 5 张表恰当；第 7 页留白，有两处图例小问题 |

本章现稿约 77，修完 F1 和 P1 后约 81–83。按我的标准，整份报告合并后约 80–82。
