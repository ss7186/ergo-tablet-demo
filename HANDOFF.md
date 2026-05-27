# 비대칭 조정 에르고미터 — 인계 문서

새로 앱을 수정/관리하는 분을 위한 가이드. README와 함께 읽기.

---

## 1. 권한 / 접근

| 자원 | URL | 권한 받는 방법 |
|---|---|---|
| GitHub 코드 repo | https://github.com/ss7186/ergo-tablet-demo | repo owner(ss7186)에게 GitHub username 알려주고 **Settings → Collaborators**에 추가 요청. public이므로 fork 후 PR도 가능 |
| Hugging Face Space (실배포) | https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo | OrthoEngine org 멤버 추가 요청. 본인 HF account 필요 |
| HF write token (push용) | https://huggingface.co/settings/tokens | 본인 계정에서 직접 발급. Type: **Write** |

---

## 2. 로컬 환경 셋업 (10분)

```powershell
# Python 3.10+ 설치 필요: https://www.python.org/downloads/
git clone https://github.com/ss7186/ergo-tablet-demo.git
cd ergo-tablet-demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 열림. 이대로 수정하면서 실시간 확인 가능 (Streamlit은 파일 저장 시 자동 새로고침).

PowerShell `cd`가 경로의 대괄호 `[]`로 막히면 `Set-Location -LiteralPath "..."` 사용.

---

## 3. 수정 자주 하는 영역 — "이 부분 바꾸려면 어디?"

### 디자인 (색, 폰트, 버튼 크기, 카드 모양)
- `style/theme.css` — CSS 변수 (`--primary`, `--bg`, `--radius` 등) + 카드/버튼 스타일 전부
- 색 톤만 바꾸려면 `:root` 블록의 `--primary`, `--accent`, `--good`, `--warn` 만 수정

### 화면 텍스트 (welcome 카피, 안내 문구, 버튼 라벨)
- `components/screen_welcome.py` — 첫 화면 카피, 사용법 dialog
- `components/screen_mode.py` — "어떤 운동을 하시겠어요?"
- `components/screen_goal.py` — 대칭 분기 라벨
- `components/screen_asym.py` — "어느 쪽이 더 불편?" 등
- `components/screen_symptom.py` — 증상 카테고리 라벨
- `components/screen_concern.py` — 안전 점검 (contraindication 선택)
- `components/screen_result.py` — 결과 카드 라벨

### 추천 매트릭스 (어떤 증상에 어떤 condition?)
- `data/goal_concern_mapping.json` 의 `prescription_matrix` 블록
  ```json
  "hip_pelvis": { "right": "ADNE", "left": "NEAD", "both": "ADAD" },
  ...
  ```
- 증상 자체 추가/제거는 `asymmetric_symptoms` 블록 + 매트릭스 모두 갱신

### condition별 효과 라벨, 영상 설명
- `data/conditions.json` 의 각 condition 블록:
  - `name_kr` — 사용자 보이는 이름
  - `user_friendly_effects.muscles_strengthened/load_decreased/load_increased` — 결과 화면 효과 카드
  - `mechanism_target` — 🎯 타겟 라벨
  - `media.video_description` — 영상 캡션
  - `contraindications` — ⚠️ 안전 경고 텍스트

### 영상 / 일러스트 교체
- `assets/videos/<code>.mp4` 같은 파일명으로 덮어쓰기 (예: `aeae.mp4`)
- `assets/illustrations/<code>.png` 같은 파일명으로 덮어쓰기
- 외부 호스팅(YouTube 등)으로 옮기려면 `conditions.json::media.video` 필드에 `https://...` URL 직접 입력 (media.py가 URL 자동 인식)

### Disclaimer / 안전 문구
- `components/screen_welcome.py` 의 `<p class="disclaimer">...</p>`
- `data/goal_concern_mapping.json` 의 `concerns` 블록 (안전 점검 옵션 항목)

### 새 화면 흐름 추가
- `app.py` 의 `routes` dict에 screen 등록 + 새 `screen_*.py` 작성

---

## 4. 변경 사항 배포 (반복 가능)

### A. GitHub에 push (원본 보관)
```powershell
git add .
git commit -m "<변경 설명>"
git push
```

### B. HF Space에 반영 (실제 운영 사이트)
GitHub push만으로는 HF Space가 자동 업데이트 X. 두 가지 방법:

**B-1. 매번 수동 (`_hf_upload.py`):**
```powershell
$env:HF_TOKEN = "hf_본인토큰"
python _hf_upload.py
```
영상이나 큰 파일 변경 시에도 LFS 자동 처리됨.

**B-2. GitHub Actions로 자동화 (한 번만 설정):**
- 인계받은 사람이 자기 PC에서 직접 push만 하면 HF에 자동 배포되게 하려면 `.github/workflows/sync-to-hf.yml` 추가
- HF token을 GitHub repo의 Settings → Secrets에 `HF_TOKEN`으로 저장
- 이후 `git push`만 하면 → GitHub Action이 HF에 mirror

