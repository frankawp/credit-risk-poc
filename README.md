# Credit Risk Anti-Fraud POC

基于 Kaggle Home Credit Default Risk 数据集，构建一个面向反欺诈变量挖掘的 POC 项目。目标不是直接追求完整生产化，而是在较短周期内验证三类反欺诈特征是否能显著提升高风险样本，尤其是短期违约样本的识别能力。

## 1. POC 目标

本项目聚焦于申请欺诈和套现欺诈的早期识别，优先验证以下三类信号：

1. 信息不一致性 `Consistency Check`
2. 短期高频行为 `Velocity Features`
3. 套现与团伙特征 `Cash-out & Collusion`

POC 的成功标准建议定义为：

- 能稳定产出一批可解释的反欺诈变量
- 这些变量在验证集上对 `TARGET=1` 的召回率有增益
- 对“首期违约”或“短期恶化”样本有更好的区分能力
- 可以形成一套后续扩展到规则引擎或特征平台的最小骨架

## 2. 数据范围与核心表

建议在 POC 第一阶段优先使用以下表：

- `application_train.csv`
  申请主表，包含标签 `TARGET`
- `previous_application.csv`
  历史申请记录，用于一致性校验和申请密度分析
- `bureau.csv`
  外部征信记录，用于多头借贷、征信查询近因特征
- `credit_card_balance.csv`
  信用卡账单及取现行为，用于套现偏好分析
- `installments_payments.csv`
  分期还款行为，用于首期违约和失联风险识别

如果时间有限，建议优先完成：

1. `application_train + previous_application`
2. `bureau + installments_payments`
3. `credit_card_balance`

## 3. 反欺诈变量设计

### 3.1 信息不一致性

围绕“同一客户多次申请资料是否自洽”构建变量：

- 年龄/工龄跳变
  - 比较 `DAYS_BIRTH`、`DAYS_EMPLOYED` 在历史申请中的变化是否符合时间推进逻辑
  - 示例：两次申请间隔 30 天，但工龄增加超过 180 天
- 联系方式稳定性
  - 统计 `FLAG_MOBIL`、`FLAG_EMP_PHONE`、`FLAG_WORK_PHONE` 的变更频率
  - 生成变更次数、变更率、最近 N 次申请中是否频繁切换
- 证件组合异常
  - 对 `FLAG_DOCUMENT_*` 统计缺失数、核心文件缺失数、非核心文件提供数
  - 挖掘“关键文件缺失 + 非核心文件补齐”的可疑模式

### 3.2 短期高频行为

围绕“短时间内异常密集的借贷/查询动作”构建变量：

- 多头借贷激增
  - 基于 `AMT_REQ_CREDIT_BUREAU_*` 系列聚合近 12 小时、24 小时、7 天的查询特征
  - 输出窗口内总次数、峰值、环比增幅
- 申请密度
  - 使用 `DAYS_DECISION` 统计历史申请的间隔、标准差、最小间隔
  - 标记“极短时间连续申请”
- 突发申请行为
  - 构建最近一次申请距前一次申请的间隔
  - 构建“最近 3 次申请是否集中发生”的规则特征

### 3.3 套现与团伙特征

围绕“异常套现习惯”和“高危群体模式”构建变量：

- ATM 取现偏好
  - 计算 `AMT_DRAWING_ATM_CURRENT / AMT_BALANCE`、`AMT_DRAWING_ATM_CURRENT / AMT_TOTAL_RECEIVABLE`
  - 统计 ATM 取现占比高的持续性与峰值
- 首期违约 `FPD`
  - 基于 `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT` 构造逾期天数
  - 重点标记第一笔还款是否即严重逾期
- 地理/群体共性
  - 组合 `REGION_POPULATION_RELATIVE` 与 `ORGANIZATION_TYPE`
  - 聚合群组坏账率、群组样本量、申请密度，挖掘高危入件点

## 4. 欺诈算子库设计

建议先抽象一层“欺诈算子”，让后续变量开发更系统，避免所有逻辑都写成零散脚本。

首批算子建议包括：

- `Time_Diff`
  计算申请时间、还款时间、历史事件时间差
- `Null_Count`
  统计关键字段缺失数、缺失比例、关键缺失组合
- `Change_Rate`
  统计历史字段变更频率、切换次数、连续变更
- `Relative_Ratio`
  计算 ATM 取现占比、查询量环比、申请金额偏移比例
- `Window_Count`
  统计近 12 小时、24 小时、7 天内行为次数
- `Group_Risk`
  计算群组坏账率、WOE、风险排名

## 5. 推荐目录结构

```text
credit-risk-poc/
├── README.md
├── configs/
│   ├── base.yaml                  # 全局配置，数据路径、随机种子、特征窗口
│   └── features.yaml              # 欺诈变量与算子配置
├── data/
│   ├── raw/                       # 原始 CSV，不做修改
│   ├── interim/                   # 清洗后中间表、join 结果
│   └── processed/                 # 建模特征宽表
├── docs/
│   └── feature_catalog.md         # 变量字典，可后续补充
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_validation.ipynb
│   └── 03_model_baseline.ipynb
├── outputs/
│   ├── features/                  # 特征样本、统计摘要
│   ├── models/                    # 模型文件、特征重要性
│   └── reports/                   # POC 报告、图表
├── sql/
│   ├── consistency_checks.sql
│   ├── velocity_features.sql
│   └── cashout_collusion.sql
├── src/
│   └── anti_fraud/
│       ├── __init__.py
│       ├── operators/             # 通用欺诈算子
│       ├── features/              # 各类特征生成逻辑
│       ├── rules/                 # 可解释规则与命中逻辑
│       ├── pipelines/             # 数据处理与训练流水线
│       ├── models/                # Isolation Forest、XGBoost 基线
│       └── utils/                 # IO、日志、通用函数
└── tests/
    ├── test_operators.py
    └── test_features.py
```

