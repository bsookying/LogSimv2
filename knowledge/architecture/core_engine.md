---
type: Architecture Component
title: Core Simulator Engine & Configuration
description: Documents `log_simulator.py`, startup flow, threading/queue pipelines, deferred execution, and the 57-key `config.json` schema.
resource: log_simulator.py
tags: [engine, threading, queues, config, pipeline, python]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Core Simulator Engine & Configuration

## 1. Entry Point & Execution Modes (`log_simulator.py`)

`log_simulator.py` (4,421 lines) is the root entry point (`python -u log_simulator.py`). Neither `log_simulator.py` nor `dashboard/app.py` parses CLI flags (`argparse`/`sys.argv` are unused); all runtime behavior is driven by `.env`, `config.json`, the interactive stdin menu, or the Flask dashboard API.

### Startup Sequence (`main()`, lines 4194–4323)
1. Loads `.env` via `python-dotenv` (`load_dotenv()`).
2. Loads `config.json` and replaces `PLACEHOLDER_*` tokens (`PLACEHOLDER_AWS_ACCOUNT_ID`, `PLACEHOLDER_GCP_PROJECT_ID`, `PLACEHOLDER_GCP_PROJECT_NUMBER`) from environment variables.
3. Expands `service_accounts` when `_expand: true`.
4. Fetches live Tor exit nodes (`fetch_tor_exit_nodes()`, lines 94–130) from `https://check.torproject.org/torbulkexitlist` with Onionoo enrichment (no static fallback).
5. Initializes high-cardinality pools and resolution tables: `cloud_ids.expand_pools(config)`, `domain_corpus.load(config)` (Tranco long-tail domains), and `resolver.load(config)` (shared forward/reverse DNS).
6. Auto-discovers top-level modules in `modules/*.py` defining `NAME` via `load_modules()` (lines 132–161).
7. Launches `dashboard/app.py` as a child subprocess (`_start_dashboard()`, lines 4379–4416) with `LOGSIM_PARENT_PID` set and `atexit.register(_cleanup_dashboard)`.
8. Builds the shared `session_context` (`modules.session_utils.build_session_context(config)`).
9. Enters the interactive `input()` menu loop:
   * **Mode 1**: Independent Product Logs (Serial round-robin or Parallel per-module threads).
   * **Mode 2**: Correlated Attack Scenarios (`1–29`, via `get_scenarios()`, lines 4005–4133 — 23 synthetic scenarios including 6 linked kill chains + 6 XDR WinRM orchestration stories `24–29`).
   * **Mode 3**: Fire a single specific analytic-capable threat.
   * **Headless Mode (`_run_headless()`, lines 4349–4366)**: Automatically entered on `EOFError` (containers/systemd without TTY); blocks on `_dashboard_proc.wait()` and handles `SIGTERM` gracefully.

---

## 2. Concurrency, Queuing & Pacing Architecture

LogSimv2 uses Python `threading`, `queue.Queue`, `threading.Timer`, `threading.Condition` + `heapq`, and `ThreadPoolExecutor` (no `asyncio`).

### Core Runtime Primitives
* **`RunCapture` & `capture_run`** (`log_simulator.py:1068–1115`): Thread-safe per-run emission counter bound via `contextvars.ContextVar("logsim_run_collector")` so concurrent scenarios record isolated manifests (`total`, `by_module`, `by_event`).
* **`ModuleState`** (`dashboard/app.py:444–554`): Per-module thread lifecycle (`_thread`, `_stop_event`, `_lock`), live-updatable `threat_level` and `event_interval`, 130s rolling per-second rate deque, 600-item threat history, and analytic on-demand threat list.

### Send Pipeline Lanes (`dashboard/app.py:1108–1290`)
Dashboard module workers (`_module_worker()`) use fixed-schedule monotonic pacing (`_pace_wait()`, dropping backlog when lag exceeds `1.0s`, minimum interval `0.0001s`) and enqueue payloads onto transport-specific bounded queues (`SEND_QUEUE_SIZE=5000`, `SEND_ENQUEUE_MAX_WAIT_S=30` before incrementing `queue_drops`):
* **Batched Lanes (`_BATCH_QUEUES["http" | "cribl" | "syslog"]`)**: Drained by `BATCH_SEND_WORKERS` (`4` threads per lane), lingering up to `BATCH_LINGER_MS` (`100ms`) or `HTTP_BATCH_MAX_EVENTS` (`1000`), grouping by `(module, config, event_name)` before calling `process_and_send(msgs, ...)`.
* **Unbatched Lane (`_SEND_QUEUE`)**: Used by `s3`, `wec`, and `pubsub`, drained by `SEND_WORKERS` (`8` threads) into `process_and_send()`.

