# Tier1设备调研 v3.1

2026-11-10。本地研究包：14个电池配置、15个电解槽配置。覆盖TESVOLT/Sungrow/Huawei/CATL/Tesla与ITM/Nel/Enapter。

v3.1保留v3原件，补入CU的Tesla来源并修正循环寿命终点。增益与未采用项见[CU交叉核查](CU_CROSSCHECK.md)。

先读[中文调研报告](REPORT_ZH.md)。需要查看具体商品时，打开[逐产品卡片](PRODUCT_CARDS_ZH.md)；需要计算接口时，打开[STUDY_INPUTS.json](STUDY_INPUTS.json)及[接入说明](MODELLING_INTERFACE.md)。

| 内容 | 入口 | 用途 |
|---|---|---|
| 调研结论、产品比较和推荐次序 | [REPORT_ZH.md](REPORT_ZH.md) | 人工阅读 |
| 每款产品全字段记录 | [PRODUCT_CARDS_ZH.md](PRODUCT_CARDS_ZH.md)、[catalogue.json](catalogue.json)、[products](products/) | 原厂事实及缺项 |
| 12套优先研究情景 | [STUDY_INPUTS.json](STUDY_INPUTS.json) | 3款交流电池、9款PEM的数值日级参考；估计有来源标记 |
| 行业成本/寿命依据 | [reference_scenarios.json](reference_scenarios.json)、[illustrative_cost_inputs.json](illustrative_cost_inputs.json) | 成套情景和逐型号换算，区别于报价 |
| 完整性与单位检查 | [field_coverage.csv](field_coverage.csv)、[comparison.csv](comparison.csv)、[QA.json](QA.json) | 空缺、测量边界、特别运行限制 |
| 模型接口与剩余询证 | [MODELLING_INTERFACE.md](MODELLING_INTERFACE.md)、[VENDOR_GAPS.md](VENDOR_GAPS.md) | SOC、功率/能量、氢气气质、维护/替换 |
| 来源与原件 | [SOURCES.json](SOURCES.json)、[evidence](evidence/) | URL、SHA256、数据表、手册、工作簿、原网页存档及关键页图像 |

原厂公开字段与日级研究输入并不相同。用户已允许采用可靠第三方研究和估计，优先选择整体资料较齐全的商品。研究输入里的行业迁移、效率拆分、维护与生命周期约定都有标记；厂商未给的完整安装价和寿命曲线继续保留为空，不制造原厂保证。旧baseline及报告本轮没有改动。

`tools/`内为目录重建和核验入口，所需Python包为PyMuPDF；读取成本工作簿另外使用openpyxl。顺序为`build_catalogue.py`、`build_reference_scenarios.py`、`build_study_inputs.py`、`build_sources.py`、`build_readable_catalogue.py`、`verify_catalogue.py`。这些脚本只读取保留的本地证据并生成目录，没有联网步骤。

原始PDF和工作簿为第三方原件，版权归各来源；本包记录出处。未发布到远程仓库。
