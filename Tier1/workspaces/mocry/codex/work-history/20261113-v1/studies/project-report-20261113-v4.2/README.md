# MMCS Final Project · report v4.2

2026-11-13。以 v4.1 为底稿更新 Chapter II。正文第 3–6 页是 Tier 1，全文正文第 1–7 页。摘要、三级目录和参考文献各自分页。[报告 PDF](report/report.pdf) · [LaTeX 主文件](report/report.tex) · [Tier 1 源码](report/sections/tier1.tex)

## 数值依据

- II.2 的配置与净收益来自 [v6 情景汇总](../tier1-multiproduct-20261110-v6/results/case_summary.csv)。电解槽单独投资与联合投资一致。仅允许电池时，逐日价格和可用放电量给出每种型号的收入上界。公式为每台可用放电量乘全期正价之和，再除以六年，且充电成本取零。四款产品的收入上界与年成本之比分别约为 56.3%、56.0%、56.9%、46.6%。
- II.3 的物理余电按逐日发电减需求的正部计算。按余电优先归因，来自物理余电的制氢用电为逐日 `min(generation_h2, max(generation - demand, 0))` 之和。原始逐日计划单位为 GWh，表内取六年年均。电力收入变化由同策略无投资参照收益减实际电力收入得到。数字按各列分别四舍五入。 [v6 逐日计划及核验](../tier1-multiproduct-20261110-v6/README.md)
- 第 4.2 节的净回价进入门槛用 v6 电解槽候选重新求解，分别固定 1.559 和 10 吨/日承购上限。 [门槛区间与全点结果](contract-thresholds.json) · [复算脚本](compute_contract_thresholds.py)。23.4 MW 固定运行的回本净回价等于（年设备成本＋放弃的电力收入）除以年产氢公斤数。两类门槛的含义不同。
- II.4 汇集[成本稳健性](../../../notes/TIER1_BATTERY_COST_ROBUSTNESS_20261111.md)、[电价与供需差扫描](../tier1-volatility-20261111/REPORT_ZH.md)、[联合投资网格](../tier1-joint-portfolio-20261111/REPORT_ZH.md)、[真实窗口回放](../gb-price-window-replay-20261112/REPORT_ZH.md)和[洞穴压缩空气敏感性](../caes-entry-envelope-20261112/REPORT_ZH.md)。洞穴站作为独立技术情景，按一座 50 MW/1.5 GWh 模拟。

本版只同步摘要、引言中的 Tier 1 结果和相关参考文献。Chapter III 源文件保留 v4.1，因此其中关于替换旧总量能量平衡的表述属于下一轮要更新的 Tier 2 规格。归档的 v4.1 保留旧合同网格和固定 20 MW 对照。

复编时在 `report/` 目录运行 `tectonic report.tex`。
