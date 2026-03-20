# Feature Catalog

本文件是 POC 第一阶段的变量手册，面向分析、建模和业务沟通共同使用。

适用范围：

- 当前客户级宽表 [train_features.parquet](/Users/frankliu/Code/credit-risk-poc/data/processed/train_features.parquet)
- 当前特征元数据 [feature_metadata.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/feature_metadata.csv)
- 当前第一阶段基线模型结果 [baseline_metrics.json](/Users/frankliu/Code/credit-risk-poc/outputs/models/baseline_metrics.json)

统一约定：

- 聚合粒度：`SK_ID_CURR`
- 标签：`TARGET`
- 口径阶段：Phase 1 baseline
- 说明原则：这些变量是“反欺诈/高风险代理变量”，不是欺诈真值

## 1. 手册阅读方式

每个变量按以下维度描述：

- `feature_name`
  训练宽表中的列名
- `source_table`
  来源表
- `formula`
  计算方式或聚合逻辑
- `risk_direction`
  变量增大时通常代表风险升高还是降低
- `business_meaning`
  业务解释
- `current_distribution`
  基于本次实际跑数的分布摘要
- `notes`
  使用风险、异常值和后续优化建议

## 2. 宽表总览

当前宽表概况：

- 样本数：`307,511`
- 特征列数：`31`
- 主键：`SK_ID_CURR`
- 标签列：`TARGET`

特征主题分为三类：

1. 信息不一致性 `Consistency`
2. 短期高频行为 `Velocity`
3. 套现与团伙特征 `Cash-out & Collusion`

## 3. 信息不一致性特征

### `emp_age_ratio`

- `source_table`: `application_train`
- `formula`: `abs(DAYS_EMPLOYED) / abs(DAYS_BIRTH)`
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 工龄相对年龄的占比。如果工龄占年龄过高，说明资料逻辑异常或编码异常。
- `current_distribution`: missing=`0.00%`, mean=`3.18`, p95=`17.41`, max=`47.49`
- `notes`: 这个变量明显受 `DAYS_EMPLOYED=365243` 特殊值影响，因此不应单独使用，需结合异常标记一起看。

### `employed_birth_inconsistency_flag`

- `source_table`: `application_train`
- `formula`: 当 `emp_age_ratio > 0.8` 或 `DAYS_EMPLOYED == 365243` 时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 标记工龄与年龄逻辑冲突，或工龄字段出现已知特殊异常值。
- `current_distribution`: missing=`0.00%`, mean=`0.1801`
- `notes`: 当前约 `18%` 样本命中，说明该规则较宽，后续可拆成“极端工龄占比”和“365243 特殊值”两个子变量。

### `phone_contact_coverage`

- `source_table`: `application_train`
- `formula`: `FLAG_MOBIL + FLAG_EMP_PHONE + FLAG_WORK_PHONE + FLAG_CONT_MOBILE + FLAG_PHONE + FLAG_EMAIL`
- `risk_direction`: 偏低通常更可疑
- `business_meaning`: 联系方式标识覆盖度。联系方式越稀疏，身份稳定性通常越弱。
- `current_distribution`: missing=`0.00%`, mean=`3.36`, p95=`5.00`, max=`6.00`
- `notes`: 这是覆盖度代理，不是真实的联系方式数量；它依赖的是标识位而不是手机号实体值。

### `phone_flags_sparse_flag`

- `source_table`: `application_train`
- `formula`: 当 `phone_contact_coverage <= 1` 时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 联系方式极度稀疏标记。
- `current_distribution`: missing=`0.00%`, mean=`0.00009`
- `notes`: 当前命中率极低，属于高精度、低覆盖的小众规则，后续应结合业务样本回看。

### `phone_flags_mismatch_score`

- `source_table`: `application_train`
- `formula`: `abs(FLAG_MOBIL - FLAG_CONT_MOBILE) + abs(FLAG_EMP_PHONE - FLAG_WORK_PHONE)`
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 移动联系方式和工作联系方式之间的错配程度。
- `current_distribution`: missing=`0.00%`, mean=`0.62`, p95=`1.00`, max=`2.00`
- `notes`: 这个变量反映的是联系方式结构异常，不是“换号次数”，因为公开数据中没有手机号实体。

### `document_core_missing_count`

- `source_table`: `application_train`
- `formula`: 核心证件组 `FLAG_DOCUMENT_2~6` 中未提供的数量
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 核心证件缺失越多，身份真实性越弱。
- `current_distribution`: missing=`0.00%`, mean=`4.19`, p95=`5.00`, max=`5.00`
- `notes`: 当前分布偏高，说明“核心证件标识”在该公开数据里普遍稀疏，不能按真实业务通过率直接理解。

### `document_noncore_count`

