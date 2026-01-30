import pandas as pd
from typing import Tuple, List
from normalize import normalize_columns

def read_any(file, sheet_name: str | None = None) -> Tuple[pd.DataFrame, List[str]]:
    name = getattr(file, "name", "").lower()

    if name.endswith(".csv"):
        df = pd.read_csv(file)
        df.columns = normalize_columns(list(df.columns))
        return df, []

    if name.endswith(".xlsx") or name.endswith(".xls"):
        xls = pd.ExcelFile(file)
        if sheet_name is None:
            return pd.DataFrame(), xls.sheet_names
        df = pd.read_excel(file, sheet_name=sheet_name)
        df.columns = normalize_columns(list(df.columns))
        return df, xls.sheet_names

    raise ValueError("Unsupported file type. Please upload .xlsx or .csv")
