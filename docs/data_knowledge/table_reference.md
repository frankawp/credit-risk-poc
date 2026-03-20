# 表说明与反欺诈价值映射

## application_train / application_test

主申请表，是所有客户级分析的锚点。

关键字段：

- `SK_ID_CURR`
- `TARGET`
- `DAYS_BIRTH`
- `DAYS_EMPLOYED`
- `DAYS_REGISTRATION`
- `DAYS_ID_PUBLISH`
- `FLAG_MOBIL`
- `FLAG_EMP_PHONE`
- `FLAG_WORK_PHONE`
- `FLAG_DOCUMENT_*`
- `AMT_REQ_CREDIT_BUREAU_*`
- `ORGANIZATION_TYPE`
- `REGION_POPULATION_RELATIVE`

反欺诈价值：

- 身份伪造：年龄、工龄、证件、联系方式的一致性
- 征信短期激增：`AMT_REQ_CREDIT_BUREAU_HOUR/DAY/WEEK`
- 团伙入件点：`ORGANIZATION_TYPE + REGION_POPULATION_RELATIVE`

## previous_application

记录客户过去的贷款申请行为。

关键字段：

- `SK_ID_PREV`
- `SK_ID_CURR`
- `DAYS_DECISION`
- `NAME_CONTRACT_STATUS`
- `NAME_CONTRACT_TYPE`

反欺诈价值：

- 申请密度和申请节奏
- 历史申请状态变化率
- 同日多次申请、短时间连续申请

## bureau

记录外部征信机构中客户的历史信用信息。

关键字段：

- `SK_ID_BUREAU`
- `SK_ID_CURR`
- `DAYS_CREDIT`
- `CREDIT_ACTIVE`
- `CREDIT_DAY_OVERDUE`
- `AMT_CREDIT_SUM_DEBT`
- `AMT_CREDIT_SUM_OVERDUE`

反欺诈价值：

- 多头借贷和短期外部授信暴露
- 活跃账户比例
- 历史外部逾期和债务压力

## bureau_balance

征信记录的月度状态表。

关键字段：

- `SK_ID_BUREAU`
- `MONTHS_BALANCE`
- `STATUS`

反欺诈价值：

- 可进一步扩展征信账户状态变化
- 适合后续第二阶段补充月度恶化速度和账户状态不稳定性

当前第一阶段未纳入主流程，主要原因是行数最大，且第一阶段已有足够特征信号。

## credit_card_balance

信用卡月度账单与行为表。

关键字段：

- `SK_ID_CURR`
- `MONTHS_BALANCE`
- `AMT_DRAWINGS_ATM_CURRENT`
- `AMT_DRAWINGS_CURRENT`
- `AMT_TOTAL_RECEIVABLE`
- `SK_DPD`
- `SK_DPD_DEF`

反欺诈价值：

- ATM 取现偏好
- 月度资金使用方式
- 套现倾向和账单风险

## installments_payments

还款级别的分期流水。

关键字段：

- `SK_ID_CURR`
- `NUM_INSTALMENT_NUMBER`
- `DAYS_INSTALMENT`
- `DAYS_ENTRY_PAYMENT`
- `AMT_INSTALMENT`
- `AMT_PAYMENT`

反欺诈价值：

- 首期违约 `FPD`
- 历史逾期比例
- 最大逾期天数

## POS_CASH_balance

POS / cash loan 的月度状态数据。

关键字段：

- `SK_ID_PREV`
- `SK_ID_CURR`
- `MONTHS_BALANCE`
- `CNT_INSTALMENT`
- `CNT_INSTALMENT_FUTURE`
- `SK_DPD`
- `SK_DPD_DEF`

反欺诈价值：

- 可扩展提前结清、月度异常逾期、剩余期数突变等行为特征

当前第一阶段未纳入，是为了先控制复杂度。
