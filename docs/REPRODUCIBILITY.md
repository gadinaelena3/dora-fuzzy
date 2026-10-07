# Reproducibility

Every claim the manuscript makes about the
fuzzy DSS can be verified by running one of the commands below from a
fresh clone. Tested on macOS 14, Ubuntu 22.04, and Windows 11 (WSL2).

---

## 1. Environment

You need exactly one of:

- Docker Desktop ≥ 24.x with `docker compose` v2 — the recommended path
- Python 3.11.x + Node.js 22.x — for local development without containers

No internet access is needed at runtime. The Docker images pull their
dependencies during the initial `build` and then run offline.

---

## 2. One-command reproduction

```bash
git clone <repo-url> fuzzy-dss
cd fuzzy-dss
docker compose up
```

Expected:

- `fuzzy-dss-backend` boots, becomes healthy within ~10 seconds.
- `fuzzy-dss-frontend` waits for the healthcheck, then starts.
- `http://localhost:5173` shows the React UI.
- `http://localhost:8000/docs` shows the OpenAPI spec.

If port 5173 or 8000 is in use, edit `docker-compose.yml` and change the
host-side port (the part before the colon).

---

## 3. Reproducing the manuscript's §4 scenarios

```bash
cd backend
pip install -r requirements.txt
python scripts/reproduce_paper_scenarios.py
```

Expected output:

```
A — Elite AI (Synergy)             22      3    7.5        87.33    Elite AI Maturity    ✓
B — Human Baseline                 12      7    3.0        60.00    Sustainable          ✓
C — Precipice (AI-Tax Risk)        25     15    0.8         9.29    Critical Risk        ✓
```

The exit code is `0` if all three linguistic-state assignments match the
manuscript, and `1` otherwise.

---

## 4. Reproducing the test suite

```bash
cd backend
python -m pytest tests/ -v
```

Expected: 35 tests, all passing, in a few seconds. Test categories:

- `TestMembershipParameters` — Tables II, IV, VI parity (3 tests)
- `TestRuleBase` — 12-rule base integrity (4 tests)
- `TestPaperScenarios` — §4 personas (3 tests)
- `TestEdgeCases` — clamping, no-rule fallback, Qd=0 fragile (5 tests)
- `TestOutputContract` — PHS bounds, state validity, MF export (4 tests)
- API integration tests — every route, including the study endpoints (10 tests)
- `test_study` — anchored scaling factors, rule base, Section 5 values
  (state distribution, H, fallback rate, Table XI), held-out check (6 tests)

If any test in `TestMembershipParameters` or `TestRuleBase` fails, the
implementation has drifted from the manuscript and the test name pinpoints
which table needs reconciling.

---

## 5. Reproducing the Section 5 study

```bash
cd backend
python -m scripts.run_study
```

The study is computed from `backend/data/study/quarterly_signals.csv` (raw signals
of the 144 project-quarters; the pull-request records are in the replication package
https://github.com/gadinaelena3/oss-dora-fuzzy). The outputs in `results/` are the
values of Tables X and XI of the manuscript.

`data/sample_projects.csv` holds the DSS inputs of the same 144 project-quarters and
can be run through the engine from the Batch tab or the CLI:

```bash
curl -F "file=@data/sample_projects.csv" http://localhost:8000/api/assess-batch \
  | python -m json.tool | head -40
```

---

## 6. Verifying the membership-function curves

The UI's plots (Assess tab) are driven by `GET /api/membership-curves`.
The same endpoint can be queried directly:

```bash
curl http://localhost:8000/api/membership-curves \
  | python -c "import json,sys; d=json.load(sys.stdin); \
               print({k: list(v['sets'].keys()) for k,v in d.items()})"
```

Expected:

```
{'DSPD': ['low', 'average', 'high'],
 'LTBF': ['rapid', 'nominal', 'sluggish'],
 'Qd':   ['fragile', 'stable', 'resilient'],
 'PHS':  ['critical_risk', 'at_risk', 'sustainable',
          'high_performance', 'elite_ai']}
```

---

## 7. Verifying the rule base

```bash
curl http://localhost:8000/api/rules | python -m json.tool | head -20
```

Should report `n_rules: 12` with R1's antecedents being
`{"DSPD": "high", "LTBF": "rapid", "Qd": "resilient"}` and consequent
`elite_ai`.

---

## 8. Pinned dependency versions

| Component | Version |
|-----------|---------|
| Python | 3.11.x |
| FastAPI | 0.115.6 |
| uvicorn | 0.32.1 |
| pydantic | 2.10.4 |
| scikit-fuzzy | 0.5.0 |
| numpy | 2.1.3 |
| pandas | 2.2.3 |
| pytest | 8.3.4 |
| Node.js | 22.x |
| React | 18.3.1 |
| Vite | 6.0.6 |
| Recharts | 2.15.0 |
| nginx (image) | 1.27-alpine |

These are the versions used to run the test suite and to capture the
results in the rebuttal letter. Newer minor versions are likely fine but
unverified.

---

## 9. If something fails

1. Re-run with `docker compose up --build` to rebuild from scratch.
2. Check the backend logs: `docker compose logs backend`.
3. If `pytest` fails on a `TestMembershipParameters` test, the constants in
   `backend/app/core/fuzzy_engine.py` have been edited; revert them or
   update the manuscript table to match.
4. If the frontend shows "Cannot reach the backend", the API container is
   not healthy yet — wait ~10 seconds and refresh.
