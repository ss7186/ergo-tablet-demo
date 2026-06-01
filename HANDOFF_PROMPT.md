# 새 Claude 세션 시작 prompt 템플릿

> 다른 사람이 이 앱을 인계받아 Claude Code로 수정하려 할 때, 첫 메시지로 던질 prompt.
> 아래 텍스트를 그대로 복사해서 본인 요청만 채워 보내면 됨.

---

## STEP 1 — 환경 한 번 셋업 (최초 1회만)

폴더가 OneDrive 안에 있다면 git 충돌 방지 위해 별도 위치로 clone 권장:

```powershell
# GitHub repo 권한이 있다고 가정 (collaborator로 초대받았어야 함)
git clone https://github.com/ss7186/ergo-tablet-demo.git C:\projects\ergo-tablet-demo
Set-Location -LiteralPath "C:\projects\ergo-tablet-demo"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Python 3.10+ 필요. 권한 못 받았으면 [ASYMM] 폴더 owner(ss7186)에게 요청.

OneDrive 폴더 안에서 그냥 작업하고 싶으면 그대로도 됨 — 단 `.git` sync 충돌 위험 약간 있음.

---

## STEP 2 — Claude Code 첫 메시지 (복사용)

작업 폴더(`C:\projects\ergo-tablet-demo` 또는 `[ERGO_Dynamics Journal]\ergo_tablet_app`)에서 `claude` 실행 후 아래를 첫 메시지로:

```
이 앱은 "다축 에르고미터" 태블릿 데모입니다. GitHub와 HF Space에 이미 배포되어 있고, 일부 수정해서 다시 배포하려고 합니다.

먼저 다음 문서를 읽어서 컨텍스트 적재해주세요 (순서대로):
1. CLAUDE.md  ← 작업 지침 / 자주 수정 영역 매핑
2. HANDOFF.md ← 권한, 환경, 협업 방식
3. README.md  ← 실행/배포 가이드

배포 흐름은 이미 자동화되어 있습니다:
  git push → GitHub Actions → HF Space 자동 mirror (1-2분)

[ASYMM]/analysis/PROTOCOL_v2.md 는 추천 매트릭스의 임상 근거입니다. 매트릭스 변경 요청 시 참고하세요.

오늘 하려는 작업:
[여기에 본인 요청 적기 — 예시 ↓]
- 예) Welcome 화면 색 톤을 차분한 청록 계열로 변경
- 예) 증상 카테고리 "허리 통증/뻐근함" 라벨을 더 친화적으로 다듬기
- 예) 결과 화면에 강도 표시를 더 크게 표시
- 예) 사용법 dialog의 4모드 그리드 layout 정리
- 예) 영상이 너무 길어 보임 — 자르거나 thumbnail로 대체

수정 후 streamlit으로 로컬 확인 → git commit + push까지 진행해주세요. HF Space는 자동 sync됩니다.
```

---

## 작업 예시별 추가 정보

### "디자인만 손볼 거예요"
→ Claude에게 `style/theme.css`만 보여달라고 하고, 본인이 보면서 변수 값 바꿔달라고 요청. 가장 안전.

### "추천 로직을 바꾸려고요"
→ 사전에 [ASYMM]/analysis/PROTOCOL_v2.md §2 매트릭스 한 번 읽기. 변경하려는 증상×side가 다른 condition을 추천하게 하려면 근거 확인 필수.

### "새 영상/일러스트 넣을게요"
→ `assets/videos/<code>.mp4` 또는 `assets/illustrations/<code>.png` 같은 파일명으로 덮어쓰기만 하면 됨. 외부 호스팅(YouTube)이면 `conditions.json::media.video` 필드에 URL 넣기.

### "새 화면을 추가하고 싶어요"
→ Claude에게 흐름 그림(어디 → 어디 → 어디)를 먼저 설명. 그래야 라우터(`app.py`) 흐름 망가지지 않게.

### "Streamlit 말고 다른 framework로 옮기고 싶어요"
→ 큰 작업. 1-3일. Claude에게 `현재 앱의 모든 화면 흐름 + 데이터 schema를 정리해줘` 먼저 요청한 후 옮길지 결정.

---

## 권한 / 인증 체크리스트 (인계받는 사람 본인이 확인)

- [ ] GitHub `ss7186/ergo-tablet-demo` repo에 collaborator로 추가됨 (web UI에서 초대 accept)
- [ ] HF `OrthoEngine` org 멤버로 초대됨 (또는 본인 HF org로 Space migrate 합의)
- [ ] HF write token 발급 (https://huggingface.co/settings/tokens, Type: Write). **token은 채팅에 노출 X**
- [ ] 로컬에서 `streamlit run app.py` 정상 동작 확인
- [ ] 작은 변경 (예: theme.css 색 1개) push → GitHub Actions 동작 → HF Space 반영까지 한 번 사이클 익숙해짐

---

## "사용자가 어떤 폴더에서 작업해야 하나" 정리

| 상황 | 작업 폴더 |
|---|---|
| **권장**: GitHub에서 fresh clone | `C:\projects\ergo-tablet-demo\` (OneDrive 밖) |
| **OneDrive 그대로 사용** | `[ERGO_Dynamics Journal]\ergo_tablet_app\` (OneDrive sync 동안 git 작업 멈춤 권장) |
| **참조만 / 자료 확인** | `[ERGO_Dynamics Journal]\` 전체 (OneDrive) |

배포 사이트 ([ASYMM] / [PROMOTION] / [Manuscript] 등 원본 자료)는 OneDrive에 그대로 두고, **앱 코드 수정은 별도 clone에서 하는 게 가장 안전**.

---

## 막혔을 때

- Claude에게 `HANDOFF.md §6 자주 묻는 케이스 부분 읽고 답해줘`
- GitHub Issues: https://github.com/ss7186/ergo-tablet-demo/issues
- repo owner(ss7186) 직접 문의
