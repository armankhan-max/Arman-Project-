const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let settings = null, voices = [], style = 'documentary', voiceMode = 'tts', current = null, pollTimer = null;

async function api(path, opts = {}) {
  if (opts.json !== undefined) { opts.body = JSON.stringify(opts.json); opts.headers = { 'Content-Type': 'application/json' }; opts.method = opts.method || 'POST'; }
  const r = await fetch(path, opts);
  if (r.status === 401 && path !== '/api/login') { showGate(); throw new Error('Please log in.'); }
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch { } throw new Error(m); }
  return opts.raw ? r : r.json();
}
async function busy(btn, fn) {
  const t = btn.textContent; btn.disabled = true; btn.textContent = 'Working…';
  try { return await fn(); } finally { btn.disabled = false; btn.textContent = t; }
}

// ---------- login ----------
async function showGate() {
  const me = await (await fetch('/api/me')).json();
  if (me.authed) return boot();
  $('#app').classList.add('hidden'); $('#gate').classList.remove('hidden');
  $('#gateMsg').textContent = me.setup ? 'Owner login' : 'First time here: choose your owner password.';
  $('#gateBtn').textContent = me.setup ? 'Log in' : 'Create password';
  $('#gateForm').onsubmit = async e => {
    e.preventDefault(); $('#gateErr').textContent = '';
    try { await api(me.setup ? '/api/login' : '/api/setup', { json: { password: $('#gatePw').value } }); $('#gatePw').value = ''; boot(); }
    catch (err) { $('#gateErr').textContent = err.message; }
  };
}
$('#logout').onclick = async () => { await api('/api/logout', { method: 'POST' }); location.reload(); };

// ---------- tabs ----------
function tab(name) {
  clearTimeout(pollTimer);
  $$('main > section').forEach(s => s.classList.toggle('hidden', s.id !== 'tab-' + name));
  $$('#nav a').forEach(a => a.classList.toggle('on', a.dataset.tab === name || (name === 'project' && a.dataset.tab === 'videos')));
  if (name === 'videos') loadVideos();
  if (name === 'settings') loadSettings();
  window.scrollTo(0, 0);
}
$$('#nav a').forEach(a => a.onclick = () => tab(a.dataset.tab));

async function boot() {
  $('#gate').classList.add('hidden'); $('#app').classList.remove('hidden');
  settings = await api('/api/settings');
  style = settings.styles[settings.default_style] ? settings.default_style : Object.keys(settings.styles)[0];
  renderStyles(); renderMusic();
  $('#aiWarn').classList.toggle('hidden', settings.llm_active !== 'none');
  $('#aiWarn').textContent = 'AI script writing is off, so paste your own script under “More options”. Turn it on in the Owner panel.';
  voices = await api('/api/voices');
  const langs = [...new Set(voices.map(v => v.lang))].sort();
  const pref = ['en-US', 'en-IN', 'hi-IN', 'en-GB'];
  $('#cVoiceLang').innerHTML = [...pref.filter(l => langs.includes(l)), ...langs.filter(l => !pref.includes(l))].map(l => `<option>${l}</option>`).join('');
  const dv = voices.find(v => v.id === settings.default_voice);
  if (dv) $('#cVoiceLang').value = dv.lang;
  fillVoices(dv && dv.id);
}
function fillVoices(sel) {
  const l = $('#cVoiceLang').value;
  $('#cVoice').innerHTML = voices.filter(v => v.lang === l).map(v => `<option value="${v.id}">${esc(v.name)}</option>`).join('');
  if (sel) $('#cVoice').value = sel;
}
$('#cVoiceLang').onchange = () => fillVoices();
function renderStyles() {
  $('#cStyles').innerHTML = Object.entries(settings.styles).map(([k, s]) =>
    `<div class="style ${k === style ? 'on' : ''}" data-k="${esc(k)}"><b>${esc(s.label || k)}</b><span>${esc(s.desc || '')}</span></div>`).join('');
  $$('#cStyles .style').forEach(el => el.onclick = () => { style = el.dataset.k; renderStyles(); });
  $('#cAvatarBox').classList.toggle('hidden', style !== 'avatar');
}
function musicOptions(sel) {
  const opts = [['', 'Best for this style'], ['cinematic', 'Cinematic'], ['suspense', 'Suspense'], ['emotional', 'Emotional'], ['calm', 'Calm'], ['upbeat', 'Upbeat'],
  ...(settings.music_library || []).map(m => [m, '♪ ' + m]), ['none', 'No music']];
  return opts.map(([v, t]) => `<option value="${esc(v)}" ${v === (sel || '') ? 'selected' : ''}>${esc(t)}</option>`).join('');
}
function renderMusic() { $('#cMusic').innerHTML = musicOptions(''); }

