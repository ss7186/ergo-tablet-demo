"""대칭 운동 분기: 근육 그룹 선택."""
import streamlit as st


def render(mapping: dict):
    st.markdown('<h1 class="screen-title">어디를 집중적으로 운동할까요?</h1>', unsafe_allow_html=True)
    st.markdown('<p class="screen-sub">양쪽 동일 자극으로 운동합니다</p>', unsafe_allow_html=True)

    goals = mapping["symmetric_goals"]
    keys = list(goals.keys())
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        goal = goals[key]
        with col:
            label = f"{goal['emoji']}\n\n{goal['label']}"
            if st.button(label, key=f"goal_{key}", use_container_width=True):
                st.session_state.sym_goal = key
                st.session_state.screen = "result"
                st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    _, back, _ = st.columns([2, 1, 2])
    with back:
        if st.button("◀ 이전", key="goal_back", type="tertiary"):
            st.session_state.screen = "mode"
            st.rerun()
