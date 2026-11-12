// Timeline editor: tracks for video shots, on-screen text/graphics, voice (scenes), music, SFX and captions,
// plus an inspector with tools for whatever is selected. Saves back to the project and re-renders.
const ED = { p: null, scenes: [], look: {}, opts: null, sel: null, pps: 40, undo: [], music: '', captions: true, sfx: true, dirty: false };

function edSnapshot() { ED.undo.push(JSON.stringify({ s: ED.scenes, l: ED.look, m: ED.music, c: ED.captions, x: ED.sfx })); if (ED.undo.length > 60) ED.undo.shift(); ED.dirty = true; }
function edUndo() { const u = ED.undo.pop(); if (!u) return; const o = JSON.parse(u); ED.scenes = o.s; ED.look = o.l; ED.music = o.m; ED.captions = o.c; ED.sfx = o.x; edDraw(); }

async function openEditor(p) {
  ED.opts = ED.opts || await api('/api/editor-options');
  ED.p = p; ED.sel = null; ED.undo = []; ED.dirty = false;
  ED.look = JSON.parse(JSON.stringify(p.look || {}));
  ED.music = p.music || ''; ED.captions = p.captions !== false; ED.sfx = p.sfx !== false;
  const tl = p.timeline || [];
  ED.scenes = p.scenes.map((s, i) => ({
    _i: i, narration: s.narration, text: s.text || '', graphic: s.graphic || '', queries: s.queries || [], kind: s.kind || 'broll',
    image_prompt: s.image_prompt || '', start: s.start || 0, dur: s.dur || 3,
    trans: s.trans || ((tl.find(t => t.scene === i && t.k === 0) || {}).trans) || '',
    assets: (s.assets || []).map((a, k) => {
      const t = tl.find(x => x.scene === i && x.k === k) || {};
      return { path: a.path, type: a.type, source: a.source, credit: a.credit || '', move: a.move || t.move || '', filter: a.filter || '', speed: a.speed || 1, weight: a.weight || 1, b: a.b };
    })
  }));
  const fit = Math.max(8, Math.min(120, (document.body.clientWidth - 120) / Math.max(10, edTotal())));
  ED.pps = Math.round(fit);
  const base = `/media/${p.id}/`;
  $('#tab-project').innerHTML = `
  <div class="row"><h1 style="flex:1">✂️ ${esc(p.title)}</h1>
    <button class="btn small" id="edBack">← Back to video</button></div>
  <div class="ed-top">
    <div class="ed-view card"><video id="edVideo" controls src="${base}${p.video}?v=${p.version || 0}"></video>
      <div class="row small muted" style="margin-top:6px"><span id="edTime">0:00</span><span style="flex:1"></span>
      Zoom <input type="range" id="edZoom" min="6" max="160" value="${ED.pps}" style="max-width:160px"></div></div>
    <div class="ed-insp card" id="edInsp"></div>
  </div>
  <div class="card ed-toolbar row">
    <button class="btn small" id="edPlay">▶ / ❚❚</button>
    <button class="btn small" id="edUndo">↶ Undo</button>
    <button class="btn small" id="edLook">🎲 New look</button>
    <span class="muted small" id="edHint">Click any block to edit it. Drag voice blocks to reorder scenes.</span>
    <span style="flex:1"></span>
    <button class="btn small" id="edDraft">Render fast draft</button>
    <button class="btn primary small" id="edSave">💾 Save & render</button>
  </div>
  <div class="card ed-tl-wrap"><div class="ed-tl" id="edTl"></div></div>
  <p class="err" id="edErr"></p>`;
  $('#edBack').onclick = () => { if (!ED.dirty || confirm('Leave without saving your edits?')) renderProject(current = ED.p); };
  $('#edZoom').oninput = e => { ED.pps = +e.target.value; edDraw(); };
  $('#edPlay').onclick = () => { const v = $('#edVideo'); v.paused ? v.play() : v.pause(); };
  $('#edUndo').onclick = edUndo;
  $('#edLook').onclick = () => { edSnapshot(); ED.look.seed = Math.floor(Math.random() * 1e9); ED.look._regen = true; ED.sel = { t: 'look' }; edDraw(); };
  $('#edSave').onclick = () => edSave(false);
  $('#edDraft').onclick = () => edSave(true);
  const v = $('#edVideo');
  v.ontimeupdate = () => { $('#edTime').textContent = fmt(v.currentTime) || '0:00'; const ph = $('#edPh'); if (ph) ph.style.left = (60 + v.currentTime * ED.pps) + 'px'; };
  ED.sel = { t: 'look' };
  edDraw();
}

