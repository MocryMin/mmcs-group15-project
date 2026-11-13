> v4：当前报告为 `report/report.pdf`；显示值为 `report_values_v4.json`。PDF_QA 与 ZIP_REPRODUCTION 为本版核验，旧版记录已另存 review/history-v3。Tier 2B 尚无实验结果。

# 计算输出索引

所有金额为 GBP2020 million，`net` 是相对同政策零投资的年度等价增益，流量字段后缀 `GWh` 一般为按 `represented_years` 年化的流量。逐日 `schedules/*.csv` 是实际当日 GWh，不是年化值。

| 文件 | 含义 |
|---|---|
| `study.json` / `cases.csv` | 主研究：2023 四类投资选择、2020–26 固定配置、同容量简单策略、非零电池池模型/库存、严格质量、站级、合同和成本压力、销量底线 |
| `extension.json` / `additional_cases.csv` | 全六年共同容量、电池上界、40 MW、50 t/day、£3/kg、99.99%/100% 销量、0%/12% 折现和初始资本 ±25% |
| `annual_replay.csv` | 2020–26 固定同一 20 MW 年度回放；`surplus_GWh` 是该期间实际物理总盈余，2026 并非完整年；A/B 收益和设备流量按代表年数年化 |
| `contract_grid.csv` | 7,930 点：A/B，承购 0–30 t/day、间隔 0.5，净回值 £0–16/kg、间隔 0.25；精确枚举优化规模 |
| `contract_grid_checks.csv` | 8 个网格点的精确枚举/完整 Xpress 容量与增益对照 |
| `threshold_reconciliation.json` | 对 £4.61/£4.62 争议的附加固定/自由投资核对；用 `python verify_threshold.py` 单独重现（需要 Xpress） |
| `daily_model_inputs.csv` | 2,452 日可直接分析的合并输入：g/d/wind/renewable 为 GWh，price 为 £2020/MWh，strict 为无需估计的质量标记 |
| `schedules/` | 60 个 Xpress、2 个规则及 2 个精确共同容量计划，共 64 份。包含供给、需求、价格、对照售电、分配、库存和捕获 |
| `report_values.json` | 正文采用的数字与显示精度，由计算结果自动生成 |
| `VALIDATION.json` | 不导入优化代码的独立导出算术核验 |
| `data_release_check.json` | 原始课程 CSV、公开上游存档和修复输出的独立核验 |
| `run_log.txt` | 本轮重算日志；不包含密钥 |
| `PDF_QA.json` | 交付 PDF 的编译、页数、引用和逐页视觉检查记录 |
| `ZIP_REPRODUCTION.json` | 从新目录解压，检查交付哈希后重新计算与编译，比较容量、收益和 PDF 文本 |

政策 A 可以按经济价值不卖负价电；B 固定每日 min(供给,需求) 直接售出。`A_zero`/`B_zero` 的收入常数各自不同，故 `A_gain` 和 `B_gain` 不宜直接解释为整个企业总利润之差。

2023 的 `hydrogen_only` / `joint` 在 B 下可以不建，故增益为 0；`B_fixed20_2023` 则强制建设，增益为负。这两种比较分别回答“要不要建”和“同样设备在不同政策下表现如何”。

站级案例仅作资产/需求边界敏感性，采用独立风场与背景发电满足后的残余需求，不是更改主系统数据。严格质量案例为 2023 年 280 天，经代表年数年化；不对其使用逐日连续库存。
