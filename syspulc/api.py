"""FastAPI service for SysPulC diagnostics."""

from pathlib import Path
import json

from fastapi import FastAPI, HTTPException

from syspulc.agents.base_agent import AgentRequest
from syspulc.diagnostics import DiagnosticEngine, DiagnosticReport


app = FastAPI(
    title="SysPulC Reliability Diagnostics API",
    description=(
        "Rack-scale telemetry and firmware diagnostics for AI infrastructure "
        "reliability triage."
    ),
    version="0.2.0",
)

engine = DiagnosticEngine()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_EVENT = PROJECT_ROOT / "samples" / "telemetry_event.json"


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return a lightweight service readiness signal."""
    return {"status": "ok", "service": "syspulc"}


@app.get("/sample", response_model=AgentRequest, tags=["diagnostics"])
def get_sample_event() -> AgentRequest:
    """Return the bundled fictional telemetry sample as an analysis request."""
    return _load_sample_request()


@app.post("/analyze", response_model=DiagnosticReport, tags=["diagnostics"])
def analyze(request: AgentRequest | None = None) -> DiagnosticReport:
    """Analyze rack telemetry and firmware signals."""
    try:
        analysis_request = request or _load_sample_request()
        return engine.analyze(analysis_request)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _load_sample_request() -> AgentRequest:
    event = json.loads(SAMPLE_EVENT.read_text(encoding="utf-8"))
    return AgentRequest(
        rack_id=event["rack_id"],
        event_id=event["event_id"],
        timestamp=event["timestamp"],
        payload=event.get("payload", {}),
    )
