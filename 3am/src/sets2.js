// Day-time sets: bathroom, kitchen, street (morning / rain / night), bus, classroom, cafeteria, cafe.
const L = require('./lib');
const { W, H, clamp, lerp, E, rng, hash, circle, ell, rr, vgrad, rgrad, text, line } = L;
const { cached, palm } = require('./sets');
const G = require('./guy');

function bathroom(ctx) {
  ctx.drawImage(cached('bath', x => {
    x.fillStyle = '#cfe6e6'; x.fillRect(0, 0, W, H);
    for (let i = 0; i < 26; i++) for (let j = 0; j < 9; j++) { x.strokeStyle = 'rgba(80,120,120,.18)'; x.lineWidth = 2; x.strokeRect(i * 80, 380 + j * 60, 80, 60); }
    x.fillStyle = '#e8f3f3'; x.fillRect(0, 86, W, 300);
    x.fillStyle = '#b6d3d6'; rr(x, 1180, 160, 420, 330, 20); x.fill(); x.fillStyle = 'rgba(255,255,255,.55)'; x.beginPath(); x.moveTo(1220, 460); x.lineTo(1400, 180); x.lineTo(1450, 180); x.lineTo(1270, 460); x.fill();
    x.fillStyle = '#f4f8f8'; rr(x, 1200, 560, 380, 70, 16); x.fill(); x.fillStyle = '#d7e4e4'; x.fillRect(1290, 630, 200, 270);
    x.fillStyle = '#9aa7a8'; x.fillRect(1380, 520, 20, 50);
    x.fillStyle = '#a7b8b8'; x.fillRect(0, 900, W, 200);
  }), 0, 0);
}
function kitchenDay(ctx) {
  ctx.drawImage(cached('kday', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#f3e1c2'], [1, '#e2c9a2']]); x.fillRect(0, 0, W, H);
    x.fillStyle = '#ffffff'; rr(x, 140, 170, 360, 300, 10); x.fill(); x.fillStyle = vgrad(x, 180, 460, [[0, '#9fd6ff'], [1, '#e2f4ff']]); x.fillRect(160, 190, 320, 260);
    x.fillStyle = '#fff3d6'; L.circle(x, 400, 260, 40); x.fill();
    for (let i = 0; i < 5; i++) { x.fillStyle = '#b98a5a'; x.fillRect(620 + i * 250, 150, 230, 220); x.fillStyle = '#8a6542'; x.fillRect(720 + i * 250, 300, 30, 8); }
    x.fillStyle = '#7a5a3c'; x.fillRect(0, 620, W, 40); x.fillStyle = '#b98a5a'; x.fillRect(0, 660, W, 300); for (let i = 0; i < 8; i++) { x.fillStyle = '#8a6542'; x.fillRect(80 + i * 240, 720, 40, 8); }
    x.fillStyle = '#d6c3a6'; x.fillRect(0, 960, W, 200);
  }), 0, 0);
}
function toaster(ctx, x, y, t, burn, pop) {
  ctx.fillStyle = '#c9ccd3'; rr(ctx, x - 90, y - 110, 180, 110, 26); ctx.fill(); ctx.fillStyle = '#9ea2ab'; ctx.fillRect(x + 70, y - 70, 30, 10);
  ctx.fillStyle = '#2b2b2b'; ctx.fillRect(x - 60, y - 112, 50, 8); ctx.fillRect(x + 10, y - 112, 50, 8);
  if (pop > 0) { const py = y - 110 - Math.sin(clamp(pop) * Math.PI) * 260 - (pop > 1 ? 0 : 0); for (const dx of [-35, 35]) { ctx.save(); ctx.translate(x + dx, py + 20); ctx.rotate(pop * (dx > 0 ? 3 : -3)); ctx.fillStyle = '#1b130c'; rr(ctx, -30, -40, 60, 70, 14); ctx.fill(); ctx.restore(); } }
  if (burn > 0) { ctx.save(); for (let i = 0; i < 9; i++) { const p = ((t * .6 + i / 9) % 1); ctx.fillStyle = `rgba(60,60,60,${.45 * burn * (1 - p)})`; circle(ctx, x + Math.sin(p * 6 + i) * 40, y - 120 - p * 380, 30 + p * 70); ctx.fill(); } ctx.restore(); }
}

