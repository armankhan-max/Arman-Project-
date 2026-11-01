// Scenes 1:51 – 6:12 (afternoon → the roost → the tree → reality check → outro)
const L = require('./lib');
const C = require('./chars');
const S = require('./sets');
const { at, end, END } = require('./timing');
const { W, H, E, tw, inv, clamp, lerp, rr, circle, ell, line, text, popText, chip, bubble, check, cross, rgrad, vgrad, canvas, rng, hash } = L;
const gold = '#f5b83d';
const FACT = (ctx, t, t0, s, x, y, until) => chip(ctx, t, t0, 'REAL FACT  •  ' + s, x, y, { size: 30, bg: '#3fc1c9', color: '#06262a', until });
const blurCache = {};
function blurred(key, src, px) { if (!blurCache[key]) { const [c, x] = canvas(); x.filter = `blur(${px}px)`; x.drawImage(src, -40, -40, W + 80, H + 80); blurCache[key] = c; } return blurCache[key]; }

// distant flock: swirling chevrons
function flock(ctx, t, n, cx, cy, rx, ry, seed = 1, col = '#120c18', size = 1) {
  const r = rng(seed); ctx.save(); ctx.strokeStyle = col; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const ph = r() * 6.28, sp = .15 + r() * .35, rad = .3 + r() * .7, sz = (5 + r() * 9) * size;
    const a = ph + t * sp * (r() < .5 ? 1 : -1);
    const x = cx + Math.cos(a) * rx * rad + Math.sin(t * .7 + ph) * 20, y = cy + Math.sin(a * 1.3) * ry * rad;
    const f = Math.sin(t * 12 + ph) * .6;
    ctx.lineWidth = sz * .35; ctx.beginPath(); ctx.moveTo(x - sz, y - sz * f); ctx.quadraticCurveTo(x - sz * .4, y - sz * .3, x, y); ctx.quadraticCurveTo(x + sz * .4, y - sz * .3, x + sz, y - sz * f); ctx.stroke();
  }
  ctx.restore();
}
function phone(ctx, x, y, s, t, msg, from = 'DEV (DISPATCH)') {
  ctx.save(); ctx.translate(x + Math.sin(t * 60) * 3 * (Math.sin(t * 4) > 0 ? 1 : 0), y); ctx.scale(s, s);
  ctx.fillStyle = '#0d0d12'; rr(ctx, -170, -320, 340, 640, 50); ctx.fill();
  ctx.fillStyle = vgrad(ctx, -300, 300, [[0, '#26315a'], [1, '#121830']]); rr(ctx, -150, -295, 300, 590, 34); ctx.fill();
  text(ctx, '5:41', 0, -220, { size: 64, color: '#fff', weight: 700 });
  ctx.fillStyle = 'rgba(255,255,255,.92)'; rr(ctx, -140, -120, 280, 200, 24); ctx.fill();
  text(ctx, from, -120, -90, { size: 20, color: '#2f9e4f', align: 'left', weight: 900 });
  const words = msg.split('|'); words.forEach((w, i) => text(ctx, w, -120, -40 + i * 40, { size: 25, color: '#111', align: 'left', weight: 700 }));
  ctx.restore();
}
function stamp(ctx, t, t0, s, x, y, col = '#ff4b3e', size = 70, rot = -.12) {
  if (t < t0) return; const k = E.out(inv(t0, t0 + .22, t));
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(2.2 - 1.2 * k, 2.2 - 1.2 * k); ctx.globalAlpha = clamp(k * 1.2);
  ctx.font = L.font(size, 900); const w = ctx.measureText(s).width + 60;
  ctx.strokeStyle = col; ctx.lineWidth = 10; rr(ctx, -w / 2, -size * .8, w, size * 1.6, 16); ctx.stroke();
  text(ctx, s, 0, 4, { size, color: col, weight: 900 }); ctx.restore();
}
function clockFace(ctx, x, y, r, hh, mm) {
  ctx.fillStyle = '#fbf6ea'; circle(ctx, x, y, r); ctx.fill(); ctx.strokeStyle = '#222'; ctx.lineWidth = r * .08; ctx.stroke();
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; line(ctx, [x + Math.cos(a) * r * .8, y + Math.sin(a) * r * .8, x + Math.cos(a) * r * .9, y + Math.sin(a) * r * .9], r * .05, '#222'); }
  const ah = ((hh % 12) + mm / 60) / 12 * Math.PI * 2 - Math.PI / 2, am = mm / 60 * Math.PI * 2 - Math.PI / 2;
  line(ctx, [x, y, x + Math.cos(ah) * r * .5, y + Math.sin(ah) * r * .5], r * .09, '#222'); line(ctx, [x, y, x + Math.cos(am) * r * .75, y + Math.sin(am) * r * .75], r * .06, '#c33');
}

const scenes = [];
const add = (s, e, cam, draw, extra = {}) => scenes.push({ s, e, cam, draw, ...extra });

// ---------- N: 1 PM puzzle + subway map
const t1 = at('1', 110), t2014 = at('in 2014'), t8s = at('8 steps', 117), tSub = at('today a crow solves'), tBefore = at('before you do'), t3 = at('3', 120);
add(t1, t3, [1.02, 1.08, 960, 540], (ctx, t) => {
  ctx.drawImage(S.board(), 0, 0);
  if (t < tSub) {
    popText(ctx, t, t2014, '2014 STUDY', 960, 200, { size: 60, color: '#9fb4ff' });
    // 8-step puzzle chain
    const n = Math.floor(clamp((t - t2014 - .6) / 2.6) * 8.99);
    for (let i = 0; i < 8; i++) {
      const x = 330 + i * 180, y = 520; const lit = i < n;
      ctx.fillStyle = lit ? gold : '#2a335e'; rr(ctx, x - 70, y - 70, 140, 140, 24); ctx.fill();
      text(ctx, String(i + 1), x, y + 4, { size: 64, color: lit ? '#1a1208' : '#5a6aa0' });
      if (i < 7) line(ctx, [x + 76, y, x + 104, y], 6, lit ? gold : '#2a335e');
    }
    if (n > 0) C.crow(ctx, 330 + Math.min(7, n - 1) * 180, 440, .9, { t, facing: 1, rim: 'rgba(120,180,255,.8)' });
    popText(ctx, t, t8s, '8 STEPS. IN ORDER.', 960, 760, { size: 64, color: '#fff' });
    FACT(ctx, t, t2014 + .3, 'a crow solved an 8-step puzzle', 960, 880);
  } else {
    // subway map race
    ctx.save(); ctx.translate(960, 500); ctx.fillStyle = '#f4efe2'; rr(ctx, -720, -330, 1440, 660, 24); ctx.fill();
    const lines = [['#e8483f', [-640, 200, -300, 200, -100, 0, 300, 0, 640, -240]], ['#2a8fd6', [-640, -200, -200, -200, 0, 0, 200, 220, 640, 220]], ['#2fae5a', [-500, 280, -500, -260]], ['#f2a33a', [420, -280, 420, 280]]];
    lines.forEach(([c, p]) => line(ctx, p, 18, c));
    const path = [[-640, 200], [-300, 200], [-100, 0], [300, 0], [420, -100], [640, -240]];
    const prog = (k, pts) => { const segs = pts.length - 1; const f = clamp(k) * segs; const i = Math.min(segs - 1, Math.floor(f)); const u = f - i; return [lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u)]; };
    const kc = E.inOut(inv(tSub + .3, tBefore + .4, t)), kl = E.inOut(inv(tSub + .3, tBefore + 3.5, t));
    const [lx, ly] = prog(kl, path); ctx.fillStyle = '#2457b8'; circle(ctx, lx, ly, 22); ctx.fill(); text(ctx, 'YOU', lx, ly - 46, { size: 28, color: '#2457b8' });
    const [qx, qy] = prog(kc, path); C.crow(ctx, qx, qy + 10, .7, { t, facing: 1, fly: t * 16, rim: null });
    ctx.restore();
    if (kc >= 1) chip(ctx, t, tBefore + .4, 'CROW: SOLVED FIRST', 960, 160, { size: 46, bg: gold });
  }
});