- `source_table`: `application_train`
- `formula`: 所有非核心 `FLAG_DOCUMENT_*` 之和
- `risk_direction`: 单独看方向不固定，需与核心证件联合解释
- `business_meaning`: 反映非核心证件的补充程度。
- `current_distribution`: missing=`0.00%`, mean=`0.12`, p95=`1.00`, max=`4.00`
- `notes`: 更适合与 `document_core_missing_count` 组合使用，而不是单独解释。

### `document_noncore_only_flag`

- `source_table`: `application_train`
- `formula`: 当核心证件全缺失且非核心证件数大于 0 时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 典型“关键证件缺失，但边缘证件有提交”的代理模式。
- `current_distribution`: missing=`0.00%`, mean=`0.0906`
- `notes`: 当前约 `9.06%` 样本命中，是较有业务解释力的组合特征。

### `days_id_publish_vs_registration_gap`

- `source_table`: `application_train`
- `formula`: `abs(DAYS_ID_PUBLISH - DAYS_REGISTRATION)`
- `risk_direction`: 偏高时可能更可疑
- `business_meaning`: 证件发布时间与注册地址变更时间的偏差，用于刻画身份资料稳定性。
- `current_distribution`: missing=`0.00%`, mean=`3234.49`, p95=`8700.00`, max=`21118.00`
- `notes`: 这是弱代理变量，业务解释较间接。后续更适合作为辅助特征，而非规则主特征。

### `prev_status_change_rate`

- `source_table`: `previous_application`
- `formula`: 按 `SK_ID_CURR` 将历史申请按 `DAYS_DECISION` 排序后，计算 `NAME_CONTRACT_STATUS` 的切换率
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 历史申请状态频繁变化，可能意味着反复申请、反复被拒或行为模式不稳定。
- `current_distribution`: missing=`0.00%`, mean=`0.2907`, p95=`1.00`, max=`1.00`
- `notes`: 这是“历史行为一致性”的代理值，比静态身份字段更接近真实申请行为。

## 4. 短期高频行为特征

### `bureau_inquiry_intensity`

- `source_table`: `application_train`
- `formula`: `3 * AMT_REQ_CREDIT_BUREAU_HOUR + 2 * AMT_REQ_CREDIT_BUREAU_DAY + AMT_REQ_CREDIT_BUREAU_WEEK`
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 对短期征信查询做加权，小时级和日级查询权重更高。
- `current_distribution`: missing=`0.00%`, mean=`0.0584`, p95=`0.00`, max=`27.00`
- `notes`: 分布极偏，说明大多数样本近端查询为 0；该特征更适合识别少量异常激增样本。

### `bureau_inquiry_spike_flag`

- `source_table`: `application_train`
- `formula`: 当 `AMT_REQ_CREDIT_BUREAU_DAY >= 2` 或 `AMT_REQ_CREDIT_BUREAU_WEEK >= 4` 时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 短期征信查询激增标记。
- `current_distribution`: missing=`0.00%`, mean=`0.00075`
- `notes`: 命中率极低，适合作为强异常规则，不适合作为单独覆盖型规则。

### `recent_application_gap_min`

- `source_table`: `previous_application`
- `formula`: 历史申请按 `DAYS_DECISION` 排序后的最小间隔绝对值
- `risk_direction`: 偏低通常更可疑
- `business_meaning`: 最短申请间隔越小，越像集中冲击式申请。
- `current_distribution`: missing=`22.43%`, mean=`185.66`, p95=`986.00`, max=`2895.00`
- `notes`: 缺失主要来自没有足够历史申请记录的客户。对缺失应理解为“无历史或历史不足”，不是坏数据。

### `recent_application_gap_std`

- `source_table`: `previous_application`
- `formula`: 历史申请间隔的标准差
- `risk_direction`: 偏低可能表示极度集中，偏高可能表示行为不稳定，需结合其他变量解释
- `business_meaning`: 刻画申请时间分布是否集中或离散。
- `current_distribution`: missing=`22.43%`, mean=`242.65`, p95=`729.15`, max=`1458.50`
- `notes`: 单独方向不稳定，更适合与申请次数和 burst 标记联合使用。

### `recent_application_count_7d`

- `source_table`: `previous_application`
- `formula`: `DAYS_DECISION` 落在近 7 天窗口的申请数
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 短期申请次数。
- `current_distribution`: missing=`5.35%`, mean=`0.0260`, p95=`0.00`, max=`21.00`
- `notes`: 该变量极度稀疏，但尾部样本很有价值。

### `recent_application_count_30d`

- `source_table`: `previous_application`
- `formula`: `DAYS_DECISION` 落在近 30 天窗口的申请数
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 月内申请密度。
- `current_distribution`: missing=`5.35%`, mean=`0.1134`, p95=`1.00`, max=`31.00`
- `notes`: 相比 7 天窗口覆盖更高，适合作为主密度特征。

