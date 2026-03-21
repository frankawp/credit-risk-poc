# 当前已实现变量

本文件只描述当前仓库里已经落成代码的变量，以及明显值得继续扩展但尚未实现的方向。

## semantic features

### consistency

- `consistency_employed_birth_ratio`
  - 逻辑：`abs(DAYS_EMPLOYED) / (abs(DAYS_BIRTH) + 1)`
  - 含义：工龄占年龄的比例，异常偏高可能不合理

- `consistency_contact_flag_sum`
  - 逻辑：`FLAG_MOBIL + FLAG_EMP_PHONE + FLAG_WORK_PHONE`
  - 含义：联系方式可用数量，越少通常越可疑

- `consistency_prev_credit_gap_ratio_mean`
  - 逻辑：历史申请中 `abs(AMT_CREDIT - AMT_APPLICATION) / (abs(AMT_APPLICATION) + 1)` 的均值
  - 含义：申请金额与批核金额长期偏差是否异常

- `consistency_prev_status_change_rate`
  - 逻辑：历史合同状态去重数 / 历史申请数
  - 含义：历史状态切换是否异常频繁

### velocity

- `velocity_prev_count_7d`
  - 逻辑：`previous_application` 中 `DAYS_DECISION >= -7` 的笔数

- `velocity_prev_count_30d`
  - 逻辑：`previous_application` 中 `DAYS_DECISION >= -30` 的笔数

- `velocity_prev_decision_gap_std`
  - 逻辑：历史申请决策时间间隔的标准差

- `velocity_bureau_recent_credit_count_30d`
  - 逻辑：`bureau` 中 `DAYS_CREDIT >= -30` 的笔数

### cashout

- `cashout_atm_ratio_mean`
  - 逻辑：`AMT_DRAWINGS_ATM_CURRENT / (abs(AMT_DRAWINGS_CURRENT) + 1)` 的客户级均值

- `cashout_first_payment_delinquency_days_max`
  - 逻辑：首期还款 `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT` 的最大值

- `cashout_fpd_severe_flag`
  - 逻辑：首期逾期是否大于 30 天

- `cashout_installments_late_ratio`
  - 逻辑：分期还款记录中逾期笔数占比

## composite features

- `composite_velocity_x_cashout`
  - 公式：`fillna(velocity_prev_count_7d, 0) * fillna(cashout_atm_ratio_mean, 0)`
  - 含义：短期申请密度与 ATM 套现偏好共振

- `composite_consistency_velocity_flag`
  - 公式：`1 if consistency_prev_credit_gap_ratio_mean > 0.20 and velocity_prev_count_30d >= 3 else 0`
  - 含义：申请/批核金额偏差异常且近期申请密度高

- `composite_fpd_velocity_flag`
  - 公式：`1 if cashout_fpd_severe_flag == 1 and velocity_prev_count_7d >= 2 else 0`
  - 含义：首期严重逾期与短期申请 burst 同时出现

## 尚未实现但建议继续挖掘

- `collusion` 相关变量
  - 例如：地区 x 组织类型风险、群组申请密度、弱团伙共现

- 更强的 `consistency`
  - 例如：跨次申请工龄跳变、年龄逻辑冲突

- 更强的 `velocity`
  - 例如：更短时间窗口、bureau_balance 月度轨迹