function edTotal() { return ED.scenes.reduce((a, s) => a + (s.dur || 3), 0); }
function edLayout() { let t = 0; ED.scenes.forEach(s => { s._st = t; t += s.dur || 3; }); return t; }

function edDraw() {
  const total = edLayout(), pps = ED.pps, W = Math.max(600, total * pps + 80), base = `/media/${ED.p.id}/`;
  const block = (x, w, cls, inner, data, title = '') => `<div class="blk ${cls}" style="left:${60 + x}px;width:${Math.max(6, w - 2)}px" ${data} title="${esc(title)}">${inner}</div>`;
  let shots = '', texts = '', voice = '', marks = '';
  ED.scenes.forEach((s, i) => {
    const wsum = s.assets.reduce((a, x) => a + (+x.weight || 1), 0) || 1;
    let x = s._st;
    s.assets.forEach((a, k) => {
      const d = (s.dur || 3) * (+a.weight || 1) / wsum;
      const on = ED.sel && ED.sel.t === 'shot' && ED.sel.i === i && ED.sel.k === k;
      const bg = a.type === 'image' || a.type === 'split' && a.b ? `background-image:url('${base}${a.type === 'split' ? a.b : a.path}')` : '';
      const label = a.source === 'motion graphic' ? '📊' : a.type === 'video' || a.type === 'split' ? '🎬' : '🖼️';
      shots += `<div class="blk shot ${on ? 'on' : ''}" style="left:${60 + x * pps}px;width:${Math.max(6, d * pps - 2)}px;${bg}" data-t="shot" data-i="${i}" data-k="${k}" title="${esc(a.source || '')} · ${esc(a.move || '')}${a.filter ? ' · ' + esc(a.filter) : ''}">
        <span>${label} ${esc(a.move || '')}${a.filter ? ' · ' + esc(a.filter) : ''}${(+a.speed || 1) !== 1 ? ' · ' + a.speed + 'x' : ''}</span></div>`;
      x += d;
    });
    if (i > 0) marks += `<div class="trans ${ED.sel && ED.sel.t === 'trans' && ED.sel.i === i ? 'on' : ''}" style="left:${60 + s._st * pps - 9}px" data-t="trans" data-i="${i}" title="Transition: ${esc(s.trans || 'auto')}">${s.trans === 'cut' ? '|' : '◆'}</div>`;
    if (s.text || s.graphic) texts += block(s._st * pps, (s.dur || 3) * pps, 'txt' + (ED.sel && ED.sel.t === 'scene' && ED.sel.i === i ? ' on' : ''),
      `<span>${s.graphic ? '📊 ' + esc(s.graphic) : '🔤 ' + esc(s.text)}</span>`, `data-t="scene" data-i="${i}"`);
    voice += block(s._st * pps, (s.dur || 3) * pps, 'voice' + (ED.sel && ED.sel.t === 'scene' && ED.sel.i === i ? ' on' : '') + (s.kind === 'aroll' ? ' aroll' : ''),
      `<span>${i + 1}. ${esc(s.narration)}</span>`, `data-t="scene" data-i="${i}" draggable="true"`, s.narration);
  });
  let ruler = '';
  const step = pps > 60 ? 1 : pps > 25 ? 5 : pps > 10 ? 10 : 30;
  for (let t = 0; t <= total; t += step) ruler += `<span style="left:${60 + t * pps}px">${fmt(t) || '0:00'}</span>`;
  const sel = t => ED.sel && ED.sel.t === t ? ' on' : '';
  const L = ED.look;
  $('#edTl').style.width = W + 'px';
  $('#edTl').innerHTML = `
    <div class="ruler" id="edRuler">${ruler}</div>
    <div class="track"><b>Video</b>${shots}${marks}</div>
    <div class="track"><b>Text</b>${texts}</div>
    <div class="track"><b>Voice</b>${voice}</div>
    <div class="track"><b>Music</b>${block(0, total * pps, 'music' + sel('music'), `<span>🎵 ${esc(ED.music || 'auto')} · vol ${L.music_volume ?? 'auto'}</span>`, 'data-t="music"')}</div>
    <div class="track"><b>SFX</b>${block(0, total * pps, 'sfx' + sel('sfx') + (ED.sfx ? '' : ' off'), `<span>🔊 ${ED.sfx ? 'Sound effects on' : 'off'} · vol ${L.sfx_volume ?? 1}</span>`, 'data-t="sfx"')}</div>
    <div class="track"><b>Captions</b>${block(0, total * pps, 'caps' + sel('look') + (ED.captions ? '' : ' off'), `<span>💬 ${ED.captions ? esc(L.caption_style || 'karaoke') + ' · ' + esc(L.font || '') : 'off'}</span>`, 'data-t="look"')}</div>
    <div class="ph" id="edPh" style="left:${60 + ($('#edVideo') ? $('#edVideo').currentTime : 0) * pps}px"></div>`;
  $$('#edTl [data-t]').forEach(el => el.onclick = e => {
    e.stopPropagation();
    ED.sel = { t: el.dataset.t, i: +el.dataset.i, k: +el.dataset.k };
    if (el.dataset.i !== undefined) { const s = ED.scenes[+el.dataset.i]; if (s && $('#edVideo')) $('#edVideo').currentTime = s._st + 0.05; }
    edDraw();
  });
  $('#edRuler').onclick = e => { const r = $('#edTl').getBoundingClientRect(); $('#edVideo').currentTime = Math.max(0, (e.clientX - r.left - 60) / pps); };
  // drag voice blocks to reorder scenes
  $$('#edTl .voice').forEach(el => {
    el.ondragstart = e => e.dataTransfer.setData('text/plain', el.dataset.i);
    el.ondragover = e => e.preventDefault();
    el.ondrop = e => {
      e.preventDefault(); const from = +e.dataTransfer.getData('text/plain'), to = +el.dataset.i;
      if (from === to) return; edSnapshot();
      const [s] = ED.scenes.splice(from, 1); ED.scenes.splice(to, 0, s); ED.sel = { t: 'scene', i: to }; edDraw();
    };
  });
  edInspector();
}

