import pandas as pd
from normalize import normalize_text

def count_submissions_by_key(
    form_df: pd.DataFrame,
    key_cols: list[str],      # ["class", "student_no"]
    ts_col: str,
    cap: int | None = None
) -> pd.DataFrame:
    """
    フォーム提出回数を
    - class + student_no + 日付
    でユニークに数える（＝1日1回）

    同じ日に複数送信しても 1 回扱い。
    """

    # 必要列だけ抜き出し
    tmp = form_df[key_cols + [ts_col]].copy()

    # 正規化
    for k in key_cols:
        tmp[k] = tmp[k].map(normalize_text)

    tmp[ts_col] = pd.to_datetime(tmp[ts_col], errors="coerce")

    # 欠損除外
    tmp = tmp.dropna(subset=[ts_col])
    for k in key_cols:
        tmp = tmp[tmp[k] != ""]

    # ★ 日付単位に落とす（ここが最重要）
    tmp["submit_date"] = tmp[ts_col].dt.date

    # ★ 同一日の重複提出を除外
    tmp = tmp.drop_duplicates(subset=key_cols + ["submit_date"])

    # ★ 日付のユニーク数をカウント
    out = (
        tmp.groupby(key_cols, as_index=False)["submit_date"]
        .nunique()
        .rename(columns={"submit_date": "form_submit_count"})
    )

    # 上限（必要なら）
    if cap is not None:
        out["form_submit_count"] = out["form_submit_count"].clip(upper=cap)

    return out

