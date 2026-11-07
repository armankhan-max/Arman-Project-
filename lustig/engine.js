'use strict';
// "The Man Who Sold the Eiffel Tower Twice" - one continuous camera over one world.
// Everything here is drawn in code. window.renderFrame(t) draws frame at time t (s).

const W = 1280, H = 720, FPS = 24, DUR = 81.12, WW = 4800, WH = 3000, RES = 2;
const RED = '#d4232d', REDG = 'rgba(235,40,50,0.85)', INK = '#1c1a17', PAPER = '#ebe6da';
const cv = document.getElementById('c'), out = cv.getContext('2d');

// ------------------------------------------------------------ helpers
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = Math.ceil(w); c.height = Math.ceil(h); return c; };
const clamp = (x, a, b) => Math.max(a, Math.min(b, x)), c01 = x => clamp(x, 0, 1);
const lerp = (a, b, t) => a + (b - a) * t;
const eio = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const eoc = t => 1 - Math.pow(1 - t, 3);
const eoq = t => 1 - Math.pow(1 - t, 5);
const sstep = (a, b, x) => { const t = c01((x - a) / (b - a)); return t * t * (3 - 2 * t); };
function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function hash2(x, y) { let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(hash2(xi, yi), hash2(xi + 1, yi), u), lerp(hash2(xi, yi + 1), hash2(xi + 1, yi + 1), u), v);
}
function fbm(x, y, o = 4) { let s = 0, a = .5, f = 1, n = 0; for (let i = 0; i < o; i++) { s += a * vnoise(x * f + i * 17, y * f); n += a; f *= 2; a *= .5; } return s / n; }
function cache(w, h, draw) { const c = mk(w * RES, h * RES), g = c.getContext('2d'); g.scale(RES, RES); draw(g, w, h); c.w = w; c.h = h; return c; }
function crSample(pts, step = 12) { // catmull-rom through pts -> dense polyline
  const outp = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    const n = Math.max(2, Math.ceil(Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step));
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      outp.push([0, 1].map(j => .5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
    }
  }
  outp.push(pts[pts.length - 1].slice());
  return outp;
}
function polyLen(p) { let L = [0]; for (let i = 1; i < p.length; i++) L.push(L[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1])); return L; }
function polyAt(p, L, f) { // point + angle at fraction f of arc length
  const d = c01(f) * L[L.length - 1]; let i = 1; while (i < L.length - 1 && L[i] < d) i++;
  const s = (d - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]);
  return { x: lerp(p[i - 1][0], p[i][0], s), y: lerp(p[i - 1][1], p[i][1], s), a: Math.atan2(p[i][1] - p[i - 1][1], p[i][0] - p[i - 1][0]) };
}
function quad(a, c, b, n = 40) { const r = []; for (let i = 0; i <= n; i++) { const t = i / n; r.push([(1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]]); } return r; }
function pathPoly(g, p) { g.beginPath(); g.moveTo(p[0][0], p[0][1]); for (let i = 1; i < p.length; i++) g.lineTo(p[i][0], p[i][1]); }
function blob(cx, cy, rx, ry, amt, seed, n = 72) {
  const p = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, k = 1 + amt * (fbm(Math.cos(a) * 2 + seed, Math.sin(a) * 2 + seed, 3) - .5) * 2; p.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]); }
  p.push(p[0].slice()); return p;
}
function grey(g, x, y, w, h, gap, seed, col = 'rgba(60,58,52,0.22)', lw = 4) { // soft grey body-copy lines
  const r = rng(seed); g.fillStyle = col;
  for (let yy = y; yy < y + h; yy += gap) { const ww = (r() < .15 ? .4 + r() * .3 : .85 + r() * .15) * w; g.fillRect(x, yy, ww, lw); }
}
function paperTex(g, w, h, seed, amt = 18) { // grain + soft stains on paper
  const r = rng(seed);
  for (let i = 0; i < 6; i++) { const x = r() * w, y = r() * h, rad = 40 + r() * w * .5; const gr = g.createRadialGradient(x, y, 0, x, y, rad); gr.addColorStop(0, `rgba(120,100,70,${.03 + r() * .05})`); gr.addColorStop(1, 'rgba(120,100,70,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }
  for (let i = 0; i < w * h / 30; i++) { g.fillStyle = r() < .5 ? `rgba(0,0,0,${r() * amt / 255})` : `rgba(255,255,255,${r() * amt / 255})`; g.fillRect(r() * w, r() * h, 1, 1); }
  const e = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * .35, w / 2, h / 2, Math.hypot(w, h) * .6); e.addColorStop(0, 'rgba(90,70,40,0)'); e.addColorStop(1, 'rgba(90,70,40,0.18)'); g.fillStyle = e; g.fillRect(0, 0, w, h);
}
function spaced(g, txt, x, y, sp) { g.letterSpacing = sp + 'px'; g.fillText(txt, x, y); g.letterSpacing = '0px'; }

// ------------------------------------------------------------ timeline data
const EV = [];                  // sound events for the audio mixer
const ev = (t, type, o = {}) => EV.push(Object.assign({ t: +t.toFixed(3), type }, o));
const SHAKES = [];              // [time, amplitude px]

// camera moves: [start, duration, cx, cy, zoom]
const CAM0 = { x: 1270, y: 1640, z: 1.15 };
const MOVES = [
  [3.62, 1.0, 1420, 1600, 0.85],
  [7.95, 1.4, 1265, 1560, 1.3],
  [9.3, 0.9, 1430, 1700, 1.0],
  [11.05, 1.0, 1950, 2340, 1.0],
  [14.45, 1.25, 1900, 860, 1.15],
  [16.75, 1.0, 2200, 830, 0.86],
  [19.45, 1.25, 2480, 1330, 0.82],
  [22.2, 1.15, 2720, 1680, 0.7],
  [25.4, 1.1, 2560, 850, 1.05],
  [28.15, 0.9, 2540, 860, 1.25],
  [31.75, 2.6, 2570, 880, 1.45],
  [35.25, 1.15, 2660, 1880, 1.15],
  [40.55, 1.4, 2700, 1860, 1.28],
  [42.95, 1.1, 2430, 1760, 0.98],
  [45.75, 1.4, 2470, 1800, 1.85],
  [47.55, 1.0, 2440, 1770, 0.98],
  [52.15, 1.2, 1265, 1650, 1.05],
  [55.3, 1.4, 3050, 900, 0.62],
  [57.05, 2.0, 3350, 840, 0.74],
  [59.2, 1.0, 3800, 1250, 1.1],
  [62.95, 1.35, 2470, 1760, 1.0],
  [67.25, 1.4, 1960, 1790, 0.56],
  [69.45, 1.3, 3000, 1000, 0.62],
  [71.0, 1.0, 2730, 1950, 0.7],
  [72.9, 1.1, 2580, 850, 0.98],
  [75.25, 1.2, 3620, 1890, 0.9],
  [78.0, 2.5, 2150, 1450, 0.29],
];
// Camera: one continuous spline through waypoints. Velocity is never zero, so no stop-and-go.
const DRIFTS = [[7, 3], [-6, 4], [5, -4], [-5, -3]];
const KF = (() => {
  const k = [{ t: 0, x: CAM0.x, y: CAM0.y, z: Math.log(CAM0.z) }];
  MOVES.forEach(([ts, d, x, y, z], i) => {
    const ta = ts + Math.min(d, .5) * .3, nx = i + 1 < MOVES.length ? MOVES[i + 1][0] : DUR;
    k.push({ t: ta, x, y, z: Math.log(z) });
    const hold = nx - ta;   // stay on the hero during the hold: slow push, then leave
    if (hold > 1.2) { const dv = DRIFTS[i % 4]; k.push({ t: nx - Math.min(.35, hold * .2), x: x + dv[0] * hold / z, y: y + dv[1] * hold / z, z: Math.log(z * (1 + .022 * hold)) }); }
  });
  const l = k[k.length - 1]; k.push({ t: DUR + 1, x: l.x + 30, y: l.y + 12, z: l.z * 1 });
  const TEN = .42;
  k.forEach((q, i) => {
    const p = k[Math.max(0, i - 1)], n = k[Math.min(k.length - 1, i + 1)], dt = Math.max(1e-3, n.t - p.t);
    q.mx = TEN * (n.x - p.x) / dt; q.my = TEN * (n.y - p.y) / dt; q.mz = TEN * (n.z - p.z) / dt;
  });
  return k;
})();
function camBase(t) {
  let i = 0; while (i < KF.length - 2 && t >= KF[i + 1].t) i++;
  const a = KF[i], b = KF[i + 1], dt = b.t - a.t, u = c01((t - a.t) / dt), u2 = u * u, u3 = u2 * u;
  const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
  const f = (p, q, mp, mq) => h00 * p + h10 * dt * mp + h01 * q + h11 * dt * mq;
  return { x: f(a.x, b.x, a.mx, b.mx), y: f(a.y, b.y, a.my, b.my), z: Math.exp(f(a.z, b.z, a.mz, b.mz)) };
}
// fast = the scheme / escape / round two; slow = backstory, suspicion, silence
const FAST = [[14.7, 31.8], [52.4, 59.4], [69.6, 81.2]];
function pace(t) { let f = 0; for (const [a, b] of FAST) f = Math.max(f, sstep(a - .4, a + .3, t) * (1 - sstep(b - .3, b + .4, t))); return f; }
const PUNCH = [[.52, .06], [3.0, .08], [4.6, .03], [8.58, .04], [13.8, .05], [15.1, .05], [17.74, .04], [21.22, .03], [23.1, .04], [24.78, .03],
  [26.86, .03], [28.88, .05], [30.76, .04], [34.8, .12], [36.6, .04], [38.48, .04], [39.8, .05], [42.42, .04], [45.3, .06], [51.6, .05],
  [53.44, .07], [56.56, .03], [58.84, .04], [62.3, .07], [68.66, .04], [71.7, .04], [74.4, .04], [77.46, .08], [80.3, .06]];
function punch(t) { let z = 0; for (const [ts, a] of PUNCH) { const d = t - ts + .04; if (d > 0 && d < 1.6) z += a * (1 - Math.exp(-d * 30)) * Math.exp(-d * 3.2); } return z; }
function shakeAt(t) {
  let x = 0, y = 0;
  for (const [ts, a] of SHAKES) { const d = t - ts; if (d < 0 || d > .6) continue; const e = a * Math.exp(-d * 9); x += e * Math.sin(d * 71 + ts); y += e * Math.cos(d * 59 + ts * 3); }
  return [x, y];
}
function camera(t) {
  const c = camBase(t), [sx, sy] = shakeAt(t), hh = .6 + .9 * pace(t);
  c.z *= 1 + punch(t);
  c.hx = (2.4 * Math.sin(t * .9) + 1.3 * Math.sin(t * 2.3 + 1) + .5 * Math.sin(t * 5.3 + 2)) * hh + sx;
  c.hy = (1.9 * Math.sin(t * .7 + 3) + 1.1 * Math.sin(t * 2.9) + .5 * Math.sin(t * 4.7 + 1)) * hh + sy;
  c.r = .0018 * Math.sin(t * .6) + .0008 * Math.sin(t * 1.7 + 2);
  return c;
}

// hero schedule: listed ids stay bright, everything else dims
const HERO = [
  [0, ['eiffel']],
  [4.3, ['eiffel', 'tag', 'pinE']],
  [5.9, ['eiffel', 'permit', 'tag']],
  [8.15, ['eiffel']],
  [9.45, ['eiffel', 'paint']],
  [11.3, ['news']],
  [14.6, ['lustig']],
  [16.8, ['lustig', 'letter']],
  [19.6, ['crillon', 'lustig', 'pinC', 'lLC']],
  [22.4, ['crillon', 'pinC', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'lD']],
  [25.55, ['letter']],
  [35.45, ['d2', 'hook']],
  [40.6, ['d2', 'watch', 'hook']],
  [43.0, ['lustig', 'd2', 'lLP']],
  [45.15, ['env', 'lustig', 'd2', 'lLP']],
  [45.95, ['env']],
  [47.5, ['d2', 'env', 'lustig', 'lLP']],
  [52.2, ['eiffel']],
  [55.35, ['pinC', 'pinG', 'route', 'train', 'case']],
  [59.3, ['stack']],
  [63.1, ['d2', 'lustig']],
  [67.5, ['d2', 'eiffel', 'lPE']],
  [69.5, ['pinC', 'pinG', 'route', 'train']],
  [71.15, ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'crillon']],
  [72.95, ['letter', 'copy']],
  [75.35, ['police', 'pinP', 'r2', 'lRP']],
  [78.05, null],
];
const DIM = 0.66;
function dimOf(id, t) {
  let prev = 0, k = 0;
  for (; k < HERO.length && HERO[k][0] <= t; k++);
  const val = i => (i < 0 || HERO[i][1] === null || HERO[i][1].includes(id)) ? 0 : DIM;
  if (k === 0) return val(0);
  const cur = val(k - 1); prev = k >= 2 ? val(k - 2) : cur;
  return lerp(prev, cur, sstep(0, .45, t - HERO[k - 1][0]));
}

