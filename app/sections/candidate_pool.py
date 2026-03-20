from __future__ import annotations

import pandas as pd
import streamlit as st

from app.data_loader import source_counts, summarize_matrix


def _preview(frame, rows: int = 20, cols: int = 20):
    if frame is None:
        return None
    return frame.iloc[:rows, : min(cols, frame.shape[1])]


def render(artifacts: dict) -> None:
    st.header("步骤1 候选池")
    st.caption("作用：查看这一轮生成了多少候选变量、来自哪里，以及候选池本身长什么样。")

    summary = artifacts.get("candidate_summary")
    registry = artifacts.get("feature_registry")
    candidate_pool = artifacts.get("candidate_pool")
    auto_matrix = artifacts.get("auto_feature_matrix")
    semantic_matrix = artifacts.get("semantic_feature_matrix")

    if summary is None:
        st.info("该步骤产物尚未生成：缺少 `outputs/candidate_pool/candidate_pool_summary.json`。")
        return

    cards = st.columns(6)
    cards[0].metric("sample_size", summary.get("sample_size", "-"))
    cards[1].metric("max_depth", summary.get("max_depth", "-"))
    cards[2].metric("auto", summary.get("auto_feature_count", "-"))
    cards[3].metric("semantic", summary.get("semantic_feature_count", "-"))
    cards[4].metric("composite", summary.get("composite_feature_count", "-"))
    shape = summary.get("candidate_pool_shape", ["-", "-"])
    cards[5].metric("候选池形状", f"{shape[0]} x {shape[1]}")

    st.subheader("来源拆分")
    counts = source_counts(registry)
    if counts.empty:
        st.info("缺少注册表，无法展示来源拆分。")
    else:
        st.bar_chart(counts.set_index("feature_source"))

    st.subheader("样本口径说明")
    notes = []
    auto_summary = summarize_matrix(auto_matrix)
    semantic_summary = summarize_matrix(semantic_matrix)
    candidate_summary = summarize_matrix(candidate_pool)
    if candidate_summary:
        notes.append(f"- 候选池宽表：`{candidate_summary['rows']}` 行，`{candidate_summary['cols']}` 列。")
    if auto_summary:
        notes.append(f"- 自动特征矩阵：`{auto_summary['rows']}` 行，`{auto_summary['cols']}` 列，当前是抽样结果。")
    if semantic_summary:
        notes.append(f"- 语义特征矩阵：`{semantic_summary['rows']}` 行，`{semantic_summary['cols']}` 列，当前是全量结果。")
    if notes:
        st.markdown("\n".join(notes))

    st.subheader("候选池预览")
    preview = _preview(candidate_pool)
    if preview is None:
        st.info("缺少 `candidate_pool.parquet`。")
    else:
        st.dataframe(preview, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Auto 产物摘要")
        if auto_summary is None:
            st.info("缺少自动特征矩阵。")
        else:
            st.write({"rows": auto_summary["rows"], "cols": auto_summary["cols"]})
            st.code("\n".join(auto_summary["sample_columns"]), language="text")

    with col2:
        st.subheader("Semantic 产物摘要")
        if semantic_summary is None:
            st.info("缺少语义特征矩阵。")
        else:
            st.write({"rows": semantic_summary["rows"], "cols": semantic_summary["cols"]})
            semantic_cols = [c for c in semantic_matrix.columns if c not in {"SK_ID_CURR", "TARGET"}]
            st.code("\n".join(semantic_cols[:12]), language="text")