### `burst_same_day_flag`

- `source_table`: `previous_application`
- `formula`: 当同一 `DAYS_DECISION` 下申请次数达到阈值时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 同日多次申请，通常是代办、扫单或重复入件的高风险代理。
- `current_distribution`: missing=`5.35%`, mean=`0.1615`
- `notes`: 命中率不低，且业务解释清晰，是当前较好的规则型变量。

### `consecutive_application_flag`

- `source_table`: `previous_application`
- `formula`: 当近 7 天申请数至少为 3，或最小申请间隔不超过 1 天时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 短期内连续密集申请标记。
- `current_distribution`: missing=`5.35%`, mean=`0.4342`
- `notes`: 当前命中率较高，阈值偏宽，第二阶段可考虑拆分为多个强度层级。

### `bureau_recent_credit_count_7d`

- `source_table`: `bureau`
- `formula`: `DAYS_CREDIT` 落在近 7 天窗口的征信记录数
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 客户近端外部授信暴露数量。
- `current_distribution`: missing=`14.31%`, mean=`0.0025`, p95=`0.00`, max=`4.00`
- `notes`: 稀疏但重要，模型中表现较好。

### `bureau_recent_credit_count_30d`

- `source_table`: `bureau`
- `formula`: `DAYS_CREDIT` 落在近 30 天窗口的征信记录数
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 近一个月外部授信活跃度。
- `current_distribution`: missing=`14.31%`, mean=`0.0400`, p95=`0.00`, max=`10.00`
- `notes`: 在当前模型中重要性较高，说明外部授信活跃度是有效风险代理。

### `bureau_active_credit_ratio`

- `source_table`: `bureau`
- `formula`: `CREDIT_ACTIVE == 'Active'` 的账户占比
- `risk_direction`: 偏高通常更可疑，但需结合债务和近期活动解释
- `business_meaning`: 活跃信贷账户越多，客户可能越处于借贷扩张期。
- `current_distribution`: missing=`14.31%`, mean=`0.4130`, p95=`1.00`, max=`1.00`
- `notes`: 当前模型中重要性较高，属于稳定、覆盖度较好的征信行为变量。

## 5. 套现与团伙特征

### `atm_cashout_ratio_max`

- `source_table`: `credit_card_balance`
- `formula`: 客户历史月度中 `AMT_DRAWINGS_ATM_CURRENT / AMT_TOTAL_RECEIVABLE` 的最大值
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: ATM 取现相对于应收总额的极端偏好程度。
- `current_distribution`: missing=`80.64%`, mean=`43.99`, p95=`3.36`, max=`2000000.00`
- `notes`: 分布存在极端离群值，说明分母很小时比率会爆炸。当前口径适合做异常信号，但建模前应考虑截尾或 winsorize。

### `atm_cashout_ratio_mean`

- `source_table`: `credit_card_balance`
- `formula`: 历史月度 `AMT_DRAWINGS_ATM_CURRENT / AMT_TOTAL_RECEIVABLE` 的均值
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 长期 ATM 取现偏好。
- `current_distribution`: missing=`80.64%`, mean=`8.13`, p95=`0.72`, max=`400007.11`
- `notes`: 同样受极小分母影响严重，建议后续改为对分母加下限或改用 `ATM / total drawings`。

### `atm_heavy_usage_months`

- `source_table`: `credit_card_balance`
- `formula`: 当 `AMT_DRAWINGS_ATM_CURRENT / AMT_DRAWINGS_CURRENT >= 0.8` 时记 1，再对月份求和
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 高 ATM 使用偏好持续出现的月份数。
- `current_distribution`: missing=`71.74%`, mean=`3.62`, p95=`16.00`, max=`68.00`
- `notes`: 比纯比率更稳，因为它变成了次数型特征；当前比率类里这个口径更适合保留。

### `credit_card_max_dpd_def`

- `source_table`: `credit_card_balance`
- `formula`: 历史最大 `SK_DPD_DEF`
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 信用卡维度的历史最大逾期代理值。
- `current_distribution`: missing=`71.74%`, mean=`0.78`, p95=`1.00`, max=`2800.00`
- `notes`: 极端值较大，建议后续增加对数化或分桶。

### `max_days_past_due_installments`

- `source_table`: `installments_payments`
- `formula`: `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT` 的最大值
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 客户历史分期中的最大逾期天数。
- `current_distribution`: missing=`5.16%`, mean=`16.23`, p95=`35.00`, max=`2884.00`
- `notes`: 覆盖度高，风险解释清晰，是当前贷后行为中很强的一类变量。

### `installments_late_ratio`

