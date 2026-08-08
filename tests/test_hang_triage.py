from syspulc.agents.hang_triage_agent import HangTriageAgent, HangTriageRequest


def test_reboot_hang_triage_requires_instrumentation():
    request = HangTriageRequest(
        issue_id="HANG-TEST-0001",
        phase="reboot",
        symptom="Intermittent hang during warm reboot loop on dGPU SKU.",
        platform="workstation",
        available_logs=["BMC SEL abnormal reset marker"],
        missing_logs=["complete OS dump", "BIOS serial checkpoint"],
        reproduce_rate="3/50",
        recent_changes=["BIOS 1.0.4", "GPU driver 555.10"],
    )

    report = HangTriageAgent().analyze(request)

    assert report.issue_id == "HANG-TEST-0001"
    assert "Warm reboot transition" in report.hang_state_classification
    assert report.release_risk == "high"
    assert "complete OS dump" in report.likely_missing_data
    assert any("BIOS checkpoint" in item for item in report.next_evidence_capture)
    assert any("PCIe speed" in item for item in report.ab_isolation_plan)
    assert any("release gate review" in item for item in report.next_actions)


def test_pre_boot_hang_without_logs_explains_missing_os_data():
    request = HangTriageRequest(
        issue_id="HANG-TEST-0002",
        phase="pre_boot",
        symptom="System hangs before logo with no OS event log.",
        platform="server",
        available_logs=[],
        missing_logs=["OS event log"],
        reproduce_rate="1/20",
    )

    report = HangTriageAgent().analyze(request)

    assert report.release_risk == "high"
    assert "No OS log can be expected" in report.no_log_interpretation
    assert "OS event log" in report.likely_missing_data
    assert any("POST code" in item for item in report.next_evidence_capture)
