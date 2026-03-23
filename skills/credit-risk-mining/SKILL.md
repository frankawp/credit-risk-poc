---
name: credit-risk-mining
description: Use when the user wants end-to-end credit-risk feature mining on local tabular data: explore credit datasets, infer entities and relations, design semantic risk features, generate auto features, evaluate and select features, interpret existing mining outputs, or archive a mining run.
---

# Credit Risk Mining

全程使用中文。

## Scope

- 适用于本地多表信贷数据的变量挖掘、结果解读、迭代优化和归档。
- 目标是把业务问题落到 `数据探索 → 变量设计 → 特征生成 → 效果验证 → 迭代沉淀`。
- 当前工作区里的 skill 资产视为只读，分析产物写到工作区 `outputs/`。

## Workflow

1. 开始前先检查 `outputs/` 是否已有内容；如果有，提醒用户上一轮结果还在，归档只能在用户明确要求时触发。
2. 判断路线：
   - 用户已有明确业务假设，优先走语义特征挖掘。
   - 用户只有数据、没有明确假设，先做数据探索，再决定自动特征或混合路线。
3. 数据探索后，先确认主表、目标变量、主键/外键关系，再进入变量设计。
4. 变量设计必须记录变量名、业务假设、计算口径、预期方向；优先把核心结论写成 `outputs/reports/*.md`。
5. 特征生成时，优先复用现有 engine 和样例；只有在现有主题不够时再新增逻辑。
6. 效果验证至少覆盖单变量表现、稳定性或分片一致性，并把结论写回报告。
7. 用户明确要求“归档”或 `archive` 时，才调用归档脚本。

## Operating Rules

- 自动特征依赖 `featuretools`。如果环境里没有它，不要卡住流程，继续做语义特征和报告。
- 把 `examples/` 当作阶段模板，不要把编号目录写成 Python import 路径。
- 用 `scripts/feature_registry.py` 管理变量注册表，用 `scripts/archive_run.py` 归档当前 `outputs/`。
- 如需解释已有结果，先读 `references/outputs_map.md` 和对应报告，再回答，不要臆造。

## Read These On Demand

- 方法论总览：`references/methodology.md`
- 变量设计和主题扩展：`references/variable_design_guide.md`、`references/themes/themes.md`
- 筛选和稳定性：`references/selection_logic.md`
- 输出目录说明：`references/outputs_map.md`
- 阶段样例：`examples/home_credit/`

## Handy Entrypoints

- `scripts/feature_registry.py --help`
- `scripts/archive_run.py --help`
- `examples/home_credit/00_data_explorer/explore_data.py`
- `examples/home_credit/01_entity_layer/build_entityset.py`
- `examples/home_credit/02_feature_generation/dual_engine.py`
- `examples/home_credit/03_composite_features/build_composite.py`
- `examples/home_credit/04_feature_selection/run_selection.py`
