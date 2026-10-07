import math

from app.core.fuzzy_engine import RULES
from app.study import ANCHORS, CHURN_FLOOR
from app.study.analysis import calibration_report, load_signals, run_study


def test_signals_cover_the_study_window():
    df = load_signals()
    assert len(df) == 144
    assert df["project_id"].nunique() == 6
    assert int(df["n_prs"].sum()) == 109866
    assert int(df["n_bot_prs"].sum()) == 615
    assert df["churn_ratio"].min() > CHURN_FLOOR


def test_anchored_scaling_factors():
    assert ANCHORS == {"dspd": 12.0, "ltbf": 7.0, "qd": 3.0}
    assert run_study()["scaling_factors"] == {"k_dspd": 12.18, "k_ltbf": 7.22, "k_qd": 4.35}


def test_rule_base_is_the_twelve_rules_of_the_paper():
    assert len(RULES) == 12
    assert len({(d, l, q) for d, l, q, _, _ in RULES}) == 12


def test_study_matches_the_manuscript():
    s = run_study()
    dp = s["discriminative_power"]
    assert dp["n_observations"] == 144
    assert dp["state_distribution"] == {
        "Sustainable": 97, "High Performance": 20, "At Risk": 19, "Critical Risk": 5, "Elite AI Maturity": 3,
    }
    assert dp["kruskal_H"] == 78.23
    assert dp["no_rule_fallback_pct"] == 29.17
    assert dp["entropy_bits"] == 1.45
    assert (dp["phs_min"], dp["phs_max"]) == (9.84, 88.33)


def test_era_comparison_matches_table_xi():
    eras = {e["project_id"]: e for e in run_study()["era_comparison"]}
    expected = {
        "vscode": (16.02, 0.0002, 1.0), "django": (1.97, 0.8817, -0.056), "numpy": (-2.89, 0.6278, -0.139),
        "rust": (-7.86, 0.0907, -0.458), "kubernetes": (-9.15, 0.4508, -0.208), "react": (-10.13, 0.0536, -0.556),
    }
    for pid, (shift, p, delta) in expected.items():
        assert (eras[pid]["phs_shift"], eras[pid]["mwu_p"], eras[pid]["cliffs_delta"]) == (shift, p, delta)
    assert [pid for pid, e in eras.items() if e["significant_bonferroni"]] == ["vscode"]


def test_calibration_report():
    c = calibration_report()
    assert c["max_entropy_bits"] == round(math.log2(3), 4)
    assert c["axes"]["LTBF"]["entropy_max_k"] == 7.22
    assert c["axes"]["DSPD"]["entropy_max_k"] == 14
    assert c["axes"]["Qd"]["entropy_max_k"] == 3
    held = {h["project_id"]: h for h in c["held_out"]}
    assert sum(h["quarters_state_changed"] for h in held.values()) == 19
    assert [pid for pid, h in held.items() if h["significant_bonferroni"]] == ["vscode"]
