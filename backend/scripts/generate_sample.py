"""
Regenerate the bundled illustrative sample dataset.
====================================================

    python -m scripts.generate_sample      (from backend/)

Writes data/sample/quarterly_metrics.csv. Deterministic — seeded per project
(md5 of the project id) plus a fixed offset — so reruns are byte-identical and
the React "OSS Study" tab always shows the same figures.

To validate against live data instead, run scripts/fetch_github.py with a
GitHub token; that writes data/derived/quarterly_metrics.csv, which the study
loader prefers over this sample.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the app package importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.study.profiles import generate_sample  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "data" / "sample" / "quarterly_metrics.csv"


def main() -> int:
    df = generate_sample()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} project-quarters to {OUT}")
    print(df.head(8).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