// red grade moments (0..1)
function redAmt(t) {
  return Math.max(
    .32 * sstep(32.9, 34.2, t) * (1 - sstep(34.6, 34.75, t)),
    sstep(34.66, 34.82, t) * (1 - sstep(35.2, 36.4, t)),
    sstep(45.8, 46.1, t) * (1 - sstep(47.0, 48.2, t))
  );
}

// ------------------------------------------------------------ assets
const IMG = {};
function loadImg(k, src) { return new Promise(r => { const i = new Image(); i.onload = () => { IMG[k] = i; r(); }; i.src = src; }); }

function bwPhoto(img, w, h, { contrast = 1.18, lift = 16, seed = 1, sepia = 0 } = {}) {
  const c = mk(w, h), g = c.getContext('2d');
  const ir = img.width / img.height, r = w / h; let sw, sh, sx, sy;
  if (ir > r) { sh = img.height; sw = sh * r; sx = (img.width - sw) / 2; sy = 0; } else { sw = img.width; sh = sw / r; sx = 0; sy = (img.height - sh) / 2; }
  g.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
  const d = g.getImageData(0, 0, w, h), p = d.data, R = rng(seed);
  for (let i = 0; i < p.length; i += 4) {
    let l = (.3 * p[i] + .59 * p[i + 1] + .11 * p[i + 2]) / 255;
    l = c01(.5 + (l - .5) * contrast); l = l * l * (3 - 2 * l) * .35 + l * .65;
    const v = lift + l * (232 - lift) + (R() - .5) * 16;
    p[i] = v * (1 + .03 * sepia); p[i + 1] = v * (1 + .005 * sepia); p[i + 2] = v * (1 - .04 * sepia);
  }
  g.putImageData(d, 0, 0);
  const gr = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * .3, w / 2, h / 2, Math.max(w, h) * .75);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,.38)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  return c;
}
function makePrint(img, pw, ph, opt = {}) {
  const b = 14, bb = opt.bb || 52, w = pw + 2 * b, h = ph + b + bb;
  const photo = bwPhoto(img, pw * RES, ph * RES, opt);
  const c = cache(w, h, (g) => {
    g.fillStyle = '#ece8df'; g.fillRect(0, 0, w, h);
    paperTex(g, w, h, opt.seed || 3, 10);
    g.drawImage(photo, b, b, pw, ph);
    g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 1; g.strokeRect(b + .5, b + .5, pw - 1, ph - 1);
  });
  c.photo = { x: b, y: b, w: pw, h: ph, cv: photo }; c.bb = bb;
  return c;
}
function makeRust(print) { // 8 progressive rust overlays for the Eiffel print
  const ph = print.photo, w = ph.cv.width, h = ph.cv.height, src = ph.cv.getContext('2d').getImageData(0, 0, w, h).data;
  const K = 8, base = new Float32Array(w * h), rev = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x, l = src[i * 4] / 255, dk = Math.pow(c01((0.5 - l) / 0.38), 1.05);
    const n = fbm(x / 26, y / 26, 3);
    base[i] = dk * (.35 + .65 * n);
    rev[i] = .55 * fbm(x / 70 + 9, y / 70, 3) + .45 * (y / h);
  }
  const stages = [];
  for (let k = 1; k <= K; k++) {
    const c = mk(w, h), g = c.getContext('2d'), d = g.createImageData(w, h), p = d.data, thr = k / K;
    for (let i = 0; i < w * h; i++) {
      const vis = c01((rev[i] - (1 - thr * 1.15)) * 7);
      const a = base[i] * vis;
      p[i * 4] = 158; p[i * 4 + 1] = 66 + 26 * base[i]; p[i * 4 + 2] = 24; p[i * 4 + 3] = clamp(a * 255 * .95, 0, 215);
    }
    g.putImageData(d, 0, 0); stages.push(c);
  }
  return stages;
}

function makeStamp(text, w, h, seed, size) {
  return cache(w, h, (g) => {
    g.strokeStyle = RED; g.fillStyle = RED;
    g.lineWidth = 5; g.strokeRect(5, 5, w - 10, h - 10);
    g.lineWidth = 2; g.strokeRect(13, 13, w - 26, h - 26);
    g.font = `700 ${size || h * .55}px Osw`; g.textAlign = 'center'; g.textBaseline = 'middle';
    spaced(g, text, w / 2 + (size ? size * .04 : 4), h / 2 + 2, Math.round((size || h * .55) * .08));
    g.globalCompositeOperation = 'destination-out';
    const r = rng(seed);
    for (let i = 0; i < w * h / 9; i++) { g.fillStyle = `rgba(0,0,0,${r() * .9})`; const s = r() * 2.2; g.fillRect(r() * w, r() * h, s, s); }
    for (let i = 0; i < 9; i++) { g.fillStyle = 'rgba(0,0,0,.5)'; g.beginPath(); g.ellipse(r() * w, r() * h, 4 + r() * 18, 2 + r() * 6, r() * 3, 0, 7); g.fill(); }
  });
}

function seal(g, x, y, r, txt) {
  g.save(); g.strokeStyle = 'rgba(40,40,60,.75)'; g.fillStyle = 'rgba(40,40,60,.75)';
  g.lineWidth = 2; g.beginPath(); g.arc(x, y, r, 0, 7); g.stroke(); g.lineWidth = 1; g.beginPath(); g.arc(x, y, r - 6, 0, 7); g.stroke();
  g.font = `600 ${r * .7}px Corm`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(txt, x, y + 1);
  g.font = `400 ${r * .2}px Osw`;
  const s = 'RÉPUBLIQUE FRANÇAISE · ';
  for (let i = 0; i < s.length; i++) { const a = -Math.PI / 2 + i / s.length * Math.PI * 2; g.save(); g.translate(x + Math.cos(a) * (r - 11), y + Math.sin(a) * (r - 11)); g.rotate(a + Math.PI / 2); g.fillText(s[i], 0, 0); g.restore(); }
  g.restore();
}

const DOC = {}; // measured anchor points inside documents (local, origin at top-left)
function makeLetter(copy) {
  const w = 440, h = 600;
  return cache(w, h, (g) => {
    g.fillStyle = copy ? '#e4dfd2' : '#efeadf'; g.fillRect(0, 0, w, h); paperTex(g, w, h, copy ? 41 : 40, 12);
    g.fillStyle = INK; g.textAlign = 'center';
    g.font = '400 11px Osw'; spaced(g, 'RÉPUBLIQUE FRANÇAISE', w / 2 + 20, 44, 4);
    g.font = '600 27px Corm'; g.fillText('MINISTÈRE DES POSTES', w / 2 + 20, 82);
    g.font = '600 20px Corm'; g.fillText('ET DES TÉLÉGRAPHES', w / 2 + 20, 106);
    seal(g, 62, 74, 34, 'RF');
    g.fillRect(40, 124, w - 80, 2); g.fillRect(40, 129, w - 80, .8);
    g.textAlign = 'left'; g.font = '12px Elite'; g.fillStyle = 'rgba(28,26,23,.85)';
    g.fillText('Direction Générale — Cabinet', 44, 154);
    g.textAlign = 'right'; g.fillText('Paris, le 3 mai 1925', w - 44, 176);
    if (copy) { g.textAlign = 'left'; g.font = '16px Elite'; g.fillStyle = 'rgba(28,26,23,.9)'; LETTER_LINES.forEach((s, i) => g.fillText(s, 44, 244 + i * 36)); }
    grey(g, 44, 360, w - 88, 110, 17, 5);
    g.strokeStyle = 'rgba(25,30,70,.8)'; g.lineWidth = 1.6; g.beginPath();
    const r = rng(8); g.moveTo(262, 528); for (let i = 0; i < 26; i++) g.lineTo(262 + i * 5.5, 522 + Math.sin(i * 1.3) * 12 * r());
    g.stroke();
    g.font = '11px Elite'; g.fillStyle = 'rgba(28,26,23,.8)'; g.textAlign = 'left'; g.fillText('Le Directeur Général adjoint', 240, 560);
  });
}
const LETTER_LINES = ['Objet : Démolition de la Tour Eiffel', 'Lot : 7 000 tonnes de fer', 'Adjudication au plus offrant.'];

