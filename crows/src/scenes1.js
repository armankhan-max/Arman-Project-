// Scenes 0:00 – 1:51 (morning → Dev's office)
const L = require('./lib');
const C = require('./chars');
const S = require('./sets');
const { at, end } = require('./timing');
const { W, H, E, tw, inv, clamp, lerp, rr, circle, ell, line, text, popText, chip, bubble, check, cross, rgrad, vgrad } = L;
const { canvas } = L;

const blurCache = {};
function blurred(key, src, px) {
  if (!blurCache[key]) { const [c, x] = canvas(); x.filter = `blur(${px}px)`; x.drawImage(src, -40, -40, W + 80, H + 80); blurCache[key] = c; }
  return blurCache[key];
}
const FACT = (ctx, t, t0, s, x, y, until) => chip(ctx, t, t0, 'REAL FACT  •  ' + s, x, y, { size: 30, bg: '#3fc1c9', color: '#06262a', until });
const gold = '#f5b83d';

// a sheet of paper / timetable
function paper(ctx, x, y, w, h, rows = 6, rot = 0, title = null) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.fillRect(-w / 2 + 6, -h / 2 + 8, w, h);
  ctx.fillStyle = '#f7f1e3'; ctx.fillRect(-w / 2, -h / 2, w, h);
  if (title) text(ctx, title, 0, -h / 2 + 30, { size: 26, color: '#2b2b33', weight: 900 });
  for (let i = 0; i < rows; i++) { ctx.fillStyle = i % 2 ? '#c9c2b0' : '#a59d8a'; ctx.fillRect(-w / 2 + 20, -h / 2 + 60 + i * ((h - 80) / rows), w - 40 - (i % 3) * 30, 8); }
  ctx.fillStyle = 'rgba(245,200,80,.6)'; ctx.fillRect(-30, -h / 2 - 10, 60, 20);
  ctx.restore();
}
// brains
function brain(ctx, x, y, r, col = '#f2a3b0', glow = 0) {
  ctx.save(); if (glow > 0) { ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, x, y, r * .2, r * 2.6, [[0, `rgba(120,220,255,${.7 * glow})`], [1, 'rgba(120,220,255,0)']]); ctx.fillRect(x - r * 3, y - r * 3, r * 6, r * 6); ctx.restore(); ctx.save(); }
  ctx.fillStyle = col; ell(ctx, x, y, r, r * .78); ctx.fill(); ctx.strokeStyle = 'rgba(120,40,60,.45)'; ctx.lineWidth = Math.max(2, r * .06);
  for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.arc(x - r * .5 + i * r * .25, y - r * .1 + (i % 2) * r * .2, r * .25, 0, Math.PI * 1.3); ctx.stroke(); }
  line(ctx, [x, y - r * .7, x, y + r * .6], Math.max(2, r * .06), 'rgba(120,40,60,.45)'); ctx.restore();
}
function walnut(ctx, x, y, r) { ctx.fillStyle = '#9a6a3a'; ell(ctx, x, y, r, r * .85); ctx.fill(); ctx.strokeStyle = '#6a4220'; ctx.lineWidth = 3; for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(x - r * .4 + i * r * .27, y, r * .3, -1, 1.5); ctx.stroke(); } line(ctx, [x, y - r * .8, x, y + r * .8], 3, '#6a4220'); }

// window with Lena inside (close-up)
function busWindow(ctx, x, y, w, h, t, o = {}) {
  ctx.save(); ctx.fillStyle = o.frame || '#f0b429'; rr(ctx, x - 30, y - 30, w + 60, h + 60, 30); ctx.fill();
  ctx.fillStyle = vgrad(ctx, y, y + h, [[0, '#2f4466'], [1, '#18233a']]); rr(ctx, x, y, w, h, 20); ctx.fill();
  ctx.save(); rr(ctx, x, y, w, h, 20); ctx.clip();
  if (o.lena !== false) C.person(ctx, x + w * .55, y + h + 300, 1.55, { who: 'lena', t, mood: o.mood || 'neutral', look: o.look ?? -1, facing: -1, shadow: false, blinkAt: o.blinkAt, drivercap: true, rim: 'rgba(255,190,120,.5)', talk: o.talk, arms: o.arms, holding: o.holding });
  ctx.fillStyle = 'rgba(255,255,255,.10)'; ctx.beginPath(); ctx.moveTo(x + w * .1, y); ctx.lineTo(x + w * .35, y); ctx.lineTo(x + w * .05, y + h); ctx.lineTo(x - w * .2, y + h); ctx.fill();
  ctx.restore(); ctx.restore();
}

const scenes = [];
const add = (s, e, cam, draw, extra = {}) => scenes.push({ s, e, cam, draw, ...extra });

