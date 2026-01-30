import pandas as pd
from normalize import normalize_text

def latest_email_by_class_studentno(
    df_form: pd.DataFrame,
    col_class: str,
    col_student_no: str,
    col_email: str,
    col_timestamp: str
) -> pd.DataFrame:
    """
    class + student_no ごとに、最新タイムスタンプのemailを採用
    """
    tmp = df_form[[col_class, col_student_no, col_email, col_timestamp]].copy()

    tmp["class"] = tmp[col_class].map(normalize_text)
    tmp["student_no"] = tmp[col_student_no].map(normalize_text)
    tmp["email"] = tmp[col_email].map(normalize_text).str.lower()
    tmp["ts"] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp.dropna(subset=["ts"])
    tmp = tmp[(tmp["class"] != "") & (tmp["student_no"] != "") & (tmp["email"] != "")]

    # 最新を採用
    tmp = tmp.sort_values("ts").drop_duplicates(subset=["class", "student_no"], keep="last")

    return tmp[["class", "student_no", "email"]]


# 互換用（残しておく）
def latest_email_by_student(
    df_form: pd.DataFrame,
    col_student_no: str,
    col_email: str,
    col_timestamp: str
) -> pd.DataFrame:
    """
    student_no ごとに、最新emailを採用（※Noがクラスで重複する運用では非推奨）
    """
    tmp = df_form[[col_student_no, col_email, col_timestamp]].copy()
    tmp["student_no"] = tmp[col_student_no].map(normalize_text)
    tmp["email"] = tmp[col_email].map(normalize_text).str.lower()
    tmp["ts"] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp.dropna(subset=["ts"])
    tmp = tmp[(tmp["student_no"] != "") & (tmp["email"] != "")]

    tmp = tmp.sort_values("ts").drop_duplicates(subset=["student_no"], keep="last")
    return tmp[["student_no", "email"]]