// ---------- create ----------
$$('#cVoiceMode a').forEach(a => a.onclick = () => {
  voiceMode = a.dataset.v;
  $$('#cVoiceMode a').forEach(x => x.classList.toggle('on', x === a));
  $('#cTts').classList.toggle('hidden', voiceMode !== 'tts'); $('#cUpload').classList.toggle('hidden', voiceMode !== 'upload');
});
$('#cPreview').onclick = e => busy(e.target, async () => {
  const r = await api('/api/voice-preview', { json: { voice: $('#cVoice').value, rate: +$('#cRate').value }, raw: true });
  const p = $('#player'); p.src = URL.createObjectURL(await r.blob()); p.play();
}).catch(err => $('#cErr').textContent = err.message);
$('#cSuggest').onclick = e => busy(e.target, async () => {
  const topic = $('#cTitle').value.trim(); if (!topic) { $('#cErr').textContent = 'Type a topic first.'; return; }
  const r = await api('/api/titles', { json: { topic, count: 8, language: $('#cLang').value } });
  $('#cIdeas').innerHTML = r.titles.map(t => `<span class="chip">${esc(t)}</span>`).join('');
  $$('#cIdeas .chip').forEach(c => c.onclick = () => $('#cTitle').value = c.textContent);
}).catch(err => $('#cErr').textContent = err.message);
$('#cGo').onclick = e => busy(e.target, async () => {
  $('#cErr').textContent = '';
  const fd = new FormData();
  fd.append('data', JSON.stringify({
    title: $('#cTitle').value, style, minutes: +$('#cMinutes').value, aspect: $('#cAspect').value, language: $('#cLang').value,
    voice: $('#cVoice').value, rate: +$('#cRate').value, source: $('#cSource').value, music: $('#cMusic').value,
    captions: $('#cCaptions').value === '1', script: $('#cScript').value, notes: $('#cNotes').value, persona: $('#cPersona').value,
    show_title: $('#cShowTitle').checked, sfx: $('#cSfx').checked, preview: $('#cFast').checked
  }));
  if (voiceMode === 'upload') { if (!$('#cVoFile').files[0]) throw new Error('Choose your voiceover file.'); fd.append('voiceover', $('#cVoFile').files[0]); }
  if (style === 'avatar' && $('#cAvatar').files[0]) fd.append('avatar', $('#cAvatar').files[0]);
  if (style === 'avatar' && $('#cAvatarVideo').files[0]) {
    if (!$('#cScript').value.trim()) throw new Error('Paste the script your avatar video speaks under “More options”, so scenes can be matched.');
    fd.append('avatar_video', $('#cAvatarVideo').files[0]);
  }
  const p = await api('/api/projects', { method: 'POST', body: fd });
  openProject(p.id);
}).catch(err => $('#cErr').textContent = err.message);

// ---------- videos ----------
const fmt = s => s ? `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}` : '';
async function loadVideos() {
  const list = await api('/api/projects');
  $('#vList').innerHTML = list.length ? list.map(p => `<div class="vcard" data-id="${p.id}">
    <div class="ph" ${p.thumb ? `style="background-image:url(/media/${p.id}/${p.thumb}?v=${Date.now()})"` : ''}>${p.thumb ? '' : esc(p.step || p.status)}</div>
    <div class="in"><b>${esc(p.title)}</b><span class="badge ${p.status}">${p.status === 'working' ? p.progress + '%' : p.status}</span>
    <span class="muted small"> ${esc((settings.styles[p.style] || {}).label || p.style || '')} ${fmt(p.duration)}</span></div></div>`).join('')
    : '<p class="muted">No videos yet. Make your first one in “Create”.</p>';
  $$('#vList .vcard').forEach(c => c.onclick = () => openProject(c.dataset.id));
}

