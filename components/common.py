"""공통 UI helpers (back button 등)."""
import streamlit as st


def render_top_back(target_screen: str, key: str, label: str = "◀ 이전") -> None:
    """우측 상단에 작은 뒤로가기 버튼.

    Layout: full-width [8, 1] 컬럼 → 마지막 컬럼에 narrow button.
    Style: theme.css 의 `button[data-testid*="_back"]` 셀렉터가 처리
           (key가 반드시 `_back` 으로 끝나야 함).

    Args:
        target_screen: 클릭 시 이동할 screen 이름 (session_state.screen 값)
        key: streamlit button unique key (suffix `_back` 필수)
        label: 버튼 라벨 (default "◀ 이전")
    """
    assert key.endswith("_back"), \
        f"render_top_back: key '{key}' must end with '_back' for CSS targeting"
    cols = st.columns([8, 1])
    with cols[1]:
        if st.button(label, key=key, use_container_width=True):
            st.session_state.screen = target_screen
            st.rerun()
