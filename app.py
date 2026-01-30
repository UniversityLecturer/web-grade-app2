import streamlit as st
import pandas as pd
import yaml

from loader import read_any
from roster_master import load_roster_master
from latest_email import latest_email_by_class_studentno
from form_submit import count_form_submissions_by_class_studentno
from scoring import build_gradebook
from export_excel import export_to_excel_bytes

st.set_page_config(page_title="WEB制作運用｜名簿＋フォーム統合", layout="wide")
st.title("WEB制作運用｜名簿＋フォーム統合 → 採点台帳Excel出力")
st.caption("学生の個人情報を扱うため、公開運用は避け、ローカル/限定環境推奨")

# YAML読み込み
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

st.write("名簿行数:", len(roster_df), "→ 正規化後:", len(roster_master))
st.write(
    "classユニーク数:", roster_master["class"].nunique(),
    "student_noユニーク数:", roster_master["student_no"].nunique()
)
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

# --- フォーム列の割り当て ---
st.markdown("### フォーム列の割り当て")
cols = list(form_df.columns)

col_ts = st.selectbox("タイムスタンプ列", cols, index=cols.index("タイムスタンプ") if "タイムスタンプ" in cols else 0)
col_email = st.selectbox("メール列", cols, index=cols.index("メールアドレス") if "メールアドレス" in cols else 0)

# No列
default_no_idx = 0
for i, c in enumerate(cols):
    if str(c).lower().startswith("no."):
        default_no_idx = i
        break
col_no = st.selectbox("student_no（No.）列", cols, index=default_no_idx)

# Class列（提出回数＆メールのキーに必須）
default_class_idx = 0
for i, c in enumerate(cols):
    if "class" in str(c).lower():
        default_class_idx = i
        break
col_class = st.selectbox("Class列", cols, index=default_class_idx)

# --- 最新メール & 提出回数（class+student_no） ---
email_latest = latest_email_by_class_studentno(form_df, col_class, col_no, col_email, col_ts)
submit_cnt = count_form_submissions_by_class_studentno(form_df, col_class, col_no, col_ts, cap=total_sessions)

# 名簿に反映（class+student_no でJOIN）
roster_enriched = roster_master.merge(email_latest, on=["class", "student_no"], how="left", suffixes=("", "_new"))
roster_enriched["email"] = roster_enriched["email_new"].fillna(roster_enriched["email"])
roster_enriched = roster_enriched.drop(columns=["email_new"])

roster_enriched = roster_enriched.merge(submit_cnt, on=["class", "student_no"], how="left")
roster_enriched["form_submit_count"] = roster_enriched["form_submit_count"].fillna(0).astype(int)

st.markdown("### 名簿（フォーム情報を反映後）")
st.dataframe(roster_enriched, use_container_width=True)

# --- デバッグ：クラス別フォーム実施日数 ---
st.write("【デバッグ】クラス別フォーム実施日数")
dbg = (
    form_df[[col_class, col_ts]].copy()
    .assign(date=pd.to_datetime(form_df[col_ts], errors="coerce").dt.date)
    .groupby(col_class)["date"]
    .nunique()
)
st.write(dbg)

st.write("【デバッグ】form_submit_count 最大値:", int(roster_enriched["form_submit_count"].max() if len(roster_enriched) else 0))

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

st.dataframe(gradebook, use_container_width=True, height=520)

# --- Excel download ---
excel_bytes = export_to_excel_bytes(roster_enriched, gradebook)
st.download_button(
    label="Excelをダウンロード（Roster＋GradeBook）",
    data=excel_bytes,
    file_name="WEB制作運用_採点台帳_自動生成.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
