# 变量设计指南

本文档提供变量设计的详细指南，包括主题分类、命名规范和设计模板。

## 变量主题分类

### 一致性主题 (consistency)

**业务含义**：身份信息、资料填写的稳定性与一致性。

**假设基础**：
- 频繁变更信息的用户风险更高
- 资料不一致可能暗示欺诈意图

**典型变量**：
| 变量名 | 含义 | 预期方向 |
|--------|------|----------|
| consistency_address_change_count | 地址变更次数 | 越高风险越大 |
| consistency_phone_change_count | 电话变更次数 | 越高风险越大 |
| consistency_income_stability | 收入稳定性 | 越低风险越大 |
| consistency_employment_years | 工作年限 | 越低风险越大 |

### 高频申请主题 (velocity)

**业务含义**：短期内的申请、查询、活动频率。

**假设基础**：
- 短期高频申请暗示资金紧张
- 多头借贷是重要的风险信号

**典型变量**：
| 变量名 | 含义 | 预期方向 |
|--------|------|----------|
| velocity_apply_count_7d | 近7天申请次数 | 越高风险越大 |
| velocity_apply_count_30d | 近30天申请次数 | 越高风险越大 |
| velocity_query_count_90d | 近90天查询次数 | 越高风险越大 |
| velocity_loan_count_active | 活跃贷款数量 | 越高风险越大 |

### 套现倾向主题 (cashout)

**业务含义**：信用卡套现、现金提取相关的行为特征。

**假设基础**：
- 高 ATM 取现比例可能暗示套现
- 大额整数消费可能是套现行为

**典型变量**：
| 变量名 | 含义 | 预期方向 |
|--------|------|----------|
| cashout_atm_ratio | ATM取现占比 | 越高风险越大 |
| cashout_round_amount_ratio | 整数金额交易占比 | 越高风险越大 |
| cashout_first_payment_ratio | 首期还款比例 | 越低风险越大 |
| cashout_cash_advance_count | 预借现金次数 | 越高风险越大 |

### 历史表现主题 (history)

**业务含义**：过往信用表现和还款行为。

**假设基础**：
- 过往逾期是未来逾期的强预测因子
- 还款行为模式反映信用意愿

**典型变量**：
| 变量名 | 含义 | 预期方向 |
|--------|------|----------|
| history_overdue_count | 历史逾期次数 | 越高风险越大 |
| history_overdue_max_days | 最大逾期天数 | 越高风险越大 |
| history_repayment_rate | 还款率 | 越低风险越大 |
| history_good_months | 正常还款月数 | 越低风险越大 |

## 变量命名规范

### 基本规则

1. **格式**：`{theme}_{具体含义}_{时间窗口}`
2. **主题**：使用英文小写
3. **含义**：使用英文单词，避免缩写
4. **时间窗口**：使用 `Xd` (天)、`Xm` (月)、`Xy` (年)

### 示例

✅ 正确示例：
- `velocity_apply_count_30d` - 近30天申请次数
- `cashout_atm_ratio_mean` - ATM取现占比均值
- `history_overdue_count_12m` - 近12个月逾期次数

❌ 错误示例：
- `apply_cnt` - 缺少主题前缀
- `v_30d_cnt` - 使用了缩写
- `申请次数` - 使用了中文

## 变量设计模板

### 单变量设计

```yaml
变量名: velocity_apply_count_30d
主题: velocity
业务假设: 短期高频申请的用户资金紧张，违约风险更高
预期方向: higher_is_riskier
计算逻辑: |
  1. 筛选最近30天的申请记录
  2. 按用户ID分组统计申请次数
依赖字段:
  - SK_ID_CURR (用户ID)
  - apply_date (申请日期)
产出类型: 数值型
```

### 衍生变量设计

```yaml
变量名: velocity_apply_ratio_30d_90d
主题: velocity
业务假设: 申请频率加速的用户风险更高
预期方向: higher_is_riskier
计算逻辑: |
  1. 计算近30天申请次数 (A)
  2. 计算近90天申请次数 (B)
  3. 计算比率: A / (B - A) * 30 / 60
依赖变量:
  - velocity_apply_count_30d
  - velocity_apply_count_90d
产出类型: 比率型 (0-1)
```

## 变量注册模板

在 `outputs/proposed_features/registry.json` 中记录：

```json
{
  "features": [
    {
      "name": "velocity_apply_count_30d",
      "theme": "velocity",
      "hypothesis": "短期高频申请的用户资金紧张，违约风险更高",
      "expected_direction": "higher_is_riskier",
      "calculation_logic": "统计最近30天的申请次数",
      "status": "proposed",
      "created_at": "2024-01-15T10:00:00"
    }
  ]
}
```

## 状态流转

```
proposed (已提出) → implemented (已实现) → validated (已验证) → selected (已入选)
                                              ↓
                                         rejected (已废弃)
```

### 状态定义

| 状态 | 含义 |
|------|------|
| proposed | 变量假设已提出，等待实现 |
| implemented | 代码已实现，等待验证 |
| validated | 已验证效果，有效或无效 |
| selected | 验证有效，已入选模型 |
| rejected | 验证无效或假设不成立 |

## 变量文档模板

每个主题建议创建一个变量说明文档：

```markdown
# Velocity 主题变量

## 主题概述
短期高频申请是重要的风险信号...

## 变量列表
| 变量名 | 业务含义 | 计算逻辑 | 状态 |
|--------|----------|----------|------|
| ... | ... | ... | ... |

## 验证结果
| 变量名 | ROC-AUC | Lift@10% | 结论 |
|--------|---------|----------|------|
| ... | ... | ... | ... |
```
