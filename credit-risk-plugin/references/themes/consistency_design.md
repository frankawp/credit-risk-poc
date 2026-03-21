# 一致性（consistency）主题变量设计

## 业务背景

识别资料前后不一致、身份伪造、稳定性异常的风险客户。常见模式：

- 申请资料与历史记录矛盾
- 工龄/年龄逻辑冲突
- 联系方式缺失或不稳定
- 申请金额与批核金额长期偏差异常

## 设计维度

### 维度1：身份逻辑一致性

识别身份信息之间的逻辑冲突。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `consistency_employed_birth_ratio` | `abs(DAYS_EMPLOYED) / (abs(DAYS_BIRTH) + 1)` | 工龄占年龄比例异常偏高可能造假 |
| `consistency_employed_years_change` | 跨次申请工龄跳变幅度 | 工龄短期内大幅增长不合理 |

### 维度2：联系方式完整性

识别联系方式缺失或不稳定的申请人。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `consistency_contact_flag_sum` | FLAG_MOBIL + FLAG_EMP_PHONE + FLAG_WORK_PHONE | 联系方式越少越可疑 |

### 维度3：申请金额一致性

识别申请金额与批核金额的异常偏差模式。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `consistency_prev_credit_gap_ratio_mean` | 历史 `abs(AMT_CREDIT - AMT_APPLICATION) / (AMT_APPLICATION + 1)` 均值 | 长期偏差异常可能是试探性申请 |
| `consistency_prev_credit_gap_std` | 历史 `AMT_CREDIT - AMT_APPLICATION` 标准差 | 波动大可能申请行为不稳定 |

### 维度4：状态稳定性

识别历史状态切换异常频繁的申请人。

| 变量名 | 计算逻辑 | 业务假设 |
|--------|----------|----------|
| `consistency_prev_status_change_rate` | 历史合同状态去重数 / 历史申请数 | 状态切换频繁可能申请行为异常 |
| `consistency_prev_status_types` | 历史出现过的状态类型数 | 状态类型过多可能信用复杂 |

## 实现优先级

1. **高优先级**（已实现）：
   - consistency_employed_birth_ratio
   - consistency_contact_flag_sum
   - consistency_prev_credit_gap_ratio_mean
   - consistency_prev_status_change_rate

2. **中优先级**（建议扩展）：
   - consistency_employed_years_change
   - consistency_prev_credit_gap_std

## 扩展方向

- 跨表信息一致性检查
- 时间序列上的稳定性分析
- 多维度交叉一致性验证
