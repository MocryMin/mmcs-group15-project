# 整合报告 v1.3：复审

2026-11-25 · mocry-claude · 个人工作区审核稿，不是组内决定。应 mocry-codex 请求 `3c757ae677064a46a20bcd8873855ce7`。

## 依据与核对范围

- **对比基准**：我对 v1.2 的审核 `../20261125-integrated-v1.2/REVIEW.md`（`338e5fe`）。
- **对象**：`Tier2/workspaces/mocry/codex/technical-report/20261125-integrated-v1.3/`（`131e986`）。
  - PDF、审阅包、2025/26 可运行包和 README 的哈希均与 `SHA256SUMS.txt` 一致。
  - 共 27 页：i–ii，正文 1–10，参考文献 R1，附录 A1–A14。
- **阅读方式**：用 v1.2 与 v1.3 的全文 diff 定位所有改动；逐页看了第 1、7、8、9 页和 A14 页的渲染图。
- **证据复算**：

| 复算项 | 来源 | 结果 |
|---|---|---|
| Table D.6 共 24 格 | `horizon-sensitivity.csv` | 与表一致 |
| 五窗合计（去掉 2021/22） | 按 Table III.2 逐列加总 | 45 块 12 小时 −278.78，11 块 −32.54，一致 |
| Table D.7 区间 | 按 6⁶=46,656 个有放回样本重算 | A 电厂 8.69–14.79，与表一致；`window-uncertainty.csv` 一致 |
| 预算行 | `capital-budget.csv` | 4 台 £29.39m、£11.11m/年；5 台 £36.74m、£13.13m/年，一致 |
| 2025/26 可运行包，B | 在 cloud 中运行 `report_sensitivity.py check-b`；numba 和 xpress 用占位模块，B 用不到 | 1 块上一时段规则 £1.330663m，9 块判别器 £8.574888m，与 Table III.2 和账本一致 |
| 2025/26 可运行包，A | — | 未能在本环境运行：需要 Numba，cloud 中不能安装，纯 Python 动态规划在 10 分钟内跑不完。CU 或本机 Windows 可以运行 |

## 0. 结论

**可以提交，没有会实质影响建议或评分的遗留问题。** 非官方估分：整份报告约 81（区间 78–84），v1.2 约 80。

## 1. v1.2 意见的处理情况

| 项 | v1.3 中的位置 | 结论 |
|---|---|---|
| **R1** 规划视野 | 第 8 页 §3 末段："Adding 12 hours of historical averages … raises the 25-block mean from −£0.28m to +£2.10m. At 45 blocks it remains negative (−£14.10m). Both sizes lose money outside 2021/22"。附录 D.7 的 Table D.6 在最终设定（20%、四天、6 台）下给出六窗的 12/24 小时对比。§D.6.1 明确把早先的试验（12.5%、半小时启停、25 块）与 D.7 的匹配测试分开 | **解决**。推迟电池的建议同时经受住了视野敏感性（24 小时）和窗口敏感性（去掉 2021/22）。D.6.1 原来与数据相反的结论已删除 |
| **R2** Tier 1 电池组合的实际运行结果 | 摘要第 3 段："A's 45 blocks lose £22.24m per window … with 12-hour planning and £14.10m with a 24-hour extension. B's nine gain £6.57m"。第 1 页 §1 末句。第 8 页 §3 首段 | **解决**。读者可以从 Tier 1 的 45/9 块直接看到它们在 Tier 2B 中的结果 |
| 预算 | 第 9 页 Table III.4 "Capital budget"行；附录 D.7 末段 | **满足题面**。£30m 和 £37m 两档都用 Xpress 求解，并说明两档都买不起一块电池 |
| 目标理由 | 第 6 页 §1："A represents a merchant operator free to maximise operating receipts … B represents an operator that gives priority to meeting electricity demand" | **基本满足题面**。说明了两种政策各自代表哪类客户 |
| §5.5 单位 | 第 5 页："Across six replay windows, one block gains …" | 解决 |
| 表格折行 | 第 7 页 Table III.1、第 10 页 Table III.5 已单行 | 解决 |
| §D.4 首时段的说法 | 已删除 | 解决 |

**版面。** 第 8 页加了一段后仍是一页；第 9 页 Table III.4 加一行后没有溢出；正文仍为 10 页。A14 的 Table D.6 和 D.7 表注写明了口径与局限（"do not estimate the probability of profit in a new year"）。没有发现新的版面问题。

## 2. 可选润色（不影响建议或评分）

1. **第 9 页 Table III.4 "Without 2021/22"行。** "The fitted controllers lose money in aggregate at every positive size" 可以写得更精确："the 12-hour controller at every size, and the 24-hour plan at the four tested sizes"。24 小时方案只测了 1、11、25、45 块。
2. **摘要第 3 段 B 的写法。** "B's nine gain £6.57m"可加半句"but lose £25.86m over the other five windows"。A 的结果已经写了亏损，B 这样写才对称。
3. **第 10 页"Basis of the recommendation"。** 可加一句："Battery gains also depend on the planning horizon and terminal stock value (Appendix D.7)." 这一点现在只在第 8 页和附录出现。
4. **预算行的一个客户视角。** 5 台用 83% 的资本（£36.74m 对 £44.08m）就能拿到 6 台 97.6% 的年净收益（£13.13m 对 £13.46m）。对资金受限的客户，这是一个有用的提示，可在 §5.5 加半句。

## 3. 打分（非官方）

| 维度 | v1.2 | v1.3 |
|---|---:|---:|
| 理解与深度 | 83 | 84 |
| 原创性 | 81 | 81 |
| 工作量 | 84 | 85 |
| 论证逻辑 | 80 | 83 |
| 背景与文献 | 71 | 71 |
| 结果有效性 | 80 | 83 |
| 呈现（权重 2） | 80 | 81 |
| **加权** | ≈80 | **≈81**（78–84） |
