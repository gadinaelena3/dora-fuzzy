"""
Run the OSS longitudinal study end-to-end and write result artefacts.
=====================================================================

    python -m scripts.run_study                 (from backend/)
    python -m scripts.run_study --rule-mode extended27

Outputs (written to ../results/):
  - phs_timeseries.csv          per (project, quarter): inputs + PHS + state
  - era_comparison.csv          per project: pre-AI vs AI-era stats + tests
  - discriminative_power.json   spread, entropy, Kruskal-Wallis, fallback rate
  - sensitivity.json            Table XI sweep
  - REPORT.md                   human-readable summary

This is the same code path the API /api/study endpoint uses, so the numbers
here match the React "OSS Study" / "Era Shift" / "Calibration" tabs exactly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.study import run_study, sensitivity_sweep  # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"


def _report(study: dict, sens: dict) -> str:
    dp = study["discriminative_power"]
    lines = ["# OSS Longitudinal Study — Findings", ""]
    lines.append(f"_Data source: **{study['source']}** · rule base: "
                 f"**{study['rule_mode']}** ({study['active_rules']} rules)._")
    lines.append("")
    lines.append("## Executive summary")
    sig = [e["project_id"] for e in study["era_comparison"] if e["significant_05"]]
    lines.append(
        f"- **{dp['n_observations']}** project-quarters across "
        f"**{dp['n_projects']}** OSS projects.\n"
        f"- PHS: mean **{dp['phs_mean']}**, std **{dp['phs_std']}**, "
        f"range **[{dp['phs_min']}, {dp['phs_max']}]**.\n"
        f"- Linguistic-state entropy: **{dp['entropy_bits']} bits** "
        f"(normalised {dp['entropy_normalised']}).\n"
        f"- Cross-project Kruskal–Wallis: H = **{dp['kruskal_H']}**, "
        f"p = **{dp['kruskal_p']:.2e}**.\n"
        f"- Significant era shift in **{len(sig)} of {len(study['era_comparison'])}** "
        f"projects: {', '.join(sig) if sig else 'none'}.\n"
        f"- No-rule fallback: **{dp['no_rule_fallback_pct']}%** "
        f"({dp['no_rule_fallback_n']}/{dp['n_observations']}).\n"
    )
    lines.append("\n## Scaling-factor calibration (Table XI)")
    for ax, d in sens["axes"].items():
        lines.append(f"- **{ax}**: entropy-optimal k = **{d['optimal_k']}** "
                     f"(H = {d['optimal_entropy']} bits).")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-mode", default="base12", choices=["base12", "extended27"])
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    study = run_study(args.rule_mode)
    sens = sensitivity_sweep()

    pd.DataFrame(study["timeseries"]).to_csv(RESULTS / "phs_timeseries.csv", index=False)
    pd.DataFrame(study["era_comparison"]).to_csv(RESULTS / "era_comparison.csv", index=False)
    with open(RESULTS / "discriminative_power.json", "w") as f:
        json.dump(study["discriminative_power"], f, indent=2)
    with open(RESULTS / "sensitivity.json", "w") as f:
        json.dump(sens, f, indent=2)
    with open(RESULTS / "REPORT.md", "w", encoding="utf-8") as f:
        f.write(_report(study, sens))

    print(f"Wrote results to {RESULTS}/ (rule mode: {args.rule_mode})")
    dp = study["discriminative_power"]
    print(f"  entropy={dp['entropy_bits']} H={dp['kruskal_H']} "
          f"fallback={dp['no_rule_fallback_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
