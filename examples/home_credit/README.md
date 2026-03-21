# Home Credit 案例示例

本示例展示如何使用 credit-risk 插件进行信贷变量挖掘。

## 数据准备

从 [Kaggle Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) 下载数据：

```bash
# 数据文件应放置在 data/raw/home-credit-default-risk/ 目录
data/raw/home-credit-default-risk/
├── application_train.csv
├── application_test.csv
├── previous_application.csv
├── bureau.csv
├── credit_card_balance.csv
└── installments_payments.csv
```

## 使用方法

### 1. 数据探索

```bash
python credit-risk-plugin/scripts/data_explorer.py data/raw/home-credit-default-risk/
```

### 2. 使用示例变量

```python
import pandas as pd
from examples.home_credit.features import (
    build_consistency_features,
    build_velocity_features,
    build_cashout_features,
)

# 加载数据
app = pd.read_csv("data/raw/home-credit-default-risk/application_train.csv")
previous = pd.read_csv("data/raw/home-credit-default-risk/previous_application.csv")
bureau = pd.read_csv("data/raw/home-credit-default-risk/bureau.csv")
credit_card = pd.read_csv("data/raw/home-credit-default-risk/credit_card_balance.csv")
installments = pd.read_csv("data/raw/home-credit-default-risk/installments_payments.csv")

# 构建特征
consistency_features = build_consistency_features(app, previous)
velocity_features = build_velocity_features(previous, bureau)
cashout_features = build_cashout_features(previous, credit_card, installments)

# 合并特征
features = consistency_features.merge(velocity_features, on="SK_ID_CURR", how="left")
features = features.merge(cashout_features, on="SK_ID_CURR", how="left")

# 保存
features.to_parquet("outputs/features.parquet", index=False)
```

### 3. 评估变量

```bash
python credit-risk-plugin/scripts/feature_evaluator.py outputs/features.parquet --target TARGET
```

## 变量主题

### 一致性主题 (consistency.py)

| 变量名 | 业务假设 | 预期方向 |
|--------|----------|----------|
| consistency_employed_birth_ratio | 工作年限占年龄比例越高，职业越稳定 | 越低风险越大 |
| consistency_contact_flag_sum | 联系方式越完整，用户越真实 | 越低风险越大 |
| consistency_prev_credit_gap_ratio_mean | 申请与获批金额差距越大，审批一致性越差 | 越高风险越大 |

### 高频申请主题 (velocity.py)

| 变量名 | 业务假设 | 预期方向 |
|--------|----------|----------|
| velocity_prev_count_7d | 近7天申请次数越多，资金越紧张 | 越高风险越大 |
| velocity_prev_count_30d | 近30天申请次数越多，多头借贷风险越高 | 越高风险越大 |
| velocity_bureau_recent_credit_count_30d | 近30天征信查询次数越多，风险越高 | 越高风险越大 |

### 套现倾向主题 (cashout.py)

| 变量名 | 业务假设 | 预期方向 |
|--------|----------|----------|
| cashout_atm_ratio_mean | ATM取现比例越高，套现倾向越强 | 越高风险越大 |
| cashout_fpd_severe_flag | 首期逾期超过30天是强风险信号 | 越高风险越大 |
| cashout_installments_late_ratio | 分期还款逾期比例越高，还款习惯越差 | 越高风险越大 |

## 自定义变量

参考现有示例，创建自己的变量实现：

```python
# my_features.py
import pandas as pd

def build_my_features(data_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    构建自定义特征。

    参数:
        data_frames: 表名到 DataFrame 的映射

    返回:
        DataFrame，索引为 SK_ID_CURR，列为自定义特征
    """
    # 实现你的变量计算逻辑
    pass
```

## 注意事项

- 此示例仅作演示，实际使用时需要根据业务场景调整
- 数据文件不包含在仓库中，需要自行下载
- 变量效果需要在实际数据上验证
