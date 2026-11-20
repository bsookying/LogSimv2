---
type: Architecture Component
title: Web Dashboard UI
description: Describes the Flask dark-themed SPA (`dashboard/templates/index.html`), its 6 built-in tabs, live polling, and the Settings UI v4 patch design.
resource: dashboard/templates/index.html
tags: [dashboard, flask, spa, ui, chartjs, settings-ui]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Web Dashboard UI

The web interface is served by `dashboard/app.py` (`GET /`) as a single-file dark-themed vanilla-JS SPA (`dashboard/templates/index.html`, 2,452 lines) with inline CSS and Chart.js 4 from CDN.

---

## 1. Global Header, Banner & Polling Mechanics

* **Top Control Bar**: Logo (`LogSim Dashboard`), `<nav class="tab-nav">` (6 tabs in base repo), live timestamp (`#live-ts`), global threat-level selector (`#global-level-select`), global logarithmic event-rate slider (`#global-rate-slider`, `0–100` mapped via `10^(pos/20 - 1)` from `0.1/s` to `10k/s`), `Start All`, and `Stop All`.
* **Sticky Bad User Banner (`#baduser-banner`)**: Visible across all tabs while Bad User mode is running, displaying target user, department, and remaining countdown.
* **Live Polling Loop (`poll()`)**:
  * Polls `/api/metrics`, `/api/timeline`, and `/api/baduser/status` in parallel every **`2000ms`** (`10000ms` when `document.hidden`).
  * Separate **`10000ms`** timer polls `/api/health/alerts` and raises browser `Notification` popups on health state transitions.
* **API Key Attachment (Browser Option B)**: `GET /` injects `<meta name="logsim-api-key" content="{{ api_key }}">` (`Cache-Control: no-store`); the `api()` fetch wrapper reads it and sends `X-API-Key` automatically on every call.

---

## 2. The 7 Built-In Tabs (`dashboard/templates/index.html`)

| Tab | Element ID | Primary Controls & Views |
|---|---|---|
| **⚔ XDR Attack** | `#tab-xdr` | Purple-team WinRM + network orchestration: `Generate workstation installer` (`logsim-kickstarter.ps1`), `Re-check preflight`, PASS/FAIL preflight & discovered target identity, story selector, vendor checkboxes (PAN NGFW default), `Fresh C2 domain`, `Prevention probe`, `Scorecard` + `↻ Re-score` with clickable Cortex console case/alert links (`XSIAM_CONSOLE_URL`), `Dry-run`, `Pace`, `Skip steps`, and polled step results. |
| **Modules** *(default)* | `#tab-modules` | Summary KPIs (`Modules Running`, `Total Logs Sent`, `Rate/s`, `Threats`, `Session Time`), per-module control cards (`DASHBOARD_MODULE = True`) with status badge, rate slider, threat-level `<select>`, Start/Stop, collapsible Threat Breakdown chart, 2-minute rolling Event Timeline (`60 × 2s` buckets with red threat markers), and Live Metrics table with Reset actions. |
| **Threats & Scenarios** | `#tab-threats` | Three sections: (1) **Fire Individual Threat** (`<optgroup>` grouped by target XSIAM analytic), (2) **Run Attack Scenario** (`Random identity campaigns` toggle + 23 scenarios & 21 Identity Threat Campaigns), and (3) **Training Mode** (6 deterministic multi-student packs, `1–50` students, variant seed, 4h Bulk backfill vs 4h Live stream with 409 confirmation gate). |
| **Schedule** | `#tab-schedule` | Create delayed (`In X minutes`) or `Exact time` jobs (`module_start`, `module_stop`, `global_start`, `global_stop`, `scenario`, `rate_change`), plus live 2s-polled queue with `Cancel` and `Clear Pending`. |
| **Health** | `#tab-health` | On-demand (`?refresh=1`) diagnostic view across `.env` vars, Threat Intel (Tor, Tranco, DNS), HTTP collectors, Syslog TCP port probes, AWS S3 (`Put`/`Delete`), GCP Pub/Sub, Cribl empty-batch & per-route UUID probes, WEC parallel workers, delivery queue drops, and XSIAM tenant `DOMAIN_HEALTH` alerts. |
| **Bad User** | `#tab-baduser` | **Config view**: Department & User selector (with OS/AWS warnings), 7 ordered Playbooks showing per-step skip reasons, duration (`1–480` min), threat level, rate slider, and module checkboxes. **Active view**: Target user header, countdown progress bar, live step tracker, per-module counters, and `Stop`. |
| **⚙ Settings** *(far right)* | `#tab-settings` | Native `.env` management UI: **LogSim API Key** (`Show`/`Hide`, `Generate New`, `Delete`), **Broker VM — Syslog Host** (Edit/Delete + multi-port TCP `Test Connection`), and **Data Source Integrations** accordion dynamically rendered from backend `_ST_SOURCES` (**10 cards, 39 keys**, `Configured` / `Partial (X/Y)` / `Not configured` badges, `choice` dropdowns, `.env.example` placeholder detection, diff-only save + reload). |
