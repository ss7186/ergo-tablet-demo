"""실시간 자세 추적 + 세션 분석 + 다음 추천 (Phase 3).

Browser-side MediaPipe Pose Landmarker (Tasks Vision).
- Live: 33-keypoint skeleton overlay + 5개 임상 metric + cue
- Session recording: 모든 frame 의 metric 을 buffer 에 저장 (privacy: browser only)
- 정지 → Summary view:
    · 평균 metric 표
    · L/R asymmetry index
    · Chart.js trend graph (pelvic / knee R/L over time)
    · 패턴 자동 분류 → PROTOCOL_v2 prescription_matrix lookup → 다음 condition 추천
    · CSV export (local download)
- 모든 처리 browser (WebGL/WASM/JS) — 서버 부담 0, 영상 미전송

추천 알고리즘 (JS 측):
  1. session mean of each metric
  2. priority order: pelvic > trunk > knee > foot
  3. side: sign of mean (pelvic > 0 = R-drop = right side)
  4. lookup mapping["prescription_matrix"][symptom][side]
  5. display name_kr + alias_kr (와이드·토인 등) from conditions.json

Phase 4 (TODO):
  - cycle 분할 (페달 회전 detection via hip flexion peak 또는 외부 IMU sync)
  - per-cycle SI 계산 (현재는 전체 session mean)
  - 환자 ID + IRB 보호 세션 히스토리 backend (별도 IRB amendment 필요)
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from components.common import render_top_back
from utils.data_loader import load_conditions, load_mapping


# ── HTML template (placeholder __XXX__ 형태로 Python 측 데이터 주입) ──
_POSE_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
  .controls { display: flex; gap: 8px; padding: 8px 12px; justify-content: center; flex-wrap: wrap; }
  button.btn {
    background: #2563eb; color: white; border: none; padding: 10px 18px;
    border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: 600;
  }
  button.btn.secondary { background: #475569; }
  button.btn.success { background: #16a34a; }
  button.btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .cues { padding: 8px 12px; text-align: center; min-height: 40px;
          font-size: 15px; font-weight: 600; color: #f59e0b; }
  .cues.alert { color: #ef4444; }
  .cues.ok { color: #22c55e; }

  /* Summary view */
  .summary { display: none; padding: 16px; max-width: 1100px; margin: 0 auto; }
  .summary.visible { display: block; }
  .summary h2 { margin: 0 0 14px; font-size: 22px; color: #e2e8f0; }
  .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 18px; }
  .stat-card { background: #1e293b; padding: 14px; border-radius: 10px; }
  .stat-card .lbl { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
  .stat-card .val { font-size: 22px; font-weight: 700; color: #e2e8f0; font-variant-numeric: tabular-nums; }
  .stat-card .sub { font-size: 12px; color: #64748b; margin-top: 4px; }
  .reco-box { background: #1e40af; border: 2px solid #3b82f6; padding: 18px;
              border-radius: 12px; margin: 16px 0; }
  .reco-box .reco-label { color: #bfdbfe; font-size: 13px; margin-bottom: 6px; }
  .reco-box .reco-cond { color: white; font-size: 24px; font-weight: 700; margin-bottom: 6px; }
  .reco-box .reco-reason { color: #dbeafe; font-size: 13px; line-height: 1.5; }
  .reco-box.neutral { background: #334155; border-color: #64748b; }
  .reco-box.neutral .reco-cond { color: #e2e8f0; }
  .reco-box.neutral .reco-label { color: #cbd5e1; }
  .reco-box.neutral .reco-reason { color: #cbd5e1; }
  .chart-wrap { background: #1e293b; padding: 14px; border-radius: 10px; margin-bottom: 16px; }
  .chart-wrap h3 { margin: 0 0 10px; font-size: 14px; color: #cbd5e1; font-weight: 600; }
  .chart-wrap canvas { max-height: 220px; }
</style>
</head>
<body>

<div id="errBox" class="err" style="display:none"></div>

<!-- ── Live view ── -->
<div id="liveView">
  <div class="wrap">
    <div class="stage">
      <video id="webcam" autoplay playsinline muted></video>
      <canvas id="output"></canvas>
    </div>

    <div class="panel">
      <div style="font-weight:700; color:#e2e8f0; font-size:14px;">
        📐 실시간 자세 지표
      </div>
      <div id="m_pelvic" class="metric"><span class="lbl">골반 list</span><span class="val">—</span></div>
      <div id="m_trunk" class="metric"><span class="lbl">허리 기울임</span><span class="val">—</span></div>
      <div id="m_knee_r" class="metric"><span class="lbl">오른 무릎</span><span class="val">—</span></div>
      <div id="m_knee_l" class="metric"><span class="lbl">왼 무릎</span><span class="val">—</span></div>
      <div id="m_foot_r" class="metric"><span class="lbl">오른 발끝</span><span class="val">—</span></div>
      <div id="m_foot_l" class="metric"><span class="lbl">왼 발끝</span><span class="val">—</span></div>
    </div>
  </div>

  <div id="cuesBox" class="cues ok">측정 준비 중...</div>

  <div class="status">
    <span>상태: <b id="statusText">초기화 중...</b></span>
    <span>FPS: <b id="fpsText">—</b></span>
    <span>샘플 수: <b id="sampleText">0</b></span>
  </div>

  <div class="controls">
    <button id="btnStart" class="btn" disabled>▶ 시작</button>
    <button id="btnStop" class="btn secondary" disabled>■ 정지 · 분석</button>
  </div>
</div>

<!-- ── Summary view ── -->
<div id="summaryView" class="summary">
  <h2>📊 세션 분석</h2>

  <div id="recoBox" class="reco-box">
    <div class="reco-label">다음 세션 추천</div>
    <div class="reco-cond" id="recoName">—</div>
    <div class="reco-reason" id="recoReason">—</div>
  </div>

  <div class="summary-grid">
    <div class="stat-card"><div class="lbl">측정 시간</div><div class="val" id="s_duration">—</div></div>
    <div class="stat-card"><div class="lbl">샘플 수</div><div class="val" id="s_samples">—</div></div>
    <div class="stat-card"><div class="lbl">평균 FPS</div><div class="val" id="s_fps">—</div></div>
  </div>

  <h3 style="color:#cbd5e1; margin: 16px 0 8px; font-size: 14px;">평균 자세 지표 (세션 전체)</h3>
  <div class="summary-grid">
    <div class="stat-card"><div class="lbl">골반 list</div><div class="val" id="s_pelvic">—</div><div class="sub" id="s_pelvic_sub">—</div></div>
    <div class="stat-card"><div class="lbl">허리 기울임</div><div class="val" id="s_trunk">—</div><div class="sub" id="s_trunk_sub">—</div></div>
    <div class="stat-card"><div class="lbl">오른 무릎 valgus</div><div class="val" id="s_kneeR">—</div></div>
    <div class="stat-card"><div class="lbl">왼 무릎 valgus</div><div class="val" id="s_kneeL">—</div></div>
    <div class="stat-card"><div class="lbl">오른 발끝</div><div class="val" id="s_footR">—</div></div>
    <div class="stat-card"><div class="lbl">왼 발끝</div><div class="val" id="s_footL">—</div></div>
  </div>

  <div class="chart-wrap">
    <h3>골반 / 허리 시간 변화</h3>
    <canvas id="chart_trunk"></canvas>
  </div>
  <div class="chart-wrap">
    <h3>무릎 R / L 시간 변화 (valgus%)</h3>
    <canvas id="chart_knee"></canvas>
  </div>

  <div class="controls">
    <button id="btnNewSession" class="btn">▶ 새 세션 시작</button>
    <button id="btnExportCsv" class="btn secondary">📥 CSV 다운로드</button>
  </div>
</div>

<script type="module">
import {
  PoseLandmarker, FilesetResolver, DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

// ── Python 측 주입 데이터 ──
const PRESCRIPTION_MATRIX = __PRESCRIPTION_MATRIX__;
const CONDITION_NAMES = __CONDITION_NAMES__;       // {ADAD: "내로우 · 롤인", ...}
const CONDITION_ALIASES = __CONDITION_ALIASES__;   // {ADAD: "ADI", ...}

const video = document.getElementById('webcam');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d');
const statusText = document.getElementById('statusText');
const fpsText = document.getElementById('fpsText');
const sampleText = document.getElementById('sampleText');
const errBox = document.getElementById('errBox');
const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const btnNewSession = document.getElementById('btnNewSession');
const btnExportCsv = document.getElementById('btnExportCsv');
const cuesBox = document.getElementById('cuesBox');
const liveView = document.getElementById('liveView');
const summaryView = document.getElementById('summaryView');

const TH = {
  pelvic_deg: 3.0,
  trunk_deg: 5.0,
  knee_dev: 0.06,
  foot_deg: 15.0,
  shoulder_deg: 4.0,
};

// 패턴 우선순위 (severity 가 높은 metric 부터 → next condition 결정)
// 임계값 절대값 대비 ratio 가 가장 큰 metric 선정
const PATTERN_PRIORITY = ['pelvic', 'trunk', 'knee', 'foot'];

let poseLandmarker = null;
let stream = null;
let running = false;
let lastVideoTime = -1;
let drawingUtils = null;
let fpsBuf = [];

// ── Session recording buffer ──
let sessionBuf = [];   // [{t, pelvic, trunk, kneeR, kneeL, footR, footL, shoulder}, ...]
let sessionStartTs = 0;
let chartTrunk = null, chartKnee = null;

function showErr(msg, isWarning = false) {
  errBox.style.display = 'block';
  errBox.innerHTML = (isWarning ? '🔔 ' : '⚠ ') + msg;
  if (isWarning) {
    errBox.style.background = '#fef3c7';
    errBox.style.color = '#92400e';
  }
  if (!isWarning) { statusText.textContent = '오류'; }
}
function setStatus(t) { statusText.textContent = t; }

function detectIframeBlock() {
  const inIframe = window.top !== window.self;
  const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  if (!hasMedia) {
    showErr('카메라 API 사용 불가 — 브라우저가 HTTPS 가 아니거나 너무 오래된 버전. Chrome / Edge / Safari 최신 사용 권장.');
    return true;
  }
  if (inIframe) {
    const directUrl = 'https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo';
    showErr('iframe 환경 — 카메라 권한이 거부되면 <a href="' + directUrl + '" target="_blank">새 탭에서 직접 열기</a>를 사용하세요.', true);
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
    sessionBuf = [];
    sessionStartTs = performance.now();
    sampleText.textContent = '0';
    btnStart.disabled = true;
    btnStop.disabled = false;
    setStatus('실행 중 · 세션 기록 중');
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
  if (sessionBuf.length >= 30) {  // 약 1초 이상 기록되면 summary 표시
    showSummary();
  } else if (sessionBuf.length > 0) {
    setStatus('샘플이 너무 적습니다 (' + sessionBuf.length + '개) — 더 길게 측정해주세요');
  }
}

// ── Metric 계산 (Phase 2 와 동일) ──
function deg(rad) { return rad * 180 / Math.PI; }
function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }

function calcMetrics(lm) {
  const Lsh = lm[11], Rsh = lm[12];
  const Lhip = lm[23], Rhip = lm[24];
  const Lkn = lm[25], Rkn = lm[26];
  const Lank = lm[27], Rank = lm[28];
  const Lheel = lm[29], Rheel = lm[30];
  const Lfoot = lm[31], Rfoot = lm[32];

  const pelvic_deg = deg(Math.atan2(Rhip.y - Lhip.y, Rhip.x - Lhip.x));
  const shMidX = (Lsh.x + Rsh.x) / 2, shMidY = (Lsh.y + Rsh.y) / 2;
  const hipMidX = (Lhip.x + Rhip.x) / 2, hipMidY = (Lhip.y + Rhip.y) / 2;
  const trunk_deg = deg(Math.atan2(shMidX - hipMidX, hipMidY - shMidY));

  const centerX = (Lhip.x + Rhip.x) / 2;
  const knee_R_valgus = (centerX - Rkn.x);
  const knee_L_valgus = (Lkn.x - centerX);
  const legR_len = Math.abs(Rank.y - Rhip.y) || 0.4;
  const legL_len = Math.abs(Lank.y - Lhip.y) || 0.4;
  const knee_R_norm = knee_R_valgus / legR_len;
  const knee_L_norm = knee_L_valgus / legL_len;

  const foot_R_offset = Rheel.x - Rfoot.x;
  const foot_L_offset = Lfoot.x - Lheel.x;
  const footR_len = dist(Rheel, Rfoot) || 0.1;
  const footL_len = dist(Lheel, Lfoot) || 0.1;
  const foot_R_deg = deg(Math.asin(Math.max(-1, Math.min(1, foot_R_offset / footR_len))));
  const foot_L_deg = deg(Math.asin(Math.max(-1, Math.min(1, foot_L_offset / footL_len))));

  const shoulder_deg = deg(Math.atan2(Rsh.y - Lsh.y, Rsh.x - Lsh.x));

  return { pelvic_deg, trunk_deg, knee_R_norm, knee_L_norm, foot_R_deg, foot_L_deg, shoulder_deg };
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

  const cues = [];
  if (Math.abs(m.pelvic_deg) >= TH.pelvic_deg)
    cues.push(m.pelvic_deg > 0 ? '⚠ 오른쪽 골반 처짐' : '⚠ 왼쪽 골반 처짐');
  if (Math.abs(m.trunk_deg) >= TH.trunk_deg)
    cues.push(m.trunk_deg > 0 ? '⚠ 허리가 오른쪽으로 기움' : '⚠ 허리가 왼쪽으로 기움');
  if (Math.abs(m.knee_R_norm) >= TH.knee_dev)
    cues.push(m.knee_R_norm > 0 ? '⚠ 오른 무릎 안쪽으로' : '⚠ 오른 무릎 바깥으로');
  if (Math.abs(m.knee_L_norm) >= TH.knee_dev)
    cues.push(m.knee_L_norm > 0 ? '⚠ 왼 무릎 안쪽으로' : '⚠ 왼 무릎 바깥으로');
  if (Math.abs(m.foot_R_deg) >= TH.foot_deg)
    cues.push(m.foot_R_deg > 0 ? '⚠ 오른 발끝 안으로' : '⚠ 오른 발끝 바깥으로');
  if (Math.abs(m.foot_L_deg) >= TH.foot_deg)
    cues.push(m.foot_L_deg > 0 ? '⚠ 왼 발끝 안으로' : '⚠ 왼 발끝 바깥으로');
  if (cues.length === 0) { cuesBox.className = 'cues ok'; cuesBox.textContent = '✓ 자세 좋음'; }
  else { cuesBox.className = 'cues alert'; cuesBox.textContent = cues.slice(0, 2).join('   ·   '); }
}

function drawProblemMarkers(lm, m) {
  const W = canvas.width, H = canvas.height;
  function px(p) { return [p.x * W, p.y * H]; }
  function circle(p, color, r=14) {
    const [x, y] = px(p);
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.strokeStyle = color; ctx.lineWidth = 4; ctx.stroke();
  }
  if (Math.abs(m.pelvic_deg) >= TH.pelvic_deg) {
    circle(lm[23], '#ef4444', 16); circle(lm[24], '#ef4444', 16);
  }
  if (Math.abs(m.knee_R_norm) >= TH.knee_dev) circle(lm[26], '#ef4444', 18);
  if (Math.abs(m.knee_L_norm) >= TH.knee_dev) circle(lm[25], '#ef4444', 18);
  if (Math.abs(m.foot_R_deg) >= TH.foot_deg) circle(lm[32], '#ef4444', 14);
  if (Math.abs(m.foot_L_deg) >= TH.foot_deg) circle(lm[31], '#ef4444', 14);
  if (Math.abs(m.trunk_deg) >= TH.trunk_deg) {
    const Lsh = lm[11], Rsh = lm[12], Lhip = lm[23], Rhip = lm[24];
    const sx = ((Lsh.x + Rsh.x) / 2) * W, sy = ((Lsh.y + Rsh.y) / 2) * H;
    const hx = ((Lhip.x + Rhip.x) / 2) * W, hy = ((Lhip.y + Rhip.y) / 2) * H;
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(hx, hy);
    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 5; ctx.stroke();
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
    ctx.translate(canvas.width, 0); ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    if (result.landmarks && result.landmarks.length > 0) {
      const lm = result.landmarks[0];
      drawingUtils.drawConnectors(lm, PoseLandmarker.POSE_CONNECTIONS, { color: '#FFFFFF', lineWidth: 3 });
      drawingUtils.drawLandmarks(lm, { color: '#22c55e', radius: 4, lineWidth: 1 });
      const m = calcMetrics(lm);
      drawProblemMarkers(lm, m);
      updateUI(m);
      // Buffer push
      sessionBuf.push({
        t: (ts - sessionStartTs) / 1000,
        pelvic: m.pelvic_deg, trunk: m.trunk_deg,
        kneeR: m.knee_R_norm * 100, kneeL: m.knee_L_norm * 100,
        footR: m.foot_R_deg, footL: m.foot_L_deg,
        shoulder: m.shoulder_deg,
      });
      sampleText.textContent = String(sessionBuf.length);
    }
    ctx.restore();

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

// ── Summary view ──
function mean(arr) { return arr.reduce((a,b) => a+b, 0) / arr.length; }

function detectPattern(stats) {
  // 가장 심한 metric 1개 (threshold 대비 ratio) 기준으로 symptom + side 결정
  const candidates = [
    { key: 'pelvic',  symptom: 'hip_pelvis',  value: stats.pelvic,
      side: stats.pelvic > 0 ? 'right' : 'left',
      ratio: Math.abs(stats.pelvic) / TH.pelvic_deg },
    { key: 'trunk',   symptom: 'low_back',    value: stats.trunk,
      side: stats.trunk > 0 ? 'right' : 'left',
      ratio: Math.abs(stats.trunk) / TH.trunk_deg },
    { key: 'kneeR',   symptom: stats.kneeR > 0 ? 'knee_medial' : 'knee_lateral', value: stats.kneeR,
      side: 'right',
      ratio: Math.abs(stats.kneeR / 100) / TH.knee_dev },
    { key: 'kneeL',   symptom: stats.kneeL > 0 ? 'knee_medial' : 'knee_lateral', value: stats.kneeL,
      side: 'left',
      ratio: Math.abs(stats.kneeL / 100) / TH.knee_dev },
    { key: 'footR',   symptom: 'foot_align',  value: stats.footR,
      side: 'right',
      ratio: Math.abs(stats.footR) / TH.foot_deg },
    { key: 'footL',   symptom: 'foot_align',  value: stats.footL,
      side: 'left',
      ratio: Math.abs(stats.footL) / TH.foot_deg },
  ];
  // 임계값 (ratio≥1) 넘은 후보만
  const above = candidates.filter(c => c.ratio >= 1);
  if (above.length === 0) {
    return { symptom: null, side: null, ratio: 0, condition: 'NENE',
             reason: '큰 비대칭 검출되지 않음 (모든 지표 임계값 이내). 현재 자세 양호 — 기본 모드 유지 권장.' };
  }
  above.sort((a, b) => b.ratio - a.ratio);
  const top = above[0];
  // foot 가 양측 모두 임계 초과면 both
  if (top.symptom === 'foot_align') {
    const rR = candidates.find(c => c.key === 'footR').ratio;
    const rL = candidates.find(c => c.key === 'footL').ratio;
    if (rR >= 1 && rL >= 1) top.side = 'both';
  }
  const cond = (PRESCRIPTION_MATRIX[top.symptom] && PRESCRIPTION_MATRIX[top.symptom][top.side]) || 'NENE';
  const sideKr = { right: '오른쪽', left: '왼쪽', both: '양쪽' }[top.side] || '';
  const sympKr = {
    hip_pelvis: '골반 처짐',
    knee_medial: '무릎 안쪽 이탈',
    knee_lateral: '무릎 바깥 이탈',
    low_back: '허리 기울임',
    foot_align: '발끝 회전',
  }[top.symptom] || '';
  return {
    symptom: top.symptom, side: top.side, ratio: top.ratio,
    condition: cond,
    reason: '주된 비대칭: ' + sideKr + ' ' + sympKr +
            ' (임계값 대비 ' + top.ratio.toFixed(1) + '× — ' +
            (top.value).toFixed(1) + (top.key.startsWith('knee') ? '%' : '°') + ')',
  };
}

function showSummary() {
  liveView.style.display = 'none';
  summaryView.classList.add('visible');

  const stats = {
    pelvic: mean(sessionBuf.map(s => s.pelvic)),
    trunk:  mean(sessionBuf.map(s => s.trunk)),
    kneeR:  mean(sessionBuf.map(s => s.kneeR)),
    kneeL:  mean(sessionBuf.map(s => s.kneeL)),
    footR:  mean(sessionBuf.map(s => s.footR)),
    footL:  mean(sessionBuf.map(s => s.footL)),
  };
  const duration = sessionBuf[sessionBuf.length-1].t;
  document.getElementById('s_duration').textContent = duration.toFixed(1) + '초';
  document.getElementById('s_samples').textContent = String(sessionBuf.length);
  document.getElementById('s_fps').textContent = (sessionBuf.length / duration).toFixed(1);

  function fmtDeg(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '°'; }
  function fmtPct(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
  function fmtSide(v, posLabel, negLabel) {
    if (Math.abs(v) < 0.5) return '편차 없음';
    return v > 0 ? posLabel : negLabel;
  }
  document.getElementById('s_pelvic').textContent = fmtDeg(stats.pelvic);
  document.getElementById('s_pelvic_sub').textContent = fmtSide(stats.pelvic, '우측 처짐 우세', '좌측 처짐 우세');
  document.getElementById('s_trunk').textContent  = fmtDeg(stats.trunk);
  document.getElementById('s_trunk_sub').textContent  = fmtSide(stats.trunk, '우측 기울임', '좌측 기울임');
  document.getElementById('s_kneeR').textContent  = fmtPct(stats.kneeR);
  document.getElementById('s_kneeL').textContent  = fmtPct(stats.kneeL);
  document.getElementById('s_footR').textContent  = fmtDeg(stats.footR);
  document.getElementById('s_footL').textContent  = fmtDeg(stats.footL);

  // Pattern → recommendation
  const reco = detectPattern(stats);
  const recoBox = document.getElementById('recoBox');
  const condName = CONDITION_NAMES[reco.condition] || reco.condition;
  const condAlias = CONDITION_ALIASES[reco.condition] || '';
  document.getElementById('recoName').textContent = condName + (condAlias ? ' (' + condAlias + ')' : '');
  document.getElementById('recoReason').textContent = reco.reason;
  recoBox.className = 'reco-box' + (reco.condition === 'NENE' ? ' neutral' : '');

  // Charts
  const labels = sessionBuf.map(s => s.t.toFixed(1));
  if (chartTrunk) chartTrunk.destroy();
  if (chartKnee) chartKnee.destroy();
  const chartOpts = {
    responsive: true,
    animation: false,
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
    scales: {
      x: { ticks: { color: '#94a3b8', maxTicksLimit: 8 }, grid: { color: '#334155' } },
      y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
    }
  };
  chartTrunk = new Chart(document.getElementById('chart_trunk'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: '골반 list (°)', data: sessionBuf.map(s => s.pelvic), borderColor: '#f59e0b', borderWidth: 1.5, pointRadius: 0 },
        { label: '허리 기울임 (°)', data: sessionBuf.map(s => s.trunk), borderColor: '#3b82f6', borderWidth: 1.5, pointRadius: 0 },
      ]
    },
    options: chartOpts,
  });
  chartKnee = new Chart(document.getElementById('chart_knee'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: '오른 무릎 valgus (%)', data: sessionBuf.map(s => s.kneeR), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0 },
        { label: '왼 무릎 valgus (%)', data: sessionBuf.map(s => s.kneeL), borderColor: '#22c55e', borderWidth: 1.5, pointRadius: 0 },
      ]
    },
    options: chartOpts,
  });
}

function backToLive() {
  liveView.style.display = '';
  summaryView.classList.remove('visible');
  sessionBuf = [];
  sampleText.textContent = '0';
  setStatus('대기 — 시작 버튼을 눌러주세요');
}

function exportCsv() {
  if (sessionBuf.length === 0) return;
  const header = 'time_s,pelvic_deg,trunk_deg,knee_R_pct,knee_L_pct,foot_R_deg,foot_L_deg,shoulder_deg\\n';
  const rows = sessionBuf.map(s =>
    [s.t, s.pelvic, s.trunk, s.kneeR, s.kneeL, s.footR, s.footL, s.shoulder]
      .map(v => v.toFixed(3)).join(',')
  );
  const blob = new Blob([header + rows.join('\\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ergo_session_' + new Date().toISOString().replace(/[:.]/g, '-') + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}

btnStart.addEventListener('click', startCamera);
btnStop.addEventListener('click', stopCamera);
btnNewSession.addEventListener('click', backToLive);
btnExportCsv.addEventListener('click', exportCsv);
window.addEventListener('beforeunload', () => { if (running) stopCamera(); });

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
        '정지하면 세션 분석과 다음 추천 모드를 제시합니다. '
        '카메라가 안 뜨면 <a href="https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo" target="_blank">'
        '새 탭에서 직접 열기</a>.</p>',
        unsafe_allow_html=True,
    )

    # ── Python 측 데이터 (prescription_matrix + condition labels) 를 HTML 에 주입 ──
    conditions = load_conditions()
    mapping = load_mapping()
    prescription = mapping.get("prescription_matrix", {})
    # 'unknown' fallback 등 _doc 키 제거
    prescription = {k: v for k, v in prescription.items() if not k.startswith("_")}
    cond_names = {k: v.get("name_kr", k) for k, v in conditions.items() if not k.startswith("_")}
    cond_aliases = {k: v.get("alias_kr", "") for k, v in conditions.items() if not k.startswith("_")}

    html = (_POSE_HTML
            .replace("__PRESCRIPTION_MATRIX__", json.dumps(prescription, ensure_ascii=False))
            .replace("__CONDITION_NAMES__", json.dumps(cond_names, ensure_ascii=False))
            .replace("__CONDITION_ALIASES__", json.dumps(cond_aliases, ensure_ascii=False)))

    components.html(html, height=1100, scrolling=True)

    st.markdown(
        '<p class="disclaimer">'
        '카메라 영상은 사용자 기기에서만 처리되며 서버로 전송·저장되지 않습니다. '
        '세션 데이터(CSV)는 로컬에만 다운로드됩니다. '
        '본 화면의 자세 평가는 운동 보조 가이드이며 의학적 진단을 대신하지 않습니다.'
        '</p>',
        unsafe_allow_html=True,
    )
