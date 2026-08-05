# SysPulC (System-Pulse-Core) — Autonomous AIOps & Telemetry Intelligence Engine

[![SysPulC-CI](https://github.com/Yao-heng/SysPulC/actions/workflows/syspulc-ci.yml/badge.svg)](https://github.com/Yao-heng/SysPulC/actions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Domain](https://img.shields.io/badge/Domain-AI_Infrastructure_&_AIOps-orange.svg)]()

> **SysPulC (System-Pulse-Core)** is an AI-native observability, telemetry correlation, and autonomous diagnostic engine engineered for hyperscale AI compute infrastructure (GPU/TPU clusters, Rack-Scale GB200/NVL72 systems, and CXL memory fabrics).

---

## 🌟 Executive Summary & Problem Statement

In modern AI Factories and hyperscale GPU clusters, hardware-software friction leads to severe operational inefficiencies:
* **Zombie Compute & Speculative Wastage**: GPUs idling at $P_0$ performance states during AI inference decode phases.
* **Asynchronous System Hangs**: Elusive failure modes triggered by transient power pulses (*Power-Rail Stealing*), PCIe/CXL retries, or firmware handshake timing gaps.
* **Context-Blind Telemetry**: Legacy OS/BIOS tools lack multi-layer correlation across hardware, firmware, and AI runtimes.

**SysPulC** bridges application-level AI runtimes with low-level silicon/firmware registers, converting fragmented system telemetry into autonomous root-cause intelligence.

---

## 🏗 System Architecture & Key Modules

SysPulC employs a **Multi-Agent Agentic Workflow** backed by a **Vector-based RAG Knowledge Graph**:
