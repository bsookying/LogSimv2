---
okf_version: "0.2"
type: Knowledge Bundle Root
title: LogSimv2 Knowledge Base
description: Comprehensive OKF v0.2 architectural, API, module, transport, fork customization, and operations documentation for bsookying/LogSimv2.
tags: [logsimv2, cortex-xsiam, security-telemetry, python, flask, okf]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# LogSimv2 Knowledge Base

Welcome to the **Google OKF (Open Knowledge Format v0.2)** knowledge bundle for **LogSimv2** (`github.com/bsookying/LogSimv2`, forked from `phreezone/LogSimv2`). LogSimv2 is a modular synthetic security-log generator and purple-team orchestration engine targeting **Palo Alto Networks Cortex XSIAM** (XDM mapping, UEBA analytics, correlation rules, and multi-stage kill-chain testing).

## Directory Structure

```text
knowledge/
├── index.md                              # Bundle Root Manifest (OKF v0.2)
├── log.md                                # Chronological architecture & session log
├── architecture/                         # Core engine, plugin modules, transports & fork delta
│   ├── index.md                          # Subdirectory progressive disclosure index
│   ├── core_engine.md                    # log_simulator.py, threading/queues, dispatch pipeline, config.json
│   ├── modules_catalog.md                # 25 generator modules, 23 helpers, xdr_orchestration, plugin contract
│   ├── transports_and_integrations.md    # 6 log transports, Cribl fallback, XSIAM API & MCP tooling
│   └── fork_customizations.md            # bsookying/LogSimv2 vs upstream, Settings UI v3/v4 patch state
├── app/                                  # Web dashboard UI & REST/MCP control surface
│   ├── index.md                          # Subdirectory progressive disclosure index
│   ├── dashboard_ui.md                   # Flask SPA (6 tabs + Settings v4 patch spec), polling & workflows
│   └── api_contract.md                   # /api/* & /api/v1/* endpoints, API key auth, OpenAPI & MCP
└── playbooks/                            # Deployment, IaC, XSIAM imports & operations runbooks
    ├── index.md                          # Subdirectory progressive disclosure index
    ├── deployment_and_iac.md             # Local, Docker/Compose, GHCR CI, AWS CloudFormation & GCP Terraform
    └── xsiam_imports_and_ops.md          # 151 correlation rules, bundle.json, sync/deploy/reload & health checks
```

## Quick Links

* [Architecture Overview](/architecture/index.md): Core simulator engine, 25 generator modules, 6 transports with Cribl fallback, and fork delta.
* [Dashboard & API](/app/index.md): Flask web dashboard SPA, REST control surface (`/api/v1/*`), OpenAPI/Postman specs, and MCP server.
* [Operations & Deployment Playbooks](/playbooks/index.md): Docker, CloudFormation, Terraform, XSIAM correlation rule lifecycle, and health operations.
* [Changelog & Session Log](/log.md): Reverse-chronological history of repository audits, fork changes, and session handovers.

## Upstream Repo Documentation Cross-Reference

This OKF bundle complements (without duplicating) the upstream reference documentation already in the repository:
* `README.md` — Project overview, feature list, and release history.
* `docs/` — Topic guides (`getting-started.md`, `transports.md`, `attack-scenarios.md`, `bad-user-playbooks.md`, `training-mode.md`, `xsiam-byok-knowledge.md`, etc.) + 22 per-module guides in `docs/modules/`.
* `integrations/README.md` & `integrations/openapi.yaml` — External REST/MCP automation contract.
