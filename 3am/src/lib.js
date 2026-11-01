// Core helpers: easing, math, noise, text, shapes, cinematic finishing.
const { createCanvas } = require('@napi-rs/canvas');

const W = 1920, H = 1080, FPS = 30;
const BAR = 86; // letterbox bar height (2.39-ish cinematic look like the reference)

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, v) => clamp((v - a) / (b - a));
const E = {
  lin: t => t,
  inOut: t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  back: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: t => (t === 0 || t === 1) ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI) / 3) + 1,
};
// animated value between times a..b
const tw = (t, a, b, from = 0, to = 1, ease = E.inOut) => lerp(from, to, ease(inv(a, b, t)));

// deterministic pseudo-random
function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const noise1 = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };

function canvas(w = W, h = H) { const c = createCanvas(w, h); return [c, c.getContext('2d')]; }

function rr(ctx, x, y, w, h, r) { // rounded rect path
  r = Math.min(r, w / 2, h / 2); ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function circle(ctx, x, y, r) { ctx.beginPath(); ctx.arc(x, y, Math.max(0.01, r), 0, Math.PI * 2); }
function ell(ctx, x, y, rx, ry, rot = 0) { ctx.beginPath(); ctx.ellipse(x, y, Math.max(.01, rx), Math.max(.01, ry), rot, 0, Math.PI * 2); }
function line(ctx, pts, w, col, cap = 'round') {
  ctx.beginPath(); ctx.moveTo(pts[0], pts[1]); for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
  ctx.lineWidth = w; ctx.strokeStyle = col; ctx.lineCap = cap; ctx.lineJoin = 'round'; ctx.stroke();
}
function quad(ctx, pts, w, col) { // smooth limb through 3 points
  ctx.beginPath(); ctx.moveTo(pts[0], pts[1]); ctx.quadraticCurveTo(pts[2], pts[3], pts[4], pts[5]);
  ctx.lineWidth = w; ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.stroke();
}
function vgrad(ctx, y0, y1, stops) { const g = ctx.createLinearGradient(0, y0, 0, y1); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }
function rgrad(ctx, x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }

function font(size, weight = 800, fam = 'Inter') { return `${weight} ${size}px ${fam}`; }
function text(ctx, s, x, y, { size = 60, weight = 800, color = '#fff', align = 'center', base = 'middle', fam = 'Inter', stroke = null, sw = 8, shadow = null, alpha = 1, track = 0 } = {}) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.font = font(size, weight, fam); ctx.textAlign = align; ctx.textBaseline = base;
  if (track) ctx.letterSpacing = track + 'px';
  if (shadow) { ctx.shadowColor = shadow; ctx.shadowBlur = size * .35; ctx.shadowOffsetY = size * .06; }
  if (stroke) { ctx.lineWidth = sw; ctx.strokeStyle = stroke; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
}
// Pop-in text with overshoot. t0 = appear time.
function popText(ctx, t, t0, s, x, y, o = {}) {
  if (t < t0) return; const k = E.back(inv(t0, t0 + .35, t)); const out = o.until ? 1 - inv(o.until, o.until + .25, t) : 1;
  if (out <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate((o.rot || 0)); ctx.scale(k, k); text(ctx, s, 0, 0, { ...o, alpha: (o.alpha ?? 1) * clamp(k) * out }); ctx.restore();
}
// Label chip (rounded box + text)
function chip(ctx, t, t0, s, x, y, { size = 44, bg = '#f5b83d', color = '#1a1208', pad = 26, rot = 0, until = null } = {}) {
  if (t < t0) return; const k = E.back(inv(t0, t0 + .35, t)); const out = until ? 1 - inv(until, until + .25, t) : 1; if (out <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k, k); ctx.globalAlpha *= clamp(k) * out;
  ctx.font = font(size, 900); const w = ctx.measureText(s).width + pad * 2, h = size * 1.55;
  ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
  rr(ctx, -w / 2, -h / 2, w, h, h * .28); ctx.fillStyle = bg; ctx.fill(); ctx.shadowColor = 'transparent';
  text(ctx, s, 0, size * .04, { size, weight: 900, color }); ctx.restore();
}

// Speech bubble anchored with a tail toward (tx,ty)
function bubble(ctx, t, t0, s, x, y, tx, ty, { size = 40, until = null, bg = '#fffaf0', color = '#1b1b22', maxW = 640 } = {}) {
  if (t < t0) return; const k = E.back(inv(t0, t0 + .3, t)); const out = until ? 1 - inv(until, until + .2, t) : 1; if (out <= 0) return;
  ctx.save(); ctx.globalAlpha *= clamp(k) * out; ctx.font = font(size, 800);
  // wrap
  const words = s.split(' '); const lines = []; let cur = '';
  for (const w of words) { const tst = cur ? cur + ' ' + w : w; if (ctx.measureText(tst).width > maxW && cur) { lines.push(cur); cur = w; } else cur = tst; }
  lines.push(cur);
  const lw = Math.max(...lines.map(l => ctx.measureText(l).width)); const bw = lw + 60, bh = lines.length * size * 1.25 + 44;
  ctx.translate(x, y); ctx.scale(k, k);
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 6; ctx.fillStyle = bg;
  rr(ctx, -bw / 2, -bh / 2, bw, bh, 30); ctx.fill();
  const dx = (tx - x) / k, dy = (ty - y) / k; const ang = Math.atan2(dy, dx); const bx = Math.cos(ang) * Math.min(bw, bh) * .35, by = Math.sin(ang) * bh * .35;
  ctx.beginPath(); ctx.moveTo(bx - 18 * Math.sin(ang), by + 18 * Math.cos(ang)); ctx.lineTo(dx * .55, dy * .55); ctx.lineTo(bx + 18 * Math.sin(ang), by - 18 * Math.cos(ang)); ctx.closePath(); ctx.fill();
  ctx.shadowColor = 'transparent';
  lines.forEach((l, i) => text(ctx, l, 0, (i - (lines.length - 1) / 2) * size * 1.25 + 2, { size, weight: 800, color }));
  ctx.restore();
}

// Big check / cross marks
function check(ctx, x, y, s, col = '#5fd16a', k = 1) { line(ctx, [x - s * .5, y, x - s * .12, y + s * .4 * k, x - s * .12 + s * .65 * k, y + s * .4 - s * .85 * k], s * .2, col); }
function cross(ctx, x, y, s, col = '#ff5a4f', k = 1) { const a = s * .45 * k; line(ctx, [x - a, y - a, x + a, y + a], s * .2, col); if (k > .5) line(ctx, [x + a, y - a, x - a, y + a], s * .2, col); }

// ---------- cinematic finishing ----------
let _vig = null, _grain = [];
function vignette(ctx, strength = .55) {
  if (!_vig) {
    const [c, x] = canvas(); x.fillStyle = rgrad(x, W / 2, H / 2, H * .35, H * 1.05, [[0, 'rgba(0,0,0,0)'], [.6, 'rgba(0,0,0,.25)'], [1, 'rgba(0,0,0,.85)']]); x.fillRect(0, 0, W, H); _vig = c;
  }
  ctx.save(); ctx.globalAlpha = strength; ctx.drawImage(_vig, 0, 0); ctx.restore();
}
function grain(ctx, f, a = .06) {
  if (!_grain.length) {
    for (let k = 0; k < 6; k++) {
      const [c, x] = canvas(480, 270); const id = x.createImageData(480, 270); const r = rng(99 + k * 7);
      for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
      x.putImageData(id, 0, 0); _grain.push(c);
    }
  }
  ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'overlay'; ctx.imageSmoothingEnabled = false;
  ctx.drawImage(_grain[f % 6], 0, 0, W, H); ctx.restore();
}
function letterbox(ctx) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, BAR); ctx.fillRect(0, H - BAR, W, BAR); }

