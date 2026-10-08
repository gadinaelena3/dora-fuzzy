import json
from pathlib import Path

import pandas as pd
import pytest

from app.core.fuzzy_engine import infer

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "Athena": (87.23, "Elite AI Maturity"),
    "Boreas": (60.0, "Sustainable"),
    "Chronos": (72.5, "High Performance"),
    "Delphi": (35.0, "At Risk"),
    "Echidna": (60.0, "Sustainable"),
    "Fenix": (60.0, "Sustainable"),
    "Gaia": (49.87, "Sustainable"),
    "Helios": (9.7, "Critical Risk"),
}


@pytest.mark.parametrize("row", list(pd.read_csv(ROOT / "data" / "ranking_exercise.csv").itertuples()), ids=lambda r: r.squad)
def test_table_xiv_scores(row):
    r = infer(row.dspd, row.ltbf, row.qd)
    phs, state = EXPECTED[row.squad]
    assert round(r.phs, 2) == phs
    assert r.linguistic_state == state


def test_reported_concordance():
    out = json.loads((ROOT / "results" / "ranking_exercise.json").read_text())
    assert out["spearman"] == 0.6343
    assert out["spearman_p_exact"] == 0.1021
    assert out["kendall_tau_b"] == 0.5669
    assert out["kendall_p_exact"] == 0.0729
    assert out["single_input"]["dspd"]["spearman"] == 0.8333
    assert out["leave_one_out"]["Delphi"] == 0.8895
