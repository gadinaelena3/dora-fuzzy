"""
Tests for the fuzzy inference engine.

These tests anchor the implementation to the paper's Tables II / IV / VI
and 4 scenarios. If a test breaks, the membership-function calibration
or the rule base no longer matches the manuscript.
"""
import pytest
from app.core.fuzzy_engine import (
    DSPD_PARAMS,
    LTBF_PARAMS,
    PHS_LABELS,
    QD_PARAMS,
    RULES,
    infer,
    membership_curves,
)


# ---------------------------------------------------------------------------
# Membership-function table parity (Tables II, IV, VI)
# ---------------------------------------------------------------------------
class TestMembershipParameters:
    def test_dspd_matches_table_ii(self):
        # Table II of the manuscript
        assert DSPD_PARAMS["low"]     == [0,  0,  5,  10]
        assert DSPD_PARAMS["average"] == [8,  12, 16]
        assert DSPD_PARAMS["high"]    == [14, 20, 50, 50]

    def test_ltbf_matches_table_iv(self):
        # Table IV of the manuscript
        assert LTBF_PARAMS["rapid"]    == [0, 0,  2,  5]
        assert LTBF_PARAMS["nominal"]  == [4, 7,  10]
        assert LTBF_PARAMS["sluggish"] == [9, 15, 30, 30]

    def test_qd_matches_table_vi(self):
        # Table VI of the manuscript (Quality Duo)
        assert QD_PARAMS["fragile"]   == [0,   0, 0.8, 1.5]
        assert QD_PARAMS["stable"]    == [1.2, 3, 5]
        assert QD_PARAMS["resilient"] == [4.5, 7, 10, 10]


# ---------------------------------------------------------------------------
# Rule base parity (Table VI – 12 rules)
# ---------------------------------------------------------------------------
class TestRuleBase:
    def test_twelve_rules(self):
        assert len(RULES) == 12

    def test_r1_synergy(self):
        # R1: High + Rapid + Resilient -> Elite AI
        assert RULES[0][:4] == ("high", "rapid", "resilient", "elite_ai")

    def test_r3_technical_debt_spiral(self):
        # R3: High + Sluggish + Fragile -> Critical Risk
        assert RULES[2][:4] == ("high", "sluggish", "fragile", "critical_risk")

    def test_r12_fake_speed(self):
        # R12: High + Rapid + Fragile -> Critical Risk
        assert RULES[11][:4] == ("high", "rapid", "fragile", "critical_risk")


# ---------------------------------------------------------------------------
# 4 paper scenarios
# ---------------------------------------------------------------------------
class TestPaperScenarios:
    def test_scenario_a_elite(self):
        r = infer(dspd=22, ltbf=3, qd=7.5)
        assert r.linguistic_state == "Elite AI Maturity"
        assert r.phs >= 80

    def test_scenario_b_baseline(self):
        r = infer(dspd=12, ltbf=7, qd=3.0)
        assert r.linguistic_state == "Sustainable"
        assert 50 <= r.phs <= 70

    def test_scenario_c_critical(self):
        r = infer(dspd=25, ltbf=15, qd=0.8)
        assert r.linguistic_state == "Critical Risk"
        assert r.phs < 30


# ---------------------------------------------------------------------------
# Robustness / edge cases (R2 asked for edge-case behaviour of Qd)
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_zero_inputs_do_not_crash(self):
        r = infer(0, 0, 0)
        assert 0 <= r.phs <= 100

    def test_max_inputs_do_not_crash(self):
        r = infer(50, 30, 10)
        assert 0 <= r.phs <= 100

    def test_inputs_above_universe_are_clamped(self):
        # Out-of-range inputs should clamp, not raise
        r = infer(999, 999, 999)
        assert 0 <= r.phs <= 100

    def test_negative_inputs_are_clamped(self):
        r = infer(-5, -1, -2)
        assert 0 <= r.phs <= 100

    def test_qd_zero_gives_fragile(self):
        # Acceptance=0 -> Qd=0 -> fully fragile
        r = infer(dspd=20, ltbf=5, qd=0.0)
        assert r.input_memberships["Qd"]["fragile"] == 1.0
        assert r.input_memberships["Qd"]["stable"] == 0.0
        assert r.input_memberships["Qd"]["resilient"] == 0.0


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------
class TestOutputContract:
    def test_phs_in_range(self):
        r = infer(15, 6, 4)
        assert 0 <= r.phs <= 100

    def test_state_label_is_known(self):
        r = infer(15, 6, 4)
        assert r.linguistic_state in PHS_LABELS.values()

    def test_input_memberships_sum_le_2(self):
        # With overlapping fuzzy sets, sum of memberships per variable <= 2
        # (max of 2 overlapping sets at any point in the universe).
        r = infer(15, 8, 4)
        for var in ("DSPD", "LTBF", "Qd"):
            s = sum(r.input_memberships[var].values())
            assert s <= 2.0 + 1e-9, f"{var} membership sum out of bounds: {s}"

    def test_membership_curves_export(self):
        curves = membership_curves()
        assert set(curves.keys()) == {"DSPD", "LTBF", "Qd", "PHS"}
        for var in curves.values():
            assert "x" in var and "sets" in var
            for series in var["sets"].values():
                assert len(series) == len(var["x"])
