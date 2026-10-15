"""Log and telemetry ingestors that produce SysPulC ``AgentRequest`` objects."""

from syspulc.ingestors.redfish_ingestor import RedfishIngestor, load_redfish_request

__all__ = ["RedfishIngestor", "load_redfish_request"]
