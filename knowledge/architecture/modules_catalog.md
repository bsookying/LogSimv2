---
type: Architecture Component
title: Generator Modules & Plugin Catalog
description: Inventories all 25 auto-discovered log generators, 23 shared helper/engine modules, the `xdr_orchestration` purple-team subpackage, and the module plugin contract.
resource: modules/
tags: [modules, plugins, generators, threats, xdr-orchestration, ueba]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Generator Modules & Plugin Catalog

The `modules/` directory contains **54 Python files**:
* **25 auto-discovered generator modules** (top-level `modules/*.py` exporting `NAME`)
* **23 top-level helper, catalog, and engine modules** (no `NAME`, ignored by `load_modules()`)
* **6 files in `modules/xdr_orchestration/`** (subpackage invoked via scenarios `24–29` and `/api/attack/*`)

Collectively, the generators produce **954 named threats** (**481 analytic-capable on-demand threats**) plus **21 cross-feed identity threat campaigns**.

---

## 1. Module Plugin Contract

`load_modules()` (`log_simulator.py:132–161`) imports every top-level `modules/*.py` file and registers any module defining `NAME`.

| Attribute / Hook | Required? | Purpose |
|---|---|---|
| `NAME`, `DESCRIPTION` | Required | Display name and description used by CLI and dashboard. |
| `CONFIG_KEY` | Standard | Key inside `config.json` (e.g., `panw_ngfw_config`, `aws_config`). |
| `NATIVE_TRANSPORT` | Optional | Defaults to `"syslog"`; overridden by `config[CONFIG_KEY]["transport"]`. |
| `SOURCE_IDENTIFIER` | Standard | Cribl catalog UUID or `GENERIC_UUID` (`af01292940d7426594d3d3e55ae17ee0`). |
| `XSIAM_VENDOR`, `XSIAM_PRODUCT` | When `GENERIC_UUID` | Headers sent to Cribl generic receiver for XSIAM dataset routing. |
| `DASHBOARD_MODULE` | Optional (`True`) | Set `False` (used by `azuread_campaigns.py`) to hide from continuous dashboard cards. |
| `generate_log(...)` | Required | Accepts `(config, scenario, threat_level, benign_only, context, scenario_event)`; returns `None`, payload, or `(payload, event_name)`. |
| `get_threat_names()` + `get_threat_info()` or `ANALYTIC_ALERTS` | Standard | Drives `modules/threat_catalog.py` to expose only analytic-backed threats on demand. |
| `cribl_record(payload)` | Optional | Custom reshape hook for Cribl fallback (used by `windows_events.py` to emit `<Event>` XML). |
| `reset_state()` | Optional | Resets internal counters/caches for deterministic Training runs (`infoblox_dns.py`, `windows_events.py`). |

---

## 2. Auto-Discovered Generator Modules (25)

### Network, Firewall, Proxy, DNS & Web (9 modules)
| File | `NAME` | Native Pipe / Port | Format | Notes |
|---|---|---|---|---|
| `cisco_asa.py` | `Cisco ASA Firewall` | `syslog` (`1514`) | Raw `%ASA-...` syslog | Shared `mgmt_plane.py` support |
| `cisco_firepower.py` | `Cisco Firepower` | `syslog` (`514`) | CEF + `%FTD-...` mgmt syslog | IPS, malware, connection events |
| `checkpoint_firewall.py` | `Check Point Firewall` | `syslog` (`514`) | CEF (`VPN-1 & FireWall-1`) | URL filtering, Identity Awareness |
| `fortinet_fortigate.py` | `Fortinet FortiGate` | `syslog` (`514`) | CEF (`Fortinet\|Fortigate`) | Verified CEF-to-XDM map |
| `panw_ngfw.py` | `Palo Alto Networks NGFW` | `syslog` (`514`) | CEF (`PANW\|NGFW_CEF`) | Aligned to PA-440 / PAN-OS `12.2.4-h1`, zones, 220+ signatures |
| `panw_ngfw_vulns.py` | `Palo Alto Networks NGFW Vulnerabilities` | `syslog` (`514`) | CEF threat syslog | On-demand only (`None` in continuous mode); 235 vulnerability signatures |
| `zscaler.py` | `Zscaler Web Gateway` | `syslog` (`514`) | CEF (NSS Weblog + NSS Firewall) | Web proxy + cloud firewall |
| `infoblox_dns.py` | `Infoblox NIOS` | `syslog` (`1516`) | Raw `named`/DHCPD/Audit + CEF RPZ | Authoritative answers synced via `resolver.py` |
| `httpd.py` | `Apache httpd` | `syslog` (`1515`) | Combined access + error syslog | Paired with Apache Operations XSIAM dashboard |

### Endpoint & Hypervisor (2 modules)
| File | `NAME` | Native Pipe | Format | Cribl Dataset |
|---|---|---|---|---|
| `windows_events.py` | `Windows Event Log` | `wec` (mTLS `5986`; `http` opt.) | Internal NXLog JSON -> `<Event>` XML | `microsoft_windows_raw` (`63b0fbeb...`) |
| `vmware_esxi.py` | `VMware ESXi` | `syslog` (`1518`) | ESXi `hostd`/`sshd`/`shell`/`vpxa` syslog | `GENERIC_UUID` (`VMware` / `ESXi`) |

### Cloud Infrastructure (3 modules)
| File | `NAME` | Native Pipe | Format | Cribl Dataset |
|---|---|---|---|---|
| `aws.py` | `aws` | `s3` | Gzipped CloudTrail `{"Records":[...]}` | `amazon_aws_raw` (`c19f87b6...`) |
| `gcp.py` | `Google Cloud Compute` | `pubsub` | GCP Cloud Logging `LogEntry` JSON | `google_cloud_logging_raw` (`00a8322c...`) |
| `azure_activity.py` | `Azure Activity` | `cribl` | Azure Monitor ARM + Storage/KV/AI + AKS `kube-audit` | `msft_azure_raw` (`fce13a1d...`) |

