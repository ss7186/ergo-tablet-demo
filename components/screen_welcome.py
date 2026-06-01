import streamlit as st
import streamlit.components.v1 as components

from utils.media import render_video, render_illustration, has_media


@st.dialog(" ", width="large")
def _howto_dialog():
    # dialog 열릴 때 스크롤 최상단으로 강제 (video 자동 focus + scrollIntoView 차단)
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const SELECTORS = [
          'div[role="dialog"]',
          '[data-testid="stDialog"]',
          'dialog',
          '[aria-modal="true"]',
          '[data-baseweb="modal"]',
        ];
        const forceTop = () => {
          // 1. video 자동 스크롤 차단
          doc.querySelectorAll('video').forEach(v => {
            v.tabIndex = -1;
            v.scrollIntoView = () => {};
            v.autofocus = false;
          });
          // 2. dialog 및 모든 scrollable 자식 top으로
          SELECTORS.forEach(sel => {
            doc.querySelectorAll(sel).forEach(dlg => {
              dlg.scrollTop = 0;
              dlg.querySelectorAll('*').forEach(el => {
                if (el.scrollHeight > el.clientHeight) el.scrollTop = 0;
              });
            });
          });
        };
        forceTop();
        [30, 80, 150, 300, 500, 800, 1200].forEach(d => setTimeout(forceTop, d));
        </script>
        """,
        height=0,
    )

    # 0. 메인 title (dialog header의 기본 title 외에 본문 시작점)
    st.markdown('<h1 class="howto-title">에르고미터 사용법</h1>', unsafe_allow_html=True)

    # 1. 에르고미터 부위 안내 이미지
    if has_media("illustrations/howto_device_parts.png"):
        render_illustration("illustrations/howto_device_parts.png")

    # 2. 사용 순서
    st.markdown('<h3 class="howto-step-title">사용 순서</h3>', unsafe_allow_html=True)
    st.markdown(
        """
        **1. 좌석 조정** — 레버를 앞으로 당겨 안장의 위치를 조절합니다.
        > 페달을 가장 멀리 뻗어 무릎이 살짝 굽혀지는 위치에서 레버를 뒤로 당겨 고정합니다.

        **2. 페달 세팅** — 화면이 추천한 좌·우 페달 각도를 확인하고 기기의 레버를 조절합니다.

        **3. 페달링** — 균일한 속도로 5 ~ 10분 탑니다.
        > 통증 발생 시 즉시 중단합니다.
        """
    )

    st.markdown("---")

    # 3. 영상 안내
    st.markdown('<h2 class="howto-section">영상 안내</h2>', unsafe_allow_html=True)
    render_video("videos/howto_main2.mp4")

    st.markdown("---")

    # 4. 4가지 페달링 모드 — mode1~mode4.png 세로 나열
    st.markdown('<h2 class="howto-section">4가지 페달링 모드</h2>', unsafe_allow_html=True)
    for i in range(1, 5):
        path = f"illustrations/mode{i}.png"
        if has_media(path):
            render_illustration(path)


def render():
    st.markdown(
        """
        <div class="welcome-wrap">
          <div class="welcome-brand">고려대학교 구로병원 정형외과 강성현교수 | 고려대학교 의공학교실</div>
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
