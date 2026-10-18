"""Unit tests for RiskScorer thresholds, defaults, and aggregation rules.

The scoring formula under test (see syspulc/risk_scoring.py):
base 8 + severity points + category points + round(confidence * 8) per
non-RCA insight, +10 when >= 3 distinct categories are implicated,
capped at 100. Levels: >=85 critical, >=65 high, >=35 medium, else low.
"""

from syspulc.agents.base_agent import AgentInsight
from syspulc.risk_scoring import RiskScorer


def insight(
    severity: str = "INFO",
    category: str = "Power",
    confidence: float = 0.0,
    summary: str = "test insight",
) -> AgentInsight:
    return AgentInsight(
        agent_name="TestAgent",
        severity=severity,
        category=category,
        summary=summary,
        confidence_score=confidence,
    )


def test_empty_insights_yield_baseline_low_risk():
    result = RiskScorer().score("RACK-01", [])

    assert result.score == 8
    assert result.level == "low"
    assert result.drivers == []
    assert result.suggested_owners == []
    assert "No release gate action" in result.release_gate_recommendation


def test_rca_insights_are_excluded_from_scoring():
    # Even a FATAL RCA insight must not move the score: RCA is the
    # roll-up narrative, not an independent risk signal.
    result = RiskScorer().score("RACK-01", [insight("FATAL", "RCA", 1.0)])

    assert result.score == 8
    assert result.level == "low"
    assert result.drivers == []


def test_medium_threshold_boundary():
    scorer = RiskScorer()
    # 8 + WARNING(12) + Power(14) + round(0.0*8)=0 -> 34 (low)
    just_below = scorer.score("R", [insight("WARNING", "Power", 0.0)])
    assert just_below.score == 34
    assert just_below.level == "low"
    # 8 + 12 + 14 + round(0.125*8)=1 -> 35 (medium)
    at_threshold = scorer.score("R", [insight("WARNING", "Power", 0.125)])
    assert at_threshold.score == 35
    assert at_threshold.level == "medium"
    assert "targeted regression" in at_threshold.release_gate_recommendation


def test_high_threshold_boundary():
    scorer = RiskScorer()
    # (12+14+0) + (12+14+4) + 8 = 64 (medium); single category -> no bonus
    just_below = scorer.score(
        "R", [insight("WARNING", "Power", 0.0), insight("WARNING", "Power", 0.5)]
    )
    assert just_below.score == 64
    assert just_below.level == "medium"
    # Second insight confidence 0.625 -> round(5.0)=5 instead of 4 -> 65 (high)
    at_threshold = scorer.score(
        "R", [insight("WARNING", "Power", 0.0), insight("WARNING", "Power", 0.625)]
    )
    assert at_threshold.score == 65
    assert at_threshold.level == "high"
    assert "Hold release decision" in at_threshold.release_gate_recommendation


def test_critical_threshold_boundary():
    scorer = RiskScorer()
    base = insight("FATAL", "Memory", 1.0)  # 36+18+8 = 62
    # 8 + 62 + INFO(0) + Thermal(10) + round(0.5*8)=4 -> 84 (high)
    just_below = scorer.score("R", [base, insight("INFO", "Thermal", 0.5)])
    assert just_below.score == 84
    assert just_below.level == "high"
    # Confidence 0.625 -> 5 points instead of 4 -> 85 (critical)
    at_threshold = scorer.score("R", [base, insight("INFO", "Thermal", 0.625)])
    assert at_threshold.score == 85
    assert at_threshold.level == "critical"
    assert "Block release" in at_threshold.release_gate_recommendation


def test_score_is_capped_at_100():
    many_fatal = [insight("FATAL", "Memory", 1.0) for _ in range(5)]
    result = RiskScorer().score("R", many_fatal)

    assert result.score == 100
    assert result.level == "critical"


def test_multi_category_bonus_and_driver():
    # Three distinct categories with INFO severity and zero confidence:
    # 8 + Power(14) + Interconnect(10) + Thermal(10) = 42, +10 bonus = 52.
    result = RiskScorer().score(
        "R",
        [
            insight("INFO", "Power"),
            insight("INFO", "Interconnect"),
            insight("INFO", "Thermal"),
        ],
    )

    assert result.score == 52
    assert "Multiple cross-layer domains are implicated." in result.drivers


def test_unknown_severity_and_category_use_default_points():
    # Unknown severity -> 4 points, unknown category -> 6 points, no owner.
    result = RiskScorer().score("R", [insight("WEIRD", "Quantum", 0.0)])

    assert result.score == 8 + 4 + 6
    assert result.level == "low"
    assert result.suggested_owners == []


def test_owners_are_deduplicated_and_sorted():
    result = RiskScorer().score(
        "R",
        [
            insight("WARNING", "Power"),
            insight("CRITICAL", "Power"),
            insight("WARNING", "Memory"),
        ],
    )

    assert result.suggested_owners == [
        "Firmware / Platform / Validation",
        "Power / Platform / ODM",
    ]