### Identity, SSO & Email Security (2 modules)
| File | `NAME` | Native Pipe | Format | Cribl Dataset |
|---|---|---|---|---|
| `okta_sso.py` | `Okta SSO` | `http` | Okta System Log JSON | `okta_sso_raw` (`5faf4c1f...`) |
| `proofpoint_email.py` | `Proofpoint Email Gateway` | `http` | Proofpoint TAP JSON (message & click) | `proofpoint_tap_raw` (`3eefce0f...`) |

### Microsoft Entra ID & M365 Workloads (8 modules — all native `cribl`)
| File | `NAME` | Format | Cribl Dataset (`UUID`) |
|---|---|---|---|
| `azuread_signin.py` | `Azure AD Sign-ins` | Graph `auditLogs/signIns` (+ Event Hub copy) | `msft_azure_ad_raw` (`f56dcfdf...`) |
| `azuread_audit.py` | `Azure AD Audit` | Graph `auditLogs/directoryAudits` | `msft_azure_ad_audit_raw` (`0e076d5a...`) |
| `azuread_identity_protection.py` | `Azure AD Identity Protection` | `ProvisioningLogs`, `RiskyUsers`, `UserRiskEvents` | `msft_azure_raw` (`fce13a1d...`) |
| `o365_azuread.py` | `Office 365 Azure AD` | `Audit.AzureActiveDirectory` (RT 8, 15) | `msft_o365_azure_ad_raw` (`e1f109f8...`) |
| `o365_exchange.py` | `Office 365 Exchange Online` | Exchange Workload (RT 1, 2, 50) | `msft_o365_exchange_online_raw` (`dee8e85c...`) |
| `o365_sharepoint.py` | `Office 365 SharePoint Online` | SharePoint/OneDrive (RT 6, 14) | `msft_o365_sharepoint_online_raw` (`3a37f519...`) |
| `o365_dlp.py` | `Office 365 DLP` | `Audit.DLP` (RT 11, 13) | `msft_o365_dlp_raw` (`8f052782...`) |
| `o365_general.py` | `Office 365 General` | Copilot (RT 261), Power BI (RT 20) | `msft_o365_general_raw` (`c7655e83...`) |

### Cross-Feed Coordinator (1 module)
* **`azuread_campaigns.py` (`Identity Threat Campaigns`)**: `DASHBOARD_MODULE = False`. Drives 21 multi-stage identity kill chains (`azuread_threat_sequences.py`), self-emitting across Entra/O365 (Cribl) and Windows (WEC/Cribl).

---

## 3. Shared Helpers, Catalogs & Engines (23 files)

* **Microsoft / Azure Helpers (8)**: `aks_audit.py`, `azure_activity_catalog.py`, `azure_audit_catalog.py` (382 directory audit ops), `azure_common.py` (`ThreatGate` Poisson scheduler + stable SHA-256 GUIDs), `azure_dataplane.py`, `azure_estate.py`, `graph_activity.py`, `azuread_threat_sequences.py` (21 kill chains).
* **Bad User & Training Engines (3)**: `bad_user_playbooks.py` (7 playbooks: `phish_to_exfil`, `insider_data_theft`, `cloud_admin_abuse`, `ransomware_precursor`, `mailbox_takeover`, `recon_and_discovery`, `endpoint_beaconing`), `bad_user_policy.py` (benign/threat allow-lists), `training_engine.py` (`freezegun` seeded bulk backfill + live stream + multi-student replay).
* **Identity, Network & High-Cardinality Composers (9)**: `session_utils.py` (user/device/IP affinity & `focus_user`), `resolver.py` (shared DNS table), `domain_corpus.py` (Tranco long-tail benign domains), `threat_domains.py` (preserves 9 correlation-rule family tokens), `threat_files.py` (strict extension-to-MIME), `cloud_ids.py` (unbounded AWS/GCP IDs), `user_agents.py`, `mgmt_plane.py`, `tor_enrichment.py` (Onionoo).
* **Transport & Catalog Plumbing (3)**: `wec_transport.py` (`WecClient` WS-Man mTLS SOAP batching), `deferred.py` (`DeferredDict`/`DeferredStr`), `threat_catalog.py` (analytic threat filter & canonical alias resolver).

---

## 4. `modules/xdr_orchestration/` Purple-Team Subpackage (6 files)

Executes real **Atomic Red Team** techniques on a live Cortex XDR Windows workstation over WinRM while simultaneously emitting identity-aligned synthetic network/DNS/firewall/proxy logs so XSIAM stitches host + network telemetry into one incident:
* `connection.py` — Fail-closed `WorkstationConnection`, `PreflightReport`, and workstation identity discovery (`username`, `hostname`, `ip`, `egress_ip`) from `XDR_TARGET_*` env vars.
* `executor.py` — `WinRMAtomicExecutor` and `DryRunExecutor`.
* `stories.py` — 6 stories (`reference`/`full`, `quick`, `intrusion`, `lateral`, `persistence`, `fullchain`), wired as Scenarios `24–29`.
* `orchestrator.py` — Optional pre-run resolution of open box incidents via `XsiamClient`, step pacing, and correlated synthetic emission.
* `kickstarter.py` — Renders one-shot PowerShell installer (`logsim-kickstarter.ps1`) served by `GET /api/attack/kickstarter`.
