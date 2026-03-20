from __future__ import annotations

import pandas as pd
import streamlit as st

from app.data_loader import drop_reason_counts, scorecard_sorted, summarize_matrix


def render(artifacts: dict) -> None:
    st.header("步骤3 特征筛选")
    st.caption("作用：查看候选变量被怎么筛掉、最后保留了哪些，以及淘汰原因是什么。")

    summary = artifacts.get("selection_summary")
    scorecard = artifacts.get("feature_scorecard")
    correlation_groups = artifacts.get("correlation_groups")
    dropped_basic = artifacts.get("dropped_basic_filters")
    selected = artifacts.get("selected_features")

    if summary is None:
        st.info("该步骤产物尚未生成：缺少 `outputs/selection/feature_selection_report.json`。")
        return

    cards = st.columns(4)
    cards[0].metric("输入特征数", summary.get("input_feature_count", "-"))
    cards[1].metric("基础过滤后", summary.get("after_basic_filter_count", "-"))
    cards[2].metric("最终入选数", summary.get("selected_feature_count", "-"))
    cards[3].metric("baseline_target_rate", f"{summary.get('baseline_target_rate', 0):.4f}")

    st.subheader("筛选漏斗")
    funnel_df = pd.DataFrame(
        {
            "阶段": ["输入特征", "基础过滤后", "最终入选"],
            "特征数": [
                summary.get("input_feature_count", 0),
                summary.get("after_basic_filter_count", 0),
                summary.get("selected_feature_count", 0),
            ],
        }
    )
    st.bar_chart(funnel_df.set_index("阶段"))

    st.subheader("单变量评分表")
    if scorecard is None:
        st.info("缺少 `feature_scorecard.csv`。")
    else:
        only_selected = st.toggle("只看入选特征", value=False)
        only_dropped = st.toggle("只看淘汰特征", value=False)
        view = scorecard_sorted(scorecard)
        if only_selected and "selected_flag" in view.columns:
            view = view[view["selected_flag"]]
        if only_dropped and "selected_flag" in view.columns:
            view = view[~view["selected_flag"]]
        st.dataframe(view, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("去相关结果")
        if correlation_groups is None:
            st.info("缺少 `correlation_groups.csv`。")
        else:
            st.dataframe(correlation_groups, use_container_width=True, hide_index=True)

    with right:
        st.subheader("基础过滤淘汰原因")
        reason_counts = drop_reason_counts(dropped_basic)
        if reason_counts.empty:
            st.info("没有基础过滤淘汰结果，或文件不存在。")
        else:
            st.bar_chart(reason_counts.set_index("drop_reason"))
            st.dataframe(reason_counts, use_container_width=True, hide_index=True)

    st.subheader("最终入选特征预览")
    selected_summary = summarize_matrix(selected)
    if selected_summary is None:
        st.info("缺少 `selected_features.parquet`。")
    else:
        st.write({"rows": selected_summary["rows"], "cols": selected_summary["cols"]})
        st.code("\n".join(selected_summary["sample_columns"]), language="text")
        st.dataframe(selected.iloc[:20, : min(20, selected.shape[1])], use_container_width=True)

    st.subheader("筛选结论说明")
    st.markdown(
        "- `high_missing_rate` / `near_constant` / `highly_correlated_with_*` 表示在基础过滤阶段被淘汰。\n"
        "- `weak_univariate_signal` 表示通过基础过滤但单变量信号不足。\n"
        "- 最终入选的是当前样本口径下被保留的代表性特征。"
    )
