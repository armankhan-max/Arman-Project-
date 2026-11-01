// Backgrounds ("sets"). Static layers are painted once and cached; scenes add live layers on top.
const L = require('./lib');
const { W, H, canvas, rr, circle, ell, line, vgrad, rgrad, rng, text } = L;

const cache = {};
function cached(key, fn) { if (!cache[key]) { const [c, x] = canvas(); fn(x); cache[key] = c; } return cache[key]; }

const PAL = {
  dawn: { sky: [[0, '#5b6fa8'], [.45, '#e8a07a'], [.75, '#f7c983'], [1, '#ffe2a8']], far: '#9c7a92', mid: '#6e5470', near: '#3b2c40', ground: ['#5a4440', '#2f2329'], light: 'rgba(255,200,140,', sun: [1480, 420] },
  day: { sky: [[0, '#f0b45e'], [.55, '#f6cf88'], [1, '#fde7b8']], far: '#c79a6a', mid: '#a5744c', near: '#6d4a32', ground: ['#8a6446', '#4d3424'], light: 'rgba(255,225,160,', sun: [1500, 230] },
  noon: { sky: [[0, '#e9a64e'], [.6, '#f7d38a'], [1, '#fff0c9']], far: '#d0a46e', mid: '#ad7d52', near: '#73503a', ground: ['#94704f', '#5a3e2a'], light: 'rgba(255,240,190,', sun: [960, 160] },
  sunset: { sky: [[0, '#2b2350'], [.4, '#8e3f63'], [.7, '#e86a45'], [1, '#ffb15e']], far: '#7a3f5a', mid: '#4f2a48', near: '#251732', ground: ['#3a2233', '#170d1c'], light: 'rgba(255,150,100,', sun: [1300, 640] },
  night: { sky: [[0, '#070a1c'], [.6, '#16204a'], [1, '#2c3566']], far: '#1d2550', mid: '#141a3a', near: '#0b0f24', ground: ['#151a33', '#07091a'], light: 'rgba(150,180,255,', sun: [1500, 210] },
  predawn: { sky: [[0, '#151a3a'], [.55, '#4a3f6e'], [.85, '#c7787a'], [1, '#f2a46e']], far: '#4e3e66', mid: '#33284c', near: '#1c1530', ground: ['#2a2238', '#120d1c'], light: 'rgba(255,170,130,', sun: [1600, 760] },
};

function sky(x, p) { x.fillStyle = vgrad(x, 0, H, p.sky); x.fillRect(0, 0, W, H); }
function stars(x, n, seed) { const r = rng(seed); for (let i = 0; i < n; i++) { x.fillStyle = `rgba(255,255,255,${.3 + r() * .7})`; circle(x, r() * W, r() * H * .6, r() * 1.8 + .3); x.fill(); } }
function skyline(x, seed, base, col, minH, maxH, { win = null, wmin = 70, wmax = 180, haze = null } = {}) {
  const r = rng(seed); let px = -40;
  while (px < W + 40) {
    const w = wmin + r() * (wmax - wmin), h = minH + r() * (maxH - minH);
    x.fillStyle = col; x.fillRect(px, base - h, w, h + 400);
    if (r() < .3) { x.fillRect(px + w * .4, base - h - 30, 6, 30); }
    if (r() < .25) { x.fillRect(px + w * .15, base - h - 18, w * .3, 18); }
    if (win) { for (let wy = base - h + 20; wy < base - 20; wy += 34) for (let wx = px + 12; wx < px + w - 18; wx += 26) if (r() < .45) { x.fillStyle = win; x.fillRect(wx, wy, 12, 16); } x.fillStyle = col; }
    px += w + r() * 8;
  }
  if (haze) { x.fillStyle = vgrad(x, base - maxH, base + 40, [[0, 'rgba(0,0,0,0)'], [1, haze]]); x.fillRect(0, base - maxH, W, maxH + 40); }
}
function hazeBand(x, y0, y1, col) { x.fillStyle = vgrad(x, y0, y1, [[0, col + '0)'], [1, col + '.55)']]); x.fillRect(0, y0, W, y1 - y0); }
function ground(x, p, y) { x.fillStyle = vgrad(x, y, H, [[0, p.ground[0]], [1, p.ground[1]]]); x.fillRect(0, y, W, H - y); }
function tree(x, cx, base, s, col, trunk = null) {
  x.fillStyle = trunk || col; x.beginPath(); x.moveTo(cx - 14 * s, base); x.lineTo(cx - 8 * s, base - 120 * s); x.lineTo(cx + 8 * s, base - 120 * s); x.lineTo(cx + 14 * s, base); x.fill();
  x.fillStyle = col; const r = rng(Math.floor(cx * 7 + s * 13));
  for (let i = 0; i < 9; i++) { circle(x, cx + (r() - .5) * 150 * s, base - 150 * s - r() * 90 * s, (45 + r() * 35) * s); x.fill(); }
}

