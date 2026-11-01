// The white stick-figure (style from the reference: cream pill body, big round head,
// thin ink outline, heavy tired lids + eye bags), plus POV hands and the phone.
const L = require('./lib');
const { E, clamp, inv, lerp, circle, ell, rr } = L;

const SKIN = '#e7e2d4', BACK = '#bdb8ab', INK = '#121212', BAG = 'rgba(70,66,58,.75)';

function stroke(ctx, w, col) { ctx.lineWidth = w; ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke(); }
function limbPath(ctx, a, c, b) { ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(c[0], c[1], b[0], b[1]); }
function limb(ctx, a, c, b, w, col, sil, ol) {
  limbPath(ctx, a, c, b);
  if (sil) { stroke(ctx, w + ol * 2, sil); return; }
  stroke(ctx, w + ol * 2, INK); limbPath(ctx, a, c, b); stroke(ctx, w, col);
}

// mood -> face recipe
const MOODS = {
  tired: { eye: 'tired', brow: 'flat', mouth: 'frown', bags: 1 },
  sad: { eye: 'tired', brow: 'sad', mouth: 'frown', bags: 1 },
  worried: { eye: 'open', brow: 'sad', mouth: 'wavy', bags: 1 },
  panic: { eye: 'wide', brow: 'sad', mouth: 'o', bags: 1 },
  shock: { eye: 'wide', brow: 'up', mouth: 'o', bags: 0 },
  happy: { eye: 'open', brow: 'up', mouth: 'bigsmile', bags: 0 },
  dream: { eye: 'happy', brow: 'up', mouth: 'bigsmile', bags: 0 },
  sing: { eye: 'happy', brow: 'up', mouth: 'o', bags: 0 },
  shy: { eye: 'happy', brow: 'flat', mouth: 'smallsmile', bags: 0 },
  smile: { eye: 'tired', brow: 'flat', mouth: 'smallsmile', bags: 1 },
  soft: { eye: 'soft', brow: 'sad', mouth: 'smallsmile', bags: 1 },
  cringe: { eye: 'squeeze', brow: 'sad', mouth: 'wavy', bags: 1 },
  asleep: { eye: 'closed', brow: 'flat', mouth: 'smallsmile', bags: 0 },
  blank: { eye: 'tired', brow: 'flat', mouth: 'flat', bags: 1 },
  awkward: { eye: 'open', brow: 'up', mouth: 'grin', bags: 0 },
  laugh: { eye: 'happy', brow: 'up', mouth: 'bigsmile', bags: 0 },
  smirk: { eye: 'tired', brow: 'flat', mouth: 'smirk', bags: 1 },
  cool: { eye: 'tired', brow: 'flat', mouth: 'smallsmile', bags: 0 },
};

