"""비대칭 분기: 어느 쪽이 불편한지 입력."""
import streamlit as st

from components.common import render_top_back


def render(mapping: dict):
    render_top_back("mode", "asym_side_back")

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
            sub = spec.get("sub_label")
            if sub:
                st.markdown(f'<p class="card-sub">{sub}</p>', unsafe_allow_html=True)
