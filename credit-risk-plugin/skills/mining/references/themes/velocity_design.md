# 高频申请（velocity）主题变量设计

## 业务背景

识别短时间高频申请、多头借贷激增、脚本化申请行为的风险客户。常见模式：

- 短期内多次申请贷款
- 多平台同时申请（多头）
- 申请时间间隔异常规律
- 征信近期活跃度异常

## 设计维度

### 维度1：短期申请密度

识别短期内的申请聚集行为。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `velocity_prev_count_7d` | previous_application 中 DAYS_DECISION >= -7 的笔数 | 7天内多次申请资金可能紧张 |
| `velocity_prev_count_30d` | previous_application 中 DAYS_DECISION >= -30 的笔数 | 30天内申请密度高风险 |
| `velocity_prev_count_90d` | previous_application 中 DAYS_DECISION >= -90 的笔数 | 季度申请密度参考 |

### 维度2：申请间隔规律

识别申请时间间隔的异常模式。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `velocity_prev_decision_gap_std` | 历史申请决策时间间隔的标准差 | 间隔稳定可能是脚本化申请 |
| `velocity_prev_decision_gap_min` | 历史申请最小间隔天数 | 极短间隔可能是急迫或脚本 |
| `velocity_prev_burst_flag` | 是否有短时间内(3天内)连续申请 | burst 申请高风险 |

### 维度3：征信活跃度

识别征信报告中的近期活跃行为。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `velocity_bureau_recent_credit_count_30d` | bureau 中 DAYS_CREDIT >= -30 的笔数 | 近期征信查询多可能多头 |
| `velocity_bureau_recent_credit_count_7d` | bureau 中 DAYS_CREDIT >= -7 的笔数 | 极短期征信查询高风险 |
| `velocity_bureau_active_count` | 当前活跃信用账户数 | 活跃账户过多可能负债高 |

## 实现优先级

1. **高优先级**（已实现）：
   - velocity_prev_count_7d
   - velocity_prev_count_30d
   - velocity_prev_decision_gap_std
   - velocity_bureau_recent_credit_count_30d

2. **中优先级**（建议扩展）：
   - velocity_prev_count_90d
   - velocity_prev_decision_gap_min
   - velocity_prev_burst_flag

## 扩展方向

- 更短时间窗口（1天、3天）
- 月度轨迹分析
- 申请时间分布熵值
- 跨平台多头检测
