import pandas as pd

REPORT_MAP = {
    "完全完成": 20,
    "一部間違い": 15,
    "データ間違い": 10,
    "未記入": 5,
    "未提出": 0,
}

FINAL_MAP = {"未提出": 0, "提出": 5, "良い": 10}

def grade_letter(score: float, b: dict) -> str:
    if score >= b["S"]: return "S"
    if score >= b["A"]: return "A"
    if score >= b["B"]: return "B"
    if score >= b["C"]: return "C"
    return "D"

def build_gradebook(roster: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    total_sessions = int(cfg["attendance"]["total_sessions"])
    max_att_points = float(cfg["attendance"]["max_points"])
    gate = float(cfg["attendance"]["gate_rate"])

    learning = cfg["learning"]
    boundary = cfg["grade_boundary"]
    defaults = cfg.get("defaults", {})

    gb = roster.copy()

    # 入力欄
    gb["absent_full"] = 0
    gb["report_status"] = defaults.get("report_status", "一部間違い")
    gb["paiza_done"] = 0
    gb["site_requirements_done"] = 0
    gb["site_requirements_total"] = int(defaults.get("site_requirements_total", 8))
    gb["final_status"] = defaults.get("final_status", "提出")
    gb["attitude_penalty"] = 0
    if "form_submit_count" not in gb.columns:
        gb["form_submit_count"] = 0
    gb["form_submit_count"] = gb["form_submit_count"].fillna(0).astype(int)

    # 出席
    gb["attended"] = (total_sessions - gb["absent_full"].astype(int)).clip(lower=0)
    gb["attendance_rate"] = (gb["attended"] / total_sessions).fillna(0)
    gb["attendance_points_30"] = (gb["attendance_rate"] * max_att_points).round(1)

    # 学習
    gb["report_points_20"] = gb["report_status"].map(REPORT_MAP).fillna(0).astype(float)
    gb["paiza_points_10"] = (gb["paiza_done"].clip(upper=27) / 27 * float(learning["paiza"])).round(1)

    denom = gb["site_requirements_total"].replace(0, 1)
    gb["site_points_20"] = (gb["site_requirements_done"].clip(lower=0) / denom * float(learning["site"])).round(1)

    gb["form_points_10"] = (gb["form_submit_count"].clip(upper=total_sessions) / total_sessions * float(learning["form"])).round(1)
    gb["final_points_10"] = gb["final_status"].map(FINAL_MAP).fillna(0).astype(float)

    gb["learning_points_70_raw"] = (
        gb["report_points_20"]
        + gb["paiza_points_10"]
        + gb["site_points_20"]
        + gb["form_points_10"]
        + gb["final_points_10"]
    ).round(1)
    gb["learning_points_70"] = (gb["learning_points_70_raw"] - gb["attitude_penalty"]).clip(lower=0).round(1)

    # 総合・判定
    gb["total_100"] = (gb["attendance_points_30"] + gb["learning_points_70"]).round(1)
    gb["grade"] = gb["total_100"].apply(lambda x: grade_letter(float(x), boundary))

    gb["attendance_gate"] = gb["attendance_rate"].apply(lambda r: "OK" if r >= gate else "NG(出席不足)")
    gb["final_judgement"] = gb.apply(
        lambda r: "不可(出席不足)" if r["attendance_rate"] < gate else ("可" if r["total_100"] >= boundary["C"] else "不可"),
        axis=1
    )

    gb["mail_line"] = gb.apply(
        lambda r: f"結果：{r['total_100']}点（{r['grade']}） 出席率：{int(round(r['attendance_rate']*100))}% 判定：{r['final_judgement']}",
        axis=1
    )

    return gb
