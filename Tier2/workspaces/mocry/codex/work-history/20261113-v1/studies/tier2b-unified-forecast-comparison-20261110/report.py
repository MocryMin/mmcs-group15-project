"""Write the local comparison report, protocol and a compact scientific figure."""
import json
import platform
import importlib.metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,Data,TARGETS,methods,dump,sha

D=Data();s=pd.read_csv(ROOT/'results/SUMMARY.csv');choice=pd.read_csv(ROOT/'results/VALIDATION_SELECTED_COMPARISON.csv');meta={m['id']:m for m in methods()}
def row(mid,t,p='test'):return s.loc[s.method.eq(mid)&s.target.eq(t)&s.split.eq(p)].iloc[0]
def number(mid,t,p='test',metric='loss',digits=6):
    r=row(mid,t,p);v=r[metric+'_mean'];sd=r[metric+'_sd']
    return f'{v:.{digits}f}'+(f' ± {sd:.{digits}f}' if pd.notna(sd) else '')
def table(ids):
    lines=['| 方法 | 发电 test loss | 需求 test loss | 电价 test loss |','|---|---:|---:|---:|']
    return '\n'.join(lines+['| '+meta[m]['label']+' | '+' | '.join(number(m,t) for t in TARGETS)+' |' for m in ids])

main=['T_fixed_Persistence','T_fixed_Seasonal7','T_fixed_Mean28','T_rule_Weekday52','T_fixed_CalendarOLS','T_fixed_OLSLevel','T_fixed_OLSResidual','T_fixed_RidgeLevel','T_fixed_RidgeResidual','T_fixed_CalendarResidualAR','T_state_LevelWeekdayFixed','T_fixed_EngineeredRidge','T_fixed_EngineeredLasso','T_fixed_EngineeredHGB','T_fixed_EqualEnsemble','N_sep_RNN','N_sep_LSTM','N_sep_Transformer','N_sep_Transformer10x','N_joint_RNN_large15','N_joint_LSTM_large15']
online=['T_state_LevelWeekdayAdaptive','T_expanding_Ridge','T_rolling730_Ridge','T_rolling730_Lasso','T_expanding_HGB','T_expanding_CalendarAR','T_rolling730_CalendarAR','T_online_EqualEnsemble']
selected=['| 目标 | 由 val 选出的模型 | Train loss | Val loss | Test loss | Test MAE | Test RMSE |','|---|---|---:|---:|---:|---:|---:|']
raw=['| 目标／模型 | Test MSE（原单位平方） | Test MAE | Test RMSE |','|---|---:|---:|---:|']
for target,cn in zip(TARGETS,['发电','需求','电价']):
    for pool in ['traditional','neural']:
        m=choice.loc[choice.target.eq(target)&choice.pool.eq(pool)].iloc[0].method
        selected.append('| '+cn+' | '+meta[m]['label']+' | '+' | '.join([number(m,target,p) for p in ['train','validation','test']]+[number(m,target,metric=x,digits=2) for x in ['MAE','RMSE']])+' |')
        raw.append('| '+cn+'／'+meta[m]['label']+' | '+' | '.join(number(m,target,metric=x,digits=2) for x in ['MSE','MAE','RMSE'])+' |')
configs=[]
for m in methods():
    if m['category']=='neural':continue
    configs.append({'method':m['id'],'label':m['label'],'regime':m['regime'],'configuration':json.dumps(m.get('selected',m.get('target_configs',m.get('members',{'window':m.get('window_days')}))),ensure_ascii=False)})
pd.DataFrame(configs).to_csv(ROOT/'results/SELECTED_CONFIGURATIONS.csv',index=False)

