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
if 'data-tab="settings"' in src or 'tab-settings' in src or '_settingsRawKey' in src:
    raise SystemExit('ABORT: index.html is already patched. Restore the clean file first:\n'
                     '  sudo -u lab-user git -C /opt/logsim checkout -- dashboard/templates/index.html\n'
                     'then re-run this script. No changes were made.')

# ── 1. Settings button — LAST in nav, margin-left:auto ────────────────────────
# Find the closing > of the bad-user button and insert Settings after it
baduser_idx = src.find('data-tab="baduser"')
assert baduser_idx != -1, 'bad-user tab not found'
close = src.find('>', baduser_idx)
assert close != -1
BTN = '\n  <button class="tab-btn" data-tab="settings" onclick="switchTab(\'settings\')" style="margin-left:auto">&#9881; Settings</button>'
src = src[:close+1] + BTN + src[close+1:]
print('1. Settings tab button added after bad-user (far right).')

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

  // Data source definitions
  const DS_CONFIG = [
    { id: 'http', name: 'HTTP Collector',
      fields: [{ key: 'HTTP_COLLECTOR_URL', label: 'Collector URL', type: 'text' }] },
    { id: 'okta', name: 'Okta SSO',
      fields: [{ key: 'OKTA_KEY', label: 'API Key', type: 'password' }] },
    { id: 'proofpoint', name: 'Proofpoint Email',
      fields: [{ key: 'PROOFPOINT_KEY', label: 'API Key', type: 'password' }] },
    { id: 'cribl', name: 'Cribl Receiver',
      fields: [
        { key: 'CRIBL_COLLECTOR_URL', label: 'Collector URL', type: 'text' },
        { key: 'CRIBL_TOKEN',         label: 'Token',         type: 'password' }
      ]},
    { id: 'wec', name: 'WEC / PFX',
      fields: [
        { key: 'WEC_BROKER_URL',     label: 'Broker URL',    type: 'text' },
        { key: 'WEC_PFX_PATH',       label: 'PFX Path',      type: 'text' },
        { key: 'WEC_PFX_PASSWORD',   label: 'PFX Password',  type: 'password' }
      ]}
  ];

  function dsIsConfigured(ds, settings) {
    return ds.fields.some(f => settings[f.key] && settings[f.key] !== '********');
  }

  function dsRender(settings) {
    const container = document.getElementById('ds-container');
    container.innerHTML = '';
    DS_CONFIG.forEach(ds => {
      const configured = dsIsConfigured(ds, settings);
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

      ds.fields.forEach(field => {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem';
        const lbl = document.createElement('label');
        lbl.style.cssText = 'width:140px;font-size:.82rem;color:var(--text-muted)';
        lbl.textContent = field.label;
        const inp = document.createElement('input');
        inp.type = field.type;
        inp.id = 'ds-field-' + ds.id + '-' + field.key;
        inp.style.cssText = 'flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:.32rem .6rem;color:var(--text);font-size:.82rem';
        if (field.type === 'password') inp.placeholder = 'Leave blank to keep current';
        const val = settings[field.key];
        if (val && val !== '********') inp.value = val;
        row.append(lbl, inp);
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
    const data = {};
    ds.fields.forEach(f => {
      const inp = document.getElementById('ds-field-' + id + '-' + f.key);
      if (inp && inp.value.trim() && inp.value !== '********') data[f.key] = inp.value.trim();
    });
    if (!Object.keys(data).length) { dsClose(id); return; }
    try {
      await api('/api/settings', 'POST', data);
      dsClose(id);
      // Update badge and buttons
      const badge = document.getElementById('ds-badge-' + id);
      const delBtn = document.getElementById('ds-del-' + id);
      badge.textContent = 'Configured';
      badge.style.cssText = 'font-size:.75rem;padding:.15rem .5rem;border-radius:10px;background:rgba(35,134,54,.2);color:#3fb950;border:1px solid rgba(35,134,54,.4)';
      if (delBtn) delBtn.style.display = '';
      settingsShowBanner();
    } catch (e) { alert('Error saving: ' + e.message); }
  }

  async function dsDelete(id, ds) {
    const names = ds.fields.map(f => f.label).join(', ');
    if (!confirm('Remove ' + ds.name + ' configuration? This will clear: ' + names + '.')) return;
    const data = {};
    ds.fields.forEach(f => { data[f.key] = ''; });
    try {
      await api('/api/settings', 'POST', data);
      // Update badge and buttons
      const badge = document.getElementById('ds-badge-' + id);
      const delBtn = document.getElementById('ds-del-' + id);
      badge.textContent = 'Not configured';
      badge.style.cssText = 'font-size:.75rem;padding:.15rem .5rem;border-radius:10px;background:var(--surface2);color:var(--text-muted);border:1px solid var(--border)';
      if (delBtn) delBtn.style.display = 'none';
      // Clear fields
      ds.fields.forEach(f => {
        const inp = document.getElementById('ds-field-' + id + '-' + f.key);
        if (inp) inp.value = '';
      });
      settingsShowBanner();
    } catch (e) { alert('Error: ' + e.message); }
  }

  async function loadSettings() {
    try {
      const s = await api('/api/settings');
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
      const broker = s['SYSLOG_HOST'] || '';
      _settingsBrokerOriginal = broker;
      document.getElementById('broker-ip-label').textContent = broker || '(not set)';
      document.getElementById('broker-ip-input').value = broker;
      if (!broker) settingsBrokerEdit();
      // Data sources
      dsRender(s);
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
    if (!host || host === '(not set)') { settingsBrokerStatus('No Broker VM IP configured.', 'warn'); return; }
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

# ── Integrity check ───────────────────────────────────────────────────────────
assert '</html>' in src, 'ERROR: file truncated!'
assert 'tab-settings' in src
assert 'switchTab' in src
assert 'dsRender' in src
assert 'LogSim API Key' in src
print(f'Integrity OK: {src.count(chr(10))+1} lines')
f.write_text(src)
print('Done. Run: sudo systemctl restart logsim')
