"""실시간 자세 추적 + clinical metric cue (Phase 2).

Browser-side MediaPipe Pose Landmarker (Tasks Vision).
- 정면 카메라 1대
- 33-keypoint pose → 5개 임상 metric (JS 측에서 frame-by-frame 계산)
  · 골반 list   pelvic_list_deg
  · 트렁크 측방 기울임 trunk_lean_deg
  · 무릎 R/L valgus/varus knee_dev_R / knee_dev_L (normalized)
  · 발끝 R/L 방향 foot_R / foot_L (heel→toe vector angle)
  · 어깨 비대칭 shoulder_diff_deg (보조)
- Threshold 초과 시 해당 joint 빨간 강조 + 텍스트 cue
- 모든 처리 browser (WebGL/WASM) — 서버 부담 0

Threshold 기준 (PROTOCOL_v2 + ADR-001~003):
  pelvic_list   > ±3°  → "골반 (좌/우) 처짐" → AENE/NEAE 후보
  trunk_lean    > ±5°  → "허리 (좌/우) 기울임" → AENE/NEAE (low_back)
  knee_dev     > 0.06  → 정상 hip-ankle 라인에서 무릎이 ±6% leg-length 만큼 이탈
                          (안쪽 valgus → AENE 후보, 바깥 varus → ADNE 후보)
  foot_angle    > ±15° → toe-in/out (foot_align → AINE/NEAI)

iframe 우회: HF Space 의 inner iframe permissions-policy 가 camera 차단 시
            "새 탭에서 열기" 링크 표시 (window.top !== window 감지).
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
  .wrap { display: grid; grid-template-columns: 1fr 280px; gap: 12px;
          max-width: 1280px; margin: 0 auto; padding: 10px; }
  @media (max-width: 800px) { .wrap { grid-template-columns: 1fr; } }
  .stage { position: relative; }
  .stage > video { display: none; }
  .stage > canvas { width: 100%; height: auto; border-radius: 12px;
                    background: #000; aspect-ratio: 4 / 3; }
  .panel { background: #1e293b; border-radius: 12px; padding: 14px;
           display: flex; flex-direction: column; gap: 10px; }
  .metric { background: #0f172a; padding: 10px 12px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            font-size: 14px; border-left: 4px solid #475569; }
  .metric.ok    { border-left-color: #22c55e; }
  .metric.warn  { border-left-color: #f59e0b; }
  .metric.alert { border-left-color: #ef4444; background: #450a0a; }
  .metric .lbl { color: #cbd5e1; }
  .metric .val { font-weight: 700; color: #e2e8f0; font-variant-numeric: tabular-nums; }
  .status { display: flex; justify-content: space-between; padding: 8px 12px;
            font-size: 13px; color: #94a3b8; }
  .status b { color: #e2e8f0; }
  .err { background: #fef2f2; color: #b91c1c; padding: 12px 16px;
         border-radius: 8px; margin: 10px; font-weight: 500;
         line-height: 1.5; font-size: 14px; }
  .err a { color: #b91c1c; text-decoration: underline; font-weight: 700; }
  .controls { display: flex; gap: 8px; padding: 8px 12px; justify-content: center; }
  button.btn {
    background: #2563eb; color: white; border: none; padding: 10px 18px;
    border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: 600;
  }
  button.btn.secondary { background: #475569; }
  button.btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .cues { padding: 8px 12px; text-align: center; min-height: 40px;
          font-size: 15px; font-weight: 600; color: #f59e0b; }
  .cues.alert { color: #ef4444; }
  .cues.ok { color: #22c55e; }
</style>
</head>
<body>

<div id="errBox" class="err" style="display:none"></div>

<div class="wrap">
  <div class="stage">
    <video id="webcam" autoplay playsinline muted></video>
    <canvas id="output"></canvas>
  </div>

  <div class="panel">
    <div style="font-weight:700; color:#e2e8f0; font-size:14px;">
      📐 실시간 자세 지표
    </div>
    <div id="m_pelvic" class="metric">
      <span class="lbl">골반 list</span><span class="val">—</span>
    </div>
    <div id="m_trunk" class="metric">
      <span class="lbl">허리 기울임</span><span class="val">—</span>
    </div>
    <div id="m_knee_r" class="metric">
      <span class="lbl">오른 무릎</span><span class="val">—</span>
    </div>
    <div id="m_knee_l" class="metric">
      <span class="lbl">왼 무릎</span><span class="val">—</span>
    </div>
    <div id="m_foot_r" class="metric">
      <span class="lbl">오른 발끝</span><span class="val">—</span>
    </div>
    <div id="m_foot_l" class="metric">
      <span class="lbl">왼 발끝</span><span class="val">—</span>
    </div>
  </div>
</div>

<div id="cuesBox" class="cues ok">측정 준비 중...</div>

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
const cuesBox = document.getElementById('cuesBox');

// --- Threshold (PROTOCOL_v2 기반) ---
const TH = {
  pelvic_deg: 3.0,      // 골반 list
  trunk_deg: 5.0,       // 허리 측방 lean
  knee_dev: 0.06,       // hip-ankle 라인 대비 무릎 이탈 (normalize by leg length)
  foot_deg: 15.0,       // foot toe-in/out (heel→toe vector vs vertical)
  shoulder_deg: 4.0,    // 어깨 수평 차이 (보조)
};

let poseLandmarker = null;
let stream = null;
let running = false;
let lastVideoTime = -1;
let drawingUtils = null;
let fpsBuf = [];

function showErr(msg) {
  errBox.style.display = 'block';
  errBox.innerHTML = '⚠ ' + msg;
  statusText.textContent = '오류';
}
function setStatus(t) { statusText.textContent = t; }

// iframe 안에서 카메라 차단 가능성 사전 안내
function detectIframeBlock() {
  const inIframe = window.top !== window.self;
  const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  if (!hasMedia) {
    showErr('카메라 API 사용 불가 — 브라우저가 HTTPS 가 아니거나 너무 오래된 버전. ' +
            'Chrome / Edge / Safari 최신 사용 권장.');
    return true;
  }
  if (inIframe) {
    // iframe 안 + camera 권한 의심
    const directUrl = 'https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo';
    const hint = '<div style="font-weight:400;font-size:13px;margin-top:6px">' +
                 'iframe(임베드)에서 카메라가 차단될 수 있습니다. ' +
                 '문제 발생 시 <a href="' + directUrl + '" target="_blank">새 탭에서 직접 열기</a> 클릭.</div>';
    // 경고는 표시하되 진행은 허용
    errBox.style.display = 'block';
    errBox.innerHTML = '🔔 iframe 환경 감지 — 카메라 권한이 거부되면 ' +
      '<a href="' + directUrl + '" target="_blank">새 탭에서 직접 열기</a>를 사용하세요.';
    errBox.style.background = '#fef3c7';
    errBox.style.color = '#92400e';
  }
  return false;
}

async function initPose() {
  if (detectIframeBlock()) { return; }
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
    showErr('카메라 접근 실패: ' + e.message +
            '<br/>· 브라우저 카메라 권한이 차단되었는지 확인 (주소창 자물쇠 → 카메라 허용)' +
            '<br/>· 다른 앱이 카메라를 사용 중인지 확인' +
            '<br/>· HTTPS 가 아닌 페이지에서는 카메라 접근 불가');
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

// --- Metric 계산 helpers ---
// MediaPipe 33 landmarks (frontal view, mirrored — 좌우 반전 적용):
//   11: L shoulder, 12: R shoulder
//   23: L hip, 24: R hip
//   25: L knee, 26: R knee
//   27: L ankle, 28: R ankle
//   29: L heel, 30: R heel
//   31: L foot_index, 32: R foot_index
// 좌우 반전(셀카) 모드라서 사용자의 R 다리는 화면상 왼쪽에 보임 — 그래도 landmark index 자체는 anatomical (R index = 12/24/26/28/30/32)

function deg(rad) { return rad * 180 / Math.PI; }
function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }

function calcMetrics(lm) {
  // lm: 33 landmarks, each {x, y, z, visibility} in [0,1] normalized
  const Lsh = lm[11], Rsh = lm[12];
  const Lhip = lm[23], Rhip = lm[24];
  const Lkn = lm[25], Rkn = lm[26];
  const Lank = lm[27], Rank = lm[28];
  const Lheel = lm[29], Rheel = lm[30];
  const Lfoot = lm[31], Rfoot = lm[32];

  // 1. Pelvic list — hip L vs R y 차이 (atan2)
  const pelvic_deg = deg(Math.atan2(Rhip.y - Lhip.y, Rhip.x - Lhip.x));
  // 정의: +값 = R hip 가 더 낮음 (R-side drop)

  // 2. Trunk lean — shoulder midpoint vs hip midpoint x 차이
  const shMidX = (Lsh.x + Rsh.x) / 2;
  const shMidY = (Lsh.y + Rsh.y) / 2;
  const hipMidX = (Lhip.x + Rhip.x) / 2;
  const hipMidY = (Lhip.y + Rhip.y) / 2;
  const trunk_deg = deg(Math.atan2(shMidX - hipMidX, hipMidY - shMidY));
  // +값 = shoulder 가 R 쪽 (오른쪽 기울임)

  // 3. Knee deviation — hip-ankle 직선 대비 knee 가 얼마나 안쪽/바깥
  // perpendicular distance from knee to line (hip → ankle), signed
  function kneeDev(hip, knee, ankle) {
    const dx = ankle.x - hip.x, dy = ankle.y - hip.y;
    const len = Math.hypot(dx, dy) || 1e-6;
    // signed perpendicular: positive if knee is right of hip→ankle direction
    const signed = ((knee.x - hip.x) * dy - (knee.y - hip.y) * dx) / len;
    return signed;   // unit: normalized image coords (~0~1 scale)
  }
  // R 다리 (anatomical): hip 24, knee 26, ankle 28
  const knee_R_dev = kneeDev(Rhip, Rkn, Rank);
  // L 다리 (anatomical): hip 23, knee 25, ankle 27
  const knee_L_dev = kneeDev(Lhip, Lkn, Lank);

  // 부호 정규화: valgus(=무릎 안쪽 모임 = knee가 center 쪽으로 빠짐)을 + 로
  // anatomical R 다리는 right side. R-knee 가 R-hip-ankle 라인 왼쪽으로(=center쪽) 빠지면 valgus.
  // signed sign 은 cross product 방향이라 hip→ankle 의 진행 방향에 의존. 단순화: 절댓값 + center 방향 판정
  const centerX = (Lhip.x + Rhip.x) / 2;
  const knee_R_valgus = (centerX - Rkn.x);  // anatomical R: 중심까지 왼쪽으로 빠지면 +
  const knee_L_valgus = (Lkn.x - centerX);  // anatomical L: 중심까지 오른쪽으로 빠지면 +
  // normalize by leg length (hip→ankle vertical extent)
  const legR_len = Math.abs(Rank.y - Rhip.y) || 0.4;
  const legL_len = Math.abs(Lank.y - Lhip.y) || 0.4;
  const knee_R_norm = knee_R_valgus / legR_len;
  const knee_L_norm = knee_L_valgus / legL_len;

  // 4. Foot direction — heel → foot_index vector vs straight-down (toe-in/out)
  // image: vertical axis = y. heel below hip, foot_index typically forward.
  // 정면 view 에서는 toe-in/out 이 x 좌표로 나타남.
  // angle: atan2(foot_index.x - heel.x, ...) — 정면일 때 heel 과 toe 가 거의 같은 y 라 noisy
  // 보수적: foot_index.x - heel.x  의 normalized signed value
  // toe-in = 발끝이 안쪽으로 (R-foot toe_index.x > heel.x = 안쪽, anatomical R 시점)
  const foot_R_dx = Rfoot.x - Rheel.x;   // anatomical R: 안쪽으로 = center 방향 = +x decrease (R 쪽이 화면상 우측이라 안쪽 = x 감소). reverse:
  // 단순화: anatomical R foot — center 대비 foot_index 위치
  const foot_R_offset = (centerX - Rfoot.x) - (centerX - Rheel.x);   // = Rheel.x - Rfoot.x; + → toe-in
  const foot_L_offset = (Lfoot.x - centerX) - (Lheel.x - centerX);   // = Lfoot.x - Lheel.x; + → toe-in
  // normalize by foot length
  const footR_len = dist(Rheel, Rfoot) || 0.1;
  const footL_len = dist(Lheel, Lfoot) || 0.1;
  const foot_R_deg = deg(Math.asin(Math.max(-1, Math.min(1, foot_R_offset / footR_len))));
  const foot_L_deg = deg(Math.asin(Math.max(-1, Math.min(1, foot_L_offset / footL_len))));

  // 5. Shoulder asymmetry (보조)
  const shoulder_deg = deg(Math.atan2(Rsh.y - Lsh.y, Rsh.x - Lsh.x));

  return {
    pelvic_deg,
    trunk_deg,
    knee_R_norm, knee_L_norm,
    foot_R_deg, foot_L_deg,
    shoulder_deg,
  };
}

function classify(value, threshold) {
  const abs = Math.abs(value);
  if (abs < threshold * 0.6) return 'ok';
  if (abs < threshold) return 'warn';
  return 'alert';
}

function setMetric(el, label, valueStr, cls) {
  el.className = 'metric ' + cls;
  el.innerHTML = '<span class="lbl">' + label + '</span><span class="val">' + valueStr + '</span>';
}

function updateUI(m) {
  // 골반 list
  setMetric(document.getElementById('m_pelvic'),
    '골반 list', (m.pelvic_deg >= 0 ? '+' : '') + m.pelvic_deg.toFixed(1) + '°',
    classify(m.pelvic_deg, TH.pelvic_deg));

  setMetric(document.getElementById('m_trunk'),
    '허리 기울임', (m.trunk_deg >= 0 ? '+' : '') + m.trunk_deg.toFixed(1) + '°',
    classify(m.trunk_deg, TH.trunk_deg));

  setMetric(document.getElementById('m_knee_r'),
    '오른 무릎', (m.knee_R_norm * 100).toFixed(1) + '%',
    classify(m.knee_R_norm, TH.knee_dev));
  setMetric(document.getElementById('m_knee_l'),
    '왼 무릎', (m.knee_L_norm * 100).toFixed(1) + '%',
    classify(m.knee_L_norm, TH.knee_dev));

  setMetric(document.getElementById('m_foot_r'),
    '오른 발끝', (m.foot_R_deg >= 0 ? 'in ' : 'out ') + Math.abs(m.foot_R_deg).toFixed(0) + '°',
    classify(m.foot_R_deg, TH.foot_deg));
  setMetric(document.getElementById('m_foot_l'),
    '왼 발끝', (m.foot_L_deg >= 0 ? 'in ' : 'out ') + Math.abs(m.foot_L_deg).toFixed(0) + '°',
    classify(m.foot_L_deg, TH.foot_deg));

  // Cue text — 가장 심한 것 1-2 개만 표시
  const cues = [];
  if (Math.abs(m.pelvic_deg) >= TH.pelvic_deg) {
    cues.push(m.pelvic_deg > 0 ? '⚠ 오른쪽 골반 처짐' : '⚠ 왼쪽 골반 처짐');
  }
  if (Math.abs(m.trunk_deg) >= TH.trunk_deg) {
    cues.push(m.trunk_deg > 0 ? '⚠ 허리가 오른쪽으로 기움' : '⚠ 허리가 왼쪽으로 기움');
  }
  if (Math.abs(m.knee_R_norm) >= TH.knee_dev) {
    cues.push(m.knee_R_norm > 0 ? '⚠ 오른 무릎 안쪽으로' : '⚠ 오른 무릎 바깥으로');
  }
  if (Math.abs(m.knee_L_norm) >= TH.knee_dev) {
    cues.push(m.knee_L_norm > 0 ? '⚠ 왼 무릎 안쪽으로' : '⚠ 왼 무릎 바깥으로');
  }
  if (Math.abs(m.foot_R_deg) >= TH.foot_deg) {
    cues.push(m.foot_R_deg > 0 ? '⚠ 오른 발끝 안으로' : '⚠ 오른 발끝 바깥으로');
  }
  if (Math.abs(m.foot_L_deg) >= TH.foot_deg) {
    cues.push(m.foot_L_deg > 0 ? '⚠ 왼 발끝 안으로' : '⚠ 왼 발끝 바깥으로');
  }
  if (cues.length === 0) {
    cuesBox.className = 'cues ok';
    cuesBox.textContent = '✓ 자세 좋음';
  } else {
    cuesBox.className = 'cues alert';
    cuesBox.textContent = cues.slice(0, 2).join('   ·   ');
  }
}

function drawProblemMarkers(lm, m) {
  const W = canvas.width, H = canvas.height;
  // 좌우 반전된 좌표계에서 그리고 있으므로 동일하게 반영
  function px(p) {
    // 캔버스가 이미 ctx.scale(-1,1) + translate 적용되어 있음 — landmark x 는 원본 video 좌표라 같이 변환됨
    return [p.x * W, p.y * H];
  }
  function circle(p, color, r=14) {
    const [x, y] = px(p);
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.stroke();
  }
  // 골반
  if (Math.abs(m.pelvic_deg) >= TH.pelvic_deg) {
    circle(lm[23], '#ef4444', 16);  // L hip
    circle(lm[24], '#ef4444', 16);  // R hip
  }
  // 무릎 R
  if (Math.abs(m.knee_R_norm) >= TH.knee_dev) {
    circle(lm[26], '#ef4444', 18);
  }
  // 무릎 L
  if (Math.abs(m.knee_L_norm) >= TH.knee_dev) {
    circle(lm[25], '#ef4444', 18);
  }
  // 발끝 R
  if (Math.abs(m.foot_R_deg) >= TH.foot_deg) {
    circle(lm[32], '#ef4444', 14);
  }
  // 발끝 L
  if (Math.abs(m.foot_L_deg) >= TH.foot_deg) {
    circle(lm[31], '#ef4444', 14);
  }
  // 트렁크 — shoulder midline에 빨간선
  if (Math.abs(m.trunk_deg) >= TH.trunk_deg) {
    const Lsh = lm[11], Rsh = lm[12];
    const Lhip = lm[23], Rhip = lm[24];
    const sx = ((Lsh.x + Rsh.x) / 2) * W;
    const sy = ((Lsh.y + Rsh.y) / 2) * H;
    const hx = ((Lhip.x + Rhip.x) / 2) * W;
    const hy = ((Lhip.y + Rhip.y) / 2) * H;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(hx, hy);
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 5;
    ctx.stroke();
  }
}

async function loop() {
  if (!running || !poseLandmarker) return;

  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    const ts = performance.now();
    const result = await poseLandmarker.detectForVideo(video, ts);

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // 좌우 반전 (셀카 mode)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (result.landmarks && result.landmarks.length > 0) {
      const lm = result.landmarks[0];
      drawingUtils.drawConnectors(lm, PoseLandmarker.POSE_CONNECTIONS, {
        color: '#FFFFFF', lineWidth: 3
      });
      drawingUtils.drawLandmarks(lm, {
        color: '#22c55e', radius: 4, lineWidth: 1
      });

      const m = calcMetrics(lm);
      drawProblemMarkers(lm, m);
      updateUI(m);
    }
    ctx.restore();

    // FPS
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
        '<p class="screen-sub">정면 카메라 앞에서 페달링하면 자세를 분석해 알려드립니다. '
        '카메라가 안 뜨면 <a href="https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo" target="_blank">'
        '새 탭에서 직접 열기</a> 를 사용하세요.</p>',
        unsafe_allow_html=True,
    )

    components.html(_POSE_HTML, height=900, scrolling=True)

    st.markdown(
        '<p class="disclaimer">'
        '카메라 영상은 사용자 기기에서만 처리되며 서버로 전송·저장되지 않습니다. '
        '본 화면의 자세 평가는 운동 보조 가이드이며 의학적 진단을 대신하지 않습니다.'
        '</p>',
        unsafe_allow_html=True,
    )