// street: kind = 'morning' | 'rain' | 'night'
function street(ctx, t, kind = 'morning', camX = 0) {
  const key = 'street_' + kind;
  ctx.drawImage(cached(key, x => {
    const sky = kind === 'morning' ? [[0, '#8fcaf5'], [1, '#e9f5ff']] : kind === 'rain' ? [[0, '#3c4655'], [1, '#6d7684']] : [[0, '#070b16'], [1, '#18223a']];
    x.fillStyle = vgrad(x, 0, 760, sky); x.fillRect(0, 0, W, H);
    const r = rng(kind === 'night' ? 12 : 4);
    for (let i = 0; i < 16; i++) { const bw = 120 + r() * 90, bh = 260 + r() * 360, bx = i * 130 - 30;
      x.fillStyle = kind === 'morning' ? ['#c99f84', '#b7c4d1', '#d8c3a5'][i % 3] : kind === 'rain' ? ['#525c6a', '#47505c', '#5c6572'][i % 3] : ['#0d1322', '#111a2c', '#0a0f1b'][i % 3]; x.fillRect(bx, 760 - bh, bw, bh);
      for (let k = 0; k < 24; k++) { const wx = bx + 16 + (k % 4) * (bw / 4.4), wy = 760 - bh + 24 + Math.floor(k / 4) * 50; if (wy > 720) continue; const lit = kind === 'night' ? r() < .25 : kind === 'rain' ? r() < .4 : false;
        x.fillStyle = lit ? 'rgba(255,205,120,.85)' : kind === 'morning' ? 'rgba(255,255,255,.45)' : 'rgba(0,0,0,.25)'; x.fillRect(wx, wy, 18, 26); } }
    x.fillStyle = kind === 'morning' ? '#b5b0a6' : kind === 'rain' ? '#5a5f68' : '#1a1f2a'; x.fillRect(0, 760, W, 180); // sidewalk
    x.fillStyle = 'rgba(0,0,0,.12)'; for (let i = 0; i < 20; i++) x.fillRect(i * 110, 760, 4, 180);
    x.fillStyle = kind === 'morning' ? '#55585f' : kind === 'rain' ? '#33363d' : '#0b0d12'; x.fillRect(0, 940, W, 200); // road
    x.fillStyle = kind === 'night' ? 'rgba(255,255,255,.2)' : 'rgba(255,255,255,.7)'; for (let i = 0; i < 12; i++) x.fillRect(i * 180, 1010, 100, 8);
  }), 0, 0);
  if (kind === 'night' || kind === 'rain') {
    for (const lx of [260, 900, 1540]) { ctx.fillStyle = '#0a0d14'; ctx.fillRect(lx - 6, 420, 12, 360); ctx.fillRect(lx - 6, 420, 70, 10);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; const g = ctx.createLinearGradient(lx + 60, 430, lx + 60, 940); g.addColorStop(0, `rgba(255,205,130,${kind === 'night' ? .45 : .25})`); g.addColorStop(1, 'rgba(255,205,130,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(lx + 50, 432); ctx.lineTo(lx + 72, 432); ctx.lineTo(lx + 230, 940); ctx.lineTo(lx - 110, 940); ctx.closePath(); ctx.fill();
      ctx.fillStyle = rgrad(ctx, lx + 60, 940, 5, 200, [[0, 'rgba(255,205,130,.35)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(lx - 200, 840, 520, 200); ctx.restore();
      ctx.fillStyle = '#ffe0a0'; ell(ctx, lx + 60, 434, 18, 7); ctx.fill(); }
    // puddles
    for (const [px, pw] of [[420, 160], [1180, 220], [1720, 140]]) { ctx.fillStyle = 'rgba(160,180,220,.18)'; ell(ctx, px, 900, pw, 16); ctx.fill(); }
  }
}
function rain(ctx, t, k = 1, seed = 2, wind = .18) {
  if (k <= 0) return; const r = rng(seed); ctx.save(); ctx.strokeStyle = `rgba(200,215,240,${.35 * k})`; ctx.lineWidth = 2;
  ctx.beginPath(); const n = Math.floor(260 * k);
  for (let i = 0; i < n; i++) { const sp = 1400 + r() * 600, x0 = r() * (W + 300), y0 = r() * H; const y = (y0 + t * sp) % (H + 100) - 50, x = (x0 - (y * wind)) % (W + 300); ctx.moveTo(x, y); ctx.lineTo(x - 40 * wind * 2, y + 40); }
  ctx.stroke(); ctx.restore();
}
function splash(ctx, t, t0, x, y) { const p = clamp((t - t0) / .35); if (p <= 0 || p >= 1) return; ctx.save(); ctx.strokeStyle = `rgba(200,220,255,${.8 * (1 - p)})`; ctx.lineWidth = 3; for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(x + i * 8, y); ctx.lineTo(x + i * 22 * p * 2, y - 40 * Math.sin(p * Math.PI)); ctx.stroke(); } ctx.restore(); }

function bus(ctx, x, y, t, doorK = 0, moving = 0) {
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = 'rgba(0,0,0,.25)'; ell(ctx, 380, 6, 460, 20); ctx.fill();
  ctx.fillStyle = '#e8a33a'; rr(ctx, -60, -420, 900, 400, 40); ctx.fill(); ctx.fillStyle = '#c9832a'; ctx.fillRect(-60, -110, 900, 20);
  for (let i = 0; i < 5; i++) { ctx.fillStyle = '#28323f'; rr(ctx, 160 + i * 130, -380, 110, 140, 12); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(170 + i * 130, -370, 20, 120); }
  // door
  ctx.fillStyle = '#1b2430'; rr(ctx, -20, -380, 150, 360, 10); ctx.fill();
  const dk = clamp(doorK); ctx.fillStyle = '#3b4a5c'; ctx.fillRect(-20, -380, 75 * dk, 360); ctx.fillRect(130 - 75 * dk, -380, 75 * dk, 360);
  ctx.fillStyle = 'rgba(255,255,255,.2)'; if (dk > 0) { ctx.fillRect(-10, -360, 50 * dk, 160); ctx.fillRect(140 - 75 * dk, -360, 50 * dk, 160); }
  text(ctx, '42', 760, -460 + 70, { size: 46, weight: 900, color: '#1b2430' });
  for (const wx of [80, 700]) { ctx.fillStyle = '#121212'; circle(ctx, wx, -14, 62); ctx.fill(); ctx.fillStyle = '#777'; circle(ctx, wx, -14, 26); ctx.fill(); ctx.save(); ctx.translate(wx, -14); ctx.rotate(moving * 6); ctx.fillStyle = '#444'; ctx.fillRect(-4, -24, 8, 48); ctx.restore(); }
  ctx.fillStyle = '#fff4c0'; ell(ctx, 832, -80, 12, 18); ctx.fill();
  ctx.restore();
}

// classroom (side view). Students sit on the right, facing left toward the screen.
const SEATS = [ // x, groundY, scale, look-variety
  [1180, 770, .34, { hair: 'bun', shirt: '#9bc3e6' }], [1430, 770, .34, { shirt: '#f2c14e' }], [1680, 770, .34, { hair: 'pony', shirt: '#e6a0b8' }],
  [1100, 1000, .44, { shirt: '#9ad19a' }], [1380, 1000, .44, { hair: 'pony', shirt: '#f4ecd8', crush: 1 }], [1660, 1000, .44, { shirt: '#c7b5f0' }],
];
function classroom(ctx, t, o = {}) {
  ctx.drawImage(cached('class', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#e9dfcc'], [.7, '#ddd0b8'], [.71, '#a88f6e'], [1, '#8c7556']]); x.fillRect(0, 0, W, H);
    x.fillStyle = '#2f4a3a'; rr(x, 860, 170, 640, 300, 10); x.fill(); x.strokeStyle = '#7a5a3c'; x.lineWidth = 14; x.strokeRect(860, 170, 640, 300);
    x.strokeStyle = 'rgba(255,255,255,.55)'; x.lineWidth = 4; x.beginPath(); x.moveTo(910, 240); x.bezierCurveTo(980, 200, 1040, 280, 1110, 230); x.stroke();
    text(x, 'E = mc²', 1260, 250, { size: 52, weight: 600, color: 'rgba(255,255,255,.75)' }); text(x, 'Due: TODAY', 1050, 380, { size: 40, weight: 700, color: 'rgba(255,255,255,.6)' });
    x.fillStyle = '#5a4a3a'; x.fillRect(100, 140, 640, 12);
    x.fillStyle = '#7a5a3c'; rr(x, 1580, 560, 260, 80, 6); x.fill(); // teacher desk (far)
    x.fillStyle = 'rgba(0,0,0,.1)'; for (let i = 0; i < 14; i++) x.fillRect(i * 140, 760, 3, 320);
    for (let i = 0; i < 3; i++) { x.fillStyle = '#fff'; circle(x, 1620 + i * 50, 140, 0); }
    x.fillStyle = '#efe9dc'; circle(x, 1700, 140, 38); x.fill(); x.strokeStyle = '#333'; x.lineWidth = 4; x.beginPath(); x.arc(1700, 140, 38, 0, Math.PI * 2); x.stroke(); x.beginPath(); x.moveTo(1700, 140); x.lineTo(1700, 116); x.moveTo(1700, 140); x.lineTo(1718, 150); x.stroke();
  }), 0, 0);
  // projector screen + slide
  ctx.fillStyle = '#f8f8f6'; ctx.fillRect(120, 150, 600, 360); ctx.strokeStyle = '#999'; ctx.lineWidth = 3; ctx.strokeRect(120, 150, 600, 360);
  if (o.slide === 'frozen') { ctx.fillStyle = '#2a4b8d'; ctx.fillRect(140, 170, 560, 70); text(ctx, 'My Project: Final Presen', 160, 205, { size: 34, weight: 800, color: '#fff', align: 'left' });
    ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(140, 170, 560, 320); ctx.fillStyle = '#fff'; rr(ctx, 230, 280, 380, 120, 12); ctx.fill(); text(ctx, '(Not Responding)', 420, 320, { size: 30, weight: 700, color: '#333' });
    ctx.save(); ctx.translate(420, 365); ctx.rotate(t * 6); ctx.strokeStyle = '#2a7be4'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, 16, 0, Math.PI * 1.5); ctx.stroke(); ctx.restore(); }
  else if (o.slide === 'win') { ctx.fillStyle = '#ffd34a'; ctx.fillRect(140, 170, 560, 320); text(ctx, 'WORLD-CLASS', 420, 290, { size: 64, weight: 900, color: '#1b1b22' }); text(ctx, 'PRESENTATION', 420, 370, { size: 56, weight: 900, color: '#1b1b22' }); }
  else { ctx.fillStyle = '#e3e8f0'; ctx.fillRect(140, 170, 560, 320); text(ctx, 'Chapter 4', 420, 330, { size: 48, weight: 700, color: '#6b7a90' }); }
}
// seated student: draws body + desk. mood, look, cheer
function student(ctx, t, i, o = {}) {
  const [x, y, s, v] = SEATS[i];
  const laugh = o.laugh ? Math.abs(Math.sin(t * 9 + i)) : 0;
  const up = o.cheer;
  G.guy(ctx, x, y - (up ? 40 * s : 0) - laugh * 14 * s, s, { mood: o.mood || 'tired', t, seed: i * .7, flip: 1, look: o.look ?? .3, hair: v.hair, shirt: v.shirt, sit: !up,
    lh: up ? [-140, -760 - Math.sin(t * 8 + i) * 50] : o.laugh ? [-60, -380] : null, rh: up ? [160, -760 - Math.cos(t * 8 + i) * 50] : o.laugh ? [80, -420] : null, bendB: up ? -.6 : 1, bendF: up ? -.6 : 1,
    blush: v.crush && o.blush ? 1 : 0 });
  // desk in front (to the left, since they face left)
  if (!up) { ctx.fillStyle = '#9a7650'; rr(ctx, x - 300 * s - 120 * s, y - 330 * s, 300 * s, 34 * s, 6); ctx.fill(); ctx.fillStyle = '#7a5a3c'; ctx.fillRect(x - 380 * s, y - 300 * s, 22 * s, 300 * s); ctx.fillStyle = '#8a6a48'; rr(ctx, x - 40 * s, y - 330 * s, 220 * s, 330 * s, 10); ctx.fill(); }
}
function teacher(ctx, x, y, s, t, o = {}) {
  G.guy(ctx, x, y, s, { mood: o.mood || 'tired', t, seed: 3.1, look: o.look ?? .5, flip: o.flip, glasses: 0, shirt: '#6f86a8', pants: '#3a3f4a', rh: o.point ? [330, -560] : o.clap ? [40 + Math.abs(Math.sin(t * 10)) * 40, -480] : null, lh: o.clap ? [-20, -470] : null, bendF: o.point ? -.3 : 1,
    outfit(ctx) { ctx.fillStyle = '#c0392b'; ctx.beginPath(); ctx.moveTo(-14, -600); ctx.lineTo(14, -600); ctx.lineTo(6, -470); ctx.lineTo(0, -455); ctx.lineTo(-6, -470); ctx.closePath(); ctx.fill(); } });
  // glasses ring-style
  ctx.save(); ctx.translate(x, y); ctx.scale(s * (o.flip ? -1 : 1), s); ctx.strokeStyle = '#121212'; ctx.lineWidth = 7; for (const ex of [-46 + (o.look ?? .5) * 38, 54 + (o.look ?? .5) * 38]) { ctx.beginPath(); ctx.arc(ex, -741, 30, 0, Math.PI * 2); ctx.stroke(); } ctx.restore();
}

function cafeteria(ctx) {
  ctx.drawImage(cached('cafeteria', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#f4ead8'], [.66, '#ece0c9'], [.67, '#c9b48f'], [1, '#b39d78']]); x.fillRect(0, 0, W, H);
    for (let i = 0; i < 4; i++) { x.fillStyle = '#fff'; rr(x, 160 + i * 440, 160, 320, 260, 10); x.fill(); x.fillStyle = vgrad(x, 170, 410, [[0, '#a6d8ff'], [1, '#e6f5ff']]); x.fillRect(176 + i * 440, 176, 288, 228); }
    x.fillStyle = '#d0563a'; x.fillRect(0, 540, W, 14);
  }), 0, 0);
}
function lunchTable(ctx, x, y, w) { ctx.fillStyle = '#e2e2e2'; rr(ctx, x, y, w, 30, 8); ctx.fill(); ctx.fillStyle = '#bcbcbc'; ctx.fillRect(x, y + 30, w, 14); ctx.fillStyle = '#8a8a8a'; ctx.fillRect(x + 30, y + 44, 16, 130); ctx.fillRect(x + w - 46, y + 44, 16, 130); }
function tray(ctx, x, y, s = 1) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = '#7d8fa3'; rr(ctx, -90, -12, 180, 24, 6); ctx.fill(); ctx.fillStyle = '#fff'; ell(ctx, -30, -20, 40, 12); ctx.fill(); ctx.fillStyle = '#f2c14e'; ell(ctx, -30, -24, 26, 8); ctx.fill(); ctx.fillStyle = '#e05d5d'; rr(ctx, 30, -46, 30, 40, 6); ctx.fill(); ctx.restore(); }
function bagOnSeat(ctx, x, y) { ctx.fillStyle = '#121212'; rr(ctx, x - 64, y - 124, 128, 128, 32); ctx.fill(); ctx.fillStyle = '#6a4fb3'; rr(ctx, x - 58, y - 118, 116, 116, 28); ctx.fill(); ctx.fillStyle = '#4e3a87'; rr(ctx, x - 40, y - 70, 80, 46, 10); ctx.fill(); ctx.strokeStyle = '#4e3a87'; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(x, y - 118, 30, Math.PI, 0); ctx.stroke(); }

