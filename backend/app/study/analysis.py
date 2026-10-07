from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import skfuzzy as fuzz
from scipy import stats

from app.core.fuzzy_engine import (
    DSPD_UNIVERSE, LTBF_UNIVERSE, QD_UNIVERSE,
    _MFS_DSPD, _MFS_LTBF, _MFS_QD,
    RULES, infer,
)
from app.study.proxies import (
    ANCHORS, PRE_AI_QUARTERS, calibrate, derive_inputs, pooled_medians, pre_ai_baseline,
)

SIGNALS_CSV = Path(__file__).resolve().parents[2] / "data" / "study" / "quarterly_signals.csv"
SOURCE = {
    "description": "Merged pull requests collected from GitHub in October 2026",
    "merged_prs_collected": 110481,
    "bot_authored_excluded": 615,
    "replication_package": "https://github.com/gadinaelena3/oss-dora-fuzzy",
}
ERAS = {
    "pre_ai": PRE_AI_QUARTERS,
    "transition": ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2", "2022Q3"],
    "ai_era": ["2022Q4", "2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2024Q3", "2024Q4"],
}
ALPHA_BONFERRONI = 0.05 / 6
PROJECT_META = {
    "vscode": {"repo": "microsoft/vscode", "language": "TypeScript", "governance": "Corporate"},
    "react": {"repo": "facebook/react", "language": "JavaScript", "governance": "Corporate-OSS"},
    "kubernetes": {"repo": "kubernetes/kubernetes", "language": "Go", "governance": "Foundation"},
    "django": {"repo": "django/django", "language": "Python", "governance": "Foundation"},
    "numpy": {"repo": "numpy/numpy", "language": "Python", "governance": "Community"},
    "rust": {"repo": "rust-lang/rust", "language": "Rust", "governance": "Foundation"},
}
MILESTONES = {"Copilot beta": "2021Q2", "ChatGPT GA": "2022Q4", "GPT-4": "2023Q1"}
WORKFLOW_BREAK = "2022Q2"
ENTROPY_GRID = {
    "DSPD": [8, 10, None, 14, 16, 20, 25],
    "LTBF": [3, 4, 5, 6, None, 8, 10, 12],
    "Qd": [2, 3, 4, None, 5, 6],
}
_AXIS = {
    "DSPD": ("k_dspd", "dspd", DSPD_UNIVERSE, _MFS_DSPD, ["low", "average", "high"]),
    "LTBF": ("k_ltbf", "ltbf", LTBF_UNIVERSE, _MFS_LTBF, ["rapid", "nominal", "sluggish"]),
    "Qd": ("k_qd", "qd", QD_UNIVERSE, _MFS_QD, ["fragile", "stable", "resilient"]),
}


def load_signals() -> pd.DataFrame:
    return pd.read_csv(SIGNALS_CSV)


