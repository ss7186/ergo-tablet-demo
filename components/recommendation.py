"""Tilted-plane ergometer 추천 엔진.

Two branches:
  1. symmetric (top_mode='symmetric')
     - 근육 그룹 goal × symm condition (NENE/ADAD/AEAE/AIAI)에서 score-based
  2. asymmetric (top_mode='asymmetric')
     - v2 prescription matrix lookup: (symptom × side) → condition
     - Reference: [ASYMM]/analysis/PROTOCOL_v2.md §2, clinical_prescription_matrix_v2.csv
"""
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Symmetric branch — score-based
# ---------------------------------------------------------------------------
def _muscle_score(condition: dict, goal: dict) -> float:
    muscles = condition["biomech_data"]["muscles"]
    weights = goal.get("weights", {})
    return sum(muscles.get(m, 0) * weights.get(m, 0) for m in goal.get("target_muscles", []))


def _symmetric_recommend(goal_key: str, conditions: dict, mapping: dict) -> tuple[str, dict, dict]:
    goal = mapping["symmetric_goals"][goal_key]
    best_key, best_score = None, float("-inf")
    for cond_key, cond_data in conditions.items():
        if cond_key.startswith("_"):
            continue
        if cond_data.get("symmetry") != "symm":  # symmetric branch는 symm condition만
            continue
        score = _muscle_score(cond_data, goal)
        if score > best_score:
            best_score, best_key = score, cond_key
    return best_key, conditions[best_key], {
        "source": "score",
        "goal": goal_key,
        "score": best_score,
    }


# ---------------------------------------------------------------------------
# Asymmetric branch — v2 prescription matrix lookup
# ---------------------------------------------------------------------------
def _asymmetric_recommend(
    symptom: str,
    side: str,
    conditions: dict,
    mapping: dict,
) -> tuple[str, dict, dict]:
    matrix = mapping["prescription_matrix"]
    cond_key = matrix.get(symptom, matrix["unknown"]).get(side, "NENE")
    return cond_key, conditions[cond_key], {
        "source": "matrix_v2",
        "symptom": symptom,
        "side": side,
    }


# ---------------------------------------------------------------------------
# Safety / contraindication check (informational)
# ---------------------------------------------------------------------------
def check_contraindications(cond: dict, concern_keys: Iterable[str], mapping: dict) -> list[str]:
    """추천된 condition에 대한 contraindication 경고 list."""
    warnings = []
    cond_contras = cond.get("contraindications", [])
    for cc in cond_contras:
        warnings.append(f"⚠️ 주의: {cc}")
    return warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def recommend(
    top_mode: str,
    conditions: dict,
    mapping: dict,
    *,
    sym_goal: Optional[str] = None,
    asym_symptom: Optional[str] = None,
    asym_side: Optional[str] = None,
) -> tuple[str, dict, dict]:
    """주어진 분기에 따라 condition 추천.

    symmetric: sym_goal 필수
    asymmetric: asym_symptom, asym_side 필수
    """
    if top_mode == "symmetric":
        if not sym_goal:
            return _symmetric_recommend("전체", conditions, mapping)
        return _symmetric_recommend(sym_goal, conditions, mapping)

    if top_mode == "asymmetric":
        symptom = asym_symptom or "unknown"
        side = asym_side or "both"
        return _asymmetric_recommend(symptom, side, conditions, mapping)

    return "NENE", conditions["NENE"], {"source": "default"}
