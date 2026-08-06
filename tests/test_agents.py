from syspulc.agents.base_agent import AgentRequest
from syspulc.agents.errata_agent import ErrataAgent
from syspulc.agents.rca_agent import RCAAgent
from syspulc.agents.telemetry_agent import TelemetryAgent


def build_request(**payload):
    return AgentRequest(
        rack_id="RACK-TEST-01",
        event_id="EVT-TEST-0001",
        payload=payload,
    )


def test_telemetry_agent_flags_power_interconnect_and_cxl_events():
    request = build_request(
        voltage_sag_mv=180.0,
        nvlink_crc_errors=120,
        cxl_aer_fatal=True,
    )

    response = TelemetryAgent().process(request)

    assert response.status == "SUCCESS"
    assert [insight.category for insight in response.insights] == [
        "Power",
        "Interconnect",
        "Memory",
    ]
    assert response.insights[0].severity == "CRITICAL"
    assert response.insights[2].severity == "FATAL"


def test_telemetry_agent_is_inconclusive_when_thresholds_are_nominal():
    request = build_request(
        voltage_sag_mv=80.0,
        nvlink_crc_errors=0,
        cxl_aer_fatal=False,
    )

    response = TelemetryAgent().process(request)

    assert response.status == "INCONCLUSIVE"
    assert response.insights == []


def test_errata_agent_flags_firmware_risks():
    request = build_request(
        reset_gpr_residual=True,
        bios_version="v1.0.4",
        bmc_version="v2.5.1",
    )

    response = ErrataAgent().process(request)

    assert response.status == "SUCCESS"
    assert len(response.insights) == 2
    assert response.insights[0].category == "Firmware"


def test_rca_agent_synthesizes_critical_findings():
    request = build_request(
        voltage_sag_mv=180.0,
        nvlink_crc_errors=120,
        reset_gpr_residual=True,
    )
    telemetry_response = TelemetryAgent().process(request)
    errata_response = ErrataAgent().process(request)

    response = RCAAgent().synthesize(request, [telemetry_response, errata_response])

    assert response.status == "SUCCESS"
    assert response.insights[0].agent_name == "RCA-Agent"
    assert response.insights[0].severity == "CRITICAL"
    assert response.metadata["critical_findings"] >= 1
