from __future__ import annotations

import streamlit as st

from app.data_loader import ARTIFACTS, artifact_exists, load_all_artifacts
from app.sections import candidate_pool, overview, registry, selection


st.set_page_config(
    page_title="Dual Engine Outputs Viewer",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def get_artifacts():
    return load_all_artifacts()


def render_sidebar() -> str:
    st.sidebar.title("Outputs 流程查看器")
    st.sidebar.caption("按双引擎工作流步骤浏览当前 outputs 产物。")
    page = st.sidebar.radio(
        "导航",
        ["总览", "步骤1 候选池", "步骤2 注册表", "步骤3 特征筛选"],
        index=0,
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("产物可用性")
    for artifact in ARTIFACTS.values():
        mark = "OK" if artifact_exists(artifact.key) else "MISSING"
        st.sidebar.write(f"{mark} {artifact.label}")
    return page


def main() -> None:
    st.title("Dual Engine Outputs Viewer")
    artifacts = get_artifacts()
    page = render_sidebar()

    if page == "总览":
        overview.render(artifacts)
    elif page == "步骤1 候选池":
        candidate_pool.render(artifacts)
    elif page == "步骤2 注册表":
        registry.render(artifacts)
    elif page == "步骤3 特征筛选":
        selection.render(artifacts)


if __name__ == "__main__":
    main()
