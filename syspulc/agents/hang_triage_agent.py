"""Intermittent hang triage agent.

This agent turns a cross-layer hang debug playbook into structured next actions.
It focuses on what data should exist, what may be missing by design, and how to
instrument the next reproduction loop when logs are absent.
"""

from typing import Literal

from pydantic import BaseModel, Field


HangPhase = Literal[
    "runtime",
    "shutdown",
    "reboot",
    "boot",
    "pre_boot",
    "sleep_resume",
    "unknown",
]


class HangTriageRequest(BaseModel):
    """Input for intermittent hang triage."""

    issue_id: str = Field(..., description="Issue, bug, or validation event ID.")
    phase: HangPhase = Field(
        default="unknown",
        description="Observed phase where the hang happens.",
    )
    symptom: str
    platform: str = "unknown"
    available_logs: list[str] = Field(default_factory=list)
    missing_logs: list[str] = Field(default_factory=list)
    observed_state: dict[str, str | bool | int | float] = Field(default_factory=dict)
    reproduce_rate: str | None = None
    recent_changes: list[str] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)
    stress_condition: str | None = None


class HangTriageReport(BaseModel):
    """Structured intermittent hang triage result."""

    issue_id: str
    hang_state_classification: str
    expected_available_data: list[str]
    likely_missing_data: list[str]
    no_log_interpretation: str
    possible_root_cause_domains: list[str]
    next_evidence_capture: list[str]
    ab_isolation_plan: list[str]
    release_risk: str
    next_actions: list[str]