// ---------- one project ----------
async function openProject(id) {
  tab('project');
  $('#tab-project').innerHTML = '<p class="muted">Loading…</p>';
  current = null;
  await refreshProject(id, true);
}
async function refreshProject(id, full) {
  let p;
  try { p = await api('/api/projects/' + id); } catch (e) { $('#tab-project').innerHTML = `<p class="err">${esc(e.message)}</p>`; return; }
  const running = p.status === 'queued' || p.status === 'working';
  if (running) {
    if (!current || !$('#pBar')) {
      $('#tab-project').innerHTML = `<h1>${esc(p.title)}</h1><div class="card"><b id="pStep"></b><div class="bar"><i id="pBar"></i></div>
        <pre class="log" id="pLog"></pre><p class="muted small">You can leave this page; the video keeps rendering. Find it later in “My videos”.</p></div>`;
    }
    $('#pStep').textContent = `${p.step || 'Starting'} · ${p.progress}%`;
    $('#pBar').style.width = p.progress + '%';
    $('#pLog').textContent = (p.log || []).slice(-40).join('\n'); $('#pLog').scrollTop = 1e6;
    current = p;
    pollTimer = setTimeout(() => refreshProject(id), 2000);
    return;
  }
  current = p;
  renderProject(p);
}
function copyBox(label, text) {
  return text ? `<label>${label}</label><div class="copybox"><span>${esc(text)}</span><button class="btn small" data-copy>Copy</button></div>` : '';
}
function renderProject(p) {
  const v = '?v=' + (p.version || 0), base = `/media/${p.id}/`;
  const m = p.meta || {};
  let html = `<div class="row"><h1 style="flex:1">${esc(p.title)}</h1><button class="btn danger small" id="pDel">Delete</button></div>`;
  if (p.status === 'error') html += `<div class="card"><p class="err">Something went wrong: ${esc(p.error)}</p><pre class="log">${esc((p.log || []).slice(-25).join('\n'))}</pre>
    <button class="btn primary" id="pRetry">Try again</button></div>`;
  if (p.video) html += `<div class="card"><video controls src="${base}${p.video}${v}" poster="${p.thumb ? base + p.thumb + v : ''}"></video>
    <div class="row" style="margin-top:10px"><a class="btn primary" href="${base}${p.video}?download=1">⬇ Download video</a>
    ${p.thumb ? `<a class="btn" href="${base}${p.thumb}?download=1">⬇ Thumbnail</a>` : ''}
    <span class="muted small">${fmt(p.duration)} · ${esc(p.aspect || '16:9')}${p.preview ? ' · fast draft (720p)' : ''}</span></div></div>`;
  if (p.video) html += `<div class="two"><div class="card"><h3>Thumbnail</h3>${p.thumb ? `<img class="thumb" src="${base}${p.thumb}${v}">` : ''}
      <div class="row" style="margin-top:10px"><input id="pThText" value="${esc(m.thumb_text || '')}" placeholder="Thumbnail text">
      <select id="pThLayout" style="max-width:130px"><option value="left">Text left</option><option value="right">Text right</option><option value="center">Centre</option></select>
      <button class="btn" id="pThGo">Remake</button></div></div>
    <div class="card"><h3>Upload pack</h3>${copyBox('Titles', (m.titles || []).join('\n'))}${copyBox('Tags', m.tags)}${copyBox('Hashtags', m.hashtags)}
      ${copyBox('Pinned comment', m.pinned_comment)}</div></div>
    <div class="card">${copyBox('Description', m.description)}${copyBox('Full script', p.script)}
      ${(p.credits || []).length ? copyBox('Footage credits', p.credits.join('\n')) : ''}</div>`;
  if ((p.scenes || []).length) {
    html += `<div class="card"><div class="row"><h3 style="flex:1;margin:0">Scenes (${p.scenes.length})</h3>
      <select id="pMusic" style="max-width:190px">${musicOptions(p.music)}</select>
      <select id="pCaptions" style="max-width:150px"><option value="1">Captions on</option><option value="0" ${p.captions === false ? 'selected' : ''}>Captions off</option></select></div>
      <p class="muted small">Change any narration, on-screen text or search words, or upload your own picture/video for a scene. Then render again; only what changed is redone.</p>
      <div id="pScenes">${p.scenes.map((s, i) => sceneRow(p, s, i)).join('')}</div>
      <div class="row" style="margin-top:14px"><button class="btn primary" id="pRender">💾 Save & render again</button>
      <button class="btn" id="pDraft">Render fast draft</button><span class="err" id="pErr"></span></div></div>`;
  }
  $('#tab-project').innerHTML = html;
  $$('[data-copy]').forEach(b => b.onclick = () => { navigator.clipboard.writeText(b.previousElementSibling.textContent); b.textContent = 'Copied'; setTimeout(() => b.textContent = 'Copy', 1200); });
  $('#pDel').onclick = async () => { if (confirm('Delete this video and all its files?')) { await api('/api/projects/' + p.id, { method: 'DELETE' }); tab('videos'); } };
  if ($('#pRetry')) $('#pRetry').onclick = () => saveScenes(p, false);
  if ($('#pThGo')) $('#pThGo').onclick = e => busy(e.target, async () => { renderProject(current = await api(`/api/projects/${p.id}/thumb`, { json: { text: $('#pThText').value, layout: $('#pThLayout').value } })); });
  if ($('#pRender')) { $('#pRender').onclick = () => saveScenes(p, false); $('#pDraft').onclick = () => saveScenes(p, true); }
  $$('.scene input[type=file]').forEach(inp => inp.onchange = async () => {
    const fd = new FormData(); fd.append('file', inp.files[0]);
    try { const s = await api(`/api/projects/${p.id}/scenes/${inp.dataset.i}/asset`, { method: 'POST', body: fd }); p.scenes[inp.dataset.i] = s; inp.closest('.scene').querySelector('.left').innerHTML = scenePic(p, s, inp.dataset.i); }
    catch (err) { $('#pErr').textContent = err.message; }
  });
}
function scenePic(p, s, i) {
  const a = (s.assets || [])[0];
  const url = a ? `/media/${p.id}/${a.path}?v=${p.version || 0}` : '';
  return `<div class="pic">${a ? (a.type === 'video' ? `<video muted preload="metadata" src="${url}#t=0.5"></video>` : `<img loading="lazy" src="${url}">`) : ''}</div>
    <div class="meta">${fmt(s.start) || '0:00'} · ${a ? esc(a.source) : 'no visual yet'}</div>`;
}
function sceneRow(p, s, i) {
  return `<div class="scene" data-i="${i}"><div class="left">${scenePic(p, s, i)}</div><div>
    <textarea data-f="narration">${esc(s.narration)}</textarea>
    <div class="row" style="margin-top:6px">
      <input data-f="text" value="${esc(s.text || '')}" placeholder="On-screen text (optional)" style="max-width:220px">
      <input data-f="queries" value="${esc((s.queries || []).join(', '))}" placeholder="B-roll search words, comma separated">
    </div>
    <div class="row" style="margin-top:6px">
      <input data-f="graphic" value="${esc(s.graphic || '')}" placeholder="Animated graphic (optional): map: Egypt · bars: Honey=3000, Milk=7 (days) · timeline: 1922=Tomb opened; 2026=Still edible">
      ${p.style === 'avatar' ? `<select data-f="kind" style="max-width:110px"><option value="broll">B-roll</option><option value="aroll" ${s.kind === 'aroll' ? 'selected' : ''}>A-roll (host)</option></select>` : ''}
    </div>
    <div class="row" style="margin-top:6px"><label class="check small" style="margin:0"><input type="checkbox" data-f="refresh"> New visuals</label>
      <label class="btn small" style="margin:0">Upload my own<input type="file" data-i="${i}" accept="image/*,video/*" hidden></label>
      <button class="btn small ghost danger" onclick="this.closest('.scene').remove()">Remove scene</button></div>
  </div></div>`;
}
async function saveScenes(p, preview) {
  const scenes = $$('#pScenes .scene').map(el => ({
    _i: +el.dataset.i, narration: $('[data-f=narration]', el).value, text: $('[data-f=text]', el).value,
    queries: $('[data-f=queries]', el).value.split(','), graphic: $('[data-f=graphic]', el).value, kind: ($('[data-f=kind]', el) || {}).value || 'broll',
    refresh: $('[data-f=refresh]', el).checked
  }));
  const body = { render: true, preview };
  if (scenes.length) Object.assign(body, { scenes, music: $('#pMusic').value, captions: $('#pCaptions').value === '1' });
  try { await api('/api/projects/' + p.id, { method: 'PUT', json: body }); current = null; refreshProject(p.id); }
  catch (err) { ($('#pErr') || {}).textContent = err.message; }
}

