import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.fuzzy_engine import infer  # noqa: E402

SCENARIOS = [
    ("A — Elite AI (Synergy)",      22,  3, 7.5, "Elite AI Maturity", 87.3),
    ("B — Human Baseline",          12,  7, 3.0, "Sustainable",       60.0),
    ("C — Precipice (AI-Tax Risk)", 25, 15, 0.8, "Critical Risk",      9.3),
]


def main() -> int:
    print("=" * 96)
    print("Appendix A scenarios — Udrescu et al., JSS (under review)")
    print("=" * 96)
    print(f"{'Scenario':<30} {'DSPD':>5} {'LTBF':>5} {'Qd':>5} "
          f"{'PHS (model)':>12} {'PHS (paper)':>12}  {'State':<20}")
    print("-" * 96)

    all_match = True
    for label, dspd, ltbf, qd, state, paper_phs in SCENARIOS:
        r = infer(dspd, ltbf, qd)
        ok = r.linguistic_state == state and abs(r.phs - paper_phs) < 0.05
        all_match = all_match and ok
        print(f"{label:<30} {dspd:>5} {ltbf:>5} {qd:>5.1f} "
              f"{r.phs:>12.2f} {paper_phs:>12.1f}  {r.linguistic_state:<20} {'✓' if ok else '✗'}")

    print("-" * 96)
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
