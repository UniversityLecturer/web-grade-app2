import pandas as pd
from normalize import normalize_text

def count_form_submissions_by_class_studentno(
    df: pd.DataFrame,
    col_class: str,
    col_student_no: str,
    col_timestamp: str,
    cap: int = 15,
) -> pd.DataFrame:
    """
    class + student_no + 日付 でユニークに数える（= 1日1回）
    同日複数送信は1回扱い。
    """
    tmp = df[[col_class, col_student_no, col_timestamp]].copy()

    tmp["class"] = tmp[col_class].map(normalize_text)
    tmp["student_no"] = tmp[col_student_no].map(normalize_text)
    tmp["ts"] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp.dropna(subset=["ts"])
    tmp = tmp[(tmp["class"] != "") & (tmp["student_no"] != "")]

    tmp["date"] = tmp["ts"].dt.date

    # 同一日の重複提出を除外
    tmp = tmp.drop_duplicates(subset=["class", "student_no", "date"])

    out = (
        tmp.groupby(["class", "student_no"], as_index=False)["date"]
        .nunique()
        .rename(columns={"date": "form_submit_count"})
    )

    out["form_submit_count"] = out["form_submit_count"].clip(upper=cap).astype(int)
    return out


# 互換用（残しておく：app.pyが古い場合に備える）
def count_form_submissions_by_studentno(
    df: pd.DataFrame,
    col_student_no: str,
    col_timestamp: str,
    cap: int = 15,
) -> pd.DataFrame:
    """
    student_no + 日付でユニーク（= 1日1回）。
    ※クラスがない場合の暫定用（Noがクラスで重複する運用では非推奨）
    """
    tmp = df[[col_student_no, col_timestamp]].copy()
    tmp["student_no"] = tmp[col_student_no].map(normalize_text)
    tmp["ts"] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp.dropna(subset=["ts"])
    tmp = tmp[tmp["student_no"] != ""]

    tmp["date"] = tmp["ts"].dt.date
    tmp = tmp.drop_duplicates(subset=["student_no", "date"])

    out = (
        tmp.groupby(["student_no"], as_index=False)["date"]
        .nunique()
        .rename(columns={"date": "form_submit_count"})
    )

    out["form_submit_count"] = out["form_submit_count"].clip(upper=cap).astype(int)
    return out