// ---------- O: 3 PM the crows count every bus
const tCount = at('the crows count'), tDelay = at('every delay'), tRoute = at('your route'), tLate = at('late 11'), tKnow = at('they know of course'), t5 = at('5', 130);
add(t3, t5, [1.03, 1.1, 960, 540], (ctx, t) => {
  ctx.drawImage(S.terminal(), 0, 0);
  ctx.fillStyle = 'rgba(255,200,120,.12)'; ctx.fillRect(0, 0, W, H);
  S.bus(ctx, 520, 960, .55, { sign: 'ROUTE 12' }); S.bus(ctx, 1250, 960, .55, { sign: 'ROUTE 7', col: '#e8483f' });
  // crow tally board on the canopy
  ctx.save(); ctx.translate(960, 290); ctx.fillStyle = '#1b1b24'; rr(ctx, -360, -120, 720, 240, 18); ctx.fill(); ctx.strokeStyle = gold; ctx.lineWidth = 4; rr(ctx, -360, -120, 720, 240, 18); ctx.stroke();
  text(ctx, 'CROW TRANSIT AUTHORITY', 0, -80, { size: 30, color: gold, track: 3 });
  const n = Math.floor(clamp((t - tCount) / 4) * 23);
  for (let i = 0; i < n; i++) { const g = Math.floor(i / 5), k = i % 5; if (k < 4) line(ctx, [-300 + g * 110 + k * 18, -30, -300 + g * 110 + k * 18, 40], 6, '#fff'); else line(ctx, [-310 + g * 110, 30, -230 + g * 110, -20], 6, '#ff6b5a'); }
  ctx.restore();
  for (let i = 0; i < 5; i++) C.crow(ctx, 640 + i * 160, 172, .55, { t: t + i, facing: i % 2 ? -1 : 1, tilt: .3, rim: null });
  chip(ctx, t, tDelay, 'EVERY BUS', 560, 520, { size: 36, bg: '#fff', color: '#222', until: tRoute });
  chip(ctx, t, tDelay + .5, 'EVERY DELAY', 1340, 520, { size: 36, bg: '#ff6b5a', color: '#fff', until: tRoute });
  if (t > tRoute) {
    const k = E.back(inv(tRoute, tRoute + .4, t)); ctx.save(); ctx.translate(960, 600); ctx.scale(k, k);
    ctx.fillStyle = '#fbf6ea'; rr(ctx, -380, -150, 760, 300, 24); ctx.fill();
    text(ctx, 'DRIVER: LENA  •  ROUTE 12', 0, -90, { size: 34, color: '#555' });
    if (t > tLate) { text(ctx, 'LATE  11×', 0, 0, { size: 100, color: '#e8483f' }); text(ctx, 'this month', 0, 90, { size: 36, color: '#555', weight: 700 }); }
    ctx.restore();
  }
  if (t > tKnow) C.person(ctx, 1640, 1010, 1, { who: 'lena', t, mood: 'worried', look: -1, facing: -1, drivercap: true });
});

// ---------- P: 5 PM news over the shoulder
const tNews = at('a crow reads the news'), tSigh = at('then it sighs'), t6 = at('6', 138);
add(t5, t6, [1.05, 1.12, 960, 560], (ctx, t) => {
  ctx.drawImage(blurred('termP', S.terminal(), 20), 0, 0); ctx.fillStyle = 'rgba(255,140,60,.15)'; ctx.fillRect(0, 0, W, H);
  // bus seat
  ctx.fillStyle = '#2a4a8a'; rr(ctx, 560, 560, 520, 520, 40); ctx.fill(); ctx.fillStyle = '#1e3a70'; rr(ctx, 600, 600, 440, 60, 20); ctx.fill();
  C.person(ctx, 820, 1180, 1.6, { who: 'people', t, mood: 'neutral', arms: 'read', holding: 'news', facing: 1, look: 1 });
  const sigh = t > tSigh;
  C.crow(ctx, 640, 600 + (sigh ? Math.sin(clamp((t - tSigh) * 2, 0, 1) * Math.PI) * 18 : 0), 1.5, { t, facing: 1, tilt: sigh ? .35 : .2, lid: 1 });
  if (sigh) { popText(ctx, t, tSigh + .2, '*sigh*', 560, 400, { size: 64, color: '#fff', stroke: '#222', sw: 10, rot: -.08 }); }
  chip(ctx, t, tNews + .5, 'reading over your shoulder', 1400, 300, { size: 34, bg: '#fff', color: '#222', until: tSigh });
});

// ---------- Q: 6 PM rush hour traffic light
const tRush = at('rush hour'), tShout = at('a crow on a traffic'), tGreen = at('the next green'), tHonk = at('nobody honks'), tSunset = at('sunset');
add(t6, tSunset, [1.03, 1.1, 960, 520], (ctx, t) => {
  ctx.drawImage(S.street(S.PAL.sunset, 'streetSunset'), 0, 0);
  const green = t > tGreen + .2;
  S.trafficLight(ctx, 1500, 900, green ? 2 : 0);
  C.crow(ctx, 1500, 175, .9, { t, facing: -1, talk: t > tGreen - .2 && t < tGreen + .8, beak: t > tGreen && t < tGreen + .8 ? .8 : 0 });
  const go = green ? E.in(clamp((t - tGreen - .5) / 2)) * 900 : 0;
  S.car(ctx, 300 + go, 960, 1, '#e8483f'); S.car(ctx, -100 + go * .9, 960, 1, '#2a8fd6'); S.car(ctx, 700 + go * 1.1, 960, 1, '#f2c14e');
  if (t > tGreen - .1 && t < tGreen + 1.2) { popText(ctx, t, tGreen - .1, 'GREEN!', 1240, 200, { size: 100, color: '#4dff7a', stroke: '#0a2a10', sw: 14, rot: -.1 }); }
  popText(ctx, t, tRush, 'RUSH HOUR', 700, 300, { size: 80, color: '#fff', stroke: '#2a1020', sw: 12, until: tShout });
  chip(ctx, t, tHonk, 'NOBODY HONKS', 700, 300, { size: 52, bg: gold });
});

// ---------- R: sunset roost → town hall
const tWinter = at('winter roosts'), tTonight = at('tonight the roost'), tHall = at('a town hall'), tWorld = at('and around the world');
add(tSunset, tWorld, [1.0, 1.14, 1200, 500], (ctx, t) => {
  ctx.drawImage(S.park(S.PAL.sunset, 'parkSunset', false), 0, 0);
  L.rays(ctx, 1300, 640, t, { col: 'rgba(255,150,100,', dir: -Math.PI / 2 - .3, spread: 2.6, a: .15, n: 12 });
  S.planeTree(ctx, 1200, 920, 1.05, { leaf: '#2a1830', leaf2: '#1e1026', trunk: '#1a0f1e' });
  const n = Math.floor(lerp(40, 260, inv(tSunset, tWinter + 2, t)));
  flock(ctx, t, n, 1200, 300, 700, 220, 7, '#120a16', 1.2);
  // perched silhouettes filling the tree
  const r = rng(77); const filled = inv(tWinter, tTonight + 2, t);
  for (let i = 0; i < 90 * filled; i++) { ctx.fillStyle = '#0c060e'; const x = 1200 + (r() - .5) * 760, y = 340 + r() * 200; ell(ctx, x, y, 10, 7); ctx.fill(); circle(ctx, x + 7, y - 6, 5); ctx.fill(); }
  FACT(ctx, t, tWinter, 'winter roosts can hold thousands of crows', 960, 900 - 40, tTonight);
  if (t > tHall) {
    // gavel crow on a branch + speech bubble
    C.crow(ctx, 1200, 520, 1.1, { t, facing: -1, talk: true, rim: 'rgba(255,150,100,.9)' });
    chip(ctx, t, tHall, 'TOWN HALL  •  IN SESSION', 1200, 200, { size: 44, bg: gold });
  }
});

