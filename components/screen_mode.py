"""최상위 분기: 대칭 운동 vs 비대칭 조정."""
import streamlit as st


def render(mapping: dict):
    st.markdown('<h1 class="screen-title">어떤 운동을 하시겠어요?</h1>', unsafe_allow_html=True)
    st.markdown('<p class="screen-sub">먼저 큰 방향을 정해주세요</p>', unsafe_allow_html=True)

    modes = mapping["top_modes"]
    cols = st.columns(2)
    for col, key in zip(cols, ["symmetric", "asymmetric"]):
        spec = modes[key]
        with col:
            # 큰 라벨만 button에. sub_label은 button 아래 caption으로 — 폰트 대비 명확.
            label = f"{spec['emoji']}  {spec['label']}"
            if st.button(label, key=f"mode_{key}", use_container_width=True):
                st.session_state.top_mode = key
                st.session_state.screen = "sym_goal" if key == "symmetric" else "asym_side"
                st.rerun()
            st.markdown(
                f'<p class="card-sub">{spec["sub_label"]}</p>',
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)
    _, back, _ = st.columns([2, 1, 2])
    with back:
        if st.button("◀ 처음으로", key="mode_back", use_container_width=True):
            st.session_state.screen = "welcome"
            st.rerun()
