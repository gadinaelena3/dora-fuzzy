"""
GitHub-signal → DSS-input proxy layer.
======================================

Maps raw public GitHub signals (merged-PR counts, PR cycle times, code churn)
into the three DSS input universes (DSPD ∈ [0,50], LTBF ∈ [0,30], Qd ∈ [0,10]).

Scaling factors
---------------
The three scaling factors are NOT theoretically derived; they are calibration
parameters selected to map OSS-scale signals into the fuzzy universes of
Section 3. Each was swept over a candidate grid and the value that MAXIMISES
the Shannon entropy of the peak-membership distribution against the actual
fuzzy sets was selected (Addendum, Table XI):

    k_DSPD = 14   (entropy maximum, H = 1.294 bits)
    k_LTBF = 8    (entropy maximum, H = 1.582 bits, within 0.003 of log2(3))
    k_Qd   = 3    (entropy maximum, H = 1.155 bits)

These constants are the SINGLE SOURCE OF TRUTH for the proxy layer. The
manuscript 5.2, the Addendum Table XI, ``docs/METHODOLOGY.md``, and
``scripts/sensitivity_analysis`` all reference the values defined here.
A regression test (``tests/test_calibration.py``) asserts they never drift.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Entropy-calibrated scaling factors (Addendum, Table XI). DO NOT EDIT without
# re-running scripts/sensitivity_analysis and updating the manuscript.
# ---------------------------------------------------------------------------
K_DSPD: int = 14
K_LTBF: int = 8
K_QD:   int = 3

# Churn ratio is floored to guard against a near-zero denominator. The minimum
# churn ratio observed in the study sample is 0.078, so this floor is never
# active and the Qd proxy is numerically identical to its unfloored form.
CHURN_FLOOR: float = 0.05


def dspd_proxy(n_prs, project_mean_prs, k: float = K_DSPD):
    """DSPD = clip(n_prs / project_mean_prs * k, 0, 50).

    Throughput relative to each project's OWN baseline. A quarter with exactly
    average PR activity maps to k; the entropy-optimal k=14 places the median
    project-quarter at the apex of the 'Average' triangular set.
    """
    return np.clip(np.asarray(n_prs) / np.asarray(project_mean_prs) * k, 0, 50)


def ltbf_proxy(median_cycle_days, k: float = K_LTBF):
    """LTBF = clip(median_cycle_days * k, 0, 30).

    OSS projects reviewed in roughly 0–4 days map across the full LTBF
    universe at k=8, giving a near-equipartition across rapid/nominal/sluggish.
    """
    return np.clip(np.asarray(median_cycle_days) * k, 0, 30)


def qd_proxy(first_time_merge_rate, churn_ratio, k: float = K_QD):
    """Qd = clip(FTMR * 10 / (max(churn, CHURN_FLOOR) * k), 0, 10).

    The ×k churn penalty prevents projects with high merge rates but heavy
    rework from saturating the 'Resilient' ceiling. k=3 is the entropy maximum
    and prevents the ceiling collapse seen at k=1 (138/144 → Resilient).
    """
    ftmr = np.asarray(first_time_merge_rate)
    churn = np.clip(np.asarray(churn_ratio), CHURN_FLOOR, None)
    return np.clip(ftmr * 10.0 / (churn * k), 0, 10)


def derive_inputs(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute (dspd, ltbf, qd) from raw GitHub-signal columns via the
    calibrated proxies. Used by the live-fetch path; the bundled sample already
    ships derived inputs but also carries the raw columns for verification.

    Required raw columns: n_prs, median_cycle_days, churn_ratio,
    first_time_merge_rate (project_mean_prs is computed per project).
    """
    out = df.copy()
    out["project_mean_prs"] = out.groupby("project_id")["n_prs"].transform("mean")
    out["dspd"] = dspd_proxy(out["n_prs"], out["project_mean_prs"]).round(2)
    out["ltbf"] = ltbf_proxy(out["median_cycle_days"]).round(2)
    out["qd"] = qd_proxy(out["first_time_merge_rate"], out["churn_ratio"]).round(2)
    return out
