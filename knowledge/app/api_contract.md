---
type: API Contract
title: HTTP API & MCP Control Contract
description: Documents every `/api/*` and `/api/v1/*` endpoint in `dashboard/app.py`, `LOGSIM_API_KEY` authentication, OpenAPI/Postman specs, and the 20-tool FastMCP server.
resource: dashboard/app.py
tags: [api, rest, openapi, auth, mcp, flask]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# HTTP API & MCP Control Contract

All HTTP endpoints live in `dashboard/app.py` (Flask, `threaded=True`, default `0.0.0.0:5000`). `log_simulator.py` defines no HTTP routes itself and spawns `dashboard/app.py` as a watched child process.

---

## 1. Authentication (`dashboard/app.py:217–245`)

* **Key Source**: `_API_KEY = (os.getenv("LOGSIM_API_KEY") or CONFIG.get("dashboard_api_key") or "").strip()`.
* **Zero-Config Default**: When `_API_KEY` is empty, authentication is disabled and all routes are open.
* **When Enabled**: `@app.before_request` (`_require_api_key`) protects every `/api/*` route except `/`, `/favicon.ico`, `/api/health`, and `/static/*`.
* **Accepted Headers**: `X-API-Key: <token>` or `Authorization: Bearer <token>` (`401` on mismatch/missing).

---

## 2. Registered Endpoints (`dashboard/app.py`)

At startup, `_register_v1_aliases()` (`dashboard/app.py:3269–3319`) registers versioned `/api/v1/...` aliases for the external automation contract (noted in the **v1?** column below).

### Modules & Telemetry
| Method & Path | v1? | Description / Body |
|---|---|---|
| `GET /` | No | Serves `dashboard/templates/index.html` (`Cache-Control: no-store`). |
| `GET /api/modules` | Yes | Lists all `DASHBOARD_MODULE` module states, metrics, and on-demand threat counts. |
| `GET /api/threat_levels` | Yes | Returns available threat level names and cooldown definitions. |
| `POST /api/modules/<name>/start` | Yes | Body `{threat_level?, event_interval?}`; `409` if already running or training active. |
| `POST /api/modules/<name>/stop` | Yes | Stops a running module worker thread. |
| `POST /api/modules/start_all` | Yes | Starts all dashboard modules (`409` if training active). |
| `POST /api/modules/stop_all` | Yes | Stops all dashboard modules. |
| `POST /api/modules/<name>/reset` | Yes | Resets metrics counters for one module. |
| `POST /api/reset_all` | Yes* | Resets all module counters (*v1 path: `POST /api/v1/modules/reset_all`). |
| `PATCH /api/modules/<name>/interval` | Yes | Live-updates `{event_interval}` (floor `0.0001`s) without restart. |
| `PATCH /api/modules/<name>/threat_level` | Yes | Live-updates `{threat_level}` without restart. |
| `GET /api/modules/<name>/threats` | Yes | Lists analytic-capable on-demand threats (`{module, threats, options}`). |
| `POST /api/modules/<name>/fire` | Yes | Body `{event}`; fires one analytic threat (synchronously flushes WEC tail batch). |
| `GET /api/timeline` | Yes | 120s rolling timeline (`60 × 2s` buckets per module with threat annotations). |
| `GET /api/metrics` | Yes | Global summary KPIs + `per_module` metrics table. |