def apply_dss(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, r in df.iterrows():
        result = infer(float(r["dspd"]), float(r["ltbf"]), float(r["qd"]))
        fired = [a["id"] for a in result.rule_activations if a["firing_strength"] > 0]
        records.append({
            "project_id": r["project_id"], "quarter": r["quarter"],
            "n_prs": int(r["n_prs"]),
            "median_cycle_hours": round(float(r["median_cycle_days"]) * 24, 2),
            "first_time_merge_rate": round(float(r["first_time_merge_rate"]), 3),
            "churn_ratio": round(float(r["churn_ratio"]), 3),
            "dspd": float(r["dspd"]), "ltbf": float(r["ltbf"]), "qd": float(r["qd"]),
            "phs": result.phs,
            "linguistic_state": result.linguistic_state,
            "rules_fired": ",".join(fired) if fired else "NONE",
            "n_rules_fired": len(fired),
        })
    return pd.DataFrame(records)


def _cliffs_delta(a, b) -> float:
    gt = sum(x > y for x in a for y in b)
    lt = sum(x < y for x in a for y in b)
    return (gt - lt) / (len(a) * len(b))


def era_comparison(df: pd.DataFrame) -> List[Dict]:
    pre, ai = set(ERAS["pre_ai"]), set(ERAS["ai_era"])
    out = []
    for pid, sub in df.groupby("project_id"):
        a = sub.loc[sub["quarter"].isin(pre), "phs"].values
        b = sub.loc[sub["quarter"].isin(ai), "phs"].values
        u, p = stats.mannwhitneyu(b, a, alternative="two-sided")
        out.append({
            "project_id": pid,
            "repo": PROJECT_META.get(pid, {}).get("repo", pid),
            "n_pre": len(a), "n_ai": len(b),
            "phs_pre_mean": round(float(np.mean(a)), 2),
            "phs_ai_mean": round(float(np.mean(b)), 2),
            "phs_shift": round(float(np.mean(b) - np.mean(a)), 2),
            "mwu_U": round(float(u), 2),
            "mwu_p": round(float(p), 4),
            "cliffs_delta": round(float(_cliffs_delta(b, a)), 3),
            "significant_05": bool(p < 0.05),
            "significant_bonferroni": bool(p < ALPHA_BONFERRONI),
        })
    return sorted(out, key=lambda r: -r["phs_shift"])


def discriminative_power(df: pd.DataFrame) -> Dict:
    phs = df["phs"].values
    counts = Counter(df["linguistic_state"].values)
    probs = np.array(list(counts.values())) / len(df)
    entropy = float(-(probs * np.log2(probs)).sum())
    h, p = stats.kruskal(*[g["phs"].values for _, g in df.groupby("project_id")])
    fallback = df["rules_fired"] == "NONE"
    return {
        "n_observations": int(len(df)),
        "n_projects": int(df["project_id"].nunique()),
        "phs_mean": round(float(np.mean(phs)), 2),
        "phs_std": round(float(np.std(phs)), 2),
        "phs_min": round(float(np.min(phs)), 2),
        "phs_max": round(float(np.max(phs)), 2),
        "phs_iqr": round(float(np.percentile(phs, 75) - np.percentile(phs, 25)), 2),
        "state_distribution": dict(counts),
        "entropy_bits": round(entropy, 3),
        "entropy_max_bits": round(float(np.log2(5)), 3),
        "entropy_normalised": round(entropy / float(np.log2(5)), 3),
        "kruskal_H": round(float(h), 2),
        "kruskal_p": float(p),
        "kruskal_significant_05": bool(p < 0.05),
        "no_rule_fallback_pct": round(float(fallback.mean() * 100), 2),
        "no_rule_fallback_n": int(fallback.sum()),
        "no_rule_fallback_by_project": {k: int(v) for k, v in fallback.groupby(df["project_id"]).sum().items()},
    }


def _span(s: pd.Series, scale: float = 1.0, digits: int = 1) -> List[float]:
    return [round(float(s.min()) * scale, digits), round(float(s.max()) * scale, digits)]


def workflow_change(signals: pd.DataFrame, project: str = "vscode") -> Dict:
    s = signals[signals["project_id"] == project]
    out = {"project_id": project, "break_quarter": WORKFLOW_BREAK}
    for label, part in (("before", s[s["quarter"] < WORKFLOW_BREAK]), ("after", s[s["quarter"] >= WORKFLOW_BREAK])):
        out[label] = {
            "quarters": int(len(part)),
            "merged_prs": [int(part["n_prs"].min()), int(part["n_prs"].max())],
            "median_cycle_hours": _span(part["median_cycle_days"], 24),
            "merged_within_1h_pct": _span(part["share_under_1h"], 100),
            "merged_without_review_pct": _span(part["share_no_review"], 100),
            "merged_by_own_author_pct": _span(part["share_self_merged"], 100),
            "from_forks_pct": _span(part["share_from_fork"], 100),
        }
    return out


def _run(signals: pd.DataFrame, k: Dict, baseline: pd.Series) -> pd.DataFrame:
    return apply_dss(derive_inputs(signals, k, baseline))


def run_study() -> Dict:
    signals = load_signals()
    k = calibrate(signals)
    baseline = pre_ai_baseline(signals)
    df = _run(signals, k, baseline)

    quarters = ERAS["pre_ai"] + ERAS["transition"] + ERAS["ai_era"]
    heatmap = []
    for pid in PROJECT_META:
        sub = df[df["project_id"] == pid].set_index("quarter")
        heatmap.append({
            "project_id": pid,
            "repo": PROJECT_META[pid]["repo"],
            "cells": [{
                "quarter": q,
                "state": sub.loc[q, "linguistic_state"] if q in sub.index else None,
                "phs": float(sub.loc[q, "phs"]) if q in sub.index else None,
                "fallback": bool(sub.loc[q, "rules_fired"] == "NONE") if q in sub.index else None,
            } for q in quarters],
        })

    return {
        "source": SOURCE,
        "n_pull_requests": int(signals["n_prs"].sum()),
        "active_rules": len(RULES),
        "scaling_factors": k,
        "alpha_bonferroni": round(ALPHA_BONFERRONI, 4),
        "quarters": quarters,
        "milestones": MILESTONES,
        "project_meta": PROJECT_META,
        "discriminative_power": discriminative_power(df),
        "era_comparison": era_comparison(df),
        "workflow_change": workflow_change(signals),
        "timeseries": df.to_dict(orient="records"),
        "heatmap": heatmap,
    }


def _zone(axis: str, value: float) -> str:
    _, _, universe, mfs, labels = _AXIS[axis]
    mu = {lbl: float(fuzz.interp_membership(universe, mfs[lbl], value)) for lbl in labels}
    return max(labels, key=lambda lbl: mu[lbl])


def _entropy(counts: Dict[str, int]) -> float:
    n = sum(counts.values())
    return -sum(c / n * math.log2(c / n) for c in counts.values() if c > 0)


def calibration_report() -> Dict:
    signals = load_signals()
    k0 = calibrate(signals)
    baseline = pre_ai_baseline(signals)
    medians = pooled_medians(signals)

    axes = {}
    for axis, (key, col, _, _, labels) in _AXIS.items():
        rows = []
        for cand in ENTROPY_GRID[axis]:
            k = dict(k0, **({key: cand} if cand is not None else {}))
            values = derive_inputs(signals, k, baseline)[col]
            counts = {lbl: 0 for lbl in labels}
            for v in values:
                counts[_zone(axis, float(v))] += 1
            rows.append({"k": k[key], "reported": cand is None, "counts": counts, "entropy": round(_entropy(counts), 3)})
        best = max(rows, key=lambda r: r["entropy"])
        axes[axis] = {
            "labels": labels,
            "pooled_pre_ai_median": round(medians[col], 3),
            "anchor": ANCHORS[col],
            "k": k0[key],
            "rows": rows,
            "entropy_max_k": best["k"],
            "entropy_max": best["entropy"],
        }

    reference = _run(signals, k0, baseline)
    held_out = []
    for pid in PROJECT_META:
        k = calibrate(signals[signals["project_id"] != pid])
        own = signals[signals["project_id"] == pid]
        d = _run(own, k, baseline)
        ref = reference[reference["project_id"] == pid]
        era = era_comparison(d)[0]
        held_out.append({
            "project_id": pid, **k,
            "cliffs_delta": era["cliffs_delta"], "mwu_p": era["mwu_p"],
            "significant_bonferroni": era["significant_bonferroni"],
            "quarters_state_changed": int((d["linguistic_state"].values != ref["linguistic_state"].values).sum()),
        })

    return {
        "scaling_factors": k0,
        "anchors": ANCHORS,
        "n_pre_ai_project_quarters": int(signals["quarter"].isin(PRE_AI_QUARTERS).sum()),
        "max_entropy_bits": round(math.log2(3), 4),
        "axes": axes,
        "held_out": held_out,
    }
