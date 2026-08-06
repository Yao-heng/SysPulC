"""
SysPulC (System-Pulse-Core) — Telemetry Agent
Specialized Agent for sub-ms signal analysis, voltage sags, CXL AER retries, and NVLink CRC errors.
"""

from typing import Dict, Any, List
from syspulc.agents.base_agent import BaseAgent, AgentRequest, AgentResponse, AgentInsight


class TelemetryAgent(BaseAgent):
    """Agent specialized in physical layer, interconnect, and power rail telemetry analysis."""

    def __init__(self):
        super().__init__(
            name="Telemetry-Agent",
            description="Analyzes sub-ms power rail sags, CXL AER link retries, and NVLink CRC error rates."
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        payload = request.payload
        insights: List[AgentInsight] = []

        # 1. Inspect Voltage Sag / Power-Rail Stealing
        voltage_sag = payload.get("voltage_sag_mv", 0)
        if voltage_sag > 150:
            insights.append(AgentInsight(
                agent_name=self.name,
                severity="CRITICAL",
                category="Power",
                summary=f"Transient Power-Rail Stealing detected: Voltage Sag {voltage_sag}mV exceeds 150mV threshold.",
                evidence=[f"Telemetry Sag: {voltage_sag}mV on VDD_CPU rail", "High di/dt GPU transient pulse observed."],
                confidence_score=0.95
            ))

        # 2. Inspect NVLink CRC Error Retries
        nvlink_crc_errors = payload.get("nvlink_crc_errors", 0)
        if nvlink_crc_errors > 50:
            insights.append(AgentInsight(
                agent_name=self.name,
                severity="WARNING",
                category="Interconnect",
                summary=f"NVLink Fabric Degradation: CRC Error Counter = {nvlink_crc_errors}.",
                evidence=[f"NVLink Link 0 CRC error counter: {nvlink_crc_errors}", "High retry frequency detected."],
                confidence_score=0.88
            ))

        # 3. Inspect CXL AER Uncorrectable Errors
        cxl_aer_fatal = payload.get("cxl_aer_fatal", False)
        if cxl_aer_fatal:
            insights.append(AgentInsight(
                agent_name=self.name,
                severity="FATAL",
                category="Memory",
                summary="CXL Memory Fabric Poison / Uncorrectable AER Fatal Event.",
                evidence=["CXL AER Register UESta set to Fatal", "Device-to-Host memory coherency stalled."],
                confidence_score=0.99
            ))

        status = "SUCCESS" if insights else "INCONCLUSIVE"
        return AgentResponse(
            agent_name=self.name,
            status=status,
            insights=insights,
            metadata={"processed_events": len(payload)}
        )
