"""webOS(스탠바이미) 등 구형 브라우저 호환성 패치.

Streamlit `st.video()`로 렌더된 <video>는 기본 속성이 부족해 webOS Chromium에서
재생이 막힐 수 있다. 본 모듈은 부모 document를 polling하며 video 태그에
필요한 속성을 강제 부여한다.

또한 iOS/webOS 일부 환경에서 emoji가 tofu로 렌더되는 것을 Twemoji로 대체하는
JS 폴백도 함께 주입한다.
"""
import streamlit.components.v1 as components


def inject_compat():
    """app.py에서 한 번 호출. 0-height iframe으로 부모 window를 패치한다."""
    components.html(
        """
        <script>
        (function() {
          var doc = window.parent && window.parent.document;
          if (!doc) return;

          // === 1. <video> 태그에 playsinline / preload / controls 강제 ===
          var patchVideos = function() {
            var vids = doc.querySelectorAll('video');
            for (var i = 0; i < vids.length; i++) {
              var v = vids[i];
              if (v.dataset.compatPatched === '1') continue;
              v.setAttribute('playsinline', '');
              v.setAttribute('webkit-playsinline', '');
              v.setAttribute('controls', '');
              v.preload = 'metadata';
              v.dataset.compatPatched = '1';
            }
          };

          // === 2. Twemoji fallback (webOS에 Color Emoji font 없을 때) ===
          var loadTwemoji = function(cb) {
            if (window.parent.twemoji) { cb(); return; }
            var s = doc.createElement('script');
            s.src = 'https://twemoji.maxcdn.com/v/latest/twemoji.min.js';
            s.crossOrigin = 'anonymous';
            s.onload = cb;
            doc.head.appendChild(s);
          };
          var parseEmoji = function() {
            try {
              if (window.parent.twemoji) {
                window.parent.twemoji.parse(doc.body, {
                  folder: 'svg',
                  ext: '.svg',
                  className: 'twemoji-img'
                });
              }
            } catch (e) {}
          };

          // === 초기 + 주기 실행 (Streamlit이 DOM 재구성하므로) ===
          var tick = function() {
            patchVideos();
            parseEmoji();
          };
          loadTwemoji(tick);
          setInterval(tick, 1500);
        })();
        </script>
        <style>
          /* twemoji가 만든 <img>를 글자 크기에 맞춤 */
          img.twemoji-img {
            height: 1em !important;
            width: 1em !important;
            margin: 0 0.05em 0 0.1em !important;
            vertical-align: -0.1em !important;
            display: inline-block !important;
          }
        </style>
        """,
        height=0,
    )
