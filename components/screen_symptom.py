"""비대칭 분기: 증상 카테고리 선택."""
import streamlit as st


def render(mapping: dict):
    side = st.session_state.get("asym_side", "both")
    side_label = mapping["asymmetric_sides"].get(side, {}).get("label", "")
    st.markdown(
        f'<h1 class="screen-title">"{side_label}" — 어떤 증상이 있나요?</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="screen-sub">가장 가까운 것 하나만 골라주세요. 잘 모르겠으면 "잘 모르겠음"</p>',
        unsafe_allow_html=True,
    )

    symptoms = mapping["asymmetric_symptoms"]
    keys = list(symptoms.keys())
    rows = [keys[i:i+4] for i in range(0, len(keys), 4)]
    for row in rows:
        cols = st.columns(len(row))
        for col, key in zip(cols, row):
            spec = symptoms[key]
            with col:
                label = f"{spec['emoji']}  {spec['label']}"
                if st.button(label, key=f"sym_{key}", use_container_width=True):
                    st.session_state.asym_symptom = key
                    st.session_state.screen = "result"
                    st.rerun()
                st.markdown(
                    f'<p class="card-sub">{spec["sub_label"]}</p>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br/>", unsafe_allow_html=True)
    _, back, _ = st.columns([2, 1, 2])
    with back:
        if st.button("◀ 이전", key="symptom_back", use_container_width=True):
            st.session_state.screen = "asym_side"
            st.rerun()
