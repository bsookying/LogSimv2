---
type: Architecture Component
title: Fork Customizations & Upstream Delta
description: Tracks the exact divergence between `bsookying/LogSimv2` and `phreezone/LogSimv2`, including the Settings UI v3/v4 patch scripts and upstream drift.
resource: patch_settings_v4.py
tags: [fork, upstream, settings-ui, patch-scripts, git]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Fork Customizations & Upstream Delta

## 1. Git Topology

* **`origin`**: `https://github.com/bsookying/LogSimv2.git` (`HEAD` = `7ddd64b` on `main`)
* **`upstream`**: `https://github.com/phreezone/LogSimv2.git` (`upstream/main` = `3c27a12`)
* **Merge Base**: `cec0e22850dd6b4ded8c9edde3174709f4f5adaa` (*Merge `feature/panw-ngfw` into `main`*)

> [!IMPORTANT]
> All core application files (`log_simulator.py`, `dashboard/app.py`, `dashboard/templates/index.html`, `config.json`, `modules/*`, `integrations/*`) in `HEAD` are **byte-for-byte identical** to merge base `cec0e22`. The 6 fork commits add **only** three standalone patcher scripts at the repository root.

---

## 2. Fork Commits (`cec0e22..7ddd64b`)

| Commit | Summary | File(s) |
|---|---|---|
| `6f44482` | Initial upload of frontend-only Settings UI patch | `patch_settings_final.py` |
| `6d3464b` | Added Data Source Integrations accordion, far-right Settings tab, `LogSim API Key` label | `patch_settings_final.py` |
| `04bd1f7` | Refuse to run on an already-patched `index.html` | `patch_settings_final.py` |
| `881698a` | Insert Settings `<button>` after Bad User `</button>` and stretch nav | `patch_settings_final.py` |
| `73dbc8b` | Settings UI v3: full backend + frontend patch fixing defects D1–D7 | `patch_settings_v3.py` |
| `7ddd64b` | Settings UI v4: backend-driven schema covering all 10 data sources (40 `.env` keys) | `patch_settings_v4.py` |

---

## 3. Standalone Settings UI Patch Scripts (`/opt/logsim`)

All three scripts hardcode `BASE = Path('/opt/logsim')` to patch an already-deployed Linux/systemd installation in place and abort if the target files are already patched:

1. **`patch_settings_final.py` (454 lines — Deprecated / Frontend-only)**:
   * Patches `dashboard/templates/index.html` only with 5 hardcoded integration cards (`http`, `okta`, `proofpoint`, `cribl`, `wec`). Assumed backend `/api/settings*` endpoints existed separately.
2. **`patch_settings_v3.py` (705 lines — Backend + Frontend, fixes D1–D7)**:
   * **D1**: Injects backend routes *before* `_register_v1_aliases()` in `dashboard/app.py` so both `/api/settings*` and `/api/v1/settings*` are registered (`GET/POST /api/settings`, `POST /api/settings/generate-key`, `POST /api/settings/test-broker`).
   * **D2**: Empty string `""` deletes/clears a `.env` key; `••••••••` (`_ST_MASK`) preserves existing secret values; `LOGSIM_API_KEY` is returned unmasked for the `Show` toggle.
   * **D3/D4**: Rejects `POST /api/settings` with `403` when `_API_KEY` is unset (requiring `generate-key` bootstrap + restart first); replaces misleading auto-restart copy with `sudo systemctl restart logsim`.
   * **D5**: Input validation (`_st_validate`) rejects non-strings, `\r\n\x00`, oversized values, invalid `SYSLOG_HOST`, and non-`http(s)://` URLs.
   * **D6**: `api_settings_test_broker()` TCP-probes **all** distinct syslog ports configured in `CONFIG` (not just `514`).
   * **D7**: Atomic `.env` writer (`tempfile.mkstemp` + `os.chmod` + `os.replace`, `0o600` on new file) + in-memory `compile()` check before modifying `app.py`.
3. **`patch_settings_v4.py` (804 lines — Current Latest)**:
   * Keeps all v3 fixes (D1–D7), raises value length cap to `16384` (for inline GCP service-account JSON), and moves the schema to `_ST_SOURCES` in `app.py` (`GET /api/settings` returns `{values, sources, mask}`).
   * Manages **40 `.env` keys** (`LOGSIM_API_KEY`, `SYSLOG_HOST`, plus **10 Data Source Integration cards**: `http`, `okta`, `proofpoint`, `cribl`, `wec`, `winhttp`, `aws`, `gcp`, `xdr`, `xsiamapi`).
   * Adds typed field validation (`text`, `url`, `host`, `port`, `path`, `choice` dropdowns), placeholder detection (`<your-...>` / `/path/to/...` treated as unconfigured), diff-only `dsSave()`, and automatic `loadSettings()` reload after save/delete.

---

## 4. Upstream Drift (`cec0e22..upstream/main`)

`upstream/main` (`3c27a12`) is **52 commits ahead** of this fork's merge base (`cec0e22`), including release tag `v2.8`:
* Syslog port-probe Cribl fallback (`4277908`).
* Expanded 5,000-user synthetic estate (`3c99074`).
* Zscaler NSS feed templates (`f8cd33f` / `v2.8`).
* Removal of estate generator & Microsoft detection catalog from public upstream + BYOK documentation (`3c27a12`).

**Architectural Recommendation for Next Work**: Before adding new UI or engine features, decide whether to (a) merge `patch_settings_v4.py` natively into `dashboard/app.py` and `dashboard/templates/index.html` (making it work identically in local, Docker, and `/opt/logsim` environments), and (b) sync selected or all upstream commits from `phreezone/LogSimv2`.