### Scenarios, Campaigns & XDR Attack Orchestration
| Method & Path | v1? | Description / Body |
|---|---|---|
| `GET /api/scenarios` | Yes | Lists Scenarios `1–23` + `21` Identity Threat Campaigns. |
| `POST /api/scenarios/<scenario_id>/run` | Yes | Async launch; returns `202` + `run_id`. |
| `GET /api/scenarios/runs` | Yes | Lists bounded recent scenario runs (`_RUNS_MAX = 200`). |
| `GET /api/scenarios/runs/<run_id>` | Yes | Status and `RunCapture` manifest for a specific run. |
| `GET, POST /api/campaigns/random` | Yes | Toggles background Poisson Identity Threat Campaigns (`{enabled: bool}`). |
| `GET /api/attack/health` | Yes | WinRM & XSIAM preflight readiness check + target workstation identity. |
| `GET /api/attack/stories` | Yes | Lists the 6 XDR Atomic Red Team stories (`24–29`). |
| `POST /api/attack/run` | Yes | Async launch (`202` + `run_id`); supports `story_id`, `dry_run`, `cleanup_prior_incidents`, `only_steps`, `skip_steps`, `pace`, `domain_override`, `anchor_dhcp`, `anchor_logon`. |
| `GET /api/attack/runs/<run_id>` | Yes | Per-step execution status, detection scorecard, and synthetic event count. |
| `POST /api/attack/runs/<run_id>/rescore` | Yes | Re-pulls XSIAM alerts/incidents for a completed run without re-firing. |
| `GET /api/attack/coverage` | Yes | Returns XDR technique detection coverage summary. |
| `GET /api/attack/ledger` | Yes | Returns persisted XDR attack run ledger. |
| `GET /api/attack/kickstarter` | Yes | Generates downloadable `logsim-kickstarter.ps1` (`?console_ip=&console_url=`). |
| `GET /api/attack/kickstarter/manifest` | Yes | Returns workstation kickstarter payload manifest. |
| `POST /api/attack/register` | Yes | Registers a workstation after kickstarter completion. |
| `GET /api/attack/register` | No | Reads current workstation registration metadata. |

### Bad User, Health, Training & Scheduler
| Method & Path | v1? | Description / Body |
|---|---|---|
| `GET /api/baduser/users` | Yes | Lists eligible users/departments from `config.json` with OS/AWS flags. |
| `GET /api/baduser/playbooks` | Yes | Lists the 7 Bad User playbooks and per-step skip eligibility. |
| `POST /api/baduser/start` | Yes | Body `{username, duration_minutes?, threat_level?, event_interval?, selected_modules?, playbook?}`. |
| `POST /api/baduser/stop` | Yes | Stops active Bad User session. |
| `GET /api/baduser/status` | Yes | Active target, countdown, step tracker, and per-module stats. |
| `GET /api/health` | Yes | Auth-exempt diagnostic report (`?refresh=1` bypasses 60s cache). |
| `GET /api/health/alerts` | Yes | Returns and drains pending health state-transition alerts. |
| `GET /api/training/packs` | No | Lists the 6 deterministic 4-hour training packs. |
| `GET /api/training/status` | No | Current bulk/stream training progress. |
| `POST /api/training/bulk` | No | Body `{pack, num_students?, seed?}`; runs `freezegun` historical backfill. |
| `POST /api/training/stream` | No | Body `{pack, confirm?, num_students?, seed?}`; returns `409 needs_confirm` if no bulk ran today. |
| `POST /api/training/stop` | No | Stops active training run. |
| `GET /api/schedule` | No | Lists pending and last-20 finished scheduled jobs. |
| `POST /api/schedule` | No | Creates scheduled job (`{type, params?, label?, run_at \| delay_seconds}`). |
| `DELETE /api/schedule/<job_id>` / `DELETE /api/schedule` | No | Cancels one job or clears all pending jobs. |

### Settings API (Native in `dashboard/app.py` — registered on `/api/*` & `/api/v1/*`)
| Method & Path | v1? | Description / Body |
|---|---|---|
| `GET /api/settings` | Yes | Returns `{values, sources, mask}` for all 41 managed `.env` keys (secrets masked as `••••••••`; `LOGSIM_API_KEY` unmasked). |
| `POST /api/settings` | Yes | Validates (`host`, `url`, `port`, `choice`, 16 KB cap) and atomically writes `.env` (`403` when `_API_KEY` is unset). |
| `POST /api/settings/generate-key` | Yes | Generates a 64-hex `LOGSIM_API_KEY` into `.env` (`0o600`); open when unconfigured to bootstrap auth. |
| `POST /api/settings/test-broker` | Yes | Body `{host?}`; TCP-probes every distinct syslog port configured across `config.json`. |

---

## 3. OpenAPI, Postman & MCP Automation (`integrations/`)

* **`integrations/openapi.yaml`**: OpenAPI 3.0.3 spec for the `/api/v1/*` surface.
* **`integrations/logsim.postman_collection.json`**: Postman v2.1 collection generated via `integrations/gen_postman_collection.py`.
* **`integrations/mcp_server.py`**: FastMCP stdio server exposing **20 MCP tools** calling `/api/v1/*` via `LOGSIM_API_URL` and `LOGSIM_API_KEY` (see `integrations/README.md`).