// ---------- A: terminal arrival
const tLand = at('crow lands');
add(0, at('it tilts'), [1.04, 1.16, 1150, 600], (ctx, t) => {
  ctx.drawImage(S.terminal(), 0, 0);
  L.rays(ctx, 1500, 470, t, { dir: Math.PI * .8, spread: 1.4, a: .14 });
  const bx = lerp(-900, 700, E.out(inv(.2, 3.6, t))); const by = 935, s = .78;
  const brake = Math.sin(clamp((t - 3.3) * 6, 0, Math.PI)) * .012;
  ctx.save(); ctx.translate(bx, by); ctx.rotate(brake); ctx.translate(-bx, -by); S.bus(ctx, bx, by, s, { driver: true }); ctx.restore();
  const mx = bx + 602 * s, my = by - 300 * s;
  // crow flies in and lands on the mirror
  const k = inv(tLand - 1.1, tLand + .25, t);
  if (k < 1) { const cx = lerp(2100, mx, E.out(k)), cy = lerp(160, my, E.inOut(k)) - Math.sin(k * Math.PI) * 60; C.crow(ctx, cx, cy, .7, { t, fly: t * 14, facing: -1 }); }
  else C.crow(ctx, mx, my, .7, { t, facing: -1, tilt: Math.sin(t * 1.4) * .1 });
  L.dust(ctx, t, 70, 3);
});

// ---------- B: close-up on the mirror + timetable, then split-screen blink
const tTilt = at('it tilts'), tLooks = at('it looks at the'), tSpeaks = at('it speaks'), tLate = at("you're late"), tBlink = at('you blink'), tBack = at('the crow blinks back'), tBehind = at('behind it');
add(tTilt, tBlink, [1.02, 1.1, 960, 560], (ctx, t) => {
  ctx.drawImage(blurred('termB', S.terminal(), 18), 0, 0);
  L.rays(ctx, 1700, 300, t, { dir: Math.PI * .85, spread: 1.2, a: .12 });
  busWindow(ctx, 1040, 230, 700, 560, t, { look: -1, mood: t > tLate ? 'surprised' : 'neutral' });
  paper(ctx, 1590, 420, 190, 250, 7, .04, 'TIMETABLE');
  // mirror arm + housing
  line(ctx, [1040, 520, 760, 470, 700, 520], 26, '#1a1a1f');
  ctx.fillStyle = '#1a1a1f'; rr(ctx, 560, 420, 260, 360, 60); ctx.fill(); ctx.fillStyle = '#8fa6c4'; rr(ctx, 585, 445, 210, 310, 46); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.moveTo(620, 460); ctx.lineTo(700, 460); ctx.lineTo(600, 700); ctx.fill();
  const look = t > tLooks && t < tSpeaks + .4;
  const tilt = t < tLooks ? Math.sin(clamp((t - tTilt) * 3, 0, Math.PI)) * -.42 : look ? -.25 : Math.sin(t * 1.2) * .06;
  C.crow(ctx, 690, 425, 2.3, { t, facing: 1, tilt, look: look ? 1 : 0, talk: t > tLate && t < tBlink - .3 });
  if (t > tLooks && t < tSpeaks) { ctx.save(); ctx.globalAlpha = .6 * Math.sin(inv(tLooks, tSpeaks, t) * Math.PI); line(ctx, [900, 300, 1560, 400], 4, '#fff'); ctx.restore(); }
  bubble(ctx, t, tLate, "You're late, Lena.", 560, 230, 760, 340, { size: 46 });
  bubble(ctx, t, at('four minutes'), 'Four minutes.', 420, 330, 700, 360, { size: 40, bg: gold });
  L.dust(ctx, t, 40, 7);
});
add(tBlink, tBehind, [1.0, 1.05, 960, 540], (ctx, t) => {
  // split screen: Lena | crow — editor trick for a "staring contest"
  const k = E.out(inv(tBlink, tBlink + .35, t));
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W / 2 - 6, H); ctx.clip();
  ctx.drawImage(blurred('termB', S.terminal(), 18), -300, 0);
  C.person(ctx, 520, 1500, 2.9, { who: 'lena', t, mood: 'surprised', facing: 1, look: 1, blinkAt: tBlink + .15, drivercap: true, shadow: false });
  ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(W / 2 + 6, 0, W / 2, H); ctx.clip(); ctx.translate((1 - k) * 600, 0);
  ctx.drawImage(blurred('termB', S.terminal(), 18), 300, 0);
  C.crow(ctx, 1420, 900, 4.2, { t, facing: -1, blink: tBack + .35, tilt: .1 });
  ctx.restore();
  ctx.fillStyle = '#000'; ctx.fillRect(W / 2 - 6, 0, 12, H);
  popText(ctx, t, tBlink + .1, 'blink.', 480, 260, { size: 70, color: '#fff', stroke: '#000', sw: 10 });
  popText(ctx, t, tBack + .25, 'blink.', 1440, 260, { size: 70, color: gold, stroke: '#000', sw: 10 });
});