// ---------- S: around the world — every city, rooftop, wire (3 fast panels)
const tCity = at('every city'), tRoof = at('every rooftop'), tWire = at('every wire'), tNotice = at('then you notice');
add(tWorld, tNotice, [1.0, 1.05, 960, 540], (ctx, t) => {
  ctx.fillStyle = '#0a0d22'; ctx.fillRect(0, 0, W, H);
  if (t < tCity) {
    // stylised globe with lit roost dots
    const R = 330; ctx.fillStyle = rgrad(ctx, 960, 520, 50, R, [[0, '#1f3a8a'], [1, '#0c1840']]); circle(ctx, 960, 520, R); ctx.fill();
    ctx.save(); circle(ctx, 960, 520, R); ctx.clip(); const r = rng(3);
    for (let i = 0; i < 9; i++) { ctx.fillStyle = '#2b5a3a'; ell(ctx, 960 + ((r() * 2 - 1) * R + t * 40) % R, 520 + (r() * 2 - 1) * R * .7, 60 + r() * 80, 40 + r() * 60, r()); ctx.fill(); }
    for (let i = 0; i < 40; i++) { const k = clamp((t - tWorld) * 3 - i * .05); if (k <= 0) continue; ctx.fillStyle = `rgba(245,184,61,${k})`; circle(ctx, 960 + (r() * 2 - 1) * R * .85, 520 + (r() * 2 - 1) * R * .7, 6); ctx.fill(); }
    ctx.restore();
    popText(ctx, t, tWorld + .2, 'AROUND THE WORLD', 960, 140 + 30, { size: 60, color: '#fff' });
  } else {
    const panels = [[tCity, 'EVERY CITY'], [tRoof, 'EVERY ROOFTOP'], [tWire, 'EVERY WIRE']];
    panels.forEach(([pt, label], i) => {
      if (t < pt) return; const k = E.out(inv(pt, pt + .3, t)); const x0 = i * 640;
      ctx.save(); ctx.beginPath(); ctx.rect(x0 + 4, 0, 632, H); ctx.clip(); ctx.translate(0, (1 - k) * 300); ctx.globalAlpha = k;
      ctx.drawImage(S.park(S.PAL.night, 'parkNight', false), x0 - 640 + i * 200, 0);
      if (i === 0) S.skyline(ctx, 91, 760, '#141a3a', 200, 500, { win: 'rgba(255,200,110,.5)', wmin: 60, wmax: 120 });
      if (i === 1) { ctx.fillStyle = '#0d1128'; ctx.beginPath(); ctx.moveTo(x0, 700); ctx.lineTo(x0 + 320, 520); ctx.lineTo(x0 + 640, 700); ctx.lineTo(x0 + 640, H); ctx.lineTo(x0, H); ctx.fill(); for (let j = 0; j < 7; j++) C.crow(ctx, x0 + 100 + j * 70, 700 - (j < 4 ? j : 6 - j) * 52 - 40, .5, { t: t + j, facing: j % 2 ? 1 : -1, eyeGlow: '#ffe28a', rim: null }); }
      if (i === 2) { ctx.strokeStyle = '#05060f'; ctx.lineWidth = 4; for (let w = 0; w < 3; w++) { ctx.beginPath(); ctx.moveTo(x0, 360 + w * 120); ctx.quadraticCurveTo(x0 + 320, 420 + w * 120, x0 + 640, 360 + w * 120); ctx.stroke(); for (let j = 0; j < 8; j++) C.crow(ctx, x0 + 40 + j * 78, 360 + w * 120 + Math.sin((j * 78 + 40) / 640 * Math.PI) * 30, .38, { t: t + j + w, facing: (j + w) % 2 ? 1 : -1, rim: null, eyeGlow: '#ffe28a' }); } }
      if (i === 0) for (let j = 0; j < 12; j++) C.crow(ctx, x0 + 40 + j * 52, 520 + (j % 3) * 60, .35, { t: t + j, rim: null, eyeGlow: '#ffe28a' });
      text(ctx, label, x0 + 320, 200, { size: 54, color: gold, stroke: '#000', sw: 10 });
      ctx.restore();
    });
  }
});

// ---------- T: the crows are watching faces
const tFaces = at('the crows are watching'), tYourFace = at('your face too'), tSeattle = at('researchers in seattle');
add(tNotice, tSeattle, [1.0, 1.25, 960, 520], (ctx, t) => {
  ctx.drawImage(S.nightStop(), 0, 0); ctx.fillStyle = 'rgba(5,6,20,.55)'; ctx.fillRect(0, 0, W, H);
  const r = rng(12);
  for (let i = 0; i < 26; i++) { const x = r() * W, y = 140 + r() * 520; const op = clamp((t - tNotice - i * .08) * 2); const bl = (t * .7 + i) % 3.3 < .1 ? .1 : 1; ctx.fillStyle = `rgba(255,226,138,${op})`; ell(ctx, x, y, 5, 5 * bl); ctx.fill(); ell(ctx, x + 16, y, 5, 5 * bl); ctx.fill(); }
  C.person(ctx, 960, 1060, 1.4, { who: 'lena', t, mood: t > tYourFace ? 'worried' : 'neutral', look: Math.sin(t * 1.5), drivercap: true, rim: 'rgba(150,180,255,.7)' });
  if (t > tFaces) {
    // face-scan brackets
    const k = E.out(inv(tYourFace, tYourFace + .4, t)), cx = 970, cy = 1060 - 1.4 * 283, s = lerp(260, 130, k);
    ctx.strokeStyle = t > tYourFace ? '#ff5a4f' : 'rgba(255,226,138,.8)'; ctx.lineWidth = 6;
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { ctx.beginPath(); ctx.moveTo(cx + sx * s, cy + sy * (s - 40)); ctx.lineTo(cx + sx * s, cy + sy * s); ctx.lineTo(cx + sx * (s - 40), cy + sy * s); ctx.stroke(); }
    if (t > tYourFace) chip(ctx, t, tYourFace + .2, 'FACE SAVED', cx, cy - s - 50, { size: 34, bg: '#ff5a4f', color: '#fff' });
  }
});

// ---------- U: Seattle mask study (sepia flashback)
const tMask = at('wore a mask'), tYears = at('years later'), tNever = at('even crows that were never'), tGrudge = at('they learned the grudge'), tNF = at('a crow never forgets');
add(tSeattle, tNF, [1.03, 1.1, 960, 540], (ctx, t) => {
  ctx.save(); ctx.filter = 'sepia(0.85) contrast(1.05)';
  ctx.drawImage(S.park(S.PAL.day, 'parkNoTree', false), 0, 0); ctx.restore();
  ctx.fillStyle = 'rgba(80,50,20,.25)'; ctx.fillRect(0, 0, W, H);
  const later = t > tYears;
  C.person(ctx, 820, 950, 1.25, { who: 'researcher', t, arms: later ? 'shrug' : 'hold', rim: 'rgba(255,230,180,.6)' });
  if (!later) {
    ctx.strokeStyle = '#3a2a1a'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(1080, 600, 80, 0, Math.PI * 2); ctx.stroke(); line(ctx, [1020, 660, 900, 800], 8, '#5a3a20');
    chip(ctx, t, tMask + .2, 'THE "DANGEROUS" MASK', 820, 280, { size: 36, bg: '#f2e2c0', color: '#3a2a1a' });
    FACT(ctx, t, tSeattle + .4, 'University of Washington mask study', 960, 900 - 30);
  } else {
    // crows scolding
    const r = rng(5);
    for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 1.2 + Math.PI * 1.9, rad = 360 + r() * 80; const x = 820 + Math.cos(a) * rad, y = 560 + Math.sin(a) * rad * .5 - 80; C.crow(ctx, x, y, .8, { t: t + i, facing: x > 820 ? -1 : 1, fly: t * 14 + i, beak: .7, rim: null }); }
    popText(ctx, t, tYears, 'YEARS LATER', 960, 200, { size: 64, color: '#fff', stroke: '#3a2a1a', sw: 10 });
    for (let i = 0; i < 4; i++) popText(ctx, t, tYears + .4 + i * .3, 'CAW!', 420 + i * 360, 330 + (i % 2) * 70, { size: 56, color: '#ff6b5a', stroke: '#2a1a0a', sw: 8, rot: (i % 2 ? .12 : -.12) });
    if (t > tNever) chip(ctx, t, tNever, 'even crows that were never there', 960, 860, { size: 36, bg: '#fff', color: '#222', until: tGrudge });
    if (t > tGrudge) chip(ctx, t, tGrudge, 'THEY LEARNED THE GRUDGE', 960, 860, { size: 44, bg: '#ff5a4f', color: '#fff' });
  }
  // film look: scratches
  ctx.save(); ctx.globalAlpha = .25; for (let i = 0; i < 3; i++) { const x = hash(Math.floor(t * 12) + i) * W; line(ctx, [x, 0, x + 4, H], 1.5, '#fff8e0'); } ctx.restore();
});

