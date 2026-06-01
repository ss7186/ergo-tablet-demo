import base64
from pathlib import Path

import streamlit as st

from components.recommendation import recommend, check_contraindications
from utils.media import render_illustration, render_video

_ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _img_data_url(rel_path: str) -> str:
    """assets 상대경로 → data: URL. 없거나 실패하면 빈 문자열."""
    if not rel_path:
        return ""
    p = _ASSETS / rel_path
    if not p.exists():
        return ""
    ext = p.suffix[1:].lower()
    mime = "jpeg" if ext == "jpg" else ext
    return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


_INTENSITY_BADGE = {
    "낮음": ("🟢", "낮음"),
    "보통": ("🟡", "보통"),
    "높음": ("🔴", "높음"),
}


def _render_settings_card(cond: dict):
    sym = cond.get("symmetry", "symm")
    sym_label = "양쪽 동일" if sym == "symm" else "왼쪽 / 오른쪽 다른 세팅"
    media = cond.get("media", {}) or {}
    img_url = _img_data_url(media.get("illustration", ""))
    img_html = (
        f'<img class="setting-card-img" src="{img_url}" alt="" '
        f'style="display:block; width:auto; max-width:100%; max-height:420px; '
        f'height:auto; object-fit:contain; margin:0.8rem auto 0; border-radius:14px;" />'
    ) if img_url else ""
    st.markdown(
        f"""
        <div class="setting-card">
          <h3>오늘의 추천 세팅</h3>
          <p class="setting-sub">{sym_label}</p>
          {img_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_effects(cond: dict, cond_key: str):
    eff = cond["user_friendly_effects"]
    targets = cond.get("mechanism_target", [])
    rows = []
    for t in targets:
        rows.append(f'<li><b>{t}</b> 타겟</li>')
    for m in eff.get("muscles_strengthened", []):
        rows.append(f'<li><b>{m}</b> 강화</li>')
    for m in eff.get("load_decreased", []):
        rows.append(f'<li><b>{m}</b> 부담 감소</li>')
    for m in eff.get("load_increased", []):
        rows.append(f'<li><b>{m}</b> 증가 (참고)</li>')
    note = eff.get("contralateral_note")
    if note:
        rows.append(f'<li>{note}</li>')

    muscle_img_url = _img_data_url(f"illustrations/muscle_{cond_key.lower()}.png")
    muscle_img_html = (
        f'<img class="effect-muscle-img" src="{muscle_img_url}" alt="" '
        f'style="display:block; width:auto; max-width:100%; max-height:300px; '
        f'height:auto; object-fit:contain; margin:1rem auto 0; border-radius:14px;" />'
    ) if muscle_img_url else ""

    st.markdown(
        f'<div class="effect-card">'
        f'<h3>예상 효과</h3>'
        f'<ul class="effect-list">{"".join(rows)}</ul>'
        f'{muscle_img_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_meta(cond: dict, source_label: str | None):
    icon, label = _INTENSITY_BADGE.get(cond["intensity"], ("🟡", cond["intensity"]))
    st.markdown(
        f"""
        <div class="meta-row">
          <div class="meta-cell"><span class="meta-icon">{icon}</span><span class="meta-label">강도</span><span class="meta-val">{label}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_safety(warnings: list[str]):
    if not warnings:
        return
    items = "".join(f"<li>{w}</li>" for w in warnings)
    st.markdown(
        f'<div class="safety-card"><h3>⚠️ 안전 안내</h3><ul>{items}</ul><p class="safety-foot">해당 사항이 있으면 운동 전 의무실에 문의해주세요.</p></div>',
        unsafe_allow_html=True,
    )


def render(conditions: dict, mapping: dict):
    top = st.session_state.get("top_mode", "asymmetric")
    if not top:
        st.session_state.screen = "mode"
        st.rerun()
        return

    cond_key, cond, br = recommend(
        top, conditions, mapping,
        sym_goal=st.session_state.get("sym_goal"),
        asym_symptom=st.session_state.get("asym_symptom"),
        asym_side=st.session_state.get("asym_side"),
    )

    cond_name = cond.get("name_kr", cond_key)
    if br["source"] == "matrix_v2":
        side_data = mapping["asymmetric_sides"][br["side"]]
        symptom_data = mapping["asymmetric_symptoms"][br["symptom"]]
        context = f"{side_data['emoji']} {side_data['label']} · {symptom_data['emoji']} {symptom_data['label']}"
        source_label = "임상 처방 매트릭스 v2"
    elif br["source"] == "score":
        goal_data = mapping["symmetric_goals"][br["goal"]]
        context = f"{goal_data['emoji']} {goal_data['label']} 강화"
        source_label = "근활성도 기반"
    else:
        context = "추천 세팅"
        source_label = None
    diff_icon, diff_label = _INTENSITY_BADGE.get(cond["intensity"], ("🟡", cond["intensity"]))
    st.markdown(
        f'<div class="result-header">'
        f'  <div class="result-title-block">'
        f'    <p class="result-context">{context}</p>'
        f'    <div class="result-condition">{cond_name}</div>'
        f'  </div>'
        f'  <div class="result-difficulty">'
        f'    <span class="diff-icon">{diff_icon}</span>'
        f'    <span class="diff-label">난이도</span>'
        f'    <span class="diff-val">{diff_label}</span>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 1행: 두 카드 (좌/우 균등, container height로 동일 높이 강제)
    left, right = st.columns(2, gap="small")
    media = cond.get("media", {}) or {}
    CARD_HEIGHT = 720
    with left:
        with st.container(height=CARD_HEIGHT, border=False):
            _render_settings_card(cond)
    with right:
        with st.container(height=CARD_HEIGHT, border=False):
            _render_effects(cond, cond_key)

    # 2행: 컨디션 영상 (전체 폭) — caption 없음
    render_video(media.get("video"))

    warnings = check_contraindications(cond, st.session_state.get("concerns", []), mapping)
    if warnings:
        _render_safety(warnings)

    st.markdown("<br/>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        if st.button("👍 도움됐어요", key="fb_up", type="tertiary"):
            st.session_state.feedback = "up"
            st.toast("감사합니다!", icon="🙏")
    with f2:
        if st.button("👎 별로예요", key="fb_down", type="tertiary"):
            st.session_state.feedback = "down"
            st.toast("의견 감사합니다", icon="🙏")
    with f3:
        if st.button("↻ 다시 시작", key="restart", type="tertiary"):
            for k in ("top_mode", "sym_goal", "asym_side", "asym_symptom", "concerns", "feedback"):
                st.session_state.pop(k, None)
            st.session_state.screen = "mode"
            st.rerun()
    with f4:
        if st.button("🏠 홈", key="home", type="tertiary"):
            for k in ("top_mode", "sym_goal", "asym_side", "asym_symptom", "concerns", "feedback"):
                st.session_state.pop(k, None)
            st.session_state.screen = "welcome"
            st.rerun()
