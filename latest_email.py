import pandas as pd
from normalize import normalize_text

def latest_email_by_student(df_form: pd.DataFrame, col_student_no: str, col_email: str, col_timestamp: str) -> pd.DataFrame:
    tmp = df_form[[col_student_no, col_email, col_timestamp]].copy()
    tmp[col_student_no] = tmp[col_student_no].map(normalize_text)
    tmp[col_email] = tmp[col_email].map(normalize_text).str.lower()
    tmp[col_timestamp] = pd.to_datetime(tmp[col_timestamp], errors="coerce")

    tmp = tmp[(tmp[col_student_no] != "") & (tmp[col_email] != "")]
    tmp = tmp.dropna(subset=[col_timestamp])

    tmp = tmp.sort_values(col_timestamp).drop_duplicates(subset=[col_student_no], keep="last")

    return tmp[[col_student_no, col_email]].rename(columns={col_student_no: "student_no", col_email: "email"})
