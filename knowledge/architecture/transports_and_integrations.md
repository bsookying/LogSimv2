---
type: Architecture Component
title: Transports & Integrations
description: Details all 6 log ingestion transports, automatic Cribl fallback routing, batching/circuit breakers, and XSIAM API/MCP tooling under `integrations/`.
resource: integrations/
tags: [transports, cribl, syslog, wec, s3, pubsub, xsiam-api, mcp]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Transports & Integrations

LogSimv2 decouples log generation from log delivery via `integrations/transport.py` and `log_simulator.py:_transmit()`, supporting **6 ingestion transports** with automatic **Cribl fallback**, plus XSIAM tenant management and AI/automation integrations under `integrations/` (14 files).

---

## 1. Ingestion Transports & Resilience

| Transport | Env Configuration | Batching / Wire Format | Failure & Resilience Behavior |
|---|---|---|---|
| **Syslog TCP** (`syslog`) | `SYSLOG_HOST`, per-module `syslog_port` (`514`, `1514–1518`) | Persistent per-`(host, port)` TCP sockets (`SO_KEEPALIVE`, 60s idle recycle), newline-framed chunks up to `SYSLOG_BATCH_MAX_BYTES` (`256 KiB`). | 1 reconnect retry on socket error; failure triggers `mark_down()` + Cribl fallback. |
| **HTTP Collector** (`http`) | `HTTP_COLLECTOR_URL`, `*_COLLECTOR_URL`, `*_AUTH_TYPE`, `*_KEY` | Pooled `requests.Session` (`HTTP_POOL_SIZE=32`). Auth modes: `xsiam`, `splunk_hec`, `basic`, `none`. Batches up to `1000` events / `1 MiB`. | Per-collector circuit breaker (`HTTP_CB_THRESHOLD=3`, `60s` cooldown, `15s` timeout); `401/403/404`/connection error triggers Cribl fallback. |
| **AWS S3** (`s3`) | `S3_BUCKET_NAME`, `AWS_ACCOUNT_ID`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Cached `boto3` client; merges events into gzipped `{"Records":[...]}` CloudTrail files under `AWSLogs/...json.gz` via `s3-batch-flusher` (4s idle / 30s age / 500 events). | 3 retries (`0.5s * attempt`); `AccessDenied`/`NoSuchBucket`/auth errors trigger Cribl fallback. |
| **GCP Pub/Sub** (`pubsub`) | `GCP_PROJECT_ID`, `GCP_PUBSUB_TOPIC`, `GCP_SERVICE_ACCOUNT_KEY_JSON` or `GOOGLE_APPLICATION_CREDENTIALS` | Synchronous per-event JSON `publish()` (`future.result(timeout=10)`). | Hard auth/topic errors trigger Cribl fallback. |
| **Windows WEC** (`wec`) | `WEC_BROKER_URL`, `WEC_PFX_PATH`, `WEC_PFX_PASSWORD` | `modules/wec_transport.py:WecClient` renders `<Event>` XML into WS-Management SOAP CDATA batches over mutual TLS (`requests-pkcs12`), flushed via `ThreadPoolExecutor` (`4` threads, `1000ms` timer). | 3 retries (exponential backoff), circuit breaker, backpressure at `wec_max_pending=10000`, Cribl XML fallback (`_wec_to_cribl`). |
| **XSIAM Cribl Receiver** (`cribl`) | `CRIBL_COLLECTOR_URL`, `CRIBL_TOKEN` | `integrations/cribl_direct.py`: `POST` gzipped NDJSON (`{"data": ..., "collector_ms": ...}`) with `Bearer` auth, `Source-Identifier` UUID, `Integration-Identifier`, and optional `Vendor`/`Product` headers for `GENERIC_UUID`. | Primary pipe for all 9 Entra/Azure/O365 feeds + universal fallback sink. Supports zero-record `probe()` health checks. |

---

## 2. Automatic Cribl Fallback (`integrations/transport.py`)

* **Resolution (`resolve(module, config)`)**:
  1. Determines preferred transport from `config[CONFIG_KEY]["transport"]` (`"auto"` -> `module.NATIVE_TRANSPORT` -> `"syslog"`).
  2. Checks `native_ready()` (verifies required env vars/libs exist) and checks `_down` table.
  3. If `cribl_fallback: true` (default) and `CRIBL_COLLECTOR_URL` + `CRIBL_TOKEN` are set, any unconfigured or failed native pipe automatically routes to `"cribl"` for `transport_retry_s` (`300s`) before retrying native delivery.
* **Payload Reshaping (`to_cribl_records()` & `group_records()`)**:
  * Unpacks gzipped S3 CloudTrail `Records` arrays into individual JSON events.
  * Calls `module.cribl_record()` (`windows_events.py` emits XML).
  * Extracts CEF `(vendor, product)` headers for `GENERIC_UUID` (`af01292940d7426594d3d3e55ae17ee0`) routing.
  * Honors per-record `__cribl_route__` overrides (e.g., Azure AD Sign-ins Event Hub copies).
  * `cribl_direct.CATALOG` registers **45 dedicated Cortex dataset UUIDs** plus `GENERIC_UUID`.

---

## 3. XSIAM API, Correlation Lifecycle & Automation (`integrations/`)

| File | Responsibility |
|---|---|
| `xsiam_client.py` | Standard-auth XSIAM Public API client (`XSIAM_API_BASE`, `XSIAM_API_KEY_ID`, `XSIAM_API_KEY`) with 4-attempt TLS retry. Supports `xql_query()`, `count_events()`, `count_windows_events()`, `get_alerts()`, `wait_for_alert()`, `get/insert/delete_correlation_rule()`, and `get_open_incidents()`/`resolve_incident()`. |
| `tenant_health.py` | Queries `dataset = alerts \| filter alert_domain = "DOMAIN_HEALTH"` to report parsing/correlation errors, silent collectors, and Broker VM health (`python -m integrations.tenant_health`). |
| `correlation_rules_sync.py` | Audits drift between `XSIAM imports/` and the live XSIAM tenant; `--write` pulls tenant updates and refreshes `rule_ids.json`. |
| `correlation_rules_deploy.py` | Pushes drifted repo correlation rules back to XSIAM in-place using `rule_id` (`--apply`). |
| `correlation_rules_reload.py` | Delete-and-recreate recovery utility with resumable checkpoint ledger (`reload_ledger_*.json`) to unwedge XSIAM correlation schedulers. |
| `esxi_correlation_rules.py` | Generates, XQL-validates (`--check`), and deploys (`--apply`) the 19 custom VMware ESXi correlation rules (`XSIAM imports/esxi_*.json`). |
| `mcp_server.py` | FastMCP stdio server exposing **20 MCP tools** over HTTP to the dashboard's `/api/v1/*` API (`LOGSIM_API_URL`, `LOGSIM_API_KEY`). |
| `openapi.yaml` | Authoritative OpenAPI 3.0.3 contract for `/api/v1/*`. |
| `gen_postman_collection.py` & `logsim.postman_collection.json` | Generates and ships a Postman v2.1 collection from `openapi.yaml`. |
| `README.md` & `requirements.txt` | Integration docs and optional `mcp`/`requests` dependencies. |
