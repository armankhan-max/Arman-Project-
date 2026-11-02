// Space B-roll kit: stars, sun, planets, orbits, thermometer, Mercury surface, frost, heat, spacecraft, radar, craters.
const L = require('./lib');
const { W, H, clamp, lerp, E, rng, hash, noise1, circle, ell, rr, vgrad, rgrad, text, line } = L;
const G = require('./guy');

const cache = {};
function cached(key, fn, w = W, h = H) { if (!cache[key]) { const [c, x] = L.canvas(w, h); fn(x); cache[key] = c; } return cache[key]; }

const ASTRO = { shirt: '#e8742c', sleeve: '#e8742c', pants: '#e8742c', pantsB: '#b8561c', suit: true, helmet: true, backpack: '#c9ccd3' };
const astro = (t, o = {}) => ({ t, seed: .3, ...ASTRO, ...o });

// ---------- space backdrop ----------
function stars(ctx, t, o = {}) {
  ctx.drawImage(cached('stars', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#04050c'], [1, '#080a18']]); x.fillRect(0, 0, W, H);
    x.fillStyle = rgrad(x, 1400, 300, 50, 900, [[0, 'rgba(90,60,160,.18)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, W, H);
    x.fillStyle = rgrad(x, 300, 800, 50, 700, [[0, 'rgba(40,90,160,.14)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, W, H);
    const r = rng(11); for (let i = 0; i < 420; i++) { const s = r(); x.fillStyle = `rgba(255,255,255,${.25 + r() * .7})`; circle(x, r() * W, r() * H, s < .9 ? .7 + r() * .8 : 1.6 + r() * 1.2); x.fill(); }
  }), 0, 0);
  if (o.twinkle !== false) { const r = rng(5); ctx.save(); for (let i = 0; i < 30; i++) { const x = r() * W, y = r() * H, a = .5 + .5 * Math.sin(t * (1 + r() * 2) + i); ctx.fillStyle = `rgba(255,255,255,${a * .9})`; circle(ctx, x, y, 1.6); ctx.fill(); } ctx.restore(); }
}
// ---------- the sun ----------
function sun(ctx, x, y, r, t, o = {}) {
  const k = o.glow ?? 1;
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = rgrad(ctx, x, y, r * .6, r * 3.2, [[0, `rgba(255,190,80,${.55 * k})`], [.4, `rgba(255,120,40,${.18 * k})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(x - r * 3.3, y - r * 3.3, r * 6.6, r * 6.6);
  // corona flicker
  for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2 + t * .05; const len = r * (1.12 + .12 * (.5 + .5 * Math.sin(t * 2 + i * 1.7))); ctx.strokeStyle = `rgba(255,170,70,${.18 * k})`; ctx.lineWidth = r * .08; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r * .95, y + Math.sin(a) * r * .95); ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len); ctx.stroke(); }
  ctx.restore();
  ctx.fillStyle = rgrad(ctx, x - r * .25, y - r * .25, r * .1, r, [[0, '#fff6d0'], [.55, '#ffc24a'], [1, '#ff7a1a']]); circle(ctx, x, y, r); ctx.fill();
  // granulation
  ctx.save(); circle(ctx, x, y, r); ctx.clip(); const rr2 = rng(3); for (let i = 0; i < 40; i++) { const a = rr2() * Math.PI * 2, d = rr2() * r; ctx.fillStyle = `rgba(255,${120 + rr2() * 80 | 0},40,${.12 + .08 * Math.sin(t * 1.5 + i)})`; circle(ctx, x + Math.cos(a) * d, y + Math.sin(a) * d, r * (.06 + rr2() * .1)); ctx.fill(); } ctx.restore();
}
// ---------- planets ----------
const PLANETS = {
  mercury: { base: ['#b9a993', '#7a6c5c', '#3d352d'], craters: 16 },
  earth: { base: ['#6fb4ff', '#2f6fc0', '#123366'], land: '#4fa65a' },
  moon: { base: ['#d8d8d8', '#9a9a9a', '#4a4a4a'], craters: 10 },
  uranus: { base: ['#c8f4f4', '#7fd0d8', '#3a7f8a'] },
  venus: { base: ['#ffe7a8', '#e0a85a', '#8a5a2a'] },
};
function planet(ctx, x, y, r, kind, o = {}) {
  const P = PLANETS[kind];
  const key = `pl_${kind}`; const S = 400;
  const img = cached(key, c => {
    c.fillStyle = rgrad(c, S * .38, S * .35, S * .05, S * .55, [[0, P.base[0]], [.6, P.base[1]], [1, P.base[2]]]); circle(c, S / 2, S / 2, S / 2 - 2); c.fill();
    c.save(); circle(c, S / 2, S / 2, S / 2 - 2); c.clip();
    const r2 = rng(kind.length * 7);
    if (P.craters) for (let i = 0; i < P.craters; i++) { const cx = r2() * S, cy = r2() * S, cr = 8 + r2() * 30; c.fillStyle = 'rgba(0,0,0,.18)'; circle(c, cx, cy, cr); c.fill(); c.fillStyle = 'rgba(255,255,255,.1)'; circle(c, cx - cr * .2, cy - cr * .2, cr * .75); c.fill(); }
    if (P.land) { c.fillStyle = P.land; for (const [cx, cy, a, b] of [[140, 150, 70, 50], [250, 240, 80, 60], [120, 290, 40, 30], [290, 120, 30, 25]]) { ell(c, cx, cy, a, b, .4); c.fill(); } c.fillStyle = 'rgba(255,255,255,.55)'; for (const [cx, cy] of [[200, 90], [100, 220], [300, 300]]) { ell(c, cx, cy, 60, 12, .2); c.fill(); } }
    if (kind === 'venus') { c.strokeStyle = 'rgba(255,255,230,.35)'; c.lineWidth = 18; for (let i = 0; i < 6; i++) { c.beginPath(); c.moveTo(0, 60 + i * 60); c.bezierCurveTo(130, 30 + i * 60, 260, 100 + i * 60, 400, 50 + i * 60); c.stroke(); } }
    if (kind === 'uranus') { c.strokeStyle = 'rgba(255,255,255,.12)'; c.lineWidth = 14; for (let i = 0; i < 5; i++) { c.beginPath(); c.moveTo(0, 90 + i * 60); c.lineTo(S, 90 + i * 60); c.stroke(); } }
    c.restore();
  }, S, S);
  ctx.save();
  if (o.atmo) { ctx.fillStyle = rgrad(ctx, x, y, r * .9, r * (1 + .35 * o.atmo), [[0, `rgba(120,190,255,${.5 * o.atmo})`], [1, 'rgba(120,190,255,0)']]); circle(ctx, x, y, r * 1.4); ctx.fill(); }
  ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.drawImage(img, -r, -r, r * 2, r * 2); ctx.restore();
  // terminator shading (light from lx direction)
  const lx = o.light ?? -1; ctx.save(); circle(ctx, x, y, r); ctx.clip();
  const g = ctx.createLinearGradient(x + lx * r, y, x - lx * r, y); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.5, 'rgba(0,0,0,.08)'); g.addColorStop(1, `rgba(0,0,10,${o.dark ?? .75})`); ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  if (o.hot) { ctx.fillStyle = rgrad(ctx, x + lx * r * .6, y, r * .1, r * 1.2, [[0, `rgba(255,140,40,${.7 * o.hot})`], [1, 'rgba(255,60,0,0)']]); ctx.fillRect(x - r, y - r, r * 2, r * 2); }
  if (o.ice) { ctx.fillStyle = rgrad(ctx, x - lx * r * .6, y, r * .1, r * 1.2, [[0, `rgba(140,200,255,${.6 * o.ice})`], [1, 'rgba(60,120,255,0)']]); ctx.fillRect(x - r, y - r, r * 2, r * 2); }
  ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.strokeStyle = 'rgba(255,255,255,.12)'; ctx.lineWidth = Math.max(1, r * .03); ctx.beginPath(); ctx.arc(x, y, r - 1, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
}
function orbit(ctx, x, y, rx, ry, a = .35, dash = true) { ctx.save(); ctx.strokeStyle = `rgba(200,210,255,${a})`; ctx.lineWidth = 3; if (dash) ctx.setLineDash([10, 12]); ell(ctx, x, y, rx, ry); ctx.stroke(); ctx.restore(); }
function label(ctx, s, x, y, o = {}) { text(ctx, s, x, y, { size: o.size || 34, weight: o.weight || 800, color: o.color || '#fff', align: o.align || 'center', alpha: o.alpha ?? 1, shadow: 'rgba(0,0,0,.6)', track: o.track || 0 }); }
function arrow(ctx, x1, y1, x2, y2, col = '#fff', w = 6, p = 1) {
  const x = lerp(x1, x2, p), y = lerp(y1, y2, p); ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x, y); ctx.stroke();
  const a = Math.atan2(y2 - y1, x2 - x1); ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * w * 1.5, y + Math.sin(a) * w * 1.5); ctx.lineTo(x + Math.cos(a + 2.5) * w * 3.2, y + Math.sin(a + 2.5) * w * 3.2); ctx.lineTo(x + Math.cos(a - 2.5) * w * 3.2, y + Math.sin(a - 2.5) * w * 3.2); ctx.closePath(); ctx.fill(); ctx.restore();
}
// counter text
function counter(ctx, t, t0, t1, from, to, fmt, x, y, o = {}) { if (t < t0) return; const v = lerp(from, to, E.out(clamp((t - t0) / (t1 - t0)))); const k = E.back(clamp((t - t0) / .35)); ctx.save(); ctx.translate(x, y); ctx.scale(k, k); text(ctx, fmt(v), 0, 0, { size: o.size || 80, weight: 900, color: o.color || '#fff', shadow: o.shadow || 'rgba(0,0,0,.6)' }); ctx.restore(); }
// ---------- thermometer ----------
function thermo(ctx, x, y, h, val, min = -250, max = 500, o = {}) {
  const w = o.w || 46; const k = clamp((val - min) / (max - min)); const hot = val > 0;
  ctx.save(); ctx.fillStyle = 'rgba(255,255,255,.12)'; rr(ctx, x - w / 2 - 8, y - h - 8, w + 16, h + 16, w); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.lineWidth = 4; ctx.stroke();
  const col = val > 200 ? '#ff4a2a' : val > 0 ? '#ffb347' : val > -100 ? '#7fc8ff' : '#4f8cff';
  ctx.fillStyle = col; rr(ctx, x - w / 2 + 6, y - h * k, w - 12, h * k, w / 2); ctx.fill();
  circle(ctx, x, y + w * .6, w * .85); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.beginPath(); ctx.arc(x, y + w * .6, w * .85 + 4, 0, Math.PI * 2); ctx.stroke();
  for (let i = 0; i <= 6; i++) { const yy = y - h * i / 6; ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.fillRect(x + w / 2 + 10, yy - 2, 18, 4); }
  if (o.zero !== false) { const zy = y - h * clamp((0 - min) / (max - min)); ctx.fillStyle = 'rgba(255,255,255,.9)'; ctx.fillRect(x - w / 2 - 20, zy - 2, w + 40, 4); text(ctx, '0°', x - w / 2 - 34, zy, { size: 26, weight: 800, color: '#fff', align: 'right' }); }
  ctx.restore();
  if (o.readout !== false) text(ctx, `${val > 0 ? '+' : val < 0 ? '−' : ''}${Math.abs(Math.round(val))}°C`, x + w / 2 + 48, y - h * k, { size: o.size || 64, weight: 900, color: col, align: 'left', shadow: 'rgba(0,0,0,.6)' });
}
// ---------- Mercury surface (side view) ----------
function surface(ctx, t, mode = 'day', o = {}) { // mode: day | night | twilight
  const key = 'surf_' + mode;
  ctx.drawImage(cached(key, x => {
    x.fillStyle = '#020308'; x.fillRect(0, 0, W, H);
    const r = rng(3); for (let i = 0; i < 300; i++) { x.fillStyle = `rgba(255,255,255,${(mode === 'day' ? .25 : .9) * r()})`; circle(x, r() * W, r() * 640, .6 + r()); x.fill(); }
    const pal = mode === 'day' ? ['#b0602e', '#7a3a18', '#3a1608'] : mode === 'night' ? ['#3d4a66', '#232b40', '#0e121f'] : ['#7a6a5e', '#4a3f38', '#1f1a17'];
    // far hills
    x.fillStyle = pal[1]; x.beginPath(); x.moveTo(0, 700); for (let i = 0; i <= 40; i++) x.lineTo(i * 48, 640 - Math.abs(noise1(i * .4 + 3)) * 120 - (i % 7 === 0 ? 40 : 0)); x.lineTo(W, 760); x.lineTo(0, 760); x.fill();
    x.fillStyle = vgrad(x, 680, H, [[0, pal[0]], [1, pal[2]]]); x.beginPath(); x.moveTo(0, 720); for (let i = 0; i <= 40; i++) x.lineTo(i * 48, 700 + noise1(i * .7) * 18); x.lineTo(W, H); x.lineTo(0, H); x.fill();
    // craters + rocks
    for (let i = 0; i < 14; i++) { const cx = r() * W, cy = 760 + r() * 260, cr = 30 + r() * 110; x.fillStyle = 'rgba(0,0,0,.25)'; ell(x, cx, cy, cr, cr * .22); x.fill(); x.fillStyle = 'rgba(255,255,255,.06)'; ell(x, cx, cy - cr * .06, cr * .85, cr * .14); x.fill(); }
    for (let i = 0; i < 26; i++) { const cx = r() * W, cy = 740 + r() * 300, s = 8 + r() * 26; x.fillStyle = pal[2]; ell(x, cx, cy, s, s * .55); x.fill(); x.fillStyle = 'rgba(255,255,255,.08)'; ell(x, cx - s * .2, cy - s * .2, s * .5, s * .25); x.fill(); }
  }), 0, 0);
  if (mode === 'day') { // glow + heat shimmer
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = vgrad(ctx, 640, H, [[0, `rgba(255,120,30,${.25 * (o.heat ?? 1)})`], [1, `rgba(255,60,0,${.12 * (o.heat ?? 1)})`]]); ctx.fillRect(0, 640, W, H - 640);
    for (let i = 0; i < 12; i++) { const y = 700 + i * 30 + Math.sin(t * 3 + i) * 6; ctx.fillStyle = `rgba(255,200,120,${.04 + .03 * Math.sin(t * 4 + i * 2)})`; ctx.fillRect(0, y, W, 6); } ctx.restore();
  }
  if (mode === 'night') { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = vgrad(ctx, 640, H, [[0, 'rgba(100,160,255,.12)'], [1, 'rgba(60,100,200,.05)']]); ctx.fillRect(0, 640, W, H - 640); ctx.restore(); }
}
// frost creeping in from the frame edges
function frost(ctx, k, t = 0) {
  if (k <= 0) return; ctx.save();
  ctx.fillStyle = rgrad(ctx, W / 2, H / 2, H * (.75 - .4 * k), H * 1.05, [[0, 'rgba(150,200,255,0)'], [1, `rgba(190,225,255,${.45 * k})`]]); ctx.fillRect(0, 0, W, H);
  const r = rng(17); ctx.strokeStyle = `rgba(230,245,255,${.55 * k})`; ctx.lineWidth = 2;
  for (let i = 0; i < 70; i++) { const side = i % 4; let x = side === 0 ? r() * W : side === 1 ? W : side === 2 ? r() * W : 0, y = side === 0 ? 0 : side === 1 ? r() * H : side === 2 ? H : r() * H; const len = (40 + r() * 160) * k;
    const a = Math.atan2(H / 2 - y, W / 2 - x) + (r() - .5) * .8; ctx.beginPath(); ctx.moveTo(x, y); const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len; ctx.lineTo(x2, y2); ctx.stroke();
    for (let b = 1; b < 3; b++) { const bx = lerp(x, x2, b / 3), by = lerp(y, y2, b / 3); ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + Math.cos(a + .7) * len * .3, by + Math.sin(a + .7) * len * .3); ctx.moveTo(bx, by); ctx.lineTo(bx + Math.cos(a - .7) * len * .3, by + Math.sin(a - .7) * len * .3); ctx.stroke(); } }
  ctx.restore();
}
function heatHaze(ctx, k) { if (k <= 0) return; ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, W / 2, H / 2, H * .3, H, [[0, 'rgba(255,120,30,0)'], [1, `rgba(255,90,20,${.45 * k})`]]); ctx.fillRect(0, 0, W, H); ctx.restore(); }
// ---------- spacecraft / radar / comet ----------
function messenger(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(Math.sin(t * .5) * .05);
  ctx.fillStyle = '#2a3a6a'; for (const sx of [-1, 1]) { ctx.save(); ctx.scale(sx, 1); rr(ctx, 60, -24, 170, 48, 4); ctx.fill(); ctx.strokeStyle = '#8aa2d8'; ctx.lineWidth = 2; for (let i = 1; i < 6; i++) { ctx.beginPath(); ctx.moveTo(60 + i * 28, -24); ctx.lineTo(60 + i * 28, 24); ctx.stroke(); } ctx.fillStyle = '#9aa'; ctx.fillRect(40, -4, 22, 8); ctx.restore(); ctx.fillStyle = '#2a3a6a'; }
  ctx.fillStyle = '#d9c9a0'; rr(ctx, -46, -46, 92, 92, 8); ctx.fill(); ctx.fillStyle = '#efe4c6'; ctx.beginPath(); ctx.moveTo(-60, -60); ctx.lineTo(60, -60); ctx.lineTo(46, -46); ctx.lineTo(-46, -46); ctx.fill(); // sunshade
  ctx.fillStyle = '#888'; circle(ctx, 0, 52, 16); ctx.fill(); ctx.strokeStyle = '#ccc'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, -46); ctx.lineTo(0, -90); ctx.stroke(); circle(ctx, 0, -94, 6); ctx.fillStyle = '#ccc'; ctx.fill();
  ctx.restore();
}
function radarDish(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = '#c9ccd3'; ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(40, 0); ctx.lineTo(16, -120); ctx.lineTo(-16, -120); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.translate(0, -140); ctx.rotate(-.6); ctx.fillStyle = '#e8e8ee'; ctx.beginPath(); ctx.ellipse(0, 0, 150, 60, 0, Math.PI, 0, true); ctx.fill(); ctx.strokeStyle = '#999'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -110); ctx.stroke(); circle(ctx, 0, -114, 8); ctx.fillStyle = '#999'; ctx.fill(); ctx.restore();
  ctx.restore();
}
function radarWaves(ctx, x1, y1, x2, y2, t, col = '120,220,255') { const a = Math.atan2(y2 - y1, x2 - x1), d = Math.hypot(x2 - x1, y2 - y1); ctx.save(); ctx.translate(x1, y1); ctx.rotate(a); for (let i = 0; i < 6; i++) { const p = ((t * .6 + i / 6) % 1); ctx.strokeStyle = `rgba(${col},${.8 * (1 - p)})`; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(p * d, 0, 30 + p * 40, -.6, .6); ctx.stroke(); } ctx.restore(); }
function comet(ctx, x, y, s, ang, t) { ctx.save(); ctx.translate(x, y); ctx.rotate(ang); const g = ctx.createLinearGradient(0, 0, -420 * s, 0); g.addColorStop(0, 'rgba(180,230,255,.8)'); g.addColorStop(1, 'rgba(180,230,255,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, -18 * s); ctx.lineTo(-420 * s, -60 * s); ctx.lineTo(-420 * s, 60 * s); ctx.lineTo(0, 18 * s); ctx.fill(); ctx.fillStyle = '#e8f6ff'; circle(ctx, 0, 0, 20 * s); ctx.fill(); ctx.restore(); }
// ---------- section title card / big words ----------
function kinetic(ctx, t, t0, s, x, y, o = {}) { // slam-in word with a shake
  if (t < t0) return; const out = o.until ? 1 - clamp((t - o.until) / .25) : 1; if (out <= 0) return;
  const k = clamp((t - t0) / .22); const sc = lerp(1.8, 1, E.out(k)); ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(sc, sc); ctx.globalAlpha *= k * out;
  text(ctx, s, 0, 0, { size: o.size || 110, weight: 900, color: o.color || '#fff', stroke: o.stroke || 'rgba(0,0,0,.65)', sw: o.sw || 14, track: o.track || 0 }); ctx.restore();
}
function typeOn(ctx, t, t0, s, x, y, o = {}) { if (t < t0) return; const out = o.until ? 1 - clamp((t - o.until) / .3) : 1; if (out <= 0) return; const n = Math.min(s.length, Math.floor((t - t0) * (o.cps || 30))); ctx.save(); ctx.globalAlpha *= out; text(ctx, s.slice(0, n), x, y, { size: o.size || 60, weight: o.weight || 800, color: o.color || '#fff', align: o.align || 'center', shadow: 'rgba(0,0,0,.7)', track: o.track || 0 }); ctx.restore(); }
function strike(ctx, t, t0, x1, x2, y, col = '#ff4a3d') { if (t < t0) return; const p = E.out(clamp((t - t0) / .3)); ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = 12; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(lerp(x1, x2, p), y - 6); ctx.stroke(); ctx.restore(); }
function factChip(ctx, t, t0, s, x, y, o = {}) { L.chip(ctx, t, t0, s, x, y, { size: o.size || 38, bg: o.bg || '#4fd1ff', color: o.color || '#04121c', until: o.until }); }

module.exports = { cached, ASTRO, astro, stars, sun, planet, orbit, label, arrow, counter, thermo, surface, frost, heatHaze, messenger, radarDish, radarWaves, comet, kinetic, typeOn, strike, factChip };