versions={k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','scikit-learn','joblib','threadpoolctl','matplotlib']}
dump(ROOT/'ENVIRONMENT.json',{'python':platform.python_version(),'versions':versions,'device_for_new_classical_fits':'CPU; two BLAS/OpenMP threads','neural_predictions':'frozen prior forecasts; no neural refits this experiment'})
(ROOT/'requirements.txt').write_text('\n'.join(k+'=='+v for k,v in versions.items())+'\n',encoding='utf-8')
protocol={
 'version':'2026-11-10 aligned next-day comparison v1','input_file':'inputs/model_daily.csv','input_sha256':sha(ROOT/'inputs/model_daily.csv'),
 'targets':TARGETS,'units':['daily average MW','daily average MW','nominal GBP/MWh'],'forecast_horizon_days':1,
 'periods':{p:{'target_start':str(D.index[o[0]+1].date()),'target_end':str(D.index[o[-1]+1].date()),'n':len(o)} for p,o in D.origins.items()},
 'context_only':'2021; never training labels','unused_targets':'2026-09-01 through 2026-09-17',
 'normalisation':{'fit':'2022-2024 labels, ddof=0','mean':D.mean.tolist(),'std':D.scale.tolist()},
 'loss':'mean over target dates of ((prediction-truth)/training_std)^2; joint is equal mean of three target losses',
 'selection':'each classical target selects config by its validation MSE; model family selection also validation only; neural checkpoints already frozen, not reselected on test',
 'information':'three observed historical series and known calendar only; no external features, no extra generation components',
 'feature_equivalence':'same source information, not identical encodings or history windows; engineered models use 44 columns; lagged OLS/Ridge retain old eight-feature histories',
 'fixed':'parameters and fit normalizers frozen after 2024; sequential features and ES states may use latest observations',
 'rolling':'refit every 28 forecast-origin days; every fit label date <= first forecast origin; expanding starts 2022 or latest730 labels; original evaluation scaler never changes',
 'uncertainty':'neural mean of three seed scores +/- sample SD, not prediction ensemble; classical deterministic, no seed SD',
 'scope':'one-step prediction comparison; no MPC decision-value claim; reused repeatedly monitored test period is not a new blind holdout',
 'OLS_precision':'inherited truncated OLS uses relative SVD cutoff 1e-6; level/residual OLS equivalent up to roundoff',
 'new_classical_grids':{'Ridge_alpha':[.1,1,10,100,1000],'Lasso_alpha':[.0001,.001,.01,.03,.1],'HGB_max_depth':[2,4],'ES_alpha':[.05,.1,.2,.3,.5,.8],'price_transform':['raw','asinh; median and scaled MAD fitted on fit labels only'],'HGB':{'iterations':300,'learning_rate':.05,'leaf_min':20,'l2':1,'early_stopping':False,'seed':17}},
 'relation_to_fable':'adaptation of method families, not a reprint of incompatible old scores; old sample periods, real price basis, six-series inputs and multi-horizon MAE not carried over',
 'audit_precision':'feature reconstruction uses the same compensated rolling-mean arithmetic for bit-sensitive histogram splits; also verifies direct window means agree within 1e-12; no forecast changed for this audit'
}
dump(ROOT/'PROTOCOL.json',protocol)

text=r'''# Tier2B：传统方法与神经网络的统一次日预测比较

本轮重新回测传统方法，并从已冻结的神经网络逐日预测重新计算全部指标。共纳入 **23 个传统／非神经方法配置和 16 个神经网络配置**。后者包括独立 RNN、LSTM、两种规模 Transformer，以及联合 RNN／LSTM 的规模与平台期策略试验。所有结果留在本地，没有上传或发出组内公告。

## 1. 对齐的评价协议

| 部分 | 次日目标日期 | 样本数 |
|---|---|---:|
| Train | 2022-01-01—2024-12-31 | 1,096 |
| Val | 2025-01-01—2025-08-31 | 243 |
| Test | 2025-09-01—2026-08-31 | 365 |

2021 年仅提供历史输入；2026 年 9 月 1—17 日未作为评价目标。每个预测起点 t 使用截至 t 的观测，预测 t+1。发电包含课程总发电和独立风电场，发电与需求单位均为日均 MW，电价为名义 GBP/MWh。输入 CSV 的 SHA256 为 `INPUTHASH`。

样本平均标准化均方误差（MSE）为：

$$
L_{j,S}=\frac{1}{|S|}\sum_{t+1\in S}\left(\frac{\widehat y_{t+1,j}-y_{t+1,j}}{s_{j,\mathrm{train}}}\right)^2.
$$

三个目标各自使用 2022—2024 年训练标签的总体标准差，整个比较中固定。这里的 loss 是每个样本平均值，不是全样本误差之和。另给出原单位的 MSE、平均绝对误差（MAE）及均方根误差（RMSE）。同一目标的标准化 MSE 与原单位 MSE 排名完全一致。三个目标的原单位误差不能直接取平均。

传统方法各自按目标的 val MSE 选参数；旧的联合 val 选参结果没有直接照搬。神经模型保留此前已经冻结的配置和各自 val 检查点。联合模型仍使用一个联合检查点，没有为三个输出另行挑选有利的权重。神经网络报告三个种子的分数均值 ± 样本标准差；它们不是三个预测先平均后的集成分数。传统方法为确定性拟合，不虚构种子波动。

新增特征模型仅使用同样的三条历史序列和已知日期：每条序列的 lag 0—6、13，过去 7／28 天均值，加次日星期、年度 Fourier 项及圣诞日期标记，共 44 列。旧 OLS／Ridge 使用与神经网络相同的八类逐日输入及其历史窗。不同方法允许不同特征表达和历史长度，没有加入 Fable 原试验中的额外发电分量、外部天气或燃料价格。

## 2. 固定训练参数：主要比较

下表均使用相同 test 日期，数值越低越好。每个方法家族已经通过 val 选定其参数；表中全部方法用于展示，不根据 test 的最低值重新选模型。

MAINTABLE

OLS 是普通最小二乘回归，Ridge 是岭回归，LASSO 是带 L1 惩罚的线性回归。水平 OLS 与预测变化量的 OLS 在当前输入包含最近值的条件下等价，两个结果只差数值舍入。日历回归单独预测很弱，但加上最近残差及其七日均值后明显改善。新增岭回归／LASSO／梯度提升树各自按 val 选择价格是否使用反双曲正弦（asinh）变换；所有评分先还原原单位。

等权集成为特征岭回归、LASSO、梯度提升树的预测各占三分之一，权重没有根据 test 调整。独立模型每个目标单独拟合；独立 Transformer 54k 是每个目标约 54k 参数，三个模型合计 162,015。联合 55k 是三个输出共用约 55k 参数，参数预算不同。

## 3. 按 val 选出的候选：train／val／test

SELECTEDTABLE

RAWTABLE

发电和需求的 MAE／RMSE 单位为 MW，电价为 GBP/MWh。神经网络的 RMSE 是各个种子的 RMSE 再取平均，所以不必恰好等于平均 MSE 的平方根。

![Train、val 与 test 的一致尺度比较](figures/selected_losses.png)

**发电：Transformer 小幅领先。** 按 val 选择的是较大 Transformer；其 test loss 为 0.181491，传统候选特征岭回归为 0.188461，MSE 约低 3.7%。小 Transformer 的 test 为 0.181218，与较大模型差异远小于种子波动，扩大参数没有稳定获益。LASSO 和等权集成的 test 也接近神经方法，但它们没有在 val 赢过该传统候选。

**需求：简单模型已经接近神经网络。** 日历＋残差 AR 的 test 为 0.105875，较大 Transformer 为 0.105558，只差约 0.3% MSE，后者三种子标准差为 0.001098。这个幅度不足以宣称有稳定优势。固定等权集成在这段 test 上更低，但不是 val 选中的传统家族，不能据此换成“测试集选模”。

**电价：传统非线性方法更有竞争力。** val 选出的梯度提升树深度为 2，使用 asinh 价格变换，test 为 0.062267，较 val 选出的 Transformer 低约 10.4% MSE；价格 MAE 为 £14.93/MWh。与 test 表现更好的独立 RNN 比较，MSE 也约低 5.2%。固定等权集成的 test 更低，但 val 上梯度提升树更好，因此当前选择仍是树模型。

训练误差与跨年份误差受年份分布影响，尤其 2022 年的价格水平和波动与 test 不同。asinh 模型最小化变换空间误差，也不保证原单位 train MSE 最小。例如 LASSO 的价格原单位 train loss 明显偏高；不能省略这个结果，也不能仅凭 test 低于 train 就判断不过拟合。

## 4. 吸收新观测后重训：单列的滚动回测

每 28 个预测起点重新拟合一次。扩展窗从 2022 年开始累计；730 天窗保留最近 730 个已观测训练标签。每一块的最大训练标签日期不晚于该块第一个预测起点。每次预测依然只能用当前已经观测的数据。

滚动方法也只按 rolling val MSE 选择参数。test 阶段允许使用此前已经发生的 val／test 观测重新拟合；现有神经模型没有这样重训，因此这张表包含更新制度带来的收益。没有一个与固定神经模型相同意义的单一 train 分数；每次拟合的训练误差与日期均存于 `results/FIT_HISTORY_all.csv`。

ONLINETABLE

动态水平＋星期模式使用过去 364 天更新星期模式，平滑系数在 val 选好后固定。它与周期重新拟合回归权重的方式不同，保留单独的 `online_state` 标签。

价格梯度提升树的 test 从固定方案的 0.062267 降到扩展重训的 0.059635，MSE 约下降 4.2%。扩展日历 AR 的需求 loss 为 0.105307。滚动等权集成在 test 的需求、电价两项更低，但 val 不一定胜出；完整表保留这些结果，未根据 test 改写候选。

## 5. 对 Tier2B 的含义

当前证据支持保留分目标建模：发电以小／大 Transformer 为候选，需求同时保留日历＋残差 AR，电价保留梯度提升树和岭回归。下一步进入模型预测控制（MPC）时，需在同一重训制度和信息边界下比较实际决策收益。单日 MSE 较低并不自动意味着电池／制氢调度收益更高。

这份 test 已被此前多轮试验查看，属于同一研究阶段的重复对比，不能当成新的盲测证明。神经模型与传统模型的搜索空间也不同；这里提供同一数据与评价尺度下的预测比较，不把差异完全归因于模型架构。SARIMA、TBATS 等仅在前期调研中被提及，未在 Fable 已交代码中完成，不列为已回测结果。

## 6. 文件与复现

- `results/COMPLETE_TABLES.md`：39 个配置在三个目标上的完整 train／val／test 表。
- `results/ALL_METRICS.csv`：逐方法、逐种子、逐目标、逐划分的原单位及标准化指标。
- `results/SUMMARY.csv`：均值、种子标准差、相对“明天照抄今天”的改进幅度。
- `results/SELECTED_CONFIGURATIONS.csv`：各传统方法的目标专属选参。
- `results/SELECTION_all.csv`、`IMPORTED_LINEAR_SELECTIONS.csv`：验证集选参记录。
- `results/ROLLING_BOUNDARIES.csv`：全部选中滚动模型的训练截止和预测起点。
- `predictions/`、`methods/`、`models/`：冻结预测、元数据及新拟合的 423 份估计器状态。
- `reference/IMPORT_MANIFEST.json`：133 份既有原始预测的来源及 SHA256。
- `results/AUDIT.json`：预测重放、指标与截止核验结果。

在 Python 3.12 环境安装 `requirements.txt` 后，可以运行 `analyse.py` 与 `audit.py` 重算指标和核验；`traditional.py --part all` 重跑本轮新增传统方法。`prepare.py` 仅用于从同级旧试验归档重新导入冻结预测，需要相应旧目录；已交比较包包含导入后的预测，所以重算比较表不依赖旧目录。神经网络的完整训练代码和权重保留在先前各个试验包，本包不重复打包其训练环境。

本轮为本地代码核验，未额外派遣独立 agent。423 份估计器状态和 414 个滚动块均已重放，最大标准化预测差异小于 2×10⁻¹⁵；三个目标的指标逐项重算通过。直方图树在训练样本的阈值处对浮点微差敏感，因此重放使用同样的补偿式滚动均值，并另验与直接窗口均值一致；未因此更改任何预测。
'''
text=text.replace('INPUTHASH',sha(ROOT/'inputs/model_daily.csv')).replace('MAINTABLE',table(main)).replace('SELECTEDTABLE','\n'.join(selected)).replace('RAWTABLE','\n'.join(raw)).replace('ONLINETABLE',table(online))
(ROOT/'README_ZH.md').write_text(text,encoding='utf-8')

# Compact figure: consistent ratio colors, explicit absolute standardized MSE text.
fig,ax=plt.subplots(figsize=(11,7.7));ids=['T_fixed_Persistence','T_fixed_OLSLevel','T_fixed_RidgeLevel','T_fixed_CalendarResidualAR','T_fixed_EngineeredRidge','T_fixed_EngineeredLasso','T_fixed_EngineeredHGB','T_fixed_EqualEnsemble','N_sep_RNN','N_sep_LSTM','N_sep_Transformer','N_sep_Transformer10x']
names=['Persistence','OLS','Lagged Ridge','Calendar + residual AR','Engineered Ridge','LASSO','Gradient boosting','Equal ensemble','Independent RNN (5k each)','Independent LSTM (5k each)','Transformer (5k each)','Transformer (54k each)']
ratio=np.array([[row(m,t).loss_mean/row('T_fixed_Persistence',t).loss_mean for t in TARGETS] for m in ids]);im=ax.imshow(ratio,cmap='Blues_r',vmin=.3,vmax=1,aspect='auto')
for i,m in enumerate(ids):
    for j,t in enumerate(TARGETS):
        r=row(m,t);label=f'{r.loss_mean:.6f}'+(f' ± {r.loss_sd:.6f}' if pd.notna(r.loss_sd) else '')
        ax.text(j,i,label,ha='center',va='center',color='white' if ratio[i,j]<.60 else 'black',fontsize=10)
ax.set_yticks(range(len(ids)),names);ax.set_xticks(range(3),['Generation','Demand','Price']);ax.xaxis.tick_top();ax.tick_params(length=0)
ax.set_title('Test mean standardized squared error | identical 365 next-day targets\nNeural values: mean +/- SD of 3 seeds; classical coefficients frozen after 2024',pad=35,fontsize=12)
fig.colorbar(im,ax=ax,label='MSE / persistence MSE (lower is better)',shrink=.7);fig.tight_layout();fig.savefig(ROOT/'figures/test_loss_matrix.png',dpi=180);plt.close(fig)
print('Report, protocol, configurations, requirements and compact figure saved.')
