// Home (prompt-first, like Vidrush) + Brand profiles.
let profiles = [], profileId = '', planInfo = null;

async function loadProfiles() {
  profiles = await api('/api/profiles');
  if (!profiles.find(p => p.id === profileId)) profileId = (profiles[0] || {}).id || '';
  $('#hProfile').innerHTML = profiles.length ? profiles.map(p => `<option value="${p.id}" ${p.id === profileId ? 'selected' : ''}>${esc(p.name)}</option>`).join('')
    : '<option value="">No brand profile yet</option>';
}
async function loadHome() {
  await loadProfiles();
  const list = await api('/api/projects');
  $('#hRecent').innerHTML = list.slice(0, 8).map(p => `<div class="recent" data-id="${p.id}">
      <div class="rth" ${p.thumb ? `style="background-image:url(/media/${p.id}/${p.thumb})"` : ''}></div>
      <div style="flex:1"><b>${esc(p.title)}</b><div class="muted small">${new Date((p.created || 0) * 1000).toLocaleString()}</div></div>
      <span class="badge ${p.status}">${p.status === 'done' ? 'Ready · Edit' : p.status === 'error' ? 'Failed' : 'Processing ' + (p.progress || 0) + '%'}</span></div>`).join('')
    || '<p class="muted">Your videos will appear here.</p>';
  $$('#hRecent .recent').forEach(r => r.onclick = () => openProject(r.dataset.id));
}
$('#hProfile').onchange = () => profileId = $('#hProfile').value;
$('#hPrompt').oninput = () => $('#hCount').textContent = `${$('#hPrompt').value.length.toLocaleString()} / 10,000`;
$('#hAvatar').onclick = () => { tab('create'); style = 'avatar'; renderStyles(); applyStyleDefaults(); goStep(1); };
$('#hTalking').onclick = () => { tab('create'); style = 'avatar'; renderStyles(); applyStyleDefaults(); goStep(3); };
$('#hGo').onclick = e => busy(e.target, async () => {
  $('#hErr').textContent = '';
  const prompt = $('#hPrompt').value.trim();
  if (!prompt) throw new Error('Describe the video you want, or paste your full prompt / scene breakdown.');
  planInfo = await api('/api/plan', { json: { prompt, profile_id: profileId } });
  applyPlan(planInfo, profiles.find(p => p.id === profileId));
  tab('create'); goStep(5);
}).catch(err => $('#hErr').textContent = err.message);

function applyPlan(pl, prof) {
  $('#cTitle').value = pl.title;
  $('#cMinutes').value = pl.minutes; $('#cMinutes').oninput();
  if (settings.styles[pl.format]) { style = pl.format; renderStyles(); applyStyleDefaults(); }
  const lang = [...$('#cLang').options].find(o => o.value.toLowerCase().startsWith((pl.language || '').toLowerCase()));
  if (lang) $('#cLang').value = lang.value;
  $('#cNotes').value = [pl.tone ? 'Tone: ' + pl.tone : '', pl.notes].filter(Boolean).join('\n\n');
  if (prof) {
    if (prof.voice && voices.find(v => v.id === prof.voice)) voiceSel = prof.voice;
    if (prof.age) $('#vfAge').value = prof.age;
    $('#cRate').value = String(prof.rate || 0);
    $('#cCaptions').value = prof.captions === false ? '0' : '1';
    $('#cSfx').checked = prof.sfx !== false;
    if (prof.music) $('#cMusic').value = prof.music;
    $('#cAspect').value = prof.aspect || '16:9';
    $('#cQuality').value = prof.quality || 'full';
    if (prof.persona) $('#cPersona').value = prof.persona;
    if (prof.style_text) $('#cStyleText').value = prof.style_text;
    if (prof.graphics) { gfxSel = new Set(prof.graphics); renderGfx(); }
  }
  renderVoices();
}

// ---------------- brand profiles ----------------
let profEdit = null;
async function loadProfilesTab() {
  await loadProfiles();
  $('#bpList').innerHTML = profiles.map(p => `<div class="recent" data-id="${p.id}"><div style="flex:1"><b>${esc(p.name)}</b>
     <div class="muted small">${esc(p.theme)} · ${esc(p.language)}${p.reference ? ' · editing style learned ✓' : ''}</div></div><span class="btn small">Edit</span></div>`).join('')
    || '<p class="muted">No profiles yet. A brand profile keeps the voice, look, rules and editing style of one channel.</p>';
  $$('#bpList .recent').forEach(r => r.onclick = () => editProfile(profiles.find(p => p.id === r.dataset.id)));
}
$('#bpNew').onclick = () => editProfile({ name: '', language: 'English', theme: 'standard', captions: true, sfx: true, aspect: '16:9', quality: 'full', rate: 0,
  sources: { stock_video: true, stock_photo: true, ai_image: true, commons: true } });
