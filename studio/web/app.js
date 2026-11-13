/* FrameForge Studio — app shell, wizard and tool pages */
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fileUrl = (p, dl) => p ? "/api/file?path=" + encodeURIComponent(p) + (dl ? "&download=" + encodeURIComponent(dl) : "") : "";
const fmtT = t => { t = Math.max(0, Math.floor(t || 0)); return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0"); };
const ago = ts => { const d = Date.now() / 1000 - ts; return d < 90 ? "just now" : d < 3600 ? Math.round(d / 60) + " min ago" : d < 86400 ? Math.round(d / 3600) + " h ago" : Math.round(d / 86400) + " d ago"; };
const views = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "K" : String(n || 0);
const S = { cat: null, voices: [], more: [], brands: [], projects: [], W: null, timer: null };
const ICON = {
  plus: '<path d="M12 5v14M5 12h14"/>', home: '<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>', film: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
  type: '<path d="M4 6V4h16v2M12 4v16M8 20h8"/>', image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5L5 20"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', id: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="12" r="2.5"/><path d="M14 10h4M14 14h4"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 21V5"/>', gear: '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.3l2-1.5-2-3.4-2.3 1a7 7 0 0 0-2.2-1.3L14 3h-4l-.4 2.5a7 7 0 0 0-2.2 1.3l-2.3-1-2 3.4 2 1.500A7 7 0 0 0 5 12c0 .4 0 .9.1 1.3l-2 1.5 2 3.400 2.300-1a7 7 0 0 0 2.200 1.300L10 21h4l.4-2.500a7 7 0 0 0 2.200-1.300l2.300 1 2-3.400-2-1.500c.1-.4.1-.9.1-1.300z"/>',
  play: '<path d="M7 4l13 8-13 8z" fill="currentColor"/>', stop: '<rect x="6" y="6" width="12" height="12" fill="currentColor"/>', dl: '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>', cut: '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.500 8l11.500 9M8.500 16L20 7"/>', swap: '<path d="M4 8h14l-4-4M20 16H6l4 4"/>',
  wand: '<path d="M4 20L16 8M14 4l1 2 2 1-2 1-1 2-1-2-2-1 2-1zM19 12l.7 1.300L21 14l-1.300.7L19 16l-.7-1.300L17 14l1.300-.7z"/>', check: '<path d="M4 12l5 5L20 6"/>', x: '<path d="M5 5l14 14M19 5L5 19"/>', copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M4 16V5a1 1 0 0 1 1-1h11"/>',
};
const ico = n => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.800" stroke-linecap="round" stroke-linejoin="round">${ICON[n] || ""}</svg>`;

async function api(path, opt = {}) {
  const o = { method: opt.method || (opt.body ? "POST" : "GET"), headers: {} };
  if (opt.body instanceof FormData) o.body = opt.body; else if (opt.body) { o.body = JSON.stringify(opt.body); o.headers["content-type"] = "application/json"; }
  const r = await fetch("/api" + path, o);
  if (r.status === 401) { showLogin(); throw new Error("Login required"); }
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch (e) { } throw new Error(typeof m === "string" ? m : JSON.stringify(m)); }
  return r.json();
}
function toast(msg, kind = "") { const d = document.createElement("div"); d.className = "toast " + kind; d.textContent = msg; $("#toasts").append(d); setTimeout(() => d.remove(), kind === "bad" ? 7000 : 3500); }
async function busy(btn, fn) { const old = btn ? btn.innerHTML : ""; if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spin"></span> ' + old; } try { return await fn(); } catch (e) { toast(e.message, "bad"); } finally { if (btn) { btn.disabled = false; btn.innerHTML = old; } } }
function modal(html) { const m = $("#modal"); m.innerHTML = `<div class="mbox">${html}</div>`; m.classList.remove("hidden"); m.onclick = e => { if (e.target === m) closeModal(); }; return m; }
function closeModal() { $("#modal").classList.add("hidden"); $("#modal").innerHTML = ""; }
function showLogin() { modal(`<h2>Owner login</h2><p class="dim">This studio is private.</p><input type="password" id="pw" placeholder="Password"><div class="row" style="margin-top:12px"><button class="btn pri" id="pwgo">Enter</button></div>`); $("#pwgo").onclick = async () => { try { await api("/login", { body: { password: $("#pw").value } }); closeModal(); location.reload(); } catch (e) { toast("Wrong password", "bad"); } }; }
function copyText(t) { navigator.clipboard?.writeText(t).then(() => toast("Copied", "ok"), () => toast("Select and copy manually")); }

const NAV = [["#/create", "plus", "New video", "cta"], ["#/", "home", "Home"], ["#/projects", "film", "My videos"], ["sep", "", "Tools"], ["#/titles", "type", "Title lab"], ["#/thumbs", "image", "Thumbnail studio"], ["#/voices", "mic", "Voices"],
["sep", "", "Library"], ["#/brands", "id", "Brand profiles"], ["#/styles", "grid", "Styles"], ["#/learn", "book", "Learn"], ["sep", "", "Owner"], ["#/settings", "gear", "Owner settings"]];
function drawNav() {
  const h = location.hash || "#/";
  $("#nav").innerHTML = NAV.map(([href, ic, label, cls]) => href === "sep" ? `<div class="sep">${label}</div>` : `<a href="${href}" class="${cls || ""} ${h === href || (href !== "#/" && h.startsWith(href)) ? "on" : ""}">${ico(ic)}${label}</a>`).join("");
  $("#tabbar").innerHTML = [["#/", "home", "Home"], ["#/create", "plus", "Create"], ["#/projects", "film", "Videos"], ["#/thumbs", "image", "Thumbs"], ["#/settings", "gear", "Owner"]].map(([href, ic, l]) => `<a href="${href}" class="${h === href ? "on" : ""}">${ico(ic)}${l}</a>`).join("");
  const st = S.cat?.settings || {};
  $("#modechip").innerHTML = `<b style="color:var(--ok)">Testing mode</b><br>Unlimited generations, no credits.<br><span class="mute">AI writer: ${esc(st.llm_active || "")}</span>`;
}
const fmtById = id => S.cat.formats.find(f => f.id === id) || S.cat.formats[0];
const themeById = id => S.cat.themes.find(t => t.id === id) || S.cat.themes[0];
const voiceById = id => [...S.voices, ...S.more].find(v => v.id === id);
const sw = t => `<div class="sw"><i style="background:${t.bg}"></i><i style="background:${t.bg2}"></i><i class="a" style="background:${t.accent}"></i><i class="a" style="background:${t.accent2}"></i><i class="a" style="background:${t.ink}"></i></div>`;
const statusTag = s => `<span class="tag ${{ done: "ok", editing: "acc", error: "bad", processing: "info", rendering: "info", queued: "" }[s] || ""}">${{ editing: "ready to edit", done: "rendered" }[s] || s}</span>`;

/* ------------------------------------------------------------------ router */
const ROUTES = {};
async function route() {
  clearInterval(S.timer); S.timer = null; window.ED && ED.leave && ED.leave();
  const h = (location.hash || "#/").slice(1), parts = h.split("/").filter(Boolean);
  const name = parts[0] || "home";
  $("#view").className = name === "p" ? "wide" : "";
  drawNav();
  const fn = ROUTES[name] || ROUTES.home;
  try { await fn(parts.slice(1)); } catch (e) { $("#view").innerHTML = `<div class="empty">Something went wrong: ${esc(e.message)}</div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

/* ------------------------------------------------------------------ home + projects */
function projectRow(p) {
  const busyP = ["queued", "processing", "rendering"].includes(p.status);
  return `<div class="pitem" data-go="#/p/${p.id}"><div class="pthumb">${p.thumb ? `<img loading="lazy" src="/api/projects/${p.id}/thumb?${p.created}" onerror="this.remove()">` : ico("film")}</div>
  <div class="grow"><b>${esc(p.title)}</b><div class="small dim">${esc(fmtById(p.format).name)} · ${p.duration ? fmtT(p.duration) : p.minutes + " min"} · ${ago(p.created)}</div>
  ${busyP ? `<div class="bar" style="margin-top:6px"><i style="width:${Math.round(p.pct * 100)}%"></i></div><div class="small mute">${esc(p.msg)}</div>` : ""}</div>
  <div class="row">${statusTag(p.status)}<button class="btn ghost sm bad" data-del="${p.id}" title="Delete">${ico("trash")}</button></div></div>`;
}
function bindProjectRows() {
  $$("[data-go]").forEach(e => e.onclick = ev => { if (!ev.target.closest("[data-del]")) location.hash = e.dataset.go; });
  $$("[data-del]").forEach(b => b.onclick = async () => { if (confirm("Delete this video and all its files?")) { await api("/projects/" + b.dataset.del, { method: "DELETE" }); route(); } });
}
ROUTES.home = async () => {
  const { projects } = await api("/projects"); S.projects = projects;
  $("#view").innerHTML = `<div class="hero"><h1>Turn a title into a finished video</h1><p>Script, voice, footage, AI images, motion graphics, music, sound design and captions, cut together for you. Then fine-tune it on a real timeline.</p>
  <div class="promptbox"><textarea id="hp" maxlength="10000" placeholder="Type a title or describe the video. Example: The untold timeline of the submarine sunk one hour before Pearl Harbor, 12 minute documentary"></textarea>
  <div class="row between"><div class="chips" id="hfmt">${["documentary", "explainer", "avatar", "anim2d", "truecrime", "listicle"].map((f, i) => `<span class="chip ${i ? "" : "on"}" data-f="${f}">${esc(fmtById(f).name)}</span>`).join("")}</div>
  <button class="btn pri lg" id="hgo">Continue ${ico("play")}</button></div></div></div>
  <div class="sect" style="margin-top:34px"><div class="row between"><h2>Recent generations</h2><a class="btn ghost sm" href="#/projects">View all</a></div>
  <div class="plist">${projects.slice(0, 6).map(projectRow).join("") || `<div class="empty">No videos yet. Type a title above to make your first one.</div>`}</div></div>
  <div class="sect"><h2>What every video gets</h2><div class="grid g4">${[["Story-first script", "Cold open, open loops, a twist and a clean ending, written for the ear."], ["Moving pictures only", "Every image pushes, pans, orbits or parallaxes. Scenes change every 4 to 5 seconds."], ["Sound design", "Original music per mood, ducked under the voice, with whooshes, hits and risers on the cuts."], ["Editable timeline", "Swap any visual, rewrite any line, add text and graphics, then render."]].map(([a, b]) => `<div class="card"><h3>${a}</h3><p class="dim small" style="margin:0">${b}</p></div>`).join("")}</div></div>`;
  let f = "documentary"; $$("#hfmt .chip").forEach(c => c.onclick = () => { $$("#hfmt .chip").forEach(x => x.classList.remove("on")); c.classList.add("on"); f = c.dataset.f; });
  $("#hgo").onclick = () => { newWizard(f, $("#hp").value.trim()); location.hash = "#/create"; };
  bindProjectRows();
  if (projects.some(p => ["queued", "processing", "rendering"].includes(p.status))) S.timer = setInterval(() => { if ((location.hash || "#/") === "#/") ROUTES.home(); }, 5000);
};
ROUTES.projects = async () => {
  const { projects } = await api("/projects");
  $("#view").innerHTML = `<div class="row between"><h1>My videos</h1><a class="btn pri" href="#/create">${ico("plus")} New video</a></div><div class="plist" style="margin-top:14px">${projects.map(projectRow).join("") || `<div class="empty">Nothing here yet.</div>`}</div>`;
  bindProjectRows();
};

/* ------------------------------------------------------------------ wizard */
const STEPS = ["Idea", "Settings", "Creative setup", "Review", "Thumbnail"];
async function newWizard(format = "documentary", prompt = "") {
  S.W = { step: 0, prompt, title: "", script: "", useScript: false, voice_upload: null, refUrl: "", ref: null, brand: null, persona: { bible: "" }, avatar: {}, settings: null, format,
    titles: null, thumb: { refs: null, ref: null, concepts: null, concept: null, url: "" } };
}
async function loadDefaults(format, keep = {}) { const d = await api("/defaults?format=" + format); S.W.settings = Object.assign(d, keep); S.W.format = format; }
ROUTES.create = async () => {
  if (!S.W) await newWizard();
  const W = S.W;
  if (!W.settings) await loadDefaults(W.format);
  const st = W.settings, v = $("#view");
  const head = `<h1>New video</h1><div class="steps">${STEPS.map((s, i) => `<div class="step ${i === W.step ? "on" : i < W.step ? "done" : ""}" data-step="${i}"><b>${i < W.step ? "✓" : i + 1}</b>${s}</div>`).join("")}</div>`;
  const foot = (next = "Continue", nextId = "wnext") => `<div class="wfoot"><button class="btn" id="wback" ${W.step ? "" : "disabled"}>Back</button><button class="btn pri lg" id="${nextId}">${next}</button></div>`;
  let body = "";
  if (W.step === 0) {
    body = `<div class="sect"><h2>What is the video about?</h2><p class="dim">A title is enough. A short brief is better: the angle, the beats you want and the feeling.</p>
    <textarea id="wprompt" maxlength="10000" style="min-height:150px;font-size:15px" placeholder="Title or full brief…">${esc(W.prompt)}</textarea>
    <div class="row between small mute" style="margin-top:6px"><span id="wcount"></span><button class="btn sm" id="wtitles">${ico("wand")} Suggest stronger titles</button></div><div id="wtitlebox" class="col" style="margin-top:10px"></div></div>
    <div class="sect grid g2"><div class="card"><label class="toggle"><input type="checkbox" id="wuse" ${W.useScript ? "checked" : ""}><i></i><b>I already have a script</b></label>
    <p class="dim small" style="margin:8px 0">Paste it and the AI will only storyboard, voice and edit it.</p><textarea id="wscript" placeholder="Paste your full script…" style="${W.useScript ? "" : "display:none"}">${esc(W.script)}</textarea></div>
    <div class="card"><b>Use my own voiceover</b><p class="dim small" style="margin:8px 0">Upload a recording (mp3, wav, m4a). The video is cut to your voice instead of an AI voice.</p>
    <input type="file" id="wvo" accept="audio/*"><div class="small" id="wvoinfo" style="margin-top:6px">${W.voice_upload ? "Uploaded: " + esc(W.voice_upload.name) : ""}</div></div></div>
    <div class="sect grid g2"><div class="card"><b>Reference video (optional)</b><p class="dim small" style="margin:8px 0">Paste a YouTube link. The AI studies how it is written and edited, then follows that style with its own flair.</p>
    <div class="row"><input type="url" id="wref" class="grow" placeholder="https://youtube.com/watch?v=…" value="${esc(W.refUrl)}"><button class="btn" id="wrefgo">Analyze</button></div><div id="wrefbox" class="small" style="margin-top:10px"></div></div>
    <div class="card"><b>Brand profile</b><p class="dim small" style="margin:8px 0">Saved voice, look, script style and persona for one channel.</p>
    <select id="wbrand"><option value="">No brand profile</option>${S.brands.map(b => `<option value="${b.id}" ${W.brand?.id === b.id ? "selected" : ""}>${esc(b.name)}</option>`).join("")}</select>
    <a class="btn ghost sm" href="#/brands" style="margin-top:8px">Manage brand profiles</a></div></div>` + foot();
  } else if (W.step === 1) {
    const max = S.cat.settings.max_minutes || 60;
    body = `<div class="sect"><h2>Editing format</h2><div class="grid auto">${S.cat.formats.map(f => `<button class="pick ${st.format === f.id ? "on" : ""}" data-format="${f.id}"><b>${esc(f.name)}</b><small>${esc(f.desc)}</small></button>`).join("")}</div></div>
    <div class="sect grid g2"><div class="card"><h3>Duration</h3><div class="chips" id="wdur">${S.cat.durations.filter(d => d <= max).map(d => `<span class="chip ${+st.duration_min === d ? "on" : ""}" data-d="${d}">${d} min</span>`).join("")}</div>
    <div class="row" style="margin-top:12px"><input type="range" id="wdurr" min="0.5" max="${max}" step="0.5" value="${st.duration_min}" class="grow"><input type="number" id="wdurn" min="0.5" max="${max}" step="0.5" value="${st.duration_min}" style="width:86px"><span class="dim">minutes</span></div>
    <p class="small mute" style="margin:8px 0 0">Any length up to ${max} minutes. Longer videos take longer to generate.</p></div>
    <div class="card grid g2"><label class="f"><span>Video language</span><select id="wlang">${S.cat.languages.map(([k, n]) => `<option value="${k}" ${st.language === k ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>
    <label class="f"><span>Shape</span><select id="waspect"><option value="16:9" ${st.aspect === "16:9" ? "selected" : ""}>Landscape 16:9</option><option value="9:16" ${st.aspect === "9:16" ? "selected" : ""}>Vertical 9:16</option></select></label>
    <label class="f"><span>Final quality</span><select id="wres">${[720, 1080].map(r => `<option value="${r}" ${+st.resolution === r ? "selected" : ""}>${r}p</option>`).join("")}</select></label>
    <label class="f"><span>Scene change every</span><select id="wpace">${[2.5, 3, 3.5, 4, 4.5, 5, 6, 8].map(r => `<option value="${r}" ${Math.abs(st.pace - r) < 0.26 ? "selected" : ""}>${r} seconds</option>`).join("")}</select></label></div></div>
    <div class="sect"><h2>Voice ${W.voice_upload ? '<span class="tag acc">your upload will be used</span>' : ""}</h2><div id="voicebox"></div></div>` + foot();
  } else if (W.step === 2) {
    const mgs = new Set(st.motion_graphics);
    body = `<div class="sect"><h2>Look</h2><div class="grid auto">${S.cat.themes.map(t => `<button class="pick ${st.theme === t.id ? "on" : ""}" data-theme="${t.id}">${sw(t)}<b>${esc(t.name)}</b><small>${esc(t.desc)}</small></button>`).join("")}</div></div>
    <div class="sect grid g2"><div class="card"><h3>Where pictures come from</h3><div class="col">${[["stock_video", "Real stock video", "Free, watermark-free clips"], ["stock_photo", "Stock photos", "Modern real-world photography"], ["archive", "Archive & historical photos", "Public-domain and free-licence collections"], ["ai", "AI-generated images", "Made for the exact line of narration"]].map(([k, a, b]) => `<label class="toggle"><input type="checkbox" data-src="${k}" ${st.sources[k] ? "checked" : ""}><i></i><span><b>${a}</b><br><span class="small dim">${b}</span></span></label>`).join("")}</div>
    ${S.cat.settings.stock_video_ready ? "" : `<p class="small" style="margin:12px 0 0;color:var(--acc2)">Stock video from Pexels and Pixabay needs their free API keys. Add them in Owner settings. Until then the engine uses free-licence video, archive photos and AI images.</p>`}
    <label class="f" style="margin-top:12px"><span>AI image style</span><select id="waist"><option value="">Match the format (recommended)</option>${S.cat.ai_styles.map(s => `<option ${st.ai_style === s ? "selected" : ""}>${s}</option>`).join("")}</select></label></div>
    <div class="card"><h3>Captions</h3><div class="chips" id="wcap">${S.cat.captions.map(([k, n]) => `<span class="chip ${st.captions === k ? "on" : ""}" data-c="${k}">${esc(n)}</span>`).join("")}</div>
    <h3 style="margin-top:16px">Music</h3><select id="wmusic">${S.cat.music.map(([k, n]) => `<option value="${k}" ${st.music === k ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>
    <label class="f" style="margin-top:10px"><span>Music level</span><input type="range" id="wmvol" min="0" max="1" step="0.05" value="${st.music_volume}"></label>
    <label class="toggle" style="margin-top:10px"><input type="checkbox" id="wsfx" ${st.sfx ? "checked" : ""}><i></i><b>Sound effects on cuts and graphics</b></label>
    <label class="toggle" style="margin-top:10px"><input type="checkbox" id="whuman" ${st.humanize ? "checked" : ""}><i></i><span><b>Humanize the voice</b><br><span class="small dim">Acts each line by emotion and adds natural pauses</span></span></label>
    <label class="toggle" style="margin-top:10px"><input type="checkbox" id="wvfx" ${st.voice_fx ? "checked" : ""}><i></i><span><b>Studio voice clean-up</b><br><span class="small dim">Noise reduction, EQ, de-ess, compression</span></span></label></div></div>
    <div class="sect"><div class="row between"><h2>Motion graphics the AI may use</h2><div class="row"><button class="btn sm" id="mgall">All</button><button class="btn sm" id="mgnone">None</button></div></div>
    <div class="chips" id="wmg">${S.cat.motion_graphics.map(([k, n]) => `<span class="chip ${mgs.has(k) ? "on" : ""}" data-mg="${k}">${esc(n)}</span>`).join("")}</div></div>
    ${st.format === "avatar" ? `<div class="sect card"><h2>Your avatar host</h2><p class="dim small">Leave everything empty and the AI invents an original host for this topic. Or paste your Persona Bible and upload your host image to keep the same face on every video.</p>
    <div class="grid g2"><label class="f"><span>Persona Bible (optional)</span><textarea id="wbible" placeholder="Name, age, backstory, look, voice, catchphrases, sign-off…">${esc(W.persona.bible || "")}</textarea></label>
    <div class="col"><label class="f"><span>Host image (optional, a front-facing portrait)</span><input type="file" id="wavimg" accept="image/*"></label><div class="small" id="wavinfo">${W.avatar.image ? "Image uploaded" : ""}</div>
    <label class="toggle"><input type="checkbox" id="wpip" ${st.avatar_pip ? "checked" : ""}><i></i><b>Keep the host in a corner bubble during B-roll</b></label></div></div></div>` : ""}
    <div class="sect card"><h3>Block list</h3><p class="dim small">Words or subjects that must never appear in visuals, separated by commas.</p><input type="text" id="wblock" value="${esc(st.blocklist)}" placeholder="blood, weapons, brand logos"></div>` + foot("Review");
  } else if (W.step === 3) {
    const est = await api("/estimate", { body: st });
    const vv = voiceById(st.voice), row = (k, v, step) => `<div class="kv"><span>${k}</span><span>${v}</span><button class="btn ghost sm" data-step="${step}">Edit</button></div>`;
    body = `<div class="sect"><h2>Review before generating</h2><p class="dim">Check that the AI understood you. Everything can still be changed in the editor afterwards.</p><div class="card">
    ${row("Brief", esc(W.prompt.slice(0, 260)) + (W.prompt.length > 260 ? "…" : ""), 0)}
    ${W.useScript && W.script ? row("Script", "Your own script, " + W.script.split(/\s+/).length + " words", 0) : ""}
    ${W.ref?.style ? row("Reference style", esc(W.ref.title || "") + '<br><span class="small dim">' + esc(W.ref.style.summary || "") + "</span>", 0) : ""}
    ${row("Format", esc(fmtById(st.format).name), 1)}${row("Duration", st.duration_min + " minutes · about " + est.words + " words · about " + est.shots + " scenes", 1)}
    ${row("Language · shape", esc(S.cat.languages.find(l => l[0] === st.language)?.[1] || st.language) + " · " + st.aspect + " · " + st.resolution + "p", 1)}
    ${row("Voice", W.voice_upload ? "Your uploaded voiceover" : esc(vv ? vv.name : st.voice), 1)}${row("Look", esc(themeById(st.theme).name), 2)}
    ${row("Visual sources", Object.entries(st.sources).filter(e => e[1]).map(e => e[0].replace("_", " ")).join(", "), 2)}
    ${row("Captions · music", esc(st.captions) + " · " + esc(st.music) + (st.sfx ? " · sound effects on" : ""), 2)}${row("Motion graphics", st.motion_graphics.length + " types allowed", 2)}</div></div>
    <div class="sect grid g2"><div class="card"><h3>Estimated generation time</h3><div style="font-size:30px;font-weight:800" class="mono">about ${est.minutes < 60 ? Math.round(est.minutes) + " min" : (est.minutes / 60).toFixed(1) + " h"}</div><p class="small dim" style="margin:6px 0 0">You can close the page. The video keeps generating and appears under My videos.</p></div>
    <div class="card"><h3>Cost</h3><div style="font-size:30px;font-weight:800;color:var(--ok)">Free <span class="small dim" style="font-weight:500">testing mode</span></div><p class="small dim" style="margin:6px 0 0">When credits are switched on this video would use about ${est.credits} credits.</p></div></div>` + foot("Approve and continue");
  } else {
    const T = W.thumb;
    body = `<div class="sect"><h2>Choose a thumbnail direction</h2><p class="dim">These are the videos pulling the most views on this topic right now. Pick one as inspiration, paste your own link, or let the AI decide. Your thumbnail is original; it borrows only what makes the reference work.</p>
    <div class="row" style="margin-bottom:12px"><input type="url" id="turl" class="grow" placeholder="Custom reference: paste any YouTube link" value="${esc(T.url)}"><button class="btn" id="turlgo">Use link</button></div>
    <div id="trefs" class="refgrid">${T.refs ? (T.refs.map((r, i) => `<div class="ref ${T.ref?.id === r.id ? "on" : ""}" data-ref="${i}"><img loading="lazy" src="${esc(r.thumb)}"><div><b>${esc((r.title || "").slice(0, 70))}</b><br><span class="mute">${esc(r.channel || "")}${r.views ? " · " + views(r.views) + " views" : ""}</span></div></div>`).join("") || `<div class="empty">No references found. Paste a link or let the AI decide.</div>`) : `<div class="empty"><span class="spin"></span> Finding what is working for this topic…</div>`}</div></div>
    <div class="sect"><div class="row between"><h2>Concepts</h2><button class="btn sm" id="tcon">${ico("wand")} ${T.concepts ? "New concepts" : "Write concepts"}</button></div>
    <div class="grid g2" id="tcons">${(T.concepts || []).map((c, i) => `<button class="pick ${T.concept === c ? "on" : ""}" data-con="${i}"><span class="tag acc">${esc(c.layout)}</span> <b style="display:inline">${esc(c.text)}</b><small style="margin-top:6px">${esc(c.idea)}</small></button>`).join("") || `<div class="empty" style="grid-column:1/-1">Optional. Skip this and the AI writes and picks a concept after the video is done.</div>`}</div></div>` + foot("Generate video", "wgen");
  }
  v.innerHTML = head + body;
  // shared wiring
  $$("[data-step]").forEach(e => e.onclick = () => { collect(); W.step = +e.dataset.step; ROUTES.create(); });
  $("#wback") && ($("#wback").onclick = () => { collect(); W.step--; ROUTES.create(); });
  $("#wnext") && ($("#wnext").onclick = () => { collect(); if (W.step === 0 && !W.prompt && !(W.useScript && W.script) && !W.voice_upload) return toast("Type a title or brief first", "bad"); W.step++; ROUTES.create(); });
  function collect() {
    if (W.step === 0) { W.prompt = $("#wprompt").value.trim(); W.useScript = $("#wuse").checked; W.script = $("#wscript").value; W.refUrl = $("#wref").value.trim(); }
    if (W.step === 1) { st.language = $("#wlang").value; st.aspect = $("#waspect").value; st.resolution = +$("#wres").value; st.pace = +$("#wpace").value; st.duration_min = +$("#wdurn").value || 3; }
    if (W.step === 2) { st.music = $("#wmusic").value; st.music_volume = +$("#wmvol").value; st.sfx = $("#wsfx").checked; st.humanize = $("#whuman").checked; st.voice_fx = $("#wvfx").checked; st.blocklist = $("#wblock").value; st.ai_style = $("#waist").value;
      if ($("#wbible")) { W.persona.bible = $("#wbible").value; st.avatar_pip = $("#wpip").checked; } }
  }
  if (W.step === 0) {
    const cnt = () => $("#wcount").textContent = $("#wprompt").value.length + " / 10,000"; cnt(); $("#wprompt").oninput = cnt;
    $("#wuse").onchange = e => $("#wscript").style.display = e.target.checked ? "" : "none";
    $("#wvo").onchange = async e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); $("#wvoinfo").innerHTML = '<span class="spin"></span> Uploading…'; try { W.voice_upload = await api("/upload", { body: fd }); $("#wvoinfo").textContent = "Uploaded: " + f.name + " (" + fmtT(W.voice_upload.duration) + ")"; } catch (er) { $("#wvoinfo").textContent = er.message; } };
    const showTitles = () => $("#wtitlebox").innerHTML = (W.titles || []).map((t, i) => `<button class="pick" data-t="${i}"><b>${esc(t.title)}</b><small>${esc(t.angle)} · click potential ${t.score}</small></button>`).join("");
    showTitles();
    $("#wtitles").onclick = e => busy(e.currentTarget, async () => { const topic = $("#wprompt").value.trim(); if (!topic) return toast("Type a topic first", "bad"); W.titles = (await api("/titles", { body: { topic, format: W.format, language: st.language, n: 8, reference: W.ref?.title || "" } })).titles; showTitles(); bindT(); });
    const bindT = () => $$("[data-t]").forEach(b => b.onclick = () => { const t = W.titles[+b.dataset.t].title; const cur = $("#wprompt").value.trim(); $("#wprompt").value = t + (cur && cur !== t ? "\n\n" + cur : ""); W.title = t; cnt(); toast("Title set", "ok"); }); bindT();
    const showRef = () => { const r = W.ref; $("#wrefbox").innerHTML = !r ? "" : r.error && !r.style ? `<span style="color:var(--bad)">${esc(r.error)}</span>` : `<b>${esc(r.title || "")}</b> <span class="mute">${esc(r.channel || "")}</span>${r.style ? `<div class="dim" style="margin-top:6px">${esc(r.style.summary || "")}<br><b>Mood:</b> ${esc(r.style.mood || "")} · <b>Hook:</b> ${esc(r.style.hook_pattern || "")}<br><b>Editing:</b> ${esc(r.style.editing || "")}</div><div class="row" style="margin-top:8px"><span class="tag ok">style saved for this video</span>${r.style.suggested_format ? `<button class="btn sm" id="wusefmt">Use ${esc(fmtById(r.style.suggested_format).name)} format</button>` : ""}</div>` : ""}`; $("#wusefmt") && ($("#wusefmt").onclick = async () => { await loadDefaults(r.style.suggested_format, {}); toast("Format set", "ok"); }); };
    showRef();
    $("#wrefgo").onclick = e => busy(e.currentTarget, async () => { W.refUrl = $("#wref").value.trim(); W.ref = await api("/reference", { body: { url: W.refUrl } }); showRef(); });
    $("#wbrand").onchange = async e => { const b = S.brands.find(x => x.id === e.target.value); W.brand = b || null; if (b) { await loadDefaults(b.format || W.format, {}); Object.assign(S.W.settings, b.settings || {}); if (b.persona) W.persona.bible = b.persona; toast("Brand profile applied", "ok"); } };
  }
  if (W.step === 1) {
    $$("[data-format]").forEach(b => b.onclick = async () => { collect(); await loadDefaults(b.dataset.format, { duration_min: st.duration_min, language: st.language, voice: st.voice, resolution: st.resolution }); ROUTES.create(); });
    const setD = d => { st.duration_min = d; $("#wdurr").value = d; $("#wdurn").value = d; $$("#wdur .chip").forEach(c => c.classList.toggle("on", +c.dataset.d === +d)); };
    $$("#wdur .chip").forEach(c => c.onclick = () => setD(+c.dataset.d)); $("#wdurr").oninput = e => setD(+e.target.value); $("#wdurn").onchange = e => setD(Math.min(S.cat.settings.max_minutes || 60, Math.max(0.5, +e.target.value || 3)));
    $("#wlang").onchange = async e => { st.language = e.target.value; await loadVoices(st.language); voicePicker($("#voicebox"), st.voice, id => st.voice = id, st.language); };
    await loadVoices(st.language); voicePicker($("#voicebox"), st.voice, id => st.voice = id, st.language);
  }
  if (W.step === 2) {
    $$("[data-theme]").forEach(b => b.onclick = () => { st.theme = b.dataset.theme; $$("[data-theme]").forEach(x => x.classList.toggle("on", x === b)); });
    $$("[data-src]").forEach(i => i.onchange = () => st.sources[i.dataset.src] = i.checked);
    $$("#wcap .chip").forEach(c => c.onclick = () => { st.captions = c.dataset.c; $$("#wcap .chip").forEach(x => x.classList.toggle("on", x === c)); });
    const syncMg = () => st.motion_graphics = $$("#wmg .chip.on").map(c => c.dataset.mg);
    $$("#wmg .chip").forEach(c => c.onclick = () => { c.classList.toggle("on"); syncMg(); });
    $("#mgall").onclick = () => { $$("#wmg .chip").forEach(c => c.classList.add("on")); syncMg(); }; $("#mgnone").onclick = () => { $$("#wmg .chip").forEach(c => c.classList.remove("on")); syncMg(); };
    $("#wavimg") && ($("#wavimg").onchange = async e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); try { const u = await api("/upload", { body: fd }); W.avatar = { image: u.path }; $("#wavinfo").textContent = "Image uploaded"; } catch (er) { toast(er.message, "bad"); } });
  }
  if (W.step === 4) {
    const T = W.thumb, topic = (W.title || W.prompt.split("\n")[0]).slice(0, 120);
    if (!T.refs) api("/thumb/references", { body: { topic } }).then(r => { T.refs = r.refs; if (S.W === W && W.step === 4) ROUTES.create(); }).catch(() => { T.refs = []; });
    $$("[data-ref]").forEach(e => e.onclick = () => { const r = T.refs[+e.dataset.ref]; T.ref = T.ref?.id === r.id ? null : r; $$("[data-ref]").forEach(x => x.classList.toggle("on", T.ref && T.refs[+x.dataset.ref].id === T.ref.id)); });
    $("#turlgo").onclick = e => busy(e.currentTarget, async () => { T.url = $("#turl").value.trim(); const r = await api("/thumb/url", { body: { url: T.url } }); if (r.error) return toast(r.error, "bad"); T.refs = [r, ...(T.refs || []).filter(x => x.id !== r.id)]; T.ref = r; ROUTES.create(); });
    $("#tcon").onclick = e => busy(e.currentTarget, async () => { T.concepts = (await api("/thumb/concepts", { body: { title: topic, format: st.format, ref_title: T.ref?.title || "" } })).concepts; T.concept = null; ROUTES.create(); });
    $$("[data-con]").forEach(b => b.onclick = () => { const c = T.concepts[+b.dataset.con]; T.concept = T.concept === c ? null : c; $$("[data-con]").forEach(x => x.classList.toggle("on", T.concepts[+x.dataset.con] === T.concept)); });
    $("#wgen").onclick = e => busy(e.currentTarget, async () => {
      const brand = Object.assign({}, W.brand || {}); if (W.ref?.script_style) brand.script_style = W.ref.script_style;
      const p = await api("/projects", { body: { title: W.title || W.prompt.split("\n")[0], title_locked: !!W.title, prompt: W.prompt, script: W.useScript ? W.script : "", voice_upload: W.voice_upload?.path || null,
        settings: st, brand, persona: W.persona.bible ? { bible: W.persona.bible } : {}, avatar: W.avatar, thumbnail: { ref: T.ref ? { id: T.ref.id, title: T.ref.title, thumb: T.ref.thumb } : null, concept: T.concept }, start: true } });
      S.W = null; location.hash = "#/p/" + p.id;
    });
  }
};

/* ------------------------------------------------------------------ voices */
async function loadVoices(lang = "en") { const r = await api("/voices?lang=" + lang); S.voices = r.voices; S.more = r.more || []; }
let audioEl = null;
function playVoice(v, lang, btn) {
  if (audioEl) { audioEl.pause(); audioEl = null; $$(".play").forEach(b => b.innerHTML = ico("play")); if (btn.dataset.on) { delete btn.dataset.on; return; } }
  $$(".play").forEach(b => delete b.dataset.on);
  audioEl = new Audio(v.provider === "elevenlabs" && v.preview ? v.preview : `/api/voices/preview?id=${encodeURIComponent(v.id)}&lang=${lang}`);
  btn.innerHTML = '<span class="spin"></span>'; btn.dataset.on = 1;
  audioEl.oncanplay = () => btn.innerHTML = ico("stop"); audioEl.onended = () => { btn.innerHTML = ico("play"); delete btn.dataset.on; }; audioEl.onerror = () => { btn.innerHTML = ico("play"); toast("Could not load this preview", "bad"); };
  audioEl.play().catch(() => { });
}
function voicePicker(box, current, onPick, lang = "en") {
  const F = voicePicker.F || (voicePicker.F = { gender: "", age: "", provider: "", q: "" });
  const loc = lang === "hinglish" ? "hi" : lang;
  const all = [...S.voices, ...S.more];
  const list = all.filter(v => (!F.gender || v.gender === F.gender) && (!F.age || v.age === F.age) && (!F.provider || v.provider === F.provider) && (!F.q || (v.name + v.accent + v.style + v.desc).toLowerCase().includes(F.q.toLowerCase())))
    .sort((a, b) => ((b.locale || "").startsWith(loc) || b.multilingual ? 1 : 0) - ((a.locale || "").startsWith(loc) || a.multilingual ? 1 : 0));
  const chip = (k, v, l) => `<span class="chip ${F[k] === v ? "on" : ""}" data-fk="${k}" data-fv="${v}">${l}</span>`;
  box.innerHTML = `<div class="row" style="margin-bottom:10px"><div class="chips">${chip("gender", "", "Any gender")}${chip("gender", "female", "Female")}${chip("gender", "male", "Male")}</div>
  <div class="chips">${chip("age", "", "Any age")}${chip("age", "child", "Child")}${chip("age", "teen", "Teen")}${chip("age", "young", "Young")}${chip("age", "middle", "Middle-aged")}${chip("age", "old", "Old")}</div>
  <div class="chips">${chip("provider", "", "All")}${chip("provider", "neural", "Natural neural (free)")}${chip("provider", "elevenlabs", "ElevenLabs")}</div><input type="text" id="vq" placeholder="Search accent, style…" value="${esc(F.q)}" style="max-width:200px"></div>
  <div class="vlist">${list.map(v => `<div class="vrow ${v.id === current ? "on" : ""}" data-v="${esc(v.id)}"><span class="play" data-p="${esc(v.id)}">${ico("play")}</span><div><b>${esc(v.name)}</b> <span class="tag ${v.provider === "elevenlabs" ? "acc" : "ok"}">${v.provider === "elevenlabs" ? "ElevenLabs" : "neural"}</span>${v.locked ? ' <span class="tag bad">needs key</span>' : ""}
  <div class="small dim">${[v.gender, v.age, v.accent, v.style].filter(Boolean).map(esc).join(" · ")}</div><div class="small mute">${esc(v.desc || "")}</div></div><span>${v.id === current ? ico("check") : ""}</span></div>`).join("") || `<div class="empty">No voices match.</div>`}</div>`;
  $$("[data-fk]", box).forEach(c => c.onclick = () => { F[c.dataset.fk] = c.dataset.fv; voicePicker(box, current, onPick, lang); });
  $("#vq", box).onchange = e => { F.q = e.target.value; voicePicker(box, current, onPick, lang); };
  $$("[data-p]", box).forEach(b => b.onclick = e => { e.stopPropagation(); playVoice(all.find(v => v.id === b.dataset.p), lang, b); });
  $$("[data-v]", box).forEach(r => r.onclick = () => { const v = all.find(x => x.id === r.dataset.v); if (v.locked) return toast("Add your ElevenLabs API key in Owner settings to use this voice. You can still listen to the preview.", "bad"); onPick(v.id); voicePicker(box, v.id, onPick, lang); });
}
ROUTES.voices = async () => {
  await loadVoices("en");
  $("#view").innerHTML = `<h1>Voices</h1><p class="dim">Natural neural voices are free and unlimited, each tuned to sound different. ElevenLabs voices unlock when you add your key in Owner settings. Press play to listen.</p><div id="vb"></div>`;
  let cur = ""; voicePicker($("#vb"), cur, id => cur = id, "en"); $(".vlist").style.maxHeight = "none";
};

/* ------------------------------------------------------------------ title lab */
ROUTES.titles = async () => {
  $("#view").innerHTML = `<h1>Title lab</h1><p class="dim">Describe the video. Get titles built on formulas that are proven to earn clicks, each scored.</p>
  <div class="card col"><textarea id="tt" placeholder="Topic or rough title…"></textarea><div class="grid g3"><label class="f"><span>Format</span><select id="tf">${S.cat.formats.map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join("")}</select></label>
  <label class="f"><span>Language</span><select id="tl">${S.cat.languages.map(([k, n]) => `<option value="${k}">${esc(n)}</option>`).join("")}</select></label><label class="f"><span>Reference title (optional)</span><input type="text" id="tr" placeholder="A title that worked in your niche"></label></div>
  <div class="row"><button class="btn pri" id="tg">${ico("wand")} Generate 12 titles</button></div></div><div id="tout" class="col" style="margin-top:16px"></div>
  <div class="sect" style="margin-top:26px"><h2>Formulas the lab draws on</h2><div class="grid g2">${S.cat.title_formulas.map(f => `<div class="card small mono">${esc(f)}</div>`).join("")}</div></div>`;
  $("#tg").onclick = e => busy(e.currentTarget, async () => {
    const topic = $("#tt").value.trim(); if (!topic) return toast("Type a topic", "bad");
    const { titles } = await api("/titles", { body: { topic, format: $("#tf").value, language: $("#tl").value, n: 12, reference: $("#tr").value } });
    $("#tout").innerHTML = titles.map((t, i) => `<div class="card row between"><div class="grow"><b style="font-size:16px">${esc(t.title)}</b><div class="small dim">${esc(t.angle)} · ${t.title.length} characters</div><div class="bar" style="max-width:220px;margin-top:6px"><i style="width:${t.score}%"></i></div></div>
    <div class="row"><span class="mono" style="font-size:20px;font-weight:800">${t.score}</span><button class="btn sm" data-cp="${i}">${ico("copy")}</button><button class="btn sm pri" data-mk="${i}">Make this video</button></div></div>`).join("");
    $$("[data-cp]").forEach(b => b.onclick = () => copyText(titles[+b.dataset.cp].title));
    $$("[data-mk]").forEach(b => b.onclick = async () => { await newWizard($("#tf").value, titles[+b.dataset.mk].title); S.W.title = titles[+b.dataset.mk].title; location.hash = "#/create"; });
  });
};

/* ------------------------------------------------------------------ thumbnail studio */
ROUTES.thumbs = async () => {
  const st = ROUTES.thumbs.st || (ROUTES.thumbs.st = { title: "", refs: [], ref: null, concepts: [], fmt: "documentary" });
  const { items } = await api("/thumb/gallery");
  $("#view").innerHTML = `<h1>Thumbnail studio</h1><p class="dim">Research what is winning for a topic, pick a reference, get original concepts and render 1280 × 720 thumbnails with perfectly spelled text.</p>
  <div class="card col"><div class="row"><input type="text" id="th" class="grow" placeholder="Video title or topic" value="${esc(st.title)}"><button class="btn" id="thr">Find references</button><button class="btn pri" id="thc">${ico("wand")} Write concepts</button></div>
  <div class="row"><input type="url" id="thu" class="grow" placeholder="Or paste a YouTube link to use as the reference"><button class="btn" id="thug">Use link</button></div></div>
  <div class="sect" style="margin-top:16px"><div class="refgrid" id="threfs">${st.refs.map((r, i) => `<div class="ref ${st.ref?.id === r.id ? "on" : ""}" data-ref="${i}"><img loading="lazy" src="${esc(r.thumb)}"><div><b>${esc((r.title || "").slice(0, 70))}</b><br><span class="mute">${esc(r.channel || "")}${r.views ? " · " + views(r.views) + " views" : ""}</span></div></div>`).join("")}</div>
  ${st.ref?.analysis?.palette ? `<div class="row small dim" style="margin-top:10px">Reference palette: ${st.ref.analysis.palette.map(c => `<i style="width:22px;height:22px;border-radius:5px;background:${c.hex};display:inline-block"></i>`).join("")} <span>Its accent color will be reused.</span></div>` : ""}</div>
  <div class="sect"><div class="grid g2">${st.concepts.map((c, i) => `<div class="card col"><div><span class="tag acc">${esc(c.layout)}</span> <span class="tag">${esc(c.hook || "none")}</span></div><p class="dim small" style="margin:0">${esc(c.idea)}</p>
  <label class="f"><span>Text on the thumbnail</span><input type="text" data-ct="${i}" value="${esc(c.text)}"></label><label class="f"><span>Picture</span><textarea data-cpr="${i}" style="min-height:70px">${esc(c.prompt)}</textarea></label>
  <button class="btn pri" data-gen="${i}">Render thumbnail</button></div>`).join("")}</div></div>
  <div class="sect"><h2>Your thumbnails</h2><div class="refgrid">${items.map(p => `<div class="ref"><img loading="lazy" src="${fileUrl(p)}"><div><a class="btn sm" href="${fileUrl(p, "thumbnail.png")}">${ico("dl")} Download</a></div></div>`).join("") || `<div class="empty">Rendered thumbnails appear here.</div>`}</div></div>`;
  const keep = () => { st.title = $("#th").value.trim(); $$("[data-ct]").forEach(i => st.concepts[+i.dataset.ct].text = i.value.toUpperCase()); $$("[data-cpr]").forEach(i => st.concepts[+i.dataset.cpr].prompt = i.value); };
  $("#thr").onclick = e => busy(e.currentTarget, async () => { keep(); if (!st.title) return toast("Type a topic", "bad"); st.refs = (await api("/thumb/references", { body: { topic: st.title } })).refs; if (!st.refs.length) toast("No references found for that topic"); ROUTES.thumbs(); });
  $("#thug").onclick = e => busy(e.currentTarget, async () => { keep(); const r = await api("/thumb/url", { body: { url: $("#thu").value } }); if (r.error) return toast(r.error, "bad"); st.refs = [r, ...st.refs.filter(x => x.id !== r.id)]; st.ref = r; if (!st.title) st.title = r.title || ""; ROUTES.thumbs(); });
  $("#thc").onclick = e => busy(e.currentTarget, async () => { keep(); if (!st.title) return toast("Type a title", "bad"); st.concepts = (await api("/thumb/concepts", { body: { title: st.title, ref_title: st.ref?.title || "" } })).concepts; ROUTES.thumbs(); });
  $$("[data-ref]").forEach(e => e.onclick = () => { keep(); const r = st.refs[+e.dataset.ref]; st.ref = st.ref?.id === r.id ? null : r; ROUTES.thumbs(); });
  $$("[data-gen]").forEach(b => b.onclick = e => busy(e.currentTarget, async () => { keep(); await api("/thumb/generate", { body: { concept: st.concepts[+b.dataset.gen], ref: st.ref } }); toast("Thumbnail rendered", "ok"); ROUTES.thumbs(); }));
};

/* ------------------------------------------------------------------ brands / styles / learn / settings */
ROUTES.brands = async () => {
  S.brands = (await api("/brands")).brands; await loadVoices("en");
  const ed = ROUTES.brands.ed;
  $("#view").innerHTML = `<div class="row between"><h1>Brand profiles</h1><button class="btn pri" id="bnew">${ico("plus")} New brand profile</button></div><p class="dim">One profile per channel: its format, look, voice, script style and host persona. Pick it in the wizard and every video stays on-brand.</p>
  <div class="grid auto" style="margin-top:14px">${S.brands.map(b => `<div class="card"><b>${esc(b.name)}</b><div class="small dim">${esc(fmtById(b.format).name)} · ${esc(themeById(b.settings?.theme).name)}</div><div class="row" style="margin-top:10px"><button class="btn sm" data-be="${b.id}">Edit</button><button class="btn sm ghost bad" data-bd="${b.id}">Delete</button></div></div>`).join("") || `<div class="empty">No brand profiles yet.</div>`}</div>
  ${ed ? `<div class="card col" style="margin-top:18px"><h2>${ed.id ? "Edit" : "New"} brand profile</h2><div class="grid g3"><label class="f"><span>Channel / brand name</span><input type="text" id="bn" value="${esc(ed.name || "")}"></label>
  <label class="f"><span>Format</span><select id="bf">${S.cat.formats.map(f => `<option value="${f.id}" ${ed.format === f.id ? "selected" : ""}>${esc(f.name)}</option>`).join("")}</select></label>
  <label class="f"><span>Look</span><select id="bt">${S.cat.themes.map(t => `<option value="${t.id}" ${ed.settings?.theme === t.id ? "selected" : ""}>${esc(t.name)}</option>`).join("")}</select></label>
  <label class="f"><span>Language</span><select id="bl">${S.cat.languages.map(([k, n]) => `<option value="${k}" ${ed.settings?.language === k ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>
  <label class="f"><span>Voice</span><select id="bv">${S.voices.filter(v => !v.locked).map(v => `<option value="${esc(v.id)}" ${ed.settings?.voice === v.id ? "selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label>
  <label class="f"><span>Block list</span><input type="text" id="bb" value="${esc(ed.settings?.blocklist || "")}"></label></div>
  <label class="f"><span>Script style (paste a reference link and press Analyze, or write it yourself)</span><div class="row"><input type="url" id="bref" class="grow" placeholder="https://youtube.com/watch?v=…"><button class="btn" id="brefgo">Analyze</button></div><textarea id="bs">${esc(ed.script_style || "")}</textarea></label>
  <label class="f"><span>Persona Bible (for avatar channels)</span><textarea id="bp">${esc(ed.persona || "")}</textarea></label><div class="row"><button class="btn pri" id="bsave">Save brand profile</button><button class="btn ghost" id="bcancel">Cancel</button></div></div>` : ""}`;
  $("#bnew").onclick = () => { ROUTES.brands.ed = { format: "documentary", settings: {} }; ROUTES.brands(); };
  $$("[data-be]").forEach(b => b.onclick = () => { ROUTES.brands.ed = JSON.parse(JSON.stringify(S.brands.find(x => x.id === b.dataset.be))); ROUTES.brands(); });
  $$("[data-bd]").forEach(b => b.onclick = async () => { if (confirm("Delete this brand profile?")) { await api("/brands/" + b.dataset.bd, { method: "DELETE" }); ROUTES.brands(); } });
  if (ed) {
    $("#bcancel").onclick = () => { ROUTES.brands.ed = null; ROUTES.brands(); };
    $("#brefgo").onclick = e => busy(e.currentTarget, async () => { const r = await api("/reference", { body: { url: $("#bref").value } }); if (r.script_style) $("#bs").value = r.script_style; else toast(r.error || "Could not analyze", "bad"); });
    $("#bsave").onclick = e => busy(e.currentTarget, async () => { if (!$("#bn").value.trim()) return toast("Name the brand", "bad"); await api("/brands", { body: { id: ed.id, name: $("#bn").value.trim(), format: $("#bf").value, script_style: $("#bs").value, persona: $("#bp").value, settings: { theme: $("#bt").value, language: $("#bl").value, voice: $("#bv").value, blocklist: $("#bb").value } } }); ROUTES.brands.ed = null; toast("Saved", "ok"); ROUTES.brands(); });
  }
};
ROUTES.styles = async () => {
  $("#view").innerHTML = `<h1>Styles</h1><p class="dim">Formats decide how a video is written and cut. Looks decide color, type, grade and transitions. Any format works with any look, and each video gets its own seeded variation so no two come out the same.</p>
  <div class="sect"><h2>Editing formats</h2><div class="grid auto">${S.cat.formats.map(f => `<div class="card"><b>${esc(f.name)}</b><p class="small dim" style="margin:4px 0 8px">${esc(f.desc)}</p><div class="small mute">Look: ${esc(themeById(f.theme).name)} · Music: ${esc(f.music)} · Cut every ${f.pace}s</div><button class="btn sm" style="margin-top:10px" data-mk="${f.id}">Start with this</button></div>`).join("")}</div></div>
  <div class="sect"><h2>Looks</h2><div class="grid auto">${S.cat.themes.map(t => `<div class="card">${sw(t)}<b>${esc(t.name)}</b><p class="small dim" style="margin:4px 0 0">${esc(t.desc)}</p></div>`).join("")}</div></div>
  <div class="sect grid g2"><div class="card"><h2>Motion graphics</h2><div class="chips">${S.cat.motion_graphics.map(m => `<span class="tag">${esc(m[1])}</span>`).join("")}</div></div>
  <div class="card"><h2>Camera moves and transitions</h2><div class="chips">${S.cat.motions.map(m => `<span class="tag info">${esc(m.replace("_", " "))}</span>`).join("")}${S.cat.transitions.map(m => `<span class="tag acc">${esc(m)}</span>`).join("")}</div></div></div>`;
  $$("[data-mk]").forEach(b => b.onclick = async () => { await newWizard(b.dataset.mk); location.hash = "#/create"; });
};
ROUTES.learn = async () => {
  const parts = [["1. Powerful opening", "Start inside the moment. The engine writes a cold open and puts the strongest visual first."], ["2. Narration that builds curiosity", "Open loops every minute, a twist near two thirds, and an ending that pays off the opening."], ["3. Visuals", "Real footage, archive photographs, maps, AI images and motion graphics, never the same picture twice."], ["4. Camera movement", "Push in, pull out, pans, orbit, tilt, parallax cards, focus pulls, speed-ramped pushes and hand-held drift. No frozen stills."],
  ["5. Sound design", "Whooshes, hits, risers, ticks and scene sounds on the moments that matter, with silence in between."], ["6. Music", "Original beds per mood that change with the chapters and duck under the voice automatically."], ["7. Motion graphics", "Animated maps, timelines, charts, numbers, callouts, documents and labelled diagrams."], ["8. Editing", "J and L style overlaps, dissolves, dips, zoom and wipe transitions, punch-ins on avatar cuts."],
  ["9. Voice processing", "Noise reduction, EQ, de-essing, compression and loudness normalised to −14 LUFS."], ["10. Colour and finish", "One grade per look, vignette and grain, no black frames, a faded ending and a credits card."]];
  $("#view").innerHTML = `<h1>Learn</h1><p class="dim">How a professional video is put together, and how to get the most out of the studio.</p>
  <div class="sect"><h2>Tips</h2><div class="grid g2">${S.cat.tips.map(([a, b]) => `<div class="card"><h3>${esc(a)}</h3><p class="small dim" style="margin:0">${esc(b)}</p></div>`).join("")}</div></div>
  <div class="sect"><h2>The ten parts of a finished video</h2><div class="grid g2">${parts.map(([a, b]) => `<div class="card"><h3>${a}</h3><p class="small dim" style="margin:0">${b}</p></div>`).join("")}</div></div>
  <div class="sect card"><h2>The workflow</h2><table class="t"><tr><th>Step</th><th>What you do</th><th>What the AI does</th></tr>
  <tr><td>Idea</td><td>Type a title or brief, optionally a reference link</td><td>Studies the reference, suggests stronger titles</td></tr><tr><td>Settings</td><td>Pick format, length, language, voice</td><td>Loads the right defaults for that format</td></tr>
  <tr><td>Creative setup</td><td>Pick the look, sources, captions and music</td><td>Plans visuals and graphics line by line</td></tr><tr><td>Review</td><td>Approve the summary</td><td>Estimates time and cost</td></tr>
  <tr><td>Generate</td><td>Wait, or close the page</td><td>Writes, records, finds and makes visuals, cuts, mixes, renders a preview</td></tr><tr><td>Edit and render</td><td>Fix anything on the timeline, press Render</td><td>Exports the final file, thumbnail, captions and upload text</td></tr></table></div>`;
};
ROUTES.settings = async () => {
  const s = await api("/settings");
  const key = (k, label, hint, link) => `<label class="f"><span>${label} ${s[k] ? '<span class="tag ok">set</span>' : ""}</span><input type="text" data-k="${k}" value="${esc(s[k])}" placeholder="${hint}" autocomplete="off">${link ? `<span class="small mute">${link}</span>` : ""}</label>`;
  $("#view").innerHTML = `<h1>Owner settings</h1><p class="dim">Only you see this page. Keys are stored on this server and never sent to the browser in full.</p>
  <div class="sect card col"><h2>Real stock footage (free)</h2><p class="small dim">Both services are free and watermark-free. Create an account, copy the API key, paste it here.</p><div class="grid g2">${key("pexels_key", "Pexels API key", "Paste key", "pexels.com/api")}${key("pixabay_key", "Pixabay API key", "Paste key", "pixabay.com/api/docs")}</div></div>
  <div class="sect card col"><h2>AI writer</h2><p class="small dim">Works with no key using a free model. Add a key for a stronger writer on long videos. Active now: <b>${esc(s.llm_active)}</b></p>
  <div class="grid g2"><label class="f"><span>Provider</span><select data-k="llm_provider">${["auto", "anthropic", "openai", "gemini", "groq", "pollinations"].map(p => `<option ${s.llm_provider === p ? "selected" : ""}>${p}</option>`).join("")}</select></label>
  <label class="f"><span>Model name (optional)</span><input type="text" data-k="llm_model" value="${esc(s.llm_model)}" placeholder="Leave empty for the provider default"></label>
  ${key("anthropic_key", "Anthropic API key", "sk-ant-…")}${key("openai_key", "OpenAI API key", "sk-…")}${key("gemini_key", "Google Gemini API key", "Free tier available")}${key("groq_key", "Groq API key", "Free tier available")}</div></div>
  <div class="sect card col"><h2>Voices and images</h2><div class="grid g2">${key("elevenlabs_key", "ElevenLabs API key", "Unlocks ElevenLabs voices")}${key("youtube_key", "YouTube Data API key (optional)", "Better thumbnail research")}
  <label class="f"><span>AI image engine</span><select data-k="image_provider">${["pollinations", "openai"].map(p => `<option ${s.image_provider === p ? "selected" : ""}>${p}</option>`).join("")}</select></label>
  <label class="f"><span>Free image model</span><input type="text" data-k="image_model" value="${esc(s.image_model)}"></label></div></div>
  <div class="sect card col"><h2>Limits and rendering</h2><div class="grid g3"><label class="f"><span>Maximum video length (minutes)</span><input type="number" data-k="max_minutes" data-n="1" value="${s.max_minutes}"></label>
  <label class="f"><span>Parallel render workers</span><input type="number" data-k="render_jobs" data-n="1" value="${s.render_jobs}"></label>
  <label class="f"><span>Default final quality</span><select data-k="default_resolution" data-n="1">${[720, 1080].map(r => `<option ${+s.default_resolution === r ? "selected" : ""}>${r}</option>`).join("")}</select></label></div>
  <label class="toggle"><input type="checkbox" disabled><i></i><span><b>Credit system</b> <span class="tag">off while testing</span><br><span class="small dim">Every generation is free and unlimited for now. The review step already shows what each video would cost.</span></span></label></div>
  <div class="sect card col"><h2>Privacy</h2><label class="f"><span>Owner password ${s.owner_password ? '<span class="tag ok">set</span>' : '<span class="tag bad">not set</span>'}</span><input type="text" data-k="owner_password" value="${esc(s.owner_password)}" placeholder="Set a password before putting this on a public server"></label></div>
  <div class="wfoot"><span></span><button class="btn pri lg" id="ssave">Save settings</button></div>`;
  $("#ssave").onclick = e => busy(e.currentTarget, async () => { const body = {}; $$("[data-k]").forEach(i => body[i.dataset.k] = i.dataset.n ? +i.value : i.value.trim()); await api("/settings", { body }); S.cat = await api("/catalog"); toast("Settings saved", "ok"); ROUTES.settings(); drawNav(); });
};

/* ------------------------------------------------------------------ boot */
(async () => {
  try { S.cat = await api("/catalog"); S.brands = (await api("/brands")).brands; } catch (e) { return; }
  route();
})();
