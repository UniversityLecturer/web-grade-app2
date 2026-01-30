import io
import streamlit as st
import pandas as pd

st.set_page_config(page_title="web-grade-app2 SAFE MODE+", layout="wide")
st.title("SAFE MODE+：アップロード確認＋ダウンロード")
st.caption("アップロード→読み込み→そのままExcel化してダウンロードできるかだけ確認します。")

roster_file = st.file_uploader("① 名簿（.xlsx / .csv）", type=["xlsx", "csv"], key="roster")
form_file   = st.file_uploader("② 統合フォーム（.xlsx / .csv）", type=["xlsx", "csv"], key="form")

def read_df(file, sheet_key: str):
    name = file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(file)

    if name.endswith(".xlsx") or name.endswith(".xls"):
        xls = pd.ExcelFile(file)
        sheet = st.selectbox(f"{sheet_key} シート", xls.sheet_names, key=f"{sheet_key}_sheet")
        return pd.read_excel(file, sheet_name=sheet)

    raise ValueError("Unsupported file type")

def to_excel_bytes(dfs: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        for sheet_name, df in dfs.items():
            df.to_excel(w, index=False, sheet_name=sheet_name)
            ws = w.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            # 列幅ざっくり
            for i, c in enumerate(df.columns):
                try:
                    mx = int(df[c].astype(str).map(len).max())
                except Exception:
                    mx = 10
                ws.set_column(i, i, max(10, min(45, mx + 2)))
    return buf.getvalue()

dfs = {}

# 名簿
if roster_file:
    st.subheader("名簿の読み込み確認")
    roster_df = read_df(roster_file, "roster")
    st.write("名簿：行数", len(roster_df), "列数", len(roster_df.columns))
    st.write("名簿列名:", list(roster_df.columns))
    st.dataframe(roster_df.head(20), use_container_width=True)
    dfs["RosterRaw"] = roster_df

# フォーム
if form_file:
    st.subheader("フォームの読み込み確認")
    form_df = read_df(form_file, "form")
    st.write("フォーム：行数", len(form_df), "列数", len(form_df.columns))
    st.write("フォーム列名:", list(form_df.columns))
    st.dataframe(form_df.head(20), use_container_width=True)
    dfs["FormRaw"] = form_df

st.divider()

if dfs:
    st.subheader("ダウンロード確認")
    excel_bytes = to_excel_bytes(dfs)
    st.download_button(
        label="Excelをダウンロード（RosterRaw＋FormRaw）",
        data=excel_bytes,
        file_name="safe_mode_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.success("ダウンロードボタンが押せればOK。次は採点ロジックを段階的に戻します。")
else:
    st.info("名簿またはフォームをアップロードすると、ダウンロードボタンが出ます。")
