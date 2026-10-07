"""API smoke tests using FastAPI's TestClient."""
import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "fuzzy-dss"


def test_assess_scenario_a():
    r = client.post("/api/assess", json={"dspd": 22, "ltbf": 3, "qd": 7.5,
                                          "project_name": "scenario_a"})
    assert r.status_code == 200
    body = r.json()
    assert body["linguistic_state"] == "Elite AI Maturity"
    assert body["phs"] >= 80
    assert body["project_name"] == "scenario_a"
    assert len(body["rule_activations"]) == 12  # always 12 rules logged


def test_assess_validation_rejects_out_of_range():
    r = client.post("/api/assess", json={"dspd": 60, "ltbf": 3, "qd": 7.5})
    assert r.status_code == 422  # pydantic validation


def test_membership_curves_endpoint():
    r = client.get("/api/membership-curves")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"DSPD", "LTBF", "Qd", "PHS"}


def test_rules_endpoint():
    r = client.get("/api/rules")
    assert r.status_code == 200
    body = r.json()
    assert body["n_rules"] == 12


def test_batch_csv():
    csv = (
        "project_name,dspd,ltbf,qd\n"
        "scenario_a,22,3,7.5\n"
        "scenario_b,12,7,3.0\n"
        "scenario_c,25,15,0.8\n"
    )
    files = {"file": ("scenarios.csv", io.BytesIO(csv.encode()), "text/csv")}
    r = client.post("/api/assess-batch", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["n_projects"] == 3
    states = [x["linguistic_state"] for x in body["results"]]
    assert "Elite AI Maturity" in states
    assert "Sustainable" in states
    assert "Critical Risk" in states


def test_batch_rejects_missing_columns():
    csv = "name,foo\nbar,1\n"
    files = {"file": ("bad.csv", io.BytesIO(csv.encode()), "text/csv")}
    r = client.post("/api/assess-batch", files=files)
    assert r.status_code == 400


def test_study_endpoints():
    r = client.get("/api/study")
    assert r.status_code == 200
    assert r.json()["discriminative_power"]["kruskal_H"] == 78.23
    assert r.json()["active_rules"] == 12
    r = client.get("/api/study/calibration")
    assert r.status_code == 200
    assert r.json()["scaling_factors"] == {"k_dspd": 12.18, "k_ltbf": 7.22, "k_qd": 4.35}


def test_uncovered_combination_falls_back():
    body = client.post("/api/assess", json={"project_name": "x", "dspd": 12, "ltbf": 20, "qd": 3}).json()
    assert body["phs"] == 50.0
    assert len(body["rule_activations"]) == 12
