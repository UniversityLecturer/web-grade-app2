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
# 名簿の Time(例: 9:10-10:50) から枠を作る
# ＝この枠に入らないフォームはカウントしない
# -----------------------
JP_WEEKDAY = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}

def parse_time_range(time_str: str):
    """
    '9:10-10:50' -> (550, 650)  # minutes
    """
    s = normalize_text(time_str)
    if "-" not in s:
        return None
    a, b = s.split("-", 1)
    a = a.strip()
    b = b.strip()
    def to_min(hm: str) -> int:
        h, m = hm.split(":")
        return int(h) * 60 + int(m)
    return to_min(a), to_min(b)

def build_time_slots_from_roster(roster_df: pd.DataFrame):
    """
    名簿の (Timetable, Time, class) から、
    weekday と time_range で class を返せるスロット一覧を作る。
    """
    slots = []
    # 例: Timetable = "木1限" -> weekday=3
    for _, r in roster_df[["class", "Timetable", "Time"]].drop_duplicates().iterrows():
        klass = normalize_text(r["class"])
        tt = normalize_text(r["Timetable"])
        tm = normalize_text(r["Time"])
        if not klass or not tt or not tm:
            continue
        w_char = tt[:1]  # "木"など
        if w_char not in JP_WEEKDAY:
            continue
        weekday = JP_WEEKDAY[w_char]
        tr = parse_time_range(tm)
        if tr is None:
            continue
        start_min, end_min = tr
        slots.append((weekday, start_min, end_min, klass, tt, tm))
    return slots

def map_class_by_time(ts_series: pd.Series, slots):
    """
    タイムスタンプ→(weekday, time) が名簿スロットに入っていれば class を返す
    入っていなければ "" を返す（=カウントしない）
    """
    dt = pd.to_datetime(ts_series, errors="coerce")
    wd = dt.dt.weekday
    mm = dt.dt.hour * 60 + dt.dt.minute

    out = []
    for w, m in zip(wd, mm):
        if pd.isna(w) or pd.isna(m):
            out.append("")
            continue
        w = int(w); m = int(m)
        found = ""
        for (sw, smin, emin, klass, _, _) in slots:
            if w == sw and smin <= m < emin:
                found = klass
                break
        out.append(found)
    return pd.Series(out)

# -----------------------
# UI: Upload
# -----------------------
st.subheader("① 名簿（RosterMaster）")
roster_file = st.file_uploader("名簿をアップロード（.xlsx / .csv）", type=["xlsx", "csv"], key="roster")

st.subheader("② 統合フォーム（FormRaw）")
form_file = st.file_uploader("統合フォームをアップロード（.xlsx / .csv）", type=["xlsx", "csv"], key="form")

if not roster_file or not form_file:
    st.info("名簿とフォームの両方をアップロードしてください。")
    st.stop()

# -----------------------
# 名簿読み込み
# -----------------------
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
st.dataframe(roster_master, use_container_width=True)

# 名簿からスロット生成（＝時間帯以外はカウントしない条件）
slots = build_time_slots_from_roster(roster_master)
st.write("【デバッグ】名簿から生成した時間帯スロット数:", len(slots))
st.write("【デバッグ】スロット例（先頭5件）:", slots[:5])

# -----------------------
# フォーム読み込み
# -----------------------
st.markdown("### フォームの読み込み")
if form_file.name.lower().endswith(".xlsx"):
    _, fsheets = read_any(form_file, sheet_name=None)
    fsheet = st.selectbox("フォームExcelのシート", fsheets, key="form_sheet")
    form_df, _ = read_any(form_file, sheet_name=fsheet)
else:
    form_df, _ = read_any(form_file, sheet_name=None)

st.dataframe(form_df.head(10), use_container_width=True)

# -----------------------
# フォーム列の割り当て（Class列は使わない：時間帯で決める）
# -----------------------
st.markdown("### フォーム列の割り当て（Class列は不要：時間帯で判定します）")
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

# -----------------------
# class_key を時間帯で作り、時間帯外は除外（=カウントしない）
# -----------------------
form_df["class_key"] = map_class_by_time(form_df[col_ts], slots)
form_df["student_no_key"] = form_df[col_no].map(normalize_text)
form_df["email_key"] = form_df[col_email].map(normalize_text).str.lower()
form_df["ts_key"] = pd.to_datetime(form_df[col_ts], errors="coerce")

in_scope = form_df["class_key"].ne("") & form_df["student_no_key"].ne("") & form_df["ts_key"].notna()
form_in = form_df.loc[in_scope].copy()

st.write("【デバッグ】フォーム行数:", len(form_df), "／時間帯内カウント対象行:", len(form_in))

# -----------------------
# 最新メール（class_key + student_no_key）
# -----------------------
latest_email = (
    form_in.loc[form_in["email_key"].ne(""), ["class_key", "student_no_key", "email_key", "ts_key"]]
    .sort_values("ts_key")
    .drop_duplicates(subset=["class_key", "student_no_key"], keep="last")
    .rename(columns={"class_key": "class", "student_no_key": "student_no", "email_key": "email"})
)[["class", "student_no", "email"]]

# -----------------------
# 提出回数（1日1回：class_key + student_no_key + date）
# -----------------------
tmp = form_in[["class_key", "student_no_key", "ts_key"]].copy()
tmp["date"] = tmp["ts_key"].dt.date
tmp = tmp.drop_duplicates(subset=["class_key", "student_no_key", "date"])

submit_cnt = (
    tmp.groupby(["class_key", "student_no_key"], as_index=False)["date"]
    .nunique()
    .rename(columns={"class_key": "class", "student_no_key": "student_no", "date": "form_submit_count"})
)
submit_cnt["form_submit_count"] = submit_cnt["form_submit_count"].clip(upper=TOTAL_SESSIONS).astype(int)

# デバッグ：クラス別実施日数（時間帯内だけで）
st.write("【デバッグ】クラス別フォーム実施日数（時間帯内のみ）")
dbg_days = (
    form_in.assign(date=form_in["ts_key"].dt.date)
    .groupby("class_key")["date"]
    .nunique()
)
st.write(dbg_days)

st.write("【デバッグ】form_submit_count 最大値（時間帯内のみ）:", int(submit_cnt["form_submit_count"].max() if len(submit_cnt) else 0))

# -----------------------
# 名簿に反映（class + student_no でJOIN）
# -----------------------
roster_enriched = roster_master.copy()
roster_enriched["email"] = ""  # 名簿にemail列が無い想定でもOK

roster_enriched = roster_enriched.merge(latest_email, on=["class", "student_no"], how="left", suffixes=("", "_new"))
roster_enriched["email"] = roster_enriched["email_new"].fillna(roster_enriched["email"])
roster_enriched = roster_enriched.drop(columns=["email_new"])

roster_enriched = roster_enriched.merge(submit_cnt, on=["class", "student_no"], how="left")
roster_enriched["form_submit_count"] = roster_enriched["form_submit_count"].fillna(0).astype(int)

st.markdown("### 名簿（時間帯内フォーム情報を反映後）")
st.dataframe(roster_enriched, use_container_width=True)

# -----------------------
# GradeBook
# -----------------------
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

# -----------------------
# Download
# -----------------------
excel_bytes = export_to_excel_bytes(roster_enriched, gradebook)
st.download_button(
    label="Excelをダウンロード（Roster＋GradeBook）",
    data=excel_bytes,
    file_name="WEB制作運用_採点台帳_自動生成.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
