"""
SysPulC (System-Pulse-Core) — Command Line Interface
Main entry point for running multi-agent diagnostics and telemetry analysis on AI clusters.
"""

import sys
import json
import argparse
from datetime import datetime
from syspulc.agents.base_agent import AgentRequest
from syspulc.agents.telemetry_agent import TelemetryAgent
from syspulc.agents.errata_agent import ErrataAgent
from syspulc.agents.rca_agent import RCAAgent


def main():
    parser = argparse.ArgumentParser(
        description="SysPulC: Autonomous AIOps & Telemetry Intelligence Engine"
    )
    parser.add_argument("--rack-id", type=str, default="RACK-01", help="Target Rack/Chassis ID")
    parser.add_argument("--voltage-sag", type=float, default=180.0, help="Voltage Sag in mV")
    parser.add_argument("--nvlink-errors", type=int, default=120, help="NVLink CRC Error Counter")
    parser.add_argument("--reset-gpr-residual", action="store_true", default=True, help="Simulate AP GPR reset residual errata")
    args = parser.parse_args()

    print("=" * 70)
    print(f" SysPulC AIOps Engine — Analyzing Rack: {args.rack_id}")
    print(f" Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    # 1. Build Telemetry Payload
    payload = {
        "voltage_sag_mv": args.voltage_sag,
        "nvlink_crc_errors": args.nvlink_errors,
        "reset_gpr_residual": args.reset_gpr_residual,
        "bios_version": "v1.0.4",
        "bmc_version": "v2.5.1"
    }

    request = AgentRequest(
        rack_id=args.rack_id,
        event_id=f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        payload=payload
    )

    # 2. Run Specialized Agents
    telemetry_agent = TelemetryAgent()
    errata_agent = ErrataAgent()

    resp_telemetry = telemetry_agent.process(request)
    resp_errata = errata_agent.process(request)

    # 3. Synthesize via RCA Master Agent
    rca_agent = RCAAgent()
    final_response = rca_agent.synthesize(request, [resp_telemetry, resp_errata])

    # 4. Output Results
    print("\n[DIAGNOSTIC INSIGHTS & RCA REPORT]")
    for insight in final_response.insights:
        print(f"\n Agent: {insight.agent_name} | [{insight.severity}] ({insight.category})")
        print(f" Summary: {insight.summary}")
        print(f" Confidence: {insight.confidence_score * 100:.1f}%")
        for ev in insight.evidence:
            print(f"   • {ev}")

    print("\n" + "=" * 70)
    print(" SysPulC Diagnosis Completed Successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
