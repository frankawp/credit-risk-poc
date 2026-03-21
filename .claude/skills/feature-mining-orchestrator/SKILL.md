---
name: feature-mining-orchestrator
description: 当用户想发起一轮信贷变量挖掘、从业务问题落到变量生成与筛选、串联解释现有产物，或归档分析过程时使用。
allowed-tools: Read, Bash, Glob, Grep
---

# 信贷变量挖掘总控

全程使用中文。

## 环境准备（首次使用或迁移到新项目时执行）

在执行任何脚本前，先检查虚拟环境是否存在：

```bash
ls .venv/bin/python 2>/dev/null || echo "需要创建虚拟环境"
```

如果不存在，执行以下步骤创建并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r .claude/skills/feature-mining-orchestrator/requirements.txt
```

这会通过 git URL 安装 `credit-risk-poc` 包（含 `dual_engine` 及其所有依赖），无需手动拷贝源码。

## 任务分支

根据用户意图，走不同分支：

### A. 新一轮挖掘

1. 先确认主题和目标；未给方向时，引导在 `consistency / velocity / cashout / collusion` 中选择。
2. 读 `references/workflow.md`，再按主题读 `references/themes.md` 和 `references/implemented_features.md`。
3. 按工作流依次执行脚本，每步交付都按标准模板输出。
4. 完成后运行 `archive_run.py` 自动归档。

### B. 语义变量探索

- 用户想围绕 consistency / velocity / cashout / collusion 设计变量、扩展思路。
- 先读 `references/themes.md`，需要判断已实现状态时再读 `references/implemented_features.md`。
- 输出时分三类：`已实现变量` / `候选变量` / `尚未实现但建议尝试`。
- 不要把 `collusion` 说成当前已经能计算。
- 如果用户要执行已实现主题，直接走脚本流程。

### C. 结果导航与产物解读

- 用户问"这个结果怎么看"、"某个特征是什么意思"。
- 读 `references/outputs_map.md`，如需解释特征再读 `references/implemented_features.md`。
- 对组合特征，优先读取 `outputs/candidate_pool/registry/feature_registry.csv` 和 `composite_feature_spec.csv`。
- 先说明产物在流程中的位置，再解释内容。
- 对组合特征必须说明：公式、基础变量、业务含义。

### D. 特征筛选解释

- 用户问"为什么这个特征被删了"、"为什么保留这个代表特征"。
- 读 `references/selection_logic.md`，必要时再读 `outputs/selection/` 下的产物文件。
- 解释必须基于现有产物，不要发明不存在的 drop reason。
- 对高相关变量，优先说明"被哪个代表特征吸收"。

## 工作流

1. 先识别任务类型：新挖掘、结果解释、筛选优化、产物导航、语义探索。
2. 只在需要时执行脚本；解释类任务优先复用已有产物，不重复跑流程。
3. 每轮交付都按固定模板输出：`结论摘要 / 关键产物 / 业务解释 / 口径提醒 / 下一步建议`。
4. 对完整挖掘任务，最后运行 `archive_run.py` 自动归档到 `archives/analysis_run/{date}_{topic}/`。

## 可调用脚本

用 Bash 执行，路径相对于项目根目录：

```bash
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/run_auto_features.py
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/run_semantic_features.py
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/run_composite_features.py
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/build_candidate_pool.py
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/select_features.py
.venv/bin/python .claude/skills/feature-mining-orchestrator/scripts/archive_run.py
```

## 标准交付模板

1. `结论摘要`：这轮做了什么、最重要发现是什么
2. `关键产物`：文件路径和建议先看哪个
3. `业务解释`：重点变量或重点筛选结论
4. `口径提醒`：抽样、全量、缺失上游产物等
5. `下一步建议`：下一轮该扩什么主题或是否要重跑

## 执行约定

- 不在回复里手写长命令，执行时使用 `.claude/skills/feature-mining-orchestrator/scripts/` 下的脚本。
- 运行 semantic 特征前，先确认主题；`collusion` 当前只支持探索，不支持直接计算。
- 如果 `outputs` 中存在抽样/全量口径不一致，必须显式提醒用户。
- 不要把尚未实现的变量说成已经产出。
- 不要直接承诺模型收益，只说明业务假设和可验证方向。