### Background Daemon Threads
* **Engine (`log_simulator.py`)**:
  * `s3-batch-flusher` (1s poll flushing buffered CloudTrail records on 4s idle, 30s max age, or 500 events).
  * `deferred-release` (min-heap `_DEFERRED_HEAP` holding `modules.deferred` future-stamped scenario steps until wall-clock `release_at`, preventing future-dated logs in XSIAM).
  * `_wec_pool` (`ThreadPoolExecutor`, `wec_sender_threads=4`) + `_wec_batch_timer` (`1000ms`).
* **Dashboard (`dashboard/app.py`)**:
  * `dashboard-watchdog` (5s poll on `LOGSIM_PARENT_PID`; exits via `os._exit(0)` if parent dies).
  * `scheduler` (1s tick firing pending scheduled jobs).
  * `health-monitor` (60s check loop caching `/api/health` and queueing state-transition alerts).
  * `tenant-health` (15m `TENANT_HEALTH_REFRESH_S=900` XQL check of XSIAM `DOMAIN_HEALTH` alerts).
  * `random-campaigns` (optional Poisson-timed Identity Threat Campaign runner).
  * On-demand worker threads for `scenario-*`, `attack-*`, `training-*`, and `baduser-*`.

---

## 3. Log Dispatch Pipeline (`process_and_send()` -> `_transmit()`)

1. **`process_and_send()` (`log_simulator.py:1460–1484`)**: Records telemetry into `_capture_sink` / `_run_collector`, short-circuits on `_dry_run` or Training bulk freeze (`_bulk_collector`), holds future-dated records in `_DEFERRED_HEAP`, and forwards immediate records to `_transmit()`.
2. **`_transmit()` (`log_simulator.py:1486–1550`)**: Calls `integrations.transport.resolve(module, config)` to pick `cribl`, `s3`, `http`, `wec`, `pubsub`, or `syslog`. On hard transport errors, marks the pipe down (`transport_retry_s=300`) and invokes `_fall_back()` to resend via `send_cribl_batch()` when Cribl fallback is enabled.

---

## 4. Configuration Schema (`config.json`)

`config.json` (`552 KB`, `20,829` lines, `57` top-level keys) is loaded read-only at startup into memory (never modified on disk by the engine or dashboard):

| Group | Count | Key Highlights |
|---|---|---|
| Global & Transports | 6 | `syslog_port` (`514`), `base_event_interval_seconds` (`1.0`), `cribl_fallback` (`true`), `transport_retry_s` (`300`), `threat_generation_levels` (6 tiers: `Benign Traffic Only` through `Insane`), `http_collectors` (`okta`, `proofpoint`, `windows_events`). |
| Network, Intel & DNS | 16 | `internal_networks` (12 CIDRs), `internal_servers` (25), `database_servers` (26), `management_plane` (admin subnet, 2 jump hosts, 4 admins, 8 network devices), `tor_exit_nodes` (live-filled), `vpn_providers` (12), `exfiltration_destinations` (60), `vpn_novel_country_pool` (84), `resolver`, `domain_corpus`, `user_agents` (33). |
| Personas & Identities | 6 | `user_profiles` (**501 users** with `display_name`, `department`, `role`, `email`, `aws_iam_user`, `gcp_iam_user`, and multi-device lists), `service_accounts` (`_expand: true`), `user_behavior` (`department_affinity: 0.6`). |
| Module Config Blocks | 22 | 9 Microsoft/Cribl configs (`o365_*`, `azure_*`), `aws_config` (46 keys, 156 IAM users/roles), `gcp_config` (32 keys), `okta_config` (101 SSO apps), `proofpoint_config`, `windows_events_config` (`transport: "wec"`), `vmware_esxi_config` (port `1518`), `infoblox_config` (port `1516`), `apache_config` (port `1515`), `cisco_asa_config` (port `1514`), `checkpoint_config`, `fortinet_config`, `firepower_config`, `panw_ngfw_config` (port `514`, PAN-OS `12.2.4-h1`), `zscaler_config`. |
| Training & XDR | 2 | `training_config` (6 4-hour packs: `domain-dominance-day`, `beaconing-implant-day`, `server-breach-cloud-day`, `cloud-ransomware-day`, `perimeter-intrusion-day`, `identity-cloud-day`) and `xdr_orchestration` (WinRM/XSIAM settings). |

### Threat Pacing Models
* **Standard Modules**: Cooldown timer per threat level (`Realistic`: `7200s`, `Elevated`: `3600s`, `High`: `1800s`, `Extreme`: `600s`, `Insane`: `0s` / 50-50 benign-threat split).
* **Microsoft Entra / O365 Feeds**: Wall-clock Poisson *episodes* (`modules/azure_common.py:ThreatGate`) after a 500-record warmup (`0.03` to `6.0` episodes/module/hr).
