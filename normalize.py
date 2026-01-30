import re
from typing import Any, List

def normalize_text(x: Any) -> str:
    """
    文字列正規化用ユーティリティ
    - None → ""
    - 改行（CR/LF）を半角スペースに変換
    - 連続する空白を1つに圧縮
    - 前後の空白を除去
    """
    if x is None:
        return ""
    s = str(x)
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def normalize_columns(cols: List[str]) -> List[str]:
    """
    DataFrameの列名正規化
    - 改行除去
    - 余分な空白除去
    """
    return [normalize_text(c) for c in cols]