function editProfile(p) {
  profEdit = JSON.parse(JSON.stringify(p));
  const vopts = voices.slice(0, 400).map(v => `<option value="${esc(v.id)}" ${v.id === p.voice ? 'selected' : ''}>${esc(v.name)} · ${esc(v.gender)} · ${esc(v.lang)}${v.provider === 'elevenlabs' ? ' · Premium' : ''}</option>`).join('');
  const themes = { standard: 'Standard documentary', history: 'History', crime: 'Crime / mystery', modern: 'Modern news', minimalist: 'Minimalist facts',
    space_ocean: 'Space & ocean', sleep: 'Sleep', avatar: 'AI avatar', stickman: '2D stickman', animated: 'Animated', top10: 'Top 10', motivation: 'Motivational' };
  const ref = p.reference;
  const st = ref && ref.script_style && typeof ref.script_style === 'object' ? ref.script_style : null;
  $('#bpEdit').innerHTML = `<div class="card">
    <div class="row"><h3 style="flex:1;margin:0">${p.id ? 'Edit' : 'New'} brand profile</h3>${p.id ? '<button class="btn small danger" id="bpDel">Delete</button>' : ''}</div>
    <div class="grid3">
      <div><label>Profile name</label><input id="bpName" value="${esc(p.name)}" placeholder="e.g. Stacey Hollywood"></div>
      <div><label>Video language</label><input id="bpLang" value="${esc(p.language)}"></div>
      <div><label>Theme</label><select id="bpTheme">${Object.entries(themes).map(([k, l]) => `<option value="${k}" ${k === p.theme ? 'selected' : ''}>${l}</option>`).join('')}</select></div>
    </div>
    <h3>Voiceover</h3>
    <div class="grid3"><div style="grid-column:span 2"><label>Voice</label><select id="bpVoice"><option value="">(default)</option>${vopts}</select></div>
      <div><label>Age tone</label><select id="bpAge"><option value="">Natural</option>${Object.entries(ages).map(([k, a]) => `<option value="${k}" ${k === p.age ? 'selected' : ''}>${esc(a.label)}</option>`).join('')}</select></div></div>
    <h3>Creative assets</h3>
    <div class="grid3"><div><label>Music</label><select id="bpMusic">${musicOptions(p.music)}</select></div>
      <div><label>Captions</label><select id="bpCap"><option value="1">On</option><option value="0" ${p.captions === false ? 'selected' : ''}>Off</option></select></div>
      <div><label>Shape</label><select id="bpAspect"><option>16:9</option><option ${p.aspect === '9:16' ? 'selected' : ''}>9:16</option><option ${p.aspect === '1:1' ? 'selected' : ''}>1:1</option></select></div></div>
    <label>Describe the look (optional)</label><input id="bpStyleText" value="${esc(p.style_text || '')}" placeholder="e.g. archival photos, slow zooms, deep serious narrator">
    <label>Persona / host notes (optional)</label><textarea id="bpPersona" rows="2">${esc(p.persona || '')}</textarea>
    <h3>Block listing & compliance</h3>
    <div class="row">${[['stock_video', 'Stock video'], ['stock_photo', 'Stock photos'], ['ai_image', 'AI images'], ['commons', 'Creative Commons / public domain']].map(([k, l]) =>
      `<label class="check"><input type="checkbox" data-src="${k}" ${(p.sources || {})[k] !== false ? 'checked' : ''}> ${l}</label>`).join('')}</div>
    <label>Never show or say (comma separated)</label><input id="bpBlock" value="${esc(p.block_words || '')}" placeholder="e.g. blood, weapons, brand names">
    <label>Blocked web sources (domains, comma separated)</label><input id="bpDomains" value="${esc(p.block_domains || '')}" placeholder="e.g. flickr.com">
    <div class="row" style="margin-top:14px"><button class="btn primary" id="bpSave">Save brand profile</button><span class="muted small" id="bpMsg"></span></div>
  </div>
  <div class="card"><h3>Editing style (train on a video)</h3>
    <p class="muted small">Give a reference video that shows the editing and script style you want. The studio studies its pace, cuts, colour and narration voice, then makes your videos in that spirit with its own flair (never a copy).${p.id ? '' : ' Save the profile first.'}</p>
    <div class="grid3"><div><label>Reference video file (mp4)</label><input type="file" id="bpRefFile" accept="video/*"></div>
      <div><label>Reference link (YouTube)</label><input id="bpRefUrl" placeholder="https://www.youtube.com/watch?v=…" value="${esc(((ref || {}).meta || {}).url || '')}"></div>
      <div><label>&nbsp;</label><button class="btn" id="bpAnalyse" ${p.id ? '' : 'disabled'}>🔍 Analyse</button></div></div>
    <label>Transcript of the reference (paste it to learn the script style)</label><textarea id="bpRefText" rows="4" placeholder="Paste the reference video's narration…"></textarea>
    <div id="bpRef">${ref ? refSummary(ref, st) : ''}</div>
  </div>`;
  $('#bpSave').onclick = e => busy(e.target, async () => {
    const body = { ...profEdit, name: $('#bpName').value, language: $('#bpLang').value, theme: $('#bpTheme').value, voice: $('#bpVoice').value, age: $('#bpAge').value,
      music: $('#bpMusic').value, captions: $('#bpCap').value === '1', aspect: $('#bpAspect').value, style_text: $('#bpStyleText').value, persona: $('#bpPersona').value,
      block_words: $('#bpBlock').value, block_domains: $('#bpDomains').value,
      sources: Object.fromEntries($$('[data-src]').map(c => [c.dataset.src, c.checked])) };
    const saved = await api('/api/profiles', { json: body });
    profileId = saved.id; $('#bpMsg').textContent = 'Saved ✓'; await loadProfilesTab(); editProfile(saved);
  }).catch(err => $('#bpMsg').textContent = err.message);
  if ($('#bpDel')) $('#bpDel').onclick = async () => { if (confirm('Delete this brand profile?')) { await api('/api/profiles/' + p.id, { method: 'DELETE' }); $('#bpEdit').innerHTML = ''; loadProfilesTab(); } };
  $('#bpAnalyse').onclick = e => busy(e.target, async () => {
    const fd = new FormData();
    if ($('#bpRefFile').files[0]) fd.append('file', $('#bpRefFile').files[0]);
    fd.append('url', $('#bpRefUrl').value); fd.append('transcript', $('#bpRefText').value);
    const saved = await api(`/api/profiles/${p.id}/reference`, { method: 'POST', body: fd });
    editProfile(saved); loadProfilesTab();
  }).catch(err => alert(err.message));
}
function refSummary(ref, st) {
  const v = ref.video, s = ref.script_stats, set = ref.settings || {};
  return `<div class="refbox">${ref.meta && ref.meta.thumb ? `<img src="${esc(ref.meta.thumb)}">` : ''}<div>
    <b>Reference analysed ✓</b>${ref.meta && ref.meta.title ? `<div class="small">${esc(ref.meta.title)}</div>` : ''}
    ${v ? `<div class="small muted">Shot every ~${v.avg_shot_seconds}s · ${v.cuts_per_minute} cuts/min · ${v.soft_transition_ratio > 0.35 ? 'soft transitions' : 'hard cuts'} · brightness ${v.brightness} · saturation ${v.saturation}</div>` : ''}
    ${s ? `<div class="small muted">${s.words_per_minute ? s.words_per_minute + ' words/min · ' : ''}${s.avg_sentence_words} words per sentence · ${s.numbers_per_100_words} numbers per 100 words</div>` : ''}
    ${st ? `<div class="small" style="margin-top:6px"><b>Style summary:</b> ${esc(st.summary || '')}<br><b>Mood:</b> ${esc(st.mood || '')} · <b>Voice & tone:</b> ${esc(st.voice_and_tone || '')}<br><b>Structure:</b> ${esc(st.structure || '')}</div>` : ''}
    <div class="small muted" style="margin-top:6px">Applied: shots ${set.shot_seconds || 'auto'}s · ${(set.transitions || []).filter(Boolean).join(', ') || 'hard cuts'} · grade ${esc(set.grade || 'none')}</div></div></div>`;
}