// Head with face. (x,y)=centre, r=radius. o.rot rotates the whole head (lying in bed).
function head(ctx, x, y, r, o = {}) {
  const m = MOODS[o.mood || 'tired'] || MOODS.tired; const k = r / 130;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  if (o.sil) { ctx.fillStyle = o.sil; circle(ctx, 0, 0, r + 5 * k); ctx.fill(); if (o.hair) hair(ctx, r, o.hair, o.sil, k, true); ctx.restore(); return; }
  if (o.hair) hair(ctx, r, o.hair, null, k, false);
  ctx.fillStyle = INK; circle(ctx, 0, 0, r + 5 * k); ctx.fill();
  ctx.fillStyle = o.skin || SKIN; circle(ctx, 0, 0, r); ctx.fill();
  // soft shade on the far side
  ctx.save(); circle(ctx, 0, 0, r); ctx.clip(); ctx.fillStyle = 'rgba(0,0,0,.07)'; circle(ctx, -r * .55 * (o.look >= 0 ? 1 : -1), r * .3, r * .9); ctx.fill(); ctx.restore();
  if (o.hair === 'bun' || o.hair === 'pony') { ctx.fillStyle = '#2a2622'; ctx.save(); circle(ctx, 0, 0, r); ctx.clip(); ell(ctx, 0, -r * .95, r * 1.1, r * .55); ctx.fill(); ctx.restore(); }
  if (o.hair === 'cap') { ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(0, -r * .2, r * 1.04, Math.PI * 1.05, Math.PI * 1.95); ctx.closePath(); ctx.fill(); ctx.fillStyle = o.capCol || '#c0392b'; ctx.beginPath(); ctx.arc(0, -r * .2, r * .98, Math.PI * 1.07, Math.PI * 1.93); ctx.closePath(); ctx.fill(); ctx.fillStyle = INK; rr(ctx, r * .1, -r * .32, r * .95, r * .2, r * .08); ctx.fill(); ctx.fillStyle = o.capCol || '#c0392b'; rr(ctx, r * .14, -r * .29, r * .88, r * .13, r * .06); ctx.fill(); }
  if (o.back) { ctx.restore(); return; } // back of head, no face
  const lx = (o.look || 0) * 38 * k, ly = (o.lookY || 0) * 20 * k;
  const blink = o.t != null && (((o.t + (o.seed || 0)) % 3.9) < .13);
  const eyeT = blink ? 'closed' : (o.eye || m.eye);
  for (const side of [-1, 1]) {
    const ex = lx + side * 50 * k + 4 * k, ey = -6 * k + ly;
    // brows
    const b = o.brow || m.brow; const by = ey - 46 * k - (b === 'up' ? 10 * k : 0);
    const inner = b === 'sad' ? -12 * k : b === 'angry' ? 10 * k : 0;
    ctx.beginPath(); const xi = ex - side * 24 * k, xo = ex + side * 26 * k; ctx.moveTo(xi, by + inner); ctx.lineTo(xo, by + (b === 'sad' ? 4 * k : 0)); stroke(ctx, 9 * k, INK);
    if (eyeT === 'closed') { ctx.beginPath(); ctx.arc(ex, ey + 2 * k, 18 * k, .15 * Math.PI, .85 * Math.PI); stroke(ctx, 7 * k, INK); }
    else if (eyeT === 'squeeze') { ctx.beginPath(); ctx.moveTo(ex - side * 18 * k, ey - 12 * k); ctx.lineTo(ex + side * 14 * k, ey); ctx.lineTo(ex - side * 18 * k, ey + 12 * k); stroke(ctx, 7 * k, INK); }
    else if (eyeT === 'happy') { ctx.beginPath(); ctx.arc(ex, ey + 8 * k, 17 * k, 1.15 * Math.PI, 1.85 * Math.PI); stroke(ctx, 7 * k, INK); }
    else if (eyeT === 'wide') { ctx.fillStyle = '#fbf8ef'; circle(ctx, ex, ey, 21 * k); ctx.fill(); ctx.beginPath(); ctx.arc(ex, ey, 21 * k, 0, Math.PI * 2); stroke(ctx, 4 * k, INK); ctx.fillStyle = INK; circle(ctx, ex + lx * .15, ey + 2 * k, 8 * k); ctx.fill(); }
    else if (eyeT === 'open') { ctx.fillStyle = INK; ell(ctx, ex, ey, 11 * k, 14 * k); ctx.fill(); ctx.fillStyle = '#fff'; circle(ctx, ex + 3 * k, ey - 5 * k, 3.2 * k); ctx.fill(); }
    else { // tired / soft: pupil under a heavy lid
      const lid = eyeT === 'soft' ? .35 : (o.lid ?? .55);
      ctx.save(); ctx.beginPath(); ctx.rect(ex - 30 * k, ey - 20 * k + lid * 24 * k, 60 * k, 40 * k); ctx.clip();
      ctx.fillStyle = INK; ell(ctx, ex, ey + 2 * k, 14 * k, 13 * k); ctx.fill(); ctx.restore();
      ctx.beginPath(); ctx.moveTo(ex - 22 * k, ey - 18 * k + lid * 24 * k); ctx.quadraticCurveTo(ex, ey - 24 * k + lid * 24 * k, ex + 22 * k, ey - 17 * k + lid * 24 * k); stroke(ctx, 7.5 * k, INK);
    }
    if ((o.bags ?? m.bags) && eyeT !== 'wide') { ctx.beginPath(); ctx.arc(ex + 1 * k, ey + 6 * k, 19 * k, .22 * Math.PI, .8 * Math.PI); stroke(ctx, 5 * k, BAG); }
    if (o.blush) { ctx.fillStyle = `rgba(240,120,120,${.45 * o.blush})`; ell(ctx, ex + side * 14 * k, ey + 34 * k, 20 * k, 10 * k); ctx.fill(); }
  }
  if (o.tear) { ctx.fillStyle = 'rgba(150,200,255,.9)'; const ty = 30 * k + o.tear * 60 * k; ell(ctx, lx + 64 * k, ty, 6 * k, 9 * k); ctx.fill(); }
  if (o.glasses) { ctx.fillStyle = '#0d0d10'; for (const s of [-1, 1]) { rr(ctx, lx + s * 50 * k - 30 * k + 4 * k, -26 * k, 60 * k, 38 * k, 14 * k); ctx.fill(); } ctx.fillRect(lx - 10 * k, -18 * k, 28 * k, 7 * k); }
  // mouth
  const mx = lx + 6 * k, my = 62 * k + ly * .6, mo = o.mouth || m.mouth;
  ctx.beginPath();
  if (mo === 'frown') { ctx.moveTo(mx - 18 * k, my + 6 * k); ctx.quadraticCurveTo(mx, my - 8 * k, mx + 18 * k, my + 6 * k); stroke(ctx, 7 * k, INK); }
  else if (mo === 'flat') { ctx.moveTo(mx - 14 * k, my); ctx.lineTo(mx + 14 * k, my); stroke(ctx, 7 * k, INK); }
  else if (mo === 'smallsmile') { ctx.moveTo(mx - 16 * k, my - 3 * k); ctx.quadraticCurveTo(mx, my + 9 * k, mx + 16 * k, my - 3 * k); stroke(ctx, 7 * k, INK); }
  else if (mo === 'wavy') { ctx.moveTo(mx - 22 * k, my); ctx.bezierCurveTo(mx - 10 * k, my - 10 * k, mx - 4 * k, my + 10 * k, mx + 6 * k, my); ctx.bezierCurveTo(mx + 12 * k, my - 8 * k, mx + 18 * k, my + 4 * k, mx + 22 * k, my); stroke(ctx, 6 * k, INK); }
  else if (mo === 'o') { ctx.fillStyle = INK; ell(ctx, mx, my + 2 * k, 13 * k, (o.talk ?? 1) * 16 * k + 3 * k); ctx.fill(); }
  else if (mo === 'smirk') { ctx.moveTo(mx - 16 * k, my + 2 * k); ctx.quadraticCurveTo(mx + 4 * k, my + 6 * k, mx + 20 * k, my - 10 * k); stroke(ctx, 7 * k, INK); }
  else if (mo === 'grin') { ctx.fillStyle = INK; rr(ctx, mx - 30 * k, my - 10 * k, 60 * k, 24 * k, 10 * k); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(mx - 24 * k, my - 6 * k, 48 * k, 8 * k); }
  else { ctx.fillStyle = INK; ctx.moveTo(mx - 30 * k, my - 8 * k); ctx.quadraticCurveTo(mx, my + 40 * k, mx + 30 * k, my - 8 * k); ctx.closePath(); ctx.fill(); }
  ctx.restore();
}
function hair(ctx, r, kind, sil, k, isSil) {
  const c = sil || '#2a2622';
  ctx.fillStyle = sil || INK;
  if (kind === 'pony') { ell(ctx, -r * 1.05, -r * .2, r * .32 + 5 * k, r * .62 + 5 * k, .5); ctx.fill(); if (!isSil) { ctx.fillStyle = c; ell(ctx, -r * 1.05, -r * .2, r * .32, r * .62, .5); ctx.fill(); ctx.fillStyle = '#f2c14e'; circle(ctx, -r * .82, -r * .62, r * .1); ctx.fill(); } }
  if (kind === 'bun') { circle(ctx, -r * .25, -r * 1.05, r * .38 + 5 * k); ctx.fill(); if (!isSil) { ctx.fillStyle = c; circle(ctx, -r * .25, -r * 1.05, r * .38); ctx.fill(); } }
}

