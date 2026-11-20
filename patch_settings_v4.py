#!/usr/bin/env python3
"""
LogSimv2 Settings UI — v4 (backend + frontend; D1-D7 fixed; all repo data sources).
Requires CLEAN dashboard/app.py and dashboard/templates/index.html (git checkout first).
Run as: sudo -u lab-user python3 patch_settings_v4.py
Nothing is written unless every check passes.
"""
from pathlib import Path

BASE = Path('/opt/logsim')
APP = BASE / 'dashboard' / 'app.py'
f = BASE / 'dashboard' / 'templates' / 'index.html'

app_src = APP.read_text(encoding='utf-8')
src = f.read_text(encoding='utf-8')
assert '</html>' in src, 'index.html appears truncated — restore from git first.'
print(f'Files read: app.py {app_src.count(chr(10))+1} lines, index.html {src.count(chr(10))+1} lines')
if ('api_settings_get' in app_src or 'data-tab="settings"' in src
        or 'tab-settings' in src or '_settingsRawKey' in src):
    raise SystemExit('ABORT: app.py or index.html is already patched. Restore clean files first:\n'
                     '  sudo -u lab-user git -C /opt/logsim checkout -- dashboard/app.py dashboard/templates/index.html\n'
                     'then re-run this script. No changes were made.')

