"""JSON 데이터를 한 번만 읽어서 캐시한다."""
import json
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def load_conditions() -> dict:
    with open(DATA_DIR / "conditions.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_mapping() -> dict:
    with open(DATA_DIR / "goal_concern_mapping.json", "r", encoding="utf-8") as f:
        return json.load(f)
