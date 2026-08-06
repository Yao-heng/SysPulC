"""
SysPulC (System-Pulse-Core) — Base Agent Architecture
Defines abstract BaseAgent and structured message types for Multi-Agent AIOps orchestration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentRequest(BaseModel):
    """Structured request payload passed to SysPulC Agents."""
    rack_id: str = Field(..., description="Target Rack/Chassis Identifier (e.g. RACK-01)")
    event_id: str = Field(..., description="Unique Telemetry Event ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict, description="Telemetry/Log payload")


class AgentInsight(BaseModel):
    """Structured diagnostic insight produced by a specialized Agent."""
    agent_name: str
    severity: str = Field(..., description="INFO, WARNING, CRITICAL, FATAL")
    category: str = Field(..., description="Power, Thermal, Interconnect, Firmware, Memory")
    summary: str
    evidence: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    """Response payload returned by an Agent execution run."""
    agent_name: str
    status: str = Field(..., description="SUCCESS, FAILED, INCONCLUSIVE")
    insights: List[AgentInsight] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract Base Class for all SysPulC Autonomous Agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """Processes the telemetry request and produces diagnostic insights."""
        pass