// ---------- props ----------
function bus(x, bx, by, s = 1, { col = '#f0b429', sign = 'ELM ST  12', driver = false, mirror = true, lights = false, t = 0 } = {}) {
  x.save(); x.translate(bx, by); x.scale(s, s);
  // body (front faces right). by = ground
  x.fillStyle = 'rgba(0,0,0,.35)'; ell(x, 0, 6, 560, 22); x.fill();
  x.fillStyle = col; rr(x, -540, -360, 1080, 320, 40); x.fill();
  x.fillStyle = '#f7f1e3'; rr(x, -540, -360, 1080, 70, 36); x.fill(); x.fillRect(-540, -320, 1080, 30);
  x.fillStyle = 'rgba(0,0,0,.18)'; x.fillRect(-540, -110, 1080, 70);
  // windows
  for (let i = 0; i < 6; i++) { const wx = -500 + i * 150; x.fillStyle = '#23334f'; rr(x, wx, -275, 128, 120, 12); x.fill(); x.fillStyle = 'rgba(255,255,255,.12)'; x.beginPath(); x.moveTo(wx + 20, -275); x.lineTo(wx + 60, -275); x.lineTo(wx + 10, -155); x.lineTo(wx - 0, -175); x.fill(); }
  // door + windshield
  x.fillStyle = '#1d2a42'; rr(x, 400, -290, 120, 250, 10); x.fill(); line(x, [460, -290, 460, -40], 4, '#0f1626');
  x.fillStyle = '#2b3d5e'; rr(x, 300, -290, 90, 140, 10); x.fill();
  if (driver) { x.save(); rr(x, 300, -290, 90, 140, 10); x.clip(); x.fillStyle = '#121218'; circle(x, 350, -205, 34); x.fill(); x.fillStyle = '#2457b8'; rr(x, 305, -175, 90, 40, 14); x.fill(); x.restore(); }
  // sign
  x.fillStyle = '#111'; rr(x, -420, -350, 380, 46, 8); x.fill(); text(x, sign, -230, -326, { size: 30, color: lights ? '#ffb340' : '#ff9c2a', fam: 'JetBrains Mono', weight: 800 });
  // wheels
  for (const wx of [-330, 300]) { x.fillStyle = '#121216'; circle(x, wx, -40, 62); x.fill(); x.fillStyle = '#5b5e66'; circle(x, wx, -40, 28); x.fill(); x.fillStyle = '#121216'; circle(x, wx, -40, 8); x.fill(); x.fillStyle = 'rgba(0,0,0,.25)'; x.beginPath(); x.arc(wx, -40, 74, Math.PI, 0); x.fill(); }
  // front light
  x.fillStyle = lights ? '#fff3c4' : '#fde9b0'; rr(x, 520, -110, 22, 40, 6); x.fill();
  if (mirror) { line(x, [540, -300, 590, -320, 600, -260], 8, '#1a1a1f'); x.fillStyle = '#1a1a1f'; rr(x, 585, -300, 34, 64, 10); x.fill(); }
  x.restore();
}
function bin(x, bx, by, s, col, lid = 0) {
  x.save(); x.translate(bx, by); x.scale(s, s);
  x.fillStyle = 'rgba(0,0,0,.3)'; ell(x, 0, 4, 70, 10); x.fill();
  x.fillStyle = col; x.beginPath(); x.moveTo(-55, -170); x.lineTo(55, -170); x.lineTo(48, 0); x.lineTo(-48, 0); x.closePath(); x.fill();
  x.fillStyle = 'rgba(0,0,0,.18)'; x.fillRect(-55, -170, 30, 170);
  x.save(); x.translate(-60, -172); x.rotate(-lid); x.fillStyle = col; rr(x, 0, -18, 122, 22, 6); x.fill(); x.fillStyle = 'rgba(0,0,0,.25)'; x.fillRect(0, -2, 122, 6); x.restore();
  x.fillStyle = '#111'; circle(x, -40, -2, 12); x.fill();
  x.restore();
}
function lampPost(x, lx, base, h, on = false) {
  line(x, [lx, base, lx, base - h, lx + 50, base - h - 10], 10, '#1e1d24');
  x.fillStyle = '#1e1d24'; rr(x, lx + 30, base - h - 14, 50, 18, 6); x.fill();
  if (on) { x.save(); x.globalCompositeOperation = 'screen'; x.fillStyle = rgrad(x, lx + 55, base - h, 5, 380, [[0, 'rgba(255,214,140,.75)'], [.4, 'rgba(255,190,110,.18)'], [1, 'rgba(255,190,110,0)']]); x.fillRect(lx - 400, base - h - 400, 900, 900); x.restore(); }
}
function bench(x, bx, by, s = 1) {
  x.save(); x.translate(bx, by); x.scale(s, s);
  x.fillStyle = 'rgba(0,0,0,.3)'; ell(x, 0, 4, 170, 12); x.fill();
  x.fillStyle = '#6b4128'; for (let i = 0; i < 3; i++) rr(x, -160, -150 + i * 26, 320, 16, 5), x.fill();
  rr(x, -170, -70, 340, 18, 5); x.fill();
  line(x, [-140, -60, -150, 0], 9, '#26262c'); line(x, [140, -60, 150, 0], 9, '#26262c'); line(x, [-150, -150, -150, -60], 9, '#26262c'); line(x, [150, -150, 150, -60], 9, '#26262c');
  x.restore();
}
function planeTree(x, cx, base, s, { leaf = '#3f6b3a', leaf2 = '#2c4f2c', trunk = '#4a3a30', light = null } = {}) {
  x.save(); x.translate(cx, base); x.scale(s, s);
  // trunk with branches
  x.fillStyle = trunk; x.beginPath(); x.moveTo(-70, 0); x.bezierCurveTo(-40, -150, -50, -300, -30, -420); x.lineTo(30, -420); x.bezierCurveTo(50, -300, 40, -150, 80, 0); x.closePath(); x.fill();
  line(x, [-20, -380, -170, -560], 34, trunk); line(x, [20, -380, 190, -580], 34, trunk); line(x, [0, -400, 10, -640], 30, trunk);
  x.fillStyle = 'rgba(255,255,255,.08)'; ell(x, 20, -200, 18, 120); x.fill();
  const r = rng(42);
  for (let i = 0; i < 40; i++) { x.fillStyle = r() < .5 ? leaf : leaf2; circle(x, (r() - .5) * 760, -560 - r() * 300 + Math.abs((r() - .5)) * 60, 70 + r() * 70); x.fill(); }
  if (light) { x.globalCompositeOperation = 'source-atop'; for (let i = 0; i < 18; i++) { x.fillStyle = light; circle(x, 80 + (r() - .3) * 400, -720 - r() * 160, 60 + r() * 40); x.fill(); } }
  x.restore();
}
function trafficLight(x, tx, base, state) {
  line(x, [tx, base, tx, base - 520], 14, '#1c1c22');
  x.fillStyle = '#1c1c22'; rr(x, tx - 50, base - 720, 100, 230, 18); x.fill();
  const cols = [['#ff4b3e', '#4a1512'], ['#ffc23a', '#4a3a10'], ['#4dff7a', '#123a1c']];
  cols.forEach(([on, off], i) => { const lit = (state === i); x.fillStyle = lit ? on : off; circle(x, tx, base - 685 + i * 70, 26); x.fill(); if (lit) { x.save(); x.globalCompositeOperation = 'screen'; x.fillStyle = rgrad(x, tx, base - 685 + i * 70, 5, 140, [[0, on + 'aa'], [1, on + '00']]); x.fillRect(tx - 140, base - 825 + i * 70, 280, 280); x.restore(); } });
}
function car(x, cx, base, s, col, facing = 1) {
  x.save(); x.translate(cx, base); x.scale(s * facing, s);
  x.fillStyle = 'rgba(0,0,0,.3)'; ell(x, 0, 4, 160, 12); x.fill();
  x.fillStyle = col; rr(x, -150, -95, 300, 70, 24); x.fill(); x.beginPath(); x.moveTo(-90, -95); x.lineTo(-50, -150); x.lineTo(60, -150); x.lineTo(100, -95); x.fill();
  x.fillStyle = '#2b3a55'; x.beginPath(); x.moveTo(-74, -98); x.lineTo(-44, -140); x.lineTo(0, -140); x.lineTo(0, -98); x.fill(); x.beginPath(); x.moveTo(10, -98); x.lineTo(10, -140); x.lineTo(54, -140); x.lineTo(84, -98); x.fill();
  for (const wx of [-90, 95]) { x.fillStyle = '#111'; circle(x, wx, -25, 30); x.fill(); x.fillStyle = '#666'; circle(x, wx, -25, 12); x.fill(); }
  x.fillStyle = '#fff2c0'; rr(x, 138, -80, 14, 20, 4); x.fill();
  x.restore();
}
function truck(x, cx, base, s, { col = '#e8e2d6', sign = 'VK DEVELOPMENTS', lights = false } = {}) {
  x.save(); x.translate(cx, base); x.scale(s, s);
  x.fillStyle = 'rgba(0,0,0,.35)'; ell(x, 0, 4, 330, 16); x.fill();
  x.fillStyle = col; rr(x, -320, -260, 430, 220, 14); x.fill();
  x.fillStyle = '#b3262e'; x.fillRect(-320, -150, 430, 26);
  text(x, sign, -105, -200, { size: 30, color: '#b3262e', weight: 900 });
  x.fillStyle = '#c9c2b4'; rr(x, 110, -200, 190, 160, 20); x.fill(); x.fillStyle = '#2b3a55'; rr(x, 170, -190, 110, 70, 10); x.fill();
  for (const wx of [-220, 210]) { x.fillStyle = '#111'; circle(x, wx, -30, 42); x.fill(); x.fillStyle = '#666'; circle(x, wx, -30, 16); x.fill(); }
  if (lights) { x.fillStyle = '#ffb000'; rr(x, 150, -214, 40, 16, 6); x.fill(); }
  x.restore();
}
function shed(x, sx, base, s, open = 0) {
  x.save(); x.translate(sx, base); x.scale(s, s);
  x.fillStyle = 'rgba(0,0,0,.3)'; ell(x, 0, 4, 200, 14); x.fill();
  x.fillStyle = '#8b5a3c'; x.fillRect(-180, -260, 360, 260);
  for (let i = -180; i < 180; i += 30) line(x, [i, -260, i, 0], 2, 'rgba(0,0,0,.2)');
  x.fillStyle = '#5a3a2a'; x.beginPath(); x.moveTo(-210, -250); x.lineTo(0, -370); x.lineTo(210, -250); x.fill();
  x.fillStyle = '#20140e'; x.fillRect(-60, -200, 120, 200);
  x.save(); x.translate(-60, -200); x.scale(1 - open * .85, 1); x.fillStyle = '#6e4630'; x.fillRect(0, 0, 120, 200); x.fillStyle = '#c9a400'; circle(x, 100, 100, 7); x.fill(); x.restore();
  if (open > .3) { x.fillStyle = '#d9b46a'; rr(x, -40, -90, 80, 90, 8); x.fill(); text(x, 'SEED', 0, -46, { size: 22, color: '#5a3a1a', weight: 900 }); }
  x.restore();
}

