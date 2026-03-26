# Home Credit 示例

这个目录展示一套可复制的信贷变量挖掘流程，用来说明如何使用 `skills/mining/engine/` 这套专用挖掘代码。

## 重要说明

- `00_` 到 `04_` 是阶段目录，不是稳定的 Python 包路径。
- 不要写 `from examples.home_credit.00_data_explorer ...` 这类 import。
- 正确用法是直接阅读对应脚本，复制其中的调用方式，或者把脚本作为阶段模板改成本地数据版本。

## 阶段目录

```text
home_credit/
├── 00_data_explorer/           # 主键/外键检测、关系推断
├── 01_entity_layer/            # EntitySet 配置和构建
├── 02_feature_generation/      # Auto + Semantic 双引擎
├── 03_composite_features/      # 组合特征
├── 04_feature_selection/       # 特征筛选与稳定性检查
└── CAPABILITY_ANALYSIS.md      # 能力总览
```

## 推荐阅读顺序

1. `00_data_explorer/explore_data.py`
   用 `explore_data_directory(...)` 先理解表结构、主键候选和关系推断。
2. `01_entity_layer/build_entityset.py`
   用 `EntityConfig` 明确主表、子表、孙表关系，再构建 `EntitySet`。
3. `02_feature_generation/dual_engine.py`
   用 `run_pipeline(entityset, frames, output_dir, target_entity="applications")` 生成候选特征。
4. `03_composite_features/build_composite.py`
   用 `build_composite_features(...)` 组合基础特征。注意返回值是 `(enhanced_matrix, specs_frame)`。
5. `04_feature_selection/run_selection.py`
   用 `run_feature_selection(...)` 和稳定性检查函数筛掉弱信号与不稳定特征。

## 关键调用形状

```python
from mining.engine.auto import generate_auto_features
from mining.engine.semantic import generate_semantic_features
from mining.engine.selection import run_feature_selection
from mining.engine.composite import build_composite_features

auto_result = generate_auto_features(
    entityset=entityset,
    target_entity="applications",
)

semantic_result = generate_semantic_features(
    frames=frames,
    anchor=frames["applications"],
    themes=["velocity", "cashout"],
)

enhanced_matrix, specs_frame = build_composite_features(feature_matrix, specs)
selection_result = run_feature_selection(feature_matrix, config)
```

## 参考文档

- [代码能力分析](./CAPABILITY_ANALYSIS.md)
- [筛选逻辑说明](../../references/selection_logic.md)
- [方法论概述](../../references/methodology.md)