// Full body. (x,y)=point between feet on the ground, s: 1 => ~830px tall.
// o: mood, look, t, lh/rh (hand targets in body units), walk (phase), lean, rim, skin, hair, prop(ctx,k) ...
function guy(ctx, x, y, s, o = {}) {
  if (o.rim) { ctx.save(); ctx.translate((o.rimDX ?? -7) , (o.rimDY ?? -5)); body(ctx, x, y, s, { ...o, sil: o.rim }); ctx.restore(); }
  body(ctx, x, y, s, o);
}
function shade(hex) { const n = parseInt(hex.slice(1), 16); const f = .72; return `rgb(${((n >> 16) & 255) * f | 0},${((n >> 8) & 255) * f | 0},${(n & 255) * f | 0})`; }
function body(ctx, x, y, s, o) {
  const sil = o.sil; const ol = 5.5;
  ctx.save(); ctx.translate(x, y); ctx.scale(s * (o.flip ? -1 : 1), s); ctx.rotate(o.lean || 0);
  const ph = o.walk; const w = ph != null ? Math.sin(ph) : 0, w2 = ph != null ? Math.cos(ph) : 0;
  const bob = ph != null ? Math.abs(Math.sin(ph)) * -12 : (o.breath != null ? Math.sin(o.breath * 1.6) * 4 : 0);
  ctx.translate(0, bob);
  const sh = o.slump ?? 0; // slump forward
  const hipB = [-34, -270], hipF = [34, -270];
  const footB = o.footB || (ph != null ? [-w * 95, 0 - Math.max(0, -w2) * 30 - bob] : [-40, 0]);
  const footF = o.footF || (ph != null ? [w * 95, 0 - Math.max(0, w2) * 30 - bob] : [44, 0]);
  if (o.sit) { footB[0] = 150; footB[1] = -10; footF[0] = 190; footF[1] = -10; }
  const kneeOf = (h, f) => o.sit ? [h[0] + 170, h[1] + 10] : [(h[0] + f[0]) / 2 + 22, (h[1] + f[1]) / 2];
  const shB = [-62 + sh * 30, -560 + sh * 20], shF = [64 + sh * 30, -556 + sh * 20];
  const hB = o.lh || [-70 + w * 40, -262 + sh * 30], hF = o.rh || [80 - w * 40, -255 + sh * 30];
  const elb = (a, b, bend = 1) => [(a[0] + b[0]) / 2 + 30 * bend, (a[1] + b[1]) / 2 + 10];
  const back = sil || BACK, skin = sil || (o.skin || SKIN);
  const legB = sil || o.pantsB || (o.pants ? shade(o.pants) : BACK), legF = sil || o.pants || skin;
  // back limbs
  limb(ctx, shB, elb(shB, hB, o.bendB ?? 1), hB, 62, back, sil, ol);
  limb(ctx, hipB, kneeOf(hipB, footB), footB, 76, legB, sil, ol);
  if (o.backpack) { ctx.save(); ctx.translate(sh * 26, sh * 18); rr(ctx, -175 - ol, -590 - ol, 120 + ol * 2, 250 + ol * 2, 40); ctx.fillStyle = sil || INK; ctx.fill(); if (!sil) { rr(ctx, -175, -590, 120, 250, 36); ctx.fillStyle = o.backpack; ctx.fill(); ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.fillRect(-165, -470, 100, 10); } ctx.restore(); }
  // torso
  ctx.save(); ctx.translate(sh * 26, sh * 18); ctx.rotate(sh * .12);
  rr(ctx, -108 - ol, -615 - ol, 216 + ol * 2, 375 + ol * 2, 108 + ol); ctx.fillStyle = sil || INK; ctx.fill();
  if (!sil) { rr(ctx, -108, -615, 216, 375, 108); ctx.fillStyle = sil ? skin : (o.shirt || skin); ctx.fill();
    ctx.save(); rr(ctx, -108, -615, 216, 375, 108); ctx.clip(); ctx.fillStyle = 'rgba(0,0,0,.08)'; ctx.fillRect(-108, -615, 60, 375); ctx.restore();
    if (o.stain) { ctx.fillStyle = `rgba(120,72,30,${.85 * o.stain})`; ctx.beginPath(); ctx.ellipse(20, -470, 52 * o.stain, 64 * o.stain, .3, 0, Math.PI * 2); ctx.fill(); circle(ctx, -30, -400, 14 * o.stain); ctx.fill(); circle(ctx, 60, -390, 10 * o.stain); ctx.fill(); }
    if (o.backpack) { ctx.strokeStyle = shade(o.backpack); ctx.lineWidth = 20; ctx.beginPath(); ctx.moveTo(-70, -600); ctx.quadraticCurveTo(-20, -480, -60, -330); ctx.stroke(); }
    if (o.outfit) o.outfit(ctx); }
  ctx.restore();
  // front limbs
  limb(ctx, hipF, kneeOf(hipF, footF), footF, 76, legF, sil, ol);
  if (o.prop && !sil) o.prop(ctx, hF);
  limb(ctx, shF, elb(shF, hF, o.bendF ?? 1), hF, 62, skin, sil, ol);
  if (o.propFront && !sil) o.propFront(ctx, hF);
  // head
  head(ctx, sh * 40 + (o.headDX || 0), -735 + sh * 30 + (o.headDY || 0), 132, { ...o, rot: o.headRot || 0, sil });
  if (o.wet && !sil && o.t != null) { for (let i = 0; i < 7; i++) { const p = ((o.t * 1.3 + i * .37) % 1); const dx = [-120, 110, -60, 140, -150, 90, 30][i], dy0 = [-760, -720, -600, -500, -420, -320, -820][i]; ctx.fillStyle = `rgba(150,200,255,${.9 * (1 - p)})`; ell(ctx, dx, dy0 + p * 160, 7, 11); ctx.fill(); }
    ctx.strokeStyle = 'rgba(120,170,230,.55)'; ctx.lineWidth = 6; for (const [a, b] of [[-60, -860], [10, -872], [70, -858]]) { ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(a + 6, b + 30); ctx.stroke(); } }
  ctx.restore();
}

