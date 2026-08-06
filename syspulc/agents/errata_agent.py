"""
Errata agent for firmware and silicon dependency hints.

The current prototype models errata-style checks using fictional sample data.
"""

from syspulc.agents.base_agent import (
    AgentInsight,
    AgentRequest,
    AgentResponse,
    BaseAgent,
)


class ErrataAgent(BaseAgent):
    """Agent specialized in silicon errata and firmware dependency analysis."""

    def __init__(self) -> None:
        super().__init__(
            name="Errata-Agent",
            description="Cross-references silicon errata hints and firmware dependencies.",
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        payload = request.payload
        insights: list[AgentInsight] = []

        reset_gpr_residual = payload.get("reset_gpr_residual", False)
        if reset_gpr_residual:
            insights.append(
                AgentInsight(
                    agent_name=self.name,
                    severity="CRITICAL",
                    category="Firmware",
                    summary=(
                        "Silicon errata style match: application processor register "
                        "state may remain non-zero after warm reset."
                    ),
                    evidence=[
                        "Fictional errata hint: AP GPR residual state after warm boot.",
                        "Review microcode and BIOS power sequencing dependencies.",
                    ],
                    confidence_score=0.98,
                )
            )

        bios_ver = payload.get("bios_version", "")
        bmc_ver = payload.get("bmc_version", "")
        if bios_ver and bmc_ver and ("v1.0" in bios_ver and "v2.5" in bmc_ver):
            insights.append(
                AgentInsight(
                    agent_name=self.name,
                    severity="WARNING",
                    category="Firmware",
                    summary="Firmware version mismatch: BIOS and BMC handshake risk.",
                    evidence=[
                        f"BIOS: {bios_ver}, BMC: {bmc_ver}.",
                        "Synchronized firmware update should be reviewed.",
                    ],
                    confidence_score=0.90,
                )
            )

        status = "SUCCESS" if insights else "INCONCLUSIVE"
        return AgentResponse(
            agent_name=self.name,
            status=status,
            insights=insights,
            metadata={"checked_errata_entries": 2},
        )