# ── 0. Backend routes — inserted BEFORE _register_v1_aliases() (fixes D1) ─────
ALIAS_MARKER = '# Register the versioned external contract'
assert app_src.count(ALIAS_MARKER) == 1, 'v1 alias marker not found exactly once in app.py'
BACKEND = r'''
# ── Settings UI routes (feature/settings-ui) ──────────────────────────────────
# Manage a small set of .env keys from the dashboard. Changes apply on restart
# (env is read at process start). Gated by the normal /api/* API-key check;
# when NO API key is set, the only write allowed is generate-key (bootstrap).
import re as _st_re
import socket as _st_socket
import secrets as _st_secrets
import tempfile as _st_tempfile
import pathlib as _st_pathlib

_ST_ENV_PATH = _st_pathlib.Path(__file__).resolve().parent.parent / '.env'
_ST_MASK = '•' * 8
_ST_HOST_RE = _st_re.compile(r'^[A-Za-z0-9.\-:\[\]]{1,253}$')


def _st_f(key, label, type='text', secret=False, optional=False, choices=None, hint=''):
    return {'key': key, 'label': label, 'type': type, 'secret': secret,
            'optional': optional, 'choices': choices or [], 'hint': hint}


# Data Source Integrations — mirrors the transport sections of .env.example.
# Single source of truth: the UI renders whatever this list contains.
_ST_SOURCES = [
    {'id': 'http', 'name': 'HTTP Collector',
     'desc': 'XSIAM HTTP Event Collector, used by all HTTP-transport modules.',
     'fields': [_st_f('HTTP_COLLECTOR_URL', 'Collector URL', 'url')]},
    {'id': 'okta', 'name': 'Okta SSO',
     'desc': 'URL and auth type are not needed if the HTTP Collector is set.',
     'fields': [_st_f('OKTA_KEY', 'API Key', secret=True),
                _st_f('OKTA_COLLECTOR_URL', 'Collector URL', 'url', optional=True),
                _st_f('OKTA_AUTH_TYPE', 'Auth Type', optional=True)]},
    {'id': 'proofpoint', 'name': 'Proofpoint Email',
     'desc': 'URL and auth type are not needed if the HTTP Collector is set.',
     'fields': [_st_f('PROOFPOINT_KEY', 'API Key', secret=True),
                _st_f('PROOFPOINT_COLLECTOR_URL', 'Collector URL', 'url', optional=True),
                _st_f('PROOFPOINT_AUTH_TYPE', 'Auth Type', optional=True)]},
    {'id': 'cribl', 'name': 'Cribl Receiver',
     'desc': 'XSIAM integrated Cribl receiver: Microsoft feeds, and the fallback for every other module.',
     'fields': [_st_f('CRIBL_COLLECTOR_URL', 'Collector URL', 'url',
                      hint='Ends in /logs/v1/integrated/cribl/data'),
                _st_f('CRIBL_TOKEN', 'Token', secret=True, hint='LogSim adds the "Bearer " prefix')]},
    {'id': 'wec', 'name': 'Windows Events — WEC',
     'desc': 'WS-Management direct to the Broker VM (default Windows transport). Needs the PFX client cert from XSIAM.',
     'fields': [_st_f('WEC_BROKER_URL', 'Broker URL', 'url', hint='https://<broker>:5986/wsman'),
                _st_f('WEC_PFX_PATH', 'PFX Path', 'path'),
                _st_f('WEC_PFX_PASSWORD', 'PFX Password', secret=True),
                _st_f('WEC_ISSUER_CA', 'Issuer CA Thumbprint', optional=True,
                      hint='Informational only; LogSim does not read it')]},
    {'id': 'winhttp', 'name': 'Windows Events — HTTP',
     'desc': 'Alternative to WEC: set transport "http" in windows_events_config.',
     'fields': [_st_f('WINDOWS_EVENTS_COLLECTOR_URL', 'Collector URL', 'url'),
                _st_f('WINDOWS_EVENTS_KEY', 'Key', secret=True)]},
    {'id': 'aws', 'name': 'AWS CloudTrail (S3)',
     'desc': 'Values come from the CloudFormation stack outputs.',
     'fields': [_st_f('S3_BUCKET_NAME', 'S3 Bucket'),
                _st_f('AWS_ACCOUNT_ID', 'Account ID'),
                _st_f('AWS_REGION', 'Region', optional=True, hint='Default us-east-1'),
                _st_f('AWS_ACCESS_KEY_ID', 'Access Key ID'),
                _st_f('AWS_SECRET_ACCESS_KEY', 'Secret Access Key', secret=True)]},
    {'id': 'gcp', 'name': 'GCP Cloud Audit (Pub/Sub)',
     'desc': 'Use either a key file path (Option A) or the inline service-account JSON (Option B).',
     'fields': [_st_f('GCP_PROJECT_ID', 'Project ID'),
                _st_f('GCP_PROJECT_NUMBER', 'Project Number'),
                _st_f('GCP_PUBSUB_TOPIC', 'Pub/Sub Topic'),
                _st_f('GOOGLE_APPLICATION_CREDENTIALS', 'Key File Path', 'path', optional=True),
                _st_f('GCP_SERVICE_ACCOUNT_KEY_JSON', 'Inline Key JSON', secret=True, optional=True,
                      hint='Single line, no newlines')]},
    {'id': 'xdr', 'name': 'XDR Attack Target (WinRM)',
     'desc': 'Live Windows box with the Cortex XDR agent for real Atomic Red Team techniques.',
     'fields': [_st_f('XDR_TARGET_HOST', 'Target Host', 'host'),
                _st_f('XDR_TARGET_WINRM_USER', 'WinRM User', hint='No DOMAIN\\ prefix for a workgroup box'),
                _st_f('XDR_TARGET_WINRM_PASSWORD', 'WinRM Password', secret=True),
                _st_f('XDR_TARGET_WINRM_PORT', 'WinRM Port', 'port', optional=True, hint='Default 5985'),
                _st_f('XDR_TARGET_WINRM_SCHEME', 'WinRM Scheme', 'choice', optional=True,
                      choices=['http', 'https']),
                _st_f('XDR_TARGET_WINRM_AUTH', 'WinRM Auth', 'choice', optional=True,
                      choices=['ntlm', 'basic', 'kerberos']),
                _st_f('XDR_TARGET_TRANSPORT', 'Transport', 'choice', optional=True,
                      choices=['winrm', 'stub']),
                _st_f('XDR_TARGET_EGRESS_IP', 'Egress IP', 'host', optional=True),
                _st_f('XDR_EMAIL_DOMAIN', 'Email Domain', optional=True)]},
    {'id': 'xsiamapi', 'name': 'XSIAM Public API',
     'desc': 'For XDR orchestration policy control and the validation scripts.',
     'fields': [_st_f('XSIAM_API_BASE', 'API Base URL', 'url'),
                _st_f('XSIAM_API_KEY_ID', 'API Key ID'),
                _st_f('XSIAM_API_KEY', 'API Key', secret=True),
                _st_f('XSIAM_FOREIGN_HOSTS', 'Foreign Hosts', optional=True,
                      hint='Comma-separated real hosts that also feed microsoft_windows_raw')]},
]
# Top-level fields shown in their own cards (not under Data Source Integrations).
# LOGSIM_API_KEY is NOT masked: any caller of this route already holds it (or auth is off).
_ST_FIELDS = {'LOGSIM_API_KEY': _st_f('LOGSIM_API_KEY', 'LogSim API Key'),
              'SYSLOG_HOST': _st_f('SYSLOG_HOST', 'Broker VM Syslog Host', 'host')}
for _st_src in _ST_SOURCES:
    for _st_fd in _st_src['fields']:
        _ST_FIELDS[_st_fd['key']] = _st_fd
_ST_KEYS = list(_ST_FIELDS)
_ST_SECRET = {k for k, fd in _ST_FIELDS.items() if fd['secret']}


def _st_unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        inner = v[1:-1]
        if v[0] == '"':
            inner = _st_re.sub(r'\\(["\\])', r'\1', inner)  # single-pass unescape of \" and \\
        return inner
    return v


def _st_quote(v):
    if v == '' or _st_re.fullmatch(r'[A-Za-z0-9_.:/@%+=,\-]+', v):
        return v
    return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _st_read_env():
    out = {}
    if _ST_ENV_PATH.exists():
        for line in _ST_ENV_PATH.read_text(encoding='utf-8').splitlines():
            s = line.strip()
            if s.startswith('export '):
                s = s[7:].lstrip()
            if s and not s.startswith('#') and '=' in s:
                k, _, v = s.partition('=')
                out[k.strip()] = _st_unquote(v)
    return out


def _st_write_env(updates):
    """Atomic in-place update; creates .env if missing; preserves file mode (D7)."""
    lines = _ST_ENV_PATH.read_text(encoding='utf-8').splitlines() if _ST_ENV_PATH.exists() else []
    written, new_lines = set(), []
    for line in lines:
        s = line.strip()
        bare = s[7:].lstrip() if s.startswith('export ') else s
        if bare and not bare.startswith('#') and '=' in bare:
            k = bare.split('=', 1)[0].strip()
            if k in updates:
                new_lines.append(f'{k}={_st_quote(updates[k])}')
                written.add(k)
                continue
        new_lines.append(line)
    for k, v in updates.items():
        if k not in written:
            new_lines.append(f'{k}={_st_quote(v)}')
    mode = _ST_ENV_PATH.stat().st_mode & 0o777 if _ST_ENV_PATH.exists() else 0o600
    fd, tmp = _st_tempfile.mkstemp(dir=str(_ST_ENV_PATH.parent), prefix='.env.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(new_lines) + '\n')
        os.chmod(tmp, mode)
        os.replace(tmp, _ST_ENV_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _st_validate(k, v):
    """Return an error string, or None if the value is acceptable (D5)."""
    if not isinstance(v, str):
        return f'{k}: value must be a string'
    if any(c in v for c in '\r\n\x00'):
        return f'{k}: line breaks are not allowed'
    if len(v) > 16384:
        return f'{k}: value too long'
    if v == '':
        return None  # empty = clear (D2)
    fd = _ST_FIELDS[k]
    t = fd['type']
    if t == 'host' and not _ST_HOST_RE.match(v):
        return f'{k}: must be an IP address or hostname'
    if t == 'url' and not v.lower().startswith(('http://', 'https://')):
        return f'{k}: must start with http:// or https://'
    if t == 'port' and not (v.isdigit() and 1 <= int(v) <= 65535):
        return f'{k}: must be a port number (1-65535)'
    if t == 'choice' and v not in fd['choices']:
        return f'{k}: must be one of {", ".join(fd["choices"])}'
    return None


def _st_write_blocked():
    if _API_KEY:
        return None  # before_request already verified the caller's key
    return (jsonify({'error': 'No LOGSIM_API_KEY is set, so settings writes are disabled. '
                              'Use Generate New to create a key, restart, then reload.'}), 403)


def api_settings_get():
    env = _st_read_env()
    values = {k: (_ST_MASK if k in _ST_SECRET and env.get(k) else env.get(k, ''))
              for k in _ST_KEYS}
    return jsonify({'values': values, 'sources': _ST_SOURCES, 'mask': _ST_MASK})


def api_settings_post():
    blocked = _st_write_blocked()
    if blocked:
        return blocked
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected a JSON object'}), 400
    updates = {}
    for k, v in data.items():
        if k not in _ST_KEYS:
            return jsonify({'error': f'{k}: not a managed setting'}), 400
        if v == _ST_MASK:
            continue  # unchanged secret placeholder
        v = v.strip() if isinstance(v, str) else v
        err = _st_validate(k, v)
        if err:
            return jsonify({'error': err}), 400
        updates[k] = v
    if not updates:
        return jsonify({'error': 'No changes provided'}), 400
    try:
        _st_write_env(updates)
    except OSError as exc:
        return jsonify({'error': f'Could not write .env: {exc}'}), 500
    return jsonify({'saved': sorted(updates), 'restart_required': True})


def api_settings_generate_key():
    key = _st_secrets.token_hex(32)
    try:
        _st_write_env({'LOGSIM_API_KEY': key})
    except OSError as exc:
        return jsonify({'error': f'Could not write .env: {exc}'}), 500
    return jsonify({'key': key, 'restart_required': True})


def api_settings_test_broker():
    """TCP-probe every syslog port LogSim ships to, like the Health tab (D6)."""
    data = request.get_json(silent=True) or {}
    host = (data.get('host') or os.getenv('SYSLOG_HOST') or '').strip()
    if not host:
        return jsonify({'ok': False, 'message': 'No Broker VM host configured', 'results': []})
    if not _ST_HOST_RE.match(host):
        return jsonify({'ok': False, 'message': 'Invalid host', 'results': []}), 400
    ports = {}
    try:
        gp = int(CONFIG.get('syslog_port', 514) or 514)
    except (TypeError, ValueError):
        gp = 514
    ports.setdefault(gp, []).append('default')
    for ck, cv in CONFIG.items():
        if isinstance(cv, dict) and cv.get('syslog_port'):
            try:
                p = int(cv['syslog_port'])
            except (TypeError, ValueError):
                continue
            ports.setdefault(p, []).append(ck[:-7] if ck.endswith('_config') else ck)
    results = []
    for p in sorted(ports):
        srcs = ', '.join(sorted(ports[p]))
        try:
            with _st_socket.create_connection((host, p), timeout=3):
                pass
            results.append({'port': p, 'ok': True, 'sources': srcs, 'detail': 'reachable'})
        except _st_socket.timeout:
            results.append({'port': p, 'ok': False, 'sources': srcs, 'detail': 'timeout'})
        except ConnectionRefusedError:
            results.append({'port': p, 'ok': False, 'sources': srcs, 'detail': 'refused (port closed)'})
        except OSError as exc:
            results.append({'port': p, 'ok': False, 'sources': srcs, 'detail': str(exc)})
    n_ok = sum(r['ok'] for r in results)
    return jsonify({'ok': n_ok == len(results),
                    'message': f'{host}: {n_ok}/{len(results)} syslog ports reachable',
                    'results': results})


for _st_rule, _st_view, _st_methods in [
    ('/api/settings',              api_settings_get,          ['GET']),
    ('/api/settings',              api_settings_post,         ['POST']),
    ('/api/settings/generate-key', api_settings_generate_key, ['POST']),
    ('/api/settings/test-broker',  api_settings_test_broker,  ['POST']),
]:
    app.add_url_rule(_st_rule, endpoint=_st_view.__name__, view_func=_st_view, methods=_st_methods)
    app.add_url_rule('/api/v1' + _st_rule[4:], endpoint='v1_' + _st_view.__name__,
                     view_func=_st_view, methods=_st_methods)


'''
ai = app_src.index(ALIAS_MARKER)
app_src = app_src[:ai] + BACKEND.lstrip('\n') + '\n' + app_src[ai:]
print('0. Backend settings routes staged (before v1 alias registration).')

