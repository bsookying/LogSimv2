---
type: Architecture Component
title: Fork Customizations & Upstream Delta
description: Tracks the exact divergence between `bsookying/LogSimv2` and `phreezone/LogSimv2`, including the native Settings UI v4 integration and upstream sync status.
resource: dashboard/app.py
tags: [fork, upstream, settings-ui, git]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:40:00Z
---

# Fork Customizations & Upstream Delta

## 1. Git Topology

* **`origin`**: `https://github.com/bsookying/LogSimv2.git`
* **`upstream`**: `https://github.com/phreezone/LogSimv2.git` (`upstream/main` = `3c27a12`, incl. tag `v2.8`)
* **Sync Status**: **`upstream/main` (`3c27a12`) is fully merged** into local `main` (zero conflicts), bringing in all 52 upstream commits:
  * XDR Attack closed-loop detection scorecard, Re-score, coverage/ledger APIs, clickable Cortex console links (`XSIAM_CONSOLE_URL`), WildFire/behaviour stages, and YAML stories (`PyYAML>=6.0`).
  * Syslog Broker port-probe Cribl fallback (`c707c60`).
  * Expanded 5,000-user synthetic estate (`config.json`), Zscaler NSS templates (`v2.8`), `docs/xsiam-byok-knowledge.md`, and `docs/modules/xdr-two-agent-lateral-design.md`.
  * Upstream removal of `MICROSOFT_DETECTION_CATALOG.md`.

---

## 2. Native Fork Customization: Dashboard Settings UI (v4 + Polish)

Previously, the Settings UI lived in three standalone `/opt/logsim` patch scripts (`patch_settings_final.py`, `patch_settings_v3.py`, `patch_settings_v4.py`). Those scripts have been **retired** and Settings UI v4 is now integrated natively into `dashboard/app.py` and `dashboard/templates/index.html` so local dev, Docker/Compose, and systemd `/opt/logsim` deployments all ship the exact same UI:

* **Backend (`dashboard/app.py`)**:
  * Registers 4 routes + `/api/v1/*` aliases via `_register_v1_aliases()`: `GET /api/settings`, `POST /api/settings`, `POST /api/settings/generate-key`, `POST /api/settings/test-broker`.
  * Single source of truth `_ST_SOURCES` covering **41 managed `.env` keys** (`LOGSIM_API_KEY`, `SYSLOG_HOST`, plus **10 Data Source Integration cards**: `http`, `okta`, `proofpoint`, `cribl`, `wec`, `winhttp`, `aws`, `gcp`, `xdr`, `xsiamapi` — updated to include upstream's `XSIAM_CONSOLE_URL`).
  * Typed validation (`text`, `url`, `host`, `port`, `choice` — including `choice` dropdowns for `OKTA_AUTH_TYPE` and `PROOFPOINT_AUTH_TYPE`), `16 KB` cap for inline GCP service-account JSON, `403` write block when `_API_KEY` is unset (while keeping `generate-key` open for initial bootstrap), atomic `0o600` `.env` writer, and multi-port syslog TCP probe across all configured ports in `config.json`.
* **Frontend (`dashboard/templates/index.html`)**:
  * Stretched `<nav class="tab-nav">` with far-right **`⚙ Settings`** tab (`#tab-settings`).
  * **LogSim API Key** card (`Show`/`Hide`, `Generate New`, `Delete`) with accurate restart helper copy.
  * **Broker VM — Syslog Host** card (Edit/Delete + multi-port `Test Connection`).
  * **Data Source Integrations** accordion with 3-state status badges (`Configured`, `Partial (X/Y)`, `Not configured`), `.env.example` placeholder detection, diff-only save + reload, environment-agnostic restart instructions (`sudo systemctl restart logsim` or `docker compose restart`), and debounced banner timeout (`clearTimeout(_settingsBannerTimer)`).
