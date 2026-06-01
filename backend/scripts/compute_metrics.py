"""
Metrics computation: raw GitHub events  ->  quarterly DSPD, LTBF, Qd.
====================================================================

Reads data/raw/{project_id}.jsonl (produced by scripts/fetch_github.py) and
writes data/derived/quarterly_metrics.csv at the project root, which the study
loader prefers over the bundled sample.

    python -m scripts.compute_metrics      (from backend/)

PROXY DEFINITIONS
-----------------
The three input metrics are derived from public GitHub signals through the
calibrated proxy layer in app/study/proxies.py. The scaling factors
(k_DSPD = 14, k_LTBF = 8, k_Qd = 3) are the entropy-optimal values from the
Addendum Table XI; they are defined ONCE in proxies.py and imported here, so
this script can never diverge from the published calibration.

  DSPD = clip(n_prs / project_mean_prs * 14, 0, 50)
  LTBF = clip(median_cycle_days * 8,         0, 30)
  Qd   = clip(FTMR * 10 / (max(churn, 0.05) * 3), 0, 10)

  first_time_merge_rate = PRs merged within 7 days / total merged PRs
  churn_ratio           = sum(LOC deleted) / max(sum(LOC added), 1)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.study.proxies import derive_inputs  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND.parent
RAW_DIR = BACKEND / "data" / "raw"
DERIVED_PATH = PROJECT_ROOT / "data" / "derived" / "quarterly_metrics.csv"


def _quarter(ts: str) -> str:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return f"{dt.year}Q{(dt.month - 1) // 3 + 1}"


def _cycle_days(pr: dict) -> float:
    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
    merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
    return max((merged - created).total_seconds() / 86400.0, 0.0)


def _load_raw(path: Path) -> tuple[str, list[dict], list[dict]]:
    project_id, prs, releases = path.stem, [], []
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            if "_meta" in obj:
                project_id = obj["_meta"]["project_id"]
            elif obj.get("type") == "release":
                releases.append(obj)
            elif obj.get("merged_at"):
                prs.append(obj)
    return project_id, prs, releases


def _raw_quarterly(project_id: str, prs: list[dict], releases: list[dict]) -> pd.DataFrame:
    rows = []
    rel_q = [_quarter(r["created_at"]) for r in releases if r.get("created_at")]
    by_q: dict[str, list[dict]] = {}
    for pr in prs:
        by_q.setdefault(_quarter(pr["merged_at"]), []).append(pr)

    for q, qprs in sorted(by_q.items()):
        cycle = np.array([_cycle_days(p) for p in qprs])
        adds = np.array([p.get("additions", 0) for p in qprs])
        dels = np.array([p.get("deletions", 0) for p in qprs])
        ftmr = float((cycle <= 7).sum()) / max(len(qprs), 1)
        rows.append({
            "project_id": project_id, "quarter": q,
            "n_prs": len(qprs),
            "n_releases": rel_q.count(q),
            "median_cycle_days": float(np.median(cycle)) if len(cycle) else 0.0,
            "churn_ratio": float(dels.sum() / max(adds.sum(), 1.0)),
            "first_time_merge_rate": ftmr,
        })
    return pd.DataFrame(rows)


def main() -> int:
    if not RAW_DIR.exists():
        print(f"No raw data at {RAW_DIR}. Run scripts/fetch_github.py first.")
        return 1

    frames = []
    for path in sorted(RAW_DIR.glob("*.jsonl")):
        pid, prs, releases = _load_raw(path)
        if not prs:
            print(f"  {pid}: no merged PRs, skipping")
            continue
        frames.append(_raw_quarterly(pid, prs, releases))

    if not frames:
        print("No usable raw data found.")
        return 1

    raw = pd.concat(frames, ignore_index=True)
    derived = derive_inputs(raw)   # applies k=14/8/3 via the proxy layer
    DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    derived.to_csv(DERIVED_PATH, index=False)
    print(f"Wrote {len(derived)} project-quarters to {DERIVED_PATH}")
    print("The study loader will now prefer this live-derived data over the sample.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
