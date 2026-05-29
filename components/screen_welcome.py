import streamlit as st

from utils.media import render_video, render_illustration, has_media


@st.dialog("에르고미터 사용법", width="large")
def _howto_dialog():
    if has_media("illustrations/device_main.png"):
        render_illustration("illustrations/device_main.png")

    st.markdown(
        """
        ### 사용 순서

        **1. 좌석 조정** — 편안한 위치에 앉아 페달이 발에 자연스럽게 닿도록 좌석 높이 조정

        **2. 페달 세팅** — 화면이 추천한 좌/우 페달 각도를 확인하고 device의 dial을 맞춥니다

        **3. 페달링** — 균일한 속도로 5–10분. 통증이 있으면 즉시 중단
        """
    )

    if has_media("illustrations/pedal_dial.png"):
        c1, c2 = st.columns([1, 2])
        with c1:
            render_illustration("illustrations/pedal_dial.png")
        with c2:
            st.markdown(
                "**페달 각도 dial**  \n"
                "–30° / 0° / +30° 눈금에 맞춰 페달의 기울임을 조절합니다."
            )

    st.markdown("---")
    st.markdown("### 영상 안내")
    render_video("videos/howto_main.mp4", description="에르고미터 사용 전반 안내")

    st.markdown("---")
    st.markdown("### 4가지 페달 모드")
    cols = st.columns(4)
    modes = [
        ("NE", "수평 (Neutral)", "기본 자세 · 대칭 운동"),
        ("AD", "발끝 안쪽 (toes-in)", "엉덩이 옆 근육 자극"),
        ("AE", "발끝 바깥 (toes-out)", "허벅지 안쪽 + 회전 안정성"),
        ("AI", "발끝 안쪽 + 외번", "고관절 회전 control"),
    ]
    for col, (code, name, sub) in zip(cols, modes):
        with col:
            render_illustration(f"illustrations/mode_{code.lower()}.png")
            st.markdown(f"**{code}** — {name}")
            st.caption(sub)


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
              <div class="title-wrap">
                <h1 class="welcome-title">Triplanar ERGO</h1>
                <p class="welcome-subtitle">다축 조정 자전거 에르고미터</p>
              </div>
              <p class="welcome-sub">페달링의 회전면과 각도를 조절하여 다양한 하지 근육을 선택적으로 타겟하는 맞춤형 사이클 운동 기기</p>
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
        '<p class="disclaimer">본 기기는 운동 가이드를 안내할 뿐 의학적 조언을 대신하지 않습니다.<br/>통증이 있으면 운동을 멈추고 전문의와 상담해주세요.</p>',
        unsafe_allow_html=True,
    )
