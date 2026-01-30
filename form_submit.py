import pandas as pd
from normalize import normalize_text

def count_form_submissions_by_studentno(df: pd.DataFrame, col_student_no: str, col_timestamp: str, cap: int = 15) -> pd.DataFrame:
    base = df[[col_student_no, col_timestamp]].copy()
    base[col_student_no] = base[col_student_no].map(normalize_text)
    base[col_timestamp] = pd.to_datetime(base[col_timestamp], errors="coerce")

    base = base[base[col_student_no] != ""]
    base = base.dropna(subset=[col_timestamp])

    base["date"] = base[col_timestamp].dt.date
    base = base.drop_duplicates(subset=[col_student_no, "date"])

    out = (
        base.groupby(col_student_no, as_index=False)
            .size()
            .rename(columns={"size": "form_submit_count"})
    )
    out["form_submit_count"] = out["form_submit_count"].clip(upper=cap).astype(int)
    return out.rename(columns={col_student_no: "student_no"})