function makeNews() {
  const w = 480, h = 640;
  return cache(w, h, (g) => {
    g.fillStyle = '#e8e2d2'; g.fillRect(0, 0, w, h); paperTex(g, w, h, 21, 14);
    g.fillStyle = INK; g.textAlign = 'center';
    g.font = '700 50px Play'; g.fillText('Le Quotidien', w / 2, 68);
    g.fillRect(24, 84, w - 48, 2);
    g.font = '11px Elite'; spaced(g, 'MARDI 5 MAI 1925  ·  PARIS  ·  15 CENTIMES', w / 2, 101, 1);
    g.fillRect(24, 110, w - 48, 1); g.fillRect(24, 114, w - 48, 2.5);
    g.font = '700 40px Play'; g.fillText('FAUT-IL DÉMOLIR', w / 2, 166); g.fillText('LA TOUR EIFFEL ?', w / 2, 212);
    g.font = '700 40px Play';
    const full = g.measureText('FAUT-IL DÉMOLIR').width, pre = g.measureText('FAUT-IL ').width, word = g.measureText('DÉMOLIR').width;
    DOC.news = { x: w / 2 - full / 2 + pre + word / 2 + 8, y: 152, rx: word / 2 + 12, ry: 29 };
    g.fillRect(24, 232, w - 48, 1);
    const ph = bwPhoto(IMG.eiffel, 200 * RES, 180 * RES, { seed: 4, contrast: 1.3 });
    g.drawImage(ph, 26, 246, 200, 180); g.strokeStyle = 'rgba(0,0,0,.5)'; g.strokeRect(26, 246, 200, 180);
    grey(g, 26, 436, 200, 60, 12, 31, 'rgba(50,48,42,.25)', 3);
    grey(g, 240, 248, 214, 250, 12, 32, 'rgba(50,48,42,.25)', 3);
    g.fillRect(24, 510, w - 48, 1);
    for (let c = 0; c < 3; c++) grey(g, 26 + c * 146, 524, 132, 100, 12, 33 + c, 'rgba(50,48,42,.25)', 3);
  });
}
function makeMiniNews(i, blank) {
  const w = 300, h = 400, days = ['6', '7', '8', '9', '11', '12'];
  return cache(w, h, (g) => {
    g.fillStyle = i % 2 ? '#e6e0cf' : '#ebe5d6'; g.fillRect(0, 0, w, h); paperTex(g, w, h, 60 + i, 14);
    g.fillStyle = INK; g.textAlign = 'center'; g.font = '700 32px Play'; g.fillText('Le Quotidien', w / 2, 44);
    g.fillRect(16, 54, w - 32, 1.5);
    g.font = '10px Elite'; g.fillText(`${days[i]} MAI 1925`, w / 2, 68); g.fillRect(16, 74, w - 32, 2);
    const r = rng(70 + i); g.fillStyle = 'rgba(30,28,24,.55)';
    g.fillRect(30, 88, 240 * (.7 + .3 * r()), 14); g.fillRect(50, 108, 200 * (.6 + .3 * r()), 14);
    for (let c = 0; c < 3; c++) grey(g, 18 + c * 92, 136, 82, 250, 10, 80 + i * 3 + c, 'rgba(50,48,42,.28)', 2.5);
    if (blank) { g.fillStyle = '#ebe5d6'; g.fillRect(108, 200, 88, 110); DOC.blank = { x: 152, y: 255, rx: 70, ry: 78 }; }
  });
}
function makePolice() {
  const w = 420, h = 560;
  return cache(w, h, (g) => {
    g.fillStyle = '#e9e4d6'; g.fillRect(0, 0, w, h); paperTex(g, w, h, 90, 12);
    g.fillStyle = INK; g.textAlign = 'center';
    seal(g, w / 2, 62, 32, 'PP');
    g.font = '600 26px Corm'; g.fillText('PRÉFECTURE DE POLICE', w / 2, 132);
    g.font = '400 13px Osw'; spaced(g, 'PROCÈS-VERBAL', w / 2 + 3, 156, 5);
    g.fillRect(40, 170, w - 80, 1.5);
    g.textAlign = 'left'; g.font = '14px Elite';
    g.fillText('N° 1925 — 2187', 44, 200); g.fillText('Plainte : escroquerie', 44, 226);
    grey(g, 44, 256, w - 88, 230, 17, 91);
  });
}
function makeDealer(i, seed) {
  const w = 150, h = 192;
  return cache(w, h, (g) => {
    const r = rng(seed);
    g.fillStyle = '#ebe7de'; g.fillRect(0, 0, w, h); paperTex(g, w, h, seed, 10);
    const px = 10, py = 10, pw = 130, ph = 142;
    const bg = g.createLinearGradient(0, py, 0, py + ph); const v = 120 + r() * 60;
    bg.addColorStop(0, `rgb(${v},${v},${v})`); bg.addColorStop(1, `rgb(${v * .55},${v * .55},${v * .55})`);
    g.fillStyle = bg; g.fillRect(px, py, pw, ph);
    g.save(); g.beginPath(); g.rect(px, py, pw, ph); g.clip();
    const cx = px + pw / 2 + (r() - .5) * 10, hy = py + 62 + r() * 8, sk = 30 + r() * 6;
    g.fillStyle = `rgb(${18 + r() * 20},${18 + r() * 20},${20 + r() * 20})`;
    g.beginPath(); g.moveTo(cx - 70, py + ph); g.bezierCurveTo(cx - 62, hy + 40, cx - 40, hy + 30, cx - 14, hy + 26); g.lineTo(cx + 14, hy + 26); g.bezierCurveTo(cx + 40, hy + 30, cx + 62, hy + 40, cx + 70, py + ph); g.fill();
    g.beginPath(); g.ellipse(cx, hy, sk * .62, sk * .78, 0, 0, 7); g.fill();
    g.fillRect(cx - 8, hy + 14, 16, 18);
    const style = i % 3;
    if (style === 0) { g.beginPath(); g.ellipse(cx, hy - sk * .55, sk * .6, sk * .55, 0, Math.PI, 0); g.fill(); g.fillRect(cx - sk * .95, hy - sk * .58, sk * 1.9, 5); }
    else if (style === 1) { g.fillRect(cx - sk * .5, hy - sk * 1.25, sk, sk * .7); g.fillRect(cx - sk * 1.05, hy - sk * .6, sk * 2.1, 5); }
    else { g.beginPath(); g.moveTo(cx - sk * .7, hy - sk * .45); g.quadraticCurveTo(cx, hy - sk * 1.3, cx + sk * .9, hy - sk * .4); g.fill(); g.fillRect(cx - sk * .8, hy - sk * .5, sk * 1.8, 5); }
    g.fillStyle = 'rgba(255,255,255,.14)'; g.fillRect(cx - 4, hy + 32, 8, 30);
    g.restore();
    const ph2 = g.getImageData(px * RES, py * RES, pw * RES, ph * RES), d = ph2.data;
    for (let k = 0; k < d.length; k += 4) { const n = (r() - .5) * 26; d[k] += n; d[k + 1] += n; d[k + 2] += n; }
    g.putImageData(ph2, px * RES, py * RES);
    g.strokeStyle = 'rgba(0,0,0,.3)'; g.strokeRect(px, py, pw, ph);
    g.fillStyle = INK; g.font = '13px Elite'; g.textAlign = 'center'; g.fillText(`N° ${String(i + 1).padStart(2, '0')}`, w / 2, h - 16);
  });
}
function makeSlip(w, h, seed, draw) { return cache(w, h, (g) => { g.fillStyle = '#ece7da'; g.fillRect(0, 0, w, h); paperTex(g, w, h, seed, 12); g.fillStyle = INK; draw(g, w, h); }); }

// stickers: icon + thick white outline + soft shadow (ref2 style)
function sticker(w, h, draw, pad = 10) {
  const W2 = w + pad * 2, H2 = h + pad * 2;
  const icon = cache(W2, H2, (g) => { g.translate(pad, pad); draw(g, w, h); });
  return cache(W2, H2, (g) => {
    const s = mk(icon.width, icon.height), sg = s.getContext('2d');
    for (let a = 0; a < 16; a++) sg.drawImage(icon, Math.cos(a / 16 * 6.283) * 5 * RES, Math.sin(a / 16 * 6.283) * 5 * RES);
    sg.globalCompositeOperation = 'source-in'; sg.fillStyle = '#f6f3ec'; sg.fillRect(0, 0, s.width, s.height);
    g.drawImage(s, 0, 0, W2, H2); g.drawImage(icon, 0, 0, W2, H2);
  });
}
const ST = {};
function buildStickers() {
  ST.env = sticker(190, 130, (g, w, h) => {
    const notes = ['#9aa58f', '#b2b59a', '#8e9c86'];
    notes.forEach((c, i) => { g.save(); g.translate(40 + i * 40, 30); g.rotate(-.25 + i * .22); g.fillStyle = c; g.fillRect(-30, -40, 70, 60); g.strokeStyle = 'rgba(40,50,35,.6)'; g.strokeRect(-26, -36, 62, 52); g.fillStyle = 'rgba(40,50,35,.75)'; g.font = '700 14px Osw'; g.fillText('1000', -14, -4); g.restore(); });
    g.fillStyle = '#d9c9a3'; g.fillRect(0, 34, w, h - 34);
    g.fillStyle = '#c9b78e'; g.beginPath(); g.moveTo(0, 34); g.lineTo(w / 2, 86); g.lineTo(w, 34); g.lineTo(w, 40); g.lineTo(w / 2, 92); g.lineTo(0, 40); g.fill();
    g.strokeStyle = 'rgba(80,60,30,.5)'; g.lineWidth = 2; g.beginPath(); g.moveTo(0, h); g.lineTo(w / 2, 86); g.lineTo(w, h); g.stroke();
  });
  ST.watch = sticker(110, 130, (g) => {
    g.fillStyle = '#b89a52'; g.beginPath(); g.arc(55, 12, 9, 0, 7); g.fill(); g.fillRect(49, 14, 12, 12);
    g.fillStyle = '#c9a85a'; g.beginPath(); g.arc(55, 75, 52, 0, 7); g.fill();
    g.fillStyle = '#f2ecd9'; g.beginPath(); g.arc(55, 75, 44, 0, 7); g.fill();
    g.fillStyle = INK; for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283; g.beginPath(); g.arc(55 + Math.cos(a) * 37, 75 + Math.sin(a) * 37, i % 3 ? 1.6 : 3, 0, 7); g.fill(); }
  });
  ST.hook = sticker(70, 150, (g) => {
    g.strokeStyle = 'rgba(220,220,220,.8)'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(40, 0); g.lineTo(40, 40); g.stroke();
    g.strokeStyle = '#8c969a'; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.moveTo(40, 40); g.lineTo(40, 110); g.arc(24, 110, 16, 0, Math.PI, false); g.lineTo(8, 96); g.stroke();
    g.fillStyle = '#8c969a'; g.beginPath(); g.moveTo(4, 98); g.lineTo(8, 80); g.lineTo(15, 98); g.fill();
    g.strokeStyle = '#d6dde0'; g.lineWidth = 2; g.beginPath(); g.moveTo(42, 46); g.lineTo(42, 104); g.stroke();
    g.beginPath(); g.arc(40, 40, 6, 0, 7); g.lineWidth = 3; g.strokeStyle = '#8c969a'; g.stroke();
  });
  ST.train = sticker(230, 110, (g) => {
    g.fillStyle = 'rgba(200,200,200,.9)'; [[40, 18, 14], [58, 10, 18], [80, 4, 14]].forEach(([x, y, r]) => { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); });
    g.fillStyle = '#1e2224';
    g.fillRect(30, 40, 120, 42); g.fillRect(140, 22, 60, 60); g.fillRect(40, 22, 18, 20); g.fillRect(196, 18, 10, 8);
    g.beginPath(); g.moveTo(30, 82); g.lineTo(10, 96); g.lineTo(30, 96); g.fill();
    g.fillStyle = RED; g.fillRect(140, 48, 60, 6); g.fillRect(30, 58, 110, 4);
    g.fillStyle = '#e8d9a6'; g.fillRect(152, 30, 16, 14); g.fillRect(176, 30, 16, 14);
    g.fillStyle = '#111'; [[52, 92, 14], [88, 92, 14], [124, 92, 14], [170, 92, 16]].forEach(([x, y, r]) => { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); });
  });
  ST.case = sticker(120, 100, (g) => {
    g.strokeStyle = '#4a2e1a'; g.lineWidth = 7; g.beginPath(); g.moveTo(42, 22); g.lineTo(42, 8); g.lineTo(78, 8); g.lineTo(78, 22); g.stroke();
    g.fillStyle = '#7b4a28'; g.fillRect(0, 20, 120, 78);
    g.fillStyle = '#5c361c'; g.fillRect(24, 20, 10, 78); g.fillRect(86, 20, 10, 78);
    g.fillStyle = '#c9a85a'; g.fillRect(25, 52, 8, 10); g.fillRect(87, 52, 8, 10);
    g.fillStyle = '#9aa58f'; g.save(); g.translate(112, 30); g.rotate(.4); g.fillRect(-6, -18, 26, 34); g.restore();
  });
  ST.ship = sticker(260, 120, (g) => {
    g.fillStyle = '#1e2224'; g.beginPath(); g.moveTo(0, 60); g.lineTo(260, 60); g.lineTo(236, 110); g.lineTo(18, 110); g.closePath(); g.fill();
    g.fillStyle = '#e9e4d6'; g.fillRect(40, 40, 180, 22); g.fillRect(70, 26, 120, 16);
    g.fillStyle = '#1e2224'; for (let i = 0; i < 12; i++) g.fillRect(48 + i * 14, 48, 6, 6);
    [[90, 0], [125, -4], [160, 0]].forEach(([x, dy]) => { g.fillStyle = '#e9e4d6'; g.fillRect(x, 4 + dy, 22, 24); g.fillStyle = RED; g.fillRect(x, 0 + dy, 22, 10); g.fillStyle = '#111'; g.fillRect(x, -2 + dy, 22, 4); });
    g.fillStyle = RED; g.fillRect(4, 64, 250, 4);
  });
  ST.wax = cache(90, 90, (g) => {
    const r = rng(5); g.fillStyle = '#9c1b20'; g.beginPath();
    for (let i = 0; i <= 28; i++) { const a = i / 28 * 6.283, rr = 38 + r() * 6; g.lineTo(45 + Math.cos(a) * rr, 45 + Math.sin(a) * rr); } g.fill();
    g.fillStyle = '#b52a2e'; g.beginPath(); g.arc(45, 45, 28, 0, 7); g.fill();
    g.strokeStyle = 'rgba(60,0,0,.6)'; g.lineWidth = 2; g.beginPath(); g.arc(45, 45, 24, 0, 7); g.stroke();
    g.fillStyle = 'rgba(70,5,8,.75)'; g.font = '600 30px Corm'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('RF', 45, 47);
    g.fillStyle = 'rgba(255,190,190,.35)'; g.beginPath(); g.ellipse(34, 30, 10, 5, -.6, 0, 7); g.fill();
  });
}

