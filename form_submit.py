import pandas as pd
from normalize import normalize_text

def count_submissions_by_key(
    form_df: pd.DataFrame,
    key_cols: list[str],      # ["class", "student_no"]
    ts_col: str,
    cap: int | None = None
) -> pd.DataFrame:
    """
    提出回数を class + student_no + 日付 でユニークに数える（＝1日1回）
    """
    tmp = form_df[key_cols + [ts_col]].copy()

    # 正規化
    for k in key_cols:
        tmp[k] = tmp[k].map(normalize_text)
    tmp[ts_col] = pd.to_datetime(tmp[ts_col], errors="coerce")

    # 欠損除外
    tmp = tmp.dropna(subset=[ts_col])
    for k in key_cols:
        tmp = tmp[tmp[k] != ""]

    # 日付単位
    tmp["submit_date"] = tmp[ts_col].dt.date

    # 同一日重複を除外
    tmp = tmp.drop_duplicates(subset=key_cols + ["submit_date"])

    # 日付ユニーク数をカウント
    out = (
        tmp.groupby(key_cols, as_index=False)["submit_date"]
        .nunique()
        .rename(columns={"submit_date": "form_submit_count"})
    )

    if cap is not None:
        out["form_submit_count"] = out["form_submit_count"].clip(upper=cap)

    return out

# -----------------------------
# 互換用ラッパー（←これが重要）
# app.py がこの名前をimportしているので残す
# -----------------------------
def count_form_submissions_by_studentno(
    df: pd.DataFrame,
    col_student_no: str,
    col_timestamp: str,
    cap: int = 15
) -> pd.DataFrame:
    """
    旧アプリ互換：
    student_no × 日付 で 1日1回カウント
    ※ class無しで数える版（必要なら app.py側で classもキーにする）
    """
    tmp = df[[col_student_no, col_timestamp]].copy()
    tmp[col_student_no] = tmp[col_student_no].map(normalize_text)
    tmp[col_timestamp] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp.dropna(subset=[col_timestamp])
    tmp = tmp[tmp[col_student_no] != ""]

    tmp["submit_date"] = tmp[col_timestamp].dt.date
    tmp = tmp.drop_duplicates(subset=[col_student_no, "submit_date"])

    out = (
        tmp.groupby(col_student_no, as_index=False)["submit_date"]
        .nunique()
        .rename(columns={"submit_date": "form_submit_count"})
    )

    out["form_submit_count"] = out["form_submit_count"].clip(upper=cap).astype(int)
    return out.rename(columns={col_student_no: "student_no"})
