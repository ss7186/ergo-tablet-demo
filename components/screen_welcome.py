import streamlit as st

from utils.media import render_video, render_illustration, render_illustration_fixed_height, has_media
from utils.data_loader import load_conditions


def _render_condition_detail(cond: dict):
    """사용법 dialog 안에서 선택된 condition 상세 표시.

    Equal-height layout: 모든 행에서 좌우 column의 끝 지점이 동일하도록
    각 block을 fixed min-height + flex로 강제.

    레이아웃:
      1. [페달 자세 block] · [활성 근육 block]                  (height: BLOCK_H)
      2. [주요 효과] · [운동 팁 + 통증 위험]                     (height: ROW2_H)
      3. 조건 영상 (전폭)
    """
    media = cond.get("media", {}) or {}
    BLOCK_H = 320
    ROW2_H = 360

    sym = cond.get("symmetry", "symm")
    sym_label = "양쪽 같은 세팅" if sym == "symm" else "왼쪽 / 오른쪽 다른 세팅"
    ma = cond.get("muscle_activation_summary", "")
    jl = cond.get("joint_load_summary", "")

    # ── 1행: 페달 자세 block | 활성 근육 block (둘 다 BLOCK_H로 통일) ──
    pedal_block, muscle_block = st.columns([1, 1])

    with pedal_block:
        st.markdown('<p class="illust-cap">페달 자세</p>', unsafe_allow_html=True)
        p_ill, p_info = st.columns([1, 1])
        with p_ill:
            render_illustration_fixed_height(media.get("illustration"), height=BLOCK_H)
        with p_info:
            st.markdown(
                f"""
                <div class="howto-setting-card vertical" style="min-height:{BLOCK_H}px;">
                  <p class="setting-sub">{sym_label}</p>
                  <div class="setting-row-v">
                    <div class="lr-tag">👈 왼쪽 페달</div>
                    <div class="lr-value">{cond.get('left_setting_label', '수평')}</div>
                  </div>
                  <div class="setting-row-v">
                    <div class="lr-tag">👉 오른쪽 페달</div>
                    <div class="lr-value">{cond.get('right_setting_label', '수평')}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with muscle_block:
        st.markdown('<p class="illust-cap">🔴 활성 근육</p>', unsafe_allow_html=True)
        m_ill, m_info = st.columns([1, 1])
        with m_ill:
            render_illustration_fixed_height(media.get("muscle_illustration"), height=BLOCK_H)
        with m_info:
            cards = []
            if ma:
                cards.append(f'<div class="info-card compact"><h4>💪 활성 근육</h4><p>{ma}</p></div>')
            if jl:
                cards.append(f'<div class="info-card compact"><h4>🦴 관절 부담</h4><p>{jl}</p></div>')
            wrap = f'<div class="info-wrap" style="min-height:{BLOCK_H}px;">{"".join(cards)}</div>'
            st.markdown(wrap, unsafe_allow_html=True)

    # ── 2행: 주요 효과 | 운동 팁 + 통증 위험 ──
    eff = cond.get("user_friendly_effects", {})
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

    eff_l, side_r = st.columns([1, 1])
    with eff_l:
        st.markdown(
            f'<div class="effect-card equal-h" style="min-height:{ROW2_H}px;">'
            f'<h3>주요 효과</h3><ul class="effect-list">{"".join(rows)}</ul></div>',
            unsafe_allow_html=True,
        )
    with side_r:
        side_html = [f'<div class="info-wrap" style="min-height:{ROW2_H}px;">']
        cue = eff.get("coaching_cue")
        if cue:
            side_html.append(
                f'<div class="coaching-card"><span class="coaching-icon">💡</span> <b>운동 팁</b><br/>{cue}</div>'
            )
        pain = cond.get("pain_risks", [])
        if pain:
            items = "".join(f"<li>{p}</li>" for p in pain)
            side_html.append(
                f'<div class="pain-card"><h4>⚠️ 다음과 같은 통증·상태가 있다면 주의</h4><ul>{items}</ul></div>'
            )
        side_html.append("</div>")
        st.markdown("".join(side_html), unsafe_allow_html=True)

    # ── 3행: 조건 영상 ──
    if has_media(media.get("video")):
        st.markdown("**🎬 조건 영상**")
        render_video(media.get("video"), media.get("video_description"))


@st.dialog("다축 에르고미터 사용법", width="large")
def _howto_dialog():
    conditions = load_conditions()

    # 1. 전체 사용법 영상
    st.markdown("### 전체 사용 안내 영상")
    render_video("videos/howto_main.mp4", description="다축 에르고미터 사용 전반 안내")

    st.markdown("---")

    # 2. 사용 순서 — 그림 1장으로 통합 (PPT 슬라이드 캡처)
    st.markdown("### 사용 순서")
    if has_media("illustrations/howto_steps.png"):
        render_illustration("illustrations/howto_steps.png")
    else:
        # 그림 추가 전 fallback: 텍스트
        st.markdown(
            """
            **1. 회전면 방향 및 페달 각도 조절** — 크랭크 옆 / 페달 옆 / 페달 아래 레버로 조작
              - 와이드·토인/토아웃 (Abduction): 15°, 30°
              - 내로우·롤인 (Adduction): 15°

            **2. 부하 조절** — 정면 다이얼로 강도 조절 (여성 8–10 / 남성 12단계 권장)

            **3. 안장 위치 조절** — 페달을 가장 멀리 뻗었을 때 무릎이 살짝 굽혀지는 위치로 고정
            """
        )
        st.info(
            "📌 통합 조작법 그림이 들어올 자리: `assets/illustrations/howto_steps.png`. "
            "파일이 추가되면 이 텍스트가 그림으로 교체됩니다."
        )

    st.markdown("---")

    # 3. 조건별 상세 탐색
    st.markdown("### 각 조건 자세히 보기")
    st.caption("궁금한 페달 조건을 골라 타겟 근육·부하 방향을 확인하세요")

    cond_keys = [k for k in conditions.keys() if not k.startswith("_")]
    cond_labels = {k: f"{k} — {conditions[k].get('name_kr', k)}" for k in cond_keys}

    # 대칭 / 비대칭 분리
    symm_keys = [k for k in cond_keys if conditions[k].get("symmetry") == "symm"]
    asym_keys = [k for k in cond_keys if conditions[k].get("symmetry") == "asym"]

    tab_symm, tab_asym = st.tabs([f"⚖️ 양쪽 동일 ({len(symm_keys)})", f"🔄 좌우 차이 ({len(asym_keys)})"])

    with tab_symm:
        choice_s = st.radio(
            "조건 선택",
            options=symm_keys,
            format_func=lambda k: cond_labels[k],
            key="howto_symm_choice",
            horizontal=True,
        )
        if choice_s:
            _render_condition_detail(conditions[choice_s])

    with tab_asym:
        choice_a = st.radio(
            "조건 선택",
            options=asym_keys,
            format_func=lambda k: cond_labels[k],
            key="howto_asym_choice",
            horizontal=True,
        )
        if choice_a:
            _render_condition_detail(conditions[choice_a])


def render():
    st.markdown(
        """
        <div class="welcome-wrap">
          <div class="welcome-brand">KOREA UNIVERSITY GURO HOSPITAL · BIOMEDICAL ENGINEERING</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    img_col, text_col = st.columns([1, 1])
    with img_col:
        render_illustration("illustrations/device_main.png")
    with text_col:
        st.markdown(
            """
            <div class="welcome-text">
              <h1 class="welcome-title">다축 에르고미터<br/><span class="welcome-sub-en">Multi-axis Ergometer</span></h1>
              <p class="welcome-sub">페달링의 회전면과 각도를 조절하여<br/>다양한 하지 근육을 선택적으로 타겟하는<br/>맞춤형 사이클 운동 기기</p>
              <p class="welcome-cta">30초만 투자하시면<br/>오늘의 맞춤 세팅을 추천해드려요</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    _, start, howto, _ = st.columns([1, 2, 2, 1])
    with start:
        if st.button("시작하기 ▶", key="start", use_container_width=True):
            st.session_state.screen = "mode"
            st.rerun()
    with howto:
        if st.button("📺 사용법 보기", key="howto", use_container_width=True):
            _howto_dialog()

    st.markdown(
        '<p class="disclaimer">본 device의 일반적 효과를 안내합니다. 의학적 조언이 아닙니다.</p>',
        unsafe_allow_html=True,
    )
