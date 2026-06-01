# Fuzzy DSS for AI-Augmented Software Development

Reference implementation accompanying:

> Udrescu A., Udrescu E.,Suduc A.-M., Bîzoi M.,  (2026).
> A Fuzzy Hybrid Decision Support System (DSS) to Govern Non-linear Dynamics
> and Uncertainty in AI-Augmented Software Development.
> Journal of Systems & Software (under revision, JSSOFTWARE-D-26-00371).

This repository implements the Mamdani-style fuzzy inference system described
in the manuscript — three input metrics (DSPD, LTBF, Qd), nine membership
functions, twelve rules, Centre-of-Gravity defuzzification, and a five-tier
Project Health Score — and exposes it as both a JSON API and a React web
interface.

### New in this revision

The reference implementation now embeds the 5 OSS longitudinal study as a
runnable, first-class part of the system — not an external script. A reviewer
running `docker compose up` can open the web UI and watch the paper's empirical
findings reproduce live:

- OSS Study tab — the project × quarter linguistic-state heatmap,
  discriminative-power metrics (entropy, Kruskal–Wallis), the Table IX state
  distribution, and a 12-rule ↔ 27-rule toggle that shows the no-rule
  fallback rate collapse to zero under full antecedent coverage.
- Era Shift tab — per-project PHS time series with AI-milestone markers and
  the Table X pre-AI-vs-AI-era comparison (Mann–Whitney U, Cliff's δ).
- Calibration tab — the Addendum's Table XI scaling-factor sensitivity
  sweep, rendered as interactive entropy curves with the entropy-maximising k
  highlighted on each axis.

The proxy layer (`backend/app/study/proxies.py`) defines the entropy-calibrated
scaling factors k_DSPD = 14, k_LTBF = 8, k_Qd = 3 as a single source of
truth, guarded by a regression test so code, manuscript 5.2, and Addendum
Table XI can never silently diverge.

---

## Quick start

### One command (Docker compose)

```bash
git clone <repo-url> fuzzy-dss
cd fuzzy-dss
docker compose up
```

Then visit:

- http://localhost:5173 — React UI
- http://localhost:8000/docs — interactive OpenAPI docs

That's the entire setup. Bringing the stack down: `docker compose down`.

### Without Docker (local dev)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

---

## Reproducing the paper's three scenarios

```bash
cd backend
python scripts/reproduce_paper_scenarios.py
```

Expected output:

```
A — Elite AI (Synergy)             22      3    7.5        87.33    Elite AI Maturity ✓
B — Human Baseline                 12      7    3.0        60.00    Sustainable       ✓
C — Precipice (AI-Tax Risk)        25     15    0.8         9.29    Critical Risk     ✓
```

All three scenarios reproduce the linguistic state reported in the paper.
See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md#paper-vs-model-numerical-drift)
for a note on the small numerical drift in the crisp PHS for Scenario C
(model: 9 vs paper: 28) and how to reconcile 4 of the revised manuscript.

---

## Reproducing the 5 OSS longitudinal study

```bash
cd backend
python -m scripts.generate_sample      # (re)build the deterministic sample
python -m scripts.run_study            # write results/ artefacts (12-rule base)
python -m scripts.run_study --rule-mode extended27   # full 27-rule coverage
```

This writes `results/phs_timeseries.csv`, `results/era_comparison.csv`,
`results/discriminative_power.json`, `results/sensitivity.json`, and
`results/REPORT.md`. The same code path backs the `/api/study` endpoint, so the
artefacts match the web UI exactly. To validate against live GitHub data:

```bash
export GITHUB_TOKEN=ghp_xxx
python scripts/fetch_github.py         # writes data/derived/quarterly_metrics.csv
python -m scripts.run_study            # now runs on live data
```

---

## What's in here

```
fuzzy-dss/
├── backend/              FastAPI service + scikit-fuzzy engine
│   ├── app/core/         fuzzy_engine.py — single source of truth (12 + 27 rules)
│   ├── app/study/        proxy layer, sample profiles, study analysis
│   ├── app/api/          REST routes & Pydantic schemas
│   ├── config/           projects.yaml — study projects & era boundaries
│   ├── tests/            tests pinning the implementation to the paper
│   └── scripts/          generate_sample · run_study · fetch_github
├── frontend/             React UI (Vite + Recharts)
│   └── src/components/   Assess · Batch · OSS Study · Era Shift · Calibration · Rule Base
├── docs/
│   ├── METHODOLOGY.md    paper-to-code mapping (incl. proxy layer 7, rules 8)
│   ├── REPRODUCIBILITY.md  how to verify every claim
│   └── …
├── data/
│   └── sample/           quarterly_metrics.csv — deterministic study sample
├── results/              generated study artefacts
└── docker-compose.yml
```

---

## Run the tests

```bash
cd backend
python -m pytest tests/ -v
```

The test suite has three layers:

1. Parameter parity — anchors the implementation to Tables II, IV, VI.
2. Paper scenarios — the three 4 personas must classify correctly.
3. Edge cases & contracts — clamping, dominant-state selection, API I/O.

If any of the parameter-parity tests fail, the code has drifted from the
paper. Reviewers can run the suite themselves to verify fidelity.

---

## License

MIT — see [`LICENSE`](LICENSE).