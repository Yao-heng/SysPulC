"""
RCA synthesis agent.

Correlates multi-agent diagnostic insights and generates a structured root
cause analysis response.
"""

from syspulc.agents.base_agent import (
    AgentInsight,
    AgentRequest,
    AgentResponse,
    BaseAgent,
)


class RCAAgent(BaseAgent):
    """Master agent for synthesizing findings into a root cause analysis report."""

    def __init__(self) -> None:
        super().__init__(
            name="RCA-Agent",
            description="Correlates telemetry and errata insights into an RCA report.",
        )

    def synthesize(
        self,
        request: AgentRequest,
        agent_responses: list[AgentResponse],
    ) -> AgentResponse:
        """Synthesize insights from all executed agents."""
        all_insights: list[AgentInsight] = []
        critical_count = 0

        for response in agent_responses:
            for insight in response.insights:
                all_insights.append(insight)
                if insight.severity in {"CRITICAL", "FATAL"}:
                    critical_count += 1

        if critical_count > 0:
            primary_cause = all_insights[0].summary if all_insights else "Unknown anomaly"
            rca_summary = (
                f"Rack {request.rack_id} has a confirmed high-risk instability path. "
                f"Primary signal: {primary_cause} Multi-agent correlation identified "
                f"{len(all_insights)} finding(s)."
            )
            severity = "CRITICAL"
            confidence = 0.96
        else:
            rca_summary = (
                f"Rack {request.rack_id} telemetry is within the current prototype thresholds."
            )
            severity = "INFO"
            confidence = 0.50

        rca_insight = AgentInsight(
            agent_name=self.name,
            severity=severity,
            category="RCA",
            summary=rca_summary,
            evidence=[f"Aggregated {len(all_insights)} insight(s) across agents."],
            confidence_score=confidence,
        )

        return AgentResponse(
            agent_name=self.name,
            status="SUCCESS",
            insights=[rca_insight, *all_insights],
            metadata={
                "correlated_agents": len(agent_responses),
                "critical_findings": critical_count,
            },
        )

    def process(self, request: AgentRequest) -> AgentResponse:
        """Default process method required by BaseAgent."""
        return self.synthesize(request, [])
