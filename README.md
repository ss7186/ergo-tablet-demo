---
title: 비대칭 조정 에르고미터
emoji: 🚲
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.57.0
app_file: app.py
pinned: false
license: mit
short_description: PROTOCOL_v2 기반 ergometer 비대칭 처방 데모
---

# 비대칭 조정 에르고미터 — 태블릿 데모 앱

병원 헬스장에 비치되는 태블릿/스탠바이미용 데모. 직원이 30초 안에 본인 증상에 맞는 ergometer 세팅을 추천받는다.

근거: [ASYMM] sub-project PROTOCOL_v2 (n=15 OpenSim + n=7 페달 + n=3 VICON 검증, 83% hit rate).

---

## 로컬 실행

Python 3.10+ 필요 (https://python.org).

```powershell
cd ergo_tablet_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501. iPad/스탠바이미 시뮬레이션은 개발자도구 → Device toolbar.

---

## 화면 흐름

```
welcome
 └ "시작하기" → mode (대칭/비대칭 분기)
 └ "📺 사용법 보기" → modal dialog

대칭 분기:    mode → sym_goal (엉덩이/허벅지 안쪽/고관절 회전/전체) → concern → result
비대칭 분기:  mode → asym_side (왼쪽/오른쪽/양쪽) → asym_symptom (7 카테고리) → concern → result
```

비대칭 분기는 PROTOCOL_v2 prescription matrix (`data/goal_concern_mapping.json::prescription_matrix`)로 (symptom × side) → condition 즉시 lookup.

---

## 파일 구조

```
ergo_tablet_app/
├── app.py                    # 라우터
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/config.toml
├── data/
│   ├── conditions.json              # 10 condition + biomech 수치 + media path + contraindications
│   └── goal_concern_mapping.json    # 분기 schema + v2 prescription matrix
├── components/
│   ├── recommendation.py     # rule-based (asymm) + score-based (symm)
│   ├── screen_welcome.py     # device 이미지 + howto dialog
│   ├── screen_mode.py
│   ├── screen_goal.py        # 대칭 분기
│   ├── screen_asym.py        # 비대칭 — 좌/우
│   ├── screen_symptom.py     # 비대칭 — 증상 카테고리
│   ├── screen_concern.py     # 안전 점검 (contraindications)
│   └── screen_result.py
├── utils/
│   ├── data_loader.py
│   └── media.py              # 영상/일러스트 파일 존재 체크 + fallback
├── assets/
│   ├── illustrations/        # 10 condition + mode_* + device_main + pedal_dial
│   ├── videos/               # symmetric mp4 4개 (asymm는 module별 fallback)
│   └── README.md
└── style/theme.css
```

---

## 배포 — GitHub + Streamlit Community Cloud

### 1) GitHub repo 만들기

GitHub에 새 repo 생성 (public 권장 — Streamlit Cloud 무료 limit). repo 이름 예: `ergo-tablet-demo`.

로컬에서:
```powershell
cd "c:\Users\kumc\OneDrive\[ERGO_Dynamics Journal]\ergo_tablet_app"
git init
git add .
git commit -m "Initial commit: 비대칭 조정 에르고미터 데모 v1"
git branch -M main
git remote add origin https://github.com/<your-username>/ergo-tablet-demo.git
git push -u origin main
```

영상 mp4 5개 총 72MB → 단일 파일 100MB / repo 1GB 한도 안. `git push`는 가능. 단 push에 시간 좀 걸림.

### 2) Streamlit Cloud 연결

1. https://share.streamlit.io 접속 → GitHub 계정 연동
2. **New app** 클릭 → repo 선택 → Branch: `main`, Main file: `app.py`
3. **Deploy** 클릭. 5분 정도 빌드 후 URL 받음: `https://<app-name>.streamlit.app`

### 3) 스탠바이미에서 띄우기

스탠바이미 웹 브라우저에서:
1. URL 접속
2. 즐겨찾기 / 홈페이지로 설정
3. 전체화면 모드
4. **자동 잠금 / 절전 비활성화** (설정 → 디스플레이/전원)

---

## 수정 흐름 (반복 가능)

```
로컬 수정
  ↓
git add <files>
git commit -m "<설명>"
git push
  ↓
Streamlit Cloud 자동 재배포 (1–2분)
  ↓
스탠바이미 브라우저 새로고침 → 반영
```

### 자주 수정할 만한 항목

| 항목 | 파일 | 영향 |
|---|---|---|
| 추천 매트릭스 (증상 → condition) | `data/goal_concern_mapping.json::prescription_matrix` | 즉시 반영 |
| condition 효과 라벨 / 영상 설명 | `data/conditions.json::<code>.user_friendly_effects`, `media.video_description` | 즉시 반영 |
| 영상/일러스트 교체 | `assets/videos/<code>.mp4`, `assets/illustrations/<code>.png` | 같은 파일명으로 덮어쓰기, git push |
| 새 증상 카테고리 | `goal_concern_mapping.json::asymmetric_symptoms` + `prescription_matrix`에 매핑 추가 | screen_symptom.py 자동 카드 추가 |
| Disclaimer 텍스트 | `components/screen_welcome.py` | — |
| CSS / 폰트 / 색 | `style/theme.css` | — |

### 영상이 큰 경우 (50MB+)

GitHub 단일 파일 100MB 한도 초과 시:
- Git LFS 사용 (`git lfs track "*.mp4"`)
- 또는 YouTube unlisted 업로드 → `conditions.json::media.video`에 `https://...` URL 직접 입력 (media.py가 URL 자동 인식)

---

## Streamlit Cloud sleep 방지

무료 plan은 1주일 미사용 시 sleep (첫 접속 시 30초 대기). 헬스장에서 매일 쓰면 sleep 안 됨. 보장하려면:
- **UptimeRobot** (무료) 으로 5분마다 ping
- **Render starter** $7/월 (sleep 없음)
- **Railway** $5/월 + 사용량

---

## 피드백 수집 (Phase 2)

현재 👍/👎 클릭은 `st.toast`만 표시 (메모리). 누적 저장은:
1. Google Cloud Console에서 service account 생성 + Google Sheet 공유
2. `.streamlit/secrets.toml`에 service account JSON 추가 (gitignored)
3. Streamlit Cloud의 Secrets 메뉴에 동일 내용 붙여넣기
4. `screen_result.py`에서 gspread로 sheet append

---

## 참고 자료

- `[ASYMM]/analysis/PROTOCOL_v2.md` — 본 앱의 prescription matrix 근거
- `[ASYMM]/analysis/clinical_prescription_matrix_v2.csv` — 17개 임상 패턴 매트릭스
- `[ASYMM]/analysis/v2_validation.csv` — 10/12 (83%) hit rate 검증
- `[ASYMM]/HANDOFF.md` — sub-project 전체 컨텍스트
