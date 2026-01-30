import io
import pandas as pd

def export_to_excel_bytes(roster: pd.DataFrame, gradebook: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        roster.to_excel(writer, index=False, sheet_name="Roster")
        gradebook.to_excel(writer, index=False, sheet_name="GradeBook")

        for sheet_name, df in [("Roster", roster), ("GradeBook", gradebook)]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            for i, col in enumerate(df.columns):
                try:
                    max_len = int(df[col].astype(str).map(len).max())
                except Exception:
                    max_len = 10
                ws.set_column(i, i, max(10, min(45, max_len + 2)))
    return output.getvalue()
