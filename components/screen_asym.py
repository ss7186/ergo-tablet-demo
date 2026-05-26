"""비대칭 분기: 어느 쪽이 불편한지 입력."""
import streamlit as st


def render(mapping: dict):
    st.markdown('<h1 class="screen-title">어느 쪽이 더 불편하세요?</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="screen-sub">정확하지 않아도 괜찮아요. 잘 모르겠으면 "양쪽 다"</p>',
        unsafe_allow_html=True,
    )

    sides = mapping["asymmetric_sides"]
    keys = list(sides.keys())
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        spec = sides[key]
        with col:
            label = f"{spec['emoji']}\n\n{spec['label']}"
            if st.button(label, key=f"side_{key}", use_container_width=True):
                st.session_state.asym_side = key
                st.session_state.screen = "asym_symptom"
                st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    _, back, _ = st.columns([2, 1, 2])
    with back:
        if st.button("◀ 이전", key="asym_side_back", use_container_width=True):
            st.session_state.screen = "mode"
            st.rerun()
