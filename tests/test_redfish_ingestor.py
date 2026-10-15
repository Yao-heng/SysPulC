from pathlib import Path

from syspulc.diagnostics import DiagnosticEngine
from syspulc.ingestors import RedfishIngestor, load_redfish_request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REDFISH_SAMPLE = PROJECT_ROOT / "samples" / "redfish_chassis_telemetry.json"


def test_bundled_redfish_sample_converts_to_expected_request():
    request = load_redfish_request(REDFISH_SAMPLE)

    assert request.rack_id == "RACK-DEMO-01"
    assert request.event_id == "EVT-REDFISH-0001"
    assert request.timestamp == "2026-01-01T00:05:00+00:00"
    assert request.payload == {
        "voltage_sag_mv": 180.0,
        "nvlink_crc_errors": 120,
        "cxl_aer_fatal": True,
        "reset_gpr_residual": True,
        "bios_version": "v1.0.4",
        "bmc_version": "v2.5.1",
    }


def test_redfish_request_flows_through_diagnostic_engine():
    request = load_redfish_request(REDFISH_SAMPLE)

    report = DiagnosticEngine().analyze(request)

    assert report.risk.level == "critical"
    assert report.risk.score >= 85
    categories = {insight.category for insight in report.rca.insights}
    assert {"Power", "Interconnect", "Memory", "Firmware"} <= categories


def test_redfish_ingestor_handles_minimal_snapshot():
    request = RedfishIngestor().from_dict({"chassis": {"Id": "RACK-MIN-01"}})

    assert request.rack_id == "RACK-MIN-01"
    assert request.payload["cxl_aer_fatal"] is False
    assert request.payload["reset_gpr_residual"] is False
    assert "bios_version" not in request.payload
    assert "bmc_version" not in request.payload


def test_redfish_ingestor_rejects_non_object_snapshot():
    try:
        RedfishIngestor().from_dict(["not", "an", "object"])
    except ValueError as exc:
        assert "JSON object" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-object snapshot")
