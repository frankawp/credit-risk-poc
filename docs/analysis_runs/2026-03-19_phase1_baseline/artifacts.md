# Artifacts

## 核心输出

- EDA 摘要：
  - [outputs/reports/eda_summary.md](/Users/frankliu/Code/credit-risk-poc/outputs/reports/eda_summary.md)
- 表规模概览：
  - [outputs/reports/table_overview.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/table_overview.csv)
- 客户记录密度：
  - [outputs/reports/customer_density.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/customer_density.csv)
- 特征元数据：
  - [outputs/reports/feature_metadata.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/feature_metadata.csv)
- 特征缺失率：
  - [outputs/reports/feature_missingness.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/feature_missingness.csv)
- 客户级特征宽表：
  - [data/processed/train_features.parquet](/Users/frankliu/Code/credit-risk-poc/data/processed/train_features.parquet)
- 模型摘要：
  - [outputs/reports/model_summary.md](/Users/frankliu/Code/credit-risk-poc/outputs/reports/model_summary.md)
- 模型详细指标：
  - [outputs/models/baseline_metrics.json](/Users/frankliu/Code/credit-risk-poc/outputs/models/baseline_metrics.json)
  - [outputs/models/baseline_metrics_all.json](/Users/frankliu/Code/credit-risk-poc/outputs/models/baseline_metrics_all.json)
  - [outputs/models/baseline_metrics_selected.json](/Users/frankliu/Code/credit-risk-poc/outputs/models/baseline_metrics_selected.json)
- 特征筛选摘要：
  - [outputs/reports/feature_selection_report.md](/Users/frankliu/Code/credit-risk-poc/outputs/reports/feature_selection_report.md)
- 特征评分卡：
  - [outputs/reports/feature_scorecard.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/feature_scorecard.csv)
- 相关组明细：
  - [outputs/reports/correlation_groups.csv](/Users/frankliu/Code/credit-risk-poc/outputs/reports/correlation_groups.csv)
- 筛选后特征宽表：
  - [data/processed/selected_features.parquet](/Users/frankliu/Code/credit-risk-poc/data/processed/selected_features.parquet)

## 代码入口

- 全流程入口：
  - [src/anti_fraud/pipelines/run_all.py](/Users/frankliu/Code/credit-risk-poc/src/anti_fraud/pipelines/run_all.py)
- EDA：
  - [src/anti_fraud/pipelines/run_eda.py](/Users/frankliu/Code/credit-risk-poc/src/anti_fraud/pipelines/run_eda.py)
- 特征构建：
  - [src/anti_fraud/pipelines/build_features.py](/Users/frankliu/Code/credit-risk-poc/src/anti_fraud/pipelines/build_features.py)
- 模型训练：
  - [src/anti_fraud/pipelines/train_models.py](/Users/frankliu/Code/credit-risk-poc/src/anti_fraud/pipelines/train_models.py)
