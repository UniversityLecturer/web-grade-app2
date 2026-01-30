import streamlit as st
import pandas as pd
import yaml

from loader import read_any
from roster_master import load_roster_master
from scoring import build_gradebook
from export_excel import export_to_excel_bytes
from normalize import normalize_text

st.set_page_config(page_title="WEB制作運用｜名簿＋フォーム統合", layout="wide")
st.title("WEB制作運用｜名簿＋フォーム統合 → 採点台帳Excel出力")
st.caption("学生の個人情報を扱うため、公開運用は避け、ローカル/限定環境推奨")

# -----------------------
# YAML読み込み
# -----------------------
try:
    with open("config/scoring.yaml", "r", encoding="utf-8") as f:
        scoring_cfg = yaml.safe_load(f)
except Exception as e:
    st.error("config/scoring.yaml の読み込みに失敗しました（インデント/全角記号/```混入を確認）。")
    st.exception(e)
    st.stop()

TOTAL_SESSIONS = int(scoring_cfg["attendance"]["total_sessions"])

# -----------------------
# 名簿の time（例: 9:10-10:50）から時間帯スロットを作る
# -----------------------
JP_WEEKDAY = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}

def parse_time_range(time_str: str):
    """
    '9:10-10:50' -> (550, 650)
    """
    s = normalize_text(time_str)
    if "-" not in s:
        return None
    a, b = s.split("-", 1)
    def to_min(hm: str) -> int:
        h