// ------------------------------------------------------------ map
const SEINE = [[4950, 2400], [4300, 2160], [3800, 1880], [3420, 1665], [2950, 1535], [2450, 1490], [2050, 1555], [1700, 1715], [1360, 1890], [1080, 2230], [820, 2580], [480, 2900], [200, 3150]];
function buildMap() {
  const c = mk(WW, WH), g = c.getContext('2d'), r = rng(7);
  g.fillStyle = '#0c1719'; g.fillRect(0, 0, WW, WH);
  for (let i = 0; i < 70; i++) { const x = r() * WW, y = r() * WH, rad = 200 + r() * 800; const gr = g.createRadialGradient(x, y, 0, x, y, rad); gr.addColorStop(0, `rgba(44,78,80,${.04 + r() * .07})`); gr.addColorStop(1, 'rgba(44,78,80,0)'); g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  // grid
  g.strokeStyle = 'rgba(120,170,170,.05)'; g.lineWidth = 1.5;
  for (let x = 0; x <= WW; x += 300) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, WH); g.stroke(); }
  for (let y = 0; y <= WH; y += 300) { g.beginPath(); g.moveTo(0, y); g.lineTo(WW, y); g.stroke(); }
  const city = blob(2620, 1450, 1980, 1300, .09, 11);
  g.fillStyle = 'rgba(32,62,64,.5)'; pathPoly(g, city); g.fill();
  const inCity = (x, y) => ((x - 2620) / 1900) ** 2 + ((y - 1450) / 1240) ** 2 < 1;
  // local street patches
  for (let i = 0; i < 1500; i++) {
    const x = 400 + r() * 4200, y = 150 + r() * 2700; if (!inCity(x, y)) continue;
    const ang = fbm(x / 1100, y / 1100, 2) * 6.283 + (r() - .5) * .3, sp = 34 + r() * 40, L = 120 + r() * 240;
    const ca = Math.cos(ang), sa = Math.sin(ang);
    g.strokeStyle = `rgba(70,115,118,${.18 + r() * .16})`; g.lineWidth = 1.3 + r() * 1.2;
    g.beginPath();
    for (let k = -2; k <= 2; k++) {
      if (r() < .2) continue;
      const ox = -sa * k * sp, oy = ca * k * sp;
      g.moveTo(x + ox - ca * L / 2, y + oy - sa * L / 2); g.lineTo(x + ox + ca * L / 2, y + oy + sa * L / 2);
      if (r() < .7) { const ox2 = ca * k * sp * 1.4, oy2 = sa * k * sp * 1.4; g.moveTo(x + ox2 + sa * L * .3, y + oy2 - ca * L * .3); g.lineTo(x + ox2 - sa * L * .3, y + oy2 + ca * L * .3); }
    }
    g.stroke();
  }
  // parks (hatched)
  const park = (pts) => { g.save(); pathPoly(g, pts); g.fillStyle = 'rgba(40,80,70,.45)'; g.fill(); g.clip(); g.strokeStyle = 'rgba(90,140,125,.18)'; g.lineWidth = 1.5; for (let k = -3000; k < 6000; k += 13) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k + 3000, 3000); g.stroke(); } g.restore(); pathPoly(g, pts); g.strokeStyle = 'rgba(90,140,125,.3)'; g.stroke(); };
  park(blob(640, 1480, 360, 520, .2, 3));
  const rect = (cx, cy, w, h, a) => { const p = [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2], [-w / 2, -h / 2]]; return p.map(([x, y]) => [cx + x * Math.cos(a) - y * Math.sin(a), cy + x * Math.sin(a) + y * Math.cos(a)]); };
  park(rect(1690, 2120, 150, 520, -.62)); park(rect(2430, 1420, 320, 90, -.08)); park(blob(3050, 2080, 150, 110, .2, 9)); park(blob(3950, 980, 140, 110, .3, 12)); park(blob(2700, 470, 160, 120, .3, 14));
  // ring boulevards + radial avenues
  g.strokeStyle = 'rgba(95,145,148,.33)'; g.lineWidth = 7;
  [[.42, 13], [.7, 17]].forEach(([s, sd]) => { pathPoly(g, blob(2700, 1420, 1900 * s, 1250 * s, .07, sd)); g.stroke(); });
  g.lineWidth = 5;
  for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283 + .2; g.beginPath(); g.moveTo(1560, 1150); g.lineTo(1560 + Math.cos(a) * 620, 1150 + Math.sin(a) * 620); g.stroke(); }
  for (let i = 0; i < 16; i++) { const a = i / 16 * 6.283 + .1; g.beginPath(); g.moveTo(2700 + Math.cos(a) * 300, 1420 + Math.sin(a) * 200); g.quadraticCurveTo(2700 + Math.cos(a + .1) * 1000, 1420 + Math.sin(a + .1) * 700, 2700 + Math.cos(a) * 1900, 1420 + Math.sin(a) * 1250); g.stroke(); }
  g.beginPath(); g.arc(1560, 1150, 34, 0, 7); g.lineWidth = 6; g.stroke();
  // rail lines
  const rail = (pts) => { const p = crSample(pts, 20); g.strokeStyle = 'rgba(140,180,180,.35)'; g.lineWidth = 3; pathPoly(g, p); g.stroke(); const L = polyLen(p); for (let d = 0; d < L[L.length - 1]; d += 22) { const q = polyAt(p, L, d / L[L.length - 1]); g.beginPath(); g.moveTo(q.x - Math.sin(q.a) * 9, q.y + Math.cos(q.a) * 9); g.lineTo(q.x + Math.sin(q.a) * 9, q.y - Math.cos(q.a) * 9); g.lineWidth = 1.5; g.stroke(); } };
  rail([[3300, 700], [3700, 520], [4300, 380], [4900, 300]]); rail([[2300, 930], [2150, 600], [1950, 200], [1850, 0]]);
  // fortifications
  g.setLineDash([10, 12]); g.strokeStyle = 'rgba(110,160,160,.32)'; g.lineWidth = 3; pathPoly(g, city); g.stroke();
  pathPoly(g, blob(2620, 1450, 2040, 1345, .09, 11)); g.stroke(); g.setLineDash([]);
  // the Seine
  const sp = crSample(SEINE, 10);
  g.lineCap = 'round'; g.lineJoin = 'round';
  g.strokeStyle = 'rgba(80,130,132,.55)'; g.lineWidth = 92; pathPoly(g, sp); g.stroke();
  g.strokeStyle = '#061011'; g.lineWidth = 80; pathPoly(g, sp); g.stroke();
  g.strokeStyle = 'rgba(80,130,132,.12)'; g.lineWidth = 2; for (const o of [-18, 14]) { pathPoly(g, sp.map(([x, y]) => [x, y + o])); g.stroke(); }
  const L = polyLen(sp);
  for (let d = 380; d < L[L.length - 1] - 200; d += 230 + (d % 7) * 20) { const q = polyAt(sp, L, d / L[L.length - 1]); g.strokeStyle = 'rgba(80,130,132,.6)'; g.lineWidth = 11; g.lineCap = 'butt'; g.beginPath(); g.moveTo(q.x - Math.sin(q.a) * 62, q.y + Math.cos(q.a) * 62); g.lineTo(q.x + Math.sin(q.a) * 62, q.y - Math.cos(q.a) * 62); g.stroke(); }
  g.fillStyle = 'rgba(32,62,64,1)'; g.strokeStyle = 'rgba(80,130,132,.6)'; g.lineWidth = 3;
  [[3290, 1625, 170, 34, .3], [3470, 1690, 80, 22, .45]].forEach(([x, y, rx, ry, a]) => { g.beginPath(); g.ellipse(x, y, rx, ry, a, 0, 7); g.fill(); g.stroke(); });
  // labels
  const lab = (t, x, y, s, a = .2, rot = 0, font = 'Osw', wt = 400, sp2 = .45) => { g.save(); g.translate(x, y); g.rotate(rot); g.fillStyle = `rgba(170,210,208,${a})`; g.font = `${wt} ${s}px ${font}`; g.textAlign = 'center'; spaced(g, t, 0, 0, s * sp2); g.restore(); };
  lab('PARIS', 3250, 1160, 150, .07, 0, 'Osw', 400, .6);
  lab('LA SEINE', 2700, 1595, 30, .3, .04); lab('LA SEINE', 1180, 2110, 26, .25, -1.0);
  lab('BOIS DE BOULOGNE', 640, 1480, 30, .25); lab('MONTMARTRE', 2700, 380, 30, .25); lab('CHAMP-DE-MARS', 1820, 2420, 22, .3, -.62);
  lab('RIVE DROITE', 3500, 1350, 30, .17); lab('RIVE GAUCHE', 2750, 2400, 30, .17); lab('ÉTOILE', 1560, 1100, 22, .28); lab('ÎLE DE LA CITÉ', 3290, 1580, 18, .32, .3);
  lab('VERS LE HAVRE', 260, 940, 26, .22); lab('VERS STRASBOURG', 4560, 230, 26, .22);
  g.font = '400 18px Osw'; g.fillStyle = 'rgba(170,210,208,.18)';
  for (let x = 300; x < WW; x += 600) g.fillText(`2°${String(14 + x / 300 | 0).padStart(2, '0')}′ E`, x + 6, 30);
  for (let y = 300; y < WH; y += 600) g.fillText(`48°${String(54 - y / 300 | 0).padStart(2, '0')}′ N`, 10, y - 6);
  // texture + edge falloff
  const lo = mk(320, 200), lg = lo.getContext('2d'), ld = lg.createImageData(320, 200);
  for (let i = 0; i < 320 * 200; i++) { const v = fbm((i % 320) / 22, (i / 320 | 0) / 22, 4) * 255; ld.data[i * 4] = ld.data[i * 4 + 1] = ld.data[i * 4 + 2] = v; ld.data[i * 4 + 3] = 255; }
  lg.putImageData(ld, 0, 0);
  g.globalCompositeOperation = 'soft-light'; g.globalAlpha = .55; g.drawImage(lo, 0, 0, WW, WH); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  const eg = g.createRadialGradient(2500, 1500, 900, 2500, 1500, 3000); eg.addColorStop(0, 'rgba(0,0,0,0)'); eg.addColorStop(1, 'rgba(0,0,0,.55)'); g.fillStyle = eg; g.fillRect(0, 0, WW, WH);
  for (let i = 0; i < 40000; i++) { g.fillStyle = `rgba(180,220,220,${r() * .06})`; g.fillRect(r() * WW, r() * WH, 1.5, 1.5); }
  return c;
}