class HangTriageAgent:
    """Classify intermittent hangs and generate evidence capture guidance."""

    def analyze(self, request: HangTriageRequest) -> HangTriageReport:
        expected = self._expected_data(request.phase)
        likely_missing = self._likely_missing_data(request.phase, request.missing_logs)
        root_cause_domains = self._root_cause_domains(request)
        next_evidence = self._next_evidence_capture(request)
        ab_plan = self._ab_isolation_plan(request)
        release_risk = self._release_risk(request)

        return HangTriageReport(
            issue_id=request.issue_id,
            hang_state_classification=self._classify_state(request),
            expected_available_data=expected,
            likely_missing_data=likely_missing,
            no_log_interpretation=self._no_log_interpretation(request),
            possible_root_cause_domains=root_cause_domains,
            next_evidence_capture=next_evidence,
            ab_isolation_plan=ab_plan,
            release_risk=release_risk,
            next_actions=self._next_actions(request, release_risk),
        )

    def _classify_state(self, request: HangTriageRequest) -> str:
        phase_summary = {
            "runtime": "OS runtime hang or hard freeze path.",
            "shutdown": "Shutdown transition hang after services or drivers start unloading.",
            "reboot": "Warm reboot transition hang across OS, firmware, and reset paths.",
            "boot": "Boot path hang after platform power-on.",
            "pre_boot": "Pre-OS firmware path hang before OS handoff.",
            "sleep_resume": "Sleep or resume path hang across ACPI, EC, driver, and firmware states.",
            "unknown": "Unknown hang phase; physical state classification is required first.",
        }
        return phase_summary[request.phase]

    def _expected_data(self, phase: HangPhase) -> list[str]:
        common = [
            "test automation timestamp and loop count",
            "failure video or remote KVM capture",
            "platform version inventory",
        ]
        by_phase = {
            "runtime": [
                "OS event log or journal",
                "kernel dmesg or driver log",
                "crash dump, live dump, kdump, or WER if the dump path survives",
                "BMC SEL or Redfish EventLog if a platform threshold is crossed",
            ],
            "shutdown": [
                "partial OS shutdown marker",
                "previous boot journal or event log",
                "BMC SEL or Redfish EventLog",
                "EC or power button state if instrumented",
            ],
            "reboot": [
                "last OS shutdown or reboot marker",
                "BIOS checkpoint or POST code on next boot attempt",
                "BMC SEL or Redfish EventLog",
                "EC/BMC reset event if instrumented",
            ],
            "boot": [
                "BIOS serial log or checkpoint trace",
                "POST code",
                "BMC SEL or Redfish EventLog",
                "EC debug log if available",
            ],
            "pre_boot": [
                "BIOS serial log or checkpoint trace",
                "POST code",
                "power-good, reset, and strap timing capture",
                "BMC/EC event log if initialized early enough",
            ],
            "sleep_resume": [
                "Windows sleep study or Linux suspend/resume journal",
                "ACPI or EC trace",
                "driver power-state logs",
                "BMC SEL if platform power or thermal events occur",
            ],
            "unknown": [
                "physical state evidence: screen, LEDs, fan, keyboard, ping, BMC, KVM",
                "test automation timestamp and loop count",
                "external video capture",
            ],
        }
        return [*common, *by_phase[phase]]

    def _likely_missing_data(
        self,
        phase: HangPhase,
        declared_missing_logs: list[str],
    ) -> list[str]:
        by_phase = {
            "runtime": [
                "latest log lines may be lost if OS freezes before filesystem flush",
            ],
            "shutdown": [
                "complete OS dump",
                "full driver stack trace after driver unload begins",
                "complete shutdown log if storage or kernel logging stops first",
            ],
            "reboot": [
                "complete OS dump",
                "next-boot OS log if firmware never hands off to OS",
                "driver unload evidence if the system wedges during reset sequencing",
            ],
            "boot": [
                "OS event log",
                "dmesg or journal for a boot that never reaches OS",
            ],
            "pre_boot": [
                "OS event log",
                "kernel log",
                "driver dump",
                "BMC SEL if the event is below platform logging threshold",
            ],
            "sleep_resume": [
                "complete resume log if storage or OS logging never resumes",
            ],
            "unknown": [
                "phase-specific logs until the hang state is classified",
            ],
        }
        return [*by_phase[phase], *declared_missing_logs]

    def _no_log_interpretation(self, request: HangTriageRequest) -> str:
        if request.available_logs:
            return (
                "Some evidence is available. Correlate timestamps before assigning "
                "ownership."
            )
        if request.phase in {"boot", "pre_boot"}:
            return (
                "No OS log can be expected if the platform never reaches OS handoff. "
                "Treat this as a firmware, power, reset, memory training, or device "
                "enumeration observability gap."
            )
        if request.phase in {"shutdown", "reboot", "sleep_resume"}:
            return (
                "No complete OS log may be expected in a transition-state hang. The "
                "next run must add BIOS/EC/BMC checkpoints and external capture."
            )
        return (
            "No log is not a closure reason. It indicates insufficient observability; "
            "instrument the next reproduction loop."
        )

    def _root_cause_domains(self, request: HangTriageRequest) -> list[str]:
        domains = {
            "BIOS/EC/BMC reset or power sequencing race",
            "Platform power rail transient or power-good timing issue",
            "PCIe/CXL/NVLink device retrain or link stability issue",
            "OS driver unload, resume, or watchdog path issue",
            "Firmware version dependency or BIOS/BMC handshake mismatch",
        }

        symptom = request.symptom.lower()
        if request.phase in {"boot", "pre_boot"}:
            domains.update(
                {
                    "Memory training or early silicon initialization hang",
                    "Device enumeration or option ROM path hang",
                }
            )
        if request.phase in {"shutdown", "reboot"}:
            domains.update(
                {
                    "Warm reset sequencing race",
                    "Device D-state transition or driver unload dependency",
                }
            )
        if request.phase == "sleep_resume":
            domains.update(
                {
                    "ACPI method, EC event, or device power-state transition issue",
                }
            )
        if "gpu" in symptom or "dgpu" in symptom:
            domains.add("dGPU reset, PCIe retrain, or high-power SKU dependency")
        if "dock" in symptom:
            domains.add("Dock, USB-C, or external display topology dependency")
        return sorted(domains)

    def _next_evidence_capture(self, request: HangTriageRequest) -> list[str]:
        capture = [
            "Record screen, LEDs, fan state, keyboard response, ping, BMC reachability, and power button behavior.",
            "Capture exact timestamps from the validation tool, DUT, BMC, and external equipment.",
            "Enable BIOS checkpoint or serial debug trace for the failing phase.",
            "Require ODM to provide loop count, failure rate, failure video, and timestamp correlation.",
        ]
        if request.phase in {"shutdown", "reboot", "boot", "pre_boot"}:
            capture.extend(
                [
                    "Add EC/BMC debug logging for reset, power-good, and power button state transitions.",
                    "Capture POST code progression and last checkpoint before hang.",
                    "Use oscilloscope or logic analyzer on key rails, reset, power-good, and GPIO signals.",
                ]
            )
        if request.phase in {"runtime", "sleep_resume"}:
            capture.extend(
                [
                    "Enable OS crash dump, watchdog, NMI, kernel dump, netconsole, or serial console where applicable.",
                    "Enable driver verbose logs for GPU, storage, network, and power-management paths.",
                ]
            )
        return capture

    def _ab_isolation_plan(self, request: HangTriageRequest) -> list[str]:
        plan = [
            "Compare latest BIOS against a known-good BIOS.",
            "Compare latest EC/BMC firmware against a known-good build.",
            "Run with suspect device disabled or removed where feasible.",
            "Run with the latest and previous OS driver package.",
            "Track pass/fail rate by exact configuration and loop count.",
        ]
        if request.phase in {"shutdown", "reboot", "sleep_resume"}:
            plan.extend(
                [
                    "Disable ASPM/L1SS or low-power state policy for isolation.",
                    "Change device power policy or disable Modern Standby/suspend path for isolation.",
                ]
            )
        if "gpu" in request.symptom.lower() or "dgpu" in request.symptom.lower():
            plan.extend(
                [
                    "Limit PCIe speed or lane width for isolation.",
                    "Run without the dGPU or with an alternate GPU SKU.",
                ]
            )
        return plan

    def _release_risk(self, request: HangTriageRequest) -> str:
        has_repro = bool(request.reproduce_rate and request.reproduce_rate != "0/0")
        has_no_logs = not request.available_logs
        if request.phase in {"boot", "shutdown", "reboot", "pre_boot"} and has_repro:
            return "high"
        if has_no_logs and has_repro:
            return "high"
        if request.phase == "unknown":
            return "medium"
        return "medium" if request.missing_logs else "low"

    def _next_actions(self, request: HangTriageRequest, release_risk: str) -> list[str]:
        actions = [
            "Classify the exact hang state before accepting an owner assignment.",
            "Build a reproduce matrix by phase, BIOS/EC/BMC/driver version, device SKU, stress condition, and loop count.",
            "Do not accept 'no log' as closure; convert it into a required instrumentation plan.",
        ]
        if release_risk == "high":
            actions.append(
                "Escalate to release gate review until failure rate, owner, root cause path, and retest evidence are available."
            )
        if request.recent_changes:
            actions.append(
                "Run A/B against recent changes: " + ", ".join(request.recent_changes)
            )
        return actions
