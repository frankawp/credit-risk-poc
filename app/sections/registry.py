from __future__ import annotations

import streamlit as st

from app.data_loader import group_counts, source_counts


def render(artifacts: dict) -> None:
    st.header("步骤2 注册表")
    st.caption("作用：按变量来源和业务定义拆解候选变量，回答每个特征到底是什么。")

    registry = artifacts.get("feature_registry")
    composite_specs = artifacts.get("composite_feature_spec")
    if registry is None:
        st.info("该步骤产物尚未生成：缺少 `outputs/candidate_pool/registry/feature_registry.csv`。")
        return

    top = st.columns(3)
    top[0].metric("总变量数", int(registry.shape[0]))
    top[1].metric("来源类型数", int(registry["feature_source"].nunique()))
    top[2].metric("分组数", int(registry["feature_group"].nunique()))

    left, right = st.columns(2)
    with left:
        st.subheader("按来源统计")
        st.dataframe(source_counts(registry), use_container_width=True, hide_index=True)
    with right:
        st.subheader("按分组统计")
        st.dataframe(group_counts(registry), use_container_width=True, hide_index=True)

    source_options = ["全部"] + sorted(registry["feature_source"].dropna().unique().tolist())
    group_options = ["全部"] + sorted(registry["feature_group"].dropna().unique().tolist())
    status_options = ["全部"] + sorted(registry["status"].dropna().unique().tolist())

    c1, c2, c3 = st.columns(3)
    source_filter = c1.selectbox("按来源过滤", source_options, index=0)
    group_filter = c2.selectbox("按分组过滤", group_options, index=0)
    status_filter = c3.selectbox("按状态过滤", status_options, index=0)
    keyword = st.text_input("按特征名搜索", value="")

    filtered = registry.copy()
    if source_filter != "全部":
        filtered = filtered[filtered["feature_source"] == source_filter]
    if group_filter != "全部":
        filtered = filtered[filtered["feature_group"] == group_filter]
    if status_filter != "全部":
        filtered = filtered[filtered["status"] == status_filter]
    if keyword.strip():
        filtered = filtered[filtered["feature_name"].str.contains(keyword.strip(), case=False, na=False)]

    st.subheader("注册表列表")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("特征详情")
    if filtered.empty:
        st.info("当前筛选条件下没有特征。")
        return

    feature_name = st.selectbox("选择一个特征查看详情", filtered["feature_name"].tolist())
    detail = filtered[filtered["feature_name"] == feature_name].iloc[0]
    for field in [
        "feature_name",
        "feature_source",
        "feature_group",
        "source_table",
        "business_definition",
        "risk_direction",
        "status",
    ]:
        st.markdown(f"**{field}**: {detail[field]}")

    if detail["feature_source"] == "auto":
        st.info("该特征来自 Featuretools DFS 自动挖掘，业务定义以原始特征表达式名称为主。")
    elif detail["feature_source"] == "composite":
        st.subheader("组合特征说明")
        if composite_specs is None or composite_specs.empty:
            st.warning("缺少 `composite_feature_spec.csv`，当前无法展示组合特征的公式和来源。")
        else:
            spec = composite_specs[composite_specs["feature_name"] == feature_name]
            if spec.empty:
                st.warning("组合特征说明表中未找到该特征。")
            else:
                row = spec.iloc[0]
                st.markdown(f"**formula**: `{row['formula']}`")
                st.markdown(f"**base_features**: {row['base_features']}")
                st.markdown(f"**notes**: {row['notes']}")