// ------------------------------------------------------------ world objects
let MAP, P = {}, RUST, STAMP = {}, GRAIN = [], VIG;
let Z = 1; // current camera zoom (for shadow sizing)

const LABELS = []; // typed labels: register key events
function typedSpec(text, t0, cps = 17) { const s = { text, t0, cps }; LABELS.push(s); return s; }
function typedStr(s, t) { if (t < s.t0) return ''; return s.text.slice(0, Math.floor((t - s.t0) * s.cps) + 1); }

const SCRIB = [];
function circleSpec(t0, dur = .42) { const s = { t0, dur, seed: SCRIB.length * 7 + 3 }; SCRIB.push(s); return s; }
function drawCircle(g, s, x, y, rx, ry, t, lw = 3.2) {
  if (t < s.t0) return; const p = eoc(c01((t - s.t0) / s.dur)), r = rng(s.seed), ph = r() * 6, a0 = -2.2 + r() * .6;
  const n = Math.max(2, Math.floor(64 * p)); g.save(); g.strokeStyle = RED; g.lineWidth = lw; g.lineCap = 'round'; g.lineJoin = 'round';
  g.shadowColor = REDG; g.shadowBlur = 8 * Z; g.beginPath();
  for (let i = 0; i <= n; i++) { const a = a0 + (i / 64) * Math.PI * 2.12, k = 1 + .04 * Math.sin(a * 3 + ph) + .05 * (i / 64); g.lineTo(x + Math.cos(a) * rx * k, y + Math.sin(a) * ry * k); }
  g.stroke(); g.restore();
}
const STAMPS = [];
function stampSpec(key, t0, until) { const s = { key, t0, until }; STAMPS.push(s); SHAKES.push([t0 + .12, 5]); return s; }
function drawStamp(g, s, x, y, rot, t, scale = 1) {
  if (t < s.t0) return; let p = (t - s.t0) / .14, sc = p < 1 ? lerp(2.6, 1, eoq(c01(p))) : 1, a = c01(p * 1.6);
  if (s.until !== undefined && t > s.until) { const q = c01((t - s.until) / .22); sc *= 1 + q * 1.4; a *= 1 - q; if (q >= 1) return; }
  const st = STAMP[s.key]; g.save(); g.translate(x, y); g.rotate(rot); g.scale(sc * scale, sc * scale); g.globalAlpha *= a * .92;
  g.drawImage(st, -st.w / 2, -st.h / 2, st.w, st.h); g.restore();
}
const DROPS = [];

// generic physical paper object
function drawPaper(g, o, t) {
  const t0 = o.t0; if (t < t0) return;
  const dd = .78 - .3 * pace(t0), p = c01((t - t0) / dd), e = eoq(p), lift0 = 1 - e;
  const st = o.pose ? o.pose(t) : { x: o.x, y: o.y, rot: o.rot, s: 1, lift: 0 };
  const lift = Math.max(lift0, st.lift || 0);
  const s = (st.s || 1) * (1 + .2 * lift0) * (1 + .05 * (st.lift || 0));
  const w = o.cv.w, h = o.cv.h;
  g.save(); g.translate(st.x + lift0 * (o.dx || 30), st.y - lift0 * 70); g.rotate(st.rot + lift0 * (o.spin || .1)); g.scale(s, s);
  g.globalAlpha = c01(p * 3.5);
  g.shadowColor = 'rgba(0,0,0,.62)'; g.shadowBlur = (8 + 46 * lift) * Z * s; g.shadowOffsetX = (5 + 26 * lift) * Z * s; g.shadowOffsetY = (9 + 48 * lift) * Z * s;
  g.fillStyle = '#000'; g.fillRect(-w / 2 + 2, -h / 2 + 2, w - 4, h - 4);
  g.shadowColor = 'transparent';
  g.drawImage(o.cv, -w / 2, -h / 2, w, h);
  g.translate(-w / 2, -h / 2);
  if (o.after) o.after(g, t, w, h);
  const dim = Math.max(dimOf(o.id, t), o.extraDim ? o.extraDim(t) : 0);
  if (dim > .01) { g.fillStyle = `rgba(3,9,11,${dim})`; g.fillRect(0, 0, w, h); }
  if (o.clip) drawClipAt(g, o.clip[0], o.clip[1], o.clip[2]);
  g.restore();
}
function drawClipAt(g, x, y, rot) {
  g.save(); g.translate(x, y); g.rotate(rot); g.lineCap = 'round'; g.lineJoin = 'round';
  const path = () => { g.beginPath(); g.moveTo(6, 60); g.lineTo(6, 8); g.arc(14, 8, 8, Math.PI, 0); g.lineTo(22, 52); g.arc(14, 52, 8, 0, Math.PI); g.lineTo(6, 20); g.moveTo(22, 52); };
  g.shadowColor = 'rgba(0,0,0,.5)'; g.shadowBlur = 4 * Z; g.shadowOffsetY = 3 * Z;
  g.strokeStyle = '#7d878b'; g.lineWidth = 4; path(); g.stroke(); g.shadowColor = 'transparent';
  g.strokeStyle = '#dfe6e8'; g.lineWidth = 1.3; path(); g.stroke();
  g.restore();
}
function drawLabelOn(g, spec, x, y, t, size = 22, align = 'center', col = INK) {
  const s = typedStr(spec, t); if (!s) return; g.save(); g.fillStyle = col; g.font = `${size}px Elite`; g.textAlign = align; spaced(g, s, x, y, size * .12); g.restore();
}

// stickers in world
function drawSticker(g, cvs, x, y, rot, t0, t, id, scale = 1, extra) {
  if (t < t0) return; const p = c01((t - t0) / .32), s = scale * (p < 1 ? lerp(.2, 1, eoq(p)) * (1 + .18 * Math.sin(p * Math.PI)) : 1);
  g.save(); g.translate(x, y); g.rotate(rot + (1 - eoc(p)) * .5); g.scale(s, s); g.globalAlpha = c01(p * 3) * (1 - dimOf(id, t) * .9);
  g.shadowColor = 'rgba(0,0,0,.55)'; g.shadowBlur = 16 * Z * s; g.shadowOffsetY = 10 * Z * s; g.shadowOffsetX = 5 * Z * s;
  g.drawImage(cvs, -cvs.w / 2, -cvs.h / 2, cvs.w, cvs.h); g.shadowColor = 'transparent';
  if (extra) extra(g, cvs.w, cvs.h);
  g.restore();
}

// dotted red connector lines
const LINES = [];
function dotted(g, pts, t0, dur, t, id, a = 1) {
  if (t < t0) return; const p = eio(c01((t - t0) / dur)), L = polyLen(pts), tot = L[L.length - 1] * p;
  g.save(); g.globalAlpha = a * (1 - dimOf(id, t) * .85); g.strokeStyle = RED; g.lineWidth = 3.6 / Math.sqrt(Z); g.lineCap = 'round';
  g.setLineDash([.1, 13 / Math.sqrt(Z)]); g.shadowColor = REDG; g.shadowBlur = 6 * Z;
  g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) { if (L[i] <= tot) g.lineTo(pts[i][0], pts[i][1]); else { const f = (tot - L[i - 1]) / (L[i] - L[i - 1]); g.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)); break; } }
  g.stroke(); g.restore();
}
const PINS = [];
function pinSpec(id, x, y, t0, label, lx, ly, align = 'left', size = 24) { const s = { id, x, y, t0, label: label ? typedSpec(label, t0 + .25, label.length > 16 ? 30 : 20) : null, lx, ly, align, size }; PINS.push(s); return s; }
function drawPin(g, s, t) {
  if (t < s.t0) return; const p = c01((t - s.t0) / .35), sc = (p < 1 ? eoq(p) * (1 + .3 * Math.sin(p * Math.PI)) : 1) / Math.sqrt(Z);
  const a = 1 - dimOf(s.id, t) * .8;
  g.save(); g.globalAlpha = a; g.translate(s.x, s.y);
  const ph = ((t - s.t0) % 1.8) / 1.8; g.strokeStyle = `rgba(230,40,50,${.7 * (1 - ph)})`; g.lineWidth = 2.5 * sc; g.beginPath(); g.arc(0, 0, (12 + 36 * ph) * sc, 0, 7); g.stroke();
  g.shadowColor = REDG; g.shadowBlur = 18 * Z; g.fillStyle = RED; g.beginPath(); g.arc(0, 0, 11 * sc, 0, 7); g.fill();
  g.shadowBlur = 0; g.fillStyle = '#ffd9d9'; g.beginPath(); g.arc(0, 0, 4 * sc, 0, 7); g.fill();
  g.restore();
  if (s.label) { const str = typedStr(s.label, t); if (str) { g.save(); g.globalAlpha = a; g.fillStyle = '#ece6da'; g.font = `400 ${s.size}px Osw`; g.textAlign = s.align; g.shadowColor = 'rgba(0,0,0,.9)'; g.shadowBlur = 6 * Z; spaced(g, str, s.lx, s.ly, s.size * .22); g.restore(); } }
}

