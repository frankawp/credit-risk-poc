# 套现风险（cashout）主题变量设计

## 业务背景

识别套现倾向、首期违约、异常还款行为的风险客户。常见模式：

- 信用卡 ATM 取现比例异常
- 首期还款逾期或违约
- 分期还款行为异常
- 资金流向可疑

## 设计维度

### 维度1：取现行为

识别信用卡取现异常行为。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `cashout_atm_ratio_mean` | `AMT_DRAWINGS_ATM_CURRENT / (AMT_DRAWINGS_CURRENT + 1)` 客户级均值 | ATM 取现比例高可能是套现 |
| `cashout_atm_ratio_max` | 单月最大 ATM 取现比例 | 极端取现行为高风险 |
| `cashout_atm_count` | ATM 取现次数 | 频繁取现可能是套现 |

**数据需求**：
| 字段 | 来源表 | 必需/可选 |
|------|--------|----------|
| AMT_DRAWINGS_ATM_CURRENT | credit_card_balance | 必需 |
| AMT_DRAWINGS_CURRENT | credit_card_balance | 必需 |

### 维度2：首期还款行为

识别首期还款异常的申请人。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `cashout_first_payment_delinquency_days_max` | 首期还款 `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT` 最大值 | 首期逾期天数多高风险 |
| `cashout_fpd_severe_flag` | 首期逾期是否 > 30 天 | 严重首期逾期极高风险 |
| `cashout_first_payment_gap_mean` | 首期还款偏差均值 | 首期还款不稳定高风险 |

**数据需求**：
| 字段 | 来源表 | 必需/可选 |
|------|--------|----------|
| NUM_INSTALMENT_NUMBER | installments_payments | 必需 |
| DAYS_INSTALMENT | installments_payments | 必需 |
| DAYS_ENTRY_PAYMENT | installments_payments | 必需 |

### 维度3：分期还款行为

识别分期还款的异常模式。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `cashout_installments_late_ratio` | 分期还款逾期笔数占比 | 逾期比例高信用差 |
| `cashout_installments_late_amount_ratio` | 分期还款逾期金额占比 | 逾期金额大风险高 |
| `cashout_payment_gap_std` | 还款时间偏差标准差 | 还款不稳定高风险 |

**数据需求**：
| 字段 | 来源表 | 必需/可选 |
|------|--------|----------|
| DAYS_INSTALMENT | installments_payments | 必需 |
| DAYS_ENTRY_PAYMENT | installments_payments | 必需 |
| AMT_INSTALMENT | installments_payments | 必需 |
| AMT_PAYMENT | installments_payments | 必需 |

### 维度4：额度使用行为

识别额度使用异常。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `cashout_credit_utilization_max` | 最大额度使用率 | 高额度使用可能资金紧张 |
| `cashout_credit_utilization_mean` | 平均额度使用率 | 持续高使用率高风险 |
| `cashout_balance_trend` | 余额变化趋势 | 余额快速增长可能是套现 |

**数据需求**：
| 字段 | 来源表 | 必需/可选 |
|------|--------|----------|
| AMT_BALANCE | credit_card_balance | 必需 |
| AMT_CREDIT_LIMIT_ACTUAL | credit_card_balance | 必需 |

## 实现优先级

1. **高优先级**（已实现）：
   - cashout_atm_ratio_mean
   - cashout_first_payment_delinquency_days_max
   - cashout_fpd_severe_flag
   - cashout_installments_late_ratio

2. **中优先级**（建议扩展）：
   - cashout_atm_ratio_max
   - cashout_installments_late_amount_ratio
   - cashout_credit_utilization_max

3. **低优先级**（数据依赖）：
   - cashout_balance_trend（需要时序分析）
   - cashout_payment_gap_std

## 扩展方向

- 资金流向分析（需要交易明细）
- 商户类型分布（需要 MCC 码）
- 取现-还款时间间隔
- 异常商户交易检测
