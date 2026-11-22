# 原始数据的首轮探索分析

2026-11-13 · MMCS Group 15 · 个人探索稿，部分结论已被后续工作取代

对五个原始 CSV 的第一遍清洗和描述统计，产出一张日表、一份数字摘要和七张图。这是读仓库之前做的，目的是摸清数据的样子。**用图或数字之前请先看下面的"已知问题"。**

- [数字摘要](results/summary.txt) · [清洗后的日表](results/clean_daily.csv) · [分析脚本](data_analysis.py)
- 图：[总览](results/fig1_overview.png) · [发电结构](results/fig2_generation_mix.png) · [季节性](results/fig3_seasonality.png) · [风电场容量因子分布和持续曲线](results/fig4_wind_farm_profile.png) · [电价与风电](results/fig5_price_vs_wind.png) · [连续大风和无风](results/fig6_wind_spells.png) · [余电与假想客户需求规模](results/fig7_surplus_vs_scaling.png)

## 仍然成立的发现

| 问题 | 本轮证据 |
|---|---|
| 风电场有多大 | 75 台 15 MW，共 1,125 MW。平均出力 424 MW，容量因子 37.7%，年发电约 3,718 GWh，约占全国需求的 1.5%。10 天零出力，29 天满发。 |
| 文件缺什么 | 发电缺 30 天，电价缺 30 天，需求缺 1 天。分燃料之和在所有共同日期上等于总发电。 |
| 明显的异常 | 2022-08-02 的需求为 636 MW。有一批日子的火电、核电、水电同时为零。 |
| 时间结构 | 风电场出力的自相关：隔 1 天 0.59，隔 2 天 0.33，隔 7 天 0.20。周末需求比工作日低 8.1%。需求与光伏的日相关为 −0.59。 |

## 已知问题

这一轮没有发现前三件事，所以涉及电价和需求水平的数字和图不能直接引用。第四条是口径上的变化。

| 问题 | 影响 | 以哪里为准 |
|---|---|---|
| 电价文件约为真实水平的一半 | 摘要里的电价均值、风电场售电收入、图 1 和图 5 的电价轴都偏低约一半 | [独立 Tier 1 的数据清洗](../../tier1-independent/20261116-v1/README.md)，或仓库的[完整修复](../../../../../public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md) |
| 每 7 天的最后一天（全是周二）的需求和电价只是一个清晨读数 | 需求和电价的日序列每周有一个偏低的点 | 同上 |
| 发电不完整的日子用的是较宽的判定规则（127 天） | 后来的判定是 107 天全零加 18 天部分缺失 | 同上 |
| 图 7 假设客户有一份按全国需求等比例缩小的自有需求 | 这是早期的一种设想，后来改用 `get_data.py` 的口径（风电场对全国供需缺口） | [独立 Tier 1 的问题定义](../../tier1-independent/20261116-v1/RESULTS_ZH.md) |

## 复算

需要 numpy、pandas、matplotlib。脚本默认读仓库根目录的五个原始 CSV，输出到 `results/`。轻量克隆默认不带原始 CSV，先运行：

```sh
git sparse-checkout add -- '/daily_demand.csv' '/daily_generation_by_fuel.csv' '/daily_generation_total.csv' '/daily_market_index_price.csv' '/wind_farm_generation.csv'
python data_analysis.py
```