// ------------------------------------------------------------ scene definition
let OBJS = [], PINE, PINC, PING, PINP, PINH;
const lustigPose = (t) => {
  const p = eio(c01((t - 43.45) / 1.0));
  return { x: lerp(1900, 2250, p), y: lerp(830, 1600, p), rot: lerp(-.035, .03, p), s: lerp(1, .8, p), lift: Math.sin(Math.PI * p) };
};
const poissonPose = (t) => {
  const p = eio(c01((t - 36.0) / .6)), q = eio(c01((t - 66.1) / .9));
  return { x: 2660, y: lerp(1880, 1860, p), rot: lerp(.02, -.025, p), s: lerp(1, 1.6, p) * lerp(1, .9, q), lift: .35 * p * (1 - q) };
};
const ROUTE_E = crSample([[2150, 1330], [2600, 1190], [2980, 1110], [3300, 700], [4000, 520], [4950, 400]], 14);
const ROUTE_EL = polyLen(ROUTE_E);
const ROUTE_W = quad([2250, 1600], [1150, 1250], [-180, 1000], 60);
const ROUTE_WL = polyLen(ROUTE_W);
const DEALER_X = i => 2300 + i * 180;

function buildScene() {
  P.eiffel = makePrint(IMG.eiffel, 400, 602, { seed: 2, contrast: 1.2 });
  P.lustig = makePrint(IMG.lustig, 560, 315, { seed: 3, contrast: 1.12 });
  P.crillon = makePrint(IMG.crillon, 520, 366, { seed: 4, contrast: 1.25 });
  RUST = makeRust(P.eiffel);
  P.letter = makeLetter(false); P.copy = makeLetter(true); P.news = makeNews(); P.police = makePolice();
  P.mini = [0, 1, 2, 3, 4, 5].map(i => makeMiniNews(i, i === 5));
  P.dealers = [0, 1, 2, 3, 4, 5].map(i => makeDealer(i, 100 + i));
  P.dealers2 = [0, 1, 2, 3, 4, 5].map(i => makeDealer(i + 6, 200 + i));
  P.tag = makeSlip(150, 66, 11, () => { });
  P.permit = makeSlip(300, 150, 12, (g) => { g.font = '12px Elite'; g.fillText('CONCESSION — EXPOSITION 1889', 18, 30); g.font = '16px Elite'; g.fillText('Durée : 20 ans', 18, 66); g.font = '24px Elite'; g.fillText('Expire : 1909', 18, 112); });
  P.paint = makeSlip(280, 150, 13, (g) => { g.font = '12px Elite'; g.fillText('PEINTURE — TOUR EIFFEL', 18, 30); g.fillText('Campagne 1924', 18, 48); g.font = '12px Elite'; g.fillText('TONNES', 150, 112); });
  ['SOLD', 'FRAUD', 'ESCAPED', 'VERIFIED'].forEach((k, i) => STAMP[k] = makeStamp(k, k.length * 44 + 70, 96, 300 + i, 58));
  STAMP.CONF = makeStamp('CONFIDENTIEL', 250, 54, 310, 28);
  buildStickers();

  // measure circle anchors
  const mg = mk(10, 10).getContext('2d'); mg.font = '16px Elite';
  const L1 = mg.measureText('Lot : ').width, L1w = mg.measureText('7 000 tonnes').width, L2 = mg.measureText('Adjudication ').width, L2w = mg.measureText('au plus offrant').width;
  mg.font = '24px Elite'; const P1 = mg.measureText('Expire : ').width, P1w = mg.measureText('1909').width;

  // ---- Eiffel print
  const sold1 = stampSpec('SOLD', .44, 3.66), sold2 = stampSpec('SOLD', 2.95, 3.7), sold3 = stampSpec('SOLD', 53.3);
  const eLab = typedSpec('TOUR EIFFEL', 1.02, 15);
  OBJS.push({ id: 'eiffel', z: 1, cv: P.eiffel, x: 1250, y: 1650, rot: -.03, t0: -.3, clip: [300, -20, .12], after: (g, t, w, h) => {
    const rp = c01((t - 8.3) / 1.0) * RUST.length; if (rp > 0) { g.save(); g.globalAlpha = 1 - .4 * sstep(10.9, 12, t); const ga = g.globalAlpha; const k = Math.min(RUST.length - 1, Math.floor(rp)), f = rp - Math.floor(rp); const ph = P.eiffel.photo;
      if (k > 0) g.drawImage(RUST[k - 1], ph.x, ph.y, ph.w, ph.h); g.globalAlpha = ga * (k === RUST.length - 1 && rp >= RUST.length ? 1 : f); g.drawImage(RUST[k], ph.x, ph.y, ph.w, ph.h); g.restore(); }
    drawLabelOn(g, eLab, w / 2, h - 18, t, 22);
    drawStamp(g, sold1, w / 2, h * .45, -.18, t); drawStamp(g, sold2, w / 2 + 20, h * .62, .1, t); drawStamp(g, sold3, w / 2, h * .5, -.14, t);
  } });
  DROPS.push([-.3]);
  // ---- 1925 tag, permit, paint
  const tagS = typedSpec('1925', 4.6, 9);
  OBJS.push({ id: 'tag', z: 2, cv: P.tag, x: 1060, y: 1300, rot: -.09, t0: 4.35, after: (g, t, w, h) => drawLabelOn(g, tagS, w / 2, 48, t, 38) });
  const c1909 = circleSpec(7.32);
  OBJS.push({ id: 'permit', z: 2, cv: P.permit, x: 1640, y: 1320, rot: .05, t0: 6.0, clip: [26, -18, -.1], after: (g, t) => drawCircle(g, c1909, 26 + P1 + P1w / 2, 103, P1w / 2 + 12, 23, t) });
  const und = { t0: 10.75, dur: .3 };
  OBJS.push({ id: 'paint', z: 2, cv: P.paint, x: 1660, y: 1760, rot: -.04, t0: 9.55, after: (g, t) => {
    if (t < 9.8) return; const v = Math.round(60 * eoc(c01((t - 9.8) / 1.0))); g.fillStyle = INK; g.font = '56px Elite'; g.textAlign = 'right'; g.fillText(String(v), 138, 116);
    if (t > und.t0) { const p = c01((t - und.t0) / und.dur); g.strokeStyle = RED; g.lineWidth = 3.5; g.lineCap = 'round'; g.shadowColor = REDG; g.shadowBlur = 6 * Z; g.beginPath(); g.moveTo(26, 128); g.quadraticCurveTo(130, 122 + 6, 26 + 210 * p, 126); g.stroke(); g.shadowColor = 'transparent'; }
  } });
  ev(9.8, 'counter', { dur: 1.0 }); ev(und.t0, 'scribble', { dur: und.dur });
  // ---- newspaper
  const cNews = circleSpec(13.78, .45);
  OBJS.push({ id: 'news', z: 2, cv: P.news, x: 1950, y: 2350, rot: .025, t0: 11.7, dx: -40, after: (g, t) => drawCircle(g, cNews, DOC.news.x, DOC.news.y, DOC.news.rx, DOC.news.ry, t, 4) });
  // ---- Lustig
  const lLab = typedSpec('VICTOR LUSTIG', 15.94, 16), esc = stampSpec('ESCAPED', 80.25);
  OBJS.push({ id: 'lustig', z: 6, cv: P.lustig, t0: 15.0, pose: lustigPose, clip: [40, -22, -.15], after: (g, t, w, h) => { drawLabelOn(g, lLab, w / 2, h - 18, t, 24); drawStamp(g, esc, w / 2, h * .45, -.12, t, 1.25); } });
  // ---- letter + copy
  const cHead = circleSpec(17.72, .5), conf = stampSpec('CONF', 26.8), c7000 = circleSpec(29.3), cBid = circleSpec(30.72);
  const lt = [typedSpec(LETTER_LINES[0], 27.2, 24), typedSpec(LETTER_LINES[1], 28.25, 22), typedSpec(LETTER_LINES[2], 30.15, 26)];
  const sealT = 33.3;
  OBJS.push({ id: 'copy', z: 3, cv: P.copy, t0: 73.85, pose: (t) => { const p = eoc(c01((t - 73.85) / .6)); return { x: lerp(2560, 2640, p), y: lerp(800, 860, p), rot: lerp(.04, .12, p), s: 1 }; } });
  OBJS.push({ id: 'letter', z: 4, cv: P.letter, x: 2560, y: 800, rot: .04, t0: 16.85, dx: 40, clip: [360, -20, .08], after: (g, t, w, h) => {
    drawCircle(g, cHead, w / 2 + 20, 86, 160, 34, t, 3);
    g.save(); g.fillStyle = 'rgba(28,26,23,.92)'; g.font = '16px Elite'; g.textAlign = 'left';
    lt.forEach((s, i) => { const str = typedStr(s, t); if (str) g.fillText(str, 44, 244 + i * 36); }); g.restore();
    drawStamp(g, conf, 300, 404, -.09, t, 1.15);
    drawCircle(g, c7000, 52 + L1 + L1w / 2, 272, L1w / 2 + 10, 19, t);
    drawCircle(g, cBid, 52 + L2 + L2w / 2, 308, L2w / 2 + 10, 19, t);
    if (t > sealT) { const p = c01((t - sealT) / .16), s = lerp(2, 1, eoq(p)); g.save(); g.translate(372, 512); g.scale(s, s); g.globalAlpha = c01(p * 2); g.shadowColor = 'rgba(0,0,0,.5)'; g.shadowBlur = 10 * Z; g.shadowOffsetY = 5 * Z; g.drawImage(ST.wax, -45, -45, 90, 90); g.restore(); }
  } });
  SHAKES.push([sealT + .12, 4]); ev(sealT + .1, 'seal');
  // ---- Crillon
  const cLab = typedSpec('HÔTEL DE CRILLON', 21.2, 17);
  OBJS.push({ id: 'crillon', z: 3, cv: P.crillon, x: 2700, y: 1430, rot: .03, t0: 20.0, dx: -30, clip: [420, -22, .1], after: (g, t, w, h) => drawLabelOn(g, cLab, w / 2, h - 18, t, 22) });
  // ---- dealers row 1 (d2 = André Poisson)
  const pLab = typedSpec('ANDRÉ POISSON', 36.62, 16), qMark = { t0: 39.78, dur: .5 }, check = { t0: 48.66, dur: .32 };
  ev(qMark.t0, 'scribble', { dur: qMark.dur }); ev(check.t0, 'scribble', { dur: check.dur });
  for (let i = 0; i < 6; i++) {
    const o = { id: 'd' + i, z: i === 2 ? 7 : 5, cv: P.dealers[i], x: DEALER_X(i), y: 1880, rot: (i % 2 ? .04 : -.035) + i * .004, t0: 23.05 + i * .13, dx: 0 };
    if (i === 2) {
      o.pose = poissonPose; o.extraDim = t => .62 * sstep(66.1, 67.0, t) * (1 - sstep(67.6, 68.3, t) * .5);
      o.after = (g, t, w, h) => {
        if (t > 36.4) { g.save(); g.fillStyle = '#f3efe6'; g.shadowColor = 'rgba(0,0,0,.35)'; g.shadowBlur = 4 * Z; g.translate(w / 2, h + 4); g.rotate(-.03); g.fillRect(-72, -12, 144, 26); g.restore(); drawLabelOn(g, pLab, w / 2, h + 7, t, 13.5); }
        if (t > qMark.t0) { const p = c01((t - qMark.t0) / qMark.dur); const pts = []; for (let k = 0; k <= 30; k++) { const a = -2.6 + k / 30 * 3.9; pts.push([w - 22 + Math.cos(a) * 16, 34 + Math.sin(a) * 16]); } pts.push([w - 22, 64], [w - 22, 74]);
          g.save(); g.strokeStyle = RED; g.lineWidth = 4.5; g.lineCap = 'round'; g.shadowColor = REDG; g.shadowBlur = 8 * Z; const n = Math.floor(pts.length * p); g.beginPath(); pts.slice(0, Math.max(2, n)).forEach(([x, y]) => g.lineTo(x, y)); g.stroke(); if (p >= 1) { g.beginPath(); g.arc(w - 22, 90, 3.5, 0, 7); g.fillStyle = RED; g.fill(); } g.restore(); }
        if (t > check.t0) { const p = c01((t - check.t0) / check.dur); const pts = [[18, 120], [36, 140], [72, 92]]; const L = polyLen(pts); g.save(); g.strokeStyle = RED; g.lineWidth = 5; g.lineCap = 'round'; g.lineJoin = 'round'; g.shadowColor = REDG; g.shadowBlur = 8 * Z; g.beginPath(); g.moveTo(18, 120); const d = p * L[2]; if (d < L[1]) g.lineTo(lerp(18, 36, d / L[1]), lerp(120, 140, d / L[1])); else { g.lineTo(36, 140); g.lineTo(lerp(36, 72, (d - L[1]) / (L[2] - L[1])), lerp(140, 92, (d - L[1]) / (L[2] - L[1]))); } g.stroke(); g.restore(); }
      };
    }
    OBJS.push(o);
  }
  // ---- dealers row 2
  for (let i = 0; i < 6; i++) OBJS.push({ id: 'r' + i, z: 5, cv: P.dealers2[i], x: DEALER_X(i) + 60, y: 2215, rot: (i % 2 ? -.03 : .04), t0: 71.62 + i * .12,
    pose: i === 2 ? (t) => { const p = eio(c01((t - 76.5) / .5)); return { x: DEALER_X(2) + 60, y: 2215 - 20 * p, rot: .04, s: 1 + .15 * p, lift: .4 * p }; } : null });
  // ---- newspaper stack
  const stackT = [60.45, 60.78, 61.08, 61.3, 61.6, 61.9], cBlank = circleSpec(62.28, .5);
  stackT.forEach((t0, i) => OBJS.push({ id: 'stack', z: 8 + i * .01, cv: P.mini[i], x: 3800 + (i - 2.5) * 22, y: 1250 + (i % 2 ? 14 : -10), rot: (i % 2 ? .07 : -.06) + i * .01, t0, dx: 60, spin: .3,
    after: i === 5 ? (g, t) => drawCircle(g, cBlank, DOC.blank.x, DOC.blank.y, DOC.blank.rx, DOC.blank.ry, t, 4) : null }));
  // ---- police report
  const fraud = stampSpec('FRAUD', 77.32);
  OBJS.push({ id: 'police', z: 9, cv: P.police, x: 3900, y: 1985, rot: -.035, t0: 76.45, dx: 50, clip: [330, -18, .1], after: (g, t, w, h) => drawStamp(g, fraud, w / 2, h * .62, -.2, t, 1.05) });

  OBJS.sort((a, b) => a.z - b.z);
  OBJS.forEach(o => { ev(o.t0 + .5, 'drop', { size: o.cv.w * o.cv.h > 150000 ? 1 : .6 }); });

  // pins
  PINE = pinSpec('pinE', 1580, 1965, 4.45, 'CHAMP-DE-MARS', 1612, 1974);
  PINC = pinSpec('pinC', 2150, 1330, 19.9, 'PLACE DE LA CONCORDE', 2118, 1378, 'right');
  PING = pinSpec('pinG', 3300, 700, 56.3, "GARE DE L'EST", 3268, 762, 'right');
  PINP = pinSpec('pinP', 3330, 1600, 75.85, 'PRÉFECTURE DE POLICE', 3365, 1585);
  PINH = pinSpec('pinH', 60, 1050, 79.55, 'LE HAVRE  →  NEW YORK', 110, 1195, 'left', 70);
  PINS.forEach(p => ev(p.t0, 'pin'));
  LINES.push(
    { id: 'lLC', t0: 19.95, dur: .8, pts: t => { const s = lustigPose(t); return [[s.x + 220 * s.s, s.y + 150 * s.s], [2150, 1330]]; } },
    ...[0, 1, 2, 3, 4, 5].map(i => ({ id: 'lD', t0: 24.75 + i * .06, dur: .55, pts: t => { const pp = i === 2 ? poissonPose(t) : { x: DEALER_X(i), y: 1880, s: 1 }; return [[pp.x, pp.y - 95 * pp.s], [2150, 1330]]; } })),
    { id: 'lLP', t0: 44.3, dur: .6, pts: t => { const a = lustigPose(t), b = poissonPose(t); return [[a.x + 120, a.y + 60], [b.x - 60, b.y - 40]]; } },
    { id: 'lPE', t0: 68.25, dur: .7, pts: t => { const b = poissonPose(t); return quad([b.x - 100, b.y], [1900, 2100], [1420, 1850], 30); } },
    { id: 'lRP', t0: 76.7, dur: .7, pts: () => quad([DEALER_X(2) + 60, 2110], [3050, 1800], [3330, 1600], 30) },
  );
  LINES.forEach(l => ev(l.t0, 'line', { dur: l.dur }));
  ev(56.3, 'line', { dur: 1.4 }); ev(79.0, 'line', { dur: 1.4 });

  // stickers
  ev(38.42, 'hook'); ev(41.9, 'watch', { dur: 1.3 }); ev(45.28, 'envelope');
  SHAKES.push([45.4, 3]); ev(51.55, 'stamp');
  ev(56.45, 'train', { dur: 3.8 }); ev(58.05, 'case'); ev(69.8, 'train', { dur: 1.4, back: 1 }); ev(79.2, 'ship', { dur: 2 });
  ev(3.62, 'rewind'); ev(8.3, 'rust', { dur: 1.0 }); ev(33.5, 'riser', { dur: 1.3 }); ev(34.8, 'impact'); ev(34.8, 'crowd', { dur: 1.2 });
  ev(45.95, 'freeze'); ev(62.3, 'nothing'); ev(66.1, 'sink', { dur: 2.0 }); ev(80.25, 'final');
  SHAKES.push([34.8, 10], [45.98, 6], [62.3, 3]);
  STAMPS.forEach(s => ev(s.t0 + .12, 'stamp'));
  SCRIB.forEach(s => ev(s.t0, 'scribble', { dur: s.dur }));
  LABELS.forEach(s => { for (let i = 0; i < s.text.length; i++) if (s.text[i] !== ' ') ev(s.t0 + i / s.cps, 'key'); });
  { let run = null; const sp = t => { const p = camBase(t), q = camBase(t + 1 / 24); return Math.hypot(q.x - p.x, q.y - p.y) * p.z * 24; };
    for (let t = 0; t < DUR; t += 1 / 12) { const v = sp(t);
      if (v > 330) { if (!run) run = { t0: t, pk: 0 }; run.pk = Math.max(run.pk, v); }
      else if (run) { if (t - run.t0 > .6 && run.pk > 520) ev(run.t0, 'whoosh', { dur: t - run.t0, amt: Math.min(1, run.pk / 1400) }); run = null; } } }
  PUNCH.forEach(([t, a]) => ev(t, 'punch', { amt: a }));
  EV.sort((a, b) => a.t - b.t);
  window.EVENTS = EV;
}

