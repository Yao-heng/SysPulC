# SysPulC — System Pulse Core

[![SysPulC-CI](https://github.com/Yao-heng/SysPulC/actions/workflows/syspulc-ci.yml/badge.svg)](https://github.com/Yao-heng/SysPulC/actions/workflows/syspulc-ci.yml)

**SysPulC turns rack-scale platform telemetry and firmware signals into
structured root-cause analysis (RCA), a rack-level risk score, suggested
owners, and release-gate guidance.**

It is a working **prototype** written in Python — not a production AIOps
platform. It demonstrates cross-layer reliability thinking from 24+ years of
server/notebook platform firmware work (BIOS/BMC, bring-up, root-cause
analysis): when failure signals span power, interconnect, memory fabric, and
firmware at once, a single log rarely tells the story, so SysPulC correlates
them with small, explainable agents instead of a black box.

## Features

Implemented today:

- **Multi-agent diagnostics** — telemetry agent (voltage sag, NVLink CRC,
  CXL AER), errata agent (firmware/silicon errata-style checks), and an RCA
  agent that synthesizes their findings
- **Rack risk scoring** — 0–100 score with risk drivers, suggested owners,
  and a release-gate recommendation
- **Intermittent hang triage** — classifies the hang phase, explains which
  logs are expected vs. missing *by design*, and generates an evidence
  capture plan plus an A/B isolation plan (instead of stopping at "no log")
- **Redfish ingestor** — converts a Redfish-style BMC snapshot (chassis
  sensors, BIOS/BMC versions, EventLog entries) into the native SysPulC
  event format (`syspulc/ingestors/`)
- **CLI and FastAPI service** sharing one diagnostic engine
- **Test suite + CI** — pytest on every push, plus CLI and API smoke tests
  in GitHub Actions

Planned, **not** implemented yet:

- Additional ingestors (IPMI SEL, dmesg, PCIe AER, CXL logs) and live BMC
  polling over the Redfish HTTP API
- RAG knowledge base over public errata notes, debug checklists, and RCA
  history
- Validation gap analysis, mitigation playbook generation, and
  prompt-injection-aware LLM reporting from trusted evidence

## Quick Start

Requires Python 3.11+.

```bash
git clone https://github.com/Yao-heng/SysPulC.git
cd SysPulC
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the CLI on the bundled sample event:

```bash
python -m syspulc.cli.syspulc_cli --input samples/telemetry_event.json
```

Or feed it a Redfish-style BMC snapshot instead (converted by the Redfish
ingestor):

```bash
python -m syspulc.cli.syspulc_cli --redfish-input samples/redfish_chassis_telemetry.json
```

Run the tests:

```bash
pytest
```

Expected result: `16 passed`.

Start the API service:

```bash
uvicorn syspulc.api:app --reload
curl http://127.0.0.1:8000/health
# {"status":"ok","service":"syspulc"}
curl -X POST http://127.0.0.1:8000/analyze -H "Content-Type: application/json" -d @samples/telemetry_event.json
curl -X POST http://127.0.0.1:8000/analyze/hang -H "Content-Type: application/json" -d @samples/intermittent_hang_event.json
```

Both `POST` endpoints also accept an empty body, in which case the bundled
sample event is analyzed as a demo default. `GET /sample` returns the sample
request payload so you can inspect or modify the request format.

## Example Output

Actual output of
`python -m syspulc.cli.syspulc_cli --input samples/telemetry_event.json`
(excerpt):

```text
========================================================================
SysPulC AIOps Engine - Analyzing rack: RACK-DEMO-01
Event ID: EVT-DEMO-0001
Timestamp: 2026-01-01T00:00:00+00:00
========================================================================

Diagnostic Insights And RCA Report

Agent: RCA-Agent | [CRITICAL] (RCA)
Summary: Rack RACK-DEMO-01 has a confirmed high-risk instability path. Primary signal: Transient power rail sag detected: 180.0 mV exceeds the 150 mV threshold. Multi-agent correlation identified 5 finding(s).
Confidence: 96.0%
  - Aggregated 5 insight(s) across agents.

Agent: Telemetry-Agent | [CRITICAL] (Power)
Summary: Transient power rail sag detected: 180.0 mV exceeds the 150 mV threshold.
Confidence: 95.0%
  - Telemetry sag: 180.0 mV on monitored power rail.
  - High di/dt accelerator transient pulse observed.

Agent: Telemetry-Agent | [FATAL] (Memory)
Summary: CXL memory fabric poison or uncorrectable AER fatal event.
Confidence: 99.0%
  - CXL AER register indicates an uncorrectable fatal event.
  - Device-to-host memory coherency may be stalled.

Rack Risk Assessment
Risk Score: 100/100 (critical)
Release Gate: Block release until owner, root cause, fix plan, and retest evidence are reviewed.
Suggested Owners:
  - BIOS / BMC / Firmware
  - Firmware / Platform / Silicon Vendor
  - Firmware / Platform / Validation
  - Power / Platform / ODM
```

The sample event models a rack incident in which a GPU workload triggers a
voltage sag, NVLink CRC counters indicate interconnect degradation, CXL AER
reports a fatal memory fabric condition, and BIOS/BMC firmware revisions are
misaligned. The hang sample (`samples/intermittent_hang_event.json`) models a
warm-reboot hang that reproduces 3 times in 50 loops with only a coarse BMC
SEL marker — the triage agent explains why a complete OS log may not exist
and what instrumentation the next reproduction loop needs.

## Project Structure

```text
syspulc/
  agents/
    base_agent.py          # AgentRequest / AgentInsight / AgentResponse schemas
    telemetry_agent.py     # voltage sag, NVLink CRC, CXL AER checks
    errata_agent.py        # firmware / silicon errata-style checks
    rca_agent.py           # multi-agent insight synthesis
    hang_triage_agent.py   # intermittent hang state + evidence planning
  ingestors/
    redfish_ingestor.py    # Redfish-style snapshot -> AgentRequest
  cli/
    syspulc_cli.py         # --input / --redfish-input / flag-driven demo
  api.py                   # FastAPI: /health /sample /analyze /analyze/hang
  diagnostics.py           # shared engine used by CLI and API
  risk_scoring.py          # rack risk score, owners, release gate
samples/
  telemetry_event.json             # stable fixture (tests depend on it)
  intermittent_hang_event.json     # hang triage sample
  redfish_chassis_telemetry.json   # Redfish-style snapshot sample
scripts/
  generate_sample_telemetry.py     # random demo events -> samples/generated/
tests/
  test_agents.py
  test_api.py
  test_hang_triage.py
  test_redfish_ingestor.py
  test_sample_generator.py
.github/workflows/
  syspulc-ci.yml
```

Note on the sample generator: it writes random demo events to
`samples/generated/` (gitignored) and never overwrites the stable fixture
`samples/telemetry_event.json`.

## Why It Matters

AI compute clusters are increasingly difficult to debug because failure
signals span multiple layers:

- BIOS, BMC, firmware, and microcode revisions
- Power rail transients and thermal envelope limits
- PCIe, CXL, NVLink, and rack-scale interconnect health
- Kernel, BMC SEL, Redfish, and platform event logs
- Validation coverage gaps and historical RCA knowledge

SysPulC explores a practical workflow for turning those signals into
structured diagnostic evidence and owner-ready mitigation guidance. The hang
triage workflow captures a specific cross-layer debug skill: when an
intermittent hang has no useful OS log, the tool should not stop at "no
data." It should classify the hang phase, explain which logs are expected or
not expected, and define the instrumentation needed for the next
reproduction loop.

## Architecture

```text
Telemetry / Firmware Signals          Redfish-style BMC snapshot
          |                                      |
          v                                      v
   Agent Request Schema              Redfish Ingestor
          |                                      |
          +------------------+-------------------+
                             v
              +-------------------+      +----------------+
              | Telemetry Agent   |      | Errata Agent   |
              | - voltage sag     |      | - silicon hint |
              | - NVLink CRC      |      | - BIOS/BMC rev |
              | - CXL AER fatal   |      +----------------+
              +-------------------+              |
                             +-----------+-------------+
                                         v
                                    RCA Agent
                                         |
                                         v
                          Structured RCA + Risk Scoring

Intermittent hang: HangTriageRequest -> HangTriageAgent -> HangTriageReport
(phase classification, expected vs. missing evidence, no-log interpretation,
evidence capture plan, A/B isolation plan, release risk)
```

## Career Positioning

This project is designed to highlight cross-domain experience in:

- Server BIOS, BMC, firmware, and platform reliability
- AI infrastructure telemetry and rack-scale failure analysis
- Multi-agent diagnostic workflow design
- Python-based reliability tooling
- Secure and explainable AI-assisted RCA workflows

## Safety And Data Notes

All data in this repository is fictional demo data. Do not commit proprietary
logs, customer telemetry, NDA errata content, credentials, or production
system identifiers.

## License

MIT — see [LICENSE](LICENSE).
