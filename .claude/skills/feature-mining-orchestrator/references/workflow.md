# 双引擎变量挖掘流程

当前项目的标准流程分 6 步：

1. `auto features`
   - 基于 Featuretools 和 EntitySet 自动生成统计型、多表聚合型变量。
   - 价值：扩大候选面，快速找到有信号的基础变量。

2. `semantic features`
   - 基于业务语义生成反欺诈变量。
   - 当前已实现主题：`consistency / velocity / cashout`
   - 当前未实现但建议探索：`collusion`

3. `composite features`
   - 在 auto 和 semantic 之上做有约束的组合变量。
   - 只做有业务假设支撑的交叉，不做暴力全组合。

4. `candidate pool`
   - 合并 auto、semantic、composite，形成客户级候选变量池。
   - 关键产物：`outputs/candidate_pool/candidate_pool.parquet`

5. `feature selection`
   - 做基础过滤、单变量评估、去相关和入选导出。
   - 关键产物：`outputs/selection/feature_scorecard.csv`

6. `result navigation / archive`
   - 使用 viewer 或结果文件解释本轮结果。
   - 对完整任务自动归档到 `archives/analysis_run/YYYY-MM-DD_<topic>/`
   - 归档目录固定包含：
     - `project/`：整个挖掘项目
     - `conclusion/summary.md`
     - `conclusion/artifacts.json`
   - 归档时自动排除隐藏目录/文件（`.git`、`.claude`、`.venv` 等）
   - 归档完成后，工作区只保留 `data/`、`archives/` 和隐藏目录/文件

## 业务侧使用建议

- 如果用户还不知道从哪里下手：先做 semantic 方向确认。
- 如果用户要快速扩变量面：先跑 auto，再补 semantic。
- 如果用户只关心“为什么这个变量有效”：直接走筛选解释或结果导航，不必重跑流程。
