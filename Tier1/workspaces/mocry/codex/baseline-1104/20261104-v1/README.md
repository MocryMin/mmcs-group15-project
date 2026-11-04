# Ran Min 的 Tier1 Baseline 1104 完整计算包

版本 20261104-v1，2026 年 11 月 4 日。个人工作区实验与候选方案，由 mocry-codex 整理。

先读 [假设、分析与结论](calculation/README.md)，再按需要查看 [数学模型](calculation/MODEL.md)、[参数](calculation/parameters.json)、[全部案例结果](calculation/results.csv)和 [验证结果](calculation/VERIFICATION.json)。本包包括本轮计算使用的数据快照、代码、82 个案例的逐日计划、比较图与来源记录，可以在单独目录复算。它没有把 Baseline 1104 升格为小组已采纳的公共方案。

## 内容

| 目录或文件 | 内容 |
|---|---|
| calculation/ | 完整假设与分析、数学定义、参数、主模型/校验/汇总代码、82 案例结果、逐日计划和比较图。 |
| inputs/data_repair/ | 完整修复 20261104-v2：五份模型输入、质量与修改审计、原始公开来源快照、修复和检验代码。 |
| inputs/course_originals/ | 五份课程原始 CSV，供对照与价格消融。 |
| inputs/research/ | 本轮采用的已审核研究 v1.1、推荐参数及其来源说明。 |
| inputs/finance/ | 实际使用的 ONS 月 CPI 快照。 |
| inputs/assumptions_1103/ | 教师澄清、解释、缺口与 1103 假设族的来源快照。 |
| provenance/ | 原计算代码/清单、文件复制及相对路径调整记录、课程内来源记录。 |
| requirements.txt | 本次复算环境的 Python 库版本。许可证不随包分发。 |
| reproduce.py | 使用包内输入，在新目录重跑、验证并与归档结果比较。 |
| PACKAGE_MANIFEST.json | 本包所有文件的提交形式 SHA-256，不包含自身。 |

## 复算

使用 Python 3.12 与 requirements.txt 所列库，并使 Xpress 许可证可用。在本文件夹运行：

```text
python reproduce.py
```

默认写入 reproduced/ 下的全新时间目录，保留 calculation/ 的归档。可以使用 --output 指定另一个空目录。Xpress 优先使用 XPRESS_LICENSE_FILE 环境变量，其次检查 Windows 常见安装位置，最后使用优化器默认许可证发现。主计算为 Python/Xpress，全样本 oracle 以 SciPy/HiGHS 求解。

程序核对全部 82 个案例的安装数量与年度收益，收益允许 £1 以下的数值差异。它同时执行能量、费用、设备与非零电池顺序检查。运行时长和迭代细节可能随求解器与机器变化。原始本地计算代码与路径调整列表位于 provenance/，模型系数、假设和归档数值不因打包改变。

## 条件与来源

参考情景的 £7.7990/kg 氢净回值及 10 吨/日承购量是明确的高价值条件。A/B 规则、零投资可选、年度设计/回放与价格修复影响均在分析中说明。年度外回放是固定容量的全知运营，不称为未知未来的因果策略测试。

修复数据固定于源发布提交 0a821eaf61a2b552682e185c137d98c5a9bffc93。这里的研究和澄清是来源快照，各自原说明保留其当时状态。它们之间的历史导航在原仓库可用，实际复算只使用包内配置和输入。ONS CPI 原公开入口为 https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23 。

打包版已在新的空目录重新求解并验证全部 82 个案例，安装数量全部一致，年度收益差值为零。见 [打包复算核对](provenance/REPRODUCTION_CHECK.json)。
