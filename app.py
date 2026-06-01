"""Tilted-Plane Ergometer 태블릿 데모 앱 — 대칭/비대칭 분기 flow."""
from pathlib import Path

import streamlit as st

from components import (
    screen_welcome, screen_mode, screen_goal,
    screen_asym, screen_symptom, screen_concern, screen_result,
)
from utils.data_loader import load_conditions, load_mapping


st.set_page_config(
    page_title="비대칭 조정 에르고미터",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _inject_css():
    css_path = Path(__file__).parent / "style" / "theme.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def _init_state():
    st.session_state.setdefault("screen", "welcome")


def main():
    _inject_css()
    _init_state()

    conditions = load_conditions()
    mapping = load_mapping()

    screen = st.session_state.screen
    routes = {
        "welcome": lambda: screen_welcome.render(),
        "mode": lambda: screen_mode.render(mapping),
        "sym_goal": lambda: screen_goal.render(mapping),
        "asym_side": lambda: screen_asym.render(mapping),
        "asym_symptom": lambda: screen_symptom.render(mapping),
        "concern": lambda: screen_concern.render(mapping),
        "result": lambda: screen_result.render(conditions, mapping),
    }
    fn = routes.get(screen)
    if fn is None:
        st.session_state.screen = "welcome"
        st.rerun()
    else:
        fn()

    st.markdown(
        """
        <div class="app-footer">
          KOREA UNIVERSITY GURO HOSPITAL · BIOMEDICAL ENGINEERING
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
