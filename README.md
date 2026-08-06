# SysPulC - System Pulse Core

SysPulC is an evolving Python-based AI infrastructure reliability diagnostics engine. It is designed to analyze telemetry, firmware, and platform signals across rack-scale systems, then generate structured RCA insights, risk scores, validation recommendations, and release-quality guidance.

The current implementation includes multi-agent diagnostics, CLI execution, sample telemetry ingestion, CI, and tests. The roadmap expands SysPulC toward FastAPI service endpoints, BIOS/BMC and Redfish/IPMI log ingestion, risk scoring, validation gap analysis, firmware dependency mapping, and LLM-assisted RCA reporting.

## Why It Matters

AI compute clusters are increasingly difficult to debug because failure signals
span multiple layers:

- BIOS, BMC, firmware, and microcode revisions
- Power rail transients and thermal envelope limits
- PCIe, CXL, NVLink, and rack-scale interconnect health
- Kernel, BMC SEL, Redfish, and platform event logs
- Validation coverage gaps and historical RCA knowledge

SysPulC explores a practical workflow for turning those signals into structured
diagnostic evidence and owner-ready mitigation guidance.

## Current Prototype Scope

Implemented today:

- Pydantic-based request, response, and insight schemas
- Base agent abstraction for diagnostic workflows
- Telemetry agent for voltage sag, NVLink CRC, and CXL AER signals
- Errata agent for firmware and silicon errata style checks
- RCA agent for multi-agent insight synthesis
- CLI demo for rack-level diagnosis
- GitHub Actions workflow for basic CLI validation
- Unit tests for agent behavior

Planned extensions:

- BIOS/BMC, Redfish, IPMI, dmesg, PCIe AER, and CXL log ingestors
- FastAPI service layer for interactive analysis
- RAG knowledge base for public errata notes, debug checklists, and RCA history
- Risk scoring and mitigation playbook generation
- Prompt-injection-aware LLM report generation from trusted evidence

## Architecture

```text
Telemetry / Firmware Signals
          |
          v
   Agent Request Schema
          |
          v
+-------------------+      +----------------+
| Telemetry Agent   |      | Errata Agent   |
| - voltage sag     |      | - silicon hint |
| - NVLink CRC      |      | - BIOS/BMC rev |
| - CXL AER fatal   |      +----------------+
+-------------------+              |
          |                         |
          +-----------+-------------+
                      v
                 RCA Agent
                      |
                      v
          Structured Diagnostic Report
```

## Repository Structure

```text
syspulc/
  agents/
    base_agent.py
    telemetry_agent.py
    errata_agent.py
    rca_agent.py
  cli/
    syspulc_cli.py
samples/
  telemetry_event.json
scripts/
  generate_sample_telemetry.py
tests/
  test_agents.py
.github/workflows/
  syspulc-ci.yml
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m syspulc.cli.syspulc_cli --rack-id RACK-CI-TEST
pytest
```

Example CLI output includes:

- RCA severity
- agent name
- diagnostic category
- summary
- supporting evidence
- confidence score

## Example Use Case

SysPulC can model a rack incident where:

- A GPU workload triggers a voltage sag over the warning threshold
- NVLink CRC counters indicate interconnect degradation
- CXL AER reports a fatal memory fabric condition
- BIOS/BMC firmware revisions are misaligned
- The RCA agent produces a consolidated diagnosis for firmware, platform, and
  data center operations teams

## Career Positioning

This project is designed to highlight cross-domain experience in:

- Server BIOS, BMC, firmware, and platform reliability
- AI infrastructure telemetry and rack-scale failure analysis
- Multi-agent diagnostic workflow design
- Python-based reliability tooling
- Secure and explainable AI-assisted RCA workflows

## Safety And Data Notes

All data in this repository is fictional demo data. Do not commit proprietary
logs, customer telemetry, NDA errata content, credentials, or production system
identifiers.