function drawWorldStickers(g, t) {
  const v = verifiedSpec;
  drawSticker(g, ST.hook, 2830, 1690, .15, 38.3, t, 'hook', 1);
  drawSticker(g, ST.watch, 2850, 2030, -.12, 41.8, t, 'watch', 1, (gg, w, h) => {
    const a = (t - 41.8) * 9, b = (t - 41.8) * .75; gg.strokeStyle = INK; gg.lineCap = 'round';
    gg.lineWidth = 3; gg.beginPath(); gg.moveTo(0, 10); gg.lineTo(Math.cos(b - 1.57) * 22, 10 + Math.sin(b - 1.57) * 22); gg.stroke();
    gg.strokeStyle = RED; gg.lineWidth = 2; gg.beginPath(); gg.moveTo(0, 10); gg.lineTo(Math.cos(a - 1.57) * 34, 10 + Math.sin(a - 1.57) * 34); gg.stroke();
  });
  drawSticker(g, ST.env, 2470, 1800, -.08, 45.2, t, 'env', 1, (gg, w, h) => drawStamp(gg, v, 0, 18, -.22, t, .55));
  // train along the east route
  if (t > 56.5) {
    let f = t < 69.6 ? eio(c01((t - 56.5) / 3.8)) : 1 - eio(c01((t - 69.75) / 1.3));
    const q = polyAt(ROUTE_E, ROUTE_EL, .03 + f * .97), flip = t >= 69.6;
    drawSticker(g, ST.train, q.x, q.y - 40, 0, 56.5, t, 'train', .9, null);
    if (t > 58.0 && t < 69.6) drawSticker(g, ST.case, q.x - 10, q.y - 115, -.1, 58.0, t, 'case', .8);
    void flip;
  }
  if (t > 79.2) { const q = polyAt(ROUTE_W, ROUTE_WL, eio(c01((t - 79.2) / 2.2)) * .92 + .05); drawSticker(g, ST.ship, q.x, q.y - 50, 0, 79.2, t, 'ship', 1.2); }
}
const verifiedSpec = { key: 'VERIFIED', t0: 51.42 };

