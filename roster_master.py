import pandas as pd
from normalize import normalize_text

def load_roster_master(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp.columns = [normalize_text(c).lower() for c in tmp.columns]

    required = ["class", "timetable", "time", "student_no", "name"]
    missing = [c for c in required if c not in tmp.columns]
    if missing:
        raise ValueError(f"RosterMaster missing columns: {missing}")

    tmp["student_no"] = tmp["student_no"].map(normalize_text)
    tmp["name"] = tmp["name"].map(normalize_text)
    tmp["class"] = tmp["class"].map(normalize_text)
    tmp["timetable"] = tmp["timetable"].map(normalize_text)
    tmp["time"] = tmp["time"].map(normalize_text)

    tmp = tmp[tmp["student_no"] != ""]
    tmp = tmp.drop_duplicates(subset=["student_no"], keep="last").reset_index(drop=True)

    tmp["email"] = ""  # フォームから上書き
    return tmp[["class", "timetable", "time", "student_no", "name", "email"]]
