# MMCS 2026/27 技术报告 LaTeX

[模板 PDF](output/pdf/report-template.pdf) · [Tier 1 样稿 PDF](output/pdf/tier1-example.pdf) · [完整 LaTeX 源码包](mmcs-technical-report-latex.zip)

| 文件 | 用途 |
|---|---|
| `report-template.tex` | 小组报告主文件。方括号内是可替换的写作提示。 |
| `tier1-example.tex` | 四页英文样稿主文件。含共用首页、Tier 1 正文、建议和参考文献。 |
| `report-style.tex` | 两个主文件共用的 A4、11 pt、字体、标题、图注和表格样式。 |
| `sections/tier1.tex` | 可移植的已填写数据及 Tier 1 部分。用它替换模板中的数据与 Tier 1 占位部分。 |
| `sections/example-references.tex` | 样稿用到的文献条目，可并入小组参考文献。 |
| `figures/*.pdf` | 两张矢量图，均可随 LaTeX 源码直接编译。 |

## 本年度的版式依据

- [本年度项目说明](../../../../../../Project_Brief.pdf)第 2–5 页要求先检查并记录数据调整，完成 Tier 1 和一个 Tier 2 扩展，并用简单策略对照、模型检验、敏感性和可视化支持投资建议。
- [说明课记录](../../../../../../Project_Launch_Transcript_Timed.txt)约 01:06:18–01:06:40 给出技术报告 10 页上限。模板把封面信息与摘要合放首页，按完整 PDF 的物理页数预算，参考文献和任何附录均预留在 10 页内。是否允许单独排除这些页面，目前的说明没有明确。
- [蓝图中的评分证据索引](../../tier1-blueprint/20261105-v1/README.md)标题为 25/26，后段不完整。可读的六项用于检查解释深度、独立分析、工作覆盖、论证、文献与结果核验。版式和项目覆盖以本年度要求为准。

## 从往年样例采用的做法

六份往年 PDF 都由 LaTeX 生成，有 A4 和 Letter 两种纸型。版式参考集中在下列正文页。

| 样例 | 参考点 | 在本模板中的落点 |
|---|---|---|
| [Group 10](../../../../../public/reference/past_project_reports/20261103-v1/Group_10.pdf) | 定义符号，再写分层模型。 | 在目标函数前定义变量和单位，约束组采用可交叉引用的编号。 |
| [Group 8](../../../../../public/reference/past_project_reports/20261103-v1/Group_8.pdf) | 先用摘要说清决策，在正文用图解释步骤。 | 摘要在首页给出规模和条件，正文的图只回答具体问题。 |
| [Group 20](../../../../../public/reference/past_project_reports/20261103-v1/Group_20.pdf)、[Group 23](../../../../../public/reference/past_project_reports/20261103-v1/Group_23.pdf) | 解释数据处理和建模近似，给出选择依据。 | 主文交代数据修复和年度储能池，并量化它对电池估值的影响。 |
| [自行车选址及再平衡报告](../../../../../public/reference/past_project_reports/20261103-v1/MethodologyModellingConsultingProject__74_.pdf)、[往届 Group 15](../../../../../public/reference/past_project_reports/20261103-v1/MMCS_Final_Project_Group15.pdf) | 编号公式、约束解释、引用和清晰的结果层级。 | 同样采用单栏正文。用紧凑标题代替独立封面，以表注标明单位与比较基准。 |

样稿使用[已核验的 Tier 1 v1 结果及 v2 对照](../../tier1-independent/20261105-v2/README.md)。它演示如何把数据、模型、图表和投资建议放在同一套报告样式中。Tier 2 的具体模型、结果和整组建议在完成小组分析后填入模板。

## 编译

在解压目录中使用常规 LaTeX 环境。两张 PDF 图已经包含，编译无需运行 Python。

```text
tectonic report-template.tex
tectonic tier1-example.tex
```

也可分别用 `latexmk -pdf` 构建两个主文件。若更换 Tier 1 数据，可运行
`python make_figures.py --results <Tier 1 v1 results 目录>` 重绘图形。
