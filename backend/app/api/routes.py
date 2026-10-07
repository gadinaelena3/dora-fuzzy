"""FastAPI route handlers."""
from __future__ import annotations

import io
from collections import Counter
from typing import List

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    BatchResponse,
    MembershipCurves,
)
from app.core.fuzzy_engine import (
    PHS_LABELS,
    RULES,
    infer,
    membership_curves,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Single-project assessment
# ---------------------------------------------------------------------------
@router.post("/assess", response_model=AssessmentResponse, tags=["assessment"])
def assess(req: AssessmentRequest) -> AssessmentResponse:
    """Run the fuzzy DSS on one project."""
    result = infer(req.dspd, req.ltbf, req.qd)
    return AssessmentResponse(
        project_name=req.project_name,
        inputs=result.inputs,
        phs=result.phs,
        linguistic_state=result.linguistic_state,
        state_membership=result.state_membership,
        input_memberships=result.input_memberships,
        rule_activations=result.rule_activations,
    )


# ---------------------------------------------------------------------------
# Batch (CSV upload)
# ---------------------------------------------------------------------------
@router.post("/assess-batch", response_model=BatchResponse, tags=["assessment"])
async def assess_batch(file: UploadFile = File(...)) -> BatchResponse:
    """
    Run the fuzzy DSS on a batch of projects supplied as CSV.

    Required columns: dspd, ltbf, qd
    Optional column:  project_name
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a .csv file.")

    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(400, f"Could not parse CSV: {exc}")

    required = {"dspd", "ltbf", "qd"}
    missing = required - {c.lower() for c in df.columns}
    if missing:
        raise HTTPException(400, f"Missing required columns: {sorted(missing)}")

    df.columns = [c.lower() for c in df.columns]

    results: List[AssessmentResponse] = []
    for _, row in df.iterrows():
        r = infer(float(row["dspd"]), float(row["ltbf"]), float(row["qd"]))
        results.append(AssessmentResponse(
            project_name=str(row.get("project_name") or f"row_{_}"),
            inputs=r.inputs,
            phs=r.phs,
            linguistic_state=r.linguistic_state,
            state_membership=r.state_membership,
            input_memberships=r.input_memberships,
            rule_activations=r.rule_activations,
        ))

    summary = dict(Counter(r.linguistic_state for r in results))
    return BatchResponse(n_projects=len(results), results=results, summary=summary)


# ---------------------------------------------------------------------------
# Metadata & introspection (powers the UI plots and the rule-base view)
# ---------------------------------------------------------------------------
@router.get("/membership-curves", response_model=MembershipCurves, tags=["metadata"])
def get_membership_curves() -> MembershipCurves:
    """Return MF curves for DSPD, LTBF, Qd and PHS — one call per UI session."""
    return MembershipCurves(**membership_curves())


@router.get("/rules", tags=["metadata"])
def get_rules() -> dict:
    """Return the 12-rule base (Table VI) for display in the UI."""
    return {
        "n_rules": len(RULES),
        "rules": [
            {
                "id": f"R{i+1}",
                "DSPD": d, "LTBF": l, "Qd": q,
                "PHS": out, "PHS_label": PHS_LABELS[out],
                "rationale": rationale,
            }
            for i, (d, l, q, out, rationale) in enumerate(RULES)
        ],
    }


# ---------------------------------------------------------------------------
# OSS longitudinal study (powers the Study / Era Shift / Calibration tabs)
# ---------------------------------------------------------------------------
@router.get("/study", tags=["study"])
def get_study() -> dict:
    """OSS longitudinal feasibility study (Section 5 of the manuscript) on the
    re-collected GitHub data.
    """
    from app.study import run_study
    return run_study()


@router.get("/study/calibration", tags=["study"])
def get_calibration() -> dict:
    """Scaling factors anchored on the Pre-AI era, the entropy of the input
    zones as a diagnostic, and the leave-one-project-out check (Addendum).
    """
    from app.study import calibration_report
    return calibration_report()


@router.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