// ---------- V: a crow never forgets a face — the files
const tWords = at('and now it has the words'), tMan = at('the man who threw'), tName = at('they know his name'), tKid = at('the kid who chased'), tAnon = at('is anyone anonymous'), tNo = at('no not one'), tSafe = at("you're safe");
add(tNF, tSafe, [1.02, 1.1, 960, 540], (ctx, t) => {
  ctx.drawImage(S.board(), 0, 0);
  if (t < tMan) {
    popText(ctx, t, tNF, 'A CROW NEVER FORGETS', 960, 420, { size: 92, color: '#fff' });
    popText(ctx, t, tNF + .9, 'A FACE.', 960, 540, { size: 120, color: gold });
    popText(ctx, t, tWords, '...and now it has the WORDS.', 960, 700, { size: 54, color: '#7fe0ff', weight: 700 });
  } else {
    const card = (x, tt, title, who, extra) => {
      if (t < tt) return; const k = E.back(inv(tt, tt + .4, t)); ctx.save(); ctx.translate(x, 500); ctx.rotate((x > 960 ? .04 : -.04)); ctx.scale(k, k);
      ctx.fillStyle = '#f4ecd8'; rr(ctx, -300, -330, 600, 660, 18); ctx.fill(); ctx.fillStyle = '#d7c9a6'; ctx.fillRect(-300, -330, 600, 70);
      text(ctx, title, 0, -295, { size: 34, color: '#3a2a1a' });
      ctx.save(); rr(ctx, -200, -240, 400, 330, 10); ctx.clip(); ctx.fillStyle = '#9aa3b5'; ctx.fillRect(-200, -240, 400, 330); C.person(ctx, 0, 380, 1.25, { who, t, mood: 'worried', shadow: false, rim: null }); ctx.restore();
      extra(ctx); ctx.restore();
    };
    card(560, tMan, 'CROW FILE #2015', 'man', c => { text(c, 'THREW A STONE • 2015', 0, 140, { size: 32, color: '#b3262e' }); if (t > tName) text(c, 'NAME: GARY P.', 0, 210, { size: 44, color: '#222', fam: 'JetBrains Mono' }); });
    card(1360, tKid, 'CROW FILE #0412', 'kid', c => { text(c, 'SCOOTER CHASE', 0, 140, { size: 32, color: '#b3262e' }); text(c, 'NAME: KNOWN', 0, 210, { size: 44, color: '#222', fam: 'JetBrains Mono' }); });
    if (t > tAnon) { ctx.fillStyle = `rgba(10,13,34,${.75 * clamp((t - tAnon) * 3)})`; ctx.fillRect(0, 0, W, H); popText(ctx, t, tAnon, 'IS ANYONE ANONYMOUS NOW?', 960, 430, { size: 72, color: '#fff' }); stamp(ctx, t, tNo, 'NO.', 960, 620, '#ff4b3e', 110); }
  }
}, { shake: [[tNo, .3, 12]] });

// ---------- W: bus stop at night — the peanut ritual
const tHabit = at('every night you leave'), tTap = at('you tap it twice'), tTapA = at('tap', tTap + .5), tTapB = at('tap', tTapA + .1), tComes = at('one crow always comes'), tPip = at('pip', tComes), tNotch = at('a notch in his tail'), tLands = at('tonight he lands');
add(tSafe, tLands, [1.03, 1.12, 1150, 640], (ctx, t) => {
  ctx.drawImage(S.nightStop(), 0, 0);
  const placing = t > tHabit && t < tTap + 1.6;
  C.person(ctx, 1040, 960, 1.15, { who: 'lena', t, mood: t > tPip ? 'smile' : 'neutral', arms: placing ? 'tap' : 'down', facing: 1, look: .5, drivercap: true, rim: 'rgba(255,200,130,.85)', rimDx: 5 });
  if (t > tHabit + .6) { ctx.fillStyle = '#d9a35b'; ell(ctx, 1200, 650, 13, 8, .3); ctx.fill(); }
  for (const tt of [tTapA, tTapB]) if (t > tt && t < tt + .6) { popText(ctx, t, tt, 'TAP', 1220 + (tt === tTapB ? 90 : 0), 560 - (tt === tTapB ? 30 : 0), { size: 56, color: gold, stroke: '#000', sw: 8 }); ctx.save(); ctx.strokeStyle = `rgba(245,184,61,${1 - (t - tt) / .6})`; ctx.lineWidth = 4; circle(ctx, 1200, 650, 20 + (t - tt) * 120); ctx.stroke(); ctx.restore(); }
  if (t > tComes) {
    const k = inv(tComes, tComes + 1.2, t); const x = lerp(1950, 1330, E.out(k)), y = lerp(260, 652, E.inOut(k));
    C.crow(ctx, x, y, .85, { t, facing: -1, fly: k < 1 ? t * 14 : undefined, notch: true, rim: 'rgba(255,200,130,.9)', tilt: k >= 1 ? Math.sin(t * 1.3) * .15 : 0 });
    if (t > tPip) chip(ctx, t, tPip, 'PIP', 1340, 470, { size: 50, bg: gold });
    if (t > tNotch) { const p = .5 + .5 * Math.sin(t * 8); ctx.strokeStyle = `rgba(245,184,61,${.6 + .4 * p})`; ctx.lineWidth = 5; circle(ctx, 1330 + 74 * .85, 652 - 14, 36 + p * 6); ctx.stroke(); chip(ctx, t, tNotch + .3, 'notch in his tail', 1500, 760, { size: 30, bg: '#fff', color: '#222' }); }
  }
});

// ---------- X: Pip says thank you; Rosa laughs
const tFed = at('you fed us'), tSo = at('so thank you'), tRosa = at('rosa the old'), tTold = at('told you they'), tSmile = at('you smile');
add(tLands, tSmile, [1.06, 1.14, 1100, 600], (ctx, t) => {
  ctx.drawImage(S.nightStop(), 0, 0);
  S.bench(ctx, 520, 960, 1.05);
  C.person(ctx, 520, 960, 1.05, { who: 'rosa', t, pose: 'sit', mood: t > tRosa ? 'laugh' : 'smile', look: 1, rim: 'rgba(255,200,130,.6)', rimDx: 5, talk: t > tTold });
  C.person(ctx, 1040, 960, 1.15, { who: 'lena', t, mood: t > tFed ? 'surprised' : 'neutral', look: .6, drivercap: true, rim: 'rgba(255,200,130,.85)', rimDx: 5 });
  C.crow(ctx, 1330, 652, .85, { t, facing: -1, notch: true, tilt: -.3, talk: (t > tFed && t < tRosa - .3), rim: 'rgba(255,200,130,.9)' });
  bubble(ctx, t, tFed, 'You fed us before we could say thank you.', 1450, 380, 1360, 590, { size: 38, maxW: 520, until: tSo - .05 });
  bubble(ctx, t, tSo, 'So... thank you.', 1450, 420, 1360, 590, { size: 50, until: tRosa + 1 });
  chip(ctx, t, tRosa, 'ROSA  •  PARK KEEPER', 520, 560, { size: 30, bg: '#7a4fa8', color: '#fff', until: tTold });
  bubble(ctx, t, tTold, 'Told you they were watching, Lena!', 560, 420, 560, 600, { size: 38, maxW: 480 });
});

// ---------- Y: Lena smiles (close-up)
const tWhat = at('what do you even'), tQuiet = at('then pip goes');
add(tSmile, tQuiet, [1.02, 1.1, 960, 520], (ctx, t) => {
  ctx.drawImage(blurred('stopY', S.nightStop(), 22), 0, 0);
  C.person(ctx, 820, 1650, 3.2, { who: 'lena', t, mood: 'smile', look: 1, drivercap: true, shadow: false, rim: 'rgba(255,200,130,.85)', rimDx: 7 });
  C.crow(ctx, 1450, 900, 2.2, { t, facing: -1, notch: true, tilt: -.2 });
  popText(ctx, t, at('a bird', tSmile), 'A BIRD.', 1400, 300, { size: 70, color: '#fff', stroke: '#000', sw: 10 });
  popText(ctx, t, at('just thanked'), 'JUST THANKED YOU.', 1400, 390, { size: 56, color: gold, stroke: '#000', sw: 10 });
  popText(ctx, t, tWhat, 'What do you even say to that?', 1360, 500, { size: 38, color: '#fff', weight: 700 });
});