// ------------------------------------------------------------ frame
let SCN, SG, ACC, AG, BLR, BG, MSK, MG;
function renderScene(g, t) {
  const c = camera(t); Z = c.z;
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#071012'; g.fillRect(0, 0, W, H);
  g.translate(W / 2 + c.hx, H / 2 + c.hy); g.rotate(c.r); g.scale(c.z, c.z); g.translate(-c.x, -c.y);
  g.drawImage(MAP, 0, 0);
  // route lines (under papers)
  if (t > 56.3) { const f = t < 69.0 ? 1 : 1; void f; dotted(g, ROUTE_E, 56.3, 1.4, t, 'route'); }
  if (t > 79.0) dotted(g, ROUTE_W, 79.0, 1.4, t, 'shipR');
  for (const l of LINES) dotted(g, l.pts(t), l.t0, l.dur, t, l.id);
  for (const p of PINS) drawPin(g, p, t);
  for (const o of OBJS) drawPaper(g, o, t);
  drawWorldStickers(g, t);
  g.setTransform(1, 0, 0, 1, 0, 0);
}

function crowd(g, t) { // riot silhouettes (screen space)
  const a = sstep(34.72, 34.95, t) * (1 - sstep(35.4, 35.95, t)); if (a <= 0) return;
  const r = rng(77), rise = (1 - eoq(c01((t - 34.72) / .35))) * 220;
  g.save();
  const person = (x, y, s, i, col) => {
    g.fillStyle = col; g.strokeStyle = col; g.lineCap = 'round'; g.lineJoin = 'round';
    g.beginPath(); g.ellipse(x, y - 150 * s, 19 * s, 23 * s, 0, 0, 7); g.fill();               // head
    g.fillRect(x - 8 * s, y - 132 * s, 16 * s, 16 * s);                                      // neck
    g.beginPath(); g.moveTo(x - 58 * s, y + 60); g.bezierCurveTo(x - 56 * s, y - 90 * s, x - 40 * s, y - 118 * s, x, y - 120 * s);
    g.bezierCurveTo(x + 40 * s, y - 118 * s, x + 56 * s, y - 90 * s, x + 58 * s, y + 60); g.fill();  // shoulders
    if (r() < .6) {                                                                            // raised arm + fist
      const side = r() < .5 ? -1 : 1, sx = x + side * 40 * s, sy = y - 100 * s, wob = Math.sin(t * 19 + i * 2) * 6 * s;
      const ex = sx + side * 22 * s, ey = sy - 70 * s, hx = sx + side * 10 * s + wob, hy = sy - 150 * s;
      g.lineWidth = 24 * s; g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
      g.lineWidth = 19 * s; g.beginPath(); g.moveTo(ex, ey); g.lineTo(hx, hy); g.stroke();
      g.beginPath(); g.ellipse(hx, hy - 6 * s, 13 * s, 15 * s, 0, 0, 7); g.fill();
    }
  };
  for (let i = 0; i < 30; i++) person(i * 46 - 10 + r() * 20, H + 10 + rise * .8 - r() * 40, .55 + r() * .2, i, `rgba(40,4,6,${a * .9})`);
  for (let i = 0; i < 18; i++) person(i * 78 - 20 + r() * 30, H + 70 + rise - r() * 50, .85 + r() * .35, i + 40, `rgba(6,1,2,${a})`);
  g.restore();
}

function post(t, frameNo) {
  const g = out;
  // red grade (ref2 look)
  const ra = redAmt(t);
  if (ra > 0) {
    g.globalCompositeOperation = 'color'; g.fillStyle = `rgba(190,18,28,${ra * .9})`; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(255,${255 - 150 * ra | 0},${255 - 150 * ra | 0},1)`; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'source-over';
  }
  crowd(g, t);
  const flash = Math.max(0, 1 - Math.abs(t - 34.83) / .2) * .28 + Math.max(0, 1 - Math.abs(t - 46.0) / .18) * .2;
  if (flash > 0) { g.fillStyle = `rgba(255,70,60,${flash})`; g.globalCompositeOperation = 'screen'; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; }
  const rw = Math.max(0, 1 - Math.abs(t - 3.9) / .6);
  if (rw > 0) { g.globalCompositeOperation = 'saturation'; g.fillStyle = `rgba(128,128,128,${eio(rw) * .8})`; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; }
  // depth of field: soft edges, stronger in slow passages
  const dof = .55 + .45 * (1 - pace(t));
  BG.filter = 'blur(5px)'; BG.drawImage(cv, 0, 0, W / 2, H / 2); BG.filter = 'none';
  MG.globalCompositeOperation = 'copy'; MG.drawImage(BLR, 0, 0, W, H); MG.globalCompositeOperation = 'destination-in';
  const dm = MG.createRadialGradient(W / 2, H / 2, H * .28, W / 2, H / 2, W * .62); dm.addColorStop(0, 'rgba(0,0,0,0)'); dm.addColorStop(1, `rgba(0,0,0,${dof})`);
  MG.fillStyle = dm; MG.fillRect(0, 0, W, H); MG.globalCompositeOperation = 'source-over'; g.drawImage(MSK, 0, 0);
  // dust motes drifting with parallax
  { const cm = camBase(t); const dr = rng(4242);
    for (let i = 0; i < 34; i++) { const depth = .3 + dr() * .9, sz = 1 + dr() * 3.5 * depth;
      let x = (dr() * W * 1.4 - cm.x * cm.z * .06 * depth + t * (6 + dr() * 10)) % (W * 1.4); if (x < 0) x += W * 1.4; x -= W * .2;
      let y = (dr() * H * 1.4 - cm.y * cm.z * .06 * depth - t * (3 + dr() * 6)) % (H * 1.4); if (y < 0) y += H * 1.4; y -= H * .2;
      const a = (.05 + .1 * dr()) * (.6 + .4 * Math.sin(t * (1 + dr()) + i));
      const gg = g.createRadialGradient(x, y, 0, x, y, sz * 3); gg.addColorStop(0, `rgba(235,230,215,${a})`); gg.addColorStop(1, 'rgba(235,230,215,0)'); g.fillStyle = gg; g.fillRect(x - sz * 3, y - sz * 3, sz * 6, sz * 6); } }
  // vignette, grain, flicker, dust
  g.drawImage(VIG, 0, 0);
  const r = rng(frameNo * 7 + 3);
  const gr = GRAIN[frameNo % GRAIN.length];
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = .16;
  const ox = -(r() * 256 | 0), oy = -(r() * 256 | 0);
  for (let y = oy; y < H; y += 256) for (let x = ox; x < W; x += 256) g.drawImage(gr, x, y);
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  g.fillStyle = `rgba(0,0,0,${.025 + .025 * r()})`; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 3; i++) if (r() < .35) { g.fillStyle = r() < .5 ? 'rgba(240,235,220,.35)' : 'rgba(0,0,0,.45)'; g.beginPath(); g.arc(r() * W, r() * H, .6 + r() * 1.4, 0, 7); g.fill(); }
  if (r() < .04) { g.fillStyle = 'rgba(240,235,220,.12)'; g.fillRect(r() * W, 0, 1, H); }
  // HUD: corner brackets + small readouts
  const ha = .3 * (1 - redAmt(t) * .6);
  g.strokeStyle = `rgba(230,225,215,${ha})`; g.lineWidth = 1.2; const m = 26, l = 22;
  [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]].forEach(([x, y, sx, sy]) => { g.beginPath(); g.moveTo(x, y + sy * l); g.lineTo(x, y); g.lineTo(x + sx * l, y); g.stroke(); });
  const c = camBase(t);
  g.font = '400 12px Osw'; g.fillStyle = `rgba(230,225,215,${ha + .1})`; g.textAlign = 'left'; spaced(g, t > 4.6 ? 'PARIS  ·  1925' : 'PARIS', m + 10, H - m - 8, 3);
  g.textAlign = 'right'; g.font = '400 11px "JetBrains Mono", monospace';
  g.fillText(`${(48.902 - c.y / WH * .1).toFixed(4)}° N  ${(2.252 + c.x / WW * .17).toFixed(4)}° E`, W - m - 10, H - m - 8);
  g.fillStyle = `rgba(220,40,50,${.5 + .4 * (Math.floor(t * 1.2) % 2)})`; g.beginPath(); g.arc(W - m - 14, m + 14, 4, 0, 7); g.fill();
  // fades
  const fade = Math.max(1 - c01(t / .45), c01((t - (DUR - .45)) / .45));
  if (fade > 0) { g.fillStyle = `rgba(0,0,0,${fade})`; g.fillRect(0, 0, W, H); }
}

function renderFrame(t) {
  const frameNo = Math.round(t * FPS);
  // motion blur: average sub-frames when the camera moves fast
  const a = camBase(t), b = camBase(t - 1 / 48);
  const disp = Math.hypot(a.x - b.x, a.y - b.y) * a.z + Math.abs(a.z - b.z) / a.z * 700;
  const N = disp > 4 ? Math.min(4, Math.ceil(disp / 7)) : 1;
  if (N === 1) { renderScene(out, t); }
  else {
    for (let i = 0; i < N; i++) {
      renderScene(SG, t - (i / (N - 1)) * (1 / 48));
      AG.globalAlpha = i === 0 ? 1 : 1 / (i + 1); AG.drawImage(SCN, 0, 0);
    }
    AG.globalAlpha = 1; out.drawImage(ACC, 0, 0);
  }
  post(t, frameNo);
  return N;
}

async function init() {
  await Promise.all([loadImg('lustig', 'assets/lustig.jpg'), loadImg('crillon', 'assets/crillon.jpg'), loadImg('eiffel', 'assets/eiffel.jpg')]);
  await Promise.all(['16px Elite', '700 20px Play', '400 20px Play', '700 20px Osw', '400 20px Osw', '600 20px Corm'].map(f => document.fonts.load(f, 'AÉÎé→')));
  MAP = buildMap();
  buildScene();
  BLR = mk(W / 2, H / 2); BG = BLR.getContext('2d'); MSK = mk(W, H); MG = MSK.getContext('2d');
  SCN = mk(W, H); SG = SCN.getContext('2d'); ACC = mk(W, H); AG = ACC.getContext('2d');
  for (let k = 0; k < 6; k++) { const c = mk(256, 256), g = c.getContext('2d'), d = g.createImageData(256, 256), r = rng(900 + k); for (let i = 0; i < 65536; i++) { const v = 128 + (r() + r() + r() - 1.5) * 120; d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = v; d.data[i * 4 + 3] = 255; } g.putImageData(d, 0, 0); GRAIN.push(c); }
  VIG = mk(W, H); const vg = VIG.getContext('2d'), gr = vg.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, W * .72);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(.7, 'rgba(0,0,0,.35)'); gr.addColorStop(1, 'rgba(0,0,0,.8)'); vg.fillStyle = gr; vg.fillRect(0, 0, W, H);
  window.DURATION = DUR; window.FPS = FPS;
  window.renderFrame = renderFrame;
  window.READY = true;
}
init().catch(e => { window.INIT_ERROR = String(e && e.stack || e); });
