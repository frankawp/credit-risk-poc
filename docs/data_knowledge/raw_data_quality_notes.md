# 原始数据质量与使用注意事项

## 1. 编码

- `HomeCredit_columns_description.csv` 不是 UTF-8
- 实际读取应使用 `cp1252` 或 `latin-1`

## 2. 时间字段语义

大量时间字段使用“相对申请日的天数”，通常为负数：

- `DAYS_BIRTH`
- `DAYS_EMPLOYED`
- `DAYS_DECISION`
- `DAYS_CREDIT`
- `DAYS_INSTALMENT`

使用时应注意：

- 不要误解为绝对日期
- 负值绝对值越大，通常表示事件离申请日越久
- 做窗口计数时，应明确窗口方向和阈值

## 3. 特殊值

在 `DAYS_EMPLOYED` 中，`365243` 是已知特殊值，通常代表缺失或异常编码，不应按正常工龄解释。

## 4. 大表内存压力

以下表行数较大，分析时不宜一次性全量读入：

- `bureau_balance.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `credit_card_balance.csv`

建议策略：

- 列裁剪
- 分块读取
- 尽早做客户级聚合

## 5. 标签解释风险

`TARGET` 是违约困难标签，不是欺诈标签。对结果解释时应避免：

- 将模型命中样本直接定义为欺诈
- 将特征重要性直接解释为欺诈因果

更合理的表述应是：

- 高风险
- 可疑申请
- 疑似异常行为
