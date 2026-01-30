import streamlit as st
import pandas as pd

st.set_page_config(page_title="web-grade-app2 SAFE MODE", layout="wide")
st.title("SAFE MODE：アップロード確認")
st.caption("ここではアップロードと読み込みだけ確認します。ロジックは一切動かしません。")

roster_file = st.file_uploader("① 名簿（.xlsx / .csv）", type=["xlsx", "csv"], key="roster")
form_file   = st.file_uploader("② 統合フォーム（.xlsx / .csv）", type=["xlsx", "csv"], key="form")

def read_any_simple(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file), []
    if name.endswith(".xlsx") or name.endswith(".xls"):
        xls = pd.ExcelFile(file)
        return None, xls.sheet_names
    raise ValueError("Unsupported file type")

def read_excel_sheet(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)

# 名簿の確認
if roster_file:
    st.subheader("名簿の読み込み確認")
    if roster_file.name.lower().endswith(".xlsx"):
        _, sheets = read_any_simple(roster_file)
        s = st.selectbox("名簿シート", sheets, key="roster_sheet")
        df = read_excel_sheet(roster_file, s)
    else:
        df, _ = read_any_simple(roster_file)

    st.write("名簿：行数", len(df), "列数", len(df.columns))
    st.write("名簿列名:", list(df.columns))
    st.dataframe(df.head(20), use_container_width=True)

# フォームの確認
if form_file:
    st.subheader("フォームの読み込み確認")
    if form_file.name.lower().endswith(".xlsx"):
        _, sheets = read_any_simple(form_file)
        s = st.selectbox("フォームシート", sheets, key="form_sheet")
        df = read_excel_sheet(form_file, s)
    else:
        df, _ = read_any_simple(form_file)

    st.write("フォーム：行数", len(df), "列数", len(df.columns))
    st.write("フォーム列名:", list(df.columns))
    st.dataframe(df.head(20), use_container_width=True)

st.info("SAFE MODEが表示できていれば、アップロードは復旧しています。次はロジックを段階的に戻します。")
