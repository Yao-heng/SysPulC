"""
Telemetry agent for rack-level platform signals.

The current prototype checks voltage sag, CXL AER, and NVLink CRC indicators.
"""

from syspulc.agents.base_agent import (
    AgentInsight,
    AgentRequest,
    AgentResponse,
    BaseAgent,
)


class TelemetryAgent(BaseAgent):
    """Agent specialized in physical layer, interconnect, and power rail telemetry."""

    def __init__(self) -> None:
        super().__init__(
            name="Telemetry-Agent",
            description=(
                "Analyzes power rail sags, CXL AER events, and NVLink CRC error rates."
            ),
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        payload = request.payload
        insights: list[AgentInsight] = []

        voltage_sag = payload.get("voltage_sag_mv", 0)
        if voltage_sag > 150:
            insights.append(
                AgentInsight(
                    agent_name=self.name,
                    severity="CRITICAL",
                    category="Power",
                    summary=(
                        "Transient power rail sag detected: "
                        f"{voltage_sag} mV exceeds the 150 mV threshold."
                    ),
                    evidence=[
                        f"Telemetry sag: {voltage_sag} mV on monitored power rail.",
                        "High di/dt accelerator transient pulse observed.",
                    ],
                    confidence_score=0.95,
                )
            )

        nvlink_crc_errors = payload.get("nvlink_crc_errors", 0)
        if nvlink_crc_errors > 50:
            insights.append(
                AgentInsight(
                    agent_name=self.name,
                    severity="WARNING",
                    category="Interconnect",
                    summary=(
                        "NVLink fabric degradation detected: "
                        f"CRC error counter is {nvlink_crc_errors}."
                    ),
                    evidence=[
                        f"NVLink CRC error counter: {nvlink_crc_errors}.",
                        "High retry frequency detected.",
                    ],
                    confidence_score=0.88,
                )
            )

        cxl_aer_fatal = payload.get("cxl_aer_fatal", False)
        if cxl_aer_fatal:
            insights.append(
                AgentInsight(
                    agent_name=self.name,
                    severity="FATAL",
                    category="Memory",
                    summary="CXL memory fabric poison or uncorrectable AER fatal event.",
                    evidence=[
                        "CXL AER register indicates an uncorrectable fatal event.",
                        "Device-to-host memory coherency may be stalled.",
                    ],
                    confidence_score=0.99,
                )
            )

        status = "SUCCESS" if insights else "INCONCLUSIVE"
        return AgentResponse(
            agent_name=self.name,
            status=status,
            insights=insights,
            metadata={"processed_fields": len(payload)},
        )
