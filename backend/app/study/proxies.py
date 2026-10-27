from __future__ import annotations

import numpy as np
import pandas as pd

ANCHORS = {"dspd": 12.0, "ltbf": 7.0, "qd": 3.0}
CHURN_FLOOR = 0.05
PRE_AI_QUARTERS = [f"{y}Q{q}" for y in (2019, 2020) for q in range(1, 5)]


def dspd_proxy(n_prs, pre_ai_mean_prs, k):
    return np.clip(np.asarray(n_prs) / np.asarray(pre_ai_mean_prs) * k, 0, 50)


def ltbf_proxy(median_cycle_days, k):
    return np.clip(np.asarray(median_cycle_days) * k, 0, 30)


def qd_proxy(first_time_merge_rate, churn_ratio, k):
    churn = np.clip(np.asarray(churn_ratio), CHURN_FLOOR, None)
    return np.clip(np.asarray(first_time_merge_rate) * 10.0 / (churn * k), 0, 10)


def pre_ai_baseline(df: pd.DataFrame) -> pd.Series:
    return df[df["quarter"].isin(PRE_AI_QUARTERS)].groupby("project_id")["n_prs"].mean()


def pooled_medians(df: pd.DataFrame) -> dict:
    pre = df[df["quarter"].isin(PRE_AI_QUARTERS)]
    volume = pre["n_prs"] / pre["project_id"].map(pre_ai_baseline(df))
    quality = pre["first_time_merge_rate"] / pre["churn_ratio"].clip(lower=CHURN_FLOOR)
    return {"dspd": volume.median(), "ltbf": pre["median_cycle_days"].median(), "qd": quality.median()}


def calibrate(df: pd.DataFrame) -> dict:
    m = pooled_medians(df)
    return {
        "k_dspd": float(np.round(ANCHORS["dspd"] / m["dspd"], 2)),
        "k_ltbf": float(np.round(ANCHORS["ltbf"] / m["ltbf"], 2)),
        "k_qd": float(np.round(10 * m["qd"] / ANCHORS["qd"], 2)),
    }


def derive_inputs(df: pd.DataFrame, k: dict, baseline: pd.Series) -> pd.DataFrame:
    out = df.copy()
    base = out["project_id"].map(baseline)
    out["dspd"] = dspd_proxy(out["n_prs"], base, k["k_dspd"]).round(2)
    out["ltbf"] = ltbf_proxy(out["median_cycle_days"], k["k_ltbf"]).round(2)
    out["qd"] = qd_proxy(out["first_time_merge_rate"], out["churn_ratio"], k["k_qd"]).round(2)
    return out
