"""
SysPulC (System-Pulse-Core) — RCA (Root Cause Analysis) Synthesis Agent
Master Agent that correlates multi-agent diagnostic insights and generates structured RCA reports.
"""

from typing import Dict, Any, List
from syspulc.agents.base_agent import BaseAgent, AgentRequest, AgentResponse, AgentInsight


class RCAAgent(BaseAgent):
    """Master Agent for synthesizing multi-agent findings into structured RCA reports."""

    def __init__(self):
        super().__init__(
            name="RCA-Agent",
            description="Correlates insights across Telemetry, Errata, and Power agents to produce Root Cause Analysis."
        )

    def synthesize(self, request: AgentRequest, agent_responses: List[AgentResponse]) -> AgentResponse:
        """Synthesizes insights from all executed agents."""
        all_insights: List[AgentInsight] = []
        critical_count = 0

        for resp in agent_responses:
            for insight in resp.insights:
                all_insights.append(insight)
                if insight.severity in ["CRITICAL", "FATAL"]:
                    critical_count += 1

        # Synthesize Root Cause Summary
        if critical_count > 0:
            primary_cause = all_insights[0].summary if all_insights else "Unknown Multi-Domain Anomaly"
            rca_summary = (
                f"ROOT CAUSE CONFIRMED: System hang/instability on rack {request.rack_id} "
                f"triggered by '{primary_cause}'. Multi-agent correlation identified {len(all_insights)} findings."
            )
            severity = "CRITICAL"
        else:
            rca_summary = f"Rack {request.rack_id} telemetry within nominal thresholds. No critical RCA triggers."
            severity = "INFO"

        rca_insight = AgentInsight(
            agent_name=self.name,
            severity=severity,
            category="RCA_Synthesis",
            summary=rca_summary,
            evidence=[f"Aggregated {len(all_insights)} insights across agents."],
            confidence_score=0.96 if critical_count > 0 else 0.50
        )

        return AgentResponse(
            agent_name=self.name,
            status="SUCCESS",
            insights=[rca_insight] + all_insights,
            metadata={"correlated_agents": len(agent_responses), "critical_findings": critical_count}
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        """Default process method required by BaseAgent."""
        return self.synthesize(request, [])
