import streamlit as st
import pandas as pd
import yaml

from loader import read_any
from roster_master import load_roster_master
from latest_email import latest_email_by_student
from form_submit import count_form_submissions_by_studentno
from scoring import build_gradebook
from export_excel import export_to_excel_bytes

st.set_page_config(page_title="WEB制作運用｜名簿＋フォーム統合", layout="wide")
st.title("WEB制作運用｜名簿＋フォーム統合 → 採点台帳Excel出力")
st.caption("学生の個人情報を扱うため、公開運用は避け、ローカル/限定環境推奨")

# YAML読み込み（壊れてたら画面に出す）
try:
    with open("config/scoring.yaml", "r", encoding="utf-8") as f:
        scoring_cfg = yaml.safe_load(f)
except Exception as e:
    st.error("config/scoring.yaml の読み込みに失敗しました（インデント/全角記号/```混入を確認）。")
    st.exception(e)
    st.stop()

total_sessions = int(scoring_cfg["attendance"]["total_sessions"])

st.subheader("① 名簿（RosterMaster）")
roster_file = st.file_uploader("名簿をアップロード（.xlsx / .csv）", type=["xlsx", "csv"], key="roster")

st.subheader("② 統合フォーム（FormRaw）")
form_file = st.file_uploader("統合フォームをアップロード（.xlsx / .csv）", type=["xlsx", "csv"], key="form")

if not roster_file or not form_file:
    st.info("名簿とフォームの両方をアップロードしてください。")
    st.stop()

# --- 名簿 ---
st.markdown("### 名簿の読み込み")
if roster_file.name.lower().endswith(".xlsx"):
    _, sheets = read_any(roster_file, sheet_name=None)
    sheet = st.selectbox("名簿Excelのシート", sheets, key="roster_sheet")
    roster_df, _ = read_any(roster_file, sheet_name=sheet)
else:
    roster_df, _ = read_any(roster_file, sheet_name=None)

try:
    roster_master = load_roster_master(roster_df)
except Exception as e:
    st.error("名簿の列名が合っていない可能性：必須 class / Timetable / Time / student_no / name")
    st.exception(e)
    st.stop()

st.dataframe(roster_master, use_container_width=True)

# --- フォーム ---
st.markdown("### フォームの読み込み")
if form_file.name.lower().endswith(".xlsx"):
    _, fsheets = read_any(form_file, sheet_name=None)
    fsheet = st.selectbox("フォームExcelのシート", fsheets, key="form_sheet")
    form_df, _ = read_any(form_file, sheet_name=fsheet)
else:
    form_df, _ = read_any(form_file, sheet_name=None)

st.dataframe(form_df.head(10), use_container_width=True)

# --- フォーム列の割り当て（手動が最強） ---
st.markdown("### フォーム列の割り当て")
cols = list(form_df.columns)

col_ts = st.selectbox("タイムスタンプ列", cols, index=cols.index("タイムスタンプ") if "タイムスタンプ" in cols else 0)
col_email = st.selectbox("メール列", cols, index=cols.index("メールアドレス") if "メールアドレス" in cols else 0)

default_no_idx = 0
for i, c in enumerate(cols):
    if c.lower().startswith("no."):
        default_no_idx = i
        break
col_no = st.selectbox("student_no（No.）列", cols, index=default_no_idx)

# --- email 最新 & 提出回数 ---
email_latest = latest_email_by_student(form_df, col_no, col_email, col_ts)
submit_cnt = count_form_submissions_by_studentno(form_df, col_no, col_ts, cap=total_sessions)

# 名簿に反映（未提出でも残る）
roster_enriched = roster_master.merge(email_latest, on="student_no", how="left", suffixes=("", "_new"))
roster_enriched["email"] = roster_enriched["email_new"].fillna(roster_enriched["email"])
roster_enriched = roster_enriched.drop(columns=["email_new"])

roster_enriched = roster_enriched.merge(submit_cnt, on="student_no", how="left")
roster_enriched["form_submit_count"] = roster_enriched["form_submit_count"].fillna(0).astype(int)

st.markdown("### 名簿（フォーム情報を反映後）")
st.dataframe(roster_enriched, use_container_width=True)

# --- GradeBook ---
st.markdown("### GradeBook（採点台帳）")
gradebook = build_gradebook(roster_enriched, scoring_cfg)

site_total = st.number_input(
    "サイト制作｜チェック項目数（主要項目数）",
    min_value=1, max_value=30,
    value=int(scoring_cfg.get("defaults", {}).get("site_requirements_total", 8)),
    step=1
)
gradebook["site_requirements_total"] = int(site_total)

# site_total変更分だけ再計算（簡易）
denom = gradebook["site_requirements_total"].replace(0, 1)
gradebook["site_points_20"] = (gradebook["site_requirements_done"].clip(lower=0) / denom * float(scoring_cfg["learning"]["site"])).round(1)
gradebook["learning_points_70_raw"] = (
    gradebook["report_points_20"]
    + gradebook["paiza_points_10"]
    + gradebook["site_points_20"]
    + gradebook["form_points_10"]
    + gradebook["final_points_10"]
).round(1)
gradebook["learning_points_70"] = (gradebook["learning_points_70_raw"] - gradebook["attitude_penalty"]).clip(lower=0).round(1)
gradebook["total_100"] = (gradebook["attendance_points_30"] + gradebook["learning_points_70"]).round(1)

st.dataframe(gradebook, use_container_width=True, height=520)

# --- Excel download ---
excel_bytes = export_to_excel_bytes(roster_enriched, gradebook)
st.download_button(
    label="Excelをダウンロード（Roster＋GradeBook）",
    data=excel_bytes,
    file_name="WEB制作運用_採点台帳_自動生成.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


