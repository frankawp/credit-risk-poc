"""
Home Credit 数据集实体关系构建样例。

参考此脚本构建其他数据集的实体关系。
"""
import sys
from pathlib import Path

# 添加引擎路径（根据实际插件安装位置调整）
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "credit-risk-plugin"))

from engine.config import EntityConfig, EnginePaths
from engine.entity import EntitySetBuilder

# 定义实体关系
ENTITY_CONFIGS = [
    # 主实体：当前申请
    EntityConfig(
        name="applications",
        file_path="application_train.csv",
        index="SK_ID_CURR",
        parent=None,
        target="TARGET",
    ),
    # 征信记录
    EntityConfig(
        name="bureau",
        file_path="bureau.csv",
        index="SK_ID_BUREAU",
        parent="applications",
        foreign_key="SK_ID_CURR",
    ),
    # 历史申请
    EntityConfig(
        name="previous_applications",
        file_path="previous_application.csv",
        index="SK_ID_PREV",
        parent="applications",
        foreign_key="SK_ID_CURR",
    ),
    # 信用卡账单
    EntityConfig(
        name="credit_card_balance",
        file_path="credit_card_balance.csv",
        index="SK_ID_PREV",
        parent="previous_applications",
        foreign_key="SK_ID_PREV",
    ),
    # 分期还款
    EntityConfig(
        name="installments_payments",
        file_path="installments_payments.csv",
        index="SK_ID_PREV",
        parent="previous_applications",
        foreign_key="SK_ID_PREV",
    ),
]


def build_home_credit_entityset(
    data_dir: Path,
    sample_size: int | None = 3000,
):
    """构建 Home Credit 数据集的 EntitySet。

    参数：
        data_dir: 数据目录路径
        sample_size: 采样数量（None 表示全量）

    返回：
        (EntitySet, 表名到DataFrame的映射)
    """
    paths = EnginePaths(data_dir=data_dir)
    builder = EntitySetBuilder(paths=paths)
    builder.add_entities(ENTITY_CONFIGS)
    return builder.build(sample_size=sample_size)


if __name__ == "__main__":
    # 使用示例
    data_dir = Path("data/raw/home-credit-default-risk")
    es, frames = build_home_credit_entityset(data_dir)

    print(f"EntitySet: {es.id}")
    for name, df in frames.items():
        print(f"  {name}: {len(df)} 行, {len(df.columns)} 列")
