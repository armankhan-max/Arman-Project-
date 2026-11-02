// Part 1 (0:00 - 3:31): hook, where Mercury is, day vs night, reasons #1 (air), #2 (time), #3 (soil).
const L = require('./lib');
const { W, H, E, inv, clamp, lerp, rng, hash, noise1, circle, ell, rr, text, rgrad, vgrad, line } = L;
const G = require('./guy');
const S = require('./space');
const T = require('./timing');
const A = (p, after = 0) => T.at(p, after);
const C = (p, after = 0) => T.at(p, after) - .12; // cut slightly before the word
const RIM_HOT = 'rgba(255,160,60,.9)', RIM_COLD = 'rgba(110,160,255,.9)';

function cracks(ctx, t, t0, k, seed = 2) { if (t < t0) return; const p = clamp((t - t0) / 1.2) * k; const r = rng(seed); ctx.save(); ctx.strokeStyle = 'rgba(10,6,4,.9)'; ctx.lineWidth = 5; ctx.lineCap = 'round';
  for (let i = 0; i < 6; i++) { let x = 200 + r() * 1500, y = 760 + r() * 220; ctx.beginPath(); ctx.moveTo(x, y); for (let j = 0; j < 8 * p; j++) { x += (r() - .5) * 120; y += (r() - .3) * 40; ctx.lineTo(x, y); } ctx.stroke(); } ctx.restore(); }
function dust(ctx, t, t0, x, y, n = 14) { const p = clamp((t - t0) / 1.2); if (p <= 0 || p >= 1) return; for (let i = 0; i < n; i++) { const a = Math.PI + (i / (n - 1)) * Math.PI; ctx.fillStyle = `rgba(200,150,110,${.6 * (1 - p)})`; circle(ctx, x + Math.cos(a) * 220 * p, y + Math.sin(a) * 40 * p - Math.sin(p * Math.PI) * 30, 14 + p * 26); ctx.fill(); } }
function sunIcon(ctx, x, y, r, k = 1) { ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.fillStyle = '#ffc24a'; circle(ctx, 0, 0, r); ctx.fill(); ctx.strokeStyle = '#ffc24a'; ctx.lineWidth = r * .18; ctx.lineCap = 'round'; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; ctx.beginPath(); ctx.moveTo(Math.cos(a) * r * 1.35, Math.sin(a) * r * 1.35); ctx.lineTo(Math.cos(a) * r * 1.75, Math.sin(a) * r * 1.75); ctx.stroke(); } ctx.restore(); }
function bar(ctx, t, t0, x, y, w, h, col, labelL, labelR, o = {}) { if (t < t0) return; const p = E.out(clamp((t - t0) / (o.dur || .8))); ctx.fillStyle = 'rgba(255,255,255,.08)'; rr(ctx, x, y, w, h, h / 2); ctx.fill(); ctx.fillStyle = col; rr(ctx, x, y, Math.max(h, w * p * (o.frac ?? 1)), h, h / 2); ctx.fill();
  text(ctx, labelL, x, y - 30, { size: o.size || 34, weight: 800, color: '#fff', align: 'left' }); if (labelR) text(ctx, labelR, x + Math.max(h, w * (o.frac ?? 1) * p) + 20, y + h / 2, { size: o.size || 34, weight: 900, color: col, align: 'left', alpha: p }); }
function tilePanel(ctx, t, t0, x, y, w, h, fn, o = {}) { if (t < t0) return; const k = E.back(clamp((t - t0) / .4)); ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.scale(k, k); ctx.translate(-w / 2, -h / 2); ctx.globalAlpha *= clamp(k);
  ctx.save(); rr(ctx, 0, 0, w, h, 24); ctx.clip(); fn(ctx, w, h); ctx.restore(); ctx.strokeStyle = o.edge || 'rgba(255,255,255,.35)'; ctx.lineWidth = 4; rr(ctx, 0, 0, w, h, 24); ctx.stroke(); ctx.restore(); }
function blanketArc(ctx, cx, cy, r, k, t) { if (k <= 0) return; ctx.save(); ctx.globalAlpha = k; ctx.lineWidth = 46; const a0 = Math.PI * (1.0 + (1 - k) * .45), a1 = Math.PI * (2.0 - (1 - k) * .45);
  const g = ctx.createLinearGradient(cx - r, cy, cx + r, cy); g.addColorStop(0, '#d9605a'); g.addColorStop(.5, '#f2a65a'); g.addColorStop(1, '#d9605a'); ctx.strokeStyle = g; ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 3; ctx.setLineDash([12, 10]); ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1); ctx.stroke(); ctx.restore(); }
function particles(ctx, t, cx, cy, r0, r1, n, col, seed = 1, drift = 0) { const r = rng(seed); for (let i = 0; i < n; i++) { const a = r() * Math.PI * 2 + t * .1 * (r() - .5), d = r0 + r() * (r1 - r0) + drift * ((t * 40 + i * 37) % 300); ctx.fillStyle = col; circle(ctx, cx + Math.cos(a) * d, cy + Math.sin(a) * d, 4 + r() * 3); ctx.fill(); } }
function heatUp(ctx, x0, x1, yb, t, k, col = '255,90,40') { if (k <= 0) return; for (let i = 0; i < 9; i++) { const x = lerp(x0, x1, (i + .5) / 9), p = ((t * .5 + i * .13) % 1); S.arrow(ctx, x, yb - p * 380, x, yb - p * 380 - 120, `rgba(${col},${k * (1 - p)})`, 8); } }
function calPage(ctx, x, y, s, label, k) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha *= k; ctx.fillStyle = '#1b2235'; rr(ctx, -110, -130, 220, 260, 18); ctx.fill(); ctx.fillStyle = '#ff5a4f'; rr(ctx, -110, -130, 220, 64, 18); ctx.fill(); ctx.fillRect(-110, -90, 220, 24); text(ctx, label, 0, -96, { size: 34, weight: 900, color: '#fff' });
  for (let i = 0; i < 20; i++) { ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(-90 + (i % 5) * 38, -40 + Math.floor(i / 5) * 38, 26, 26); } ctx.restore(); }