// ---------- titles ----------
$('#tGo').onclick = e => busy(e.target, async () => {
  const r = await api('/api/titles', { json: { topic: $('#tTopic').value, count: 10 } });
  $('#tNote').textContent = r.source === 'ai' ? '' : 'AI writer is not reachable, so these come from proven title formulas. Add an AI key in the Owner panel for smarter titles.';
  $('#tOut').innerHTML = r.titles.map(t => `<div class="copybox"><span>${esc(t)}</span><button class="btn small" data-use>Use</button></div>`).join('');
  $$('#tOut [data-use]').forEach(b => b.onclick = () => { $('#cTitle').value = b.previousElementSibling.textContent; tab('create'); });
}).catch(err => $('#tNote').textContent = err.message);

// ---------- thumbnails ----------
$('#thGo').onclick = e => busy(e.target, async () => {
  $('#thErr').textContent = '';
  if (!$('#thText').value.trim()) throw new Error('Type the thumbnail text.');
  const fd = new FormData();
  fd.append('text', $('#thText').value); fd.append('layout', $('#thLayout').value); fd.append('accent', $('#thAccent').value);
  fd.append('arrow', $('#thArrow').value); fd.append('bg_prompt', $('#thPrompt').value);
  if ($('#thBg').files[0]) fd.append('bg', $('#thBg').files[0]);
  if ($('#thSubject').files[0]) fd.append('subject', $('#thSubject').files[0]);
  const r = await api('/api/thumbnail', { method: 'POST', body: fd });
  $('#thOut').innerHTML = `<img class="thumb" src="${r.url}"><div class="row" style="margin-top:10px"><a class="btn primary" href="${r.url}?download=1">⬇ Download</a><span class="muted small">${esc(r.note)}</span></div>`;
}).catch(err => $('#thErr').textContent = err.message);