// ---------- Z: the plane tree + Victor's plan
const tTree = at('the big plane tree'), tThousands = at('thousands of us'), tDawn = at('at dawn a developer'), tVictor = at('named victor'), tCut = at('to cut it down'), tParking = at('a parking lot'), tPlan = at('the crows have a plan');
add(tQuiet, tPlan, [1.02, 1.12, 1300, 520], (ctx, t) => {
  if (t < tDawn) {
    ctx.drawImage(S.park(S.PAL.night, 'parkNight'), 0, 0);
    const r = rng(9); const k = inv(tThousands, tThousands + 2, t);
    for (let i = 0; i < 160 * k; i++) { const x = 1300 + (r() - .5) * 760, y = 230 + r() * 300; const bl = (t + i * .37) % 3 < .08 ? .1 : 1; ctx.fillStyle = '#ffe28a'; ell(ctx, x, y, 3, 3 * bl); ctx.fill(); }
    C.crow(ctx, 470, 900, 1.3, { t, facing: 1, notch: true, talk: t > tTree && t < tThousands + 1.5, tilt: -.25, rim: 'rgba(150,180,255,.8)' });
    chip(ctx, t, tTree + .3, 'THE BIG PLANE TREE', 1300, 160, { size: 44, bg: gold });
    popText(ctx, t, tThousands, 'THOUSANDS SLEEP HERE', 1300, 920 - 60, { size: 54, color: '#fff', stroke: '#000', sw: 10 });
  } else {
    // blueprint
    ctx.fillStyle = '#123a6e'; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(255,255,255,.12)'; ctx.lineWidth = 1; for (let i = 0; i < W; i += 40) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, H); ctx.stroke(); } for (let j = 0; j < H; j += 40) { ctx.beginPath(); ctx.moveTo(0, j); ctx.lineTo(W, j); ctx.stroke(); }
    ctx.strokeStyle = '#dfe9ff'; ctx.lineWidth = 4; ctx.strokeRect(900, 220, 860, 600);
    const k = E.inOut(inv(tParking, tParking + 1, t));
    for (let i = 0; i < 9; i++) { ctx.globalAlpha = k; line(ctx, [960 + i * 90, 260, 960 + i * 90, 420], 3, '#dfe9ff'); line(ctx, [960 + i * 90, 620, 960 + i * 90, 780], 3, '#dfe9ff'); ctx.globalAlpha = 1; }
    // tree icon being crossed out
    ctx.strokeStyle = '#7fe08a'; ctx.lineWidth = 5; circle(ctx, 1330, 520, 90 * (1 - k * .2)); ctx.stroke(); text(ctx, 'TREE', 1330, 522, { size: 34, color: '#7fe08a' });
    if (t > tCut) cross(ctx, 1330, 520, 180, '#ff4b3e', E.out(inv(tCut, tCut + .4, t)));
    if (t > tParking) text(ctx, 'P  PARKING LOT  P', 1330, 860, { size: 44, color: '#fff', alpha: k });
    C.person(ctx, 460, 980, 1.35, { who: 'victor', t, mood: 'smile', arms: t > tCut ? 'point' : 'hips', talk: false, rim: 'rgba(160,200,255,.6)' });
    chip(ctx, t, tVictor, 'VICTOR  •  DEVELOPER', 460, 400, { size: 36, bg: '#b3262e', color: '#fff' });
  }
});

// ---------- AA: do the math
const tTB = at('thousands of birds'), tVoices = at('thousands of voices'), tEnough = at('is that enough'), tMath = at('do the math'), t450 = at('450 grams each'), tNoH = at('no hands', 240), tCanShout = at('they can shout'), tCircle = at('they can circle'), tCable = at("they can't pull"), tForm = at("they can't sign"), tTruck = at("they can't stand"), tNotR = at('not really'), tNeed = at('they need you'), t530 = at('5:30');
add(tPlan, t530, [1.02, 1.1, 960, 540], (ctx, t) => {
  if (t < tMath) {
    ctx.drawImage(S.park(S.PAL.night, 'parkNight'), 0, 0);
    flock(ctx, t, Math.floor(lerp(30, 300, inv(tPlan, tEnough, t))), 960, 380, 900, 260, 5, '#05060f', 1.3);
    popText(ctx, t, tTB, 'THOUSANDS OF BIRDS', 960, 360, { size: 70, color: '#fff', stroke: '#000', sw: 10, until: tVoices });
    popText(ctx, t, tVoices, 'THOUSANDS OF VOICES', 960, 360, { size: 70, color: gold, stroke: '#000', sw: 10, until: tEnough });
    if (t > tEnough) { popText(ctx, t, tEnough, 'vs.', 960, 360, { size: 60, color: '#fff' }); popText(ctx, t, tEnough + .7, 'A CHAINSAW', 960, 470, { size: 100, color: '#ff5a4f', stroke: '#000', sw: 12 }); }
  } else {
    ctx.drawImage(S.board(), 0, 0);
    C.crow(ctx, 360, 640, 2, { t, facing: 1, rim: 'rgba(120,180,255,.8)' });
    chip(ctx, t, t450, '450 g EACH', 360, 760, { size: 40, bg: '#fff', color: '#1a2140' });
    chip(ctx, t, tNoH, 'NO HANDS', 360, 850, { size: 40, bg: '#ff5a4f', color: '#fff' });
    const rows = [[tCanShout, 'SHOUT', true], [tCircle, 'CIRCLE', true], [tCable, 'PULL A CABLE', false], [tForm, 'SIGN A FORM', false], [tTruck, 'STAND IN FRONT OF A TRUCK', false]];
    text(ctx, 'CAN', 860, 200, { size: 44, color: '#5fd16a' }); text(ctx, "CAN'T", 860, 470, { size: 44, color: '#ff5a4f' });
    rows.forEach(([tt, s, ok], i) => {
      if (t < tt) return; const k = clamp(E.back(inv(tt, tt + .35, t))); const y = ok ? 270 + i * 90 : 540 + (i - 2) * 90;
      if (ok) check(ctx, 860, y - 6, 56, '#5fd16a', k); else cross(ctx, 860, y, 56, '#ff5a4f', k);
      text(ctx, s, 920, y, { size: 46, color: '#fff', align: 'left', alpha: k });
    });
    if (t > tNotR) { ctx.fillStyle = `rgba(10,13,34,${.8 * clamp((t - tNeed) * 3)})`; ctx.fillRect(0, 0, W, H); }
    popText(ctx, t, tNeed, 'THEY NEED YOU.', 960, 520, { size: 120, color: gold, stroke: '#000', sw: 12 });
  }
});

// ---------- AB: 5:30 AM crew arrives; phone buzzes
const tCrew = at('the crew arrives'), tEng = at('engines rumble'), tShift = at('your shift starts'), tBuzz = at('your phone buzzes'), tClock = at('clock in'), tThenS = at('then a sound');
add(t530, tThenS, [1.02, 1.1, 1100, 560], (ctx, t) => {
  if (t < tBuzz) {
    ctx.drawImage(S.park(S.PAL.predawn, 'parkPredawn'), 0, 0);
    L.rays(ctx, 1600, 760, t, { col: 'rgba(255,170,130,', dir: -Math.PI / 2 - .5, spread: 2.2, a: .12 });
    const k = E.out(inv(tCrew, tCrew + 2, t));
    const shake = t > tEng ? Math.sin(t * 60) * 2 : 0;
    S.truck(ctx, lerp(-500, 520, k), 960 + shake, .9, { lights: true });
    for (let i = 0; i < 3; i++) C.person(ctx, lerp(-200, 700 + i * 150, E.out(inv(tCrew + .6 + i * .2, tCrew + 2.6, t))), 980, .8, { who: 'crew', t: t + i, walk: t > tCrew + 2.6 ? undefined : t * 9 + i, mood: 'neutral' });
    if (t > tEng) { popText(ctx, t, tEng, 'VRRRMMM', 520, 600, { size: 60, color: '#ffb000', stroke: '#000', sw: 10, rot: -.06 }); }
    if (t > tShift) { const kk = E.back(inv(tShift, tShift + .4, t)); ctx.save(); ctx.translate(1660, 300); ctx.scale(kk, kk); clockFace(ctx, 0, 0, 110, 5, 30 + (t - tShift) * 3); ctx.restore(); chip(ctx, t, tShift + .3, 'SHIFT STARTS 6:00', 1660, 460, { size: 32, bg: gold }); }
  } else {
    ctx.drawImage(blurred('predawnBlur', S.park(S.PAL.predawn, 'parkPredawn'), 24), 0, 0);
    C.person(ctx, 640, 1200, 2.2, { who: 'lena', t, mood: 'worried', look: 1, drivercap: true, arms: 'phone', holding: 'phone', rim: 'rgba(255,170,130,.8)' });
    if (t > tClock - .3) phone(ctx, 1320, 520, 1.15, t, 'Clock in, Lena.|Or don\'t come back.');
    else phone(ctx, 1320, 520, 1.15, t, '...');
  }
}, { shake: [[tEng, .6, 6]] });

