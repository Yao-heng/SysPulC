"""Command line interface for SysPulC rack diagnostics."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from syspulc.agents.base_agent import AgentRequest
from syspulc.agents.errata_agent import ErrataAgent
from syspulc.agents.rca_agent import RCAAgent
from syspulc.agents.telemetry_agent import TelemetryAgent


def load_event(path: Path) -> dict[str, Any]:
    """Load a SysPulC event envelope from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def build_request(args: argparse.Namespace) -> AgentRequest:
    if args.input:
        event = load_event(args.input)
        return AgentRequest(
            rack_id=event["rack_id"],
            event_id=event["event_id"],
            timestamp=event.get("timestamp", datetime.now(UTC).isoformat()),
            payload=event.get("payload", {}),
        )

    payload = {
        "voltage_sag_mv": args.voltage_sag,
        "nvlink_crc_errors": args.nvlink_errors,
        "cxl_aer_fatal": args.cxl_aer_fatal,
        "reset_gpr_residual": args.reset_gpr_residual,
        "bios_version": "v1.0.4",
        "bmc_version": "v2.5.1",
    }
    return AgentRequest(
        rack_id=args.rack_id,
        event_id=f"EVT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now(UTC).isoformat(),
        payload=payload,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SysPulC: multi-agent diagnostics for AI infrastructure reliability."
    )
    parser.add_argument("--rack-id", default="RACK-01", help="Target rack or chassis ID.")
    parser.add_argument("--input", type=Path, help="Optional JSON telemetry event envelope.")
    parser.add_argument("--voltage-sag", type=float, default=180.0, help="Voltage sag in mV.")
    parser.add_argument("--nvlink-errors", type=int, default=120, help="NVLink CRC error counter.")
    parser.add_argument(
        "--reset-gpr-residual",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Simulate a firmware errata-style warm reset residual condition.",
    )
    parser.add_argument(
        "--cxl-aer-fatal",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Simulate a CXL AER fatal event.",
    )
    args = parser.parse_args()

    request = build_request(args)

    print("=" * 72)
    print(f"SysPulC AIOps Engine - Analyzing rack: {request.rack_id}")
    print(f"Event ID: {request.event_id}")
    print(f"Timestamp: {request.timestamp}")
    print("=" * 72)

    telemetry_response = TelemetryAgent().process(request)
    errata_response = ErrataAgent().process(request)
    final_response = RCAAgent().synthesize(
        request,
        [telemetry_response, errata_response],
    )

    print("\nDiagnostic Insights And RCA Report")
    for insight in final_response.insights:
        print(f"\nAgent: {insight.agent_name} | [{insight.severity}] ({insight.category})")
        print(f"Summary: {insight.summary}")
        print(f"Confidence: {insight.confidence_score * 100:.1f}%")
        for evidence in insight.evidence:
            print(f"  - {evidence}")

    print("\n" + "=" * 72)
    print("SysPulC diagnosis completed successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
