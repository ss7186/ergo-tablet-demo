# Claude Code 작업 지침 — ergo_tablet_app

> Claude Code가 이 디렉토리에 진입할 때 자동으로 로드됨.
> 사람이 읽는 인계 문서는 `HANDOFF.md`, 일반 README는 `README.md`.

---

## 0. 정체성

- **앱**: 병원 헬스장 직원용 다축 에르고미터 태블릿 데모 (Streamlit, Python)
- **목적**: 직원이 30초 안에 본인 증상에 맞는 ergometer 페달 세팅 추천 받음
- **근거**: [ASYMM]/analysis/PROTOCOL_v2.md (n=15 OpenSim + n=7 페달 + n=3 VICON, 83% hit rate)
- **배포**:
  - GitHub: https://github.com/ss7186/ergo-tablet-demo (코드 원본)
  - HF Space: https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo (실배포)
  - 자동: `git push` → GitHub Actions → HF Space mirror (1-2분)

---

## 1. 작업 시작 시 우선 확인할 문서

새 세션에서는 다음 순서로 읽어 컨텍스트 적재:

1. **`HANDOFF.md`** (이 폴더) — 권한, 환경 셋업, 자주 수정 영역 매핑, 협업 방식
2. **`README.md`** — 실행/배포 가이드
3. **`data/conditions.json`** + **`data/goal_concern_mapping.json`** — 추천 매트릭스 schema
4. (필요 시) **`../[ASYMM]/analysis/PROTOCOL_v2.md`** — 매트릭스 임상 근거
5. (필요 시) **`../[ASYMM]/HANDOFF.md`** — sub-project 전체 컨텍스트

큰 PDF/PPTX 자료(`../[참고자료]/`, `../[PROMOTION]/`)는 사용자가 명시적으로 요청할 때만 열기.

---

## 2. 핵심 규칙 (코드 작성 시)

- **의학 용어 노출 금지**: 사용자 보이는 텍스트는 일상어 한국어 ("엉덩이 옆 근육" not "Gluteus medius"). 내부 변수명은 영어 OK
- **수치 노출 최소**: 결과 화면에 %/N·m 같은 raw 수치 X. 화살표/이모지/색으로
- **PROTOCOL_v2 매트릭스 임의 변경 금지**: `data/goal_concern_mapping.json::prescription_matrix` 는 [ASYMM] 연구 근거에 기반. 변경 요청 시 PROTOCOL_v2.md 근거를 사용자와 확인
- **condition 코드**: 4문자 = **앞 2글자=오른쪽 페달, 뒤 2글자=왼쪽 페달** (HANDOFF.md §1 명시). 절대 좌/우 뒤집지 말 것
- **모듈 의미** (PROTOCOL_v2 §1):
  - **AD** (toes-in) → hip ABDUCTS → 외전근(Gmed) 동원
  - **AE** (toes-out + ER) → hip ADDUCTS → 내전근 + ER stabilizer + trunk
  - **AI** (toes-in + everted) → rotation ROM 증가 → 회전 control
  - 모듈 이름은 발 동작, joint 효과는 보상 방향 — 헷갈리기 쉬움

---

## 3. 자주 수정하는 영역 (어디에 무엇이 있나)

| 카테고리 | 파일 |
|---|---|
| 색/폰트/카드 디자인 | `style/theme.css` (`:root` 변수 4-5줄로 전체 톤 변경) |
| 첫 화면 카피, 사용법 dialog | `components/screen_welcome.py` |
| 결과 화면 layout (column 비율, 일러스트/영상 크기) | `components/screen_result.py` |
| 증상 카테고리 / 매트릭스 | `data/goal_concern_mapping.json` |
| condition 효과 라벨, 영상 설명 | `data/conditions.json` |
| 영상/일러스트 자산 | `assets/videos/`, `assets/illustrations/` |
| Disclaimer / 안전 문구 | `screen_welcome.py`, `goal_concern_mapping.json::concerns` |
| 새 화면 추가 | `app.py::routes` + 새 `components/screen_*.py` |