// ---------- AC: tap tap Pip — time slows — the choice
const tTT = at('tap tap pip'), tSlow = at('time slows'), t11 = at('11 minutes'), t2km = at('2 kilometers'), tLookB = at('you look at the bus'), tLookT = at('you look at the tree'), tOne = at('one choice'), tJob = at('keep your job'), tWord = at('keep your word'), tSwitch = at('you switch off');
add(tThenS, tSwitch, [1.02, 1.12, 960, 520], (ctx, t) => {
  if (t < tLookB) {
    // bus window, Pip taps
    ctx.drawImage(blurred('predawnBlur', S.park(S.PAL.predawn, 'parkPredawn'), 24), 0, 0);
    const slow = t > tSlow ? clamp((t - tSlow) * 2) : 0;
    ctx.fillStyle = '#f0b429'; rr(ctx, 260, 160, 1100, 760, 40); ctx.fill(); ctx.fillStyle = '#26324e'; rr(ctx, 300, 200, 1020, 680, 26); ctx.fill();
    ctx.save(); rr(ctx, 300, 200, 1020, 680, 26); ctx.clip(); C.person(ctx, 640, 1400, 2.5, { who: 'lena', t, mood: 'surprised', look: 1, drivercap: true, shadow: false, rim: null }); ctx.restore();
    ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fillRect(300, 200, 1020, 680);
    const tap = (t > tTT && t < tTT + .3) || (t > tTT + .35 && t < tTT + .65);
    C.crow(ctx, 1470, 800, 2.2, { t: slow ? tSlow + (t - tSlow) * .2 : t, facing: -1, notch: true, rot: tap ? -.25 : 0, tilt: .1 });
    if (t > tTT) { popText(ctx, t, tTT, 'TAP', 1290, 440, { size: 60, color: gold, stroke: '#000', sw: 8, until: tTT + 1.2 }); popText(ctx, t, tTT + .35, 'TAP', 1300, 540, { size: 60, color: gold, stroke: '#000', sw: 8, until: tTT + 1.2 }); }
    if (slow) { ctx.fillStyle = `rgba(20,30,60,${.35 * slow})`; ctx.fillRect(0, 0, W, H); }
    if (t > t11) { const k = E.back(inv(t11, t11 + .4, t)); ctx.save(); ctx.translate(960, 330); ctx.scale(k, k); ctx.fillStyle = 'rgba(0,0,0,.6)'; rr(ctx, -300, -90, 600, 180, 24); ctx.fill(); text(ctx, '11:00', 0, -6, { size: 120, color: '#ff5a4f', fam: 'JetBrains Mono' }); text(ctx, 'until the first cut', 0, 70, { size: 28, color: '#fff', weight: 700 }); ctx.restore(); }
    if (t > t2km) chip(ctx, t, t2km, '2 KM TO THE TERMINAL', 960, 520, { size: 44, bg: '#fff', color: '#222' });
  } else {
    // split: bus vs tree
    const k = E.out(inv(tLookB, tLookB + .4, t)), k2 = E.out(inv(tLookT, tLookT + .4, t));
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W / 2 - 6, H); ctx.clip(); ctx.globalAlpha = k;
    ctx.drawImage(S.terminal(), -480, 0); S.bus(ctx, 560, 900, .6, { lights: true });
    ctx.restore();
    if (t > tLookT) { ctx.save(); ctx.beginPath(); ctx.rect(W / 2 + 6, 0, W / 2, H); ctx.clip(); ctx.globalAlpha = k2; ctx.drawImage(S.park(S.PAL.predawn, 'parkPredawn'), -200, 0); ctx.restore(); }
    ctx.fillStyle = '#000'; ctx.fillRect(W / 2 - 6, 0, 12, H);
    popText(ctx, t, tOne, 'ONE CHOICE', 960, 200, { size: 80, color: '#fff', stroke: '#000', sw: 12 });
    chip(ctx, t, tJob, 'KEEP YOUR JOB', 480, 820, { size: 50, bg: '#2457b8', color: '#fff' });
    chip(ctx, t, tWord, 'KEEP YOUR WORD', 1440, 820, { size: 50, bg: gold });
  }
});

// ---------- AD: switch off, walk, stand. Victor: "Move."
const tWalk = at('you walk to the tree'), tStand = at('you stand right'), tWaves = at('victor waves'), tMove = at('move he says'), tDont = at("you don't");
add(tSwitch, tDont + 1.2, [1.02, 1.12, 1100, 560], (ctx, t) => {
  if (t < tWalk) {
    ctx.fillStyle = '#15151c'; ctx.fillRect(0, 0, W, H);
    // ignition close-up
    ctx.fillStyle = '#2a2a33'; circle(ctx, 960, 540, 200); ctx.fill(); ctx.fillStyle = '#3a3a46'; circle(ctx, 960, 540, 150); ctx.fill();
    text(ctx, 'OFF', 790, 380, { size: 40, color: '#ff5a4f' }); text(ctx, 'ON', 1130, 380, { size: 40, color: '#5fd16a' });
    const a = lerp(.6, -.6, E.back(inv(tSwitch + .3, tSwitch + .7, t)));
    ctx.save(); ctx.translate(960, 540); ctx.rotate(a); ctx.fillStyle = '#c9ced6'; rr(ctx, -30, -120, 60, 200, 20); ctx.fill(); ctx.fillStyle = '#0e0e13'; circle(ctx, 0, 120, 70); ctx.fill(); ctx.restore();
  } else {
    ctx.drawImage(S.park(S.PAL.predawn, 'parkPredawn'), 0, 0);
    L.rays(ctx, 1600, 760, t, { col: 'rgba(255,170,130,', dir: -Math.PI / 2 - .5, spread: 2.2, a: .12 });
    S.truck(ctx, 1750, 960, .8, { lights: true });
    const k = E.inOut(inv(tWalk, tStand + .6, t)), walking = k > 0 && k < 1;
    C.person(ctx, lerp(-100, 1080, k), 975, 1.05, { who: 'lena', t, walk: walking ? t * 8 : undefined, mood: 'determined', facing: 1, drivercap: true, rim: 'rgba(255,170,130,.85)', arms: t > tDont ? 'cross' : 'down' });
    C.person(ctx, 1460, 985, 1.05, { who: 'victor', t, facing: -1, mood: t > tMove ? 'angry' : 'annoyed', arms: t > tWaves ? 'permit' : 'hips', holding: t > tWaves ? 'permit' : null, talk: t > tMove && t < tMove + .6, rim: 'rgba(255,170,130,.8)' });
    C.person(ctx, 1640, 990, .9, { who: 'crew', t, facing: -1, mood: 'worried' });
    bubble(ctx, t, tMove, 'Move.', 1500, 420, 1460, 560, { size: 60, until: tDont + .8 });
    popText(ctx, t, tDont, "YOU DON'T.", 600, 300, { size: 90, color: gold, stroke: '#000', sw: 12 });
  }
});

