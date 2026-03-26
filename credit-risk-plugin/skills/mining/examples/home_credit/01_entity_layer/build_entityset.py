"""
Home Credit 数据集 EntitySet 构建。

展示如何配置实体关系图，为后续特征生成做准备。

数据集结构：
- applications (主表)
  ├── previous_applications (历史申请)
  │   ├── credit_card_balance (信用卡流水)
  │   ├── installments_payments (分期还款)
  │   └── pos_cash_balance (POS 现金贷)
  └── bureau (征信记录)
      └── bureau_balance (征信流水)
"""

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mining.engine import EntityConfig, EnginePaths
from mining.engine.entity import EntitySetBuilder, build_entityset_from_config


# ============================================================================
# 方法一：使用 EntityConfig 列表配置
# ============================================================================

def get_entity_configs() -> list[EntityConfig]:
    """定义 Home Credit 数据集的实体配置。

    每个实体配置包含：
    - name: 实体名称
    - file_path: 数据文件路径（相对于 data_dir）
    - index: 主键列
    - parent: 父实体名称（None 表示主实体）
    - foreign_key: 外键列（连接父实体）
    - columns: 可选，指定加载的列
    """
    return [
        # 主实体 - 申请表
        EntityConfig(
            name="applications",
            file_path="application_train.csv",
            index="SK_ID_CURR",
            parent=None,
            foreign_key=None,
            columns=[
                "SK_ID_CURR",
                "TARGET",
                "AMT_INCOME_TOTAL",
                "AMT_CREDIT",
                "AMT_ANNUITY",
                "AMT_GOODS_PRICE",
                "DAYS_BIRTH",
                "DAYS_EMPLOYED",
                "EXT_SOURCE_1",
                "EXT_SOURCE_2",
                "EXT_SOURCE_3",
            ],
        ),
        # 子实体 - 历史申请
        EntityConfig(
            name="previous_applications",
            file_path="previous_application.csv",
            index="SK_ID_PREV",
            parent="applications",
            foreign_key="SK_ID_CURR",
            columns=[
                "SK_ID_PREV",
                "SK_ID_CURR",
                "AMT_APPLICATION",
                "AMT_CREDIT",
                "AMT_DOWN_PAYMENT",
                "NAME_CONTRACT_STATUS",
                "DAYS_DECISION",
            ],
        ),
        # 子实体 - 征信记录
        EntityConfig(
            name="bureau",
            file_path="bureau.csv",
            index="SK_ID_BUREAU",
            parent="applications",
            foreign_key="SK_ID_CURR",
            columns=[
                "SK_ID_BUREAU",
                "SK_ID_CURR",
                "CREDIT_ACTIVE",
                "DAYS_CREDIT",
                "AMT_CREDIT_SUM",
                "AMT_CREDIT_SUM_DEBT",
            ],
        ),
        # 孙实体 - 信用卡流水
        EntityConfig(
            name="credit_card_balance",
            file_path="credit_card_balance.csv",
            index="credit_card_id",  # 需要自动生成
            parent="previous_applications",
            foreign_key="SK_ID_PREV",
            columns=[
                "SK_ID_PREV",
                "MONTHS_BALANCE",
                "AMT_BALANCE",
                "AMT_CREDIT_LIMIT_ACTUAL",
                "AMT_DRAWINGS_CURRENT",
            ],
        ),
        # 孙实体 - 分期还款
        EntityConfig(
            name="installments_payments",
            file_path="installments_payments.csv",
            index="installment_id",  # 需要自动生成
            parent="previous_applications",
            foreign_key="SK_ID_PREV",
            columns=[
                "SK_ID_PREV",
                "NUM_INSTALMENT_NUMBER",
                "DAYS_INSTALMENT",
                "DAYS_ENTRY_PAYMENT",
                "AMT_INSTALMENT",
                "AMT_PAYMENT",
            ],
        ),
        # 孙实体 - 征信流水
        EntityConfig(
            name="bureau_balance",
            file_path="bureau_balance.csv",
            index="bureau_balance_id",  # 需要自动生成
            parent="bureau",
            foreign_key="SK_ID_BUREAU",
            columns=["SK_ID_BUREAU", "MONTHS_BALANCE", "STATUS"],
        ),
    ]


def build_entityset_quick() -> tuple:
    """快速构建：使用配置列表。

    适用于：配置已知，快速构建。
    """
    configs = get_entity_configs()
    paths = EnginePaths(data_dir="data/raw")

    entityset, frames = build_entityset_from_config(
        entity_configs=configs,
        paths=paths,
        sample_size=10000,  # 采样 1 万条
    )

    return entityset, frames


# ============================================================================
# 方法二：使用 Builder 流式构建
# ============================================================================

def build_entityset_fluent() -> tuple:
    """流式构建：逐步添加实体。

    适用于：需要动态调整配置的场景。
    """
    builder = EntitySetBuilder(
        name="home_credit",
        paths=EnginePaths(data_dir="data/raw"),
    )

    # 添加主实体
    builder.add_entity(EntityConfig(
        name="applications",
        file_path="application_train.csv",
        index="SK_ID_CURR",
        parent=None,
        foreign_key=None,
    ))

    # 添加子实体
    builder.add_entities([
        EntityConfig(
            name="previous_applications",
            file_path="previous_application.csv",
            index="SK_ID_PREV",
            parent="applications",
            foreign_key="SK_ID_CURR",
        ),
        EntityConfig(
            name="bureau",
            file_path="bureau.csv",
            index="SK_ID_BUREAU",
            parent="applications",
            foreign_key="SK_ID_CURR",
        ),
    ])

    # 构建
    return builder.build(sample_size=10000)


# ============================================================================
# 验证实体关系
# ============================================================================

def verify_entityset(entityset) -> dict:
    """验证 EntitySet 结构。"""
    return {
        "entities": list(entityset.dataframe_dict.keys()),
        "relationships": [
            f"{r.parent_dataframe_name}.{r.parent_column_name} -> {r.child_dataframe_name}.{r.child_column_name}"
            for r in entityset.relationships
        ],
        "row_counts": {
            name: len(df)
            for name, df in entityset.dataframe_dict.items()
        },
    }


# ============================================================================
# 运行示例
# ============================================================================

if __name__ == "__main__":
    # 构建实体集
    entityset, frames = build_entityset_quick()

    # 验证
    info = verify_entityset(entityset)
    print("实体列表:", info["entities"])
    print("关系数量:", len(info["relationships"]))
    print("各表行数:", info["row_counts"])

    # 后续使用
    # entityset 传递给特征生成器
