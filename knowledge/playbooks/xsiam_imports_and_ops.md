---
type: Playbook
title: XSIAM Imports & Operational Maintenance
description: Guide to the 157 JSON artifacts in `XSIAM imports/`, UI vs API import workflows, rule sync/deploy/reload scripts, and tenant health diagnostics.
resource: XSIAM imports/
tags: [xsiam, correlation-rules, dashboards, operations, health]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# XSIAM Imports & Operational Maintenance

## 1. Artifact Inventory (`XSIAM imports/`)

LogSimv2 relies on **built-in Cortex XSIAM Marketplace content packs** for log parsing and XDM modeling. Accordingly, `XSIAM imports/` contains **0 parsing rules, 0 modeling rules, 0 BIOCs, and 0 SOAR playbooks**. Its **157 JSON files** break down as:

| Category | Count | Contents & Usage |
|---|---|---|
| **Individual Correlation Rules** | `151` | 1-element JSON arrays (`action: "ALERTS"`, `is_enabled: true`): `59` scenario step rules (`01_step*–10_step*`), `19` VMware ESXi rules (`esxi_*.json`), `11` Infoblox rules (`ibx_*.json`), `9` multi-stage scenario rules (`scenario_01_*–10_*`), `43` vendor rules (Proofpoint, Firepower, Zscaler, Apache, Check Point, FortiGate, Okta, ASA, GCP), and `10` standalone rules. `146` are `SCHEDULED` (`*/10 * * * *`) and `5` are `REAL_TIME`. |
| **Correlation Rule Bundle** | `1` | `bundle.json` — single bulk-import array of **`104` rules** (`59` step + `19` ESXi + `11` Infoblox + `9` scenario + `6` standalone ASA rules), all stripped of `rule_id`. The remaining `47` single-rule files (including 5 `(v2)` replacements and vendor exports) are imported individually. |
| **Dashboards** | `2` | `Dashboards/XDR_Dashboard Manager_Apache_Operations.json` and duplicate top-level `Apache - .json` (identical SHA-256) defining the 7-widget **Apache Operations** XQL dashboard (`apache_httpd_raw`). |
| **Tenant Sync & Reload State** | `3` | `tenant_export_2026-11-02.json` (`125`-rule live snapshot), `rule_ids.json` (name -> `rule_id` index), and `reload_ledger_2026-11-02.json` (delete/recreate audit log). |

> [!WARNING]
> **Rule ID Gotcha**: `20` of the `151` individual rule files are direct tenant exports containing a `rule_id` field (whereas `131` files and `bundle.json` omit `rule_id`). In XSIAM, importing a rule JSON that includes a `rule_id` attempts an *in-place update* and fails if the target tenant does not already have that ID. Strip `rule_id` before importing those files into a new tenant.

---

## 2. Manual XSIAM Console Import Workflow

1. **Bulk Correlation Rules**: Navigate to **Detection → Correlation Rules → Import** and upload `XSIAM imports/bundle.json` (`104` rules).
2. **Additive `(v2)` Replacement Rules**: Import the 5 `(v2)` replacement files individually, verify alerts fire on live simulated traffic, then disable/delete the legacy originals.
3. **Apache Operations Dashboard**: Navigate to **Dashboards & Reports → Dashboard Manager → Import** and upload `XSIAM imports/Dashboards/XDR_Dashboard Manager_Apache_Operations.json`.

---

## 3. Programmatic XSIAM API Operations (`integrations/`)

Requires `XSIAM_API_BASE`, `XSIAM_API_KEY_ID`, and `XSIAM_API_KEY` in `.env`:

* **Check Tenant Health (`DOMAIN_HEALTH` alerts)**:
  ```bash
  python -m integrations.tenant_health
  ```
  Surfaces LogSim parsing-rule errors, correlation-rule errors, silent LogSim collectors, and Broker VM alerts. Also polled automatically every `900s` (`TENANT_HEALTH_REFRESH_S`) by the dashboard's **Health** tab.
* **Audit & Pull Live Correlation Rule Drift**:
  ```bash
  python -m integrations.correlation_rules_sync           # dry-run drift check
  python -m integrations.correlation_rules_sync --write   # pull live tenant edits into XSIAM imports/ & rule_ids.json
  ```
* **Deploy Drifted Repo Rules Back to XSIAM**:
  ```bash
  python -m integrations.correlation_rules_deploy --apply
  ```
* **Generate, Validate & Deploy ESXi Correlation Rules**:
  ```bash
  python -m integrations.esxi_correlation_rules --check   # validate XQL against live data
  python -m integrations.esxi_correlation_rules --apply   # create/update in tenant
  ```
* **Recover Wedged XSIAM Correlation Schedulers**:
  `integrations/correlation_rules_reload.py` deletes and recreates rules from a `tenant_export_*.json` snapshot while checkpointing each rule's `old_id` / `new_id` into `reload_ledger_*.json` so interrupted runs can resume safely.
