# 当前项目分析 Playbook

## 1. 当前项目的标准流程

截至目前，这个项目已经形成一条相对稳定的执行路径：

1. 准备原始数据
2. 运行 EDA
3. 构建客户级变量
4. 运行特征筛选与去相关
5. 训练全量与筛选后两套模型
6. 将结果归档到 docs

对应入口：

- EDA：`PYTHONPATH=src python3 -m anti_fraud.pipelines.run_eda`
- 特征构建：`PYTHONPATH=src python3 -m anti_fraud.pipelines.build_features`
- 特征筛选：`PYTHONPATH=src python3 -m anti_fraud.pipelines.select_features`
- 模型训练：`PYTHONPATH=src python3 -m anti_fraud.pipelines.train_models --feature-set all|selected`
- 全流程：`PYTHONPATH=src python3 -m anti_fraud.pipelines.run_all`

## 2. 当前项目的变量挖掘路径

本项目当前采用“三层推进”：

### 第一层：业务母题

- 信息不一致性
- 短期高频行为
- 套现与团伙特征

### 第二层：客户级聚合

把行为表统一聚合到 `SK_ID_CURR`，形成客户级宽表。

### 第三层：筛选和去相关

用 scorecard、相关组和模型对比，控制变量池质量。

## 3. 当前项目的判断标准

目前不是看“变量能不能算出来”，而是看三个维度：

1. 业务解释是否成立
2. 单变量是否有区分度
3. 放进模型后是否真的有增益

如果一个变量：

- 很难解释
- 命中极少
- 或者和已有变量高度重复

则默认不进入最终选中特征集。

## 4. 当前项目的文档归档规则

### 稳定知识放哪里

放在：

- `docs/data_knowledge/`
- `docs/methodology/`
- `docs/feature_catalog.md`

### 某一次分析放哪里

放在：

- `docs/analysis_runs/<date>_<run_name>/`

### 自动产物放哪里

放在：

- `outputs/reports/`
- `outputs/models/`
- `data/processed/`

## 5. 当前项目的下一步使用方式

如果后面要新增特征，建议按固定顺序做：

1. 先在 `docs/methodology/credit_customer_variable_mining_method.md` 里确认变量属于哪个主题
2. 再在 `docs/data_knowledge/table_reference.md` 里确认来源表和字段
3. 落地到代码后，在 `docs/feature_catalog.md` 补变量说明
4. 跑 `select_features`
5. 把结论记到新的 `analysis_runs` 子目录里

这样项目会越来越像方法体系，而不是一次性的 POC。
