#!/usr/bin/env python3
"""
LogSimv2 Settings UI — final clean patch.
Run as: sudo -u lab-user python3 patch_settings_final.py
"""
from pathlib import Path

f = Path('/opt/logsim/dashboard/templates/index.html')
src = f.read_text()
assert '</html>' in src, 'File appears truncated — restore from git first.'
print(f'File OK: {src.count(chr(10))+1} lines')

# ── 1. Settings tab button — inserted BEFORE bad-user ─────────────────────────
baduser_idx = src.find('data-tab="baduser"')
assert baduser_idx != -1, 'bad-user tab button not found'
btn_open = src.rfind('<button', 0, baduser_idx)
assert btn_open != -1
BTN = '<button class="tab-btn" data-tab="settings" onclick="switchTab(\'settings\')">&#9881; Settings</button>\n  '
src = src[:btn_open] + BTN + src[btn_open:]
print('1. Settings tab button added before bad-user.')

# ── 2. Settings tab HTML — inserted before </main> ────────────────────────────
TAB_HTML = """
  <div id="tab-settings" class="tab-content">
    <div style="max-width:660px;margin:0 auto;padding:1rem 0">

      <div id="settings-saved-banner" style="display:none;margin-bottom:1rem;padding:.75rem 1rem;
           background:rgba(35,134,54,.18);border:1px solid rgba(35,134,54,.4);
           border-radius:6px;font-size:.85rem;color:#3fb950">
        Settings saved.<strong style="display:block;margin-top:.3rem">
        Restart to apply: <code style="color:var(--text)">sudo systemctl restart logsim</code>
        </strong>
      </div>

      <!-- API Key -->
      <div style="border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem;margin-bottom:1rem">
        <div style="font-size:.8rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;
                    letter-spacing:.06em;margin-bottom:.8rem">API Key</div>
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

      <!-- Other Transport Settings -->
      <details style="border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem">
        <summary style="font-size:.8rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;
                        letter-spacing:.06em;cursor:pointer">Other Transport Settings</summary>
        <form id="settings-transport-form" style="margin-top:.9rem">

          <div style="font-size:.78rem;color:var(--text-muted);margin-bottom:.5rem">HTTP Collector</div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Collector URL</label>
            <input type="text" name="HTTP_COLLECTOR_URL"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Okta Key</label>
            <input type="password" name="OKTA_KEY" placeholder="Leave blank to keep current"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Proofpoint Key</label>
            <input type="password" name="PROOFPOINT_KEY" placeholder="Leave blank to keep current"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>

          <div style="font-size:.78rem;color:var(--text-muted);margin-bottom:.5rem">Cribl Receiver</div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Collector URL</label>
            <input type="text" name="CRIBL_COLLECTOR_URL"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Token</label>
            <input type="password" name="CRIBL_TOKEN" placeholder="Leave blank to keep current"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>

          <div style="font-size:.78rem;color:var(--text-muted);margin-bottom:.5rem">WEC (Windows Events)</div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">Broker URL</label>
            <input type="text" name="WEC_BROKER_URL"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">PFX Path</label>
            <input type="text" name="WEC_PFX_PATH"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem">
            <label style="width:160px;font-size:.82rem;color:var(--text-muted)">PFX Password</label>
            <input type="password" name="WEC_PFX_PASSWORD" placeholder="Leave blank to keep current"
                   style="flex:1;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem">
          </div>

          <button type="submit"
                  style="background:var(--accent);border:none;border-radius:6px;color:#fff;
                         cursor:pointer;font-size:.82rem;font-weight:600;padding:.45rem 1.1rem">
            Save Transport Settings
          </button>
        </form>
      </details>

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

# ── 4. Settings JS — inserted before </script> ────────────────────────────────
JS = """
  // -- Settings tab -----------------------------------------------------------
  let _settingsRawKey = '';
  let _settingsKeyVisible = false;
  let _settingsBrokerOriginal = '';

  async function loadSettings() {
    try {
      const s = await api('/api/settings');
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
      const broker = s['SYSLOG_HOST'] || '';
      _settingsBrokerOriginal = broker;
      document.getElementById('broker-ip-label').textContent = broker || '(not set)';
      document.getElementById('broker-ip-input').value = broker;
      if (!broker) settingsBrokerEdit();
      const form = document.getElementById('settings-transport-form');
      const skip = new Set(['LOGSIM_API_KEY', 'SYSLOG_HOST']);
      for (const [k, v] of Object.entries(s)) {
        if (skip.has(k)) continue;
        const el = form.querySelector('[name="' + k + '"]');
        if (el && v && v !== '********') el.value = v;
      }
    } catch (e) { console.error('loadSettings failed', e); }
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
      settingsShowBanner('API key removed. Restart the service to apply.');
    } catch (e) { alert('Error: ' + e.message); }
  }

  async function settingsGenerateKey() {
    if (!confirm('Generate a new API key? The service will restart automatically.')) return;
    document.getElementById('apikey-label').textContent = 'Generating...';
    try {
      const r = await api('/api/settings/generate-key', 'POST', {});
      _settingsRawKey = r.key;
      _settingsKeyVisible = false;
      document.getElementById('apikey-label').textContent = '\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022';
      const tkBtn = document.getElementById('apikey-toggle-btn');
      if (tkBtn) { tkBtn.style.display = ''; tkBtn.textContent = 'Show'; }
      settingsShowBanner('New key saved. Service is restarting \\u2014 this usually takes 10\\u201315 seconds. Page reloads automatically.');
      setTimeout(() => location.reload(), 12000);
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
    if (!host || host === '(not set)') {
      settingsBrokerStatus('No Broker VM IP configured.', 'warn'); return;
    }
    settingsBrokerStatus('Testing...', '');
    try {
      const r = await api('/api/settings/test-broker', 'POST', { host });
      settingsBrokerStatus(r.message, r.ok ? 'ok' : 'err');
    } catch (e) { settingsBrokerStatus(e.message, 'err'); }
  }
  function settingsBrokerStatus(msg, state) {
    const el = document.getElementById('broker-status');
    const colors = { ok: '#3fb950', err: '#f85149', warn: '#d29922', '': 'var(--text-muted)' };
    el.style.color = colors[state] || colors[''];
    el.textContent = msg;
  }
  document.getElementById('settings-transport-form').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {};
    for (const el of e.target.querySelectorAll('input[name]')) {
      if (el.value.trim() && el.value !== '********') data[el.name] = el.value.trim();
    }
    if (!Object.keys(data).length) { alert('No changes to save.'); return; }
    try { await api('/api/settings', 'POST', data); settingsShowBanner(); }
    catch (err) { alert('Error: ' + err.message); }
  });
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
    setTimeout(() => {
      el.style.display = 'none';
      strong.style.display = 'block';
    }, 15000);
  }
"""
sc = src.rfind('</script>')
assert sc != -1, '</script> not found'
src = src[:sc] + JS + src[sc:]
print('4. Settings JS added.')

# ── Integrity check ───────────────────────────────────────────────────────────
assert '</html>' in src, 'ERROR: file truncated after patching!'
assert 'tab-settings' in src
assert 'switchTab' in src
assert 'loadSettings' in src
print(f'Integrity OK: {src.count(chr(10))+1} lines')

f.write_text(src)
print('Done. Run: sudo systemctl restart logsim')
