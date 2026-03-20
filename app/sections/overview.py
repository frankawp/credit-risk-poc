from __future__ import annotations

import pandas as pd
import streamlit as st

from app.data_loader import build_lineage_warning, group_counts, source_counts, summarize_matrix


def render(artifacts: dict) -> None:
    st.header("总览")
    st.caption("作用：先用一页看清整个双引擎流程当前产出了什么，以及每一步的规模。")

    candidate_summary = artifacts.get("candidate_summary") or {}
    selection_summary = artifacts.get("selection_summary") or {}
    registry = artifacts.get("feature_registry")

    row1 = st.columns(4)
    row1[0].metric("样本量", candidate_summary.get("sample_size", "-"))
    row1[1].metric("自动特征数", candidate_summary.get("auto_feature_count", "-"))
    row1[2].metric("语义特征数", candidate_summary.get("semantic_feature_count", "-"))
    row1[3].metric("组合特征数", candidate_summary.get("composite_feature_count", "-"))

    row2 = st.columns(4)
    row2[0].metric("候选池列数", (candidate_summary.get("candidate_pool_shape") or ["-", "-"])[1])
    row2[1].metric("输入特征数", selection_summary.get("input_feature_count", "-"))
    row2[2].metric("基础过滤后", selection_summary.get("after_basic_filter_count", "-"))
    row2[3].metric("最终入选数", selection_summary.get("selected_feature_count", "-"))

    warning = build_lineage_warning(artifacts)
    if warning:
        st.warning(warning)

    left, right = st.columns(2)
    with left:
        st.subheader("变量来源占比")
        source_df = source_counts(registry)
        if source_df.empty:
            st.info("变量来源信息尚未生成。")
        else:
            st.bar_chart(source_df.set_index("feature_source"))

    with right:
        st.subheader("变量分组占比")
        group_df = group_counts(registry)
        if group_df.empty:
            st.info("变量分组信息尚未生成。")
        else:
            st.bar_chart(group_df.set_index("feature_group"))

    st.subheader("关键产物概览")
    matrices = []
    for label, key in [
        ("候选池宽表", "candidate_pool"),
        ("自动特征矩阵", "auto_feature_matrix"),
        ("语义特征矩阵", "semantic_feature_matrix"),
        ("最终入选特征", "selected_features"),
    ]:
        summary = summarize_matrix(artifacts.get(key))
        if summary:
            matrices.append({"产物": label, "行数": summary["rows"], "列数": summary["cols"], "示例列": ", ".join(summary["sample_columns"][:6])})
    if matrices:
        st.dataframe(pd.DataFrame(matrices), use_container_width=True, hide_index=True)
    else:
        st.info("尚未检测到可展示的矩阵产物。")
