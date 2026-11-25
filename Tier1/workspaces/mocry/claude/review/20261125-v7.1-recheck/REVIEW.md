# 项目报告 v7.1：复核

2026-11-25 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `23f4acc1607549389f3e274281f7b198`。

- **标准**：`../20261122-tier1-independent-standard/STANDARD.md`（`9d86960`），未作修改。
- **对比基准**：我的 v7 审核 `../20261124-v7-content/REVIEW.md`（`05ce003`）。
- **对象**：`Tier1/workspaces/mocry/codex/technical-report-latex/20261125-v7.1/`（`311c6cd`）。
  - 7 个文件的哈希均与 `SHA256SUMS.txt` 一致。
  - 共 16 页：正文 1–6 页，Tier 1 占第 2–5 页。
- **阅读方式**：
  - 用 v7 与 v7.1 的全文 diff 定位所有改动；
  - 逐页看了正文 1–6 页和附录 A5、A6 页的 90 dpi 渲染图。
- **核对**：
  - `electricity-input-split.csv`、`four-day-price-sweep.csv`、`eleven-block-replay.csv` 与正文和附录逐格核对；
  - £2.50/kg 的出处已在 `Project_Launch_Transcript.txt` 中核实，原话为"just assume you can always sell like 1 kg of hydrogen for, I don't know, 2 pounds 50"。

## 0. 结论

**复核通过，没有阻碍提交的问题。非官方估分约 80（区间 77–83），v7 约 79。** 我在 v7 审核中提的 M1–M3 全部解决，P2 也大多处理了。剩下几处是可选的加强，见 §2。

## 1. v7 审核意见的处理情况

| 项 | v7.1 的处理 | 核对 | 结论 |
|---|---|---|---|
| **M1** 资格与可再生份额 | 第 5 页 §5.5 写明 25.4% 的保本份额；若只有 14.8% 的可再生盈余电拿到支持价，每年亏 £1.93m；要求"Confirm buyer terms and qualifying supply before investing"。第 4 页 §5.3 写明只捕获约 1%（28 GWh/年）、从售电挪用 125 GWh/年。附录 C.5 写明这是"fixed six-module schedule"的敏感性，平均收入 £3.28/kg，低于 £3.85/kg。 | 0.1476×7.799+0.8524×2.50=£3.282/kg；(3.282−3.848)×3,406 t=−£1.93m；保本份额 (3.848−2.50)/(7.799−2.50)=25.43% | **解决**。§5.5 开头的"At fixed dispatch"覆盖后两句，C.5 也写明是固定调度，**作为固定调度敏感性的表述清楚** |
| M1 输入拆分 | 附录 C.4 写 190.42 ≃ 63.23+1.79+125.39 GWh/年（20%）、192.17 = 71.70+2.08+118.39（12.5%），并与同一份 Xpress 调度对上 | 与 `electricity-input-split.csv` 一致；63.23/190.42=33.2%，与我在 v7 中独立算出的结果相同 | 解决 |
| **M2** 表 II.6 的下限 | 改为 20%：0/6/6/7 台，£0.00/4.31/13.46/19.37m；12.5% 的结果移到 C.5 正文 | 与 `four-day-price-sweep.csv` 一致 | **解决** |
| **M3** 认证与缺口 | 第 4 页 §5.1 拆成两句："Xpress certifies the four-day capacities at both floors. At 20%, the remaining dispatch gain is at most £2,600/year …"。表 C.1 加了"Other-count bound"列，表注写明是竞争容量的最高上界 | 118.818207−118.811177=£7,030/年 > 缺口 £2,600；12.5% 下为 £8,259 > £1,999；B 为 6.070258−6.069620=£638/年 > 缺口 £0.17 | **解决** |
| P2 §II.1 叙述顺序 | 改为"compare half-hour dispatch … with a daily benchmark (Table II.5)" | — | 解决 |
| P2 2,432 GWh 的基数 | §5.3 写"Of the 5,165 GWh/year … 2,432 is renewable"；C.4 也给出日聚合的 1,138/2,276 | — | 解决 |
| P2 表 III.1 的 11 块 | A、B 都加了 11 块一列 | 12 个格与 `eleven-block-replay.csv` 一致；合计 22.99/40.97，去掉 2021/22 后 −32.32/−35.62 | 解决 |
| P2 统一 20% 的上界 | 表 C.1 仍为 118.820807，C.2 正文仍写 HiGHS 的上界更紧（118.819824） | — | 保留，影响很小 |
| P2 封面作者 | 未改 | — | 请组内按课程提交要求确认 |

**版面**：第 2、4、5、6 页和 A5、A6 页，表格和图都没有跨页，也没有孤立标题。表 III.1 加到 8 列后仍在版心内，负号和小数点对齐。表 C.1 新加一列后没有挤压。第 5 页有三张表，但间距正常。转入 Tier 2B 的衔接不变，仍然顺畅。

## 2. 可选加强（P2，不阻碍提交）

1. **题面核心价格下的台数（第 5 页表 II.6 与 §5.5）。** 表 II.6 显示，在题面核心价 £9.50/kg 下，即使用 20% 下限也选 7 台。也就是说，6 台还是 7 台不只取决于下限，也取决于氢价。建议在 §5.5 "Electrolysis." 段加一句："At the brief's £9.50/kg, seven modules are optimal even at 20%; six remain the choice at the £7.80/kg netback." 评分人对照题面的 £9.5/kg 时，就不会觉得首推与题面价格不一致。
2. **摘要的条件不完整。** 摘要第二段只写了"depends on the buyer's terms and the investor's right to divert electricity from sales"，没有提支持价的资格条件，也没有给题面 Tier 1 标题问题的答案（捕获了多少可再生盈余）。建议加半句："… and on a qualifying low-carbon supply for the support price; the plant would capture about 1% of renewable surplus."
3. **§5.1 认证一句可以加上余量。** 如"(the best competing capacity's bound is £7,030/year below)"，让正文不看附录也能分清"容量已认证"和"调度缺口"。

## 3. 打分（非官方）

| 维度 | 权重 | v7 | v7.1 | 变化原因 |
|---|---:|---:|---:|---|
| U 理解与深度 | 1 | 83 | 84 | §5.3 对可再生捕获的解读 |
| O 原创性 | 1 | 80 | 80 | — |
| W 工作量 | 1 | 84 | 84 | — |
| L 论证逻辑 | 1 | 79 | 82 | M1 关闭：资格条件与固定调度敏感性表述准确 |
| B 背景与文献 | 1 | 70 | 70 | — |
| V 结果有效性 | 1 | 81 | 82 | 输入拆分与同一 Xpress 调度一致；表 II.6 改用 20% |
| P 呈现（轻评） | 2 | 77 | 78 | 表 C.1 的认证列；表 III.1 补齐 |
| **加权** | 8 | ≈79 | **≈80** | 区间 77–83 |
