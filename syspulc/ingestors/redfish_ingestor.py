"""Redfish ingestor: convert a Redfish-style snapshot into a SysPulC event.

The input is a single JSON snapshot assembled from the Redfish responses a
BMC would normally serve separately (this is demo tooling, so the sections
are bundled into one file):

- ``chassis``         -- a Chassis resource with a ``Sensors`` array
                         (``Name`` / ``Reading`` per sensor).
- ``computer_system`` -- a ComputerSystem resource (``BiosVersion``).
- ``manager``         -- a Manager resource (``FirmwareVersion``, the BMC).
- ``event_log``       -- an EventLog entries collection (``Members`` with
                         ``Severity`` / ``Message`` / ``MessageId`` / ``Created``).

The output is the same :class:`AgentRequest` envelope the CLI and API use
for native SysPulC events (see ``samples/telemetry_event.json``), so a
Redfish snapshot flows through the existing agents unchanged.

Mapping rules (keyword based, intentionally small and explicit):

- Sensor named ``*voltage*sag*``        -> ``payload["voltage_sag_mv"]``
- Sensor named ``*nvlink*crc*``         -> ``payload["nvlink_crc_errors"]``
- Event mentioning CXL + AER + fatal or uncorrectable
                                        -> ``payload["cxl_aer_fatal"] = True``
- Event mentioning ``GPR residual``     -> ``payload["reset_gpr_residual"] = True``
- ``computer_system.BiosVersion``       -> ``payload["bios_version"]``
- ``manager.FirmwareVersion``           -> ``payload["bmc_version"]``
- ``chassis.Id``                        -> ``rack_id``
- ``snapshot_id`` / ``collected_at``    -> ``event_id`` / ``timestamp``

All data handled here is fictional demo data.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from syspulc.agents.base_agent import AgentRequest


class RedfishIngestor:
    """Convert Redfish-style snapshots into SysPulC ``AgentRequest`` objects."""

    def from_path(self, path: Path | str) -> AgentRequest:
        """Load a Redfish-style snapshot JSON file and convert it."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.from_dict(data)

    def from_dict(self, data: dict[str, Any]) -> AgentRequest:
        """Convert one parsed Redfish-style snapshot dict."""
        if not isinstance(data, dict):
            raise ValueError("Redfish snapshot must be a JSON object.")

        chassis = data.get("chassis") or {}
        system = data.get("computer_system") or {}
        manager = data.get("manager") or {}
        event_log = data.get("event_log") or {}
        entries = event_log.get("Members") or []

        payload: dict[str, Any] = {}
        self._map_sensors(chassis.get("Sensors") or [], payload)
        payload["cxl_aer_fatal"] = self._has_cxl_aer_fatal(entries)
        payload["reset_gpr_residual"] = self._has_gpr_residual(entries)

        bios_version = system.get("BiosVersion")
        if bios_version:
            payload["bios_version"] = bios_version
        bmc_version = manager.get("FirmwareVersion")
        if bmc_version:
            payload["bmc_version"] = bmc_version

        timestamp = data.get("collected_at")
        if not timestamp and entries:
            timestamp = entries[0].get("Created")
        if not timestamp:
            timestamp = datetime.now(UTC).isoformat()

        return AgentRequest(
            rack_id=chassis.get("Id") or data.get("rack_id") or "RACK-REDFISH-UNKNOWN",
            event_id=data.get("snapshot_id") or "EVT-REDFISH-UNKNOWN",
            timestamp=timestamp,
            payload=payload,
        )

    @staticmethod
    def _map_sensors(sensors: list[dict[str, Any]], payload: dict[str, Any]) -> None:
        for sensor in sensors:
            name = str(sensor.get("Name", "")).lower()
            reading = sensor.get("Reading")
            if reading is None:
                continue
            if "voltage" in name and "sag" in name:
                payload["voltage_sag_mv"] = float(reading)
            elif "nvlink" in name and "crc" in name:
                payload["nvlink_crc_errors"] = int(reading)

    @staticmethod
    def _event_text(entry: dict[str, Any]) -> str:
        return (
            f"{entry.get('Message', '')} {entry.get('MessageId', '')}".lower()
        )

    @classmethod
    def _has_cxl_aer_fatal(cls, entries: list[dict[str, Any]]) -> bool:
        for entry in entries:
            text = cls._event_text(entry)
            if "cxl" in text and "aer" in text and (
                "fatal" in text or "uncorrectable" in text
            ):
                return True
        return False

    @classmethod
    def _has_gpr_residual(cls, entries: list[dict[str, Any]]) -> bool:
        return any("gpr residual" in cls._event_text(entry) for entry in entries)


def load_redfish_request(path: Path | str) -> AgentRequest:
    """Convenience wrapper: load a snapshot file as an ``AgentRequest``."""
    return RedfishIngestor().from_path(path)