// ---------- D: crows reading the route map on the dashboard
const tPoints = at('one points'), tToast = at('another one is eating');
add(tBehind, at('yesterday crows'), [1.03, 1.12, 960, 520], (ctx, t) => {
  ctx.drawImage(blurred('termD', S.terminal(), 26), 0, -120);
  // windshield frame + dashboard
  ctx.fillStyle = '#16161c'; ctx.fillRect(0, 0, W, 120); ctx.fillRect(0, 0, 70, H); ctx.fillRect(W - 70, 0, 70, H);
  ctx.fillStyle = vgrad(ctx, 700, H, [[0, '#2d2a33'], [1, '#141218']]); ctx.beginPath(); ctx.moveTo(0, 760); ctx.quadraticCurveTo(960, 690, W, 760); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
  // route map board
  ctx.save(); ctx.translate(960, 420); ctx.fillStyle = '#f4efe2'; rr(ctx, -380, -230, 760, 430, 18); ctx.fill();
  text(ctx, 'ROUTE 12', -260, -190, { size: 34, color: '#2b2b33', weight: 900 });
  line(ctx, [-330, 120, -150, 40, 40, 60, 200, -60, 330, -120], 14, '#e8483f');
  line(ctx, [-330, -60, -100, -40, 60, 120, 330, 130], 14, '#2a8fd6');
  const stops = [[-330, 120], [-150, 40], [40, 60], [200, -60], [330, -120], [-100, -40], [60, 120]];
  stops.forEach(([a, b]) => { ctx.fillStyle = '#fff'; circle(ctx, a, b, 14); ctx.fill(); ctx.strokeStyle = '#2b2b33'; ctx.lineWidth = 5; ctx.stroke(); });
  if (t > tPoints) { const p = .5 + .5 * Math.sin(t * 8); ctx.strokeStyle = `rgba(245,184,61,${.6 + .4 * p})`; ctx.lineWidth = 8; circle(ctx, 200, -60, 30 + p * 8); ctx.stroke(); }
  text(ctx, 'ELM ST', 200, -110, { size: 30, color: t > tPoints ? '#c47b00' : '#555', weight: 900 });
  ctx.restore();
  // three crows on the dash
  C.crow(ctx, 520, 790, 1.5, { t, facing: 1, tilt: -.35, seed: 1 });
  const pk = E.out(inv(tPoints, tPoints + .5, t));
  C.crow(ctx, 900 + pk * 120, 780, 1.6, { t, facing: 1, tilt: -.5 * pk - .1, seed: 2, rot: -.25 * pk });
  const eat = t > tToast;
  C.crow(ctx, 1450, 800, 1.5, { t, facing: -1, tilt: eat ? Math.sin(t * 10) * .12 + .2 : -.2, hold: eat ? 'toast' : null, seed: 3, beak: eat ? .3 : 0 });
  if (!eat) { ctx.fillStyle = '#d9a04a'; rr(ctx, 1260, 760, 60, 50, 10); ctx.fill(); }
  chip(ctx, t, tToast + .6, 'HEY! MY TOAST', 1500, 560, { size: 36, bg: '#ff6b5a', color: '#fff', rot: .05 });
});

