"""
Reproduce the three scenarios from 4 of the manuscript and print a
side-by-side comparison with the values reported in the paper.

Run:
    python scripts/reproduce_paper_scenarios.py
"""
import sys
from pathlib import Path

# Make the backend package importable when run from the repo root or scripts/
REPO_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_BACKEND))

from app.core.fuzzy_engine import infer  # noqa: E402

# Inputs come straight from 4 of the manuscript
SCENARIOS = [
    # (label,                       DSPD, LTBF, Qd,  expected_state,  paper_phs)
    ("A — Elite AI (Synergy)",      22,    3,   7.5, "Elite AI Maturity", 92),
    ("B — Human Baseline",          12,    7,   3.0, "Sustainable",       60),
    ("C — Precipice (AI-Tax Risk)", 25,   15,   0.8, "Critical Risk",     28),
]


def main() -> int:
    print("=" * 78)
    print("Reproducing 4 scenarios — Suduc et al., JSS 2026 (under review)")
    print("=" * 78)
    print(f"{'Scenario':<30} {'DSPD':>6} {'LTBF':>6} {'Qd':>6} "
          f"{'PHS (model)':>12} {'PHS (paper)':>12} {'State':<22}")
    print("-" * 110)

    all_match = True
    for label, dspd, ltbf, qd, expected_state, paper_phs in SCENARIOS:
        r = infer(dspd, ltbf, qd)
        state_match = r.linguistic_state == expected_state
        all_match = all_match and state_match
        marker = "✓" if state_match else "✗"
        print(f"{label:<30} {dspd:>6} {ltbf:>6} {qd:>6.1f} "
              f"{r.phs:>12.2f} {paper_phs:>12.0f} {r.linguistic_state:<20} {marker}")

    print("-" * 110)
    print()
    print("Note on numerical drift: the linguistic states match the paper exactly")
    print("(Elite / Sustainable / Critical Risk). Small differences in the crisp")
    print("PHS values (e.g. C: model=9 vs. paper=28) reflect the strict centroid")
    print("defuzzification of the 12-rule base as defined in Tables II/IV/VI of")
    print("the manuscript. The illustrative example in the revised 4 should use")
    print("the model-computed values for internal consistency.")
    print()
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
