# 变量设计方法论

本文档指导如何设计有价值的风险变量。

## 设计原则

### 1. 业务假设驱动

每个变量都要回答一个问题："这个变量为什么能识别风险？"

**好的假设示例**：
- "短期内多次申请贷款的人，资金链可能紧张，违约风险更高"
- "ATM 取现比例高的人，可能有套现行为"

**坏的假设示例**：
- "我觉得这个变量可能有用"（没有业务逻辑）
- "别人论文里用过"（不考虑适用场景）

### 2. 数据可验证

假设必须能用现有数据验证。

**可验证**：
- "7 天内申请次数 > 3 的客户违约率更高" → 可用 previous_application 表验证

**不可验证**：
- "客户情绪不稳定时风险高" → 没有情绪数据

### 3. 方向明确

设计时就要明确预期方向：
- `higher_is_riskier`：变量值越高，风险越高
- `lower_is_riskier`：变量值越低，风险越高

## 设计流程

### Step 1: 从业务问题出发

```
业务问题 → 风险场景 → 观测点 → 变量假设
```

示例：
- 业务问题：首期违约率高
- 风险场景：套现后快速失联
- 观测点：首期还款行为
- 变量假设：首期还款逾期天数越多，后续违约风险越高

### Step 2: 确定数据来源

列出需要的数据表和字段：

| 变量 | 主表 | 关联表 | 关键字段 |
|------|------|--------|----------|
| 首期逾期天数 | installments_payments | - | DAYS_INSTALMENT, DAYS_ENTRY_PAYMENT |
| 7 天申请次数 | previous_application | - | DAYS_DECISION |
| ATM 取现比例 | credit_card_balance | - | AMT_DRAWINGS_ATM_CURRENT |

### Step 3: 设计计算逻辑

用伪代码或公式描述：

```
velocity_prev_count_7d = count(previous_application where DAYS_DECISION >= -7)
cashout_atm_ratio = sum(AMT_DRAWINGS_ATM_CURRENT) / sum(AMT_DRAWINGS_CURRENT)
```

### Step 4: 预估效果

基于经验或类似场景，预估：
- 预期 ROC-AUC 范围
- 预期覆盖率
- 可能的问题（缺失、异常值）

## 常见变量模式

### 计数类

适用于：频率、次数统计

```python
# 时间窗口计数
count_7d = df[df["DAYS"] >= -7].groupby("SK_ID_CURR").size()

# 条件计数
count_flag = df[df["AMT"] > threshold].groupby("SK_ID_CURR").size()
```

### 比例类

适用于：偏好、占比

```python
# 占比
ratio = numerator / (denominator + 1)  # 加 1 避免除零

# 平均比例
ratio_mean = df.groupby("SK_ID_CURR").apply(lambda g: g["numerator"].sum() / (g["denominator"].sum() + 1))
```

### 时间类

适用于：间隔、趋势

```python
# 间隔统计
gaps = np.diff(np.sort(df["DAYS"]))
gap_std = np.std(gaps)

# 最近一次距今天数
last_days = df.groupby("SK_ID_CURR")["DAYS"].max()
```

### 聚合类

适用于：多表关联

```python
# 多表聚合
result = anchor.merge(agg1, on="SK_ID_CURR", how="left")
result = result.merge(agg2, on="SK_ID_CURR", how="left")
```

## 避免的坑

### 1. 数据泄漏

不要用申请后的数据预测申请时的风险：

**错误**：用当前贷款状态预测当前贷款违约
**正确**：用历史贷款数据预测当前贷款违约

### 2. 过度拟合

不要设计过于具体的变量：

**过度**：`最近 3 天凌晨 2-4 点申请次数`
**合理**：`最近 7 天申请次数`

### 3. 忽略覆盖

一个变量如果覆盖不到 1% 的客户，很难发挥作用。

### 4. 相关性陷阱

两个变量高度相关时，选一个即可，不要都保留。

## 与 AI 协作

设计变量时，可以：

1. **描述业务场景**：让 AI 帮你转化为变量假设
2. **提供数据结构**：让 AI 推荐可能的变量
3. **讨论假设合理性**：与 AI 讨论假设是否有漏洞
4. **迭代优化**：根据效果反馈调整设计

AI 会帮助你：
- 补充遗漏的维度
- 指出潜在的逻辑漏洞
- 生成实现代码
- 评估变量效果
