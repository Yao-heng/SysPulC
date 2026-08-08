"""Risk scoring for SysPulC diagnostic insights."""

from pydantic import BaseModel, Field

from syspulc.agents.base_agent import AgentInsight


SEVERITY_POINTS = {
    "INFO": 0,
    "WARNING": 12,
    "CRITICAL": 28,
    "FATAL": 36,
}

CATEGORY_POINTS = {
    "Power": 14,
    "Interconnect": 10,
    "Memory": 18,
    "Firmware": 12,
    "Thermal": 10,
    "RCA": 0,
}

OWNER_BY_CATEGORY = {
    "Power": "Power / Platform / ODM",
    "Interconnect": "Firmware / Platform / Silicon Vendor",
    "Memory": "Firmware / Platform / Validation",
    "Firmware": "BIOS / BMC / Firmware",
    "Thermal": "Thermal / Platform / ODM",
}


class RiskAssessment(BaseModel):
    """Rack-level operational risk assessment."""

    rack_id: str
    score: int = Field(ge=0, le=100)
    level: str
    drivers: list[str]
    suggested_owners: list[str]
    release_gate_recommendation: str


class RiskScorer:
    """Convert structured agent insights into a rack-level risk score."""

    def score(self, rack_id: str, insights: list[AgentInsight]) -> RiskAssessment:
        raw_score = 8
        drivers: list[str] = []
        owners: set[str] = set()
        categories: set[str] = set()

        for insight in insights:
            if insight.category == "RCA":
                continue

            severity_points = SEVERITY_POINTS.get(insight.severity, 4)
            category_points = CATEGORY_POINTS.get(insight.category, 6)
            confidence_points = round(insight.confidence_score * 8)

            raw_score += severity_points + category_points + confidence_points
            categories.add(insight.category)
            drivers.append(
                f"{insight.category}: {insight.severity} - {insight.summary}"
            )

            owner = OWNER_BY_CATEGORY.get(insight.category)
            if owner:
                owners.add(owner)

        if len(categories) >= 3:
            raw_score += 10
            drivers.append("Multiple cross-layer domains are implicated.")

        score = min(100, raw_score)
        level = self._level(score)
        return RiskAssessment(
            rack_id=rack_id,
            score=score,
            level=level,
            drivers=drivers,
            suggested_owners=sorted(owners),
            release_gate_recommendation=self._release_gate_recommendation(level),
        )

    def _level(self, score: int) -> str:
        if score >= 85:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    def _release_gate_recommendation(self, level: str) -> str:
        if level == "critical":
            return (
                "Block release until owner, root cause, fix plan, and retest "
                "evidence are reviewed."
            )
        if level == "high":
            return (
                "Hold release decision for risk review and require explicit "
                "closure evidence."
            )
        if level == "medium":
            return "Track through issue governance and require targeted regression."
        return "No release gate action required under current prototype thresholds."
