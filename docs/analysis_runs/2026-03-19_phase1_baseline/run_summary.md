# 2026-03-19 Phase 1 Baseline Run

## 1. 本次目标

完成第一阶段反欺诈 POC 的最小闭环：

- 停止 Docker 容器释放内存
- 对 Home Credit 原始数据做 EDA
- 产出客户级反欺诈特征宽表
- 训练基线模型验证特征效果

## 2. 输入数据

原始数据目录：

- [data/raw/home-credit-default-risk](/Users/frankliu/Code/credit-risk-poc/data/raw/home-credit-default-risk)

本次主要使用的表：

- `application_train.csv`
- `previous_application.csv`
- `bureau.csv`
- `credit_card_balance.csv`
- `installments_payments.csv`

## 3. 方法概述

### EDA

覆盖了：

- 表规模和主键关系
- 主表标签分布
- 主表缺失率 Top 列
- 明细表的客户级记录密度

### 特征工程

按三条主线构造客户级特征：

1. 信息不一致性
   - 工龄/年龄逻辑
   - 联系方式覆盖与错配
   - 证件缺失组合
   - 历史申请状态变化率
2. 短期高频行为
   - 历史申请最小间隔和标准差
   - 近 7 天 / 30 天申请数
   - 同日 burst 申请
   - 征信短期查询强度
3. 套现与团伙特征
   - ATM 取现占比
   - 历史逾期比例
   - 首期违约
   - 组织类型与区域组合风险

### 模型

训练了三组结果：

- baseline XGBoost
- anti-fraud XGBoost
- anti-fraud Isolation Forest

## 4. 关键结果

主结果如下：

- Baseline XGBoost ROC-AUC: `0.5968`
- Anti-Fraud XGBoost ROC-AUC: `0.6825`
- Baseline Recall@TopK: `0.0759`
- Anti-Fraud Recall@TopK: `0.1488`
- Isolation Forest ROC-AUC: `0.5036`

结论：

- 第一阶段构造的反欺诈特征对监督模型有明显增益
- 无监督 `Isolation Forest` 在当前标签体系下效果较弱
- 当前最有效的变量集中在群体风险、征信近期活跃度和贷后逾期行为

## 5. 业务解释

从本次结果看，最有价值的信号不是单一“身份伪造字段”，而是三类信号叠加：

- 群体风险画像
- 近期征信 / 借贷活跃度
- 贷后早期恶化行为

这与反欺诈实务一致：单点静态字段常常不足以识别欺诈，组合行为信号更稳定。