## 6. 各目录职责

- `configs/`
  放参数配置，不把窗口大小、阈值、字段名单硬编码在脚本里
- `data/raw/`
  只存原始数据，保持可追溯
- `data/interim/`
  存清洗、对齐主键、宽表拼接前的中间结果
- `data/processed/`
  存建模输入，如 `train_features.parquet`
- `sql/`
  放适合用 SQL 验证的规则和特征原型，方便快速交叉验证
- `src/anti_fraud/operators/`
  放通用特征算子，实现复用
- `src/anti_fraud/features/`
  按主题拆分变量，例如 `consistency.py`、`velocity.py`、`cashout.py`
- `src/anti_fraud/rules/`
  放高解释性的命中规则，便于和模型特征同时评估
- `src/anti_fraud/pipelines/`
  放端到端流程，如数据预处理、特征构建、训练评估
- `src/anti_fraud/models/`
  放 POC 阶段的异常检测和监督模型
- `outputs/reports/`
  放最终对外展示材料，例如召回率对比、特征案例分析

## 7. 推荐开发顺序

### Step 1. 完成数据落盘与字段梳理

- 将原始 CSV 放入 `data/raw/`
- 统一主键、时间字段和缺失值语义
- 输出一份字段说明到 `docs/feature_catalog.md`

### Step 2. 实现欺诈算子库

优先实现：

- `Time_Diff`
- `Null_Count`
- `Change_Rate`
- `Relative_Ratio`
- `Window_Count`

这一步完成后，大部分变量都可以参数化生成，而不是逐条手写。

### Step 3. 分主题开发变量

建议至少形成三份特征模块：

- `features/consistency.py`
- `features/velocity.py`
- `features/cashout.py`

每个模块统一输出：

- `SK_ID_CURR`
- `feature_name`
- `feature_value`

或直接输出按 `SK_ID_CURR` 聚合后的宽表。

### Step 4. 规则验证与案例分析

把最直观的规则先跑出来，例如：

- 工龄跳变异常
- 联系方式变更过快
- 历史申请极度密集
- 首期严重逾期
- 高 ATM 取现占比

先看这些规则命中的样本，在 `TARGET=1` 中是否明显富集。

### Step 5. 建立基线模型

建议同时做两类：

- 无监督异常检测：`Isolation Forest`
- 有监督分类：`XGBoost` 或 `LightGBM`

评估重点不是整体 AUC，而是：

- `TARGET=1` 的召回率
- Top-K 风险样本捕获率
- 首期违约/短期恶化样本的命中率

## 8. 首批建议落地的变量清单

建议先做一批“低成本、高解释性”的变量：

- `emp_length_inconsistency_max`
  历史申请中工龄跳变量最大值
- `birth_info_inconsistency_flag`
  年龄信息是否出现逻辑冲突
- `phone_flag_change_count_90d`
  近历史申请中电话标志变更次数
- `document_core_missing_count`
  核心身份证明缺失数
- `document_noncore_only_flag`
  是否仅提供非核心文件
- `recent_application_gap_min`
  最近申请最小间隔
- `recent_application_gap_std`
  历史申请间隔标准差
- `bureau_inquiry_spike_flag`
  征信查询是否突增
- `atm_cashout_ratio_max`
  ATM 取现占比峰值
- `first_payment_delinquency_days`
  首期还款逾期天数
- `fpd_severe_flag`
  首期是否严重逾期
- `org_region_risk_rank`
  组织类型与区域组合风险排名

## 9. README 之外，后续建议补充的文件

当你开始写代码后，建议继续补充：

- `docs/feature_catalog.md`
  记录每个变量的业务含义、口径、来源表、计算方式
- `configs/features.yaml`
  统一配置窗口和阈值
- `sql/*.sql`
  快速原型验证 SQL
- `tests/`
  为关键算子和特征写单测，避免口径漂移

## 10. POC 里程碑建议

可以把项目分成三个短周期：

1. `Week 1`
   完成数据梳理、字段映射、算子库骨架
2. `Week 2`
   完成三大类变量的首版产出和规则验证
3. `Week 3`
   完成基线模型、召回率对比、POC 汇报材料

## 11. 你下一步最值得先做什么

如果要最快推进，我建议下一步直接做下面三件事：

1. 把 Kaggle 原始 CSV 放进 `data/raw/`
2. 先实现 `consistency.py`，因为它最容易快速产出可解释异常变量
3. 再补一条简单训练流水线，验证这些变量是否提升 `TARGET=1` 的召回

## 12. 后续可扩展方向

POC 成功后，可以继续扩展到：

- 引入图关系特征，识别团伙申请网络
- 将规则命中结果与模型分数融合，形成欺诈评分卡
- 将变量产出流程迁移到定时批处理或特征平台
- 引入申请时序行为日志，补充更细粒度的自动化操作识别
