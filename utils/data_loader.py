"""JSON 데이터 로더. 파일 작아서 매 rerun마다 다시 읽음 (캐시 무효화 이슈 회피)."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_conditions() -> dict:
    with open(DATA_DIR / "conditions.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_mapping() -> dict:
    with open(DATA_DIR / "goal_concern_mapping.json", "r", encoding="utf-8") as f:
        return json.load(f)
