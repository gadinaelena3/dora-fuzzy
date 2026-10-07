from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.study import calibration_report, run_study

RESULTS = Path(__file__).resolve().parents[2] / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    study = run_study()
    pd.DataFrame(study["timeseries"]).to_csv(RESULTS / "phs_timeseries.csv", index=False)
    pd.DataFrame(study["era_comparison"]).to_csv(RESULTS / "era_comparison.csv", index=False)
    (RESULTS / "discriminative_power.json").write_text(json.dumps(study["discriminative_power"], indent=2))
    (RESULTS / "calibration.json").write_text(json.dumps(calibration_report(), indent=2))

    dp = study["discriminative_power"]
    print(f"H={dp['kruskal_H']} fallback={dp['no_rule_fallback_pct']}% states={dp['state_distribution']}")
    print(pd.DataFrame(study["era_comparison"])[["project_id", "phs_shift", "mwu_p", "cliffs_delta", "significant_bonferroni"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
