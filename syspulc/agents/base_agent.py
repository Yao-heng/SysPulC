"""
SysPulC base agent architecture.

Defines abstract agents and structured message types for multi-agent AIOps
diagnostic workflows.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Structured request payload passed to SysPulC agents."""

    rack_id: str = Field(..., description="Target rack or chassis identifier.")
    event_id: str = Field(..., description="Unique telemetry event identifier.")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetry, firmware, or log payload.",
    )


class AgentInsight(BaseModel):
    """Structured diagnostic insight produced by a specialized agent."""

    agent_name: str
    severity: str = Field(..., description="INFO, WARNING, CRITICAL, or FATAL.")
    category: str = Field(..., description="Power, Thermal, Interconnect, Firmware, Memory, or RCA.")
    summary: str
    evidence: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    """Response payload returned by an agent execution run."""

    agent_name: str
    status: str = Field(..., description="SUCCESS, FAILED, or INCONCLUSIVE.")
    insights: list[AgentInsight] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all SysPulC diagnostic agents."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process the telemetry request and produce diagnostic insights."""
        raise NotImplementedError
