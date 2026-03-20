# Key Decisions

## 本次决定

1. 以 `SK_ID_CURR` 作为第一阶段统一聚合主键。
2. 第一阶段只纳入 5 张核心表，不把 `bureau_balance` 和 `POS_CASH_balance` 放进主流程。
3. 大表统一采用分块读取和聚合，避免全表入内存。
4. 第一阶段先做客户级宽表，不做事件级特征存储。
5. 基线模型优先用 `XGBoost`，`Isolation Forest` 作为异常检测对照。
6. Notebook 目前按 `PYTHONPATH=src` 方式运行，不依赖本机已安装 editable package。
7. 新增正式的特征筛选与去相关阶段，避免“全量特征直接训练”成为长期默认做法。
8. 将分析过程、变量手册和方法论分层固化到 `docs/`，把 POC 结果转成可复用的方法体系。

## 这些决定背后的原因

- 第一阶段目标是验证方向，不是追求最全覆盖
- `bureau_balance` 与 `POS_CASH_balance` 会显著增加复杂度和计算成本
- 在缺少设备、手机号、证件号等强标识的前提下，客户级聚合更适合现阶段
- 当前环境里 `xgboost` 可直接使用，`lightgbm` 未安装