// ---------- whole sets ----------
function terminal(p = PAL.dawn) {
  return cached('terminal', x => {
    sky(x, p); L.sunDisc(x, 1500, 470, 70);
    skyline(x, 3, 700, p.far, 120, 340, { haze: 'rgba(240,170,130,.45)' });
    skyline(x, 7, 760, p.mid, 80, 260, { win: 'rgba(255,210,140,.35)', haze: 'rgba(220,140,110,.35)' });
    ground(x, p, 760);
    // terminal canopy
    x.fillStyle = '#2a1f2c'; x.fillRect(0, 300, W, 40); for (let i = 0; i < 6; i++) x.fillRect(80 + i * 360, 340, 22, 430);
    x.fillStyle = 'rgba(255,200,140,.12)'; x.fillRect(0, 336, W, 6);
    // lane markings
    for (let i = 0; i < 12; i++) { x.fillStyle = 'rgba(255,230,170,.35)'; x.beginPath(); x.moveTo(i * 200, 990); x.lineTo(i * 200 + 120, 990); x.lineTo(i * 200 + 110, 1004); x.lineTo(i * 200 - 10, 1004); x.fill(); }
    text(x, 'CENTRAL TERMINAL', 960, 320, { size: 26, color: '#f2c98a', weight: 800, track: 8 });
  });
}
function board() {
  return cached('board', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#1a2140'], [1, '#0d1128']]); x.fillRect(0, 0, W, H);
    x.strokeStyle = 'rgba(120,150,230,.10)'; x.lineWidth = 1.5;
    for (let i = 0; i < W; i += 60) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, H); x.stroke(); }
    for (let j = 0; j < H; j += 60) { x.beginPath(); x.moveTo(0, j); x.lineTo(W, j); x.stroke(); }
    x.fillStyle = rgrad(x, W / 2, H / 2, 100, 1100, [[0, 'rgba(90,120,220,.18)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, W, H);
  });
}
function street(p = PAL.day, key = 'street') {
  return cached(key, x => {
    sky(x, p); L.sunDisc(x, p.sun[0], p.sun[1], 60);
    skyline(x, 11, 620, p.far, 160, 380, { haze: 'rgba(250,200,140,.5)' });
    // row houses
    const r = rng(5);
    for (let i = 0; i < 7; i++) {
      const hx = i * 300 - 40, hh = 330 + r() * 120; const cols = ['#c66a4a', '#d89a5a', '#9a5a48', '#b77a52', '#c98a6a'];
      x.fillStyle = cols[i % 5]; x.fillRect(hx, 800 - hh, 290, hh);
      x.fillStyle = 'rgba(0,0,0,.15)'; x.fillRect(hx, 800 - hh, 290, 24);
      for (let k = 0; k < 2; k++) for (let j = 0; j < 3; j++) { x.fillStyle = '#3a3448'; rr(x, hx + 30 + j * 85, 800 - hh + 60 + k * 120, 56, 80, 6); x.fill(); x.fillStyle = 'rgba(255,220,160,.25)'; x.fillRect(hx + 34 + j * 85, 800 - hh + 64 + k * 120, 22, 72); }
      x.fillStyle = '#4a2e28'; rr(x, hx + 120, 650, 60, 150, 6); x.fill();
    }
    hazeBand(x, 500, 800, 'rgba(255,200,140,');
    x.fillStyle = '#b8a48c'; x.fillRect(0, 800, W, 70); x.fillStyle = '#8f7c66'; x.fillRect(0, 862, W, 12);
    x.fillStyle = vgrad(x, 874, H, [[0, '#5a4c44'], [1, '#2e2622']]); x.fillRect(0, 874, W, H - 874);
  });
}
function park(p = PAL.day, key = 'park', withTree = true) {
  const id = key; key = key.toLowerCase();
  return cached(id + (withTree ? ':T' : ':N'), x => {
    sky(x, p); if (key.includes('night')) stars(x, 160, 4);
    if (!key.includes('night')) L.sunDisc(x, p.sun[0], p.sun[1], key.includes('predawn') ? 50 : 60, key.includes('predawn') ? '255,200,150' : '255,244,214');
    else { x.fillStyle = '#f3efe0'; circle(x, 1560, 200, 46); x.fill(); x.fillStyle = PAL.night.sky[1][1]; circle(x, 1580, 190, 42); x.fill(); }
    skyline(x, 21, 640, p.far, 140, 360, { win: key.includes('night') ? 'rgba(255,210,120,.55)' : null, haze: key.includes('night') ? null : 'rgba(250,190,140,.45)' });
    for (let i = 0; i < 12; i++) tree(x, 60 + i * 170, 700, .8 + (i % 3) * .15, p.mid);
    hazeBand(x, 520, 720, p.light);
    x.fillStyle = vgrad(x, 690, H, [[0, key.includes('night') ? '#1d2a2a' : key.includes('predawn') ? '#3a3a40' : '#7c8a3e'], [1, key.includes('night') ? '#0a1010' : key.includes('predawn') ? '#1a1820' : '#3e4a1e']]); x.fillRect(0, 690, W, H - 690);
    // path
    x.fillStyle = key.includes('night') ? '#2a2a33' : key.includes('predawn') ? '#4a4048' : '#c9a873'; x.beginPath(); x.moveTo(0, 900); x.bezierCurveTo(600, 840, 1200, 860, W, 820); x.lineTo(W, 900); x.bezierCurveTo(1200, 940, 600, 930, 0, 1000); x.fill();
    if (withTree) planeTree(x, 1300, 860, 1, key.includes('night') ? { leaf: '#13221f', leaf2: '#0c1714', trunk: '#1a1614' } : key.includes('predawn') ? { leaf: '#2a3a34', leaf2: '#1e2a26', trunk: '#2a2224', light: 'rgba(255,170,130,.18)' } : { light: 'rgba(255,220,140,.25)' });
  });
}
function nightStop() {
  return cached('nightStop', x => {
    sky(x, PAL.night); stars(x, 180, 9);
    skyline(x, 31, 700, PAL.night.far, 160, 420, { win: 'rgba(255,200,110,.6)' });
    skyline(x, 37, 760, PAL.night.mid, 80, 240, { win: 'rgba(255,190,100,.45)' });
    x.fillStyle = vgrad(x, 760, H, [[0, '#1a1d30'], [1, '#07080f']]); x.fillRect(0, 760, W, H - 760);
    x.fillStyle = '#2a2c3a'; x.fillRect(0, 820, W, 20);
    // shelter
    x.fillStyle = 'rgba(160,190,230,.10)'; x.fillRect(300, 420, 560, 400); x.strokeStyle = '#3b3f52'; x.lineWidth = 10; x.strokeRect(300, 420, 560, 400);
    x.fillStyle = '#2b2f40'; x.fillRect(280, 400, 600, 30);
    x.fillStyle = '#f5c242'; rr(x, 330, 450, 150, 60, 8); x.fill(); text(x, 'BUS 12', 405, 481, { size: 30, color: '#1a1208', weight: 900 });
    // the rail (where the peanut goes)
    line(x, [900, 760, 900, 660, 1500, 660, 1500, 760], 12, '#5a5f72'); line(x, [1200, 660, 1200, 760], 10, '#4a4e60');
    x.fillStyle = 'rgba(255,255,255,.18)'; x.fillRect(900, 653, 600, 3);
    lampPost(x, 1640, 820, 520, true);
  });
}
function office() {
  return cached('office', x => {
    x.fillStyle = vgrad(x, 0, H, [[0, '#3a3046'], [1, '#1f1a28']]); x.fillRect(0, 0, W, H);
    // window with city
    x.save(); rr(x, 1100, 160, 700, 460, 12); x.clip(); sky(x, PAL.noon); skyline(x, 51, 640, '#b98658', 100, 300); x.restore();
    x.strokeStyle = '#2a2232'; x.lineWidth = 18; rr(x, 1100, 160, 700, 460, 12); x.stroke(); line(x, [1450, 160, 1450, 620], 12, '#2a2232');
    // screens
    for (let i = 0; i < 3; i++) { x.fillStyle = '#14121a'; rr(x, 140 + i * 280, 300, 250, 170, 10); x.fill(); x.fillStyle = '#1f3b5a'; rr(x, 152 + i * 280, 312, 226, 146, 6); x.fill(); for (let k = 0; k < 5; k++) { x.fillStyle = ['#5fd16a', '#f5c242', '#ff6b5a'][(i + k) % 3]; x.fillRect(170 + i * 280, 330 + k * 24, 60 + ((i * 7 + k * 13) % 110), 10); } }
    x.fillStyle = '#5a4030'; x.fillRect(0, 720, W, 40); x.fillStyle = '#3a2a20'; x.fillRect(0, 760, W, 320);
    text(x, 'DISPATCH', 520, 230, { size: 40, color: 'rgba(255,220,170,.5)', weight: 900, track: 10 });
  });
}

module.exports = { PAL, cached, sky, stars, skyline, ground, tree, hazeBand, bus, bin, lampPost, bench, planeTree, trafficLight, car, truck, shed, terminal, board, street, park, nightStop, office };