원하시면 B-2 workflow 파일 만들어드릴 수 있습니다.

### 변경 흐름 요약
```
로컬 수정 → streamlit run으로 확인 → git commit + push → HF 업로드
                                       ↓                    ↓
                                 GitHub 보관             스탠바이미 새로고침
```

---

## 5. 협업 방식 선택

| 방식 | 장점 | 단점 |
|---|---|---|
| **Collaborator 추가** | 직접 push 가능, 빠름 | 검토 단계 없음. 디자인 변경이 main에 즉시 반영 |
| **Fork + PR** | 검토 후 merge. 안전 | 매번 PR 단계 추가. 작은 변경에도 번거로움 |
| **별도 branch + PR** | 검토하면서 빠름 | 인계받는 사람이 branch 워크플로우 익숙해야 |

데모 운영 단계면 **Collaborator 직접 push**가 가장 효율적. 추후 본격 운영이면 PR.

---

## 6. 자주 묻는 케이스

### "디자인 색만 바꾸려면?"
`style/theme.css` 상단의 `:root` 블록 4-5줄만 수정. push.

### "특정 증상에 다른 condition 추천하려면?"
`data/goal_concern_mapping.json::prescription_matrix` 의 해당 row만 수정.
예: 무릎 안쪽 → 다른 condition으로 바꾸기:
```json
"knee_medial": { "right": "ADNE",  ← AENE에서 ADNE로 변경
                 "left":  "NEAD",
                 "both":  "ADAD" }
```
근거는 [ASYMM]/analysis/PROTOCOL_v2.md §2 매트릭스 참고.

### "영상이 너무 큰 / 무겁다는 컴플레인"
- 영상 길이 더 짧게 자르기 (15-30초 권장)
- 또는 YouTube unlisted 업로드 → `conditions.json::media.video` URL로 변경 → repo에서 mp4 삭제

### "스탠바이미가 sleep 모드로 들어감"
- 스탠바이미 설정 → 자동 잠금 비활성화
- HF Space 자체가 sleep되는 경우 UptimeRobot으로 5분 ping

### "결과 화면이 너무 길어 / 짧아"
`components/screen_result.py` 의 layout. `st.columns([2, 3])` 비율 변경, 일러스트 `width=320` 같은 픽셀 값 조정.

### "직원이 자기 비대칭 잘 인식 못 함"
현재 증상 카테고리(엉덩이/골반, 무릎 안/바깥/앞, 허리, 발 정렬, 잘 모름) 7개. 더 추가하려면 `asymmetric_symptoms` + `prescription_matrix`에 row 추가. [ASYMM]/analysis/PROTOCOL_v2.md §2의 17개 임상 패턴 참고.

---

## 7. 근거 자료 (수정 시 참고)

| 자료 | 위치 | 용도 |
|---|---|---|
| Asymmetry sub-project handoff | `[ASYMM]/HANDOFF.md` | 전체 컨텍스트 |
| 임상 처방 프로토콜 v2 | `[ASYMM]/analysis/PROTOCOL_v2.md` | 본 앱 매트릭스의 출처 |
| 16-row 매트릭스 (CSV) | `[ASYMM]/analysis/clinical_prescription_matrix_v2.csv` | 임상 패턴 → condition 매핑 원본 |
| condition별 joint effect | `[ASYMM]/analysis/condition_mechanism_signature.csv` | n=15 OpenSim 수치 (conditions.json의 outcomes 출처) |
| Whole-body 검증 | `[ASYMM]/analysis/v2_validation.csv` | 83% hit rate 근거 |
| PROMOTION 영상/PPT | `[PROMOTION]/` 폴더 | 영상/이미지 원본 |
| 본 앱 README | `README.md` | 배포/실행 가이드 |

---

## 8. 막혔을 때

- GitHub repo issue로 질문
- 또는 ss7186 / 본 프로젝트 owner에게 직접 문의
- 코드 의도 모를 때: `git log -p <파일>` 로 변경 히스토리 확인

---

## 9. 인계 체크리스트 (인계받는 분이 한 번씩 확인)

- [ ] GitHub username 알려드리고 collaborator 추가 받음
- [ ] HF account 만들고 OrthoEngine org 멤버 추가 받음 (또는 본인 HF org 새로 만들고 Space migrate)
- [ ] 본인 HF write token 발급
- [ ] 로컬에서 `streamlit run app.py` 정상 동작 확인
- [ ] 작은 변경 (예: 색상 1개 변경) 한 번 push해서 HF 반영까지 흐름 익숙
- [ ] [ASYMM]/analysis/PROTOCOL_v2.md 한 번 정독 (매트릭스 수정 시 필수)
