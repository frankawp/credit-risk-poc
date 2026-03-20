# Home Credit Default Risk 数据集总览

## 1. 数据集定位

本数据集来自 Kaggle `Home Credit Default Risk` 比赛，核心目标是预测借款人是否会出现还款困难。对于本项目，数据集被重解释为“信用风险 + 申请反欺诈”联合分析场景：

- `TARGET=1` 代表样本在贷款初期表现出明显违约风险
- 在 POC 中，这个标签被当作反欺诈挖掘的弱监督信号，而不是严格的“欺诈标签”

这意味着：

- 特征可以服务于识别高风险和疑似欺诈样本
- 但模型效果不应被直接解读为“真实欺诈识别率”

## 2. 当前已落地的原始文件

原始文件位于 [data/raw/home-credit-default-risk](/Users/frankliu/Code/credit-risk-poc/data/raw/home-credit-default-risk)。

本次项目实际使用和核对过的文件包括：

| 文件名 | 作用 | 行数级别 |
| --- | --- | --- |
| `application_train.csv` | 主申请表，含 `TARGET` 标签 | 307,511 |
| `application_test.csv` | 无标签测试表 | 48,744 |
| `previous_application.csv` | 历史申请记录 | 1,670,428 |
| `bureau.csv` | 外部征信记录 | 1,716,428 |
| `bureau_balance.csv` | 征信账户月度状态 | 27,299,925 |
| `credit_card_balance.csv` | 信用卡月度账务和取现行为 | 3,840,312 |
| `installments_payments.csv` | 分期还款记录 | 13,605,401 |
| `POS_CASH_balance.csv` | POS / cash loan 月度状态 | 10,001,358 |
| `HomeCredit_columns_description.csv` | 字段说明 | 220 |
| `sample_submission.csv` | 比赛提交样例 | 48,744 |

## 3. 主键和关联主线

数据分析主线以客户主键 `SK_ID_CURR` 为中心：

- `application_train.csv` / `application_test.csv`
  - 一行一个客户申请
- `previous_application.csv`
  - 一位客户对应多条历史申请
- `bureau.csv`
  - 一位客户对应多条征信记录
- `credit_card_balance.csv`
  - 一位客户对应多条信用卡月度记录
- `installments_payments.csv`
  - 一位客户对应多条还款记录

辅助主键包括：

- `SK_ID_PREV`
  - 历史申请或账户层级主键
- `SK_ID_BUREAU`
  - 征信记录主键

## 4. 适合反欺诈 POC 的原因

虽然数据集原始任务是信用违约预测，但它具备典型反欺诈研究需要的三类线索：

1. 申请身份与资料侧信息
   - 年龄、工龄、联系方式、证件标识
2. 申请频率与外部征信行为
   - 历史申请、短期征信查询、账户活跃度
3. 贷后套现与失联行为
   - ATM 取现、首期逾期、月度逾期状态

这使得它可以作为一个较好的反欺诈 POC 数据源，即使标签并非纯欺诈标签。

## 5. 本项目中的分析限制

- 数据是脱敏后的公开比赛数据，没有真实手机号、身份证号、设备号、IP、GPS 等强反欺诈主键
- 团伙特征只能通过“组织类型、区域、相似行为模式”做弱代理
- `TARGET` 不是纯欺诈标签，因此更适合用来验证变量的区分能力，而不是作为欺诈最终真值
- 部分时间字段是相对天数，不是绝对时间戳，因此短期窗口只能近似刻画

## 6. 对反欺诈建模的启示

- 应优先做可解释的客户级聚合特征
- 应把“身份不一致”“短期高频”“贷后异常行为”作为三条主线
- 应保留规则思路，而不是只做黑盒模型
- 应把模型结果解读为“高风险 / 可疑样本排序能力”
