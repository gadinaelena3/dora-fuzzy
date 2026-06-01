"""OSS longitudinal study package — integrated into the DSS backend.

This package makes the empirical validation of 5 a first-class, runnable
part of the reference implementation rather than an external script. It
exposes:

  * ``profiles``  — deterministic sample-data generation (public-knowledge
                    trajectories for the six study projects).
  * ``proxies``   — the GitHub-signal → (DSPD, LTBF, Qd) proxy layer with the
                    entropy-calibrated scaling factors k_DSPD=14, k_LTBF=8,
                    k_Qd=3 (Addendum, Table XI).
  * ``analysis``  — applies the fuzzy engine to every project-quarter and
                    computes discriminative power, era comparison, and the
                    sensitivity sweep.

All numbers consumed by the React "OSS Study", "Era Shift", and
"Calibration" tabs are produced here.
"""
from app.study.proxies import (
    K_DSPD, K_LTBF, K_QD, CHURN_FLOOR,
    dspd_proxy, ltbf_proxy, qd_proxy,
)
from app.study.analysis import (
    run_study, sensitivity_sweep, load_sample,
)

__all__ = [
    "K_DSPD", "K_LTBF", "K_QD", "CHURN_FLOOR",
    "dspd_proxy", "ltbf_proxy", "qd_proxy",
    "run_study", "sensitivity_sweep", "load_sample",
]
