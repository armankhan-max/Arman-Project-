// Backgrounds. Static parts are cached once; moving parts (fan, light, crowd) are drawn per frame.
const L = require('./lib');
const { W, H, clamp, lerp, E, rng, hash, circle, ell, rr, vgrad, rgrad, text, line } = L;
const G = require('./guy');

const cache = {};
function cached(key, fn) { if (!cache[key]) { const [c, x] = L.canvas(); fn(x); cache[key] = c; } return cache[key]; }

// ---------------- BEDROOM (side view) ----------------
const BED = { headX: 498, headY: 640, s: .46, nsX: 120, nsTop: 700, clockX: 205, clockY: 655 };
function bedroomStatic(x, day = false) {
  x.fillStyle = vgrad(x, 0, H, day ? [[0, '#e6d5b8'], [.62, '#d9c4a2'], [.63, '#a98a63'], [1, '#8a6c49']] : [[0, '#0f1626'], [.62, '#121b2e'], [.63, '#0b101b'], [1, '#070a11']]); x.fillRect(0, 0, W, H);
  // ceiling line
  x.fillStyle = day ? '#d3bf9e' : '#0b111d'; x.fillRect(0, 0, W, 128); x.fillStyle = 'rgba(255,255,255,.04)'; x.fillRect(0, 126, W, 3);
  // wall texture: faint vertical panels
  for (let i = 0; i < 14; i++) { x.fillStyle = `rgba(255,255,255,${.008 + hash(i) * .01})`; x.fillRect(i * 140, 128, 70, 560); }
  // poster frames
  x.fillStyle = day ? '#8a6f52' : '#0c1220'; rr(x, 620, 300, 170, 220, 6); x.fill(); x.strokeStyle = 'rgba(255,255,255,.07)'; x.lineWidth = 4; x.stroke();
  x.fillStyle = 'rgba(120,140,190,.10)'; x.beginPath(); x.moveTo(640, 500); x.lineTo(700, 400); x.lineTo(745, 460); x.lineTo(770, 430); x.lineTo(770, 500); x.closePath(); x.fill();
  x.fillStyle = day ? '#6f8fb3' : '#0c1220'; rr(x, 830, 340, 120, 150, 6); x.fill(); x.stroke();
  // window
  const wx = 1360, wy = 170, ww = 360, wh = 400;
  x.fillStyle = '#05070d'; rr(x, wx - 18, wy - 18, ww + 36, wh + 36, 10); x.fill();
  x.fillStyle = vgrad(x, wy, wy + wh, day ? [[0, '#7cc4ff'], [1, '#d6efff']] : [[0, '#0d1c3c'], [1, '#1d2d55']]); x.fillRect(wx, wy, ww, wh);
  const r = rng(5); if (!day) for (let i = 0; i < 40; i++) { x.fillStyle = `rgba(255,255,255,${.3 + r() * .6})`; circle(x, wx + r() * ww, wy + r() * wh * .6, .8 + r() * 1.4); x.fill(); }
  // moon
  if (day) { x.fillStyle = '#fff6d8'; circle(x, wx + 270, wy + 90, 44); x.fill(); } else {
  x.fillStyle = rgrad(x, wx + 270, wy + 90, 10, 160, [[0, 'rgba(220,230,255,.5)'], [1, 'rgba(220,230,255,0)']]); x.fillRect(wx, wy, ww, wh);
  x.fillStyle = '#e8eefc'; circle(x, wx + 270, wy + 90, 34); x.fill(); x.fillStyle = '#1a2a50'; circle(x, wx + 284, wy + 80, 30); x.fill(); }
  // city
  for (let i = 0; i < 9; i++) { const bw = 30 + r() * 40, bh = 80 + r() * 160, bx = wx + i * 42 - 10; x.fillStyle = day ? '#9bb8d6' : '#070b16'; x.fillRect(bx, wy + wh - bh, bw, bh);
    for (let k = 0; k < 6; k++) if (!day && r() < .12) { x.fillStyle = 'rgba(255,200,110,.85)'; x.fillRect(bx + 6 + (k % 2) * 14, wy + wh - bh + 14 + Math.floor(k / 2) * 22, 7, 9); } }
  // blinds
  for (let i = 0; i < (day ? 3 : 14); i++) { x.fillStyle = day ? 'rgba(240,235,225,.95)' : 'rgba(8,12,22,.78)'; x.fillRect(wx, wy + i * (wh / 14), ww, wh / 14 * .52); }
  x.fillStyle = '#05070d'; x.fillRect(wx + ww / 2 - 7, wy, 14, wh); x.fillRect(wx, wy + wh / 2 - 7, ww, 14);
  // floor
  x.fillStyle = vgrad(x, 880, H, day ? [[0, '#8a6847'], [1, '#6b4f35']] : [[0, '#0a0e18'], [1, '#05070c']]); x.fillRect(0, 880, W, H - 880);
  x.fillStyle = 'rgba(255,255,255,.03)'; x.fillRect(0, 880, W, 3);
  // bed frame
  x.fillStyle = '#1a1410'; rr(x, 318, 470, 48, 420, 12); x.fill(); // headboard
  x.fillStyle = '#2a2018'; rr(x, 330, 760, 1010, 80, 10); x.fill(); x.fillStyle = '#1a1410'; x.fillRect(350, 840, 26, 50); x.fillRect(1300, 840, 26, 50);
  x.fillStyle = '#c9c7d6'; rr(x, 340, 700, 990, 70, 18); x.fill(); // mattress/sheet
  x.fillStyle = 'rgba(0,0,0,.25)'; x.fillRect(340, 740, 990, 30);
  // pillow
  x.fillStyle = '#dcdbe8'; ell(x, 470, 690, 120, 36, -.05); x.fill(); x.fillStyle = 'rgba(0,0,0,.18)'; ell(x, 470, 706, 112, 16); x.fill();
  // nightstand
  x.fillStyle = '#231a14'; rr(x, 100, 700, 210, 190, 8); x.fill(); x.fillStyle = '#2e231b'; x.fillRect(96, 694, 218, 14);
  x.fillStyle = 'rgba(255,255,255,.06)'; x.fillRect(120, 760, 170, 4); x.fillStyle = '#5a4a3a'; circle(x, 205, 795, 6); x.fill();
  // clock body
  x.fillStyle = '#0a0a0c'; rr(x, 140, 630, 130, 64, 12); x.fill(); x.strokeStyle = '#26262c'; x.lineWidth = 3; x.stroke();
  // glass of water
  x.fillStyle = 'rgba(170,200,255,.18)'; rr(x, 278, 640, 30, 54, 4); x.fill(); x.fillStyle = 'rgba(170,200,255,.25)'; x.fillRect(280, 662, 26, 30);
}
function bedroomBase(ctx, day = false) { ctx.drawImage(cached(day ? 'bedroomDay' : 'bedroom', x => bedroomStatic(x, day)), 0, 0); }

