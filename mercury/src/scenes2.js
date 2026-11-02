// Part 2 (3:31 - end): the honest twist (Uranus), backward sunrise, shrinking planet, the ice, verdict, teaser.
const L = require('./lib');
const { W, H, E, inv, clamp, lerp, rng, hash, noise1, circle, ell, rr, text, rgrad, vgrad, line } = L;
const G = require('./guy');
const S = require('./space');
const T = require('./timing');
const A = (p, after = 0) => T.at(p, after);
const C = (p, after = 0) => T.at(p, after) - .12;
const RIM_HOT = 'rgba(255,160,60,.9)', RIM_COLD = 'rgba(110,160,255,.9)';

function titleCard(ctx, t, o = {}) {
  S.stars(ctx, t);
  text(ctx, 'WHY MERCURY IS THE', 960, 380, { size: 70, weight: 900, color: '#fff', track: 4, stroke: 'rgba(0,0,0,.6)', sw: 12 });
  text(ctx, 'COLDEST PLANET?', 960, 520, { size: 120, weight: 900, color: '#9fdcff', stroke: '#0a1a33', sw: 14 });
}
function stamp(ctx, t, t0, s, x, y, col = '#ff4a3d', rot = -.12, size = 90) { if (t < t0) return; const k = clamp((t - t0) / .18); const sc = lerp(2.2, 1, E.out(k)); ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc); ctx.globalAlpha *= k; ctx.font = L.font(size, 900); const w = ctx.measureText(s).width + 60;
  ctx.strokeStyle = col; ctx.lineWidth = 10; rr(ctx, -w / 2, -size * .75, w, size * 1.5, 16); ctx.stroke(); text(ctx, s, 0, 4, { size, weight: 900, color: col }); ctx.restore(); }
