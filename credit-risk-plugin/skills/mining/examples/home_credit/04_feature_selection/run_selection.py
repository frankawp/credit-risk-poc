"""
特征筛选流水线。

展示完整的特征筛选流程：
1. Basic Filtering - 基础过滤（缺失/常量/相关性）
2. Supervised Selection - 有监督筛选（单变量评估）
3. Correlation Grouping - 相关性分组
4. Stability Check - 稳定性检查（PSI/时间分片）
5. Advanced Selection - 高级筛选（模型增益/重复检测）

输出：
- selected_features.parquet - 入选特征矩阵
- feature_scorecard.csv - 特征评分卡
- correlation_groups.csv - 相关性分组
- stability_report.md - 稳定性报告
- feature_selection_report.md - 筛选报告
"""

from pathlib import Path

import pandas as pd

from engine import SelectionConfig, EnginePaths
from engine.selection import (
    run_feature_selection,
    apply_basic_filters,
    evaluate_univariate,
    # 稳定性检查
    calculate_psi,
    check_time_stability,
    check_slice_consistency,
    run_stability_check,
    # 高级筛选
    detect_duplicates,
    detect_near_duplicates,
    evaluate_model_gain,
    evaluate_incremental_gain,
    run_advanced_selection,
)


# ============================================================================
# 配置筛选参数
# ============================================================================

def get_selection_config() -> SelectionConfig:
    """获取筛选配置。

    关键参数：
    - id_col: ID 列名
    - target_col: 目标列名
    - missing_rate_threshold: 缺失率阈值（超过则剔除）
    - correlation_threshold: 相关性阈值（超过则剔除）
    - min_auc: 最低 AUC 阈值
    - min_ap_lift: 最低 AP Lift 阈值
    - topk_ratio: Top-K 比例
    """
    return SelectionConfig(
        id_col="SK_ID_CURR",
        target_col="TARGET",
        missing_rate_threshold=0.95,     # 缺失率 > 95% 剔除
        correlation_threshold=0.95,      # 相关性 > 0.95 剔除
        min_auc=0.52,                    # ROC-AUC >= 0.52 入选
        min_ap_lift=1.02,                # PR-AUC >= baseline * 1.02 入选
        topk_ratio=0.10,                 # Top 10% 用于召回率计算
    )


# ============================================================================
# 完整筛选流程
# ============================================================================

