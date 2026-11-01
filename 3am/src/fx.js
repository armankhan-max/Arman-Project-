// The film, scene by scene. Every time comes from tl.js so picture and sound stay locked.
const L = require('./lib');
const { W, H, BAR, E, tw, inv, clamp, lerp, rng, hash, circle, ell, rr, text, rgrad, vgrad } = L;
const G = require('./guy');
const S = require('./sets');
const SC = require('./screens');
const T = require('./tl');

const RIM = 'rgba(110,150,255,.85)', RIM_W = 'rgba(255,170,90,.85)';

// ---------- text helpers ----------
function wrap(ctx, s, maxW, size, weight = 700, style = '') { ctx.font = `${style} ${weight} ${size}px Inter`; const out = []; for (const para of s.split('\n')) { let cur = ''; for (const w of para.split(' ')) { const tt = cur ? cur + ' ' + w : w; if (ctx.measureText(tt).width > maxW && cur) { out.push(cur); cur = w; } else cur = tt; } out.push(cur); } return out; }
// inner-voice line: typewriter in, soft fade out
function thought(ctx, t, t0, t1, s, x, y, o = {}) {
  if (t < t0 || t > t1 + .5) return;
  const size = o.size || 62, cps = o.cps || 26; const n = Math.floor((t - t0) * cps); const shown = o.instant ? s : s.slice(0, n);
  const a = clamp((t - t0) / .2) * (1 - clamp((t - t1) / .5));
  const lines = wrap(ctx, shown, o.maxW || 900, size, o.weight || 700, 'italic');
  ctx.save(); ctx.globalAlpha *= a;
  lines.forEach((l, i) => { const yy = y + (i - (lines.length - 1) / 2) * size * 1.22;
    ctx.save(); ctx.font = `italic ${o.weight || 700} ${size}px Inter`; ctx.textAlign = o.align || 'center'; ctx.textBaseline = 'middle'; ctx.shadowColor = o.glow || 'rgba(120,150,255,.55)'; ctx.shadowBlur = 30;
    ctx.fillStyle = o.color || '#f4f1ea'; ctx.fillText(l, x, yy); ctx.restore(); });
  ctx.restore();
}
function pop(ctx, t, t0, t1, s, x, y, o = {}) { L.popText(ctx, t, t0, s, x, y, { size: 70, weight: 900, color: '#fff', shadow: 'rgba(0,0,0,.6)', until: t1, ...o }); }
function factCard(ctx, t, t0, t1, label, body, o = {}) {
  if (t < t0 || t > t1 + .5) return;
  const k = E.out(clamp((t - t0) / .5)), out = 1 - clamp((t - t1) / .5); const x = 70 - (1 - k) * 80, y = o.y || 720, w = o.w || 820;
  const lines = wrap(ctx, body, w - 70, 32, 600); const h = 96 + lines.length * 42;
  ctx.save(); ctx.globalAlpha *= k * out;
  ctx.fillStyle = 'rgba(8,10,18,.82)'; rr(ctx, x, y - h, w, h, 22); ctx.fill(); ctx.strokeStyle = 'rgba(233,185,73,.55)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = '#e9b949'; ctx.fillRect(x, y - h + 22, 6, 40);
  text(ctx, label, x + 34, y - h + 44, { size: 26, weight: 900, color: '#e9b949', align: 'left', track: 3 });
  lines.forEach((l, i) => text(ctx, l, x + 34, y - h + 96 + i * 42, { size: 32, weight: 600, color: '#f1eee6', align: 'left' }));
  ctx.restore();
}
function bubbleDark(ctx, t, t0, s, x, y, o = {}) {
  if (t < t0) return; const k = E.back(clamp((t - t0) / .28)); const out = o.until ? 1 - clamp((t - o.until) / .3) : 1; if (out <= 0) return;
  const size = o.size || 36; const lines = wrap(ctx, s, o.maxW || 460, size, 800); ctx.font = L.font(size, 800);
  const bw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 60, bh = lines.length * size * 1.25 + 40;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(k, k); ctx.globalAlpha *= clamp(k) * out;
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 24; ctx.fillStyle = o.bg || 'rgba(22,24,34,.94)'; rr(ctx, -bw / 2, -bh / 2, bw, bh, 26); ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.strokeStyle = o.edge || 'rgba(255,90,90,.6)'; ctx.lineWidth = 3; ctx.stroke();
  for (let i = 0; i < 2; i++) { ctx.fillStyle = o.bg || 'rgba(22,24,34,.94)'; circle(ctx, -bw * .3 - i * 22, bh / 2 + 14 + i * 18, 12 - i * 4); ctx.fill(); }
  lines.forEach((l, i) => text(ctx, l, 0, (i - (lines.length - 1) / 2) * size * 1.25 + 2, { size, weight: 800, color: o.color || '#fff' }));
  ctx.restore();
}
function speech(ctx, t, t0, t1, s, x, y, tx, ty, o = {}) { L.bubble(ctx, t, t0, s, x, y, tx, ty, { size: 46, until: t1, ...o }); }