// ---------- E: yesterday vs today (split wipe)
const tToday = at('today they think');
add(at('yesterday crows'), at('a crow weighs'), [1.0, 1.06, 960, 540], (ctx, t) => {
  const wipe = E.inOut(inv(tToday - .1, tToday + .5, t));
  const div = lerp(W + 100, W / 2, wipe);
  // left: yesterday (sepia, clever bird)
  ctx.fillStyle = vgrad(ctx, 0, H, [[0, '#cdb38a'], [1, '#8a6e4a']]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#7a5e3c'; ctx.fillRect(0, 820, W, 260);
  C.crow(ctx, lerp(960, 520, wipe), 830, 3.2, { t, facing: 1, hold: 'twig', rim: 'rgba(255,240,200,.6)' });
  popText(ctx, t, at('yesterday crows') + .1, 'YESTERDAY', lerp(960, 480, wipe), 210, { size: 84, color: '#3a2a18' });
  popText(ctx, t, at('clever birds'), 'clever bird', lerp(960, 480, wipe), 300, { size: 52, weight: 700, color: '#3a2a18' });
  // right: today
  ctx.save(); ctx.beginPath(); ctx.moveTo(div, 0); ctx.lineTo(W, 0); ctx.lineTo(W, H); ctx.lineTo(div - 80, H); ctx.closePath(); ctx.clip();
  ctx.fillStyle = vgrad(ctx, 0, H, [[0, '#2a3a8a'], [1, '#141a40']]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = rgrad(ctx, 1450, 520, 20, 600, [[0, 'rgba(120,220,255,.45)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#10142e'; ctx.fillRect(0, 820, W, 260);
  brain(ctx, 1480, 470, 46, '#f2a3b0', .8 + .2 * Math.sin(t * 5));
  C.crow(ctx, 1400, 830, 3.2, { t, facing: -1, tilt: .1, rim: 'rgba(120,220,255,.9)' });
  text(ctx, 'TODAY', 1440, 210, { size: 84, color: '#fff' });
  if (t > at('think like you')) popText(ctx, t, at('think like you'), 'thinks like YOU', 1440, 300, { size: 52, color: gold });
  ctx.restore();
  line(ctx, [div, 0, div - 80, H], 10, '#fff');
});

// ---------- F/G: the science board
const tWeigh = at('a crow weighs'), tWal = at('size of a walnut'), tYours = at('yours about'), tNeur = at('86 billion'), tOver = at('overnight'), tGap = at('the gap closes');
add(tWeigh, tGap, [1.02, 1.08, 960, 520], (ctx, t) => {
  ctx.drawImage(S.board(), 0, 0);
  // crow side
  C.crow(ctx, 520, 760, 2.6, { t, facing: 1, rim: 'rgba(120,180,255,.8)' });
  chip(ctx, t, tWeigh + .7, '≈ 450 g', 470, 830, { size: 52, bg: '#fff', color: '#1a2140' });
  if (t > tWal) { const k = E.back(inv(tWal + .2, tWal + .6, t)); ctx.save(); ctx.translate(640, 330); ctx.scale(k, k); walnut(ctx, 0, 0, 46); ctx.restore(); popText(ctx, t, tWal + .3, 'brain = walnut', 640, 250, { size: 40, color: '#ffd9a0' }); }
  // human side
  if (t > tYours) {
    const k = E.out(inv(tYours, tYours + .5, t)); ctx.save(); ctx.globalAlpha = k; ctx.translate(lerp(1700, 1420, k), 0);
    ctx.fillStyle = '#2a335e'; circle(ctx, 0, 470, 210); ctx.fill(); ctx.fillRect(-120, 640, 240, 300);
    brain(ctx, 10, 440, 120, '#f2a3b0', 0); ctx.restore();
    chip(ctx, t, tYours + .5, '≈ 1.4 kg', 1420, 760, { size: 52, bg: '#fff', color: '#1a2140' });
  }
  if (t > tNeur) {
    const k = inv(tNeur, tNeur + 1.4, t); const n = Math.floor(E.out(k) * 86);
    text(ctx, `${n} BILLION NEURONS`, 1420, 860, { size: 48, color: gold, stroke: '#0d1128', sw: 8, alpha: inv(tNeur, tNeur + .2, t) });
  }
  if (t > tOver) {
    const k = E.inOut(inv(tOver, tOver + .8, t));
    ctx.save(); ctx.setLineDash([18, 14]); ctx.lineDashOffset = -t * 60; line(ctx, [1300, 440, lerp(1300, 700, k), lerp(440, 420, k)], 8, '#7fe0ff'); ctx.restore();
    brain(ctx, 640, 330, 46 * k, '#f2a3b0', k);
    popText(ctx, t, tOver + .3, 'OVERNIGHT', 960, 200, { size: 90, color: '#7fe0ff', stroke: '#0d1128', sw: 10 });
  }
});
const tOnly = at('but only inside'), tBodies = at('their bodies stay'), tNoH = at('no hands'), tBeak = at('just a beak'), tFeet = at('two feet'), tWings = at('two wings'), tRule = at("that's the rule"), tSoWhat = at('so what if');
add(tGap, tSoWhat, [1.02, 1.1, 960, 540], (ctx, t) => {
  ctx.drawImage(S.board(), 0, 0);
  if (t < tBodies) {
    // the gap closing: two bars
    const k = E.inOut(inv(tGap + .2, tGap + 1.4, t));
    text(ctx, 'CROW MIND', 380, 380, { size: 40, color: '#9fb4ff', align: 'right' });
    text(ctx, 'HUMAN MIND', 380, 520, { size: 40, color: '#9fb4ff', align: 'right' });
    ctx.fillStyle = '#2a335e'; rr(ctx, 420, 350, 1100, 60, 30); ctx.fill(); rr(ctx, 420, 490, 1100, 60, 30); ctx.fill();
    ctx.fillStyle = '#7fe0ff'; rr(ctx, 420, 350, lerp(280, 1080, k), 60, 30); ctx.fill();
    ctx.fillStyle = gold; rr(ctx, 420, 490, 1080, 60, 30); ctx.fill();
    popText(ctx, t, tGap + 1.4, 'GAP: CLOSED', 960, 680, { size: 64, color: '#fff' });
    if (t > tOnly) { popText(ctx, t, tOnly + .1, '...but only inside their heads', 960, 790, { size: 46, color: '#7fe0ff', weight: 700 }); }
  } else {
    const cx = 640;
    C.crow(ctx, cx, 820, 3.6, { t, facing: 1, rim: 'rgba(120,180,255,.8)' });
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, cx + 120, 600, 10, 160, [[0, `rgba(120,220,255,${.5 + .2 * Math.sin(t * 4)})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(cx - 100, 400, 450, 400); ctx.restore();
    popText(ctx, t, tBodies + .1, 'SAME BODY', cx + 60, 230, { size: 64, color: '#fff' });
    const rows = [[tNoH, 'HANDS', false], [tBeak, 'A BEAK', true], [tFeet, 'TWO FEET', true], [tWings, 'TWO WINGS', true]];
    rows.forEach(([tt, s, ok], i) => {
      if (t < tt) return; const k = E.back(inv(tt, tt + .35, t)); const y = 330 + i * 130;
      ctx.save(); ctx.globalAlpha = clamp(k); ctx.fillStyle = 'rgba(255,255,255,.06)'; rr(ctx, 1060, y - 50, 640, 100, 20); ctx.fill(); ctx.restore();
      text(ctx, s, 1220, y, { size: 52, color: '#fff', align: 'left', alpha: clamp(k) });
      if (ok) check(ctx, 1130, y - 6, 70, '#5fd16a', clamp(k)); else cross(ctx, 1130, y, 70, '#ff5a4f', clamp(k));
    });
    if (t > tRule) { const k = E.back(inv(tRule, tRule + .3, t)); ctx.save(); ctx.translate(1380, 900); ctx.rotate(-.08); ctx.scale(2 - k, 2 - k); ctx.globalAlpha = clamp(k); ctx.strokeStyle = '#ff5a4f'; ctx.lineWidth = 8; rr(ctx, -260, -50, 520, 100, 14); ctx.stroke(); text(ctx, "THAT'S THE RULE", 0, 4, { size: 50, color: '#ff5a4f', weight: 900 }); ctx.restore(); }
  }
}, { shake: [[tRule, .25, 10]] });

// ---------- H: title card
const t7 = at('7 in the morning');
add(tSoWhat, t7, [1.0, 1.12, 960, 520], (ctx, t) => {
  ctx.drawImage(S.street(S.PAL.dawn, 'streetDawn'), 0, 0);
  ctx.fillStyle = 'rgba(20,10,30,.45)'; ctx.fillRect(0, 0, W, H);
  L.rays(ctx, 1500, 420, t, { dir: Math.PI * .8, spread: 1.6, a: .2 });
  // power line with crow silhouettes
  ctx.strokeStyle = '#120c16'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, 300); ctx.quadraticCurveTo(960, 420, W, 300); ctx.stroke();
  for (let i = 0; i < 9; i++) { const xx = 140 + i * 205, yy = 300 + Math.sin((xx / W) * Math.PI) * 60 * 2 * .98 - 4; C.crow(ctx, xx, yy, .55, { t: t + i, facing: i % 2 ? -1 : 1, rim: null, tilt: Math.sin(t * 2 + i) * .15, eyeGlow: '#7fe0ff' }); }
  const s0 = tSoWhat;
  popText(ctx, t, s0 + .1, 'WHAT IF', 960, 520, { size: 80, color: '#fff', stroke: '#120c16', sw: 12 });
  popText(ctx, t, at('crows had') , 'CROWS', 960, 640, { size: 150, color: gold, stroke: '#120c16', sw: 16 });
  popText(ctx, t, at('human intelligence'), 'HAD HUMAN INTELLIGENCE', 960, 770, { size: 70, color: '#fff', stroke: '#120c16', sw: 12 });
  popText(ctx, t, at('tomorrow', s0), 'TOMORROW?', 960, 860, { size: 56, color: '#7fe0ff', stroke: '#120c16', sw: 10 });
}, { flash: true });

// ---------- I: 7 AM garbage day
const tGarb = at('garbage day'), tLearn = at('crows always learn'), tRead = at('they read your'), tShut = at('your bins stay'), tComp = at('file a complaint'), t8 = at('8', 60);
add(t7, t8, [1.03, 1.12, 900, 560], (ctx, t) => {
  ctx.drawImage(S.street(), 0, 0); L.rays(ctx, 1500, 230, t, { a: .12 });
  // lamp post with calendar
  S.lampPost(ctx, 420, 880, 560);
  paper(ctx, 420, 520, 150, 190, 5, -.03, 'TRASH');
  const reading = t > tRead && t < tShut + .5;
  C.crow(ctx, 470, 330, .9, { t, facing: -1, tilt: reading ? .35 : 0, seed: 4 });
  if (reading) chip(ctx, t, tRead + .3, "reading the city's calendar", 560, 220, { size: 30, bg: '#fff', color: '#222', until: tShut + .3 });
  // bins
  const shut = t > tShut;
  S.bin(ctx, 900, 880, 1.2, '#2f7d4a', shut ? 0 : .5 + Math.sin(t * 3) * .05); S.bin(ctx, 1110, 880, 1.2, '#2a5fa8', shut ? 0 : .4);
  if (shut) { ctx.fillStyle = '#c9ced6'; rr(ctx, 880, 664, 40, 30, 6); ctx.fill(); rr(ctx, 1090, 664, 40, 30, 6); ctx.fill(); chip(ctx, t, tShut + .3, 'LOCKED', 1005, 600, { size: 34, bg: '#5fd16a', color: '#0a2a10', until: tComp - .2 }); }
  // crows at bins
  C.crow(ctx, 760, 880, .9, { t, facing: 1, tilt: shut ? .2 : Math.sin(t * 8) * .2, seed: 5 });
  C.crow(ctx, 1300, 880, .9, { t, facing: -1, hold: t > tComp ? 'pen' : null, seed: 6, tilt: t > tComp ? .3 : 0 });
  FACT(ctx, t, tLearn, 'crows learn trash-day schedules', 960, 160, tRead);
  if (t > tComp) {
    const k = E.back(inv(tComp, tComp + .4, t)); ctx.save(); ctx.translate(1520, 520); ctx.rotate(.06); ctx.scale(k, k);
    ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(-170, -200, 360, 420); ctx.fillStyle = '#fbf6ea'; ctx.fillRect(-180, -210, 360, 420);
    text(ctx, 'OFFICIAL COMPLAINT', 0, -160, { size: 30, color: '#b3262e' }); text(ctx, 'Re: the lids.', 0, -90, { size: 34, weight: 700, color: '#222' });
    text(ctx, 'They are rude.', 0, -40, { size: 30, weight: 500, color: '#444' }); text(ctx, '— The Crows', 40, 100, { size: 30, weight: 700, color: '#444', fam: 'DejaVu Serif' });
    ctx.restore();
  }
  popText(ctx, t, tGarb, 'GARBAGE DAY', 960, 330, { size: 72, color: '#fff', stroke: '#3a2418', sw: 12, until: tLearn - .1 });
});

// ---------- J: 8 AM cafe
const tCopy = at('copy a few'), tFull = at('full sentences'), tOrder = at('orders your'), tPol = at('politely'), tRec = at('asks for a receipt'), t9 = at('9', 75);
add(t8, t9, [1.03, 1.1, 960, 520], (ctx, t) => {
  ctx.drawImage(S.street(S.PAL.day), 0, 0);
  // cafe facade
  ctx.fillStyle = '#3a2a3a'; ctx.fillRect(560, 300, 900, 580);
  ctx.fillStyle = '#251a26'; ctx.fillRect(540, 280, 940, 40);
  for (let i = 0; i < 10; i++) { ctx.fillStyle = i % 2 ? '#fff4e0' : '#d9483f'; ctx.beginPath(); ctx.moveTo(560 + i * 90, 380); ctx.lineTo(650 + i * 90, 380); ctx.lineTo(660 + i * 90, 470); ctx.lineTo(570 + i * 90, 470); ctx.fill(); }
  text(ctx, 'CAFÉ  CORVO', 1010, 345, { size: 44, color: gold, weight: 900, track: 6 });
  ctx.fillStyle = '#ffd99a'; rr(ctx, 620, 520, 420, 300, 10); ctx.fill(); ctx.fillStyle = 'rgba(80,40,30,.25)'; for (let i = 0; i < 4; i++) rr(ctx, 650 + i * 95, 700, 70, 40, 20), ctx.fill();
  ctx.fillStyle = '#3a2418'; rr(ctx, 1110, 540, 160, 340, 8); ctx.fill();
  C.person(ctx, 820, 880, .9, { who: 'people', t, mood: 'surprised', look: 1 });
  C.person(ctx, 1350, 900, 1.05, { who: 'lena', t, mood: t > tOrder ? 'surprised' : 'neutral', facing: -1, look: -1 });
  // the crow on the roof edge
  const k = inv(tOrder, tOrder + .3, t);
  C.crow(ctx, 900, 284, 1.15, { t, facing: 1, talk: (t > tFull && t < tFull + 1.3) || (t > tOrder && t < tPol) || (t > tRec && t < tRec + 1.4), hold: t > tRec + 1.4 ? 'receipt' : null, tilt: k * -.15 });
  bubble(ctx, t, tCopy + .2, 'Hello.', 760, 160, 900, 240, { size: 38, until: tFull - .1, bg: '#e9dcc4' });
  bubble(ctx, t, tFull, 'Good morning! Lovely weather, isn\'t it?', 700, 170, 900, 240, { size: 36, until: tOrder - .2, maxW: 560 });
  bubble(ctx, t, tOrder + .2, 'One croissant, please.', 680, 170, 900, 240, { size: 44, until: tRec - .1 });
  chip(ctx, t, tPol, 'POLITELY', 1300, 210, { size: 40, bg: gold, rot: .06, until: tRec - .1 });
  bubble(ctx, t, tRec + .1, 'And a receipt, please.', 680, 170, 900, 240, { size: 44 });
  FACT(ctx, t, tCopy, 'crows can mimic human words', 960, 960 - 130, tFull + .6);
});

// ---------- K: 9 AM tools
const tTwig = at('bend twigs'), tWild = at('wild ones'), tMorning = at('this morning a crow'), tOpens = at('and opens the park'), tWhy = at('why it wanted'), tSeed = at('bird seed'), tFair = at('fair'), tNoon = at('noon');
add(t9, tNoon, [1.03, 1.1, 960, 540], (ctx, t) => {
  if (t < tMorning) {
    ctx.drawImage(S.board(), 0, 0);
    // twig -> hook animation
    const k = E.inOut(inv(tTwig + .2, tTwig + 1.4, t));
    ctx.save(); ctx.translate(960, 520); ctx.scale(2.4, 2.4);
    ctx.strokeStyle = '#a07040'; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-160, 0); ctx.lineTo(120, 0); ctx.quadraticCurveTo(150 + 10 * (1 - k), -30 * k, 140 - 30 * k, -40 * k); ctx.stroke();
    ctx.restore();
    popText(ctx, t, tTwig + .3, 'TWIG  →  HOOK', 960, 300, { size: 70, color: '#fff' });
    if (t > tWild) { C.crow(ctx, 520, 820, 2, { t, facing: 1, hold: 'hook' }); ctx.fillStyle = '#6a4a2a'; rr(ctx, 1200, 740, 420, 120, 50); ctx.fill(); ctx.fillStyle = '#f2e3a0'; ell(ctx, 1330 + Math.sin(t * 6) * 6, 800, 26, 12); ctx.fill(); }
    FACT(ctx, t, tTwig, 'New Caledonian crows make hooks', 960, 170);
  } else {
    ctx.drawImage(S.park(S.PAL.day, 'parkNoTree', false), 0, 0); L.rays(ctx, 1500, 230, t, { a: .12 });
    const op = E.out(inv(tOpens + .4, tOpens + 1.1, t));
    S.shed(ctx, 1150, 880, 1.25, op);
    const bend = t > tMorning + .8;
    const fk = inv(tOpens - .5, tOpens + .3, t);
    const cx = lerp(650, 1100, E.inOut(fk)), cy = lerp(880, 650, E.inOut(fk)) - Math.sin(fk * Math.PI) * 120;
    C.crow(ctx, cx, cy, 1.3, { t, facing: 1, hold: bend ? 'hook' : 'clip', fly: fk > 0 && fk < 1 ? t * 14 : undefined, tilt: !bend ? Math.sin(t * 9) * .15 : 0 });
    if (bend && fk <= 0) chip(ctx, t, tMorning + .8, 'paper clip → key', 650, 560, { size: 32, bg: '#fff', color: '#222' });
    popText(ctx, t, tWhy, 'WHY?', 600, 300, { size: 80, color: '#fff', stroke: '#3a2418', sw: 12, until: tSeed });
    if (t > tSeed) { C.crow(ctx, 1170, 880, 1.1, { t, facing: -1, hold: 'pebble', seed: 9, tilt: Math.sin(t * 9) * .2 }); chip(ctx, t, tSeed, 'IT WANTED THE BIRD SEED', 700, 300, { size: 40, bg: gold }); }
    popText(ctx, t, tFair, 'Fair.', 700, 420, { size: 70, color: '#fff', stroke: '#3a2418', sw: 10, weight: 900 });
  }
});

// ---------- L: noon — stones in water, then the soda cup
const tStones = at('crows once drop'), tTodayP = at('today one drops'), tFry = at('the last fry'), tAppl = at('applause'), tDev = at('dev your dispatcher');
add(tNoon, tDev, [1.02, 1.08, 960, 540], (ctx, t) => {
  const today = t > tTodayP;
  if (!today) ctx.drawImage(S.board(), 0, 0); else { ctx.drawImage(S.park(S.PAL.noon, 'parkNoon', false), 0, 0); L.rays(ctx, 960, 160, t, { dir: Math.PI / 2, spread: 1.4, a: .1 }); }
  const t0 = today ? tTodayP + .2 : tStones + .4;
  const n = Math.min(6, Math.floor(Math.max(0, t - t0) / .55));
  const lvl = n / 6;
  // the container
  const cx = 960, top = today ? 280 : 360, bot = 860, w = today ? 300 : 360;
  ctx.save();
  if (today) { ctx.fillStyle = '#e8483f'; ctx.beginPath(); ctx.moveTo(cx - w / 2 - 20, top); ctx.lineTo(cx + w / 2 + 20, top); ctx.lineTo(cx + w / 2 - 20, bot); ctx.lineTo(cx - w / 2 + 20, bot); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(cx - w / 2 - 6, top + 160, w + 12, 60); text(ctx, 'SODA', cx, top + 192, { size: 40, color: '#e8483f', weight: 900 }); ctx.globalAlpha = .55; }
  ctx.fillStyle = 'rgba(200,230,255,.25)'; ctx.fillRect(cx - w / 2, top, w, bot - top);
  const wy = lerp(bot - 160, top + 40, E.out(lvl)); ctx.fillStyle = today ? 'rgba(90,40,20,.85)' : 'rgba(80,170,255,.7)'; ctx.fillRect(cx - w / 2, wy, w, bot - wy);
  ctx.restore();
  ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.lineWidth = 6; ctx.strokeRect(cx - w / 2, top, w, bot - top);
  for (let i = 0; i < n; i++) { ctx.fillStyle = '#8a8680'; ell(ctx, cx - w / 2 + 40 + (i * 53) % (w - 80), bot - 26 - Math.floor(i / 4) * 34, 26, 20); ctx.fill(); }
  // falling pebble
  const ph = ((t - t0) % .55) / .55; if (t > t0 && n < 6) { ctx.fillStyle = '#8a8680'; ell(ctx, cx + 30, lerp(top - 140, wy, ph * ph), 22, 18); ctx.fill(); }
  // treat / fry floating at surface
  const fx = cx - 40;
  if (today) { ctx.save(); ctx.translate(fx, wy - 10); ctx.rotate(-.5); ctx.fillStyle = '#f2c14e'; rr(ctx, -12, -60, 24, 110, 6); ctx.fill(); ctx.restore(); }
  else { ctx.fillStyle = '#f2e3a0'; ell(ctx, fx, wy - 8, 30, 14); ctx.fill(); }
  C.crow(ctx, cx + w / 2 + 40, top - 20, 1.6, { t, facing: -1, hold: n < 6 ? 'pebble' : null, tilt: .4 });
  if (!today) { popText(ctx, t, tStones + .2, 'STONES  →  WATER RISES', 960, 200, { size: 56, color: '#fff' }); FACT(ctx, t, tStones, "crows pass Aesop's water test", 960, 940 - 40); }
  else {
    popText(ctx, t, tFry, 'THE LAST FRY', 560, 300, { size: 60, color: '#fff', stroke: '#3a2418', sw: 10 });
    if (t > tAppl) { for (let i = 0; i < 4; i++) C.crow(ctx, 260 + i * 120 + (i > 1 ? 1100 : 0), 880, 1, { t: t + i, facing: i > 1 ? -1 : 1, fly: t * 20 + i, seed: i }); chip(ctx, t, tAppl, 'APPLAUSE', 960, 180, { size: 52, bg: gold }); }
  }
});

// ---------- M: Dev rolls his eyes
const tRolls = at('rolls his eyes'), tJust = at("they're just birds"), tAre = at('are they'), t1 = at('1', 110);
add(tDev, t1, [1.04, 1.12, 900, 560], (ctx, t) => {
  ctx.drawImage(S.office(), 0, 0);
  C.person(ctx, 760, 1000, 1.5, { who: 'dev', t, mood: t > tRolls ? 'annoyed' : 'neutral', look: t > tRolls && t < tJust ? -1 : .5, lid: t > tRolls && t < tJust ? .3 : 0, talk: t > tJust && t < tAre - .2, arms: 'cross', holding: null, rim: 'rgba(255,200,140,.6)' });
  if (t > tRolls && t < tJust) { popText(ctx, t, tRolls + .1, '🙄', 0, 0, { size: 1 }); chip(ctx, t, tRolls + .1, '*eye roll*', 760, 300, { size: 34, bg: '#fff', color: '#222', until: tJust }); }
  chip(ctx, t, tDev, 'DEV  •  DISPATCHER', 360, 880, { size: 32, bg: '#2f9e4f', color: '#fff' });
  bubble(ctx, t, tJust, "They're just birds, Lena.", 980, 320, 820, 430, { size: 42, until: tAre - .1 });
  // crow at the window behind him
  if (t > tAre - .4) { const k = E.out(inv(tAre - .4, tAre + .2, t)); C.crow(ctx, lerp(1900, 1400, k), 600, 1.6, { t, facing: -1, tilt: .3, fly: k < 1 ? t * 14 : undefined }); }
  popText(ctx, t, tAre, 'ARE THEY?', 1400, 300, { size: 84, color: gold, stroke: '#1a1222', sw: 12 });
});

module.exports = scenes;
