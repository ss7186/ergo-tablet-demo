import streamlit as st

from components.recommendation import recommend
from utils.media import render_illustration, render_video


_INTENSITY_BADGE = {
    "쉬움": ("🟢", "쉬움"),
    "보통": ("🟡", "보통"),
    "강함": ("🔴", "강함"),
}


def _render_settings_card(cond: dict):
    sym = cond.get("symmetry", "symm")
    sym_label = "양쪽 같은 세팅" if sym == "symm" else "왼쪽 / 오른쪽 다른 세팅"
    right = cond.get("right_setting_label", "수평")
    left = cond.get("left_setting_label", "수평")
    st.markdown(
        f"""
        <div class="setting-card">
          <h3>오늘의 추천 세팅 ✨</h3>
          <p class="setting-sub">{sym_label}</p>
          <div class="lr-grid">
            <div class="lr-cell">
              <div class="lr-tag">👈 왼쪽 페달</div>
              <div class="lr-value">{left}</div>
            </div>
            <div class="lr-cell">
              <div class="lr-tag">👉 오른쪽 페달</div>
              <div class="lr-value">{right}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_effects(cond: dict):
    eff = cond["user_friendly_effects"]
    targets = cond.get("mechanism_target", [])
    rows = []
    for t in targets:
        rows.append(f'<li class="eff-good">🎯 <b>{t}</b> 타겟</li>')
    for m in eff.get("muscles_strengthened", []):
        rows.append(f'<li class="eff-good">💪 <b>{m}</b> 강화</li>')
    for m in eff.get("load_decreased", []):
        rows.append(f'<li class="eff-good">✅ <b>{m}</b> 부담 감소</li>')
    for m in eff.get("load_increased", []):
        rows.append(f'<li class="eff-warn">⚠️ <b>{m}</b> 증가 (참고)</li>')
    note = eff.get("contralateral_note")
    if note:
        rows.append(f'<li class="eff-info">🧠 {note}</li>')

    st.markdown(
        f'<div class="effect-card"><h3>예상 효과</h3><ul class="effect-list">{"".join(rows)}</ul></div>',
        unsafe_allow_html=True,
    )

    # Phase-resolved coaching cue (ADR-003) — push/pull concentric/eccentric pattern을
    # 일상어로 한 줄. 데이터 출처는 conditions.json::biomech_data.phase_resolved.
    cue = eff.get("coaching_cue")
    if cue:
        st.markdown(
            f'<div class="coaching-card"><span class="coaching-icon">💡</span> <b>운동 팁</b>: {cue}</div>',
            unsafe_allow_html=True,
        )


def _render_meta(cond: dict, source_label: str | None):
    icon, label = _INTENSITY_BADGE.get(cond["intensity"], ("🟡", cond["intensity"]))
    dur = cond["duration_min"]
    dur_label = f"{dur[0]}–{dur[1]}분" if isinstance(dur, list) and len(dur) == 2 else f"{dur}분"
    src = f'<div class="meta-cell"><span class="meta-icon">📋</span><span class="meta-label">근거</span><span class="meta-val">{source_label}</span></div>' if source_label else ""
    st.markdown(
        f"""
        <div class="meta-row">
          <div class="meta-cell"><span class="meta-icon">{icon}</span><span class="meta-label">강도</span><span class="meta-val">{label}</span></div>
          <div class="meta-cell"><span class="meta-icon">⏱</span><span class="meta-label">추천 시간</span><span class="meta-val">{dur_label}</span></div>
          {src}
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
        side = mapping["asymmetric_sides"][br["side"]]["label"]
        symptom = mapping["asymmetric_symptoms"][br["symptom"]]["label"]
        title = f"{side} · {symptom} → {cond_name}"
        source_label = "임상 처방 매트릭스 v2"
    elif br["source"] == "score":
        goal = mapping["symmetric_goals"][br["goal"]]["label"]
        title = f"{goal} 강화 → {cond_name}"
        source_label = "근활성도 기반"
    elif br["source"] == "forced":
        goal = mapping["symmetric_goals"][br["goal"]]["label"]
        title = f"{goal} → {cond_name}"
        source_label = "관절 부담 최저 모드"
    else:
        title = f"추천 세팅 → {cond_name}"
        source_label = None
    st.markdown(f'<h1 class="screen-title">{title}</h1>', unsafe_allow_html=True)

    left, right = st.columns([2, 3])
    media = cond.get("media", {}) or {}
    with left:
        _render_settings_card(cond)
        render_illustration(media.get("illustration"), width=320)
    with right:
        _render_effects(cond)
        render_video(media.get("video"), media.get("video_description"))

    # ── 활성 근육 + 관절 부담 + 통증 위험 (사용법 dialog와 일관) ──
    ma = cond.get("muscle_activation_summary")
    jl = cond.get("joint_load_summary")
    pain = cond.get("pain_risks", [])
    if ma or jl or pain:
        st.markdown("<br/>", unsafe_allow_html=True)
        info_l, info_r = st.columns([1, 1])
        with info_l:
            if ma:
                st.markdown(
                    f'<div class="info-card"><h4>💪 활성화되는 근육</h4><p>{ma}</p></div>',
                    unsafe_allow_html=True,
                )
            if jl:
                st.markdown(
                    f'<div class="info-card"><h4>🦴 관절 부담</h4><p>{jl}</p></div>',
                    unsafe_allow_html=True,
                )
        with info_r:
            muscle_illust = media.get("muscle_illustration")
            if muscle_illust:
                render_illustration(muscle_illust, width=280)
            if pain:
                items = "".join(f"<li>{p}</li>" for p in pain)
                st.markdown(
                    f'<div class="pain-card"><h4>⚠️ 다음과 같은 통증·상태가 있다면 주의</h4><ul>{items}</ul></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br/>", unsafe_allow_html=True)
    f1, f2, _, again_col = st.columns([1, 1, 1, 2])
    with f1:
        if st.button("👍 도움됐어요", key="fb_up", use_container_width=True):
            st.session_state.feedback = "up"
            st.toast("감사합니다!", icon="🙏")
    with f2:
        if st.button("👎 별로예요", key="fb_down", use_container_width=True):
            st.session_state.feedback = "down"
            st.toast("의견 감사합니다", icon="🙏")
    with again_col:
        if st.button("다시 시작 ↻", key="restart", use_container_width=True):
            for k in ("top_mode", "sym_goal", "asym_side", "asym_symptom", "concerns", "feedback"):
                st.session_state.pop(k, None)
            st.session_state.screen = "welcome"
            st.rerun()
