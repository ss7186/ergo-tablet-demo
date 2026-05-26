"""안전 점검 (contraindications). 'None' 큰 버튼이 default."""
import streamlit as st


def render(mapping: dict):
    st.markdown('<h1 class="screen-title">최근 수술 또는 급성 통증이 있나요?</h1>', unsafe_allow_html=True)
    st.markdown('<p class="screen-sub">없으면 큰 버튼을 눌러주세요. 안전 확인용입니다.</p>', unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        if st.button("없어요 — 운동 시작 ✨", key="no_concern", use_container_width=True):
            st.session_state.concerns = []
            st.session_state.screen = "result"
            st.rerun()

    st.markdown('<p class="or-divider">또는 해당하는 항목 선택</p>', unsafe_allow_html=True)

    concern_keys = list(mapping["concerns"].keys())
    selected = []
    cols = st.columns(len(concern_keys))
    for col, key in zip(cols, concern_keys):
        with col:
            if st.checkbox(key, key=f"concern_{key}"):
                selected.append(key)

    st.markdown("<br/>", unsafe_allow_html=True)
    back_col, _, next_col = st.columns([1, 2, 1])
    with back_col:
        if st.button("◀ 이전", key="concern_back", use_container_width=True):
            top = st.session_state.get("top_mode", "asymmetric")
            st.session_state.screen = "sym_goal" if top == "symmetric" else "asym_symptom"
            st.rerun()
    with next_col:
        if st.button("다음 ▶", key="concern_next", use_container_width=True):
            st.session_state.concerns = selected
            st.session_state.screen = "result"
            st.rerun()
