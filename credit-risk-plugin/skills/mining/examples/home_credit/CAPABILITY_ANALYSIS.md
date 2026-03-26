# 代码能力分析报告

对比工作流程与现有 `skills/mining/engine` 和 `scripts` 代码能力。

## 工作流程 vs 现有能力

```
Raw Tables
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 0. Data Exploration (数据探索)                              │
├─────────────────────────────────────────────────────────────┤
│ 案例代码:                                                    │
│   ✅ examples/home_credit/00_data_explorer/explore_data.py  │
│     - detect_primary_key(): 主键检测                        │
│     - detect_foreign_keys(): 外键检测                       │
│     - analyze_table_relationships(): 关系推断               │
│     - analyze_column_quality(): 列质量分析                  │
│     - explore_data_directory(): 完整探索流程                │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Entity Layer (EntitySet / Join Graph / Key Mapping)      │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/entity/builder.py                 │
│     - EntitySetBuilder 类                                   │
│     - build_entityset_from_config()                         │
│   ✅ skills/mining/engine/config.py                         │
│     - EntityConfig 数据类                                   │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Auto Feature Engine (Featuretools)                       │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/auto/generator.py                 │
│     - generate_auto_features()                              │
│     - check_featuretools_available()                        │
│   ✅ skills/mining/engine/config.py                         │
│     - AutoFeatureConfig                                     │
│                                                             │
│ 状态: 完整（依赖 Featuretools）                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Semantic Feature Engine (Business Rules)                 │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/semantic/generator.py             │
│     - generate_semantic_features()                          │
│     - list_available_themes()                               │
│     - get_theme_description()                               │
│   ✅ skills/mining/engine/semantic/registry.py              │
│     - ThemeRegistry 类                                      │
│   ✅ skills/mining/engine/semantic/base.py                  │
│     - ThemeBase 抽象类                                      │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Composite Feature Builder (Ratios / Interactions)        │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/composite/builder.py              │
│     - build_composite_features()                            │
│     - create_cross_feature()                                │
│     - create_flag_feature()                                 │
│   ✅ CompositeFeatureSpec 数据类                            │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Basic Filtering (Null / Constant / Coverage / Duplicates)│
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/selection/basic_filters.py        │
│     - apply_basic_filters()                                 │
│     - FilterResult 数据类                                   │
│   ✅ skills/mining/engine/selection/advanced.py             │
│     - detect_duplicates()                                   │
│     - detect_near_duplicates()                              │
│                                                             │
│ 支持的过滤类型:                                              │
│   ✅ high_missing_rate (缺失率过高)                          │
│   ✅ near_constant (近常量)                                  │
│   ✅ highly_correlated (高度相关)                            │
│   ✅ duplicate_features (重复特征检测)                       │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Supervised Selection (Univariate / Model Gain)           │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/selection/univariate.py           │
│     - evaluate_univariate()                                 │
│     - 支持指标: ROC-AUC, PR-AUC, Recall@TopK, Lift, IV      │
│   ✅ skills/mining/engine/selection/advanced.py             │
│     - evaluate_model_gain()                                 │
│     - evaluate_incremental_gain()                           │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Correlation Grouping (Representative Retention)          │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ 在 basic_filters.py 中实现                             │
│     - 高相关特征被剔除并记录代表特征                         │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Stability Check (PSI / Slice Consistency)                │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ skills/mining/engine/selection/stability.py            │
│     - calculate_psi()                                       │
│     - check_feature_stability()                             │
│     - check_time_stability()                                │
│     - check_slice_consistency()                             │
│     - run_stability_check()                                 │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Registry & Archive                                       │
├─────────────────────────────────────────────────────────────┤
│ 现有能力:                                                    │
│   ✅ scripts/feature_registry.py                            │
│     - 变量注册管理 CLI                                      │
│   ✅ scripts/archive_run.py                                 │
│     - 归档工具 CLI                                          │
│                                                             │
│ 状态: 完整                                                  │
└─────────────────────────────────────────────────────────────┘
```

## 汇总表

| 流程阶段 | 模块 | 状态 | 说明 |
|---------|------|------|------|
| Data Exploration | examples/.../00_data_explorer | ✅ 完整 | 主键/外键检测、关系推断 |
| Entity Layer | skills/mining/engine/entity | ✅ 完整 | |
| Auto Features | skills/mining/engine/auto | ✅ 完整 | 依赖 Featuretools |
| Semantic Features | skills/mining/engine/semantic | ✅ 完整 | |
| Composite Features | skills/mining/engine/composite | ✅ 完整 | |
| Basic Filtering | skills/mining/engine/selection/basic_filters | ✅ 完整 | |
| Supervised Selection | skills/mining/engine/selection/univariate | ✅ 完整 | |
| Advanced Selection | skills/mining/engine/selection/advanced | ✅ 完整 | 模型增益/重复检测 |
| Correlation Grouping | skills/mining/engine/selection/basic_filters | ✅ 完整 | |
| Stability Check | skills/mining/engine/selection/stability | ✅ 完整 | PSI/时间分片/分组一致性 |
| Registry & Archive | scripts/ | ✅ 完整 | |

## 目录结构

```
examples/home_credit/
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
├── CAPABILITY_ANALYSIS.md      # 本文档
└── README.md                   # 说明文档
```

## 核心函数说明

### 00_data_explorer/explore_data.py

数据探索核心函数：

```python
# 主键检测
pks = detect_primary_key(df)

# 外键检测
fks = detect_foreign_keys(child_df, parent_df, parent_pk)

# 关系分析
relationships = analyze_table_relationships(tables)

# 完整探索流程
report = explore_data_directory(
    data_dir=Path("data/raw"),
    sample_size=10000,
    output_dir=Path("outputs/exploration"),
)
```

### skills/mining/engine/selection/stability.py

稳定性检查模块：

```python
# PSI 计算
psi = calculate_psi(train_values, test_values, n_bins=10)

# 时间分片稳定性
report = check_time_stability(frame, time_col="MONTHS_BALANCE")

# 分组一致性
report = check_slice_consistency(frame, slice_col="CHANNEL_TYPE")
```

### skills/mining/engine/selection/advanced.py

高级筛选模块：

```python
# 重复特征检测
duplicates = detect_near_duplicates(frame, id_col, target_col, threshold=0.99)

# 模型增益评估
gain_report = evaluate_model_gain(frame, base_features, candidates, id_col, target_col)

# 增量特征选择
report = evaluate_incremental_gain(frame, feature_cols, id_col, target_col)
```

## 结论

所有工作流程阶段现已具备完整的代码支撑能力。
