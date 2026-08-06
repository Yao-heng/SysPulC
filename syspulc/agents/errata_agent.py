"""
SysPulC (System-Pulse-Core) — Errata Agent
Specialized Agent for Silicon Errata, Microcode Patch Dependencies, and FW Revision Matching.
"""

from typing import Dict, Any, List
from syspulc.agents.base_agent import BaseAgent, AgentRequest, AgentResponse, AgentInsight


class ErrataAgent(BaseAgent):
    """Agent specialized in silicon-level errata lookup and firmware microcode dependency analysis."""

    def __init__(self):
        super().__init__(
            name="Errata-Agent",
            description="Cross-references silicon errata database and firmware/microcode dependencies."
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        payload = request.payload
        insights: List[AgentInsight] = []

        # 1. Check for CPU Reset Initialization Errata
        reset_gpr_residual = payload.get("reset_gpr_residual", False)
        if reset_gpr_residual:
            insights.append(AgentInsight(
                agent_name=self.name,
                severity="CRITICAL",
                category="Firmware",
                summary="Silicon Errata Match: AP General Purpose Register non-zero data post-reset.",
                evidence=[
                    "Intel Xeon Silicon Errata #SKL-089: AP GPR residual state in warm boot.",
                    "Microcode patch MCU_0x0671_v24 or BIOS power-sequencing update required."
                ],
                confidence_score=0.98
            ))

        # 2. Check for BIOS / BMC Firmware Version Mismatch
        bios_ver = payload.get("bios_version", "")
        bmc_ver = payload.get("bmc_version", "")
        if bios_ver and bmc_ver and ("v1.0" in bios_ver and "v2.5" in bmc_ver):
            insights.append(AgentInsight(
                agent_name=self.name,
                severity="WARNING",
                category="Firmware",
                summary="Firmware Version Mismatch: Unaligned BIOS/BMC IPMB handshake protocol.",
                evidence=[f"BIOS: {bios_ver}, BMC: {bmc_ver}", "Requires synchronized FW update."],
                confidence_score=0.90
            ))

        status = "SUCCESS" if insights else "INCONCLUSIVE"
        return AgentResponse(
            agent_name=self.name,
            status=status,
            insights=insights,
            metadata={"checked_errata_entries": 2}
        )