// Floating dust motes in light (like the reference)
function dust(ctx, t, n = 60, seed = 1, col = 'rgba(255,220,150,', area = [0, 0, W, H]) {
  const r = rng(seed); ctx.save();
  for (let i = 0; i < n; i++) {
    const bx = r(), by = r(), sp = .2 + r() * .8, sz = 1 + r() * 3.2, ph = r() * 10;
    const x = area[0] + ((bx * area[2] + t * 14 * sp + Math.sin(t * .6 + ph) * 18) % area[2]);
    const y = area[1] + ((by * area[3] - t * 6 * sp + area[3] * 10) % area[3]);
    const a = (.25 + .5 * (.5 + .5 * Math.sin(t * 1.3 + ph))) * .8;
    ctx.fillStyle = col + a.toFixed(3) + ')'; circle(ctx, x, y, sz); ctx.fill();
  }
  ctx.restore();
}
// God rays from a sun position
function rays(ctx, sx, sy, t, { n = 9, len = 1600, col = 'rgba(255,230,170,', a = .16, spread = 1.1, dir = Math.PI * .72 } = {}) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < n; i++) {
    const ang = dir - spread / 2 + spread * (i + .5) / n + Math.sin(t * .25 + i) * .015; const w = .025 + hash(i * 3.3) * .05;
    const g = ctx.createLinearGradient(sx, sy, sx + Math.cos(ang) * len, sy + Math.sin(ang) * len);
    const aa = a * (.5 + .5 * hash(i * 9.1)) * (.75 + .25 * Math.sin(t * .7 + i * 2));
    g.addColorStop(0, col + aa + ')'); g.addColorStop(1, col + '0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(ang - w) * len, sy + Math.sin(ang - w) * len); ctx.lineTo(sx + Math.cos(ang + w) * len, sy + Math.sin(ang + w) * len); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
function sunDisc(ctx, x, y, r, col = '255,244,214') {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = rgrad(ctx, x, y, r * .2, r * 4.5, [[0, `rgba(${col},.75)`], [.25, `rgba(${col},.25)`], [1, `rgba(${col},0)`]]); ctx.fillRect(x - r * 5, y - r * 5, r * 10, r * 10);
  ctx.restore(); ctx.fillStyle = `rgb(${col})`; circle(ctx, x, y, r); ctx.fill();
}

module.exports = { W, H, FPS, BAR, clamp, lerp, inv, E, tw, rng, hash, noise1, canvas, rr, circle, ell, line, quad, vgrad, rgrad, font, text, popText, chip, bubble, check, cross, vignette, grain, letterbox, dust, rays, sunDisc };
