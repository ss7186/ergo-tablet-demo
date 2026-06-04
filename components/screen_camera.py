"""실시간 자세 추적 (Phase 1 PoC).

Browser-side MediaPipe Pose Landmarker (Tasks Vision).
- 정면 카메라 1대 / 30fps (가능한 만큼)
- Skeleton overlay 만 — metric / feedback cue 는 Phase 2 에서
- 모든 처리는 사용자 브라우저 (WebGL/WASM) — 서버 부담 0

References:
- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js
- ADR-005 (예정) — Real-time skeletal tracking 임상 metric 매핑

Notes for inheritor:
- StanbyME 등 Android WebView 에서 동작하려면 AndroidManifest 의 CAMERA permission +
  WebChromeClient.onPermissionRequest grant 필요. ergo-android-wrapper repo 확인.
- HF Space 는 iframe `allow=camera` 가 기본값 (2025+ 정책). 차단되면 직접 URL 접속.
- 향후 Python 측 metric 계산이 필요하면 streamlit-webrtc 로 마이그레이션 또는
  postMessage 로 landmark JSON 전달 + components.declare_component 로 재작성.
"""
import streamlit as st
import streamlit.components.v1 as components

from components.common import render_top_back


_POSE_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<style>
  html, body { margin: 0; padding: 0; background: #0f172a; color: #e2e8f0;
               font-family: -apple-system, "Segoe UI", "Apple SD Gothic Neo",
                            "Malgun Gothic", sans-serif; }
  .stage { position: relative; max-width: 960px; margin: 0 auto; padding: 8px; }
  .stage > video { display: none; }
  .stage > canvas { width: 100%; height: auto; border-radius: 12px;
                    background: #000; aspect-ratio: 4 / 3; }
  .status { display: flex; justify-content: space-between; padding: 8px 12px;
            font-size: 14px; color: #94a3b8; }
  .status b { color: #e2e8f0; }
  .err { background: #fef2f2; color: #b91c1c; padding: 12px 16px;
         border-radius: 8px; margin: 16px; font-weight: 500; }
  .controls { display: flex; gap: 8px; padding: 8px 12px; justify-content: center; }
  button.btn {
    background: #2563eb; color: white; border: none; padding: 10px 18px;
    border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: 600;
  }
  button.btn.secondary { background: #475569; }
  button.btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
</head>
<body>

<div id="errBox" class="err" style="display:none"></div>

<div class="stage">
  <video id="webcam" autoplay playsinline muted></video>
  <canvas id="output"></canvas>
</div>

<div class="status">
  <span>상태: <b id="statusText">초기화 중...</b></span>
  <span>FPS: <b id="fpsText">—</b></span>
</div>

<div class="controls">
  <button id="btnStart" class="btn" disabled>▶ 시작</button>
  <button id="btnStop" class="btn secondary" disabled>■ 정지</button>
</div>

<script type="module">
import {
  PoseLandmarker, FilesetResolver, DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

const video = document.getElementById('webcam');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d');
const statusText = document.getElementById('statusText');
const fpsText = document.getElementById('fpsText');
const errBox = document.getElementById('errBox');
const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');

let poseLandmarker = null;
let stream = null;
let running = false;
let lastVideoTime = -1;
let drawingUtils = null;
let fpsBuf = [];

function showErr(msg) {
  errBox.style.display = 'block';
  errBox.textContent = '⚠ ' + msg;
  statusText.textContent = '오류';
}
function setStatus(t) { statusText.textContent = t; }

async function initPose() {
  setStatus('MediaPipe 모델 로드 중...');
  try {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm");
    poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "GPU"
      },
      runningMode: "VIDEO",
      numPoses: 1
    });
    setStatus('모델 준비 완료 · 시작 버튼을 눌러주세요');
    btnStart.disabled = false;
  } catch (e) {
    showErr('MediaPipe 모델 로드 실패: ' + e.message);
  }
}

async function startCamera() {
  if (running) return;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    video.srcObject = stream;
    await new Promise((res) => { video.onloadeddata = res; });
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    drawingUtils = new DrawingUtils(ctx);
    running = true;
    btnStart.disabled = true;
    btnStop.disabled = false;
    setStatus('실행 중');
    requestAnimationFrame(loop);
  } catch (e) {
    showErr('카메라 접근 실패: ' + e.message + ' (브라우저 권한·HTTPS 확인)');
  }
}

function stopCamera() {
  running = false;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  btnStart.disabled = false;
  btnStop.disabled = true;
  setStatus('정지');
}

async function loop() {
  if (!running || !poseLandmarker) return;

  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    const ts = performance.now();
    const result = await poseLandmarker.detectForVideo(video, ts);

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // 좌우 반전 (셀카 mode — 사용자 동작이 자연스럽게 보이도록)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (result.landmarks && result.landmarks.length > 0) {
      for (const lm of result.landmarks) {
        drawingUtils.drawConnectors(lm, PoseLandmarker.POSE_CONNECTIONS, {
          color: '#FFFFFF', lineWidth: 3
        });
        drawingUtils.drawLandmarks(lm, {
          color: '#22c55e', radius: 4, lineWidth: 1
        });
      }
    }
    ctx.restore();

    // FPS 측정 (sliding 20-frame window)
    const now = performance.now();
    fpsBuf.push(now);
    while (fpsBuf.length > 20) fpsBuf.shift();
    if (fpsBuf.length > 2) {
      const fps = 1000 * (fpsBuf.length - 1) / (fpsBuf[fpsBuf.length - 1] - fpsBuf[0]);
      fpsText.textContent = fps.toFixed(1);
    }
  }
  requestAnimationFrame(loop);
}

btnStart.addEventListener('click', startCamera);
btnStop.addEventListener('click', stopCamera);
window.addEventListener('beforeunload', stopCamera);

initPose();
</script>

</body>
</html>
"""


def render():
    render_top_back("result", "camera_back")

    st.markdown(
        '<h1 class="screen-title">📷 실시간 자세 체크</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="screen-sub">카메라를 정면에 두고 페달링하면서 본인 모습을 확인하세요. '
        '(Phase 1 — skeleton 표시만, 자세 평가·피드백은 추후 단계)</p>',
        unsafe_allow_html=True,
    )

    components.html(_POSE_HTML, height=720, scrolling=False)

    st.markdown(
        '<p class="disclaimer">'
        '카메라 영상은 사용자 기기에서만 처리되며 서버로 전송·저장되지 않습니다.'
        '</p>',
        unsafe_allow_html=True,
    )