// ---------- AE: the papers — permit never signed
const tDrops = at('then a crow drops'), tPaper = at('paper pages'), tDevRun = at('dev comes running'), tReads = at('he reads them'), tAgain = at('then he reads them again'), tNever2 = at('the permit was never'), tEngStop = at('engines stop'), tStays = at('the tree stays'), tNight = at('that night the crows');
add(tDont + 1.2, tNight, [1.02, 1.1, 1100, 560], (ctx, t) => {
  ctx.drawImage(S.park(S.PAL.dawn, 'parkDawn'), 0, 0);
  L.rays(ctx, 1480, 420, t, { dir: Math.PI * .8, spread: 1.6, a: .18 });
  S.truck(ctx, 1750, 960, .8, { lights: t < tEngStop });
  const k = inv(tDrops, tDrops + 1.4, t);
  C.crow(ctx, lerp(1300, 1700, k), lerp(330, 220, k), .8, { t, fly: t * 14, facing: 1, hold: k < .2 ? 'paper' : null, notch: true });
  if (t > tDrops + .3) { const fk = E.out(inv(tDrops + .3, tDrops + 1, t)); ctx.save(); ctx.translate(1120, lerp(400, 960, fk)); ctx.rotate(fk * .5); ctx.fillStyle = '#fbf6ea'; ctx.fillRect(-40, -12, 80, 24); ctx.restore(); }
  const dk = E.out(inv(tDevRun, tDevRun + 1.6, t));
  const devX = lerp(-150, 760, dk);
  C.person(ctx, 1000, 975, 1.05, { who: 'lena', t, mood: t > tNever2 ? 'happy' : 'determined', facing: 1, drivercap: true, arms: 'cross', rim: 'rgba(255,200,140,.85)' });
  C.person(ctx, devX, 985, 1.05, { who: 'dev', t, walk: dk < 1 ? t * 11 : undefined, arms: dk < 1 ? 'run' : 'read', holding: t > tReads ? 'papers' : null, mood: t > tNever2 ? 'surprised' : 'angry', look: t > tReads ? .5 : 1, rim: 'rgba(255,200,140,.85)' });
  C.person(ctx, 1460, 985, 1.05, { who: 'victor', t, facing: -1, mood: t > tNever2 ? 'worried' : 'angry', arms: 'hips', rim: 'rgba(255,200,140,.8)' });
  chip(ctx, t, tPaper, "PAGES FROM VICTOR'S TRUCK", 1100, 240, { size: 36, bg: '#fff', color: '#222', until: tReads });
  chip(ctx, t, tDevRun + .2, 'still angry', devX, 520, { size: 30, bg: '#ff5a4f', color: '#fff', until: tReads });
  if (t > tAgain && t < tNever2) popText(ctx, t, tAgain, '...again.', 760, 480, { size: 54, color: '#fff', stroke: '#000', sw: 8 });
  if (t > tNever2) {
    ctx.save(); const kk = E.out(inv(tNever2, tNever2 + .4, t)); ctx.globalAlpha = kk; ctx.translate(960, 420);
    ctx.fillStyle = '#fbf6ea'; ctx.fillRect(-260, -170, 520, 340); text(ctx, 'TREE REMOVAL PERMIT', 0, -120, { size: 34, color: '#222' });
    for (let i = 0; i < 4; i++) { ctx.fillStyle = '#bbb'; ctx.fillRect(-200, -70 + i * 30, 400 - i * 40, 8); }
    text(ctx, 'Signature: ________', -40, 120, { size: 30, color: '#555', weight: 700 }); ctx.restore();
    stamp(ctx, t, tNever2 + .7, 'NOT SIGNED', 960, 440, '#ff4b3e', 76);
  }
  if (t > tEngStop) chip(ctx, t, tEngStop, 'ENGINES: OFF', 1700, 600, { size: 34, bg: '#222', color: '#fff' });
  popText(ctx, t, tStays, 'THE TREE STAYS.', 960, 220, { size: 96, color: gold, stroke: '#000', sw: 12 });
}, { shake: [[tNever2 + .7, .3, 12]] });

// ---------- AF: town hall — the new rules
const tRule = at('one new rule'), tR1 = at('crows keep the roost'), tR2 = at('people keep the sidewalks'), tR3 = at('dev keeps your shift'), tBarely = at('barely'), tCall = at('a crow never forgets', 300);
add(tNight, tCall, [1.02, 1.1, 1200, 520], (ctx, t) => {
  ctx.drawImage(S.park(S.PAL.night, 'parkNight'), 0, 0);
  const r = rng(19); for (let i = 0; i < 120; i++) { ctx.fillStyle = '#ffe28a'; const x = 1300 + (r() - .5) * 760, y = 230 + r() * 300; ell(ctx, x, y, 3, 3); ctx.fill(); }
  C.crow(ctx, 1300, 380, 1.3, { t, facing: -1, talk: true, notch: true, rim: 'rgba(150,180,255,.8)' });
  ctx.save(); ctx.translate(560, 460); ctx.fillStyle = '#f4ecd8'; rr(ctx, -360, -260, 720, 520, 20); ctx.fill();
  text(ctx, 'TOWN HALL  •  RULE #1', 0, -200, { size: 40, color: '#3a2a1a' });
  const rows = [[tR1, 'Crows keep the roost.'], [tR2, 'People keep the sidewalks.'], [tR3, 'Dev keeps your shift.']];
  rows.forEach(([tt, s], i) => { if (t < tt) return; const k = clamp(E.out(inv(tt, tt + .3, t))); check(ctx, -290, -96 + i * 110, 44, '#2f9e4f', k); text(ctx, s, -240, -90 + i * 110, { size: 40, color: '#222', align: 'left', weight: 700, alpha: k }); });
  ctx.restore();
  if (t > tR3) C.person(ctx, 400, 1040, .95, { who: 'dev', t, mood: 'annoyed', arms: 'cross', look: 1 });
  popText(ctx, t, tBarely, '(barely)', 680, 860, { size: 54, color: gold, stroke: '#000', sw: 8, rot: -.08 });
});

// ---------- AG: callback — "Yours? They say thank you."
const tYours2 = at('yours', 325), tThank = at('say thank you', 326), tReal = at('so how real');
add(tCall, tReal, [1.0, 1.15, 1150, 600], (ctx, t) => {
  ctx.drawImage(S.nightStop(), 0, 0);
  ctx.fillStyle = 'rgba(255,170,100,.12)'; ctx.fillRect(0, 0, W, H);
  C.person(ctx, 1040, 960, 1.15, { who: 'lena', t, mood: 'smile', look: .6, drivercap: true, rim: 'rgba(255,200,130,.85)', rimDx: 5 });
  C.crow(ctx, 1330, 652, .85, { t, facing: -1, notch: true, tilt: -.2, rim: 'rgba(255,200,130,.9)' });
  popText(ctx, t, tCall, 'A crow never forgets a face.', 760, 260, { size: 54, color: '#fff', weight: 700 });
  if (t > tYours2) { const k = E.out(inv(tYours2, tYours2 + .4, t)), cx = 1050, cy = 960 - 1.15 * 283; ctx.strokeStyle = gold; ctx.lineWidth = 6; const s = lerp(220, 120, k); for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { ctx.beginPath(); ctx.moveTo(cx + sx * s, cy + sy * (s - 40)); ctx.lineTo(cx + sx * s, cy + sy * s); ctx.lineTo(cx + sx * (s - 40), cy + sy * s); ctx.stroke(); } }
  if (t > tThank) chip(ctx, t, tThank, 'FILE: LENA  —  "THANK YOU."', 760, 380, { size: 40, bg: gold });
});