def run_selection_pipeline(
    feature_matrix: pd.DataFrame,
    output_dir: Path,
    time_col: str | None = None,
    slice_col: str | None = None,
) -> dict:
    """运行完整筛选流程。

    参数：
        feature_matrix: 候选特征矩阵（包含 ID 和 TARGET）
        output_dir: 输出目录
        time_col: 时间列（用于稳定性检查）
        slice_col: 分组列（用于一致性检查）

    返回：
        筛选结果摘要
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    config = get_selection_config()

    # 执行基础筛选
    result = run_feature_selection(
        frame=feature_matrix,
        config=config,
        output_dir=output_dir,
    )

    # 打印汇总
    print("=" * 50)
    print("特征筛选报告")
    print("=" * 50)
    print(f"输入特征数: {result.summary['input_feature_count']}")
    print(f"基础过滤后: {result.summary['after_basic_filter_count']}")
    print(f"入选特征数: {result.summary['selected_feature_count']}")
    print(f"目标率基线: {result.summary['baseline_target_rate']:.4f}")
    print("=" * 50)

    # 按 IV 排序展示 Top 特征
    top_features = result.scorecard.nlargest(10, "iv")[
        ["feature_name", "univariate_roc_auc", "lift_top_decile", "iv", "selected_flag"]
    ]
    print("\nTop 10 特征（按 IV 排序）:")
    print(top_features.to_string(index=False))

    return result.summary


# ============================================================================
# 稳定性检查
# ============================================================================

def run_stability_pipeline(
    feature_matrix: pd.DataFrame,
    output_dir: Path,
    time_col: str | None = None,
    slice_col: str | None = None,
) -> dict:
    """运行稳定性检查流程。

    参数：
        feature_matrix: 特征矩阵
        output_dir: 输出目录
        time_col: 时间列名
        slice_col: 分组列名

    返回：
        稳定性检查结果
    """
    config = get_selection_config()
    stability_config = {
        "time_col": time_col,
        "slice_col": slice_col,
        "id_col": config.id_col,
        "target_col": config.target_col,
    }

    report, summary = run_stability_check(
        frame=feature_matrix,
        config=stability_config,
        output_dir=output_dir,
    )

    print("\n稳定性检查结果:")
    print(f"  稳定特征: {summary['stable_count']}")
    print(f"  中等变化: {summary['moderate_count']}")
    print(f"  显著变化: {summary['unstable_count']}")

    return summary


def step_psi_check(
    train_values: pd.Series,
    test_values: pd.Series,
    feature_name: str = "feature",
) -> dict:
    """计算单个特征的 PSI。

    PSI 解读：
    - PSI < 0.1: 稳定，无需关注
    - 0.1 <= PSI < 0.25: 中等变化，需关注
    - PSI >= 0.25: 显著变化，需处理
    """
    psi = calculate_psi(train_values.to_numpy(), test_values.to_numpy())

    if psi < 0.1:
        level = "stable"
    elif psi < 0.25:
        level = "moderate"
    else:
        level = "unstable"

    print(f"特征 {feature_name}: PSI = {psi:.4f} ({level})")
    return {"feature_name": feature_name, "psi": psi, "level": level}


def step_time_stability(
    feature_matrix: pd.DataFrame,
    time_col: str,
    output_dir: Path,
) -> pd.DataFrame:
    """时间分片稳定性检查。

    将数据按时间分片，计算各特征在不同时间片的 PSI。
    """
    config = get_selection_config()

    report = check_time_stability(
        frame=feature_matrix,
        time_col=time_col,
        id_col=config.id_col,
        target_col=config.target_col,
        n_splits=3,
        output_dir=output_dir,
    )

    # 打印不稳定特征
    unstable = report[report["stability_level"] == "unstable"]
    if len(unstable) > 0:
        print(f"\n不稳定特征 ({len(unstable)} 个):")
        for _, row in unstable.nlargest(5, "max_psi").iterrows():
            print(f"  - {row['feature_name']}: PSI = {row['max_psi']:.4f}")

    return report


def step_slice_consistency(
    feature_matrix: pd.DataFrame,
    slice_col: str,
    output_dir: Path,
) -> pd.DataFrame:
    """分组一致性检查。

    检查特征在不同分组间的分布一致性。
    """
    config = get_selection_config()

    report = check_slice_consistency(
        frame=feature_matrix,
        slice_col=slice_col,
        id_col=config.id_col,
        target_col=config.target_col,
        output_dir=output_dir,
    )

    return report


# ============================================================================
# 高级筛选
# ============================================================================

def run_advanced_pipeline(
    feature_matrix: pd.DataFrame,
    output_dir: Path,
) -> dict:
    """运行高级筛选流程。

    包含：
    - 重复特征检测
    - 模型增益评估
    """
    config = get_selection_config()

    results = run_advanced_selection(
        frame=feature_matrix,
        id_col=config.id_col,
        target_col=config.target_col,
        detect_duplicate=True,
        evaluate_gain=True,
        output_dir=output_dir,
    )

    print("\n高级筛选结果:")
    print(f"  重复特征对: {results['summary']['duplicate_pairs']}")
    print(f"  正增益特征: {results['summary']['features_with_positive_gain']}")

    return results


def step_duplicate_detection(
    feature_matrix: pd.DataFrame,
    threshold: float = 0.99,
) -> pd.DataFrame:
    """检测重复/近重复特征。

    参数：
        feature_matrix: 特征矩阵
        threshold: 相关性阈值

    返回：
        重复特征报告
    """
    config = get_selection_config()

    dup_report = detect_near_duplicates(
        frame=feature_matrix,
        id_col=config.id_col,
        target_col=config.target_col,
        threshold=threshold,
    )

    if len(dup_report) > 0:
        print(f"\n发现 {len(dup_report)} 对重复/近重复特征:")
        for _, row in dup_report.head(10).iterrows():
            print(f"  - {row['feature_a']} <-> {row['feature_b']}: r={row['correlation']:.4f}")
    else:
        print("\n未发现重复特征")

    return dup_report


def step_model_gain(
    feature_matrix: pd.DataFrame,
    base_features: list[str],
    candidate_features: list[str],
) -> pd.DataFrame:
    """评估特征对模型的增益。

    参数：
        feature_matrix: 特征矩阵
        base_features: 基线特征列表
        candidate_features: 待评估特征列表

    返回：
        模型增益报告
    """
    config = get_selection_config()

    gain_report = evaluate_model_gain(
        frame=feature_matrix,
        base_features=base_features,
        candidate_features=candidate_features,
        id_col=config.id_col,
        target_col=config.target_col,
    )

    if len(gain_report) > 0:
        print("\n特征增益 Top 10:")
        print(gain_report.head(10).to_string(index=False))

    return gain_report


def step_incremental_selection(
    feature_matrix: pd.DataFrame,
    feature_cols: list[str],
    output_dir: Path,
    min_gain: float = 0.0001,
) -> pd.DataFrame:
    """增量特征选择（前向选择）。

    从空集开始，逐步添加增益最大的特征。
    """
    config = get_selection_config()

    report = evaluate_incremental_gain(
        frame=feature_matrix,
        feature_cols=feature_cols,
        id_col=config.id_col,
        target_col=config.target_col,
        min_gain=min_gain,
        output_dir=output_dir,
    )

    return report


# ============================================================================
# 分步执行（用于调试）
# ============================================================================

def step1_basic_filter(feature_matrix: pd.DataFrame) -> tuple:
    """步骤 1：基础过滤。

    剔除：
    - high_missing_rate: 缺失率过高
    - near_constant: 近常量（唯一值 <= 1）
    - highly_correlated: 高度相关（被代表特征吸收）
    """
    config = get_selection_config()

    result = apply_basic_filters(
        frame=feature_matrix,
        id_col=config.id_col,
        target_col=config.target_col,
        missing_rate_threshold=config.missing_rate_threshold,
        correlation_threshold=config.correlation_threshold,
    )

    print(f"基础过滤:")
    print(f"  输入: {result.summary['input_count']} 特征")
    print(f"  输出: {result.summary['output_count']} 特征")
    print(f"  剔除原因:")
    for reason, count in result.summary["drop_reasons"].items():
        print(f"    - {reason}: {count}")

    return result.filtered, result.drop_report


def step2_univariate_evaluation(
    filtered_matrix: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    """步骤 2：单变量评估。

    计算指标：
    - univariate_roc_auc: ROC 曲线下面积
    - univariate_pr_auc: PR 曲线下面积
    - recall_at_topk: Top-K 召回率
    - lift_top_decile: Top 10% Lift 值
    - iv: Information Value 信息价值
    """
    config = get_selection_config()

    scorecard = evaluate_univariate(
        frame=filtered_matrix,
        id_col=config.id_col,
        target_col=config.target_col,
        topk_ratio=config.topk_ratio,
    )

    # 保存
    scorecard.to_csv(output_dir / "univariate_scorecard.csv", index=False)

    # IV 分布统计
    print("\nIV 分布:")
    print(f"  无预测能力 (IV < 0.02): {(scorecard['iv'] < 0.02).sum()}")
    print(f"  弱预测能力 (0.02-0.1): {((scorecard['iv'] >= 0.02) & (scorecard['iv'] < 0.1)).sum()}")
    print(f"  中等预测能力 (0.1-0.3): {((scorecard['iv'] >= 0.1) & (scorecard['iv'] < 0.3)).sum()}")
    print(f"  强预测能力 (IV >= 0.3): {(scorecard['iv'] >= 0.3).sum()}")

    return scorecard


def step3_mark_selected(
    filtered_matrix: pd.DataFrame,
    scorecard: pd.DataFrame,
) -> tuple:
    """步骤 3：标记入选特征。"""
    config = get_selection_config()
    baseline_ap = float(filtered_matrix[config.target_col].mean())

    # 标记
    scorecard["selected_flag"] = (
        (scorecard["univariate_roc_auc"] >= config.min_auc)
        | (scorecard["univariate_pr_auc"] >= baseline_ap * config.min_ap_lift)
    )
    scorecard["drop_reason"] = scorecard["selected_flag"].map(
        lambda f: "" if f else "weak_univariate_signal"
    )

    # 提取入选
    selected_features = scorecard.loc[scorecard["selected_flag"], "feature_name"].tolist()
    selected_matrix = filtered_matrix[[config.id_col, config.target_col] + selected_features].copy()

    print(f"\n入选特征: {len(selected_features)} / {len(scorecard)}")

    return selected_matrix, scorecard


# ============================================================================
# 运行示例
# ============================================================================

if __name__ == "__main__":
    # 假设已有候选特征矩阵
    # 直接参考 ../02_feature_generation/dual_engine.py 中的 run_pipeline 调用方式
    # feature_matrix = run_pipeline(...)

    output_dir = Path("outputs/run_001/selection")

    # 完整流程
    # summary = run_selection_pipeline(feature_matrix, output_dir)

    # 稳定性检查（需要时间列）
    # stability_summary = run_stability_pipeline(
    #     feature_matrix,
    #     output_dir / "stability",
    #     time_col="MONTHS_BALANCE",
    # )

    # 高级筛选
    # advanced_results = run_advanced_pipeline(feature_matrix, output_dir / "advanced")

    print("特征筛选完成")