- `source_table`: `installments_payments`
- `formula`: 历史还款中 `days_late > 0` 的比例
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 贷后还款稳定性差的客户，通常风险更高。
- `current_distribution`: missing=`5.16%`, mean=`0.0758`, p95=`0.3291`, max=`1.00`
- `notes`: 当前模型中重要性较高，是第一阶段最有效的贷后行为变量之一。

### `first_payment_delinquency_days`

- `source_table`: `installments_payments`
- `formula`: 首笔还款记录的 `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT`
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 首期还款逾期天数，是典型 `FPD` 口径。
- `current_distribution`: missing=`5.16%`, mean=`-11.82`, p95=`0.00`, max=`2790.00`
- `notes`: 均值为负说明多数客户提前或按时还款。该变量本身很有价值，但当前严重逾期样本较少。

### `fpd_severe_flag`

- `source_table`: `installments_payments`
- `formula`: 当 `first_payment_delinquency_days >= 30` 时取 `1`
- `risk_direction`: `1` 更可疑
- `business_meaning`: 首期严重逾期标记。
- `current_distribution`: missing=`5.16%`, mean=`0.00073`
- `notes`: 当前命中极低，导致本次 FPD slice 仅 45 个验证样本，暂时不足以稳定评估切片模型效果。

### `org_region_bad_rate`

- `source_table`: `application_train`
- `formula`: 按 `ORGANIZATION_TYPE + REGION_POPULATION_RELATIVE` 分桶组合计算 `TARGET` 坏账率
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 高危组织类型和区域组合的群体风险画像。
- `current_distribution`: missing=`0.00%`, mean=`0.0807`, p95=`0.1165`, max=`0.3333`
- `notes`: 这是群体层编码变量，解释时应避免说成客户自身属性，而应理解为“所处群体风险”。

### `org_region_risk_rank`

- `source_table`: `application_train`
- `formula`: 对 `org_region_bad_rate` 做群组风险排序分位
- `risk_direction`: 偏高通常更可疑
- `business_meaning`: 组织与区域组合处于更高风险层级时，客户也更可能属于高风险申请。
- `current_distribution`: missing=`0.00%`, mean=`0.5064`, p95=`0.8633`, max=`1.00`
- `notes`: 这是当前模型里重要性最高的变量，说明群体风险代理在公开数据中非常有效。

## 6. 当前模型中的高价值变量

基于当前 [baseline_metrics.json](/Users/frankliu/Code/credit-risk-poc/outputs/models/baseline_metrics.json)，前几位重要特征包括：

1. `org_region_risk_rank`
2. `bureau_recent_credit_count_7d`
3. `installments_late_ratio`
4. `org_region_bad_rate`
5. `bureau_active_credit_ratio`
6. `document_core_missing_count`
7. `bureau_recent_credit_count_30d`
8. `emp_age_ratio`

当前可得出的结论：

- 群体风险编码在公开数据里作用很强
- 征信近期活跃度是稳定的风险信号
- 贷后逾期行为对 `TARGET` 区分能力明显
- 纯静态身份变量有用，但单独贡献不如行为变量和群体变量

## 7. 当前已知问题与后续优化建议

### 比率类极端值

受分母很小影响，以下变量存在明显爆炸值：

- `atm_cashout_ratio_max`
- `atm_cashout_ratio_mean`

建议后续：

- 对分母设置下限
- 使用 winsorize / clip
- 增加对数变换版特征

### 稀疏规则命中率低

以下变量命中率极低：

- `phone_flags_sparse_flag`
- `bureau_inquiry_spike_flag`
- `fpd_severe_flag`

建议后续：

- 保留为规则型特征
- 不要期待它们单独贡献大面积覆盖
- 增加近似强度变量，而不只做二值标记

### 时间口径仍是相对时间

当前所有时间特征基于相对天数，不是绝对时点。后续如接入真实业务数据，应优先升级为：

- 真实事件时间戳
- 真实申请渠道
- 真实设备 / 身份主键

## 8. 使用建议

在后续分析或建模中，建议按下面方式使用这份变量手册：

- 规则引擎优先看：
  - `document_noncore_only_flag`
  - `burst_same_day_flag`
  - `bureau_inquiry_spike_flag`
  - `fpd_severe_flag`
- 排序模型优先看：
  - `org_region_risk_rank`
  - `bureau_recent_credit_count_7d`
  - `installments_late_ratio`
  - `bureau_active_credit_ratio`
  - `emp_age_ratio`
- 需要二次加工的变量：
  - `atm_cashout_ratio_max`
  - `atm_cashout_ratio_mean`
  - `recent_application_gap_std`

这份手册在第二阶段应继续扩展，纳入：

- 更细的征信月度状态特征
- `POS_CASH_balance` 相关变量
- 图关系或群体共现特征