function fan(ctx, t, speed = 1.3, cx = 960, cy = 158) {
  ctx.fillStyle = '#0a0d16'; ctx.fillRect(cx - 5, 112, 10, cy - 112); ell(ctx, cx, 116, 30, 8); ctx.fill();
  const a0 = t * speed; const blades = [0, 1, 2].map(i => a0 + i * Math.PI * 2 / 3).sort((a, b) => Math.sin(a) - Math.sin(b));
  const blade = a => { const ex = Math.cos(a) * 300, ey = Math.sin(a) * 22; ctx.save(); ctx.translate(cx, cy); ctx.fillStyle = Math.sin(a) < 0 ? '#0b0f1a' : '#141a29';
    ctx.beginPath(); ctx.moveTo(0, -5); ctx.quadraticCurveTo(ex * .5, ey * .5 - 14, ex, ey - 6); ctx.quadraticCurveTo(ex * 1.03, ey, ex, ey + 6); ctx.quadraticCurveTo(ex * .5, ey * .5 + 10, 0, 6); ctx.closePath(); ctx.fill(); ctx.restore(); };
  blades.filter(a => Math.sin(a) < 0).forEach(blade);
  ctx.fillStyle = '#161c2c'; ell(ctx, cx, cy, 44, 18); ctx.fill(); ctx.fillStyle = '#0d1120'; ell(ctx, cx, cy + 12, 22, 10); ctx.fill();
  blades.filter(a => Math.sin(a) >= 0).forEach(blade);
}
function clockDigits(ctx, s, glow = 1) {
  ctx.save(); ctx.shadowColor = 'rgba(255,70,60,.9)'; ctx.shadowBlur = 18 * glow;
  text(ctx, s, BED.clockX, BED.clockY + 6, { size: 40, weight: 700, color: '#ff4a3d', fam: 'Inter', track: 2 }); ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, BED.clockX, BED.clockY, 5, 170, [[0, `rgba(255,60,50,${.16 * glow})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 450, 450, 450); ctx.restore();
}
function moonBars(ctx, t, a = 1) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < 6; i++) { const y0 = 200 + i * 60; ctx.fillStyle = `rgba(120,150,230,${.035 * a * (.8 + .2 * Math.sin(t * .3 + i))})`;
    ctx.beginPath(); ctx.moveTo(1360, y0); ctx.lineTo(1360, y0 + 26); ctx.lineTo(760, y0 + 400 + 26); ctx.lineTo(760, y0 + 400); ctx.closePath(); ctx.fill(); }
  ctx.restore();
}
// Blanket over the body (draw after head/body-under). bump = breathing
function blanket(ctx, t, o = {}) {
  const br = Math.sin(t * 1.4) * 4; const knee = o.knee || 0;
  ctx.save(); ctx.fillStyle = o.col || '#2c3d63';
  ctx.beginPath(); ctx.moveTo(548, 720); ctx.bezierCurveTo(560, 650 - br, 700, 640 - br, 820, 660 - br * .5); ctx.bezierCurveTo(950, 676, 1040, 650 - knee * 40, 1120, 655 - knee * 50);
  ctx.bezierCurveTo(1220, 662, 1300, 680, 1338, 705); ctx.lineTo(1352, 820); ctx.bezierCurveTo(1000, 846, 700, 840, 540, 812); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.moveTo(540, 760); ctx.bezierCurveTo(800, 780, 1100, 770, 1350, 760); ctx.lineTo(1352, 820); ctx.bezierCurveTo(1000, 846, 700, 840, 540, 812); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,.06)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(560, 690 - br); ctx.bezierCurveTo(700, 660, 820, 672, 940, 690); ctx.stroke();
  ctx.fillStyle = '#d6d4e2'; ctx.beginPath(); ctx.moveTo(548, 722); ctx.bezierCurveTo(556, 690 - br, 600, 668 - br, 650, 664 - br); ctx.lineTo(668, 690 - br); ctx.bezierCurveTo(620, 694, 580, 712, 566, 728); ctx.closePath(); ctx.fill(); // sheet fold
  ctx.restore();
}
// Phone light on the face/wall
function phoneGlow(ctx, x, y, a = 1, col = '120,165,255', r = 520) {
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, x, y, 8, r, [[0, `rgba(${col},${.42 * a})`], [.3, `rgba(${col},${.14 * a})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.restore();
}
// Giant shadow-self on the wall/ceiling (grows with k)
function wallShadow(ctx, t, k, x = 900, y = 900, clip = [372, 86, 975, 612]) {
  if (k <= 0.01) return; const s = .45 + k * .75;
  ctx.save(); ctx.beginPath(); ctx.rect(...clip); ctx.clip(); ctx.globalAlpha = clamp(k * 1.4) * .9;
  // lit wall patch so the shadow reads
  ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, x, 360, 30, 800, [[0, 'rgba(90,120,200,.22)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over';
  const wob = Math.sin(t * 2.1) * 8 * k;
  ctx.translate(x + wob, y); ctx.scale(s, s);
  ctx.fillStyle = 'rgba(2,3,8,.92)';
  ctx.beginPath(); ctx.arc(0, -560, 190, 0, Math.PI * 2); ctx.fill();
  rr(ctx, -170, -420, 340, 520, 150); ctx.fill();
  // claw-like arms reaching
  ctx.lineCap = 'round'; ctx.strokeStyle = 'rgba(2,3,8,.92)'; ctx.lineWidth = 80;
  ctx.beginPath(); ctx.moveTo(-140, -360); ctx.quadraticCurveTo(-380, -420 - k * 80, -520 - k * 120, -560 + Math.sin(t * 1.3) * 30); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(140, -360); ctx.quadraticCurveTo(380, -440 - k * 80, 540 + k * 100, -600 + Math.cos(t * 1.1) * 30); ctx.stroke();
  // eyes
  const eA = clamp((k - .35) * 2.5); if (eA > 0) { ctx.fillStyle = `rgba(255,70,60,${eA})`; ctx.shadowColor = 'rgba(255,60,40,.9)'; ctx.shadowBlur = 30; ell(ctx, -60, -575, 26, 12, .25); ctx.fill(); ell(ctx, 60, -575, 26, 12, -.25); ctx.fill(); }
  ctx.restore();
}

// figure lying in bed. o: mood, look, armsUp (phone above face), hold point, drum (t), turned (face into pillow)
function lyingGuy(ctx, t, o = {}) {
  const s = BED.s, hx = BED.headX + (o.headDX || 0), hy = BED.headY + (o.headDY || 0);
  const r = 132 * s;
  if (o.rim) G.head(ctx, hx - 4, hy - 4, r, { sil: o.rim, rot: o.rot ?? -.32 });
  G.head(ctx, hx, hy, r, { mood: o.mood || 'tired', look: o.look ?? .5, lookY: o.lookY ?? -.6, rot: o.rot ?? -.32, t, seed: 1.3, back: o.turned, lid: o.lid, eye: o.eye, mouth: o.mouth, tear: o.tear, blush: o.blush, brow: o.brow });
  blanket(ctx, t, { knee: o.knee || 0 });
  // arms
  const ol = 5, aw = 62 * s;
  const sh = [585, 700];
  if (o.hands) for (const [hxp, hyp, back] of o.hands) { const el = [(sh[0] + hxp) / 2 + 30, (sh[1] + hyp) / 2 + 40]; G.limb(ctx, [sh[0] + (back ? -10 : 10), sh[1]], el, [hxp, hyp], aw, back ? G.BACK : G.SKIN, null, ol); }
}

// ---------------- DREAM: STAGE ----------------
function stage(ctx, t, k = 1) {
  ctx.fillStyle = vgrad(ctx, 0, H, [[0, '#14062a'], [.6, '#3a0f4f'], [1, '#12041c']]); ctx.fillRect(0, 0, W, H);
  // back LED wall
  for (let i = 0; i < 24; i++) for (let j = 0; j < 8; j++) { const v = .5 + .5 * Math.sin(t * 3 + i * .5 + j * .7); ctx.fillStyle = `rgba(${200 + 55 * v | 0},${60 + 90 * v | 0},255,${.05 + .07 * v})`; ctx.fillRect(220 + i * 62, 170 + j * 52, 56, 46); }
  // spot cones
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < 6; i++) { const sx = 200 + i * 300, ang = Math.PI / 2 + Math.sin(t * .9 + i * 1.7) * .45; const len = 1200;
    const g = ctx.createLinearGradient(sx, 90, sx + Math.cos(ang) * len, 90 + Math.sin(ang) * len); const c = i % 2 ? '255,90,200' : '120,140,255'; g.addColorStop(0, `rgba(${c},.35)`); g.addColorStop(1, `rgba(${c},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(sx, 90); ctx.lineTo(sx + Math.cos(ang - .09) * len, 90 + Math.sin(ang - .09) * len); ctx.lineTo(sx + Math.cos(ang + .09) * len, 90 + Math.sin(ang + .09) * len); ctx.closePath(); ctx.fill(); }
  // main spot on the singer
  ctx.fillStyle = rgrad(ctx, 960, 700, 20, 420, [[0, 'rgba(255,240,210,.55)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(400, 200, 1100, 800);
  ctx.restore();
  // stage floor
  ctx.fillStyle = '#0c0614'; ctx.fillRect(0, 760, W, 400); ctx.fillStyle = 'rgba(255,120,220,.25)'; ctx.fillRect(0, 760, W, 4);
}
function crowd(ctx, t, energy = 1, y0 = 1000) {
  const r = rng(77);
  for (let row = 0; row < 3; row++) for (let i = 0; i < 26; i++) {
    const x = i * 78 + (row % 2) * 39 - 20 + r() * 20, y = y0 - row * 50 + Math.abs(Math.sin(t * (5 + r() * 2) + i)) * -18 * energy;
    const c = ['#0b0412', '#12061c', '#1a0a26'][row]; ctx.fillStyle = c; circle(ctx, x, y - 70, 36); ctx.fill(); rr(ctx, x - 40, y - 40, 80, 120, 34); ctx.fill();
    if (r() < .55) { const ax = x + (r() < .5 ? -30 : 30), sw = Math.sin(t * 4 + i) * 18; ctx.strokeStyle = c; ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(ax, y - 30); ctx.lineTo(ax + sw, y - 150); ctx.stroke();
      if (r() < .45) { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, ax + sw, y - 160, 1, 30, [[0, 'rgba(255,255,240,.95)'], [1, 'rgba(255,255,240,0)']]); ctx.fillRect(ax + sw - 30, y - 190, 60, 60); ctx.restore(); } }
  }
}
function confetti(ctx, t, t0, n = 120, seed = 3) {
  if (t < t0) return; const r = rng(seed); const lt = t - t0;
  for (let i = 0; i < n; i++) { const x = r() * W + Math.sin(lt * 2 + i) * 30, y = -50 + ((r() * 600 + lt * (180 + r() * 160)) % 1150), a = lt * 4 + i;
    ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.fillStyle = ['#ff5ea8', '#ffd84a', '#6ae0ff', '#a98bff', '#fff'][i % 5]; ctx.fillRect(-7, -3 * Math.abs(Math.cos(a)), 14, 6 * Math.abs(Math.cos(a)) + 1); ctx.restore(); }
}

// ---------------- DREAM: CAR / HOUSE ----------------
function sunsetSky(ctx, top = '#2b1b4a', mid = '#e0567a', low = '#ffb35c') {
  ctx.fillStyle = vgrad(ctx, 0, 800, [[0, top], [.6, mid], [1, low]]); ctx.fillRect(0, 0, W, H);
  L.sunDisc(ctx, 1450, 640, 70, '255,226,170');
}
function carSet(ctx, t) {
  ctx.drawImage(cached('carset', x => {
    sunsetSky(x);
    const r = rng(9); for (let i = 0; i < 30; i++) { const bw = 50 + r() * 90, bh = 120 + r() * 330, bx = i * 70 - 40; x.fillStyle = 'rgba(40,16,50,.85)'; x.fillRect(bx, 800 - bh, bw, bh); for (let k = 0; k < 10; k++) if (r() < .3) { x.fillStyle = 'rgba(255,210,140,.7)'; x.fillRect(bx + 8 + (k % 3) * 16, 800 - bh + 14 + Math.floor(k / 3) * 26, 8, 12); } }
    x.fillStyle = '#20122a'; x.fillRect(0, 800, W, 300); x.fillStyle = 'rgba(255,190,120,.25)'; x.fillRect(0, 800, W, 4);
    for (let i = 0; i < 12; i++) { x.fillStyle = 'rgba(255,220,160,.5)'; x.fillRect(i * 180, 930, 100, 8); }
    palm(x, 260, 820, 1.1); palm(x, 1700, 820, .9);
  }), 0, 0);
}
function palm(x, px, py, s) { x.save(); x.translate(px, py); x.scale(s, s); x.strokeStyle = '#1a0c20'; x.lineWidth = 22; x.lineCap = 'round'; x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(30, -200, 10, -420); x.stroke(); x.fillStyle = '#1a0c20';
  for (let i = 0; i < 7; i++) { const a = -Math.PI + i * Math.PI / 6; x.beginPath(); x.moveTo(10, -420); x.quadraticCurveTo(10 + Math.cos(a) * 120, -470 + Math.sin(a) * 60, 10 + Math.cos(a) * 220, -400 + Math.abs(Math.cos(a)) * 60); x.quadraticCurveTo(10 + Math.cos(a) * 110, -440, 10, -410); x.fill(); } x.restore(); }
function sportsCar(ctx, x, y, s = 1, t = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = 'rgba(0,0,0,.35)'; ell(ctx, 0, 8, 430, 26); ctx.fill();
  ctx.fillStyle = '#d6263c'; ctx.beginPath(); ctx.moveTo(-420, -30); ctx.quadraticCurveTo(-410, -110, -300, -120); ctx.lineTo(-150, -130); ctx.quadraticCurveTo(-60, -215, 90, -210); ctx.quadraticCurveTo(200, -205, 280, -130); ctx.quadraticCurveTo(420, -120, 430, -60); ctx.lineTo(430, -20); ctx.quadraticCurveTo(430, 0, 400, 0); ctx.lineTo(-400, 0); ctx.quadraticCurveTo(-425, -5, -420, -30); ctx.fill();
  ctx.fillStyle = '#1b2b45'; ctx.beginPath(); ctx.moveTo(-120, -132); ctx.quadraticCurveTo(-50, -195, 80, -195); ctx.quadraticCurveTo(170, -192, 240, -132); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.moveTo(-60, -140); ctx.lineTo(10, -188); ctx.lineTo(40, -188); ctx.lineTo(-30, -140); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.fillRect(-380, -70, 760, 6);
  for (const wx of [-250, 270]) { ctx.fillStyle = '#0d0d10'; circle(ctx, wx, -8, 70); ctx.fill(); ctx.fillStyle = '#9aa0ad'; circle(ctx, wx, -8, 38); ctx.fill(); ctx.save(); ctx.translate(wx, -8); ctx.rotate(t * 3); ctx.strokeStyle = '#555a66'; ctx.lineWidth = 7; for (let i = 0; i < 5; i++) { ctx.rotate(Math.PI * 2 / 5); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(34, 0); ctx.stroke(); } ctx.restore(); }
  ctx.fillStyle = '#ffe7a8'; ell(ctx, 410, -66, 18, 10); ctx.fill();
  ctx.restore();
}
function houseSet(ctx, t) {
  ctx.drawImage(cached('house', x => {
    sunsetSky(x, '#1a1440', '#7a3f8a', '#f39a6a');
    x.fillStyle = '#1b1430'; x.fillRect(0, 800, W, 300);
    // modern house
    x.fillStyle = '#efe7da'; x.fillRect(420, 360, 1080, 440); x.fillStyle = '#2a2236'; x.fillRect(380, 330, 1160, 40); x.fillRect(700, 560, 900, 26);
    x.fillStyle = '#d9cfbf'; x.fillRect(420, 586, 1080, 214);
    for (const [wx, wy, ww, wh] of [[470, 400, 300, 150], [820, 400, 300, 150], [1170, 400, 280, 150], [470, 620, 420, 170], [960, 620, 220, 170], [1220, 620, 230, 170]]) {
      x.fillStyle = rgrad(x, wx + ww / 2, wy + wh / 2, 10, ww, [[0, '#ffe2a0'], [1, '#f2a85a']]); x.fillRect(wx, wy, ww, wh); x.fillStyle = 'rgba(80,50,30,.35)'; x.fillRect(wx + ww / 2 - 3, wy, 6, wh); }
    // pool
    x.fillStyle = '#3fc6e0'; x.beginPath(); x.moveTo(300, 860); x.lineTo(1650, 860); x.lineTo(1760, 990); x.lineTo(180, 990); x.closePath(); x.fill();
    x.fillStyle = 'rgba(255,230,170,.35)'; for (let i = 0; i < 8; i++) x.fillRect(420 + i * 140, 900 + (i % 3) * 22, 80, 5);
    palm(x, 230, 850, 1.2); palm(x, 1720, 850, 1.0);
  }), 0, 0);
  ctx.save(); ctx.globalCompositeOperation = 'screen'; for (let i = 0; i < 10; i++) { ctx.fillStyle = `rgba(255,255,255,${.12 + .1 * Math.sin(t * 3 + i)})`; ctx.fillRect(330 + i * 135 + Math.sin(t + i) * 20, 880 + (i % 4) * 26, 60, 4); } ctx.restore();
}

// ---------------- DREAM: SCHOOL HALLWAY (soft) ----------------
function hallway(ctx, t, red = 0) {
  ctx.drawImage(cached('hall', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#f6d6c8'], [.7, '#efc0b0'], [1, '#d99f92']]); x.fillRect(0, 0, W, H);
    for (let i = 0; i < 3; i++) { x.fillStyle = 'rgba(255,250,235,.85)'; rr(x, 1180 + i * 230, 170, 190, 330, 10); x.fill(); x.fillStyle = 'rgba(255,220,190,.6)'; x.fillRect(1180 + i * 230 + 92, 170, 6, 330); }
    for (let i = 0; i < 9; i++) { x.fillStyle = i % 2 ? '#8fb3c9' : '#86a9bf'; x.fillRect(60 + i * 115, 360, 108, 480); x.fillStyle = 'rgba(0,0,0,.12)'; for (let k = 0; k < 4; k++) x.fillRect(80 + i * 115, 390 + k * 14, 60, 6); x.fillStyle = '#5b7486'; x.fillRect(150 + i * 115, 560, 8, 40); }
    x.fillStyle = '#c98f80'; x.fillRect(0, 840, W, 260); x.fillStyle = 'rgba(255,255,255,.25)'; x.fillRect(0, 840, W, 5);
  }), 0, 0);
  // bokeh
  ctx.save(); ctx.globalCompositeOperation = 'screen'; const r = rng(31);
  for (let i = 0; i < 26; i++) { const x = r() * W, y = r() * 700, rad = 20 + r() * 60, a = .08 + .08 * Math.sin(t + i); ctx.fillStyle = rgrad(ctx, x, y, 1, rad, [[0, `rgba(255,${200 - red * 120 | 0},${200 - red * 150 | 0},${a})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  ctx.restore();
}
function hearts(ctx, t, t0, x, y, n = 6) {
  if (t < t0) return; const lt = t - t0;
  for (let i = 0; i < n; i++) { const p = ((lt * .5 + i / n) % 1); const hx = x + Math.sin(p * 6 + i) * 40 + (i - n / 2) * 18, hy = y - p * 260, s = 14 + (1 - p) * 10; ctx.save(); ctx.globalAlpha = Math.sin(p * Math.PI) * .9; heart(ctx, hx, hy, s, '#ff6f91'); ctx.restore(); }
}
function heart(ctx, x, y, s, col) { ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x, y + s * .9); ctx.bezierCurveTo(x - s * 1.6, y - s * .2, x - s * .7, y - s * 1.3, x, y - s * .45); ctx.bezierCurveTo(x + s * .7, y - s * 1.3, x + s * 1.6, y - s * .2, x, y + s * .9); ctx.fill(); }

// ---------------- FLASHBACK: RESTAURANT (grey) ----------------
function restaurant(ctx) {
  ctx.drawImage(cached('rest', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#3a3836'], [.68, '#4a4744'], [.69, '#2e2c2a'], [1, '#232120']]); x.fillRect(0, 0, W, H);
    for (let i = 0; i < 20; i++) { x.fillStyle = i % 2 ? 'rgba(255,255,255,.03)' : 'rgba(0,0,0,.03)'; x.fillRect(i * 100, 86, 100, 650); }
    x.fillStyle = '#2b2927'; rr(x, 300, 250, 260, 190, 6); x.fill(); x.fillStyle = '#5a5652'; x.fillRect(318, 268, 224, 154);
    x.fillStyle = '#6e6a65'; x.beginPath(); x.moveTo(330, 410); x.lineTo(400, 330); x.lineTo(460, 380); x.lineTo(500, 350); x.lineTo(530, 410); x.fill();
    // hanging lamp
    x.strokeStyle = '#1f1d1c'; x.lineWidth = 4; x.beginPath(); x.moveTo(1000, 86); x.lineTo(1000, 250); x.stroke(); x.fillStyle = '#1f1d1c'; x.beginPath(); x.moveTo(930, 300); x.lineTo(1070, 300); x.lineTo(1030, 250); x.lineTo(970, 250); x.fill();
    x.fillStyle = rgrad(x, 1000, 420, 10, 520, [[0, 'rgba(255,255,255,.18)'], [1, 'rgba(255,255,255,0)']]); x.fillRect(400, 250, 1200, 700);
    // table
    x.fillStyle = '#d9d6d0'; x.beginPath(); x.moveTo(640, 700); x.lineTo(1340, 700); x.lineTo(1380, 790); x.lineTo(600, 790); x.closePath(); x.fill();
    x.fillStyle = '#bebbb4'; x.fillRect(600, 790, 780, 120); x.fillStyle = '#2b2927'; x.fillRect(640, 910, 22, 100); x.fillRect(1320, 910, 22, 100);
    x.fillStyle = '#f2f0ec'; ell(x, 900, 730, 80, 20); x.fill(); x.fillStyle = '#a7a39b'; ell(x, 900, 724, 50, 12); x.fill();
    x.fillStyle = 'rgba(220,220,220,.5)'; rr(x, 1100, 670, 30, 56, 4); x.fill();
  }), 0, 0);
}

// ---------------- KITCHEN (fridge) ----------------
function kitchen(ctx, t, open = 0) {
  ctx.drawImage(cached('kitchen', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#0b1120'], [.72, '#101829'], [.73, '#0a0e18'], [1, '#05070c']]); x.fillRect(0, 0, W, H);
    for (let i = 0; i < 16; i++) { x.strokeStyle = 'rgba(255,255,255,.03)'; x.lineWidth = 2; x.beginPath(); x.moveTo(i * 130, 790); x.lineTo(i * 130 - 200, H); x.stroke(); }
    x.fillStyle = '#121a2b'; x.fillRect(0, 560, 1100, 230); x.fillStyle = '#1a2337'; x.fillRect(0, 548, 1100, 16);
    for (let i = 0; i < 4; i++) { x.fillStyle = '#0e1524'; x.fillRect(30 + i * 270, 600, 240, 170); x.fillStyle = '#2a3348'; x.fillRect(130 + i * 270, 620, 40, 6); }
    x.fillStyle = '#0e1524'; for (let i = 0; i < 4; i++) x.fillRect(30 + i * 270, 160, 240, 230);
    x.fillStyle = '#1a2235'; x.fillRect(1240, 220, 330, 590); // fridge
    x.fillStyle = '#121a2a'; x.fillRect(1240, 440, 330, 8); x.fillStyle = '#2c3650'; x.fillRect(1260, 300, 10, 100); x.fillRect(1260, 480, 10, 130);
  }), 0, 0);
  if (open > 0) {
    // light flood
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    const a = open; ctx.fillStyle = `rgba(255,232,180,${.10 * a})`; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = rgrad(ctx, 1240, 520, 30, 1000, [[0, `rgba(255,230,170,${.55 * a})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H);
    ctx.restore();
    // open fridge interior + door
    ctx.fillStyle = `rgba(255,246,222,${a})`; ctx.fillRect(1250, 230, 310, 570); ctx.fillStyle = 'rgba(200,190,170,.8)'; for (let i = 0; i < 3; i++) ctx.fillRect(1250, 330 + i * 140, 310, 6);
    const items = [[1290, 300, 40, 30, '#e05d5d'], [1350, 290, 30, 40, '#7fc77a'], [1440, 440, 60, 30, '#f2c14e'], [1300, 580, 40, 50, '#9ad0f5'], [1460, 580, 40, 50, '#e7e2d4']];
    for (const [ix, iy, iw, ih, c] of items) { ctx.fillStyle = c; rr(ctx, ix, iy, iw, ih, 6); ctx.fill(); }
    ctx.fillStyle = '#1e2740'; ctx.beginPath(); ctx.moveTo(1240, 220); ctx.lineTo(1240 - 260 * a, 180); ctx.lineTo(1240 - 260 * a, 860); ctx.lineTo(1240, 810); ctx.closePath(); ctx.fill();
  }
}

// ---------------- DESK: paper under lamp (top-down) ----------------
function desk(ctx, t) {
  ctx.drawImage(cached('desk', x => {
    x.fillStyle = '#1b130e'; x.fillRect(0, 0, W, H);
    for (let i = 0; i < 30; i++) { x.strokeStyle = `rgba(255,200,150,${.02 + hash(i) * .03})`; x.lineWidth = 3; x.beginPath(); x.moveTo(0, i * 40 + hash(i * 3) * 20); x.bezierCurveTo(600, i * 40 + 30, 1200, i * 40 - 20, W, i * 40 + 10); x.stroke(); }
    x.fillStyle = rgrad(x, 980, 520, 50, 900, [[0, 'rgba(255,200,130,.35)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, W, H);
    x.save(); x.translate(980, 560); x.rotate(-.03); x.shadowColor = 'rgba(0,0,0,.6)'; x.shadowBlur = 40; x.fillStyle = '#f4ecd8'; x.fillRect(-420, -430, 840, 900); x.shadowColor = 'transparent';
    for (let i = 0; i < 16; i++) { x.fillStyle = 'rgba(80,120,200,.25)'; x.fillRect(-420, -300 + i * 52, 840, 2); } x.fillStyle = 'rgba(220,80,80,.35)'; x.fillRect(-330, -430, 2, 900);
    x.restore();
    x.fillStyle = '#c7b9a0'; rr(x, 1500, 300, 140, 140, 70); x.fill(); x.fillStyle = '#3b2a1e'; circle(x, 1570, 370, 52); x.fill(); // mug
  }), 0, 0);
}

// ---------------- MOM's ROOM (split-screen) ----------------
function momRoom(ctx, t) {
  ctx.drawImage(cached('mom', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#1f150f'], [.65, '#2a1c12'], [.66, '#160f0a'], [1, '#0d0906']]); x.fillRect(0, 0, W, H);
    x.fillStyle = rgrad(x, 1300, 560, 20, 700, [[0, 'rgba(255,190,110,.35)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, W, H);
    x.fillStyle = '#3a2618'; rr(x, 1180, 600, 220, 230, 8); x.fill(); x.fillStyle = '#ffd08a'; x.beginPath(); x.moveTo(1230, 520); x.lineTo(1350, 520); x.lineTo(1320, 440); x.lineTo(1260, 440); x.closePath(); x.fill(); x.fillStyle = '#5a3a24'; x.fillRect(1284, 520, 12, 80);
    x.fillStyle = '#2d1e14'; rr(x, 1225, 300, 130, 110, 6); x.fill(); x.fillStyle = '#7a5a3e'; x.fillRect(1238, 312, 104, 86); x.fillStyle = '#e7e2d4'; circle(x, 1275, 350, 16); x.fill(); circle(x, 1310, 358, 12); x.fill();
    x.fillStyle = '#4a2f22'; rr(x, 200, 700, 950, 90, 16); x.fill(); x.fillStyle = '#8c3b3b'; rr(x, 240, 640, 880, 90, 30); x.fill();
  }), 0, 0);
}

module.exports = { BED, bedroomBase, fan, clockDigits, moonBars, blanket, phoneGlow, wallShadow, lyingGuy, stage, crowd, confetti, carSet, sportsCar, houseSet, hallway, hearts, heart, restaurant, kitchen, desk, momRoom, palm, cached };
