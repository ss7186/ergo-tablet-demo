# 미결정 사항 (나중에 결정)

> 작업 중 정정 보류된 항목, 임상/디자인/운영 결정이 필요한 항목을 모아둠.
> 새 항목은 해당 섹션에 동일 포맷으로 추가.

---

## 의학적 정확성 검토 필요

> 2026-05-29 condition 모듈 재정의 (NE/AD/AE/AI) 시 함께 정정하지 않은 영역.
> 옛 모듈 정의 기반의 임상 설명이 남아 있어 새 정의와 일관성 불일치 가능성.

### 1. `user_friendly_effects` (효과 설명)

- **위치**: [data/conditions.json](data/conditions.json) — 각 condition block의 `user_friendly_effects` 필드 (10개 condition × {muscles_strengthened, load_decreased, load_increased, contralateral_note})
- **현재 상태**: 옛 모듈 정의("AD=발끝 안쪽 → hip ABDUCTS → 외전근 Gmed 동원" 등) 기반으로 작성된 효과 설명. 예: ADAD의 "양쪽 엉덩이 옆 근육 강화" 등
- **검토 필요 이유**: 새 정의(AD = adduction + inversion → 내로우·롤인)로는 강화 근육 / 부담 감소 부위가 달라질 수 있음. 결과 화면 사용자에게 노출되는 핵심 정보라 임상 정합성 중요
- **결정 주체**: **임상 검토 (ss7186 / 정형외과 교수) + PROTOCOL_v2.md §1-3 재확인**
- **상태**: [ ] 미결정

### 2. `mechanism_target` (🎯 타겟 라벨)

- **위치**: [data/conditions.json](data/conditions.json) — 각 condition block의 `mechanism_target` 필드 (배열)
- **현재 상태**: 옛 정의 기반의 타겟 근육/joint 표기. 결과 화면 [components/screen_result.py:42-44](components/screen_result.py#L42-L44)에서 "🎯 {타겟} 타겟" 형식으로 사용자에게 노출
- **검토 필요 이유**: user_friendly_effects와 같은 이슈. 새 모듈 정의에서 실제 타겟 근육/joint가 다를 가능성
- **결정 주체**: **임상 검토 (ss7186 / 정형외과 교수) + PROTOCOL_v2.md 매트릭스 근거**
- **상태**: [ ] 미결정

### 3. `contraindications` (⚠️ 안전 경고)

- **위치**: [data/conditions.json](data/conditions.json) — 각 condition block의 `contraindications` 필드 (배열) + [data/goal_concern_mapping.json:106-125](data/goal_concern_mapping.json#L106-L125) `concerns` 블록의 `blocks_module`
- **현재 상태**: 옛 모듈 정의 기반의 금기 사항 (예: 고관절 인공관절 → AD 모듈 차단). 안전 가드 역할
- **검토 필요 이유**:
  - 모듈 정의가 바뀌었으므로 어떤 condition이 어떤 환자에게 금기인지도 재검증 필요
  - 추가 발견 이슈: [components/recommendation.py:61-67](components/recommendation.py#L61-L67) `check_contraindications()` 함수가 `concern_keys` 파라미터를 받지만 **함수 내부에서 사용 안 함** (dead parameter). 즉 PROTOCOL_v2 §7 안전 차단 로직이 실제로는 작동 안 함
- **결정 주체**: **임상 검토 필수 (ss7186 / 정형외과 교수). 안전 영향 직접 — CLAUDE.md §5에 따라 절대 임의 변경 금지**
- **상태**: [ ] 미결정

### 4. `_symmetric_recommend` (대칭 분기 점수 계산)

- **위치**: [components/recommendation.py:16-37](components/recommendation.py#L16-L37) `_muscle_score()` + `_symmetric_recommend()`
- **현재 상태**: `goal.weights × condition.biomech_data.muscles[m]` 점수 합산 방식. muscles 수치는 옛 모듈 정의 + [ASYMM]/analysis/condition_mechanism_signature.csv (OpenSim n=15) 기반
- **검토 필요 이유**:
  - 새 모듈 정의로는 각 condition의 muscle activation 패턴이 다르게 해석될 수 있음
  - 현재 엉덩이 → ADAD 추천하는 로직이 새 정의(AD = adduction)와도 부합하는지 임상 검증 필요
  - muscles 데이터(`biomech_data.muscles`) 자체가 OpenSim 시뮬 결과인지, 옛 정의 해석인지 확인 필요
- **결정 주체**: **임상 검토 + 시뮬 데이터 원본 (condition_mechanism_signature.csv) 재검증 (ss7186)**
- **상태**: [ ] 미결정

### 5. `intensity` (난이도)

- **위치**: [data/conditions.json](data/conditions.json) — 각 condition block의 `intensity` 필드. 결과 화면 상단 우측 "난이도" 표시에 사용 ([components/screen_result.py](components/screen_result.py))
- **현재 상태**: 활성 모듈 수 기반 임의 분류
  - 쉬움: NENE (둘 다 수평, 0개 활성)
  - 보통: ADNE / NEAD / AENE / NEAE / AINE / NEAI (한쪽만 비-NE, 1개 활성)
  - 강함: ADAD / AEAE / AIAI (양쪽 모두 비-NE, 2개 활성)
- **검토 필요 이유**: **난이도 임의로 설정함. 기준 필요.**
  - 명시적 분류 기준 문서 없음 (`_schema_doc`, CLAUDE.md, HANDOFF.md, PROTOCOL_v2.md 모두에 기준 미명시)
  - "활성 모듈 수"가 실제 운동 난이도와 일치하는지 임상 검증 안 됨
  - 모듈별 강도 차이 (AD vs AE vs AI) 미반영 — 예: AIAI와 ADAD가 같은 "강함"이지만 실제 부담은 다를 수 있음
  - 새 모듈 정의(adduction+inversion 등) 적용 후 난이도 재검증 필요
- **결정 주체**: **임상 검토 (ss7186 / 정형외과 교수) + condition_mechanism_signature.csv 활성도 데이터 기반 재분류**
- **상태**: [ ] 미결정

---

## 디자인/카피 결정 필요

> 사용자에게 노출되는 텍스트/시각 요소 중 추후 다듬을 항목.

(없음 — 발생 시 추가)

---

## 기타

> 위 카테고리에 안 맞는 운영/배포/인프라 관련 미결정 사항.

(없음 — 발생 시 추가)

---

작성: 2026-05-29 / JHM