function cafe(ctx, t) {
  ctx.drawImage(cached('cafe', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#4a2f22'], [.62, '#5c3b2a'], [.63, '#3a251a'], [1, '#2a1a12']]); x.fillRect(0, 0, W, H);
    x.fillStyle = '#1e1410'; rr(x, 760, 150, 680, 230, 10); x.fill(); text(x, 'MENU', 1100, 190, { size: 34, weight: 900, color: '#f2d9b0', track: 6 });
    ['Espresso ........ 120', 'Latte ............ 180', 'Cold Coffee .... 160', 'Croissant ....... 140'].forEach((s, i) => text(x, s, 800, 240 + i * 34, { size: 24, weight: 600, color: 'rgba(242,217,176,.8)', align: 'left' }));
    for (const lx of [500, 1700]) { x.strokeStyle = '#120c09'; x.lineWidth = 4; x.beginPath(); x.moveTo(lx, 86); x.lineTo(lx, 200); x.stroke(); x.fillStyle = '#f2b35a'; ell(x, lx, 214, 40, 22); x.fill(); x.fillStyle = rgrad(x, lx, 240, 10, 360, [[0, 'rgba(255,190,100,.3)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(lx - 400, 200, 800, 700); }
    x.fillStyle = '#c4c4c8'; rr(x, 1500, 470, 220, 170, 16); x.fill(); x.fillStyle = '#8a8a90'; x.fillRect(1540, 560, 40, 60); x.fillRect(1640, 560, 40, 60);
    x.fillStyle = '#7a4f34'; x.fillRect(0, 640, W, 40); x.fillStyle = '#5c3b2a'; x.fillRect(0, 680, W, 260); for (let i = 0; i < 14; i++) { x.fillStyle = 'rgba(0,0,0,.15)'; x.fillRect(i * 140, 680, 4, 260); }
    // door on the left
    x.fillStyle = '#2a1a12'; x.fillRect(40, 220, 220, 720); x.fillStyle = 'rgba(160,200,230,.3)'; x.fillRect(70, 260, 160, 360);
    x.fillStyle = '#e0b04a'; circle(x, 270, 240, 14); x.fill();
  }), 0, 0);
}
function coffeeCup(ctx, x, y, s = 1) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = '#f4ece0'; ctx.beginPath(); ctx.moveTo(-28, -60); ctx.lineTo(28, -60); ctx.lineTo(20, 10); ctx.lineTo(-20, 10); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#7a4f34'; ctx.fillRect(-26, -40, 52, 22); ctx.fillStyle = '#3a251a'; rr(ctx, -32, -70, 64, 14, 6); ctx.fill(); ctx.restore(); }

module.exports = { bathroom, kitchenDay, toaster, street, rain, splash, bus, classroom, student, teacher, SEATS, cafeteria, lunchTable, tray, bagOnSeat, cafe, coffeeCup };