// ---------- reusable bedroom shot ----------
const CLOCKS = [[0, '3:07'], [T.night, '3:07'], [T.jump319, '3:19'], [T.song, '3:22'], [T.drift, '3:26'], [T.storm, '3:33'], [T.fridge, '3:47'], [T.shrink, '3:58'], [T.callback, '3:59'], [T.next, '3:07']];
const clockAt = t => { let c = CLOCKS[0][1]; for (const [a, v] of CLOCKS) if (t >= a) c = v; return c; };
function heldPhone(ctx, t, a = 1, col) {
  ctx.save(); ctx.translate(588, 548); ctx.rotate(-.12); ctx.fillStyle = '#0b0b0e'; rr(ctx, -62, -10, 124, 20, 6); ctx.fill(); ctx.fillStyle = col ? `rgba(${col},.9)` : 'rgba(140,180,255,.9)'; ctx.globalAlpha = a; ctx.fillRect(-56, 8, 112, 3); ctx.restore();
  S.phoneGlow(ctx, 560, 600, a, col);
}
function bed(ctx, t, o = {}) {
  S.bedroomBase(ctx, o.day); if (!o.day) S.moonBars(ctx, t, o.moon ?? 1);
  S.wallShadow(ctx, t, o.shadow || 0);
  S.fan(ctx, t, o.fan ?? 1.3); S.clockDigits(ctx, o.clock || clockAt(t), o.clockGlow ?? 1);
  // earbuds case on the pillow corner
  if (o.case !== false) { ctx.fillStyle = '#e9e9ee'; rr(ctx, 384, 656, 36, 24, 10); ctx.fill(); ctx.fillStyle = `rgba(90,255,140,${.5 + .5 * Math.sin(t * 2)})`; circle(ctx, 402, 661, 2.5); ctx.fill(); }
  if (o.pre) o.pre(ctx, t);
  const phone = o.phone ?? true;
  if (o.noGuy) S.blanket(ctx, t); else S.lyingGuy(ctx, t, { rim: o.day ? null : phone ? RIM : 'rgba(110,150,255,.4)', hands: phone ? [[548, 556, 1], [626, 548, 0]] : o.hands, ...o.guy });
  if (o.buds) { for (const [dx, dy] of [[-58, -16]]) { ctx.fillStyle = '#fff'; circle(ctx, S.BED.headX + dx, S.BED.headY + dy, 8); ctx.fill(); } }
  if (phone) heldPhone(ctx, t, o.glow ?? 1, o.glowCol);
  if (o.post) o.post(ctx, t);
  if (o.red) { ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = `rgba(255,30,40,${.55 * o.red})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  if (o.dark) { ctx.fillStyle = `rgba(0,0,0,${o.dark})`; ctx.fillRect(0, 0, W, H); }
}
// big close-up hand with n fingers raised (counting)
function countingHand(ctx, t, n, x = 960, y = 760) {
  const fingers = [[-105, 0], [-36, -14], [34, -10], [102, 8]];
  ctx.save(); ctx.translate(x, y);
  const up = i => clamp(n - i);
  fingers.forEach(([fx, fy], i) => { const len = lerp(70, 230, E.back(up(i))); G.finger(ctx, [fx, -60 + fy], [fx, -60 + fy - len], 62); });
  ctx.fillStyle = G.INK; rr(ctx, -150 - 6, -90 - 6, 300 + 12, 330 + 12, 90); ctx.fill(); ctx.fillStyle = G.SKIN; rr(ctx, -150, -90, 300, 330, 84); ctx.fill();
  const th = clamp(n - 4); G.finger(ctx, [-130, 40], [lerp(-60, -250, E.back(th)), lerp(-10, -80, th)], 62);
  for (let i = 0; i < 3; i++) { ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-70 + i * 70, -80); ctx.lineTo(-70 + i * 70, -40); ctx.stroke(); }
  ctx.restore();
}
function digitalText(ctx, s, x, y, size, a = 1) { ctx.save(); ctx.globalAlpha *= a; ctx.shadowColor = 'rgba(255,60,50,.95)'; ctx.shadowBlur = size * .35; text(ctx, s, x, y, { size, weight: 800, color: '#ff4a3d', track: 4 }); ctx.restore(); }

// Storm thought bubbles: spawn faster and faster
const STORM = ['You too!?', 'Late again tomorrow?', 'What are you doing with your life?', 'The whole class laughed.', 'You declined Mom.', 'She waved at HIM.', 'Not even in the photo.', 'Missed the bus. Again?', 'Coffee. On a WHITE shirt.', 'Say something. Anything.', "Everyone's ahead of you.", 'Did you lock the door?', 'Everyone noticed.', 'You wasted today.', 'Again.'];
function stormBubbles(ctx, t, t0, t1, density = 1) {
  const r = rng(91); let tt = t0 + 1; let i = 0;
  while (tt < t1 && i < 140) {
    const x = 300 + r() * 1320, y = 170 + r() * 560, rot = (r() - .5) * .25;
    if (t > tt) bubbleDark(ctx, t, tt, STORM[i % STORM.length], x, y, { rot, size: 30 + r() * 10, until: tt + 2.4 + r() * 2 });
    const gap = Math.max(.12, 1.9 * Math.pow(.86, i)) / density; tt += gap; i++;
  }
}
// blur toward the frame edges (dreamy/feverish)
const { createCanvas } = require('@napi-rs/canvas');
let _eb = null, _ebx = null;
function edgeBlur(ctx, cv, k) {
  if (!_eb) { _eb = createCanvas(W / 2, H / 2); _ebx = _eb.getContext('2d'); }
  _ebx.globalCompositeOperation = 'source-over'; _ebx.filter = `blur(${(8 * k).toFixed(1)}px)`; _ebx.clearRect(0, 0, W / 2, H / 2); _ebx.drawImage(cv, 0, 0, W / 2, H / 2); _ebx.filter = 'none';
  _ebx.globalCompositeOperation = 'destination-in'; _ebx.fillStyle = rgrad(_ebx, W / 4, H / 4, H * .12, H * .5, [[0, 'rgba(0,0,0,0)'], [1, `rgba(0,0,0,${clamp(k)})`]]); _ebx.fillRect(0, 0, W / 2, H / 2);
  ctx.drawImage(_eb, 0, 0, W, H);
}

module.exports = { RIM, RIM_W, wrap, thought, pop, factCard, bubbleDark, speech, clockAt, heldPhone, bed, countingHand, digitalText, stormBubbles, edgeBlur };