// ---------- AH: reality check
const tTools = at('crows really bend'), tRem = at('they really remember'), tCopyW = at('some even copy'), tWalnut = at('but a walnut'), tImp = at('impossible'), tSmart = at('and how smart'), tArgue = at('experts still'), tReason = at('some see real'), tTrial = at('others say'), tSide = at('which side are you'), tTease = at('but tonight far');
add(tReal, tTease, [1.02, 1.08, 960, 540], (ctx, t) => {
  ctx.drawImage(S.board(), 0, 0);
  if (t < tSmart) {
    popText(ctx, t, tReal, 'HOW REAL IS THIS?', 960, 180, { size: 72, color: '#fff' });
    const rows = [[tTools, 'Crows bend twigs into tools', true], [tRem, 'They remember faces for years', true], [tCopyW, 'Some copy human words', true], [tWalnut, 'Walnut brain = human mind', false]];
    rows.forEach(([tt, s, ok], i) => { if (t < tt) return; const k = clamp(E.back(inv(tt, tt + .35, t))); const y = 330 + i * 130; ctx.save(); ctx.globalAlpha = k; ctx.fillStyle = 'rgba(255,255,255,.06)'; rr(ctx, 380, y - 52, 1160, 104, 20); ctx.fill(); ctx.restore(); if (ok) check(ctx, 460, y - 6, 64, '#5fd16a', k); else cross(ctx, 460, y, 64, '#ff5a4f', k); text(ctx, s, 540, y, { size: 50, color: '#fff', align: 'left', alpha: k }); chip(ctx, t, tt + .3, ok ? 'REAL' : 'FICTION', 1440, y, { size: 32, bg: ok ? '#5fd16a' : '#ff5a4f', color: '#fff' }); });
    stamp(ctx, t, tImp, 'IMPOSSIBLE', 1240, 880, '#ff4b3e', 70);
  } else {
    popText(ctx, t, tSmart, 'HOW SMART ARE CROWS — REALLY?', 960, 180, { size: 60, color: '#fff' });
    // a balance scale
    const tilt = t < tReason ? 0 : t < tTrial ? -.12 : t < tSide ? .12 : Math.sin(t * 1.5) * .1;
    ctx.save(); ctx.translate(960, 560); line(ctx, [0, 0, 0, 300], 16, '#9fb4ff'); ctx.fillStyle = '#9fb4ff'; rr(ctx, -120, 290, 240, 30, 10); ctx.fill();
    ctx.rotate(tilt); line(ctx, [-480, 0, 480, 0], 12, '#9fb4ff');
    for (const [sx, label, col, tt] of [[-1, 'REAL REASONING', '#7fe0ff', tReason], [1, 'FAST TRIAL & ERROR', gold, tTrial]]) {
      ctx.save(); ctx.translate(sx * 480, 0); ctx.rotate(-tilt); line(ctx, [0, 0, -90, 140], 4, '#9fb4ff'); line(ctx, [0, 0, 90, 140], 4, '#9fb4ff'); ctx.fillStyle = '#2a335e'; rr(ctx, -150, 140, 300, 40, 14); ctx.fill();
      if (t > tt) { text(ctx, label, 0, 230, { size: 38, color: col, alpha: clamp((t - tt) * 3) }); C.crow(ctx, 0, 140, .9, { t, facing: -sx, tilt: sx * .2, rim: null }); }
      ctx.restore();
    }
    ctx.restore();
    chip(ctx, t, tArgue, 'EXPERTS STILL ARGUE', 960, 300, { size: 40, bg: '#fff', color: '#1a2140', until: tSide });
    popText(ctx, t, tSide, 'WHICH SIDE ARE YOU ON?', 960, 300, { size: 64, color: gold, stroke: '#0d1128', sw: 10 });
  }
});

// ---------- AI: teaser — something in the walls
const tEyes = at('else opens its eyes'), tQuietly = at('quietly patiently'), tListen = at('and it has been listening'), tOut = at('what do you think');
add(tTease, tOut, [1.0, 1.25, 1000, 560], (ctx, t) => {
  ctx.drawImage(S.nightStop(), 0, 0); ctx.fillStyle = 'rgba(4,5,14,.6)'; ctx.fillRect(0, 0, W, H);
  // a brick wall with a crack, in shadow
  const k = E.inOut(inv(tTease, tEyes + 1, t));
  ctx.save(); ctx.globalAlpha = k; ctx.fillStyle = '#1a1416'; ctx.fillRect(0, 0, W, H);
  for (let y = 0; y < H; y += 60) for (let x = (y / 60) % 2 ? -60 : 0; x < W; x += 120) { ctx.fillStyle = '#231a1c'; rr(ctx, x + 4, y + 4, 112, 52, 4); ctx.fill(); }
  ctx.fillStyle = '#000'; ctx.beginPath(); ctx.moveTo(900, 420); ctx.lineTo(1000, 400); ctx.lineTo(1120, 470); ctx.lineTo(1080, 620); ctx.lineTo(940, 640); ctx.lineTo(880, 540); ctx.closePath(); ctx.fill();
  ctx.restore();
  if (t > tEyes) { const o = E.out(inv(tEyes + .2, tEyes + .9, t)); for (const [ex, ey] of [[975, 520], [1035, 520]]) { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, ex, ey, 2, 60, [[0, `rgba(255,60,60,${.8 * o})`], [1, 'rgba(255,60,60,0)']]); ctx.fillRect(ex - 60, ey - 60, 120, 120); ctx.restore(); ctx.fillStyle = '#ffdddd'; ell(ctx, ex, ey, 9, 9 * o); ctx.fill(); } }
  if (t > tQuietly) { // whiskers + ear hints
    ctx.save(); ctx.globalAlpha = clamp((t - tQuietly) * 1.5) * .7; line(ctx, [1060, 560, 1160, 545], 2, '#665'); line(ctx, [1060, 568, 1165, 572], 2, '#665'); line(ctx, [950, 560, 850, 545], 2, '#665'); line(ctx, [950, 568, 845, 572], 2, '#665'); ctx.restore(); }
  if (t > tListen) popText(ctx, t, tListen, 'listening...', 1000, 780, { size: 54, color: '#ff8a8a', weight: 700 });
}, { vig: .8 });

// ---------- AJ: outro — comments, which animal next, like & subscribe
const tTell = at('tell us in the'), tWhich = at('which animal'), tHit = at('hit like'), tSubs = at('subscribe');
add(tOut, END + 1, [1.0, 1.06, 960, 540], (ctx, t) => {
  ctx.drawImage(S.street(S.PAL.dawn, 'streetDawn'), 0, 0); ctx.fillStyle = 'rgba(20,10,30,.35)'; ctx.fillRect(0, 0, W, H);
  L.rays(ctx, 1500, 420, t, { dir: Math.PI * .8, spread: 1.6, a: .18 });
  popText(ctx, t, tOut, 'WHAT DO YOU THINK?', 960, 230, { size: 80, color: '#fff', stroke: '#120c16', sw: 12 });
  if (t > tTell) { const k = E.back(inv(tTell, tTell + .4, t)); ctx.save(); ctx.translate(700, 470); ctx.scale(k, k); ctx.fillStyle = '#fff'; rr(ctx, -420, -80, 840, 160, 24); ctx.fill(); ctx.fillStyle = '#ccc'; circle(ctx, -340, 0, 40); ctx.fill(); text(ctx, 'Make the rats smart next!', -270, 0, { size: 40, color: '#222', align: 'left', weight: 700 }); line(ctx, [380, -10 + ((t * 2) % 1 > .5 ? 0 : 999), 380, 20], 3, '#222'); ctx.restore(); }
  popText(ctx, t, tWhich, 'WHICH ANIMAL NEXT?', 700, 640, { size: 56, color: gold, stroke: '#120c16', sw: 10 });
  if (t > tHit) {
    const k = E.back(inv(tHit, tHit + .4, t)); ctx.save(); ctx.translate(1450, 520); ctx.scale(k, k);
    const liked = t > tHit + .5;
    ctx.fillStyle = liked ? '#2a8fd6' : '#333'; rr(ctx, -150, -60, 300, 120, 60); ctx.fill(); text(ctx, liked ? '👍 LIKED' : 'LIKE', 0, 4, { size: 44, color: '#fff', fam: liked ? 'Noto Color Emoji, Inter' : 'Inter' });
    const subbed = t > tSubs + .5; ctx.translate(0, 170); ctx.fillStyle = subbed ? '#444' : '#e62117'; rr(ctx, -210, -60, 420, 120, 20); ctx.fill(); text(ctx, subbed ? 'SUBSCRIBED' : 'SUBSCRIBE', 0, 4, { size: 44, color: '#fff' });
    ctx.restore();
  }
  // Pip on the lamp, caws at the very end
  S.lampPost(ctx, 1780, 880, 560);
  const caw = t > END - 1.4;
  C.crow(ctx, 1810, 318, 1, { t, facing: -1, notch: true, beak: caw ? .9 : 0, tilt: caw ? -.3 : Math.sin(t) * .1 });
  if (caw) popText(ctx, t, END - 1.3, 'CAW!', 1650, 200, { size: 70, color: gold, stroke: '#000', sw: 10, rot: -.1 });
});

module.exports = scenes;
