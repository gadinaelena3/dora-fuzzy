"""
Regression tests for the OSS study integration.

These guard against the single most dangerous failure mode for the revision:
silent drift between the executable code, the manuscript 5, and the Addendum
Table XI. If any scaling factor, rule count, or headline study figure changes,
these tests fail loudly.
"""
import math

from app.core.fuzzy_engine import (
    RULES, EXTENDED_RULES, set_rule_mode, active_rule_count,
)
from app.study import K_DSPD, K_LTBF, K_QD, CHURN_FLOOR
from app.study.analysis import run_study, sensitivity_sweep


# ---------------------------------------------------------------------------
# Calibration constants must match the manuscript 5.2 and Addendum Table XI.
# ---------------------------------------------------------------------------
def test_scaling_factors_locked():
    assert K_DSPD == 14, "k_DSPD drifted from the published calibration (14)."
    assert K_LTBF == 8, "k_LTBF drifted from the published calibration (8)."
    assert K_QD == 3, "k_Qd drifted from the published calibration (3)."
    assert CHURN_FLOOR == 0.05


def test_churn_floor_never_binds_on_sample():
    """The Addendum claims the 0.05 floor is never active (min churn 0.078)."""
    import pandas as pd
    from app.study.analysis import SAMPLE_CSV
    df = pd.read_csv(SAMPLE_CSV)
    assert df["churn_ratio"].min() > CHURN_FLOOR


# ---------------------------------------------------------------------------
# Rule bases
# ---------------------------------------------------------------------------
def test_base_rule_base_is_twelve():
    assert len(RULES) == 12, "Table VI must contain exactly 12 rules."


def test_extended_rule_base_is_full_coverage():
    assert len(EXTENDED_RULES) == 27
    combos = {(d, l, q) for d, l, q, _, _ in EXTENDED_RULES}
    assert len(combos) == 27, "Extended base must cover all 3x3x3 antecedents."


def test_rule_mode_toggle():
    set_rule_mode("base12")
    assert active_rule_count() == 12
    set_rule_mode("extended27")
    assert active_rule_count() == 27
    set_rule_mode("base12")  # restore default-of-record


# ---------------------------------------------------------------------------
# Study reproducibility (bundled sample is deterministic)
# ---------------------------------------------------------------------------
def test_study_shape():
    s = run_study("base12")
    dp = s["discriminative_power"]
    assert dp["n_observations"] == 144
    assert dp["n_projects"] == 6
    assert len(s["era_comparison"]) == 6
    assert len(s["heatmap"]) == 6


def test_extended_mode_reduces_fallback():
    base = run_study("base12")["discriminative_power"]["no_rule_fallback_pct"]
    ext = run_study("extended27")["discriminative_power"]["no_rule_fallback_pct"]
    set_rule_mode("base12")
    assert ext <= base
    assert ext == 0.0, "Full 27-rule coverage must eliminate the fallback."


def test_sensitivity_optima():
    sw = sensitivity_sweep()
    # DSPD and Qd optima match the published calibration on the bundled sample.
    assert sw["axes"]["DSPD"]["optimal_k"] == 14
    assert sw["axes"]["Qd"]["optimal_k"] == 3
    assert sw["max_entropy_bits"] == round(math.log2(3), 4)


def test_era_significance_pattern():
    """vscode and rust show significant positive AI-era shifts (manuscript Table X)."""
    eras = {e["project_id"]: e for e in run_study("base12")["era_comparison"]}
    assert eras["vscode"]["significant_05"] and eras["vscode"]["phs_shift"] > 0
    assert eras["rust"]["significant_05"] and eras["rust"]["phs_shift"] > 0
