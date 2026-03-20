---
name: feature-mining-orchestrator
description: 当用户想用自然语言完成信贷客户变量挖掘、反欺诈特征设计、候选池构建、特征筛选、结果解读或过程归档时使用。适合编排 auto features、semantic features、composite features、candidate pool、selection 和 outputs 导航。
---

# 信贷变量挖掘总控

全程使用中文。

## 什么时候用

- 用户要发起一轮新的变量挖掘任务
- 用户希望 AI 帮他从业务问题落到变量生成与筛选
- 用户要把现有产物串起来解释，而不是只看单个文件
- 用户希望完整沉淀一次分析过程

## 工作流

1. 先识别任务类型：新挖掘、结果解释、筛选优化、产物导航。
2. 对新挖掘任务，先确认主题和目标；未给方向时，引导在 `consistency / velocity / cashout / collusion` 中选择。
3. 只在需要时执行脚本；解释类任务优先复用已有产物，不重复跑流程。
4. 每轮交付都按固定模板输出：`结论摘要 / 关键产物 / 业务解释 / 口径提醒 / 下一步建议`。
5. 对完整挖掘任务，最后运行 `scripts/archive_run.py` 自动归档。

## 先读哪些参考材料

- 新一轮挖掘：读 `references/workflow.md`，再按主题读 `references/themes.md` 和 `references/implemented_features.md`
- 特征筛选解释：读 `references/selection_logic.md`
- 产物导航和 viewer 解读：读 `references/outputs_map.md`

## 执行约定

- 不在回复里手写长命令，执行时使用 `scripts/` 下的脚本。
- 运行 semantic 特征前，先确认主题；`collusion` 当前只支持探索，不支持直接计算。
- 如果 `outputs` 中存在抽样/全量口径不一致，必须显式提醒用户。
- 不要把尚未实现的变量说成已经产出。

## 可调用脚本

- `scripts/run_auto_features.py`
- `scripts/run_semantic_features.py`
- `scripts/run_composite_features.py`
- `scripts/build_candidate_pool.py`
- `scripts/select_features.py`
- `scripts/archive_run.py`

## 标准交付模板

1. `结论摘要`：这轮做了什么、最重要发现是什么
2. `关键产物`：文件路径和建议先看哪个
3. `业务解释`：重点变量或重点筛选结论
4. `口径提醒`：抽样、全量、缺失上游产物等
5. `下一步建议`：下一轮该扩什么主题或是否要重跑
