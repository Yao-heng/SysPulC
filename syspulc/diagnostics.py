"""Shared diagnostic engine used by the CLI and FastAPI service."""

from pydantic import BaseModel

from syspulc.agents.base_agent import AgentRequest, AgentResponse
from syspulc.agents.errata_agent import ErrataAgent
from syspulc.agents.rca_agent import RCAAgent
from syspulc.agents.telemetry_agent import TelemetryAgent
from syspulc.risk_scoring import RiskAssessment, RiskScorer


class DiagnosticReport(BaseModel):
    """Full SysPulC analysis result."""

    request: AgentRequest
    agent_responses: list[AgentResponse]
    rca: AgentResponse
    risk: RiskAssessment


class DiagnosticEngine:
    """Run SysPulC agents and rack-level risk scoring."""

    def __init__(self) -> None:
        self.telemetry_agent = TelemetryAgent()
        self.errata_agent = ErrataAgent()
        self.rca_agent = RCAAgent()
        self.risk_scorer = RiskScorer()

    def analyze(self, request: AgentRequest) -> DiagnosticReport:
        agent_responses = [
            self.telemetry_agent.process(request),
            self.errata_agent.process(request),
        ]
        rca = self.rca_agent.synthesize(request, agent_responses)
        risk = self.risk_scorer.score(request.rack_id, rca.insights)
        return DiagnosticReport(
            request=request,
            agent_responses=agent_responses,
            rca=rca,
            risk=risk,
        )