// ---------- owner settings ----------
const S_TEXT = ['llm_provider', 'anthropic_key', 'anthropic_model', 'openai_base', 'openai_key', 'openai_model', 'pollinations_key', 'pexels_key', 'pixabay_key', 'lipsync_provider', 'did_key', 'script_rules'];
const S_NUM = ['words_per_minute', 'music_volume'], S_BOOL = ['use_pollinations', 'use_openverse'];
async function loadSettings() {
  settings = await api('/api/settings');
  S_TEXT.concat(S_NUM).forEach(k => $('#s_' + k).value = settings[k] ?? '');
  S_BOOL.forEach(k => $('#s_' + k).checked = !!settings[k]);
  $('#s_styles').value = JSON.stringify(settings.styles, null, 2);
  $('#sActive').textContent = '· now using: ' + settings.llm_active;
  $('#sMusicList').textContent = (settings.music_library || []).length ? 'Your tracks: ' + settings.music_library.join(', ') : 'No uploaded tracks yet. Built-in music is generated automatically.';
}
$('#sSave').onclick = e => busy(e.target, async () => {
  const patch = {};
  S_TEXT.forEach(k => patch[k] = $('#s_' + k).value.trim());
  S_NUM.forEach(k => patch[k] = +$('#s_' + k).value);
  S_BOOL.forEach(k => patch[k] = $('#s_' + k).checked);
  try { patch.styles = JSON.parse($('#s_styles').value); } catch { throw new Error('The styles box is not valid JSON. Check commas and quotes.'); }
  await api('/api/settings', { method: 'PUT', json: patch });
  await loadSettings(); renderStyles(); renderMusic();
  $('#aiWarn').classList.toggle('hidden', settings.llm_active !== 'none');
  $('#sMsg').textContent = 'Saved ✓';
}).catch(err => $('#sMsg').textContent = err.message);
$('#sReset').onclick = () => { $('#s_script_rules').value = settings.defaults.script_rules; $('#s_styles').value = JSON.stringify(settings.defaults.styles, null, 2); $('#sMsg').textContent = 'Defaults loaded. Press Save to keep them.'; };
$('#sMusic').onchange = async () => { const fd = new FormData(); fd.append('file', $('#sMusic').files[0]); await api('/api/music', { method: 'POST', body: fd }); loadSettings(); };
$('#sPwGo').onclick = async () => { try { await api('/api/password', { json: { password: $('#sPw').value } }); $('#sPw').value = ''; alert('Password changed.'); } catch (err) { alert(err.message); } };

showGate();