function crackedGround(ctx, t) { S.surface(ctx, t, 'twilight'); const r = rng(8); ctx.save(); ctx.strokeStyle = 'rgba(0,0,0,.85)'; ctx.lineWidth = 6; for (let i = 0; i < 7; i++) { let x = r() * W, y = 740 + r() * 260; ctx.beginPath(); ctx.moveTo(x, y); for (let j = 0; j < 8; j++) { x += (r() - .5) * 140; y += (r() - .3) * 40; ctx.lineTo(x, y); } ctx.stroke(); } ctx.restore(); }
function crater(ctx, t, o = {}) { // cross-section of a polar crater; o.sun (low-angle light), o.ice, o.layer
  S.stars(ctx, t);
  const g = vgrad(ctx, 560, H, [[0, '#6b5a4c'], [1, '#2a211a']]); ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(0, 600); ctx.lineTo(380, 590); ctx.quadraticCurveTo(470, 520, 540, 600); ctx.quadraticCurveTo(700, 900, 960, 905); ctx.quadraticCurveTo(1220, 900, 1380, 600); ctx.quadraticCurveTo(1450, 520, 1540, 590); ctx.lineTo(W, 600); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  if (o.sun) { // low sun from the left: light hits rims, floor stays in shadow
    S.sun(ctx, -40, 470, 70, t, { glow: .8 });
    ctx.save(); ctx.globalCompositeOperation = 'screen'; const lg = ctx.createLinearGradient(0, 470, 1500, 560); lg.addColorStop(0, 'rgba(255,220,150,.35)'); lg.addColorStop(1, 'rgba(255,220,150,0)'); ctx.fillStyle = lg; ctx.beginPath(); ctx.moveTo(0, 430); ctx.lineTo(1600, 520); ctx.lineTo(1600, 610); ctx.lineTo(0, 520); ctx.closePath(); ctx.fill(); ctx.restore();
    ctx.fillStyle = 'rgba(255,200,120,.5)'; ctx.beginPath(); ctx.moveTo(1380, 600); ctx.quadraticCurveTo(1440, 525, 1540, 590); ctx.lineTo(1540, 610); ctx.quadraticCurveTo(1440, 560, 1385, 620); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,10,.55)'; ctx.beginPath(); ctx.moveTo(540, 600); ctx.quadraticCurveTo(700, 900, 960, 905); ctx.quadraticCurveTo(1220, 900, 1380, 600); ctx.lineTo(1300, 640); ctx.lineTo(560, 640); ctx.closePath(); ctx.fill();
  }
  if (o.ice) { const k = o.ice; ctx.save(); ctx.globalAlpha = k; ctx.fillStyle = '#bfe8ff'; ctx.beginPath(); ctx.moveTo(760, 860); ctx.quadraticCurveTo(960, 920, 1160, 860); ctx.quadraticCurveTo(960, 880, 760, 860); ctx.fill(); ell(ctx, 960, 880, 200, 22); ctx.fill();
    ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 960, 880, 5, 260, [[0, `rgba(150,220,255,${.5 * (.7 + .3 * Math.sin(t * 2))})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(660, 700, 600, 300); ctx.restore(); }
  if (o.layer) { ctx.save(); ctx.globalAlpha = o.layer; ctx.fillStyle = '#2b2622'; ell(ctx, 960, 868, 210, 16); ctx.fill(); ctx.restore(); }
}

const scenes = [
  // ---------------- THE HONEST PART ----------------
  { s: C('now i have to be honest'), cam: [1.0, 1.06, 960, 540], draw(ctx, t) {
      titleCard(ctx, t);
      G.guy(ctx, 1640, 990, .38, S.astro(t, { look: -.6, mood: t > A('the title of this') ? 'awkward' : 'tired', flip: 1 }));
      if (t > A("and that's the feeling")) { const k = E.back(clamp((t - A("and that's the feeling")) / .35)); ctx.save(); ctx.translate(1520, 450); ctx.scale(k, k); text(ctx, '*', 0, 0, { size: 160, weight: 900, color: '#ffd34a' }); ctx.restore(); S.typeOn(ctx, t, A("and that's the feeling") + .3, '*it FEELS like the coldest', 960, 660, { size: 44, color: '#ffd34a' }); }
      S.typeOn(ctx, t, A('because no other planet'), 'No other planet loses heat this violently this close to the Sun', 960, 800, { size: 36, color: 'rgba(255,255,255,.85)' });
    } },
  { s: C("but if we're talking"), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      ctx.fillStyle = 'rgba(8,12,24,.85)'; rr(ctx, 260, 180, 1400, 720, 30); ctx.fill(); ctx.strokeStyle = 'rgba(233,185,73,.6)'; ctx.lineWidth = 3; ctx.stroke();
      text(ctx, 'COLDEST TEMPERATURE EVER RECORDED', 960, 250, { size: 40, weight: 900, color: '#e9b949', track: 3 });
      const tu = A('record belongs to uranus');
      const row = (y, rank, kind, name, val, t0, col) => { if (t < t0) return; const k = E.out(clamp((t - t0) / .5)); ctx.save(); ctx.globalAlpha = k; ctx.translate((1 - k) * 80, 0); text(ctx, rank, 360, y, { size: 64, weight: 900, color: col }); S.planet(ctx, 520, y, 64, kind, { light: -1, dark: .4 }); text(ctx, name, 620, y, { size: 56, weight: 900, color: '#fff', align: 'left' }); text(ctx, val, 1580, y, { size: 64, weight: 900, color: col, align: 'right' }); ctx.restore(); };
      row(420, '#1', 'uranus', 'URANUS', '−224°C', tu, '#9fdcff');
      row(640, '#?', 'mercury', 'MERCURY (night)', '−180°C', tu + 1.4, '#ffb347');
      if (t > tu + .3) { const k = E.back(clamp((t - tu - .3) / .4)); ctx.save(); ctx.translate(1200, 420); ctx.scale(k, k); L.chip(ctx, t, tu + .3, 'RECORD', 0, -70, { size: 30, bg: '#e9b949' }); ctx.restore(); }
      S.factChip(ctx, t, A('lowest temperature'), "LOWEST IN A PLANET'S ATMOSPHERE", 960, 960, { bg: '#9fdcff' });
    } },
  { s: C("so mercury doesn't win"), cam: [1.0, 1.04, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const tn = A("doesn't win by the numbers"); S.kinetic(ctx, t, tn, "DOESN'T WIN BY NUMBERS", 960, 170, { size: 60, until: A('it wins by shock') - .1 });
      S.kinetic(ctx, t, A('it wins by shock'), 'IT WINS BY SHOCK', 960, 170, { size: 80, color: '#ff5a4f' });
      S.sun(ctx, 80, 600, 130, t); const xM = 330, xU = 1760;
      S.planet(ctx, xM, 600, 22, 'mercury', { light: -1, ice: clamp((t - A('still freezes')) / 1) });
      const tf = A('far far away'); const p = E.inOut(clamp((t - tf + .6) / 1.6));
      if (t > tf - .6) { ctx.save(); ctx.setLineDash([14, 12]); ctx.strokeStyle = 'rgba(255,255,255,.4)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(xM, 700); ctx.lineTo(lerp(xM, xU, p), 700); ctx.stroke(); ctx.restore(); S.planet(ctx, lerp(xM, xU, p), 600, 46, 'uranus', { light: -1 }); S.label(ctx, '≈ 2.9 BILLION KM', 1100, 760, { size: 40, alpha: p }); }
      if (t > A('being cold is what')) S.label(ctx, 'cold = expected', xU - 40, 500, { size: 34, color: '#9fdcff' });
      S.label(ctx, 'MERCURY', xM, 660, { size: 30, color: '#ffb347' });
      if (t > A('right next to the fire')) { S.factChip(ctx, t, A('right next to the fire'), 'NEXT TO THE FIRE... STILL FREEZES', 700, 400, { bg: '#ffb347' }); }
      S.kinetic(ctx, t, A('so disturbing'), 'DISTURBING.', 960, 920, { size: 80, color: '#ff5a4f' });
    } },
  { s: C("and i haven't even told"), cam: [1.0, 1.12, 960, 600], shake: [[A('not peaceful', 245), .5, 10]], draw(ctx, t) {
      crackedGround(ctx, t);
      G.guy(ctx, 760, 930, .5, S.astro(t, { look: .6, mood: 'worried', rim: RIM_COLD }));
      stamp(ctx, t, A('not peaceful', 245), 'NOT PEACEFUL', 1300, 420);
    } },

  // ---------------- THE BACKWARD SUNRISE ----------------
  { s: C("let's talk about the sunrise"), cam: [1.0, 1.04, 960, 560], draw(ctx, t) {
      const p = clamp((t - A('the sun comes up')) / 3.6); const day = Math.sin(p * Math.PI);
      ctx.fillStyle = vgrad(ctx, 0, H, [[0, `rgb(${lerp(20, 110, day) | 0},${lerp(30, 180, day) | 0},${lerp(70, 255, day) | 0})`], [1, `rgb(${lerp(60, 220, day) | 0},${lerp(50, 210, day) | 0},${lerp(90, 200, day) | 0})`]]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#2f5a3a'; ctx.fillRect(0, 860, W, 220);
      ctx.save(); ctx.setLineDash([10, 14]); ctx.strokeStyle = 'rgba(255,255,255,.5)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(960, 860, 700, 600, 0, Math.PI, 0); ctx.stroke(); ctx.restore();
      if (p > 0) { const a = Math.PI + p * Math.PI; S.sun(ctx, 960 + Math.cos(a) * 700, 860 + Math.sin(a) * 600, 60, t); }
      ctx.fillStyle = '#2f5a3a'; ctx.fillRect(0, 860, W, 220);
      S.typeOn(ctx, t, A("let's talk about the sunrise"), "LET'S TALK ABOUT THE SUNRISE", 960, 170, { size: 56, until: A('on earth the sun') });
      S.label(ctx, 'EARTH:  UP  →  ACROSS  →  DOWN', 960, 960, { size: 46, alpha: clamp((t - A('the sun comes up')) / .5) });
      stamp(ctx, t, A('simple'), 'SIMPLE.', 1500, 300, '#7fd99a', -.08, 70);
    } },
  { s: C('on mercury if you stand'), cam: [1.0, 1.08, 960, 600], draw(ctx, t) {
      // sun path: rise -> stop -> back down -> stop -> rise again
      const k = [[A('the sun rises', 257), 0], [A('then it stops', 257), 1], [A('slowly moves backward'), 1], [A('sets again'), .3], [A('stops once more'), .3], [A('turns around', 262), .3], [A('rises again', 262) + 1.2, 1.1]];
      let h = 0; for (let i = 0; i < k.length - 1; i++) { const [ta, ha] = k[i], [tb, hb] = k[i + 1]; if (t >= ta) h = lerp(ha, hb, E.inOut(clamp((t - ta) / Math.max(.3, tb - ta)))); }
      ctx.fillStyle = '#04050c'; ctx.fillRect(0, 0, W, H); S.stars(ctx, t);
      S.surface(ctx, t, 'twilight');
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, 650); ctx.clip(); S.sun(ctx, 1380 - h * 140, 700 - h * 300, 80, t, { glow: .5 + h * .5 }); ctx.restore();
      G.guy(ctx, 560, 930, .5, S.astro(t, { look: .7, lookY: -.6, mood: t > A('then it stops', 257) ? 'shock' : 'tired', rim: RIM_HOT, rimDX: 7 }));
      const lab = [['RISES', A('the sun rises', 257)], ['STOPS', A('then it stops', 257)], ['GOES BACK', A('slowly moves backward')], ['STOPS', A('stops once more')], ['RISES AGAIN', A('rises again', 262)]];
      lab.forEach(([s, t0], i) => S.kinetic(ctx, t, t0, s, 1500, 320, { size: 70, color: '#ffd34a', until: (lab[i + 1] || [0, 1e9])[1] - .05 }));
      S.typeOn(ctx, t, A('appears to change direction'), 'THE SUN CHANGES DIRECTION', 960, 440, { size: 60, color: '#fff' });
    } },
  { s: C('this happens because'), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); const fx = 760, cy = 560, a = 520, b = 420, c = Math.sqrt(a * a - b * b) * .9; const cx = fx + c;
      S.orbit(ctx, cx, cy, a, b, .4); S.sun(ctx, fx, cy, 70, t);
      const ang = Math.PI + Math.sin(t * .8) * .6; const mx = cx + Math.cos(ang) * a, my = cy + Math.sin(ang) * b;
      for (let i = 1; i < 6; i++) { const aa = ang - i * .05; ctx.fillStyle = `rgba(255,180,80,${.3 - i * .05})`; circle(ctx, cx + Math.cos(aa) * a, cy + Math.sin(aa) * b, 30); ctx.fill(); }
      S.planet(ctx, mx, my, 34, 'mercury', { light: 1 }); S.label(ctx, 'CLOSEST TO SUN = FASTEST', mx + 40, my - 80, { size: 30, align: 'left', alpha: clamp((t - A('closest to the sun', 270)) / .4) });
      const gauge = (y, lab, v, col, t0) => { if (t < t0) return; const p = E.out(clamp((t - t0) / .8)); text(ctx, lab, 1320, y - 34, { size: 34, weight: 900, color: '#fff', align: 'left' }); ctx.fillStyle = 'rgba(255,255,255,.1)'; rr(ctx, 1320, y, 460, 40, 20); ctx.fill(); ctx.fillStyle = col; rr(ctx, 1320, y, 460 * v * p, 40, 20); ctx.fill(); };
      gauge(380, 'ORBIT SPEED', .95, '#ffb347', A('how fast')); gauge(520, 'SPIN SPEED', .25, '#9fdcff', A('how slowly'));
      S.kinetic(ctx, t, A('the orbit wins'), 'THE ORBIT WINS', 1550, 720, { size: 70, color: '#ffb347' });
      S.typeOn(ctx, t, A('seems to go backward'), '→ the Sun seems to go backward', 1550, 820, { size: 38 });
    } },
  { s: C('imagine watching that'), cam: [1.3, 1.5, 700, 560], draw(ctx, t) {
      S.surface(ctx, t, 'twilight');
      const h = .55 + Math.sin(t * 1.4) * .12; ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, 650); ctx.clip(); S.sun(ctx, 1200, 700 - h * 300, 70, t, { glow: .8 }); ctx.restore();
      G.guy(ctx, 620, 930, .5, S.astro(t, { look: .7, lookY: -.7, mood: 'worried', rim: RIM_HOT, rimDX: 7 }));
      S.typeOn(ctx, t, A('a sunrise that hesitates'), 'A SUNRISE THAT HESITATES', 820, 400, { size: 54, color: '#ffd34a' });
    } },

  // ---------------- THE SHRINKING PLANET ----------------
  { s: C('and the surface is even stranger'), cam: [1.0, 1.1, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -200, 300, 260, t, { glow: .6 });
      S.planet(ctx, 960, 620, 300, 'mercury', { light: -1, dark: .55 });
      const a = (t - A('when scientists')) * .6; const r = 420; if (t > A('when scientists') - .5) { S.orbit(ctx, 960, 620, r, r * .32, .3); S.messenger(ctx, 960 + Math.cos(a) * r, 620 + Math.sin(a) * r * .32, .7, t); }
      S.factChip(ctx, t, A('messenger'), 'NASA MESSENGER (2011–2015)', 960, 190, { bg: '#c9ccd3' });
      S.typeOn(ctx, t, A('and the surface is even stranger'), 'THE SURFACE IS EVEN STRANGER', 960, 960, { size: 50, until: A('when scientists') });
    } },
  { s: C('they found long cliffs'), cam: [1.0, 1.08, 960, 560], draw(ctx, t) {
      S.surface(ctx, t, 'twilight');
      // a long scarp running across the landscape
      ctx.fillStyle = '#2a221c'; ctx.beginPath(); ctx.moveTo(0, 820); for (let i = 0; i <= 40; i++) ctx.lineTo(i * 48, 760 - Math.sin(i * .3) * 20 - (noise1(i * .5) * 14)); ctx.lineTo(W, 800); ctx.lineTo(W, 900); ctx.lineTo(0, 900); ctx.fill();
      ctx.fillStyle = '#4a3e34'; ctx.beginPath(); ctx.moveTo(0, 820); for (let i = 0; i <= 40; i++) ctx.lineTo(i * 48, 760 - Math.sin(i * .3) * 20 - (noise1(i * .5) * 14)); ctx.lineTo(W, 690); ctx.lineTo(0, 700); ctx.fill();
      const tl = A('hundreds of kilometers'), th = A('more than a kilometer');
      if (t > tl) { const p = E.out(clamp((t - tl) / 1)); S.arrow(ctx, 960, 620, lerp(960, 1800, p), 620, '#ffd34a', 6); S.arrow(ctx, 960, 620, lerp(960, 120, p), 620, '#ffd34a', 6); S.label(ctx, 'HUNDREDS OF KM LONG', 960, 570, { color: '#ffd34a', alpha: p }); }
      if (t > th) { const p = E.out(clamp((t - th) / .7)); S.arrow(ctx, 300, 830, 300, lerp(830, 700, p), '#9fdcff', 6); S.label(ctx, '1+ KM HIGH', 420, 760, { color: '#9fdcff', align: 'left', alpha: p }); }
      const tw = A("aren't made by wind"); if (t > tw) { S.label(ctx, 'WIND', 760, 330, { size: 54 }); S.label(ctx, 'WATER', 1160, 330, { size: 54 }); S.strike(ctx, t, A('wind', 298) + .2, 680, 840, 330); S.strike(ctx, t, A('water', 298) + .2, 1060, 1260, 330); }
      S.kinetic(ctx, t, A('by shrinking'), 'SHRINKING', 960, 200, { size: 110, color: '#ff8a3d' });
    } },
  { s: C("mercury's giant iron core"), cam: [1.0, 1.1, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const tc = A('as it cools'); const cool = clamp((t - tc) / 4); const shrink = 1 - cool * .05;
      const R = 330 * (1 - cool * .02), cx = 960, cy = 580;
      // crust with wrinkles
      ctx.fillStyle = '#6b5a4c'; ctx.beginPath(); for (let i = 0; i <= 120; i++) { const a = i / 120 * Math.PI * 2; const rr2 = R + Math.sin(a * 23) * 6 * cool + Math.sin(a * 41) * 4 * cool; i ? ctx.lineTo(cx + Math.cos(a) * rr2, cy + Math.sin(a) * rr2) : ctx.moveTo(cx + Math.cos(a) * rr2, cy + Math.sin(a) * rr2); } ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#8a7462'; circle(ctx, cx, cy, R * .92); ctx.fill();
      const coreR = R * .85 * shrink * .97; ctx.fillStyle = rgrad(ctx, cx, cy, 10, coreR, [[0, `rgb(255,${lerp(220, 120, cool) | 0},${lerp(120, 60, cool) | 0})`], [1, `rgb(${lerp(230, 140, cool) | 0},${lerp(90, 50, cool) | 0},30)`]]); circle(ctx, cx, cy, coreR); ctx.fill();
      S.label(ctx, 'GIANT IRON CORE', cx, cy, { size: 44, alpha: clamp((t - A('iron core')) / .4) });
      S.factChip(ctx, t, A('billions of years', 302), 'COOLING FOR BILLIONS OF YEARS', cx, 215, { bg: '#ff8a3d' });
      if (t > tc) for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; S.arrow(ctx, cx + Math.cos(a) * (R + 140), cy + Math.sin(a) * (R + 140), cx + Math.cos(a) * (R + 50), cy + Math.sin(a) * (R + 50), 'rgba(255,255,255,.75)', 6); }
      const ta = A('drying apple'); if (t > ta - .8) { const k = E.back(clamp((t - ta + .8) / .4)); ctx.save(); ctx.translate(1600, 700); ctx.scale(k, k); ctx.fillStyle = 'rgba(8,10,20,.85)'; rr(ctx, -200, -200, 400, 400, 30); ctx.fill();
        const dry = clamp((t - ta) / 1.5); ctx.fillStyle = `rgb(${lerp(220, 150, dry) | 0},${lerp(60, 70, dry) | 0},${lerp(60, 40, dry) | 0})`; ctx.beginPath(); for (let i = 0; i <= 80; i++) { const a = i / 80 * Math.PI * 2; const rr2 = 110 * (1 - dry * .18) + Math.sin(a * 17) * 10 * dry; i ? ctx.lineTo(Math.cos(a) * rr2, 20 + Math.sin(a) * rr2) : ctx.moveTo(Math.cos(a) * rr2, 20 + Math.sin(a) * rr2); } ctx.fill(); ctx.strokeStyle = '#5a3a20'; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(0, -80); ctx.lineTo(10, -130); ctx.stroke(); text(ctx, 'LIKE A DRYING APPLE', 0, 170, { size: 26, weight: 900, color: '#fff' }); ctx.restore(); }
    } },
  { s: C('mercury is getting smaller'), cam: [1.15, 1.0, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); const k = 1 - .06 * clamp((t - A('mercury is getting smaller')) / 3); S.planet(ctx, 960, 580, 260 * k, 'mercury', { light: -1 });
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + .4; S.arrow(ctx, 960 + Math.cos(a) * 420, 580 + Math.sin(a) * 420, 960 + Math.cos(a) * 300, 580 + Math.sin(a) * 300, 'rgba(255,180,80,.8)', 7); }
      S.kinetic(ctx, t, A('getting smaller'), 'MERCURY IS SHRINKING', 960, 220, { size: 80 });
      S.kinetic(ctx, t, A('not in a movie'), 'NOT IN A MOVIE.', 600, 880, { size: 56 }); S.kinetic(ctx, t, A('right now', 313), 'RIGHT NOW.', 1360, 880, { size: 70, color: '#ff5a4f' });
    } },
  { s: C('so think about what this planet'), cam: [1.0, 1.04, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); const tiles = [['BURNING HEAT', A('burning heat'), '#ff6a2a', 'fire'], ['DEEP FREEZING', A('deep freezing'), '#4f8cff', 'ice'], ['CRACKING CRUST', A('cracking from the inside'), '#8a6c52', 'crack'], ['BACKWARD SUN', A('moves backward', 320), '#ffc24a', 'sun']];
      tiles.forEach(([lab, t0, col, kind], i) => { if (t < t0) return; const x = 260 + (i % 2) * 720, y = 160 + Math.floor(i / 2) * 380; const k = E.back(clamp((t - t0) / .35)); ctx.save(); ctx.translate(x + 350, y + 170); ctx.scale(k, k); ctx.translate(-350, -170);
        ctx.fillStyle = col; rr(ctx, 0, 0, 700, 340, 26); ctx.fill(); ctx.fillStyle = 'rgba(0,0,0,.25)'; rr(ctx, 0, 260, 700, 80, 0); ctx.fill();
        if (kind === 'fire') for (let j = 0; j < 6; j++) { ctx.fillStyle = '#ffd34a'; ctx.beginPath(); const fx = 120 + j * 95, fh = 100 + 40 * Math.sin(t * 6 + j); ctx.moveTo(fx - 35, 230); ctx.quadraticCurveTo(fx, 230 - fh * 1.4, fx + 35, 230); ctx.fill(); }
        if (kind === 'ice') for (let j = 0; j < 7; j++) { ctx.fillStyle = 'rgba(220,240,255,.9)'; ctx.beginPath(); ctx.moveTo(80 + j * 90, 40); ctx.lineTo(110 + j * 90, 40); ctx.lineTo(95 + j * 90, 120 + (j % 3) * 30); ctx.fill(); }
        if (kind === 'crack') { ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(60, 130); ctx.lineTo(200, 110); ctx.lineTo(280, 180); ctx.lineTo(420, 120); ctx.lineTo(520, 200); ctx.lineTo(650, 150); ctx.stroke(); }
        if (kind === 'sun') { S.sun(ctx, 350 + Math.sin(t * 2) * 120, 140, 50, t); S.arrow(ctx, 470, 220, 230, 220, '#fff', 6); }
        text(ctx, lab, 350, 300, { size: 46, weight: 900, color: '#fff' }); ctx.restore(); });
      stamp(ctx, t, A('peaceful', 322), 'PEACEFUL?', 960, 540, '#fff', -.05, 80);
      stamp(ctx, t, A('not even close'), 'NOT EVEN CLOSE.', 960, 540, '#ff4a3d', .06, 90);
    } },

  // ---------------- THE IMPOSSIBLE ICE ----------------
  { s: C('but i promised you'), cam: [1.0, 1.15, 960, 620], draw(ctx, t) {
      S.stars(ctx, t); ctx.fillStyle = '#141826'; ctx.beginPath(); ctx.moveTo(0, 640); ctx.quadraticCurveTo(960, 560, W, 640); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
      ctx.fillStyle = '#05060b'; ell(ctx, 960, 760, 520, 120); ctx.fill(); ctx.strokeStyle = '#2a3048'; ctx.lineWidth = 10; ell(ctx, 960, 760, 520, 120); ctx.stroke();
      const open = clamp((t - A("and now it's time")) / .6); const g = .5 + .5 * Math.sin(t * 2.4);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 960, 780, 10, 320 + open * 200, [[0, `rgba(120,200,255,${(.5 + open * .4) * g})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(400, 400, 1120, 700); ctx.restore();
      // padlock
      ctx.save(); ctx.translate(960, 560 - open * 60); ctx.globalAlpha = 1 - open * .9; ctx.fillStyle = '#e9b949'; rr(ctx, -70, -20, 140, 110, 18); ctx.fill(); ctx.strokeStyle = '#e9b949'; ctx.lineWidth = 18; ctx.beginPath(); ctx.arc(0, -20 - open * 40, 46, Math.PI, 0); ctx.stroke(); ctx.restore();
      S.typeOn(ctx, t, A('something frozen', 320), 'SOMETHING FROZEN THAT SHOULD NOT EXIST', 960, 220, { size: 52 });
      S.kinetic(ctx, t, A("and now it's time"), "NOW IT'S TIME.", 960, 330, { size: 80, color: '#9fdcff' });
    } },
  { s: C('for decades astronomers'), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.planet(ctx, 260, 760, 300, 'earth', { atmo: 1, light: 1, dark: .4 }); S.radarDish(ctx, 420, 520, .9, t);
      const mx = 1450, my = 480, mr = 230; S.planet(ctx, mx, my, mr, 'mercury', { light: -1, dark: .5 }); S.radarWaves(ctx, 520, 400, mx - mr, my, t);
      const tp = A('near the poles'); if (t > tp) { const k = clamp((t - tp) / .8) * (.7 + .3 * Math.sin(t * 4)); ctx.save(); ctx.globalCompositeOperation = 'screen'; for (const [dx, dy] of [[-30, -mr * .88], [40, -mr * .84], [-20, mr * .86], [30, mr * .9]]) { ctx.fillStyle = rgrad(ctx, mx + dx, my + dy, 2, 40, [[0, `rgba(255,255,255,${k})`], [1, 'rgba(255,255,255,0)']]); circle(ctx, mx + dx, my + dy, 40); ctx.fill(); } ctx.restore(); S.label(ctx, 'BRIGHT PATCHES AT THE POLES', mx, my + mr + 70, { size: 34, alpha: clamp((t - tp) / .5) }); }
      S.factChip(ctx, t, A('radar at mercury'), 'RADAR FROM EARTH', 420, 280, { bg: '#7fd99a' });
      S.typeOn(ctx, t, A('looked a lot like ice'), 'LOOKED A LOT LIKE ICE', 1450, 150, { size: 52, color: '#9fdcff' });
    } },
  { s: C('ice on the planet'), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -100, 300, 240, t, { glow: .7 });
      S.kinetic(ctx, t, A('ice on the planet'), 'ICE?', 960, 220, { size: 150, color: '#9fdcff' });
      S.typeOn(ctx, t, A('on the planet closest'), 'ON THE PLANET CLOSEST TO THE SUN?', 960, 360, { size: 50 });
      const tn = A('no way'); for (let i = 0; i < 3; i++) { const x = 600 + i * 360; G.guy(ctx, x, 1000, .38, { t, seed: i, mood: t > tn ? 'blank' : 'tired', look: Math.sin(t * 7 + i) * (t > tn ? .9 : 0), shirt: '#f4f1ea', outfit(c) { c.fillStyle = '#fff'; c.fillRect(-108, -420, 216, 10); } }); if (t > tn) L.bubble(ctx, t, tn + i * .15, 'NO WAY.', x + 80, 560, x, 680, { size: 38, until: A('something else', 344) + 1 }); }
    } },
  { s: C('then messenger arrived'), cam: [1.0, 1.15, 960, 560], flash: false, draw(ctx, t) {
      S.stars(ctx, t); const cx = 960, cy = 600, R = 300; S.planet(ctx, cx, cy, R, 'mercury', { light: -1, dark: .45 });
      const ta = A('messenger arrived'); const p = E.out(clamp((t - ta) / 2)); const a = (t - ta) * .8; const r = lerp(900, 420, p);
      S.orbit(ctx, cx, cy, 420, 140, .25 * p); S.messenger(ctx, cx + Math.cos(a) * r, cy + Math.sin(a) * r * .33 - (1 - p) * 300, .6, t);
      const tm = A('mapped the poles'); if (t > tm) { const k = clamp((t - tm) / 1.6); ctx.save(); circle(ctx, cx, cy, R); ctx.clip(); ctx.fillStyle = 'rgba(120,220,255,.25)'; ctx.fillRect(cx - R, cy - R, R * 2, R * 2 * k); ctx.strokeStyle = 'rgba(120,220,255,.9)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(cx - R, cy - R + R * 2 * k); ctx.lineTo(cx + R, cy - R + R * 2 * k); ctx.stroke();
        ctx.globalCompositeOperation = 'screen'; for (const [dx, dy] of [[-40, -R * .88], [50, -R * .84], [-30, R * .86], [20, R * .9]]) { if (cy + dy < cy - R + R * 2 * k) { ctx.fillStyle = rgrad(ctx, cx + dx, cy + dy, 2, 46, [[0, 'rgba(160,230,255,1)'], [1, 'rgba(160,230,255,0)']]); circle(ctx, cx + dx, cy + dy, 46); ctx.fill(); } } ctx.restore(); }
      S.kinetic(ctx, t, A('changed everything'), 'CHANGED EVERYTHING', 960, 250, { size: 64, until: A('mercury has water ice') - .1 });
      if (t > A('mercury has water ice')) { const tw = A('mercury has water ice'); ctx.fillStyle = `rgba(255,255,255,${.6 * (1 - clamp((t - tw) / .4))})`; ctx.fillRect(0, 0, W, H); S.kinetic(ctx, t, tw, 'MERCURY HAS WATER ICE', 960, 250, { size: 100, color: '#9fdcff', stroke: '#0a1a33' }); }
    } },
  { s: C("here's how it's possible"), cam: [1.0, 1.04, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      const axis = (x, y, r, kind, tilt, lab, val) => { S.planet(ctx, x, y, r, kind, { light: -1, rot: tilt, atmo: kind === 'earth' ? 1 : 0 }); ctx.save(); ctx.translate(x, y); ctx.rotate(tilt); ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.setLineDash([16, 10]); ctx.beginPath(); ctx.moveTo(0, -r - 90); ctx.lineTo(0, r + 90); ctx.stroke(); ctx.restore(); S.label(ctx, lab, x, y + r + 140, { size: 44 }); S.label(ctx, val, x, y + r + 190, { size: 38, color: '#ffd34a' }); };
      axis(600, 480, 180, 'earth', .41, 'EARTH', 'TILT 23.4°');
      if (t > A('barely tilts') - .3) axis(1320, 480, 150, 'mercury', .0006, 'MERCURY', 'TILT ≈ 0.03°');
      S.kinetic(ctx, t, A('almost perfectly upright'), 'ALMOST PERFECTLY UPRIGHT', 960, 160, { size: 60 });
    } },
  { s: C('that means near the poles'), cam: [1.0, 1.1, 900, 600], draw(ctx, t) {
      S.surface(ctx, t, 'night');
      const h = .12 + Math.sin(t * .4) * .02; ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, 660); ctx.clip(); S.sun(ctx, 1600, 690 - h * 300, 70, t, { glow: .8 }); ctx.restore();
      ctx.save(); ctx.globalCompositeOperation = 'screen'; const g = ctx.createLinearGradient(1600, 650, 0, 760); g.addColorStop(0, 'rgba(255,200,130,.35)'); g.addColorStop(1, 'rgba(255,200,130,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(1600, 620); ctx.lineTo(0, 700); ctx.lineTo(0, 780); ctx.lineTo(1600, 680); ctx.fill(); ctx.restore();
      G.guy(ctx, 560, 930, .45, S.astro(t, { look: .8, rim: RIM_HOT, rimDX: 7 }));
      S.typeOn(ctx, t, A('always sits low'), 'AT THE POLES: THE SUN STAYS LOW', 900, 290, { size: 52 });
      S.kinetic(ctx, t, A('never climbs high'), 'IT NEVER CLIMBS HIGH', 900, 390, { size: 60, color: '#ffd34a' });
    } },
  { s: C('so inside some deep craters'), cam: [1.0, 1.06, 960, 600], draw(ctx, t) {
      crater(ctx, t, { sun: true });
      S.typeOn(ctx, t, A("the sun's light never reaches"), "SUNLIGHT NEVER REACHES THE FLOOR", 960, 200, { size: 50 });
      S.kinetic(ctx, t, A('not for a day'), 'NOT FOR A DAY.', 960, 320, { size: 56, until: A('not for a year') - .05 });
      S.kinetic(ctx, t, A('not for a year'), 'NOT FOR A YEAR.', 960, 320, { size: 56, until: A('not for billions') - .05 });
      S.kinetic(ctx, t, A('not for billions'), 'NOT FOR BILLIONS OF YEARS.', 960, 320, { size: 64, color: '#9fdcff' });
      S.label(ctx, 'SHADOW', 960, 820, { size: 40, color: 'rgba(160,190,255,.8)', alpha: clamp((t - A("the sun's light never")) / .5) });
    } },
  { s: C('these are permanently shadowed'), cam: [1.0, 1.08, 960, 640], draw(ctx, t) {
      crater(ctx, t, { sun: true });
      S.kinetic(ctx, t, A('permanently shadowed'), 'PERMANENTLY SHADOWED CRATERS', 960, 200, { size: 60, color: '#9fdcff' });
      if (t > A('colder than minus') - .3) S.thermo(ctx, 1540, 900, 300, lerp(0, -170, E.out(clamp((t - A('colder than minus') + .3) / 1.4))), -250, 500, { size: 54, w: 36 });
    } },
  { s: C('any water that fell'), cam: [1.0, 1.06, 960, 620], draw(ctx, t) {
      const tc = A('delivered by comets'); const hit = tc + 1.3;
      crater(ctx, t, { sun: true, ice: clamp((t - hit - .4) / 1.5) });
      if (t < hit) { const p = clamp((t - tc + .6) / 1.9); S.comet(ctx, lerp(1900, 1000, p), lerp(100, 860, p), 1, Math.atan2(760, -900), t); }
      else { const p = clamp((t - hit) / 1.2); if (p < 1) { ctx.fillStyle = `rgba(255,255,255,${.7 * (1 - p)})`; circle(ctx, 1000, 870, 40 + p * 220); ctx.fill(); for (let i = 0; i < 14; i++) { const a = -Math.PI * (i / 13); ctx.fillStyle = `rgba(200,230,255,${1 - p})`; circle(ctx, 1000 + Math.cos(a) * 300 * p, 870 + Math.sin(a) * 200 * p, 8); ctx.fill(); } } }
      S.factChip(ctx, t, tc, 'COMETS & ASTEROIDS', 1500, 430, { bg: '#c9e8ff' });
      S.kinetic(ctx, t, A('frozen in the dark'), 'FROZEN IN THE DARK', 960, 200, { size: 66, color: '#9fdcff' });
      S.typeOn(ctx, t, A('safe from the sun'), 'safe from the Sun, on the planet nearest to it', 960, 300, { size: 42 });
    } },
  { s: C('some of that ice is even'), cam: [1.2, 1.4, 960, 760], draw(ctx, t) {
      crater(ctx, t, { sun: true, ice: 1, layer: clamp((t - A('dark layer') ) / 1.2) });
      S.typeOn(ctx, t, A('dark layer'), 'COVERED BY A DARK LAYER', 960, 560, { size: 46 });
      S.factChip(ctx, t, A('protect it'), 'IT MAY PROTECT THE ICE', 960, 640, { bg: '#9fdcff' });
    } },
  { s: C('so think about the final picture'), cam: [1.0, 1.06, 960, 600], draw(ctx, t) {
      crater(ctx, t, { sun: true, ice: 1 });
      const tl = A('rocks that could melt lead'); if (t > tl - .4) { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 1460, 570, 10, 300, [[0, 'rgba(255,110,30,.8)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(1100, 300, 820, 500); ctx.restore(); S.label(ctx, '+430°C', 1500, 460, { size: 60, color: '#ff8a3d' }); S.label(ctx, 'melts lead', 1500, 520, { size: 32 }); }
      const tk = A('a few kilometers away'); if (t > tk) { const p = E.out(clamp((t - tk) / .8)); S.arrow(ctx, 1380, 700, lerp(1380, 1080, p), lerp(700, 830, p), '#fff', 5); S.label(ctx, 'A FEW KM', 1300, 790, { size: 34, alpha: p }); }
      const ti = A('ice that has lasted'); if (t > ti) { S.label(ctx, '−170°C ICE', 960, 760, { size: 44, color: '#9fdcff' }); S.label(ctx, 'billions of years old', 960, 960, { size: 32 }); }
      if (t > A('fire and ice')) { const t0 = A('fire and ice'); S.kinetic(ctx, t, t0, 'FIRE', 760, 220, { size: 120, color: '#ff8a3d' }); S.kinetic(ctx, t, t0 + .25, '&', 960, 220, { size: 90 }); S.kinetic(ctx, t, t0 + .45, 'ICE', 1160, 220, { size: 120, color: '#9fdcff' }); S.typeOn(ctx, t, A('on the same tiny planet'), 'ON THE SAME TINY PLANET', 960, 330, { size: 44 }); }
    } },

  // ---------------- THE VERDICT ----------------
  { s: C('so was the title true'), cam: [1.0, 1.04, 960, 540], draw(ctx, t) {
      titleCard(ctx, t); S.strike(ctx, t, A("isn't the coldest") + .2, 560, 1370, 520, '#ff4a3d');
      S.typeOn(ctx, t, A('so was the title true'), 'SO... WAS THE TITLE TRUE?', 960, 200, { size: 50, color: '#ffd34a' });
      stamp(ctx, t, A("isn't the coldest") + .3, 'NOT THE COLDEST', 960, 760, '#ff4a3d', -.06, 70);
    } },
  { s: C("but it's the only planet"), cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -260, 560, 380, t, { glow: .8 }); S.planet(ctx, 960, 580, 280, 'mercury', { light: -1, hot: 1, ice: 1, dark: .25 });
      S.kinetic(ctx, t, A('the hottest day'), 'THE HOTTEST DAY', 560, 200, { size: 60, color: '#ff8a3d' });
      S.kinetic(ctx, t, A('one of the coldest nights'), 'ONE OF THE COLDEST NIGHTS', 1360, 200, { size: 56, color: '#9fdcff' });
      S.typeOn(ctx, t, A('happen on the same ground'), 'SAME GROUND. SAME SUN.', 960, 960, { size: 60 });
    } },
  { s: C('and it has no air to save'), cam: [1.0, 1.12, 960, 560], draw(ctx, t) {
      S.surface(ctx, t, 'night'); S.frost(ctx, .5);
      S.kinetic(ctx, t, A('no air to save'), 'NO AIR.', 960, 300, { size: 110 });
      S.kinetic(ctx, t, A('no blanket', 420), 'NO BLANKET.', 960, 460, { size: 110 });
      S.kinetic(ctx, t, A('no mercy'), 'NO MERCY.', 960, 620, { size: 130, color: '#ff4a3d' });
    } },
  { s: C('so the next time someone'), cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S.stars(ctx, t);
      S.kinetic(ctx, t, A('the closest planet', 423), 'CLOSEST', 640, 480, { size: 110 }); S.kinetic(ctx, t, A('must be the hottest'), '= HOTTEST', 1260, 480, { size: 110, color: '#ff8a3d' });
      S.strike(ctx, t, A("you'll know the truth") , 360, 1600, 470);
      S.typeOn(ctx, t, A('the truth is stranger'), 'THE TRUTH IS STRANGER.', 960, 680, { size: 64, color: '#9fdcff' });
    } },
  { s: C('and if mercury already feels'), cam: [1.0, 1.12, 960, 560], draw(ctx, t) {
      S.stars(ctx, t); S.sun(ctx, -200, 560, 300, t, { glow: .7 }); S.planet(ctx, 420, 560, 50, 'mercury', { light: -1, hot: .6 }); S.label(ctx, 'MERCURY', 420, 650, { size: 30, color: '#ffb347' });
      const tw = A('which planet'); const reveal = clamp((t - A("even though it's farther")) / 2);
      if (t > tw - .3) { const k = E.back(clamp((t - tw + .3) / .5)); ctx.save(); ctx.translate(1250, 560); ctx.scale(k, k); ctx.fillStyle = rgrad(ctx, 0, 0, 100, 360, [[0, 'rgba(255,120,40,.5)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(-400, -400, 800, 800);
        S.planet(ctx, 0, 0, 200, 'venus', { light: -1, dark: .9 - reveal * .5 }); ctx.fillStyle = `rgba(0,0,0,${.85 - reveal * .5})`; circle(ctx, 0, 0, 202); ctx.fill(); text(ctx, '?', 0, 0, { size: 220, weight: 900, color: '#ffd34a', alpha: 1 - reveal * .3 }); ctx.restore(); }
      S.typeOn(ctx, t, A('hotter than mercury'), 'WHICH PLANET IS HOTTER THAN MERCURY?', 960, 250, { size: 54 });
      if (t > A("even though it's farther")) { const p = E.out(clamp((t - A("even though it's farther")) / 1)); S.arrow(ctx, 520, 820, lerp(520, 1080, p), 820, '#fff', 5); S.label(ctx, 'FARTHER FROM THE SUN', 800, 880, { size: 32, alpha: p }); }
      S.kinetic(ctx, t, A('even more terrifying'), 'EVEN MORE TERRIFYING', 960, 900, { size: 64, color: '#ff5a4f' });
      if (t > T.END - 3) { const a = clamp((t - (T.END - 3)) / .6); L.chip(ctx, t, T.END - 3, 'SUBSCRIBE FOR PART 2', 1500, 300, { size: 40, bg: '#ff3b30', color: '#fff' }); ctx.globalAlpha = 1; }
    } },
];
module.exports = scenes;
