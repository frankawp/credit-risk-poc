"""
双引擎特征生成。

展示 Auto 和 Semantic 双引擎如何协同生成特征。

工作流：
1. Auto Engine - Featuretools 自动聚合/转换
2. Semantic Engine - 业务主题特征
3. 合并候选池
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mining.engine import AutoFeatureConfig
from mining.engine.auto import generate_auto_features, check_featuretools_available
from mining.engine.semantic import (
    generate_semantic_features,
    list_available_themes,
    get_theme_description,
)


# ============================================================================
# 前置检查
# ============================================================================

def check_environment():
    """检查特征生成环境是否就绪。"""
    result = check_featuretools_available()
    if not result:
        print("警告: Featuretools 未安装，自动特征引擎不可用")
        print("安装命令: pip install featuretools")
    return result


def _detect_anchor_frame(
    frames: dict[str, pd.DataFrame],
    target_entity: str,
) -> pd.DataFrame:
    """获取锚点表。"""
    if target_entity in frames:
        return frames[target_entity]
    if not frames:
        raise ValueError("frames 为空，无法生成候选特征")
    return next(iter(frames.values()))


# ============================================================================
# Auto Engine - 自动特征生成
# ============================================================================

def run_auto_features(
    entityset,
    output_dir: Path,
    target_entity: str = "applications",
) -> pd.DataFrame:
    """运行自动特征引擎。

    使用 Featuretools 的 DFS (Deep Feature Synthesis) 自动生成：
    - 聚合特征：COUNT, SUM, MEAN, MAX, MIN, STD
    - 转换特征：diff, rate, ratio
    - 时间窗口特征：最近 N 天的统计

    参数：
        entityset: 已构建的 EntitySet
        output_dir: 输出目录

    返回：
        自动特征矩阵
    """
    config = AutoFeatureConfig(
        max_depth=2,           # 聚合深度
        sample_size=10000,     # 采样大小
    )

    result = generate_auto_features(
        entityset=entityset,
        target_entity=target_entity,
        config=config,
        output_dir=output_dir / "auto",
    )

    print(f"自动特征数量: {len(result.feature_names)}")

    return result.feature_matrix


# ============================================================================
# Semantic Engine - 语义特征生成
# ============================================================================

def run_semantic_features(
    frames: dict[str, pd.DataFrame],
    anchor: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    """运行语义特征引擎。

    基于业务假设生成主题特征：
    - velocity: 申请速度类（短期内多次申请）
    - consistency: 信息一致性类（申请信息 vs 历史信息）
    - stability: 稳定性类（居住、工作稳定性）

    参数：
        frames: 原始数据表字典
        output_dir: 输出目录

    返回：
        语义特征矩阵
    """
    # 查看可用主题
    themes = list_available_themes()
    print(f"可用主题: {themes}")

    for theme in themes:
        desc = get_theme_description(theme)
        print(f"  - {theme}: {desc}")

    # 生成所有主题特征
    result = generate_semantic_features(
        frames=frames,
        anchor=anchor,
        output_dir=output_dir / "semantic",
        themes=None,  # None = 全部主题
    )

    semantic_features = [c for c in result.feature_matrix.columns if c not in anchor.columns]
    print(f"语义特征数量: {len(semantic_features)}")

    return result.feature_matrix


# ============================================================================
# 合并候选池
# ============================================================================

def merge_candidate_pools(
    auto_matrix: pd.DataFrame,
    semantic_matrix: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    """合并 Auto 和 Semantic 候选池。

    合并规则：
    1. 以 ID 列为锚点
    2. 保留 TARGET 列
    3. 特征列自动处理重名（添加后缀）

    参数：
        auto_matrix: 自动特征矩阵
        semantic_matrix: 语义特征矩阵
        output_dir: 输出目录

    返回：
        合并后的候选池
    """
    # 确保锚点一致
    id_col = "SK_ID_CURR"
    target_col = "TARGET"

    anchor = auto_matrix[[id_col, target_col]].copy()

    # 提取特征列
    auto_features = [c for c in auto_matrix.columns if c not in {id_col, target_col}]
    semantic_features = [c for c in semantic_matrix.columns if c not in {id_col, target_col}]

    # 合并
    merged = anchor.copy()
    merged = merged.merge(
        auto_matrix[[id_col] + auto_features],
        on=id_col,
        how="left",
    )
    merged = merged.merge(
        semantic_matrix[[id_col] + semantic_features],
        on=id_col,
        how="left",
    )

    # 保存
    merged.to_parquet(output_dir / "candidate_pool.parquet", index=False)

    # 汇总
    summary = {
        "auto_feature_count": len(auto_features),
        "semantic_feature_count": len(semantic_features),
        "total_feature_count": len(auto_features) + len(semantic_features),
        "row_count": len(merged),
    }

    import json
    (output_dir / "candidate_pool_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )

    print(f"候选池汇总:")
    print(f"  - Auto 特征: {summary['auto_feature_count']}")
    print(f"  - Semantic 特征: {summary['semantic_feature_count']}")
    print(f"  - 总计: {summary['total_feature_count']}")

    return merged


# ============================================================================
# 运行示例
# ============================================================================

def run_pipeline(
    entityset,
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    target_entity: str = "applications",
) -> pd.DataFrame:
    """运行完整的特征生成流水线。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    anchor = _detect_anchor_frame(frames, target_entity)

    # 1. 检查环境
    if not check_environment():
        print("跳过 Auto Engine，仅使用 Semantic Engine")
        auto_matrix = anchor.copy()
    else:
        # 2. Auto 特征
        auto_matrix = run_auto_features(entityset, output_dir, target_entity=target_entity)

    # 3. Semantic 特征
    semantic_matrix = run_semantic_features(frames, anchor, output_dir)

    # 4. 合并
    candidate_pool = merge_candidate_pools(auto_matrix, semantic_matrix, output_dir)

    return candidate_pool


if __name__ == "__main__":
    # 假设已有 entityset 和 frames
    # 直接参考 ../01_entity_layer/build_entityset.py 中的 build_entityset_quick 调用方式

    output_dir = Path("outputs/run_001/features")
    # run_pipeline(entityset, frames, output_dir)
