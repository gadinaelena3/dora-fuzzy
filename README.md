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

### The OSS study in the application

The application also runs the longitudinal feasibility study of Section 5 of the
manuscript, on the data and with the method reported there:

- OSS Study tab: project × quarter linguistic states, state distribution,
  Kruskal–Wallis test, fallback rate.
- Era Shift tab: per-project PHS time series and the Pre-AI against AI-era
  comparison (Mann–Whitney U, Cliff's δ, Bonferroni-corrected), with the
  pull-request indicators behind the microsoft/vscode shift.
- Calibration tab: scaling factors anchored on the Pre-AI era, the held-out
  check and the entropy diagnostic of the Addendum.

The study reads `backend/data/study/quarterly_signals.csv`: 144 project-quarters
of raw signals computed from 109,866 merged pull requests (110,481 collected from
GitHub in October 2026, 615 bot-authored excluded). The pull-request records and
the collection script are in the replication package,
https://github.com/gadinaelena3/oss-dora-fuzzy. Tests pin the application to the
values of the manuscript (state distribution, H = 78.23, fallback 29.17%, Table XI).

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

All three scenarios reproduce the scores and linguistic states reported in
Appendix A of the manuscript (87.3, 60.0, 9.3).

---

## Reproducing the Section 5 study

```bash
cd backend
python -m scripts.run_study
```

This writes `phs_timeseries.csv`, `era_comparison.csv`, `discriminative_power.json`
and `calibration.json`. The same code backs `/api/study` and `/api/study/calibration`.

---

## What's in here

```
fuzzy-dss/
├── backend/              FastAPI service + scikit-fuzzy engine
│   ├── app/core/         fuzzy_engine.py — single source of truth (12 rules)
│   ├── app/study/        proxy layer, anchored calibration, study analysis
│   ├── app/api/          REST routes & Pydantic schemas
│   ├── data/study/       quarterly_signals.csv — raw signals of the 144 project-quarters
│   ├── tests/            tests pinning the implementation to the paper
│   └── scripts/          run_study · reproduce_paper_scenarios
├── frontend/             React UI (Vite + Recharts)
│   └── src/components/   Assess · Batch · OSS Study · Era Shift · Calibration · Rule Base
├── docs/
│   └── REPRODUCIBILITY.md  how to verify every claim
├── data/
│   ├── paper_scenarios.csv  the three scenarios of Appendix A
│   └── sample_projects.csv  DSS inputs of the 144 project-quarters (for the Batch tab)
├── results/              study outputs written by run_study
└── docker-compose.yml
```

---

## Run the tests

```bash
cd backend
python -m pytest tests/ -v
```

The test suite has three layers:

1. Parameter parity — anchors the implementation to Tables II, IV, VI, VII.
2. Paper scenarios and study — the Appendix A personas and the Section 5 values must reproduce.
3. Edge cases & contracts — clamping, dominant-state selection, API I/O.

If any of the parameter-parity tests fail, the code has drifted from the
paper. Reviewers can run the suite themselves to verify fidelity.

---

## License

MIT — see [`LICENSE`](LICENSE).