# ── 1. Settings button — LAST in nav, margin-left:auto ────────────────────────
# Insert after the full bad-user <button>...</button> element
baduser_idx = src.find('data-tab="baduser"')
assert baduser_idx != -1, 'bad-user tab not found'
close = src.find('</button>', baduser_idx)
assert close != -1
close += len('</button>') - 1
BTN = '\n  <button class="tab-btn" data-tab="settings" onclick="switchTab(\'settings\')" style="margin-left:auto">&#9881; Settings</button>'
src = src[:close+1] + BTN + src[close+1:]
print('1. Settings tab button added after bad-user (far right).')

# Nav is content-width inside a space-between header, so margin-left:auto has no
# room to act. Let the nav fill the gap between logo and header-actions.
NAV_OPEN = '<nav class="tab-nav">'
assert src.count(NAV_OPEN) == 1, 'tab-nav opening tag not found exactly once'
src = src.replace(NAV_OPEN, '<nav class="tab-nav" style="flex:1;margin:0 20px">')
print('1b. Nav stretched so Settings sits at far right.')

# ── 2. Settings tab HTML — inserted before </main> ────────────────────────────
TAB_HTML = """
  <div id="tab-settings" class="tab-content">
    <div style="max-width:700px;margin:0 auto;padding:1rem 0">

      <div id="settings-saved-banner" style="display:none;margin-bottom:1rem;padding:.75rem 1rem;
           background:rgba(35,134,54,.18);border:1px solid rgba(35,134,54,.4);
           border-radius:6px;font-size:.85rem;color:#3fb950">
        Settings saved.<strong style="display:block;margin-top:.3rem">
          Restart to apply: <code style="color:var(--text)">sudo systemctl restart logsim</code>
        </strong>
      </div>

      <!-- LogSim API Key -->
      <div style="border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem;margin-bottom:1rem">
        <div style="font-size:.8rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;
                    letter-spacing:.06em;margin-bottom:.8rem">LogSim API Key</div>
        <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:.5rem">
          <span id="apikey-label" style="font-family:monospace;font-size:.88rem;color:var(--text);
                flex:1;min-width:200px">&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;</span>
          <button onclick="settingsToggleKey()" id="apikey-toggle-btn"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:var(--text);cursor:pointer;font-size:.8rem">Show</button>
          <button onclick="settingsGenerateKey()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:#f0a5b8;cursor:pointer;font-size:.8rem">Generate New</button>
          <button onclick="settingsApiKeyDelete()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:#f85149;cursor:pointer;font-size:.8rem">Delete</button>
        </div>
        <div id="apikey-status" style="font-size:.8rem;min-height:1.2em;color:var(--text-muted)"></div>
        <div style="font-size:.75rem;color:var(--text-muted);margin-top:.4rem">
          Sent as <code>X-API-Key</code> header. Generating a new key restarts the service automatically.
        </div>
      </div>

      <!-- Broker VM -->
      <div style="border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem;margin-bottom:1rem">
        <div style="font-size:.8rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;
                    letter-spacing:.06em;margin-bottom:.8rem">Broker VM &mdash; Syslog Host</div>
        <div id="broker-view" style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
          <span id="broker-ip-label" style="font-family:monospace;font-size:.9rem;color:var(--text);
                flex:1;min-width:160px"></span>
          <button onclick="settingsBrokerEdit()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:var(--text);cursor:pointer;font-size:.8rem">Edit</button>
          <button onclick="settingsBrokerDelete()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:#f85149;cursor:pointer;font-size:.8rem">Delete</button>
          <button onclick="settingsBrokerTest()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:var(--text);cursor:pointer;font-size:.8rem">Test Connection</button>
        </div>
        <div id="broker-edit" style="display:none;align-items:center;gap:.5rem;flex-wrap:wrap">
          <input id="broker-ip-input" type="text" placeholder="e.g. 10.1.0.158"
                 style="flex:1;min-width:200px;background:var(--surface2);border:1px solid var(--border);
                        border-radius:4px;padding:.35rem .6rem;color:var(--text);font-size:.85rem">
          <button onclick="settingsBrokerSave()"
                  style="background:var(--accent);border:none;border-radius:4px;padding:.35rem .9rem;
                         color:#fff;cursor:pointer;font-size:.8rem;font-weight:600">Save</button>
          <button onclick="settingsBrokerCancel()"
                  style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                         padding:.35rem .7rem;color:var(--text);cursor:pointer;font-size:.8rem">Cancel</button>
        </div>
        <div id="broker-status" style="margin-top:.6rem;font-size:.8rem;min-height:1.2em"></div>
      </div>

      <!-- Data Source Integrations -->
      <div style="border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem">
        <div style="font-size:.8rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;
                    letter-spacing:.06em;margin-bottom:1rem">Data Source Integrations</div>
        <div id="ds-container"></div>
      </div>

    </div>
  </div>
"""
mc = src.rfind('</main>')
assert mc != -1, '</main> not found'
src = src[:mc] + TAB_HTML + src[mc:]
print('2. Settings tab HTML added.')