const opt = (list, val, labels) => list.map(x => `<option value="${esc(x)}" ${x === val ? 'selected' : ''}>${esc(labels ? labels[x] || x : x || '(auto)')}</option>`).join('');

function edInspector() {
  const el = $('#edInsp'), s = ED.sel || {}, O = ED.opts, base = `/media/${ED.p.id}/`;
  if (s.t === 'shot') {
    const sc = ED.scenes[s.i], a = sc.assets[s.k];
    if (!a) { ED.sel = null; return edInspector(); }
    const src = a.type === 'split' ? a.b : a.path;
    el.innerHTML = `<h3>Shot ${s.k + 1} of scene ${s.i + 1}</h3>
      <div class="ed-prev">${a.type === 'image' ? `<img src="${base}${src}">` : `<video src="${base}${a.path}#t=0.5" muted controls></video>`}</div>
      <div class="muted small">${esc(a.source || '')} ${a.credit ? '· ' + esc(a.credit) : ''}</div>
      <div class="grid2">
        <div><label>Camera move</label><select data-f="move">${opt(['', ...O.moves], a.move)}</select></div>
        <div><label>Effect / filter</label><select data-f="filter">${opt(O.filters, a.filter || 'none')}</select></div>
        <div><label>Speed (video clips)</label><select data-f="speed">${opt(['0.5', '0.75', '1', '1.25', '1.5'], String(a.speed || 1))}</select></div>
        <div><label>Length share in scene</label><input type="range" data-f="weight" min="0.25" max="4" step="0.25" value="${a.weight || 1}"></div>
      </div>
      <label>Replace this visual</label>
      <div class="row"><input id="edQ" placeholder="Search stock video & photos…" value="${esc((sc.queries || [])[0] || '')}"><select id="edQk" style="max-width:110px"><option value="all">All</option><option value="video">Videos</option><option value="photo">Photos</option></select><button class="btn small" id="edFind">Search</button></div>
      <div class="row" style="margin-top:6px"><input id="edAi" placeholder="…or describe an AI image" value="${esc(sc.image_prompt || '')}"><button class="btn small" id="edGen">Generate</button></div>
      <div class="row" style="margin-top:6px"><label class="btn small" style="margin:0">⬆ Upload<input type="file" id="edUp" accept="image/*,video/*" hidden></label></div>
      <div class="cands" id="edCands"></div>
      <div class="row" style="margin-top:12px"><button class="btn small" id="edDup">➕ Duplicate shot</button><button class="btn small danger" id="edDel">🗑 Delete shot</button>
      <button class="btn small" id="edLeft">◀ Move</button><button class="btn small" id="edRight">Move ▶</button></div>`;
    $$('#edInsp [data-f]').forEach(c => c.onchange = c.oninput = () => {
      edSnapshot(); a[c.dataset.f] = c.dataset.f === 'filter' && c.value === 'none' ? '' : (c.dataset.f === 'speed' || c.dataset.f === 'weight') ? +c.value : c.value; edDraw();
    });
    const setAsset = r => { edSnapshot(); sc.assets[s.k] = { ...a, path: r.path, type: r.type, source: r.source, credit: r.credit || '', b: undefined }; edDraw(); };
    $('#edFind').onclick = e => busy(e.target, async () => {
      const r = await api(`/api/projects/${ED.p.id}/candidates`, { json: { query: $('#edQ').value, kind: $('#edQk').value } });
      $('#edCands').innerHTML = r.items.length ? r.items.map((x, n) => `<div class="cand" data-n="${n}" style="background-image:url('${esc(x.preview || x.url)}')"><span>${x.type === 'video' ? '🎬' : '🖼️'}</span></div>`).join('')
        : `<p class="muted small">Nothing found. ${esc((r.errors || []).join(' · ') || 'Add Pexels / Pixabay keys in the Owner panel for stock video.')}</p>`;
      $$('#edCands .cand').forEach(c => c.onclick = () => busy(c, async () => {
        const x = r.items[+c.dataset.n];
        setAsset(await api(`/api/projects/${ED.p.id}/pick`, { json: { url: x.url, type: x.type, kind: x.kind, credit: x.credit } }));
      }).catch(err => alert(err.message)));
    }).catch(err => alert(err.message));
    $('#edGen').onclick = e => busy(e.target, async () => setAsset(await api(`/api/projects/${ED.p.id}/pick`, { json: { prompt: $('#edAi').value, aspect: ED.p.aspect } }))).catch(err => alert(err.message));
    $('#edUp').onchange = async () => { const fd = new FormData(); fd.append('file', $('#edUp').files[0]); try { setAsset(await api(`/api/projects/${ED.p.id}/upload`, { method: 'POST', body: fd })); } catch (err) { alert(err.message); } };
    $('#edDup').onclick = () => { edSnapshot(); sc.assets.splice(s.k + 1, 0, { ...a }); ED.sel.k = s.k + 1; edDraw(); };
    $('#edDel').onclick = () => { if (sc.assets.length < 2) return alert('A scene needs at least one shot. Replace it instead, or delete the scene.'); edSnapshot(); sc.assets.splice(s.k, 1); ED.sel = null; edDraw(); };
    $('#edLeft').onclick = () => { if (s.k < 1) return; edSnapshot(); [sc.assets[s.k - 1], sc.assets[s.k]] = [sc.assets[s.k], sc.assets[s.k - 1]]; ED.sel.k--; edDraw(); };
    $('#edRight').onclick = () => { if (s.k >= sc.assets.length - 1) return; edSnapshot(); [sc.assets[s.k + 1], sc.assets[s.k]] = [sc.assets[s.k], sc.assets[s.k + 1]]; ED.sel.k++; edDraw(); };
    return;
  }
  if (s.t === 'trans') {
    const sc = ED.scenes[s.i];
    el.innerHTML = `<h3>Transition into scene ${s.i + 1}</h3><label>Type</label><select id="edTr">${opt(['', ...O.transitions], sc.trans, { '': '(automatic)' })}</select>
      <p class="muted small">“cut” is a hard cut. Others blend the two shots over half a second.</p>
      <button class="btn small" id="edTrAll">Use this transition everywhere</button>`;
    $('#edTr').onchange = () => { edSnapshot(); sc.trans = $('#edTr').value; edDraw(); };
    $('#edTrAll').onclick = () => { edSnapshot(); ED.scenes.forEach((x, n) => { if (n) x.trans = sc.trans; }); edDraw(); };
    return;
  }
  if (s.t === 'scene') {
    const sc = ED.scenes[s.i];
    el.innerHTML = `<h3>Scene ${s.i + 1} <span class="muted small">${fmt(sc._st) || '0:00'} · ${(sc.dur || 0).toFixed(1)}s</span></h3>
      <label>Narration (changing it re-records this part of the voice)</label><textarea id="edNar" rows="4">${esc(sc.narration)}</textarea>
      <label>On-screen text</label><input id="edTxt" value="${esc(sc.text)}" placeholder="Big text / number for this scene">
      <label>Motion graphic</label><div class="row"><select id="edGfxT" style="max-width:140px"><option value="">None</option>${Object.keys(O.graphics).map(k => `<option value="${k}">${k}</option>`).join('')}</select>
      <input id="edGfx" value="${esc(sc.graphic)}" placeholder="e.g. map: Egypt"></div><p class="muted small" id="edGfxHelp"></p>
      ${(ED.p.style || '').startsWith('avatar') ? `<label>Shot type</label><select id="edKind"><option value="broll">B-roll</option><option value="aroll" ${sc.kind === 'aroll' ? 'selected' : ''}>A-roll (host)</option></select>` : ''}
      <label>B-roll search words</label><input id="edQs" value="${esc((sc.queries || []).join(', '))}">
      <div class="row" style="margin-top:12px"><button class="btn small" id="edSplit">✂️ Split scene</button><button class="btn small" id="edMerge">⤵ Merge with next</button>
      <button class="btn small" id="edUp1">▲</button><button class="btn small" id="edDn1">▼</button><button class="btn small danger" id="edDelS">🗑 Delete scene</button></div>`;
    const t0 = $('#edGfx').value.split(':')[0].trim(); if (O.graphics[t0]) $('#edGfxT').value = t0;
    $('#edGfxT').onchange = () => { const k = $('#edGfxT').value; $('#edGfxHelp').textContent = k ? 'Format: ' + O.graphics[k] : ''; if (k && !$('#edGfx').value.startsWith(k + ':')) $('#edGfx').value = k + ': '; if (!k) $('#edGfx').value = ''; $('#edGfx').focus(); };
    const bind = (id, f, tr = x => x) => { $(id).onchange = () => { edSnapshot(); sc[f] = tr($(id).value); if (f === 'graphic' || f === 'queries') sc.assets = sc.assets.filter(a => a.source !== 'motion graphic').length ? sc.assets.filter(a => a.source !== 'motion graphic') : sc.assets; if (f === 'graphic') sc._gfx = true; edDraw(); }; };
    bind('#edNar', 'narration'); bind('#edTxt', 'text'); bind('#edGfx', 'graphic'); bind('#edQs', 'queries', v => v.split(',').map(x => x.trim()).filter(Boolean));
    if ($('#edKind')) bind('#edKind', 'kind');
    $('#edSplit').onclick = () => {
      const sents = sc.narration.match(/[^.!?।]+[.!?।]*\s*/g) || [sc.narration];
      if (sents.length < 2) return alert('This scene has only one sentence.');
      edSnapshot(); const cut = Math.ceil(sents.length / 2);
      const a1 = sc.assets.slice(0, Math.ceil(sc.assets.length / 2)), a2 = sc.assets.length > 1 ? sc.assets.slice(a1.length) : sc.assets.map(x => ({ ...x }));
      const ns = { ...sc, _i: undefined, narration: sents.slice(cut).join('').trim(), text: '', graphic: '', assets: a2, trans: '', dur: sc.dur / 2 };
      Object.assign(sc, { narration: sents.slice(0, cut).join('').trim(), assets: a1, dur: sc.dur / 2 });
      ED.scenes.splice(s.i + 1, 0, ns); edDraw();
    };
    $('#edMerge').onclick = () => { const nx = ED.scenes[s.i + 1]; if (!nx) return; edSnapshot(); sc.narration += ' ' + nx.narration; sc.assets = sc.assets.concat(nx.assets); sc.dur += nx.dur; ED.scenes.splice(s.i + 1, 1); edDraw(); };
    $('#edUp1').onclick = () => { if (!s.i) return; edSnapshot(); [ED.scenes[s.i - 1], ED.scenes[s.i]] = [ED.scenes[s.i], ED.scenes[s.i - 1]]; ED.sel.i--; edDraw(); };
    $('#edDn1').onclick = () => { if (s.i >= ED.scenes.length - 1) return; edSnapshot(); [ED.scenes[s.i + 1], ED.scenes[s.i]] = [ED.scenes[s.i], ED.scenes[s.i + 1]]; ED.sel.i++; edDraw(); };
    $('#edDelS').onclick = () => { if (ED.scenes.length < 2) return; edSnapshot(); ED.scenes.splice(s.i, 1); ED.sel = null; edDraw(); };
    return;
  }
  if (s.t === 'music') {
    el.innerHTML = `<h3>Music</h3><label>Track</label><select id="edMus">${musicOptions(ED.music)}</select>
      <label>Volume under the voice: <b id="edMvL">${ED.look.music_volume ?? 'auto'}</b></label><input type="range" id="edMv" min="0" max="0.6" step="0.02" value="${ED.look.music_volume ?? 0.2}">
      <p class="muted small">Music ducks automatically under the narration. 🎲 New look also changes the key and chords.</p>
      <label>Voice volume</label><input type="range" id="edVv" min="0.5" max="1.6" step="0.05" value="${ED.look.voice_volume ?? 1}">`;
    $('#edMus').onchange = () => { edSnapshot(); ED.music = $('#edMus').value; edDraw(); };
    $('#edMv').oninput = () => { ED.look.music_volume = +$('#edMv').value; $('#edMvL').textContent = ED.look.music_volume; ED.dirty = true; };
    $('#edMv').onchange = () => edDraw();
    $('#edVv').onchange = () => { edSnapshot(); ED.look.voice_volume = +$('#edVv').value; };
    return;
  }
  if (s.t === 'sfx') {
    el.innerHTML = `<h3>Sound effects</h3><label class="check"><input type="checkbox" id="edSfx" ${ED.sfx ? 'checked' : ''}> Whooshes, hits, risers, pops</label>
      <label>Volume</label><input type="range" id="edSv" min="0" max="2" step="0.1" value="${ED.look.sfx_volume ?? 1}">`;
    $('#edSfx').onchange = () => { edSnapshot(); ED.sfx = $('#edSfx').checked; edDraw(); };
    $('#edSv').onchange = () => { edSnapshot(); ED.look.sfx_volume = +$('#edSv').value; edDraw(); };
    return;
  }
  // look / captions
  const L = ED.look;
  el.innerHTML = `<h3>Look & captions</h3>
    <label class="check"><input type="checkbox" id="edCap" ${ED.captions ? 'checked' : ''}> Captions</label>
    <div class="grid2">
      <div><label>Caption style</label><select id="edCs">${opt(Object.keys(O.caption_styles), L.caption_style, O.caption_styles)}</select></div>
      <div><label>Position</label><select id="edCp">${opt(['bottom', 'lower', 'middle'], L.caption_pos)}</select></div>
      <div><label>Font</label><select id="edFont">${opt(O.fonts, L.font)}</select></div>
      <div><label>Title style</label><select id="edTs">${opt(O.title_styles, L.title_style)}</select></div>
      <div><label>Accent colour</label><input type="color" id="edAcc" value="${esc(L.accent || '#FFD400')}"></div>
      <div><label>Colour grade (whole video)</label><select id="edGr">${opt(O.filters, L.grade || 'none')}</select></div>
    </div>
    <div class="swatch">${O.palettes.map(c => `<i style="background:${c}" data-c="${c}"></i>`).join('')}</div>
    <p class="muted small">${L._regen ? '🎲 A new random look will be generated on render (fonts, colours, transitions, moves, music).' : 'Every video gets its own look. Change anything here, or press 🎲 New look.'}</p>`;
  const set = (id, f, tr = x => x) => $(id).onchange = () => { edSnapshot(); L[f] = tr($(id).value); delete L._regen; edDraw(); };
  set('#edCs', 'caption_style'); set('#edCp', 'caption_pos'); set('#edFont', 'font'); set('#edTs', 'title_style'); set('#edAcc', 'accent');
  set('#edGr', 'grade', v => v === 'none' ? '' : v);
  $('#edCap').onchange = () => { edSnapshot(); ED.captions = $('#edCap').checked; edDraw(); };
  $$('.swatch i').forEach(i => i.onclick = () => { edSnapshot(); L.accent = i.dataset.c; delete L._regen; edDraw(); });
}

async function edSave(preview) {
  $('#edErr').textContent = '';
  const look = { ...ED.look };
  if (look._regen) { delete look._regen; look.regen_seed = look.seed; }
  const body = {
    render: true, preview, music: ED.music, captions: ED.captions, sfx: ED.sfx, look,
    scenes: ED.scenes.map(s => ({
      _i: s._i, narration: s.narration, text: s.text, graphic: s.graphic, queries: s.queries, kind: s.kind, image_prompt: s.image_prompt,
      trans: s.trans, assets: s._gfx ? undefined : s.assets.map(a => ({ path: a.path, type: a.type, source: a.source, credit: a.credit, move: a.move, filter: a.filter, speed: a.speed, weight: a.weight }))
    }))
  };
  try { await api('/api/projects/' + ED.p.id, { method: 'PUT', json: body }); ED.dirty = false; current = null; refreshProject(ED.p.id); }
  catch (err) { $('#edErr').textContent = err.message; }
}
