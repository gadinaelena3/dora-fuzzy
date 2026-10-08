"""
FastAPI entrypoint for the AI-Augmented SDLC Fuzzy DSS.

Run locally:
    uvicorn app.main:app --reload --port 8000

Or via Docker compose from the repo root:
    docker compose up
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Fuzzy DSS for AI-Augmented Software Development",
    description=(
        "Reference implementation of the Fuzzy Inference System described in "
        "Suduc et al., 'A Fuzzy Hybrid Decision Support System (DSS) to Govern "
        "Non-linear Dynamics and Uncertainty in AI-Augmented Software "
        "Development', Journal of Systems & Software (under review, 2026). "
        "Includes the Section 5 OSS longitudinal feasibility study (/api/study) "
        "and the calibration report of the Addendum (/api/study/calibration)."
    ),
    version="0.2.0",
)

# Permissive CORS so the React dev server (Vite, port 5173) can call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {
        "service": "fuzzy-dss",
        "docs": "/docs",
        "endpoints": ["/api/assess", "/api/assess-batch",
                      "/api/membership-curves", "/api/rules",
                      "/api/study", "/api/study/calibration", "/api/health"],
    }
