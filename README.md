# SysPulC - System Pulse Core

SysPulC is an evolving Python-based AI infrastructure reliability diagnostics
engine. It analyzes telemetry, firmware, and platform signals across rack-scale
systems, then generates structured RCA insights, rack-level risk scores,
suggested owners, and release-quality guidance.

The project is intentionally scoped as a lightweight working engine, not a
production AIOps platform. It demonstrates system architecture thinking across
BIOS/BMC, server platform debug, GPU rack telemetry, CXL/NVLink fabrics,
release-quality decisions, and AI-assisted reliability workflows.

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

## Current Implementation

Implemented today:

- Pydantic-based request, response, and insight schemas
- Base agent abstraction for diagnostic workflows
- Telemetry agent for voltage sag, NVLink CRC, and CXL AER signals
- Errata agent for firmware and silicon errata style checks
- RCA agent for multi-agent insight synthesis
- Rack-level risk scoring with risk drivers, suggested owners, and release gate
  recommendations
- CLI demo for rack-level diagnosis
- FastAPI service with `/health`, `/sample`, and `/analyze` endpoints
- GitHub Actions workflow for tests, CLI smoke, and API import validation
- Unit tests for agents and API behavior

Planned extensions:

- BIOS/BMC, Redfish, IPMI, dmesg, PCIe AER, and CXL log ingestors
- RAG knowledge base for public errata notes, debug checklists, and RCA history
- Validation gap analysis and firmware dependency mapping
- Mitigation playbook generation
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
       Structured RCA + Risk Scoring
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
  api.py
  diagnostics.py
  risk_scoring.py
samples/
  telemetry_event.json
scripts/
  generate_sample_telemetry.py
tests/
  test_agents.py
  test_api.py
.github/workflows/
  syspulc-ci.yml
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m syspulc.cli.syspulc_cli --rack-id RACK-CI-TEST
uvicorn syspulc.api:app --reload
pytest
```

API endpoints:

- `GET /health`
- `GET /sample`
- `POST /analyze`

Example API call:

```bash
curl -X POST http://127.0.0.1:8000/analyze
```

Example CLI and API output includes:

- RCA severity
- agent name
- diagnostic category
- summary
- supporting evidence
- confidence score
- rack risk score
- suggested owners
- release gate recommendation

## Example Use Case

SysPulC can model a rack incident where:

- A GPU workload triggers a voltage sag over the warning threshold
- NVLink CRC counters indicate interconnect degradation
- CXL AER reports a fatal memory fabric condition
- BIOS/BMC firmware revisions are misaligned
- The RCA agent produces a consolidated diagnosis and risk score for firmware,
  platform, validation, ODM, and data center operations teams

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
