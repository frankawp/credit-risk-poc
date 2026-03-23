# 输出目录地图

## 核心产出：业务报告

**面向业务人员，呈现完整挖掘过程。**

```
outputs/
├── reports/                           # 报告目录（核心产出）
│   ├── 01_data_overview.md           # 数据概览报告
│   ├── 02_feature_design.md          # 变量设计报告
│   ├── 03_feature_evaluation.md      # 变量效果报告
│   ├── 04_stability_check.md         # 稳定性检查报告
│   ├── 05_selection_summary.md       # 筛选总结报告
│   └── mining_report.md              # 完整挖掘报告（合并版）
└── data/                             # 数据文件（辅助产物）
    ├── feature_matrix.parquet        # 特征矩阵
    └── feature_registry.csv          # 变量注册表
```

---

## 报告内容说明

### 01_data_overview.md

- 表结构概览（表名、字段数、记录数）
- 主键/外键识别结果
- 表间关系推断
- 数据质量摘要（缺失率、异常值）

### 02_feature_design.md

- 变量假设清单（名称、逻辑、假设、优先级）
- 变量计算口径（公式、数据来源、时间窗口）
- 业务含义说明（预期方向、风险解读）

### 03_feature_evaluation.md

- 单变量效果表（AUC、IV、缺失率、方向验证）
- 假设验证结论（成立/部分成立/不成立）
- 业务解读（有效变量、需调整变量、废弃变量）

### 04_stability_check.md

- PSI 分析结果（训练/测试、时间分片）
- 不稳定变量清单及处理建议
- 分组一致性检查

### 05_selection_summary.md

- 入选变量清单
- 筛选方法说明（阈值、标准、流程）
- 最终效果汇总

### mining_report.md

- 合并上述所有报告
- 完整挖掘过程记录
- 供业务人员阅读的主报告

---

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `data/feature_matrix.parquet` | 特征矩阵，用于后续建模 |
| `data/feature_registry.csv` | 变量注册表，记录所有变量元信息 |

---

## 口径提醒

- 报告中的样本量和数据文件可能不一致（报告基于抽样分析）
- 解释结果时必须显式提醒口径差异
