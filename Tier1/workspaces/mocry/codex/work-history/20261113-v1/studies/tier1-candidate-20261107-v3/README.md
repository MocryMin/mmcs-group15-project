# MMCS Tier 1 候选包 · 2026-11-07 v3

负责人：Ran Min。课程：Methodology, Modelling and Consulting Skills，2026/27，Group 15。

从 [四页技术报告](report/Tier1_Report.pdf) 开始阅读；[完整报告模板](report/report-template.pdf) 和所有 LaTeX 源码在 `report/`。本包是一份完整的 Tier 1 候选：可阅读、可复算、可核对来源。整组报告还需结合选定的 Tier 2，按 10 个物理页安排。本包不代表小组已采纳或已提交。

## 本轮结论

在 £7.799/kg（2020 年英镑）的支持性氢净回值情景、10 t/day 承购上限和 5% 实际折现率下，2020–2025 六个完整年份共同最优规模为 **20 MW 电解槽、零电池**。按同一政策的零投资方案计算，年度等价增益均值为：

| 调度政策 | 六年平均增益 | 2023 年增益 | 主要条件 |
|---|---:|---:|---|
| A：按经济价值自由分配发电 | £10.94m/年 | £8.57m/年 | 可以把原本可售电量转为制氢 |
| B：每天优先售出 min(供给, 需求) | £2.12m/年 | 固定 20 MW 为 −£1.07m/年 | 六年中三年亏损；2023 单年可自由投资时选择零 |

建议是推进一台 20 MW 设备的**承购合同与场址评估**。初始资本约 £29.21m；实际承购条款和调度权决定是否投入。2023 是六个完整年份里物理盈余最少的一年，因此保留为压力情景，同时展示全六年。2026 只有 260 天，其年化案例留在结果档案，不混入六年均值。

## 包内入口

| 内容 | 位置 |
|---|---|
| 成稿、模板、公式、矢量图和生成表格 | [report/](report/) |
| 本轮吸收课程、Opus、CU 意见的逐项记录 | [review/FEEDBACK_DISPOSITION.md](review/FEEDBACK_DISPOSITION.md) |
| 系统边界、参数来源、数学模型与口径 | [MODEL_AND_ASSUMPTIONS.md](MODEL_AND_ASSUMPTIONS.md) |
| 参数逐项说明和金融换算 | [research/PARAMETER_BASIS.md](research/PARAMETER_BASIS.md) |
| 课程原始五份 CSV | [originals/](originals/) |
| 直接进入模型的修复数据、质量标记、CPI 和参数 | [inputs/](inputs/) |
| 数据修复代码、公开上游证据、逐单元格修复记录 | [data_repair/](data_repair/) |
| 四主题研究和价格更正说明 | [research/README.md](research/README.md) |
| 原题、完整转写、教师澄清、评分标准和独立对照 | [references/](references/) |
| 数值结果、64 个逐日计划、7,930 点合同网格、核验记录 | [results/](results/) |
| 全包文件清单与 SHA-256 | [PACKAGE_MANIFEST.json](PACKAGE_MANIFEST.json) |

## 复算

验证环境为 Windows、Python 3.12、FICO Xpress 9.9；依赖固定在 [requirements.txt](requirements.txt)。本机已有可用 Xpress 安装/授权。对方电脑需配置自己的授权，包内不携带密钥。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python run_all.py
```

`run_all.py` 校验冻结输入、重算案例、生成图表/LaTeX 表格，再用不导入优化模型的独立算术程序核对导出计划。读取结果和运行 `verify_results.py` 无需 Xpress；后者只需 NumPy 和 pandas。全包文件完整性可以只用标准 Python 检查：

```powershell
python verify_package.py
python verify_results.py
python data_repair/validate_release.py --course-root originals
```

编译 PDF 需要 Tectonic 或 XeLaTeX 和 TeX Gyre Pagella/Heros 字体；两种编译入口都在 [build_pdf.py](build_pdf.py)。把编译器加入 PATH，或设置 `TECTONIC` 为其路径，然后执行：

```powershell
python build_pdf.py
# 或计算并编译
python run_all.py --pdf
```

首次配置 LaTeX 可能需要安装宏包。已经编译的两份 PDF 随包提供。`report/build_logs/` 保存本轮日志。

## 验收与版本

本轮验证了 60 个 Xpress 案例、2 个简单规则和 2 个精确枚举的共同配置计划；另外以 Xpress 核对 8 个合同网格点。14 个年度回放与独立实现 B 在其公布精度内一致，最大差 £49.55/年。验证结果见 [VALIDATION.json](results/VALIDATION.json)，数据修复的独立复核见 [data_release_check.json](results/data_release_check.json)，解压后重新计算和编译的核验见 [ZIP_REPRODUCTION.json](results/ZIP_REPRODUCTION.json)。全部检查离线完成；未访问学校新页面。

源材料以共享仓库提交 `53e3b50181ff9b6238a802cb32d65652518dbb29` 为截点；旧报告和意见原文保留在 `review/`，本轮的处理结论另列。历史研究中旧版电价不进入计算；唯一计算输入为 `inputs/`。`PACKAGE_MANIFEST.json` 记录交付时的文件哈希，重算后的日志/输出发生变化时，旧清单会正确提示这些文件已变化。
