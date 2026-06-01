from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from app.core.fuzzy_engine import (
    DSPD_PARAMS, LTBF_PARAMS, QD_PARAMS,
    DSPD_UNIVERSE, LTBF_UNIVERSE, QD_UNIVERSE,
    _MFS_DSPD, _MFS_LTBF, _MFS_QD, infer,
)
from app.study.proxies import CHURN_FLOOR

import skfuzzy as fuzz

# ---------------------------------------------------------------------------
# Data location & era definitions
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _first_existing(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


# Sample/derived data may live at the project root (local checkout) or inside
# the backend image (Docker). Check both so the study loads in either layout.
SAMPLE_CSV = _first_existing(
    ROOT / "data" / "sample" / "quarterly_metrics.csv",
    BACKEND_ROOT / "data" / "sample" / "quarterly_metrics.csv",
)
DERIVED_CSV = _first_existing(
    ROOT / "data" / "derived" / "quarterly_metrics.csv",
    BACKEND_ROOT / "data" / "derived" / "quarterly_metrics.csv",
)

ERAS = {
    "pre_ai":     [f"{y}Q{q}" for y in (2019, 2020) for q in range(1, 5)],
    "transition": ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2", "2022Q3"],
    "ai_era":     ["2022Q4", "2023Q1", "2023Q2", "2023Q3", "2023Q4",
                   "2024Q1", "2024Q2", "2024Q3", "2024Q4"],
}

PROJECT_META = {
    "vscode":     {"repo": "microsoft/vscode",       "language": "TypeScript", "governance": "Corporate"},
    "react":      {"repo": "facebook/react",         "language": "JavaScript", "governance": "Corporate-OSS"},
    "kubernetes": {"repo": "kubernetes/kubernetes",  "language": "Go",         "governance": "Foundation"},
    "django":     {"repo": "django/django",          "language": "Python",     "governance": "Foundation"},
    "numpy":      {"repo": "numpy/numpy",            "language": "Python",     "governance": "Community"},
    "rust":       {"repo": "rust-lang/rust",         "language": "Rust",       "governance": "Foundation"},
}

# Milestone markers (quarter index on the 24-quarter axis) for UI dashed lines.
MILESTONES = {"Copilot beta": "2021Q3", "ChatGPT GA": "2022Q4", "GPT-4": "2023Q2"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_sample() -> tuple[pd.DataFrame, str]:
    """Prefer live-fetched derived data; fall back to bundled sample."""
    if DERIVED_CSV.exists():
        return pd.read_csv(DERIVED_CSV), "live"
    if SAMPLE_CSV.exists():
        return pd.read_csv(SAMPLE_CSV), "sample"
    # Last resort: regenerate the bundled sample in-memory.
    from app.study.profiles import generate_sample
    return generate_sample(), "generated"


# ---------------------------------------------------------------------------
# Apply DSS to every project-quarter
# ---------------------------------------------------------------------------
def apply_dss(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, r in df.iterrows():
        result = infer(float(r["dspd"]), float(r["ltbf"]), float(r["qd"]))
        fired = [a["id"] for a in result.rule_activations if a["firing_strength"] > 0]
        records.append({
            "project_id": r["project_id"], "quarter": r["quarter"],
            "dspd": round(float(r["dspd"]), 2),
            "ltbf": round(float(r["ltbf"]), 2),
            "qd": round(float(r["qd"]), 2),
            "phs": result.phs,
            "linguistic_state": result.linguistic_state,
            "rules_fired": ",".join(fired) if fired else "NONE",
            "n_rules_fired": len(fired),
        })
    return pd.DataFrame(records)


def _cliffs_delta(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    n_gt = sum((x > y) for x in a for y in b)
    n_lt = sum((x < y) for x in a for y in b)
    return (n_gt - n_lt) / (len(a) * len(b))


def era_comparison(df: pd.DataFrame) -> List[Dict]:
    pre, ai = set(ERAS["pre_ai"]), set(ERAS["ai_era"])
    out = []
    for pid, sub in df.groupby("project_id"):
        pre_phs = sub.loc[sub["quarter"].isin(pre), "phs"].values
        ai_phs = sub.loc[sub["quarter"].isin(ai), "phs"].values
        if len(pre_phs) < 2 or len(ai_phs) < 2:
            continue
        u, p = stats.mannwhitneyu(ai_phs, pre_phs, alternative="two-sided")
        out.append({
            "project_id": pid,
            "repo": PROJECT_META.get(pid, {}).get("repo", pid),
            "n_pre": len(pre_phs), "n_ai": len(ai_phs),
            "phs_pre_mean": round(float(np.mean(pre_phs)), 2),
            "phs_ai_mean": round(float(np.mean(ai_phs)), 2),
            "phs_shift": round(float(np.mean(ai_phs) - np.mean(pre_phs)), 2),
            "mwu_U": round(float(u), 2),
            "mwu_p": round(float(p), 4),
            "cliffs_delta": round(float(_cliffs_delta(ai_phs, pre_phs)), 3),
            "significant_05": bool(p < 0.05),
        })
    return sorted(out, key=lambda r: -r["phs_shift"])


def discriminative_power(df: pd.DataFrame) -> Dict:
    phs = df["phs"].values
    states = df["linguistic_state"].values
    counts = Counter(states)
    total = sum(counts.values())
    probs = np.array([c / total for c in counts.values()])
    entropy_bits = float(-(probs * np.log2(probs)).sum())
    entropy_max = float(np.log2(5))
    groups = [g["phs"].values for _, g in df.groupby("project_id")]
    h, p = stats.kruskal(*groups)
    fallback_pct = float((df["rules_fired"] == "NONE").sum()) / len(df) * 100
    return {
        "n_observations": int(len(df)),
        "n_projects": int(df["project_id"].nunique()),
        "phs_mean": round(float(np.mean(phs)), 2),
        "phs_std": round(float(np.std(phs)), 2),
        "phs_min": round(float(np.min(phs)), 2),
        "phs_max": round(float(np.max(phs)), 2),
        "phs_iqr": round(float(np.percentile(phs, 75) - np.percentile(phs, 25)), 2),
        "state_distribution": dict(counts),
        "entropy_bits": round(entropy_bits, 3),
        "entropy_max_bits": round(entropy_max, 3),
        "entropy_normalised": round(entropy_bits / entropy_max, 3),
        "kruskal_H": round(float(h), 2),
        "kruskal_p": float(p),
        "kruskal_significant_05": bool(p < 0.05),
        "no_rule_fallback_pct": round(fallback_pct, 2),
        "no_rule_fallback_n": int((df["rules_fired"] == "NONE").sum()),
    }


# ---------------------------------------------------------------------------
# Top-level study runner (consumed by /api/study)
# ---------------------------------------------------------------------------
def run_study(rule_mode: str = "base12") -> Dict:
    """Run the full study and return everything the UI needs.

    rule_mode: 'base12' (default-of-record, the manuscript's 12-rule base) or
    'extended27' (the completed rule base; see fuzzy_engine.set_rule_mode).
    """
    from app.core.fuzzy_engine import set_rule_mode, active_rule_count
    set_rule_mode(rule_mode)

    df_raw, source = load_sample()
    df = apply_dss(df_raw)

    timeseries = df.to_dict(orient="records")
    dp = discriminative_power(df)
    eras = era_comparison(df)

    # Heatmap matrix: project × quarter → state (ordered for the UI)
    quarters = ERAS["pre_ai"] + ERAS["transition"] + ERAS["ai_era"]
    project_order = list(PROJECT_META.keys())
    heatmap = []
    for pid in project_order:
        sub = df[df["project_id"] == pid].set_index("quarter")
        heatmap.append({
            "project_id": pid,
            "repo": PROJECT_META[pid]["repo"],
            "cells": [{
                "quarter": q,
                "state": sub.loc[q, "linguistic_state"] if q in sub.index else None,
                "phs": float(sub.loc[q, "phs"]) if q in sub.index else None,
            } for q in quarters],
        })

    return {
        "source": source,
        "rule_mode": rule_mode,
        "active_rules": active_rule_count(),
        "quarters": quarters,
        "milestones": MILESTONES,
        "project_meta": PROJECT_META,
        "discriminative_power": dp,
        "era_comparison": eras,
        "timeseries": timeseries,
        "heatmap": heatmap,
    }


# ---------------------------------------------------------------------------
# Sensitivity sweep (reproduces Addendum Table XI; consumed by /api/study/sensitivity)
# ---------------------------------------------------------------------------
_LABELS = {
    "DSPD": ["low", "average", "high"],
    "LTBF": ["rapid", "nominal", "sluggish"],
    "Qd":   ["fragile", "stable", "resilient"],
}
_UNIVERSES = {"DSPD": DSPD_UNIVERSE, "LTBF": LTBF_UNIVERSE, "Qd": QD_UNIVERSE}
_MFS = {"DSPD": _MFS_DSPD, "LTBF": _MFS_LTBF, "Qd": _MFS_QD}

KS_GRID = {
    "DSPD": [8, 10, 12, 14, 15, 16, 18, 20, 25, 30, 35],
    "LTBF": [2, 3, 4, 5, 6, 7, 8, 10, 12],
    "Qd":   [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8],
}


def _classify(axis: str, value: float) -> str:
    universe = _UNIVERSES[axis]
    best = _LABELS[axis][0]
    best_mu = float(fuzz.interp_membership(universe, _MFS[axis][best], value))
    for lbl in _LABELS[axis][1:]:
        mu = float(fuzz.interp_membership(universe, _MFS[axis][lbl], value))
        if mu > best_mu:
            best, best_mu = lbl, mu
    return best


def _shannon(counts: Dict[str, int]) -> float:
    n = sum(counts.values())
    if n == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / n
            h -= p * math.log2(p)
    return h


def sensitivity_sweep() -> Dict:
    df_raw, source = load_sample()
    df = df_raw.copy()
    df["project_mean_prs"] = df.groupby("project_id")["n_prs"].transform("mean")

    def scaled(axis, k):
        if axis == "DSPD":
            return np.clip(df["n_prs"] / df["project_mean_prs"] * k, 0, 50).values
        if axis == "LTBF":
            return np.clip(df["median_cycle_days"] * k, 0, 30).values
        return np.clip(df["first_time_merge_rate"] * 10
                       / (df["churn_ratio"].clip(lower=CHURN_FLOOR) * k), 0, 10).values

    result = {"source": source, "max_entropy_bits": round(math.log2(3), 4), "axes": {}}
    for axis in ("DSPD", "LTBF", "Qd"):
        rows = []
        for k in KS_GRID[axis]:
            vals = scaled(axis, k)
            counts = {lbl: 0 for lbl in _LABELS[axis]}
            for v in vals:
                counts[_classify(axis, v)] += 1
            rows.append({"k": k, "counts": counts, "entropy": round(_shannon(counts), 4)})
        best = max(rows, key=lambda r: r["entropy"])
        result["axes"][axis] = {
            "labels": _LABELS[axis],
            "rows": rows,
            "optimal_k": best["k"],
            "optimal_entropy": best["entropy"],
        }
    return result
