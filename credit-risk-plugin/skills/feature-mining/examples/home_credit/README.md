# Home Credit 案例示例

本示例展示完整的信贷变量挖掘流程。

## 目录结构

```
home_credit/
├── 00_data_explorer/           # 数据探索
│   └── explore_data.py         # 主键/外键检测、关系推断
├── 01_entity_layer/            # 实体层构建
│   └── build_entityset.py      # EntitySet 配置示例
├── 02_feature_generation/      # 特征生成
│   └── dual_engine.py          # Auto + Semantic 双引擎
├── 03_composite_features/      # 组合特征
│   └── build_composite.py      # 比率/交互/规则交叉
├── 04_feature_selection/       # 特征筛选
│   └── run_selection.py        # 完整筛选流水线
├── CAPABILITY_ANALYSIS.md      # 代码能力分析
└── README.md                   # 本文档
```

## 数据准备

从 [Kaggle Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) 下载数据：

```bash
data/raw/
├── application_train.csv
├── application_test.csv
├── previous_application.csv
├── bureau.csv
├── bureau_balance.csv
├── credit_card_balance.csv
├── installments_payments.csv
└── POS_CASH_balance.csv
```

## 流程说明

### 0. Data Exploration（数据探索）

理解数据结构，识别主键和外键：

```python
from pathlib import Path

# 导入探索模块
import sys
sys.path.insert(0, "$CLAUDE_SKILL_DIR/../../")

from examples.home_credit.00_data_explorer.explore_data import (
    explore_data_directory,
    print_exploration_report,
)

# 探索数据目录
report = explore_data_directory(
    data_dir=Path("data/raw"),
    sample_size=10000,
    output_dir=Path("outputs/exploration"),
)

# 打印报告
print_exploration_report(report)
```

输出：
- `exploration_report.json` - 完整探索报告
- `relationship_guide.md` - 关系配置建议

### 1. Entity Layer（实体层）

配置数据表之间的关系：

```python
from engine import EntityConfig, EnginePaths
from engine.entity import EntitySetBuilder

configs = [
    EntityConfig(
        name="applications",
        file_path="application_train.csv",
        index="SK_ID_CURR",
        parent=None,
    ),
    EntityConfig(
        name="previous_applications",
        file_path="previous_application.csv",
        index="SK_ID_PREV",
        parent="applications",
        foreign_key="SK_ID_CURR",
    ),
    # ... 更多实体
]

builder = EntitySetBuilder(paths=EnginePaths(data_dir="data/raw/"))
entityset, frames = builder.build(sample_size=10000)
```

### 2. Feature Generation（特征生成）

双引擎生成候选特征：

```python
from engine.auto import generate_auto_features
from engine.semantic import generate_semantic_features

# Auto 特征（Featuretools）
auto_result = generate_auto_features(entityset, target_entity="applications")

# Semantic 特征（业务主题）
semantic_result = generate_semantic_features(frames, anchor, themes=["velocity", "cashout"])
```

### 3. Composite Features（组合特征）

基于业务逻辑组合特征：

```python
from engine.composite import CompositeFeatureSpec, build_composite_features

specs = [
    CompositeFeatureSpec(
        feature_name="composite_credit_usage_ratio",
        formula="AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL",
        base_features="AMT_BALANCE, AMT_CREDIT_LIMIT_ACTUAL",
        business_definition="信用卡额度使用率",
        risk_direction="higher_is_riskier",
    ),
]

enhanced, specs_frame = build_composite_features(feature_matrix, specs)
```

### 4. Feature Selection（特征筛选）

完整筛选流水线：

```python
from engine.selection import run_feature_selection, run_stability_check
from engine import SelectionConfig

# 基础筛选 + 单变量评估
config = SelectionConfig(id_col="SK_ID_CURR", target_col="TARGET")
result = run_feature_selection(feature_matrix, config)

# 稳定性检查
stability_config = {"time_col": "MONTHS_BALANCE"}
report, summary = run_stability_check(feature_matrix, stability_config)
```

## 参考文档

- [代码能力分析](CAPABILITY_ANALYSIS.md)
- [筛选逻辑说明](../../references/selection_logic.md)
- [方法论概述](../../references/methodology.md)
