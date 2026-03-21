# 主题扩展指南

本文档说明如何创建新的变量挖掘主题。

## 扩展流程

### 1. 创建设计文档

在 `engine/semantic/themes/` 目录下创建 `{theme}.py` 文件。

**文件命名**：`{英文标识}.py`，例如 `fraud.py`

### 2. 实现主题类

继承 `ThemeBase` 基类：

```python
from ..base import ThemeBase, FeatureSpec

class FraudTheme(ThemeBase):
    @property
    def name(self) -> str:
        return "fraud"

    @property
    def description(self) -> str:
        return "识别欺诈申请、职业骗贷行为"

    def feature_specs(self) -> list[FeatureSpec]:
        return [
            FeatureSpec(
                name="fraud_field_std_score",
                theme="fraud",
                hypothesis="关键字段值的标准化程度异常",
                expected_direction="higher_is_riskier",
                calculation_logic="关键字段值的变异系数",
                source_tables=["application"],
            ),
        ]

    def build_features(
        self,
        frames: dict[str, pd.DataFrame],
        anchor: pd.DataFrame,
    ) -> pd.DataFrame:
        # 实现特征构建逻辑
        entity_id_col = "entity_id"
        result = anchor[[entity_id_col]].copy()
        # ... 构建特征
        return result
```

### 3. 注册主题

在 `engine/semantic/themes/__init__.py` 中添加导出：

```python
from .fraud import FraudTheme

__all__ = [
    # ...
    "FraudTheme",
]
```

主题会在导入时自动注册到 `ThemeRegistry`。

### 4. 创建设计文档（可选）

在 `references/themes/` 目录下创建 `{theme}_design.md` 文件，记录设计思路。

## 设计原则

### 业务假设驱动

每个变量都要回答：**这个变量为什么能识别风险？**

### 数据可验证

确保有数据支撑：
- 检查数据表是否有相关字段
- 确认字段值的有效性
- 评估覆盖率是否足够

### 方向明确

明确变量的风险方向：
- `higher_is_riskier`：值越高越坏
- `lower_is_riskier`：值越低越坏

### 优先级合理

- 高优先级：业务价值高、数据可用
- 中优先级：有价值但需验证
- 低优先级：数据依赖或不确定

## 注意事项

- 设计文档要具体，避免模糊描述
- 计算逻辑要明确，便于 AI 理解和实现
- 数据需求要核实，避免无法实现
- 使用 `validate_data_availability` 检查数据可用性