---

## 4. 작업 후 배포 흐름

```
파일 수정
  ↓ (streamlit run app.py로 로컬 확인 권장)
git add <파일>
git commit -m "<설명>"
git push
  ↓ (GitHub Actions 자동 트리거, 1-2분)
HF Space 재배포 → 스탠바이미 브라우저 새로고침으로 반영
```

**push 전 체크**:
- 추천 매트릭스 변경했으면 PROTOCOL_v2.md 근거 확인했는가?
- 영상/일러스트 교체했으면 파일명이 conditions.json의 media 경로와 일치하는가?
- Streamlit 1.57+ API 호환 (`st.image(width="stretch")` 등 — None 금지)?

**GitHub Actions 로그 확인**: https://github.com/ss7186/ergo-tablet-demo/actions

---

## 5. 위험한 작업 — 사용자 컨펌 필수

- **PROTOCOL_v2 매트릭스 변경**: 임상 처방 로직 — 근거 없이 바꾸면 환자 안전 영향
- **`contraindications` 제거**: 고관절 인공관절/ACL 재건 등 안전 가드. 임의 삭제 X
- **`git push --force`**: 다른 사람 작업 덮어쓸 위험
- **HF Space repo 삭제 / 이름 변경**: 스탠바이미가 가리키는 URL 끊김
- **secret 노출**: `HF_TOKEN` 채팅에 출력하거나 commit 금지

---

## 6. 환경 / 권한

| 자원 | 위치 | 권한 받는 방법 |
|---|---|---|
| GitHub repo | ss7186/ergo-tablet-demo | repo owner에게 GitHub username 알려 collaborator 추가 요청 |
| HF Space | OrthoEngine/ergo-tablet-demo | OrthoEngine org 멤버 초대 요청 |
| HF write token | 본인 발급 | https://huggingface.co/settings/tokens — Type: Write |
| GitHub Actions secret | repo Settings → Secrets → `HF_TOKEN` | 자동 배포가 안 되면 secret 등록 확인 |

---

## 7. OneDrive + git 충돌 (인계 환경 특이사항)

이 프로젝트는 OneDrive 동기화 폴더 안에 있을 수 있음. `.git` 폴더와 OneDrive sync 동시 활성화 시 commit 깨질 위험.

**권장**: OneDrive 폴더 안에서 작업 대신 별도 위치로 clone:
```powershell
git clone https://github.com/ss7186/ergo-tablet-demo.git C:\projects\ergo-tablet-demo
```

OneDrive 폴더의 `ergo_tablet_app/`은 인계 자료 참조용으로만 사용. 실제 git 작업은 별도 clone에서.

---

## 8. 로컬 개발 환경 (최초 1회)

```powershell
git clone https://github.com/ss7186/ergo-tablet-demo.git
Set-Location -LiteralPath "ergo-tablet-demo"   # cd가 막히면 LiteralPath
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

`runOnSave=true` 설정되어 있어 파일 저장 시 브라우저 자동 새로고침.

---

## 9. 응답 스타일 (사용자 선호)

- 한국어 본문 + 학술 용어 영어 병기 OK
- 짧고 핵심 위주. 불필요한 요약/내부 추론 narration X
- 결정 사항은 명확하게: "A로 진행" 또는 "사용자 컨펌 필요" 둘 중 하나
- 큰 변경은 단계별 보고 + todos
- 사용자가 `진행해줘`/`직접 진행해줘` 하면 합리적 default로 자동 실행, 권한 외 작업은 명확히 사용자 요청

---

## 10. 막혔을 때

- `git log -p <파일>` — 변경 히스토리
- HANDOFF.md §6 (자주 묻는 케이스)
- 코드 의도 모호하면 사용자에게 물어보기 (`AskUserQuestion`)
- 임상 매트릭스 관련: PROTOCOL_v2.md §1-3 확인
