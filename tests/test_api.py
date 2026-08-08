from fastapi.testclient import TestClient

from syspulc.api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_sample_event():
    response = client.get("/sample")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rack_id"] == "RACK-DEMO-01"
    assert payload["event_id"] == "EVT-DEMO-0001"


def test_analyze_sample_event_returns_risk_scoring():
    response = client.post("/analyze")

    assert response.status_code == 200
    payload = response.json()
    assert payload["request"]["rack_id"] == "RACK-DEMO-01"
    assert payload["rca"]["agent_name"] == "RCA-Agent"
    assert payload["risk"]["score"] >= 85
    assert payload["risk"]["level"] == "critical"
    assert payload["risk"]["suggested_owners"]


def test_analyze_inline_nominal_event_returns_low_risk():
    response = client.post(
        "/analyze",
        json={
            "rack_id": "RACK-NOMINAL-01",
            "event_id": "EVT-NOMINAL-0001",
            "payload": {
                "voltage_sag_mv": 80,
                "nvlink_crc_errors": 0,
                "cxl_aer_fatal": False,
                "reset_gpr_residual": False,
                "bios_version": "v3.2.0",
                "bmc_version": "v3.2.1",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk"]["level"] == "low"
    assert payload["risk"]["score"] < 35


def test_analyze_hang_sample_returns_triage_plan():
    response = client.post("/analyze/hang")

    assert response.status_code == 200
    payload = response.json()
    assert payload["issue_id"] == "HANG-DEMO-0001"
    assert payload["release_risk"] == "high"
    assert payload["possible_root_cause_domains"]
    assert payload["next_evidence_capture"]
    assert payload["ab_isolation_plan"]