function stickman(ctx, x, y, s, t, o = {}) { G.guy(ctx, x, y, s, { t, seed: 1.1, ...o }); }

const scenes = [
  // ---------------- HOOK ----------------
  { s: 0, cam: [1.08, 1.18, 1000, 540], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -160, 540, 560, t);
      S.planet(ctx, 1150, 560, 190, 'mercury', { light: -1, hot: .5 + .5 * clamp(t / 4), dark: .6 });
      S.heatHaze(ctx, clamp(t / 5));
      S.factChip(ctx, t, A('closest'), 'CLOSEST TO THE SUN', 1150, 300, { bg: '#ffb347' });
      S.kinetic(ctx, t, A('burning'), 'BURNING', 1560, 470, { size: 92, color: '#ff8a3d' });
      S.kinetic(ctx, t, A('glowing'), 'GLOWING', 1560, 600, { size: 92, color: '#ffd34a' });
      S.kinetic(ctx, t, A('melting'), 'MELTING', 1560, 730, { size: 92, color: '#ff4a2a' });
      if (t > A('melting') + .2) for (let i = 0; i < 5; i++) { const p = ((t - A('melting')) * .8 + i * .2) % 1; ctx.fillStyle = `rgba(255,74,42,${1 - p})`; ell(ctx, 1420 + i * 60, 780 + p * 120, 9, 14); ctx.fill(); }
    } },
  { s: C('but the moment'), cam: [1.0, 1.1, 960, 560], draw(ctx, t) {
      const t0 = A('leaves'), p = clamp((t - t0) / 2.2);
      S.surface(ctx, t, 'day'); if (p > 0) { ctx.save(); ctx.globalAlpha = p; S.surface(ctx, t, 'night'); ctx.restore(); }
      ctx.save(); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, 600); ctx.lineTo(0, 600); ctx.closePath(); ctx.clip();
      S.sun(ctx, 1500, lerp(300, 820, E.inOut(p)), 120, t, { glow: 1 - p * .7 }); ctx.restore();
      G.guy(ctx, 620, 930, .5, S.astro(t, { look: .6, mood: p > .6 ? 'worried' : 'tired', rim: p > .5 ? RIM_COLD : RIM_HOT, rimDX: p > .5 ? -7 : 7 }));
      S.frost(ctx, clamp((t - A('coldest', 6)) / 1.6) * .8);
      S.typeOn(ctx, t, A('coldest', 6) - .6, 'ONE OF THE COLDEST PLACES', 1180, 330, { size: 64, color: '#cfe8ff' });
    } },
  { s: C('why mercury is the coldest'), cam: [1.12, 1.0, 960, 540], flash: true, shake: [[A('why mercury is the coldest') + .4, .3, 12]], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -300, 540, 420, t, { glow: .7 });
      S.planet(ctx, 960, 560, 230, 'mercury', { light: -1, hot: 1, ice: 1, dark: .4 });
      S.kinetic(ctx, t, A('why mercury is the coldest'), 'WHY MERCURY IS THE', 960, 220, { size: 70, track: 4 });
      S.kinetic(ctx, t, A('coldest', 11.6), 'COLDEST PLANET?', 960, 900, { size: 120, color: '#9fdcff', stroke: '#0a1a33' });
    } },
  { s: C("and it's not peaceful"), cam: [1.0, 1.12, 960, 600], shake: [[A('peaceful', 13), .6, 10], [A('repeat'), .8, 14]], draw(ctx, t) {
      S.surface(ctx, t, 'night'); cracks(ctx, t, A('peaceful', 13) - .2, 1); cracks(ctx, t, A('repeat'), 1, 7);
      G.guy(ctx, 700, 930, .5, S.astro(t, { look: .3, mood: 'panic', lean: Math.sin(t * 9) * .05, rim: RIM_COLD }));
      S.kinetic(ctx, t, A('peaceful', 13), 'NOT PEACEFUL.', 1300, 330, { size: 96, color: '#ff5a4f' });
      S.kinetic(ctx, t, A('repeat'), 'I REPEAT.', 1300, 470, { size: 70, rot: -.04 });
    } },
  { s: C('stay with me'), cam: [1.0, 1.2, 960, 600], draw(ctx, t) {
      S.stars(ctx, t);
      ctx.fillStyle = '#141826'; ctx.beginPath(); ctx.moveTo(0, 640); ctx.quadraticCurveTo(960, 560, W, 640); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
      ctx.fillStyle = '#05060b'; ell(ctx, 960, 760, 520, 120); ctx.fill(); ctx.strokeStyle = '#2a3048'; ctx.lineWidth = 10; ell(ctx, 960, 760, 520, 120); ctx.stroke();
      const g = .5 + .5 * Math.sin(t * 2.4); ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 960, 780, 10, 320, [[0, `rgba(120,200,255,${.5 * g})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(500, 500, 920, 500); ctx.restore();
      S.kinetic(ctx, t, A('something frozen') , '?', 960, 740, { size: 220, color: '#9fdcff' });
      S.typeOn(ctx, t, A('should not exist'), 'SHOULD NOT EXIST', 960, 300, { size: 80, color: '#fff', track: 6 });
      S.factChip(ctx, t, A('by the end'), 'REVEALED AT THE END', 960, 430, { bg: '#ff5a4f', color: '#fff' });
    } },

  // ---------------- WHERE IS MERCURY ----------------
  { s: C("let's start with where"), cam: [1.0, 1.04, 960, 540], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, 60, 560, 200, t);
      const xE = 1720, xM = 60 + (58 / 150) * (xE - 60);
      S.orbit(ctx, 60, 560, xM - 60, (xM - 60) * .3, .25); S.orbit(ctx, 60, 560, xE - 60, (xE - 60) * .3, .25);
      const tE = A('earth sits'), tM = A('mercury sits');
      if (t > tE) { S.planet(ctx, xE, 560, 46, 'earth', { atmo: 1, light: -1 }); S.label(ctx, 'EARTH', xE, 650); const p = E.out(clamp((t - tE) / 1.2)); S.arrow(ctx, 270, 760, lerp(270, xE, p), 760, '#6fb4ff', 6); S.counter(ctx, t, tE, tE + 1.4, 0, 150, v => `${Math.round(v)} MILLION KM`, 1000, 830, { size: 56, color: '#6fb4ff' }); }
      if (t > tM) { S.planet(ctx, xM, 560, 26, 'mercury', { light: -1, hot: .6 }); S.label(ctx, 'MERCURY', xM, 630, { color: '#ffb347' }); const p = E.out(clamp((t - tM) / 1)); S.arrow(ctx, 270, 380, lerp(270, xM, p), 380, '#ffb347', 6); S.counter(ctx, t, tM, tM + 1.2, 0, 58, v => `ONLY ${Math.round(v)} MILLION KM`, 560, 300, { size: 52, color: '#ffb347' }); }
      S.typeOn(ctx, t, A("let's start with where"), 'WHERE IS MERCURY?', 960, 170, { size: 54, color: 'rgba(255,255,255,.8)', until: tE });
    } },
  { s: C("that's so close that"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(958, 200, 4, 700);
      S.planet(ctx, 500, 700, 110, 'earth', { atmo: 1, light: -1 }); S.label(ctx, 'EARTH', 500, 870);
      S.planet(ctx, 1420, 700, 80, 'mercury', { light: -1, hot: .8 }); S.label(ctx, 'MERCURY', 1420, 870, { color: '#ffb347' });
      sunIcon(ctx, 500, 400, 46, E.back(clamp((t - A('sunlight')) / .4))); S.label(ctx, '1×', 500, 500, { size: 54, alpha: clamp((t - A('sunlight')) / .4) });
      const t7 = A('seven times'); for (let i = 0; i < 7; i++) { const k = E.back(clamp((t - t7 - i * .12) / .35)); if (k > 0) sunIcon(ctx, 1420 + (i - 3) * 82, 400 - (i % 2) * 40, 30, k); }
      if (t > t7) S.label(ctx, '7×', 1420, 520, { size: 72, color: '#ffc24a' });
      S.kinetic(ctx, t, A('seven times', 33), 'SEVEN TIMES STRONGER', 960, 170, { size: 74, color: '#ffc24a' });
    } },
  { s: C("it's only a little bigger"), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      S.planet(ctx, 1700, 600, 420, 'earth', { atmo: .8, light: -1 }); S.label(ctx, 'EARTH', 1500, 220, { alpha: .8 });
      const k1 = E.back(clamp((t - A("it's only")) / .5)), k2 = E.back(clamp((t - A('our moon')) / .5));
      if (k1 > 0) { S.planet(ctx, 720, 600, 160 * k1, 'mercury', { light: -1 }); S.label(ctx, 'MERCURY', 720, 820, { color: '#ffb347' }); S.label(ctx, '4,880 km', 720, 870, { size: 28, color: 'rgba(255,255,255,.7)' }); }
      if (k2 > 0) { S.planet(ctx, 260, 640, 116 * k2, 'moon', { light: -1 }); S.label(ctx, 'MOON', 260, 820); S.label(ctx, '3,475 km', 260, 870, { size: 28, color: 'rgba(255,255,255,.7)' }); }
      S.typeOn(ctx, t, A('a little bigger'), 'ONLY A LITTLE BIGGER THAN OUR MOON', 760, 200, { size: 50 });
      S.kinetic(ctx, t, A('small rocky'), 'SMALL.', 430, 330, { size: 70, color: '#ffb347' }); S.kinetic(ctx, t, A('rocky', 37), 'ROCKY.', 840, 330, { size: 70, color: '#ffb347' });
    } },
  { s: C('right next to a giant'), cam: [1.0, 1.2, 1000, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -380, 540, 820, t); S.planet(ctx, 1280, 560, 70, 'mercury', { light: -1, hot: .7 });
      S.kinetic(ctx, t, A('giant ball'), 'A GIANT BALL OF FIRE', 1350, 260, { size: 70, color: '#ffd34a' });
    } },

  // ---------------- THE DAY SIDE ----------------
  { s: C('now imagine you land'), cam: [1.0, 1.08, 960, 600], draw(ctx, t) {
      const heat = clamp((t - A('430') + .5) / 2.5);
      S.surface(ctx, t, 'day', { heat: .6 + heat * .8 }); S.sun(ctx, 1700, 230, 130, t);
      const tl = A('land') + .8; const y = t < tl ? lerp(300, 930, E.out(clamp((t - A('land') + .4) / 1.2))) : 930;
      G.guy(ctx, 560, y, .52, S.astro(t, { look: .6, rim: RIM_HOT, rimDX: 7, visor: .6, mood: heat > .5 ? 'worried' : 'tired' }));
      if (t < tl) { for (let i = 0; i < 3; i++) { ctx.fillStyle = `rgba(255,220,180,${.5})`; circle(ctx, 520 + i * 40, y + 20 + Math.random() * 30, 16); ctx.fill(); } }
      dust(ctx, t, tl, 560, 930);
      if (t > A('430') - .4) { S.thermo(ctx, 1120, 820, 440, lerp(20, 430, E.out(clamp((t - A('430') + .4) / 1.6)))); }
      if (t > A('melt lead')) { const p = clamp((t - A('melt lead')) / 2.5); const bx = 1520, by = 930; ctx.fillStyle = '#8d939c'; ctx.beginPath(); ctx.moveTo(bx - 90 - p * 70, by); ctx.lineTo(bx + 90 + p * 70, by); ctx.quadraticCurveTo(bx + 70, by - 90 * (1 - p) - 10, bx, by - 100 * (1 - p) - 12); ctx.quadraticCurveTo(bx - 70, by - 90 * (1 - p) - 10, bx - 90 - p * 70, by); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,.3)'; ell(ctx, bx - 20, by - 60 * (1 - p) - 6, 30, 6); ctx.fill();
        S.factChip(ctx, t, A('melt lead') + .3, 'LEAD MELTS AT 327°C', 1520, 760, { bg: '#c9ccd3' }); }
      if (t > A('every rock')) { const r = rng(9); ctx.save(); ctx.globalCompositeOperation = 'screen'; for (let i = 0; i < 18; i++) { const x = r() * W, yy = 760 + r() * 260; ctx.fillStyle = rgrad(ctx, x, yy, 2, 50, [[0, `rgba(255,140,40,${.6 * clamp((t - A('every rock')) / 1)})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(x - 50, yy - 50, 100, 100); } ctx.restore(); }
      S.kinetic(ctx, t, A('melt lead') - .2, 'HOT ENOUGH TO MELT LEAD', 1100, 200, { size: 64, color: '#ff8a3d', until: A('the sky is black') - .3 });
    } },
  { s: C('the sky is black'), cam: [1.4, 1.55, 760, 520], draw(ctx, t) {
      S.surface(ctx, t, 'day', { heat: 1.3 });
      G.guy(ctx, 760, 930, .55, S.astro(t, { look: .7, lookY: -.6, rim: RIM_HOT, rimDX: 8, visor: 1, mood: 'cringe', rh: [200, -800], bendF: -1 }));
      const k = clamp((t - A('blinding')) / .5); S.sun(ctx, 1250, 260, 110 + k * 30, t, { glow: 1 + k });
      ctx.save(); ctx.globalCompositeOperation = 'screen'; for (let i = 1; i < 5; i++) { ctx.fillStyle = `rgba(255,220,150,${.18 * k})`; circle(ctx, 1250 - i * 110, 260 + i * 70, 20 + i * 12); ctx.fill(); } ctx.fillStyle = `rgba(255,250,230,${.55 * k})`; ctx.fillRect(0, 0, W, H); ctx.restore();
      S.kinetic(ctx, t, A('black', 53), 'BLACK SKY', 520, 260, { size: 60 });
      S.kinetic(ctx, t, A('blinding'), 'BLINDING LIGHT', 520, 360, { size: 60, color: '#ffd34a' });
    } },

  // ---------------- WALK TO THE NIGHT ----------------
  { s: C('now walk away'), cam: [1.0, 1.25, 1150, 600], draw(ctx, t) {
      const bx = 1000;
      S.surface(ctx, t, 'day'); ctx.save(); ctx.beginPath(); ctx.rect(bx, 0, W - bx, H); ctx.clip(); S.surface(ctx, t, 'night'); ctx.restore();
      const g = ctx.createLinearGradient(bx - 120, 0, bx + 120, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.5, 'rgba(0,0,0,.55)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(bx - 120, 640, 240, 440);
      ctx.save(); ctx.setLineDash([16, 14]); ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(bx, 640); ctx.lineTo(bx, 1000); ctx.stroke(); ctx.restore();
      S.label(ctx, 'DAY', bx - 220, 600, { color: '#ffb347', size: 46 }); S.label(ctx, 'NIGHT', bx + 220, 600, { color: '#9fdcff', size: 46 });
      const x = lerp(260, 1420, clamp((t - A('now walk away')) / (A('and here is where') - A('now walk away') + .8)));
      const cold = x > bx; G.guy(ctx, x, 930, .45, S.astro(t, { walk: x < 1420 ? t * 5 : null, look: .6, rim: cold ? RIM_COLD : RIM_HOT, rimDX: cold ? -7 : 7, mood: cold ? 'worried' : 'tired' }));
      S.typeOn(ctx, t, A('the line between'), 'THE LINE BETWEEN DAY AND NIGHT', 1150, 330, { size: 50 });
      if (t > A('turns strange')) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - A('turns strange')) / 2) * .6})`; ctx.fillRect(0, 0, W, H); }
    } },

  // ---------------- THE NIGHT SIDE ----------------
  { s: C('on the night side'), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.surface(ctx, t, 'night');
      const shiver = Math.sin(t * 40) * 3;
      G.guy(ctx, 380 + shiver, 930, .5, S.astro(t, { look: .6, mood: 'worried', rim: RIM_COLD, lh: [40, -470], rh: [40, -470], bendB: -1, bendF: -1 }));
      const tv = A('180'); S.thermo(ctx, 720, 820, 440, lerp(20, -180, E.out(clamp((t - tv + 1) / 1.8))), -250, 500);
      S.frost(ctx, clamp((t - tv) / 2) * .7);
      const tf = A('freezer'), ta = A('antarctica');
      if (t > A("that's colder than") - .2) { ctx.fillStyle = 'rgba(6,10,22,.75)'; rr(ctx, 1040, 230, 780, 560, 30); ctx.fill();
        S.label(ctx, 'HOW COLD?', 1430, 290, { size: 40, color: '#9fdcff', track: 4 });
        bar(ctx, t, tf - .3, 1090, 400, 680, 44, '#9fd4ff', 'Your freezer', '−18°C', { frac: 18 / 180 });
        bar(ctx, t, ta - .3, 1090, 540, 680, 44, '#6fa8ff', 'Antarctica (record)', '−89°C', { frac: 89 / 180 });
        bar(ctx, t, ta + .9, 1090, 680, 680, 44, '#4f6fff', 'Mercury at night', '−180°C', { frac: 1, size: 36 }); }
    } },
  { s: C('so in one planet'), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const x = 760, top = 230, bot = 880; const yAt = v => lerp(bot, top, (v + 200) / 650);
      ctx.fillStyle = 'rgba(255,255,255,.1)'; rr(ctx, x - 40, top - 20, 80, bot - top + 40, 40); ctx.fill();
      const g = ctx.createLinearGradient(0, top, 0, bot); g.addColorStop(0, '#ff4a2a'); g.addColorStop(.45, '#ffb347'); g.addColorStop(.7, '#9fd4ff'); g.addColorStop(1, '#4f6fff'); ctx.fillStyle = g; rr(ctx, x - 28, top, 56, bot - top, 28); ctx.fill();
      S.label(ctx, '+430°C  DAY', x + 80, yAt(430), { align: 'left', color: '#ff8a3d', size: 46 }); S.label(ctx, '−180°C  NIGHT', x + 80, yAt(-180), { align: 'left', color: '#9fd4ff', size: 46 });
      const p = E.out(clamp((t - A('600') + .3) / 1)); ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x - 80, yAt(430)); ctx.lineTo(x - 120, yAt(430)); ctx.lineTo(x - 120, lerp(yAt(430), yAt(-180), p)); ctx.lineTo(x - 80, lerp(yAt(430), yAt(-180), p)); ctx.stroke();
      S.counter(ctx, t, A('600') - .3, A('600') + 1, 0, 610, v => `${Math.round(v)}°`, 420, 560, { size: 110 });
      S.label(ctx, 'DIFFERENCE', 420, 650, { size: 40, alpha: p });
    } },
  { s: C("that's not a weather"), cam: [1.0, 1.1, 960, 540], draw(ctx, t) {
      S.stars(ctx, t);
      const tw = A('two different worlds');
      if (t < tw - .1) { sunIcon(ctx, 760, 520, 60); ctx.fillStyle = '#dfe6f2'; for (const [dx, dy, r] of [[1080, 540, 70], [1150, 500, 80], [1230, 540, 64]]) { circle(ctx, dx, dy, r); ctx.fill(); }
        S.strike(ctx, t, A('weather change') + .2, 640, 1340, 520); S.kinetic(ctx, t, A('weather change') - .1, 'NOT A WEATHER CHANGE', 960, 260, { size: 70 }); }
      else { S.planet(ctx, 960, 560, 260, 'mercury', { light: -1, hot: 1, ice: 1, dark: .2 });
        S.kinetic(ctx, t, tw, 'TWO WORLDS', 960, 200, { size: 90 }); S.kinetic(ctx, t, A('one surface'), 'ONE SURFACE', 960, 920, { size: 70, color: '#ffd34a' });
        S.label(ctx, 'FIRE', 580, 560, { color: '#ff8a3d', size: 54, alpha: clamp((t - tw) / .4) }); S.label(ctx, 'ICE', 1340, 560, { color: '#9fdcff', size: 54, alpha: clamp((t - tw) / .4) }); }
    } },
  { s: C('so the big question'), cam: [1.0, 1.15, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, 120, 560, 240, t, { glow: .9 }); S.planet(ctx, 760, 560, 60, 'mercury', { light: -1, ice: .6 });
      const k = E.back(clamp((t - A('big question')) / .4)); ctx.save(); ctx.translate(1350, 520); ctx.scale(k, k); ctx.rotate(Math.sin(t * 2) * .05); text(ctx, '?', 0, 0, { size: 360, weight: 900, color: '#9fdcff', stroke: '#0a1a33', sw: 16 }); ctx.restore();
      S.typeOn(ctx, t, A('how can a planet'), 'HOW CAN A PLANET SO CLOSE', 960, 260, { size: 60 });
      S.typeOn(ctx, t, A('get this cold'), 'GET THIS COLD?', 960, 860, { size: 80, color: '#9fdcff' });
    } },

  // ---------------- REASON #1: AIR ----------------
  { s: C('the first answer'), cam: [1.0, 1.1, 960, 560], draw(ctx, t) {
      ctx.fillStyle = vgrad(ctx, 0, H, [[0, '#9fd2ff'], [1, '#dff1ff']]); ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#7cc47a'; ctx.fillRect(0, 900, W, 200);
      const br = .5 + .5 * Math.sin(t * 2.2); stickman(ctx, 700, 920, .55, t, { mood: 'asleep', look: .6, headRot: -.05 * br });
      for (let i = 0; i < 8; i++) { const p = ((t * .5 + i / 8) % 1); ctx.fillStyle = `rgba(255,255,255,${.8 * Math.sin(p * Math.PI)})`; circle(ctx, 1100 - p * 300, 470 + Math.sin(p * 9 + i) * 30, 9); ctx.fill(); }
      S.kinetic(ctx, t, A('air.'), 'AIR.', 1320, 420, { size: 160, color: '#2f6fc0', stroke: '#fff' });
      S.typeOn(ctx, t, A("you're breathing"), "something you're breathing right now", 960, 180, { size: 46, color: '#123366' });
    } },
  { s: C("earth's atmosphere"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -120, 540, 260, t, { glow: .8 });
      const cx = 1100, cy = 620; S.planet(ctx, cx, cy, 230, 'earth', { atmo: 1.4, light: -1, dark: .55 });
      blanketArc(ctx, cx, cy, 290, E.out(clamp((t - A('blanket')) / .9)), t);
      S.kinetic(ctx, t, A('blanket'), 'A BLANKET', 1100, 200, { size: 80, color: '#f2a65a' });
      const tt = A('traps heat'); if (t > tt) { const p = (t - tt); for (let i = 0; i < 4; i++) { const k = ((p * .6 + i * .25) % 1); const y = 420 + i * 70; const x = k < .5 ? lerp(250, cx - 270, k * 2) : lerp(cx - 270, 520, (k - .5) * 2); ctx.fillStyle = k < .5 ? '#ffd34a' : '#ff6a3d'; circle(ctx, x, y, 12); ctx.fill(); } S.factChip(ctx, t, tt + .3, 'TRAPS HEAT', 520, 840, { bg: '#ff8a3d' }); S.factChip(ctx, t, A('through the night') , 'KEEPS IT AT NIGHT', 520, 920, { bg: '#2f6fc0', color: '#fff' }); }
    } },
  { s: C("that's why you can step"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      ctx.fillStyle = vgrad(ctx, 0, H, [[0, '#2b2a6a'], [.6, '#c9688a'], [1, '#f2a65a']]); ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#2a3a2e'; ctx.fillRect(0, 880, W, 200);
      ctx.fillStyle = '#3d2c2a'; rr(ctx, 1300, 560, 360, 320, 6); ctx.fill(); ctx.fillStyle = '#5a3a30'; ctx.beginPath(); ctx.moveTo(1270, 570); ctx.lineTo(1480, 420); ctx.lineTo(1690, 570); ctx.fill(); ctx.fillStyle = '#ffd08a'; ctx.fillRect(1380, 640, 90, 90); ctx.fillRect(1520, 640, 90, 90);
      ctx.fillStyle = '#f4f1ea'; circle(ctx, 300, 220, 50); ctx.fill();
      stickman(ctx, 820, 900, .5, t, { mood: 'happy', look: .4, lh: [-200, -700], rh: [200, -700], bendB: -.5, bendF: -.5 });
      S.factChip(ctx, t, A('not freeze'), 'AFTER SUNSET: STILL FINE', 820, 300, { bg: '#7fd99a' });
    } },
  { s: C('mercury has almost no atmosphere'), cam: [1.0, 1.2, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -200, 540, 300, t, { glow: .7 });
      S.planet(ctx, 960, 560, 250, 'mercury', { light: -1 });
      particles(ctx, t, 960, 560, 270, 420, t > A('few scattered') ? 9 : 5, 'rgba(160,210,255,.85)', 3);
      S.kinetic(ctx, t, A('almost no atmosphere'), 'ALMOST NO ATMOSPHERE', 960, 270, { size: 70 });
      S.factChip(ctx, t, A('exosphere'), 'EXOSPHERE', 960, 830, { bg: '#9fdcff', size: 48 });
      S.typeOn(ctx, t, A('closer to empty space'), 'closer to empty space than to air', 960, 900, { size: 40, color: 'rgba(255,255,255,.85)' });
    } },
  { s: C('why is it so thin'), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      S.kinetic(ctx, t, A('why is it so thin'), 'WHY SO THIN?', 960, 170, { size: 70 });
      const tg = A('gravity is weak');
      S.planet(ctx, 520, 600, 260, 'earth', { atmo: 1, light: -1 }); S.label(ctx, 'EARTH', 520, 930);
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; S.arrow(ctx, 520 + Math.cos(a) * 400, 600 + Math.sin(a) * 400, 520 + Math.cos(a) * 290, 600 + Math.sin(a) * 290, 'rgba(120,200,255,.8)', 8); }
      S.planet(ctx, 1380, 600, 100, 'mercury', { light: -1 }); S.label(ctx, 'MERCURY', 1380, 760, { color: '#ffb347' });
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; S.arrow(ctx, 1380 + Math.cos(a) * 150, 600 + Math.sin(a) * 150, 1380 + Math.cos(a) * 118, 600 + Math.sin(a) * 118, 'rgba(255,180,80,.7)', 4); }
      if (t > tg) { particles(ctx, t, 1380, 600, 160, 200, 8, 'rgba(160,210,255,.85)', 5, 1); S.factChip(ctx, t, tg, 'SMALL = WEAK GRAVITY', 1380, 880, { bg: '#ffb347' }); }
    } },
  { s: C('and because the sun keeps'), cam: [1.0, 1.1, 1000, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -100, 560, 360, t);
      const cx = 1250, cy = 560; S.planet(ctx, cx, cy, 160, 'mercury', { light: -1, hot: .4 });
      const r = rng(4); for (let i = 0; i < 70; i++) { const y = 200 + r() * 720, sp = 900 + r() * 700; const x = ((r() * W + t * sp) % (W + 200)) - 100; const nearP = Math.abs(y - cy) < 170 && x > cx - 180 && x < cx; ctx.strokeStyle = r() < .5 ? 'rgba(255,220,120,.7)' : 'rgba(255,150,80,.7)'; ctx.lineWidth = 3; if (!nearP) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 50, y); ctx.stroke(); } }
      for (let i = 0; i < 16; i++) { const p = ((t * .7 + i / 16) % 1); ctx.fillStyle = `rgba(160,210,255,${.9 * (1 - p)})`; circle(ctx, cx + 170 + p * 520, cy + (i - 8) * 18 * (1 + p), 6); ctx.fill(); }
      S.kinetic(ctx, t, A('charged particles'), 'SOLAR WIND', 760, 240, { size: 74, color: '#ffd34a' });
      const tb = A("can't hold onto"); if (t > tb) { const p = E.in(clamp((t - tb) / 2)); ctx.save(); ctx.translate(cx + 120 + p * 600, cy - 220 - p * 200); ctx.rotate(p * 2); ctx.fillStyle = '#e07a5a'; rr(ctx, -90, -60, 180, 120, 14); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.5)'; ctx.setLineDash([10, 8]); ctx.lineWidth = 3; rr(ctx, -80, -50, 160, 100, 10); ctx.stroke(); ctx.restore(); S.typeOn(ctx, t, tb, "Mercury can't hold onto a blanket", 1000, 920, { size: 46 }); }
    } },
  { s: C('so what happens when'), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      const night = t > A('when night comes') - .3; const nk = clamp((t - A('when night comes') + .3) / 1);
      ctx.fillStyle = '#05060c'; ctx.fillRect(0, 0, W, H); S.stars(ctx, t); if (!night) { ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.fillRect(0, 0, W, H); }
      // ground cross-section
      const soak = clamp((t - A('soaks up')) / 2.5) * (1 - nk);
      ctx.fillStyle = vgrad(ctx, 640, H, [[0, `rgb(${lerp(120, 60, nk) | 0},${lerp(80, 70, nk) | 0},${lerp(60, 110, nk) | 0})`], [1, '#1a1410']]); ctx.fillRect(0, 640, W, H);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = vgrad(ctx, 640, 900, [[0, `rgba(255,120,30,${.7 * soak})`], [1, 'rgba(255,60,0,0)']]); ctx.fillRect(0, 640, W, 260); ctx.restore();
      if (!night) { S.sun(ctx, 1600, 200, 110, t); for (let i = 0; i < 7; i++) { const p = ((t * .8 + i / 7) % 1); S.arrow(ctx, 1500 - i * 150, 260 + p * 380, 1500 - i * 150 - 80, 260 + p * 380 + 120, `rgba(255,210,90,${1 - p})`, 7); } }
      if (night) heatUp(ctx, 200, 1720, 630, t, nk);
      S.typeOn(ctx, t, A('nothing stops it'), 'NOTHING STOPS IT FROM LEAVING', 960, 170, { size: 54, until: A('soaks up') });
      S.factChip(ctx, t, A('soaks up'), 'DAY: GROUND SOAKS UP HEAT', 600, 380, { bg: '#ff8a3d', until: A('when night comes') - .3 });
      S.kinetic(ctx, t, A('straight back into space'), 'STRAIGHT BACK INTO SPACE', 960, 170, { size: 60, color: '#ff8a3d' });
      S.kinetic(ctx, t, A('no air to slow'), 'NO AIR', 500, 360, { size: 70 }); S.kinetic(ctx, t, A('no clouds'), 'NO CLOUDS', 960, 360, { size: 70 }); S.kinetic(ctx, t, A('no blanket', 135), 'NO BLANKET', 1420, 360, { size: 70 });
      if (t > A('just rock in a very')) { ctx.fillStyle = `rgba(80,140,255,${.25 * clamp((t - A('just rock in a very')) / 1)})`; ctx.fillRect(0, 640, W, 440); }
    } },
  { s: C('but wait if heat'), cam: [1.0, 1.12, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      S.planet(ctx, 600, 580, 200, 'moon', { light: -1 }); S.label(ctx, 'THE MOON: ALSO NO AIR', 600, 850, { size: 36 });
      const ty = A('second problem'); if (t < ty) { S.typeOn(ctx, t, A('shouldn\'t every planet'), "Shouldn't every airless planet freeze at night?", 960, 180, { size: 46 }); }
      S.kinetic(ctx, t, ty, 'PROBLEM #2', 1350, 420, { size: 100, color: '#ffd34a' });
      if (t > A('about time')) { const k = E.back(clamp((t - A('about time')) / .4)); ctx.save(); ctx.translate(1350, 680); ctx.scale(k, k); ctx.fillStyle = '#f4f1ea'; circle(ctx, 0, 0, 110); ctx.fill(); ctx.strokeStyle = '#121212'; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(0, 0, 110, 0, Math.PI * 2); ctx.stroke(); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(t * 3) * 80, Math.sin(t * 3) * 80); ctx.stroke(); ctx.lineWidth = 14; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(t * .3) * 55, Math.sin(t * .3) * 55); ctx.stroke(); ctx.restore(); S.label(ctx, 'TIME', 1350, 870, { size: 64 }); }
    } },

  // ---------------- REASON #2: TIME ----------------
  { s: C("here's something that sounds"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); const cx = 760, cy = 560; S.sun(ctx, cx, cy, 90, t);
      S.orbit(ctx, cx, cy, 380, 300, .4);
      const t88 = A('88'); const ph = t > t88 ? (t - t88) * .9 : 0; const mx = cx + Math.cos(ph) * 380, my = cy + Math.sin(ph) * 300;
      S.planet(ctx, mx, my, 40, 'mercury', { light: Math.cos(ph) > 0 ? 1 : -1 });
      S.typeOn(ctx, t, A('sounds fake'), 'SOUNDS FAKE. IT\'S TRUE.', 960, 160, { size: 54, until: t88 });
      if (t > t88) { S.counter(ctx, t, t88, t88 + 2, 0, 88, v => `1 YEAR = ${Math.round(v)} EARTH DAYS`, 1440, 300, { size: 50, color: '#ffb347' }); }
      const ts = A('spins very slowly'); if (t > ts) { const k = E.back(clamp((t - ts) / .4)); ctx.save(); ctx.translate(1440, 640); ctx.scale(k, k); S.planet(ctx, 0, 0, 150, 'mercury', { light: -1, rot: (t - ts) * .25 }); ctx.save(); ctx.rotate((t - ts) * .25); ctx.fillStyle = '#ff5a4f'; ctx.fillRect(-3, -200, 6, 60); ctx.beginPath(); ctx.moveTo(3, -200); ctx.lineTo(50, -186); ctx.lineTo(3, -172); ctx.fill(); ctx.restore(); ctx.restore();
        S.counter(ctx, t, A('59'), A('59') + 1.6, 0, 59, v => `1 SPIN = ${Math.round(v)} EARTH DAYS`, 1440, 900, { size: 50, color: '#9fdcff' }); }
    } },
  { s: C('put those two together'), cam: [1.0, 1.04, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      S.typeOn(ctx, t, A('a single day on mercury'), 'ONE DAY ON MERCURY (sunrise → sunrise)', 960, 200, { size: 46 });
      S.counter(ctx, t, A('176'), A('176') + 1.4, 0, 176, v => `${Math.round(v)} EARTH DAYS`, 960, 320, { size: 90, color: '#fff' });
      const x0 = 200, x1 = 1720, y = 520, p = E.inOut(clamp((t - A('176') + .2) / 1.4));
      ctx.fillStyle = 'rgba(255,255,255,.08)'; rr(ctx, x0, y, x1 - x0, 90, 45); ctx.fill();
      const mid = (x0 + x1) / 2; ctx.fillStyle = '#ff9a3d'; rr(ctx, x0, y, Math.max(0, Math.min(mid, lerp(x0, x1, p)) - x0), 90, 45); ctx.fill();
      if (lerp(x0, x1, p) > mid) { ctx.fillStyle = '#1f2e6a'; rr(ctx, mid, y, lerp(x0, x1, p) - mid, 90, 45); ctx.fill(); }
      if (p > .4) { S.label(ctx, 'DAY ≈ 88 days', (x0 + mid) / 2, y + 45, { size: 40 }); } if (p > .9) S.label(ctx, 'NIGHT ≈ 88 days', (mid + x1) / 2, y + 45, { size: 40, color: '#9fdcff' });
      S.factChip(ctx, t, A('two full mercury years'), '= 2 MERCURY YEARS', 960, 690, { bg: '#ffb347' });
      const tm = A('three months of darkness'); if (t > tm - .3) { ['MONTH 1', 'MONTH 2', 'MONTH 3'].forEach((m, i) => { const k = E.back(clamp((t - tm - i * .3) / .35)); if (k > 0) calPage(ctx, 700 + i * 260, 880, .7 * k, m, 1); }); }
    } },
  { s: C('think about that', 175), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const te = A('12 hours'), tm = A('on mercury the surface'); const p2 = E.inOut(clamp((t - tm) / 2.4));
      bar(ctx, t, te - .3, 220, 330, 1480, 70, '#6fb4ff', 'Night on Earth', '~12 hours', { frac: 12 / 2112 + .012 });
      bar(ctx, t, tm, 220, 560, 1480, 70, '#4f6fff', 'Night on Mercury', '~2,100 hours', { frac: .88, dur: 2.4 });
      if (t > A("that's why the night side")) { S.thermo(ctx, 1500, 960, 220, lerp(100, -180, clamp((t - A("that's why the night side")) / 1.5)), -250, 500, { size: 46, w: 34 }); }
      S.kinetic(ctx, t, A('brutally cold'), 'BRUTALLY COLD', 760, 860, { size: 100, color: '#9fdcff' }); S.frost(ctx, clamp((t - A('brutally cold')) / 1) * .7);
    } },

  // ---------------- REASON #3: THE SOIL ----------------
  { s: C("but there's one more trick"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const top = 380; ctx.fillStyle = '#8a6c52'; ctx.fillRect(0, top, W, 60); ctx.fillStyle = vgrad(ctx, top + 60, H, [[0, '#5a4636'], [1, '#2a1f18']]); ctx.fillRect(0, top + 60, W, H);
      const r = rng(6); for (let i = 0; i < 60; i++) { ctx.fillStyle = 'rgba(0,0,0,.2)'; ell(ctx, r() * W, top + 80 + r() * 600, 10 + r() * 30, 6 + r() * 12); ctx.fill(); }
      const thin = clamp((t - A('thin layer')) / 1); const swing = Math.sin(t * 2.2);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = swing > 0 ? `rgba(255,110,30,${.6 * thin * swing})` : `rgba(80,140,255,${.6 * thin * -swing})`; ctx.fillRect(0, top, W, 60); ctx.restore();
      S.factChip(ctx, t, A('terrible conductor'), 'DUST = TERRIBLE HEAT CONDUCTOR', 960, 200, { bg: '#ffb347' });
      S.label(ctx, 'THIN TOP LAYER', 300, top - 40, { size: 32, alpha: thin, align: 'left' });
      const td = A('dig down'); if (t > td) { const p = E.out(clamp((t - td) / 1.2)); ctx.fillStyle = '#c9ccd3'; ctx.fillRect(1300, top - 120, 20, 120 + p * 360); ctx.fillStyle = '#9aa0ad'; ctx.beginPath(); ctx.moveTo(1290, top + p * 360); ctx.lineTo(1330, top + p * 360); ctx.lineTo(1310, top + p * 360 + 40); ctx.fill(); }
      // two gauges: violent surface vs calm below
      const gauge = (x, y, v, lab) => { ctx.fillStyle = 'rgba(0,0,0,.5)'; circle(ctx, x, y, 80); ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(x, y, 80, Math.PI, 0); ctx.stroke(); const a = Math.PI * 1.5 + v * 1.3; ctx.lineWidth = 8; ctx.strokeStyle = v > 0 ? '#ff6a3d' : '#6fa8ff'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * 66, y + Math.sin(a) * 66); ctx.stroke(); text(ctx, lab, x, y + 120, { size: 30, weight: 900, color: '#fff' }); };
      if (t > A('surface is violent') - .3) gauge(560, 560, swing, 'SURFACE: VIOLENT'); if (t > A('just beneath') - .2) gauge(560, 860, swing * .08, 'BELOW: CALM');
    } },
  { s: C('so if you ever had to survive'), cam: [1.0, 1.1, 960, 600], draw(ctx, t) {
      S.surface(ctx, t, 'twilight');
      ctx.fillStyle = '#20180f'; ctx.fillRect(0, 800, W, 300); ctx.fillStyle = '#3a2c1e'; ell(ctx, 960, 920, 520, 120); ctx.fill();
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 960, 900, 10, 400, [[0, 'rgba(255,200,120,.35)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(400, 700, 1120, 400); ctx.restore();
      const tu = A("you'd hide underground"); const y = t > tu ? lerp(700, 980, E.inOut(clamp((t - tu) / 1))) : 700;
      G.guy(ctx, 960, y, .4, S.astro(t, { look: .4, mood: t > tu + 1 ? 'happy' : 'tired', rim: 'rgba(255,200,120,.8)' }));
      ctx.fillStyle = '#4a3a2c'; ctx.fillRect(0, 780, W, 22);
      S.kinetic(ctx, t, A("you wouldn't hide"), 'NOT ON THE SURFACE', 960, 220, { size: 64 }); S.kinetic(ctx, t, tu, 'UNDERGROUND', 960, 340, { size: 90, color: '#ffd08a' });
    } },
];
module.exports = scenes;
