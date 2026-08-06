import argparse
import json
import random
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_OUTPUT = Path("samples") / "telemetry_event.json"


def build_sample_event(rack_id: str) -> dict:
    """Build a fictional rack telemetry event for local demos."""
    return {
        "rack_id": rack_id,
        "event_id": f"EVT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": {
            "voltage_sag_mv": round(random.uniform(120.0, 210.0), 1),
            "nvlink_crc_errors": random.randint(10, 160),
            "cxl_aer_fatal": random.choice([False, False, True]),
            "reset_gpr_residual": random.choice([False, True]),
            "bios_version": "v1.0.4",
            "bmc_version": "v2.5.1",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate fictional SysPulC telemetry sample data."
    )
    parser.add_argument("--rack-id", default="RACK-DEMO-01")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    event = build_sample_event(args.rack_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(event, indent=2), encoding="utf-8")
    print(f"Wrote sample telemetry event to {args.output}")


if __name__ == "__main__":
    main()
