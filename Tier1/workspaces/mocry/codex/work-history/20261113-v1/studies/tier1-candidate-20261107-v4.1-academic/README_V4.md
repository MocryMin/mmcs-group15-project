# MMCS 学术报告工作稿 · v4.1 · 2026-11-07

负责人：Ran Min，Group 15。按本人最新规定重写报告结构、叙述顺序与学术版式。Tier 1 数值研究沿用 v3；本轮未改变计算输入、经济假设或优化结果。

## 阅读入口

- [学术报告 PDF](report/report.pdf)
- [LaTeX 主文件](report/report.tex)；[公共部分](report/sections/common.tex)、[Tier 1](report/sections/tier1.tex)、[Tier 2B 方法规格](report/sections/tier2.tex)
- [框架、页数和顺序阅读检查](review/ACADEMIC_REVISION.md)
- [计算口径与假设](MODEL_AND_ASSUMPTIONS.md)；[参数依据](research/PARAMETER_BASIS.md)

报告采用黑白、Computer Modern 衬线字体。章居中并用 I/II/III 编号；节靠左用阿拉伯数字，节编号在章内重新开始。Abstract、目录使用 i/ii，正文从 1 开始，References 使用 R1。

| 部分 | 当前页码 | 内容状态 |
|---|---|---|
| Abstract / Contents | i / ii | 已填写，单独分页 |
| I. Introduction and data | 1–2 | 四段引言、整体架构、数据问题与修复、全局符号和假设 |
| II. Tier 1 | 3–6 | 问题分析、假设与研究、数学模型、结果/分析/结论 |
| III. Tier 2B | 7 | 已写预测与滚动控制的方法和评价规格，实验尚未执行 |
| References | R1 | 独立于正文页码 |

当前正文 7 页；Tier 1 为 4 页。按本人本轮规定，摘要、目录和参考文献不占正文额度。全组正文预算为公共部分 2 页 + Tier 1 最多 4 页 + Tier 2B 最多 4 页，总计最多 10 页。本轮没有把往年样例的版式推断改记成新的学校原文。

## 这轮修改

撤掉 KPI 卡片、决策框、彩色标题和年度柱状图。正文按问题、假设/证据、符号/模型、结果/分析顺序展开。引言先解释两种调度含义及收益口径，再给主要结果。数据修复集中在第一章。仅将跨 tier 的时间、供给、需求、价格等放在全局符号表；设备和预测符号在本章首次需要时定义。

图表保留 7,930 个合同点的两政策容量切换图，叠加利润等高线；新增数据—投资—预测—滚动优化—执行—库存/观测反馈的整体架构图。六年结果改为一张同时呈现盈余天数、盈余量、捕获量和 A/B 收益的表。

Tier 2B 使用预测模型是本人本轮指定的本组方案。规格采用多步正则化自回归预测与滚动优化，比较季节朴素预测、当前日规则和完美信息上界。旧 11 月 2 日原型没有预测模型且参数已过时，其数值未移入这份稿。当前第三章是待实施的方法规格，没有预测精度或控制收益的完成声明。

## 计算与复编

所有原始 CSV、修复输入、上游证据、质量标记、64 个逐日计划、合同网格、四主题研究和独立对照仍完整保留。输入由 `inputs/MANIFEST.json` 固定。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python run_all.py
```

`run_all.py` 复算 Tier 1、生成本版图表和表格、核对导出流量与现金。需要自己配置可用 Xpress 授权；包内无密钥。完整性与离线数据核验：

```powershell
python verify_package.py
python verify_results.py
python data_repair/validate_release.py --course-root originals
```

PDF 由 Tectonic 或 XeLaTeX 编译，设编译器为 PATH 中可用程序或设置 `TECTONIC` 路径：

```powershell
python build_report.py
python build_pdf.py
# 或计算并编译
python run_all.py --pdf
```

入口现在是 `report/report.tex`，不再使用 v3 的两份演示 PDF 入口。PDF 源码、生成图表和计算数据均随包提供。

## v4.1 补充

第三页通过调换换算说明、研究表与金融参数行填充空间；II.3 现分为设备选择和六年运营两个面板，II.4 扩为六个情景、九个信息列。两表均按内容确定列宽，取消伸展首列。详见 [本轮修改](review/LAYOUT_RESULTS_REVISION_4_1.md)。