// ---------- POV: two hands holding a phone (screen drawn by `screen` canvas) ----------
const PW = 400, PH = 820;
const { createCanvas } = require('@napi-rs/canvas');
const scr = createCanvas(PW, PH), sctx = scr.getContext('2d');
function phoneScreen(fn) { sctx.setTransform(1, 0, 0, 1, 0, 0); sctx.clearRect(0, 0, PW, PH); fn(sctx, PW, PH); return scr; }

function finger(ctx, a, b, w) { ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); stroke(ctx, w + 11, INK); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); stroke(ctx, w, SKIN); }
// thumb: {x,y} in screen-local px (0..PW, 0..PH) or null; press 0..1
function povPhone(ctx, cx, cy, sc, screenFn, o = {}) {
  const w = PW * sc + 36 * sc, h = PH * sc + 40 * sc; const x0 = cx - w / 2, y0 = cy - h / 2;
  ctx.save();
  if (o.rot) { ctx.translate(cx, cy); ctx.rotate(o.rot); ctx.translate(-cx, -cy); }
  // screen light spill
  if (!o.off) { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = L.rgrad(ctx, cx, cy, 50, 900 * sc, [[0, `rgba(120,160,255,${.16 * (o.glow ?? 1)})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(cx - 1000, cy - 1000, 2000, 2000); ctx.restore(); }
  // arms from the bottom of frame
  const armL = [cx - w * .62, cy + h * .95], armR = [cx + w * .62, cy + h * .95];
  finger(ctx, [cx - w * .9, cy + h * 1.4], armL, 150 * sc); finger(ctx, [cx + w * .9, cy + h * 1.4], armR, 150 * sc);
  // palms behind phone
  for (const s of [-1, 1]) { ctx.fillStyle = INK; ell(ctx, cx + s * w * .47, cy + h * .36, 105 * sc + 6, 170 * sc + 6, s * .25); ctx.fill(); ctx.fillStyle = SKIN; ell(ctx, cx + s * w * .47, cy + h * .36, 105 * sc, 170 * sc, s * .25); ctx.fill(); }
  // fingers peeking around the side edges (behind the phone)
  for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { const fy = cy + h * (.08 + i * .1); const ex = cx + s * w / 2; finger(ctx, [ex + s * 34 * sc, fy + 12 * sc], [ex - s * 8 * sc, fy], 44 * sc); }
  // phone body
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 40; rr(ctx, x0, y0, w, h, 58 * sc); ctx.fillStyle = '#0b0b0e'; ctx.fill(); ctx.shadowColor = 'transparent';
  rr(ctx, x0 + 3, y0 + 3, w - 6, h - 6, 56 * sc); ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(160,170,200,.35)'; ctx.stroke();
  const sx = x0 + 18 * sc, sy = y0 + 20 * sc, sw = PW * sc, shh = PH * sc;
  ctx.save(); rr(ctx, sx, sy, sw, shh, 44 * sc); ctx.clip();
  if (o.off) { ctx.fillStyle = '#020203'; ctx.fillRect(sx, sy, sw, shh); if (o.reflect) o.reflect(ctx, sx, sy, sw, shh); }
  else { const c = phoneScreen(screenFn); ctx.globalAlpha = o.bright ?? 1; ctx.drawImage(c, sx, sy, sw, shh); ctx.globalAlpha = 1; if ((o.bright ?? 1) < 1) { } }
  // glass glare
  const g = ctx.createLinearGradient(sx, sy, sx + sw, sy + shh); g.addColorStop(0, 'rgba(255,255,255,.07)'); g.addColorStop(.45, 'rgba(255,255,255,0)'); ctx.fillStyle = g; ctx.fillRect(sx, sy, sw, shh);
  ctx.restore();
  // notch
  ctx.fillStyle = '#000'; rr(ctx, cx - 60 * sc, sy + 14 * sc, 120 * sc, 30 * sc, 15 * sc); ctx.fill();
  // thumbs
  const thumb = (base, tip, press) => { const tx = sx + tip.x * sc, ty = sy + tip.y * sc; const dx = tx - base[0], dy = ty - base[1], d = Math.hypot(dx, dy) || 1, len = Math.min(d, 170 * sc);
    finger(ctx, [tx - dx / d * len, ty - dy / d * len], [tx, ty], (58 + press * 6) * sc); };
  const baseL = [cx - w * .62, cy + h * .62], baseR = [cx + w * .62, cy + h * .62];
  thumb(baseL, o.thumbL || { x: -6, y: 690 }, 0);
  thumb(baseR, o.thumbR || { x: 406, y: 690 }, o.press || 0);
  ctx.restore();
  return { sx, sy, sw, sh: shh };
}

module.exports = { SKIN, BACK, INK, MOODS, head, guy, povPhone, phoneScreen, PW, PH, limb, finger };