# ── 3. switchTab hook ─────────────────────────────────────────────────────────
hook = "if (tab === 'health') runHealthCheck();"
assert hook in src, 'switchTab hook marker not found'
src = src.replace(hook, hook + "\n    if (tab === 'settings') loadSettings();")
print('3. switchTab hook added.')

# ── 4. All settings JS — inserted before </script> ────────────────────────────
JS = """
  // -- Settings tab -----------------------------------------------------------
  let _settingsRawKey = '';
  let _settingsKeyVisible = false;
  let _settingsBrokerOriginal = '';

  // Data source definitions come from the backend (GET /api/settings -> sources)
  let DS_VALUES = {};
  let DS_MASK = '\\u2022'.repeat(8);  // backend placeholder for a set secret

  // Unfilled .env.example values like <your-tenant> or /path/to/x count as not set
  function dsIsPlaceholder(v) {
    return !v || /^<[^>]*>$/.test(v) || v.indexOf('<your-') !== -1 || v.indexOf('/path/to/') === 0;
  }

  function dsIsConfigured(ds, values) {
    const req = ds.fields.filter(f => !f.optional);
    return (req.length ? req : ds.fields).some(f => !dsIsPlaceholder(values[f.key]));
  }

  function dsRender(sources, values) {
    DS_VALUES = values;
    const container = document.getElementById('ds-container');
    container.innerHTML = '';
    sources.forEach(ds => {
      const configured = dsIsConfigured(ds, values);
      const card = document.createElement('div');
      card.id = 'ds-card-' + ds.id;
      card.style.cssText = 'border:1px solid var(--border);border-radius:6px;margin-bottom:.6rem;overflow:hidden';

      // Header
      const header = document.createElement('div');
      header.style.cssText = 'display:flex;align-items:center;gap:.6rem;padding:.75rem 1rem;cursor:pointer;';
      header.onclick = () => dsToggle(ds.id);

      const arrow = document.createElement('span');
      arrow.id = 'ds-arrow-' + ds.id;
      arrow.textContent = '\\u25b6';
      arrow.style.cssText = 'font-size:.65rem;color:var(--text-muted);transition:transform .2s;';

      const nameEl = document.createElement('span');
      nameEl.style.cssText = 'flex:1;font-size:.88rem;font-weight:500;color:var(--text)';
      nameEl.textContent = ds.name;

      const badge = document.createElement('span');
      badge.id = 'ds-badge-' + ds.id;
      badge.style.cssText = 'font-size:.75rem;padding:.15rem .5rem;border-radius:10px;' +
        (configured
          ? 'background:rgba(35,134,54,.2);color:#3fb950;border:1px solid rgba(35,134,54,.4)'
          : 'background:var(--surface2);color:var(--text-muted);border:1px solid var(--border)');
      badge.textContent = configured ? 'Configured' : 'Not configured';

      const editBtn = document.createElement('button');
      editBtn.style.cssText = 'background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:.28rem .65rem;color:var(--text);cursor:pointer;font-size:.78rem';
      editBtn.textContent = configured ? 'Edit' : 'Configure';
      editBtn.onclick = e => { e.stopPropagation(); dsOpen(ds.id); };

      const delBtn = document.createElement('button');
      delBtn.style.cssText = 'background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:.28rem .65rem;color:#f85149;cursor:pointer;font-size:.78rem' + (configured ? '' : ';display:none');
      delBtn.id = 'ds-del-' + ds.id;
      delBtn.textContent = 'Delete';
      delBtn.onclick = e => { e.stopPropagation(); dsDelete(ds.id, ds); };

      header.append(arrow, nameEl, badge, editBtn, delBtn);

      // Body (collapsed)
      const body = document.createElement('div');
      body.id = 'ds-body-' + ds.id;
      body.style.cssText = 'display:none;padding:.75rem 1rem 1rem;border-top:1px solid var(--border);background:rgba(0,0,0,.12)';

      if (ds.desc) {
        const d = document.createElement('div');
        d.style.cssText = 'font-size:.78rem;color:var(--text-muted);margin-bottom:.7rem';
        d.textContent = ds.desc;
        body.appendChild(d);
      }

      const inputStyle = 'flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem';
      ds.fields.forEach(field => {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:flex-start;gap:.6rem;margin-bottom:.5rem';
        const lbl = document.createElement('label');
        lbl.style.cssText = 'width:170px;font-size:.82rem;color:var(--text-muted);padding-top:.35rem';
        lbl.textContent = field.label + (field.optional ? ' (optional)' : '');
        lbl.title = field.key;
        const val = values[field.key] || '';
        let inp;
        if (field.type === 'choice') {
          inp = document.createElement('select');
          ['', ...field.choices].forEach(c => {
            const o = document.createElement('option');
            o.value = c;
            o.textContent = c || '(default)';
            inp.appendChild(o);
          });
          inp.value = field.choices.includes(val) ? val : '';
        } else {
          inp = document.createElement('input');
          inp.type = field.secret ? 'password' : 'text';
          inp.autocomplete = 'off';
          if (field.secret) {
            inp.placeholder = val === DS_MASK ? 'Set \\u2014 leave blank to keep current' : 'Not set';
          } else {
            if (!dsIsPlaceholder(val)) inp.value = val;
            else if (val) inp.placeholder = val;  // show the example as a hint
          }
        }
        inp.id = 'ds-field-' + ds.id + '-' + field.key;
        inp.style.cssText = inputStyle;
        const col = document.createElement('div');
        col.style.cssText = 'flex:1;display:flex;flex-direction:column';
        col.appendChild(inp);
        if (field.hint) {
          const h = document.createElement('div');
          h.style.cssText = 'font-size:.72rem;color:var(--text-muted);margin-top:.2rem';
          h.textContent = field.hint;
          col.appendChild(h);
        }
        row.append(lbl, col);
        body.appendChild(row);
      });

      const actions = document.createElement('div');
      actions.style.cssText = 'display:flex;gap:.5rem;margin-top:.75rem';

      const saveBtn = document.createElement('button');
      saveBtn.style.cssText = 'background:var(--accent);border:none;border-radius:4px;padding:.35rem .9rem;color:#fff;cursor:pointer;font-size:.8rem;font-weight:600';
      saveBtn.textContent = 'Save';
      saveBtn.onclick = () => dsSave(ds.id, ds);

      const cancelBtn = document.createElement('button');
      cancelBtn.style.cssText = 'background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:.35rem .7rem;color:var(--text);cursor:pointer;font-size:.8rem';
      cancelBtn.textContent = 'Cancel';
      cancelBtn.onclick = () => dsClose(ds.id);

      actions.append(saveBtn, cancelBtn);
      body.appendChild(actions);

      card.append(header, body);
      container.appendChild(card);
    });
  }

  function dsToggle(id) {
    const body = document.getElementById('ds-body-' + id);
    const arrow = document.getElementById('ds-arrow-' + id);
    const open = body.style.display === 'none';
    body.style.display = open ? 'block' : 'none';
    arrow.style.transform = open ? 'rotate(90deg)' : '';
  }

  function dsOpen(id) {
    const body = document.getElementById('ds-body-' + id);
    const arrow = document.getElementById('ds-arrow-' + id);
    body.style.display = 'block';
    arrow.style.transform = 'rotate(90deg)';
  }

  function dsClose(id) {
    const body = document.getElementById('ds-body-' + id);
    const arrow = document.getElementById('ds-arrow-' + id);
    body.style.display = 'none';
    arrow.style.transform = '';
  }

  async function dsSave(id, ds) {
    // Send only what changed. Secrets: blank = keep. Other fields: blank = clear.
    const data = {};
    ds.fields.forEach(f => {
      const inp = document.getElementById('ds-field-' + id + '-' + f.key);
      if (!inp) return;
      const v = inp.value.trim();
      const cur = DS_VALUES[f.key] || '';
      if (f.secret) {
        if (v && v !== DS_MASK) data[f.key] = v;
      } else if (v !== (dsIsPlaceholder(cur) && f.type !== 'choice' ? '' : cur)) {
        data[f.key] = v;
      }
    });
    if (!Object.keys(data).length) { dsClose(id); return; }
    try {
      await api('/api/settings', 'POST', data);
      await loadSettings();
      settingsShowBanner();
    } catch (e) { alert('Error saving ' + ds.name + ': ' + e.message); }
  }

  async function dsDelete(id, ds) {
    const names = ds.fields.map(f => f.label).join(', ');
    if (!confirm('Remove ' + ds.name + ' configuration? This will clear: ' + names + '.')) return;
    const data = {};
    ds.fields.forEach(f => { data[f.key] = ''; });
    try {
      await api('/api/settings', 'POST', data);
      await loadSettings();
      settingsShowBanner();
    } catch (e) { alert('Error removing ' + ds.name + ': ' + e.message); }
  }

  async function loadSettings() {
    try {
      const resp = await api('/api/settings');
      const s = resp.values || {};
      if (resp.mask) DS_MASK = resp.mask;
      // API key
      _settingsRawKey = s['LOGSIM_API_KEY'] || '';
      _settingsKeyVisible = false;
      const tkBtn = document.getElementById('apikey-toggle-btn');
      if (_settingsRawKey) {
        document.getElementById('apikey-label').textContent = '\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022';
        if (tkBtn) { tkBtn.style.display = ''; tkBtn.textContent = 'Show'; }
      } else {
        document.getElementById('apikey-label').textContent = '(not configured \\u2014 click Generate New)';
        if (tkBtn) tkBtn.style.display = 'none';
      }
      // Broker VM
      const broker = dsIsPlaceholder(s['SYSLOG_HOST']) ? '' : s['SYSLOG_HOST'];
      _settingsBrokerOriginal = broker;
      document.getElementById('broker-ip-label').textContent = broker || '(not set)';
      document.getElementById('broker-ip-input').value = broker;
      if (!broker) settingsBrokerEdit();
      // Data sources
      dsRender(resp.sources || [], s);
      settingsLoadError('');
    } catch (e) {
      console.error('loadSettings failed', e);
      settingsLoadError('Could not load settings: ' + e.message);
    }
  }

  function settingsLoadError(msg) {
    let el = document.getElementById('settings-load-error');
    if (!el) {
      el = document.createElement('div');
      el.id = 'settings-load-error';
      el.style.cssText = 'margin-bottom:1rem;padding:.75rem 1rem;border-radius:6px;font-size:.85rem;' +
        'background:rgba(248,81,73,.12);border:1px solid rgba(248,81,73,.4);color:#f85149';
      const banner = document.getElementById('settings-saved-banner');
      banner.parentNode.insertBefore(el, banner);
    }
    el.textContent = msg;
    el.style.display = msg ? 'block' : 'none';
  }

  function settingsToggleKey() {
    _settingsKeyVisible = !_settingsKeyVisible;
    const tb = document.getElementById('apikey-toggle-btn');
    if (_settingsKeyVisible) {
      document.getElementById('apikey-label').textContent = _settingsRawKey || '(not configured)';
      if (tb) tb.textContent = 'Hide';
    } else {
      document.getElementById('apikey-label').textContent = _settingsRawKey
        ? '\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022' : '(not configured)';
      if (tb) tb.textContent = 'Show';
    }
  }

  async function settingsApiKeyDelete() {
    if (!confirm('Remove the API key? The dashboard will become unauthenticated.')) return;
    try {
      await api('/api/settings', 'POST', { LOGSIM_API_KEY: '' });
      _settingsRawKey = '';
      _settingsKeyVisible = false;
      document.getElementById('apikey-label').textContent = '(not configured \\u2014 click Generate New)';
      const tkBtn = document.getElementById('apikey-toggle-btn');
      if (tkBtn) tkBtn.style.display = 'none';
      document.getElementById('apikey-status').textContent = '';
      settingsShowBanner('API key removed from .env. After restart the dashboard API is unauthenticated: sudo systemctl restart logsim');
    } catch (e) { alert('Error: ' + e.message); }
  }

  async function settingsGenerateKey() {
    if (!confirm('Generate a new API key? It is saved to .env and takes effect after you restart the service. ' +
                 'External API callers will then need the new key.')) return;
    document.getElementById('apikey-label').textContent = 'Generating...';
    try {
      const r = await api('/api/settings/generate-key', 'POST', {});
      _settingsRawKey = r.key;
      _settingsKeyVisible = false;
      document.getElementById('apikey-label').textContent = '\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022';
      const tkBtn = document.getElementById('apikey-toggle-btn');
      if (tkBtn) { tkBtn.style.display = ''; tkBtn.textContent = 'Show'; }
      settingsShowBanner('New key saved to .env. Restart to apply: sudo systemctl restart logsim \\u2014 then reload this page.');
    } catch (e) {
      document.getElementById('apikey-label').textContent = _settingsRawKey
        ? '\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022' : '(not configured \\u2014 click Generate New)';
      alert('Error: ' + e.message);
    }
  }

  function settingsBrokerEdit() {
    document.getElementById('broker-view').style.display = 'none';
    const ed = document.getElementById('broker-edit');
    ed.style.display = 'flex';
    ed.querySelector('input').focus();
  }
  function settingsBrokerCancel() {
    document.getElementById('broker-ip-input').value = _settingsBrokerOriginal;
    document.getElementById('broker-edit').style.display = 'none';
    document.getElementById('broker-view').style.display = 'flex';
  }
  async function settingsBrokerSave() {
    const ip = document.getElementById('broker-ip-input').value.trim();
    if (!ip) { alert('Enter a Broker VM IP address.'); return; }
    try {
      await api('/api/settings', 'POST', { SYSLOG_HOST: ip });
      _settingsBrokerOriginal = ip;
      document.getElementById('broker-ip-label').textContent = ip;
      document.getElementById('broker-edit').style.display = 'none';
      document.getElementById('broker-view').style.display = 'flex';
      settingsBrokerStatus('', '');
      settingsShowBanner();
    } catch (e) { alert('Error saving: ' + e.message); }
  }
  async function settingsBrokerDelete() {
    if (!confirm('Remove the Broker VM IP?')) return;
    try {
      await api('/api/settings', 'POST', { SYSLOG_HOST: '' });
      _settingsBrokerOriginal = '';
      document.getElementById('broker-ip-label').textContent = '(not set)';
      settingsBrokerStatus('', '');
      settingsShowBanner();
      settingsBrokerEdit();
    } catch (e) { alert('Error: ' + e.message); }
  }
  async function settingsBrokerTest() {
    const host = document.getElementById('broker-ip-label').textContent.trim();
    if (!host || host === '(not set)') { settingsBrokerStatus('No Broker VM IP configured.', 'warn'); return; }
    settingsBrokerStatus('Testing...', '');
    try {
      const r = await api('/api/settings/test-broker', 'POST', { host });
      settingsBrokerStatus(r.message, r.ok ? 'ok' : 'err');
      const el = document.getElementById('broker-status');
      (r.results || []).forEach(p => {
        const row = document.createElement('div');
        row.style.cssText = 'font-family:monospace;font-size:.78rem;margin-top:.2rem;color:' + (p.ok ? '#3fb950' : '#f85149');
        row.textContent = (p.ok ? '\\u2713 ' : '\\u2717 ') + 'TCP ' + p.port + ' \\u2014 ' + p.detail + '  (' + p.sources + ')';
        el.appendChild(row);
      });
    } catch (e) { settingsBrokerStatus(e.message, 'err'); }
  }
  function settingsBrokerStatus(msg, state) {
    const el = document.getElementById('broker-status');
    const colors = { ok: '#3fb950', err: '#f85149', warn: '#d29922', '': 'var(--text-muted)' };
    el.style.color = colors[state] || colors[''];
    el.textContent = msg;
  }
  function settingsShowBanner(msg) {
    const el = document.getElementById('settings-saved-banner');
    const strong = el.querySelector('strong');
    if (msg) {
      strong.style.display = 'none';
      el.childNodes[0].textContent = msg + ' ';
    } else {
      strong.style.display = 'block';
      el.childNodes[0].textContent = 'Settings saved. ';
    }
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; strong.style.display = 'block'; }, 15000);
  }
"""
sc = src.rfind('</script>')
assert sc != -1, '</script> not found'
src = src[:sc] + JS + src[sc:]
print('4. Settings JS added.')

# ── Integrity check — nothing is written unless all of this passes ────────────
assert '</html>' in src, 'ERROR: index.html truncated!'
assert src.count('id="tab-settings"') == 1
assert src.count('data-tab="settings"') == 1
assert src.count('let _settingsRawKey') == 1
assert 'dsRender' in src and 'LogSim API Key' in src
ai = app_src.index(ALIAS_MARKER)
assert app_src.index('def api_settings_get') < ai < app_src.index('if __name__ == "__main__"'), \
    'backend routes are not positioned before alias registration / entry point'
compile(app_src, str(APP), 'exec')  # SyntaxError here aborts before any write
print(f'Integrity OK: app.py {app_src.count(chr(10))+1} lines, index.html {src.count(chr(10))+1} lines')
APP.write_text(app_src, encoding='utf-8')
f.write_text(src, encoding='utf-8')
print('Done. Run: sudo systemctl restart logsim')
