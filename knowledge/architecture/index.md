---
type: Directory Index
title: Architecture Concepts
description: Progressive disclosure index covering LogSimv2's core engine, generator modules, transport/integration architecture, and fork customizations.
tags: [architecture, index]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Architecture Concepts

* [Core Simulator Engine & Configuration](/architecture/core_engine.md): Documents `log_simulator.py`, startup flow, threading/queue pipelines, deferred execution, and the 57-key `config.json` schema.
* [Generator Modules & Plugin Catalog](/architecture/modules_catalog.md): Inventories all 25 auto-discovered log generators, 23 shared helper/engine modules, the `xdr_orchestration` purple-team subpackage, and the module plugin contract.
* [Transports & Integrations](/architecture/transports_and_integrations.md): Details all 6 log ingestion transports, automatic Cribl fallback routing, batching/circuit breakers, and XSIAM API/MCP tooling under `integrations/`.
* [Fork Customizations & Upstream Delta](/architecture/fork_customizations.md): Tracks the exact divergence between `bsookying/LogSimv2` and `phreezone/LogSimv2`, including the Settings UI v3/v4 patch scripts and upstream drift.
