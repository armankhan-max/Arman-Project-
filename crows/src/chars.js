// Characters in the reference style: big round black heads, cream facial features,
// one bold outfit colour each, black limbs, warm rim light from the sun side.
const L = require('./lib');
const { circle, ell, line, quad, rr, lerp } = L;

const SKIN = '#15151c', FACE = '#f4e6cc', PUPIL = '#15151c';
const CAST = {
  lena: { jacket: '#2457b8', shade: '#1a3f88', hair: 'pony', tie: '#f5c242', badge: true },
  dev: { jacket: '#2f9e4f', shade: '#217539', cap: '#1d4a32', hood: true },
  rosa: { jacket: '#7a4fa8', shade: '#5a3780', hair: 'bun', glasses: true, skirt: '#3b2b55', cane: false },
  victor: { jacket: '#b3262e', shade: '#86181f', hair: 'slick', tie2: '#f2c94c', shirt: '#e8e2d6' },
  crew: { jacket: '#ff7a1a', shade: '#cc5a0a', vest: true, hardhat: '#ffd23a' },
  researcher: { jacket: '#e9eef2', shade: '#c4ccd4', mask: true },
  man: { jacket: '#6b6f78', shade: '#50535a', cap: '#2b2d33' },
  kid: { jacket: '#ff5c8a', shade: '#d23d69', hair: 'pony', tie: '#7ad3ff', small: true },
  people: { jacket: '#c88a3a', shade: '#9c6a28' },
};

// Draw a person. (x,y) = point between the feet on the ground. s = scale (1 => ~340px tall).
function person(ctx, x, y, s, o = {}) {
  const c = { ...(CAST[o.who] || {}), ...o };
  const t = o.t || 0;
  ctx.save(); ctx.translate(x, y); ctx.scale(s * (o.facing || 1), s);
  if (c.small) ctx.scale(.78, .78);
  // ground shadow
  if (o.shadow !== false) { ctx.save(); ctx.globalAlpha = .35; ctx.fillStyle = '#000'; ell(ctx, 0, 2, 70, 12); ctx.fill(); ctx.restore(); }
  const rim = o.rim === undefined ? 'rgba(255,190,110,.95)' : o.rim;
  if (rim) { ctx.save(); ctx.translate(o.rimDx ?? -5, o.rimDy ?? -4); body(ctx, c, t, rim); ctx.restore(); }
  body(ctx, c, t, null);
  ctx.restore();
}

function body(ctx, c, t, mono) {
  const col = k => mono || k;
  const walk = c.walk; // walk phase in radians or undefined
  const bob = walk !== undefined ? Math.abs(Math.sin(walk)) * -8 : Math.sin(t * 2.1) * 1.6; // breathing / bob
  const lean = c.lean || 0;
  // ---- legs
  const hipY = -122 + bob;
  const legs = [[-15, 1], [15, -1]];
  for (const [hx, side] of legs) {
    let ang = 0, kneeBend = 0;
    if (walk !== undefined) { ang = Math.sin(walk + (side > 0 ? 0 : Math.PI)) * .45; kneeBend = Math.max(0, -Math.cos(walk + (side > 0 ? 0 : Math.PI))) * .5; }
    if (c.pose === 'sit') { ang = -1.35; kneeBend = 1.4; }
    if (c.pose === 'brace') { ang = side > 0 ? .25 : -.3; }
    const ux = hx + Math.sin(ang) * 62, uy = hipY + Math.cos(ang) * 62;
    const fx = ux + Math.sin(ang - kneeBend) * 62 * (c.pose === 'sit' ? -0.1 : 1) + (c.pose === 'sit' ? 0 : 0), fy = c.pose === 'sit' ? uy + 60 : Math.min(-6, uy + Math.cos(ang - kneeBend) * 62);
    quad(ctx, [hx, hipY, ux, uy, fx, fy], 23, col(c.legs || SKIN));
    ctx.fillStyle = col('#0c0c10'); ell(ctx, fx + 9, fy + 4, 19, 9); ctx.fill();
  }
  if (c.skirt) { ctx.fillStyle = col(c.skirt); ctx.beginPath(); ctx.moveTo(-44, hipY - 20); ctx.lineTo(44, hipY - 20); ctx.lineTo(54, hipY + 48); ctx.lineTo(-54, hipY + 48); ctx.closePath(); ctx.fill(); }

  ctx.save(); ctx.translate(0, hipY); ctx.rotate(lean); ctx.translate(0, -hipY);
  const sh = hipY - 106; // shoulder line
  // ---- back arm (drawn before torso)
  const arms = armPose(c, t);
  drawArm(ctx, -34, sh + 10, arms[0], c, col, true);
  // ---- torso / jacket
  ctx.fillStyle = col(c.jacket || '#555');
  ctx.beginPath(); ctx.moveTo(-40, sh); ctx.quadraticCurveTo(0, sh - 12, 40, sh);
  ctx.quadraticCurveTo(52, sh + 50, 46, hipY + 8); ctx.quadraticCurveTo(0, hipY + 18, -46, hipY + 8); ctx.quadraticCurveTo(-52, sh + 50, -40, sh); ctx.fill();
  if (!mono) {
    // shading on back side + zipper
    ctx.save(); ctx.clip(); ctx.fillStyle = c.shade || 'rgba(0,0,0,.2)'; ctx.globalAlpha = .9; ell(ctx, -46, hipY - 40, 22, 90); ctx.fill(); ctx.restore();
    if (c.shirt) { ctx.fillStyle = c.shirt; ctx.beginPath(); ctx.moveTo(-10, sh - 4); ctx.lineTo(10, sh - 4); ctx.lineTo(4, sh + 46); ctx.lineTo(-4, sh + 46); ctx.closePath(); ctx.fill(); }
    if (c.tie2) { ctx.fillStyle = c.tie2; ctx.beginPath(); ctx.moveTo(-5, sh); ctx.lineTo(5, sh); ctx.lineTo(7, sh + 44); ctx.lineTo(0, sh + 54); ctx.lineTo(-7, sh + 44); ctx.closePath(); ctx.fill(); }
    if (!c.shirt) line(ctx, [4, sh + 2, 6, hipY + 10], 3.5, 'rgba(0,0,0,.35)');
    if (c.vest) { ctx.fillStyle = '#d7ff3a'; ctx.fillRect(-40, sh + 40, 82, 10); ctx.fillRect(-42, sh + 70, 86, 10); }
    if (c.badge) { ctx.fillStyle = '#f5c242'; circle(ctx, 22, sh + 26, 6); ctx.fill(); }
    if (c.hood) { ctx.fillStyle = c.shade; ell(ctx, -6, sh - 4, 36, 12); ctx.fill(); }
    if (c.jacket === '#e9eef2') { line(ctx, [0, sh, 0, hipY + 10], 3, '#9aa4ad'); }
  }
  // ---- head
  const hx = 4, hy = sh - 52;
  const tilt = c.tilt || 0;
  ctx.save(); ctx.translate(hx, hy); ctx.rotate(tilt);
  if (c.hair === 'pony') { ctx.fillStyle = col(SKIN); ell(ctx, -66, -14 + Math.sin(t * 3) * 2, 20, 30, -.5); ctx.fill(); if (!mono) { ctx.fillStyle = c.tie; circle(ctx, -54, -24, 7); ctx.fill(); } }
  if (c.hair === 'bun') { ctx.fillStyle = col('#d9d4cc'); circle(ctx, -20, -64, 24); ctx.fill(); }
  ctx.fillStyle = col(SKIN); circle(ctx, 0, 0, 62); ctx.fill();
  if (!mono) {
    if (c.hair === 'bun') { ctx.save(); circle(ctx, 0, 0, 62); ctx.clip(); ctx.fillStyle = '#d9d4cc'; ell(ctx, -14, -58, 64, 26, -.15); ctx.fill(); ctx.restore(); }
    if (c.hair === 'slick') { ctx.save(); circle(ctx, 0, 0, 62); ctx.clip(); ctx.fillStyle = '#2a2018'; ell(ctx, -6, -54, 70, 24, -.12); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(-6, -20, 52, -2.6, -1.1); ctx.stroke(); ctx.restore(); }
    if (c.mask) drawMask(ctx); else face(ctx, c, t);
  }
  if (c.cap) { ctx.fillStyle = col(c.cap); ctx.beginPath(); ctx.arc(0, -10, 64, Math.PI * 1.08, Math.PI * 1.98); ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.moveTo(30, -26); ctx.quadraticCurveTo(80, -30, 92, -14); ctx.lineTo(40, -14); ctx.closePath(); ctx.fill(); }
  if (c.hardhat) { ctx.fillStyle = col(c.hardhat); ctx.beginPath(); ctx.arc(0, -16, 64, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.fillRect(-74, -22, 148, 10); }
  if (c.drivercap) { ctx.fillStyle = col('#173a7a'); rr(ctx, -56, -76, 112, 34, 10); ctx.fill(); ctx.fillStyle = col('#0d1f45'); ctx.fillRect(-10, -46, 92, 10); if (!mono) { ctx.fillStyle = '#f5c242'; circle(ctx, 0, -60, 7); ctx.fill(); } }
  ctx.restore();
  // ---- front arm
  drawArm(ctx, 34, sh + 10, arms[1], c, col, false);
  ctx.restore();
}

function armPose(c, t) {
  // returns [[upperAngle, foreAngle], ...] for back, front arms (angle from straight down, + = forward)
  const p = c.arms || 'down';
  const sw = c.walk !== undefined ? Math.sin(c.walk) * .5 : Math.sin(t * 2.1) * .03;
  switch (p) {
    case 'wave': return [[-.15, 0], [2.6, 2.6 + Math.sin(t * 9) * .45]];
    case 'point': return [[-.1, -.1], [1.45, 1.45]];
    case 'up': return [[-2.4, -2.6], [2.4, 2.6]];
    case 'hips': return [[-.7, .9], [.7, -.9]];
    case 'phone': return [[.05, .1], [.35, 2.5]];
    case 'hold': return [[.6, 1.5], [.7, 1.6]];
    case 'permit': return [[-.1, 0], [2.2 + Math.sin(t * 7) * .25, 2.5 + Math.sin(t * 7) * .3]];
    case 'tap': return [[-.05, 0], [1.1, 1.6 + Math.max(0, Math.sin(t * 9)) * .3]];
    case 'shrug': return [[-.9, -2.0], [.9, 2.0]];
    case 'read': return [[.9, 2.0], [.9, 2.1]];
    case 'run': return [[-Math.sin(c.walk || 0) * .9, -Math.sin(c.walk || 0) * .9 + 1.3], [Math.sin(c.walk || 0) * .9, Math.sin(c.walk || 0) * .9 + 1.3]];
    case 'cross': return [[.35, 1.9], [.15, -1.75]];
    default: return [[-sw, -sw * .6], [sw, sw * .6 + .08]];
  }
}
function drawArm(ctx, x, y, [a1, a2], c, col, back) {
  const L1 = 54, L2 = 52;
  const ex = x + Math.sin(a1) * L1, ey = y + Math.cos(a1) * L1;
  const hx = ex + Math.sin(a2) * L2, hy = ey + Math.cos(a2) * L2;
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(ex, ey); ctx.lineTo(hx, hy);
  ctx.lineWidth = 25; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = col(back ? (c.shade || c.jacket) : c.jacket); ctx.stroke();
  ctx.fillStyle = col('#0e0e13'); circle(ctx, hx, hy + 3, 12); ctx.fill();
  if (!back && !col('') && c.holding) holdItem(ctx, hx, hy, c.holding, c.t || 0);
}
function holdItem(ctx, x, y, what, t) {
  ctx.save(); ctx.translate(x, y);
  if (what === 'phone') { ctx.fillStyle = '#111'; rr(ctx, -10, -40, 26, 46, 6); ctx.fill(); ctx.fillStyle = Math.sin(t * 30) > 0 ? '#8fe3ff' : '#4bb9e8'; rr(ctx, -7, -36, 20, 36, 3); ctx.fill(); }
  if (what === 'permit') { ctx.rotate(-.2); ctx.fillStyle = '#f7f1e3'; ctx.fillRect(-10, -76, 64, 84); ctx.fillStyle = '#9aa'; for (let i = 0; i < 6; i++) ctx.fillRect(-2, -66 + i * 11, 46 - (i % 2) * 14, 4); ctx.fillStyle = '#c33'; ctx.fillRect(-2, -8, 30, 6); }
  if (what === 'papers') { ctx.rotate(-.1); ctx.fillStyle = '#efe7d4'; ctx.fillRect(-4, -70, 66, 82); ctx.fillStyle = '#fbf6ea'; ctx.fillRect(-12, -76, 66, 82); ctx.fillStyle = '#a9a'; for (let i = 0; i < 6; i++) ctx.fillRect(-4, -66 + i * 11, 46, 4); }
  if (what === 'clipboard') { ctx.fillStyle = '#8a5a2b'; rr(ctx, -6, -70, 58, 76, 6); ctx.fill(); ctx.fillStyle = '#f4efe2'; ctx.fillRect(0, -60, 46, 62); }
  if (what === 'peanut') { ctx.fillStyle = '#d9a35b'; ell(ctx, 6, -8, 12, 7, .4); ctx.fill(); }
  if (what === 'news') { ctx.fillStyle = '#ece6d6'; ctx.fillRect(-20, -86, 120, 90); ctx.fillStyle = '#333'; ctx.fillRect(-12, -78, 90, 12); ctx.fillStyle = '#999'; for (let i = 0; i < 5; i++) ctx.fillRect(-12, -58 + i * 11, 100, 4); }
  if (what === 'cup') { ctx.fillStyle = '#e8483f'; ctx.beginPath(); ctx.moveTo(-14, -62); ctx.lineTo(22, -62); ctx.lineTo(16, 4); ctx.lineTo(-8, 4); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(-10, -40, 28, 8); line(ctx, [8, -62, 14, -92], 4, '#fff'); }
  if (what === 'stone') { ctx.fillStyle = '#8a8a8a'; ell(ctx, 4, -6, 14, 11); ctx.fill(); }
  ctx.restore();
}

function face(ctx, c, t) {
  const mood = c.mood || 'neutral';
  const look = c.look || 0;
  const fx = 16 + look * 6, fy = -2;
  // blink every ~3.7s (offset per character)
  const bp = ((t + (c.blinkOff || 0)) % 3.7); let open = bp < .12 ? Math.abs(bp - .06) / .06 : 1;
  if (c.blinkAt !== undefined && Math.abs(t - c.blinkAt) < .12) open = Math.abs(t - c.blinkAt) / .12;
  const lid = c.lid || (mood === 'tired' ? .45 : 0);
  const big = mood === 'surprised' ? 1.25 : 1;
  for (const ex of [-20, 20]) {
    const x = fx + ex, y = fy - 6;
    ctx.fillStyle = FACE; ell(ctx, x, y, 10 * big, 12 * big * open * (1 - lid * .5)); ctx.fill();
    if (open > .3) { ctx.fillStyle = PUPIL; circle(ctx, x + 2 + look * 3, y + 1 + (lid ? 3 : 0), 5 * big); ctx.fill(); ctx.fillStyle = '#fff'; circle(ctx, x + 4 + look * 3, y - 2, 1.8); ctx.fill(); }
    if (lid > 0) { ctx.fillStyle = SKIN; ctx.fillRect(x - 13, y - 16, 26, 16 * lid + 2); }
  }
  // brows
  const bw = 3.6; const by = fy - 26;
  const br = { neutral: [0, 0], sad: [.35, -.35], worried: [.4, -.4], angry: [-.45, .45], surprised: [0, 0], happy: [0, 0], smile: [0, 0], tired: [.2, -.2], determined: [-.3, .3], annoyed: [-.25, .1] }[mood] || [0, 0];
  const lift = mood === 'surprised' ? -8 : 0;
  line(ctx, [fx - 30, by + lift + br[0] * 10, fx - 10, by + lift - br[0] * 10], bw, FACE);
  line(ctx, [fx + 10, by + lift + br[1] * 10 * -1, fx + 30, by + lift - br[1] * 10 * -1], bw, FACE);
  // mouth
  const my = fy + 26; const talk = c.talk ? Math.abs(Math.sin(t * 14)) : 0;
  ctx.strokeStyle = FACE; ctx.fillStyle = FACE; ctx.lineWidth = 3.6; ctx.lineCap = 'round';
  if (talk > 0.05 || mood === 'surprised') { ell(ctx, fx, my, 7, 3 + (mood === 'surprised' ? 8 : talk * 7)); ctx.fill(); }
  else if (mood === 'happy' || mood === 'smile' || mood === 'laugh') { ctx.beginPath(); ctx.arc(fx, my - 8, mood === 'laugh' ? 14 : 11, .25 * Math.PI, .75 * Math.PI); if (mood === 'laugh') ctx.fill(); else ctx.stroke(); }
  else if (mood === 'sad' || mood === 'worried' || mood === 'angry') { ctx.beginPath(); ctx.arc(fx, my + 10, 11, 1.2 * Math.PI, 1.8 * Math.PI); ctx.stroke(); }
  else { line(ctx, [fx - 8, my, fx + 8, my], 3.6, FACE); }
  if (c.glasses) { ctx.strokeStyle = '#d8c79b'; ctx.lineWidth = 3; circle(ctx, fx - 20, fy - 6, 15); ctx.stroke(); circle(ctx, fx + 20, fy - 6, 15); ctx.stroke(); line(ctx, [fx - 5, fy - 6, fx + 5, fy - 6], 3, '#d8c79b'); }
}
function drawMask(ctx) { // the 'caveman' mask from the Seattle study, stylised
  ctx.fillStyle = '#d8c3a0'; ell(ctx, 10, 0, 56, 60); ctx.fill();
  ctx.fillStyle = '#6a4a2a'; ell(ctx, 10, -48, 60, 20); ctx.fill();
  line(ctx, [-16, -18, 4, -12], 7, '#3a2a1a'); line(ctx, [20, -12, 40, -18], 7, '#3a2a1a');
  ctx.fillStyle = '#2a1c10'; circle(ctx, -6, -2, 6); ctx.fill(); circle(ctx, 30, -2, 6); ctx.fill();
  ctx.fillStyle = '#b89870'; ell(ctx, 13, 14, 12, 9); ctx.fill();
  line(ctx, [-6, 34, 32, 34], 5, '#5a3a20');
}

// ---------------- CROW ----------------
// (x,y) = feet on perch. s = scale (1 => ~ 120px long). o: facing, tilt, beak (0..1 open), fly (phase), blink, notch, hold, look
function crow(ctx, x, y, s, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * (o.facing || 1), s);
  if (o.rot) ctx.rotate(o.rot);
  const rim = o.rim === undefined ? 'rgba(255,190,110,.9)' : o.rim;
  if (rim) { ctx.save(); ctx.translate(-3, -3); crowBody(ctx, o, rim); ctx.restore(); }
  crowBody(ctx, o, null);
  ctx.restore();
}
function crowBody(ctx, o, mono) {
  const K = '#14151d', K2 = '#232a3d';
  const col = k => mono || k; const t = o.t || 0;
  const flying = o.fly !== undefined; const hop = o.hop ? Math.abs(Math.sin(t * 8)) * -10 : 0;
  ctx.translate(0, hop);
  // legs
  if (!flying) {
    line(ctx, [-4, -22, -6, 0], 4, col('#2b2b30')); line(ctx, [6, -22, 6, 0], 4, col('#2b2b30'));
    line(ctx, [-16, 0, 6, 0], 3.5, col('#2b2b30')); line(ctx, [-6, 0, 16, 0], 3.5, col('#2b2b30'));
  }
  const by = flying ? -40 : -44;
  // tail
  ctx.fillStyle = col(K);
  ctx.beginPath(); ctx.moveTo(-28, by + 4); ctx.lineTo(-84, by + (flying ? 2 : 26)); 
  if (o.notch && !mono) { ctx.lineTo(-80, by + (flying ? 10 : 33)); ctx.lineTo(-70, by + (flying ? 10 : 31)); ctx.lineTo(-76, by + (flying ? 18 : 40)); }
  ctx.lineTo(-72, by + (flying ? 22 : 42)); ctx.lineTo(-20, by + 18); ctx.closePath(); ctx.fill();
  // back wing (when flying)
  if (flying) { const f = Math.sin(o.fly); ctx.fillStyle = col('#0f1017'); ctx.beginPath(); ctx.moveTo(-8, by - 6); ctx.quadraticCurveTo(-30, by - 70 * f, -70, by - 92 * f); ctx.quadraticCurveTo(-30, by - 30 * f, 14, by - 4); ctx.closePath(); ctx.fill(); }
  // body
  ctx.fillStyle = col(K); ell(ctx, 0, by, 44, 26, -.12); ctx.fill();
  if (!mono) { ctx.save(); ell(ctx, 0, by, 44, 26, -.12); ctx.clip(); ctx.fillStyle = K2; ell(ctx, 6, by - 16, 34, 10, -.12); ctx.fill(); ctx.restore(); }
  // front wing
  if (flying) { const f = Math.sin(o.fly + .4); ctx.fillStyle = col('#1b1e2b'); ctx.beginPath(); ctx.moveTo(-6, by - 4); ctx.quadraticCurveTo(-10, by - 80 * f, -48, by - 104 * f); ctx.quadraticCurveTo(-4, by - 40 * f, 22, by - 2); ctx.closePath(); ctx.fill(); }
  else { ctx.fillStyle = col('#0c0d13'); ell(ctx, -12, by + 2, 34, 17, -.2); ctx.fill(); if (!mono) { line(ctx, [-36, by + 8, -6, by + 4], 2, 'rgba(120,140,190,.35)'); } }
  // head
  const tilt = o.tilt || 0;
  ctx.save(); ctx.translate(34, by - 22); ctx.rotate(tilt);
  ctx.fillStyle = col(K); circle(ctx, 0, 0, 21); ctx.fill();
  // beak
  const bo = (o.beak || 0) + (o.talk ? Math.max(0, Math.sin(t * 16)) * .8 : 0);
  ctx.fillStyle = col('#2a2b33');
  ctx.beginPath(); ctx.moveTo(12, -9); ctx.quadraticCurveTo(34, -9, 46, -2 - bo * 4); ctx.lineTo(14, 1); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(14, 2); ctx.lineTo(42, 4 + bo * 10); ctx.lineTo(12, 8); ctx.closePath(); ctx.fill();
  if (!mono) {
    // eye
    const bl = o.blink !== undefined && Math.abs(t - o.blink) < .1 ? .1 : ((t * 1.0 + (o.seed || 0)) % 4.3 < .1 ? .15 : 1);
    ctx.fillStyle = o.eyeGlow || '#f2efe6'; ell(ctx, 6, -6, 5.5, 5.5 * bl); ctx.fill();
    if (bl > .5) { ctx.fillStyle = '#0a0a0e'; circle(ctx, 7 + (o.look || 0) * 1.5, -6, 3); ctx.fill(); ctx.fillStyle = '#fff'; circle(ctx, 8, -8, 1.2); ctx.fill(); }
    ctx.strokeStyle = 'rgba(140,160,210,.35)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, 18, -2.4, -1.2); ctx.stroke();
    if (o.hold) { ctx.save(); ctx.translate(40, 4); crowHold(ctx, o.hold, t); ctx.restore(); }
  }
  ctx.restore();
}
function crowHold(ctx, what, t) {
  if (what === 'clip') { ctx.strokeStyle = '#c9ced6'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(26, 0); ctx.arc(26, 6, 6, -Math.PI / 2, Math.PI / 2); ctx.lineTo(8, 12); ctx.stroke(); }
  if (what === 'hook') { ctx.strokeStyle = '#c9ced6'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(34, 2); ctx.arc(34, 10, 8, -Math.PI / 2, Math.PI * .6); ctx.stroke(); }
  if (what === 'twig') { ctx.strokeStyle = '#7a5530'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(44, 4); ctx.lineTo(50, 12); ctx.stroke(); }
  if (what === 'peanut') { ctx.fillStyle = '#d9a35b'; ell(ctx, 8, 2, 11, 6, .2); ctx.fill(); }
  if (what === 'pebble') { ctx.fillStyle = '#9a9690'; ell(ctx, 6, 4, 8, 6); ctx.fill(); }
  if (what === 'paper') { ctx.rotate(.3); ctx.fillStyle = '#f6f0e1'; ctx.fillRect(-4, -6, 46, 58); ctx.fillStyle = '#999'; for (let i = 0; i < 4; i++) ctx.fillRect(2, 2 + i * 10, 32, 3); }
  if (what === 'toast') { ctx.fillStyle = '#d9a04a'; rr(ctx, -2, -10, 36, 30, 8); ctx.fill(); ctx.fillStyle = '#f1d08c'; rr(ctx, 3, -5, 26, 20, 5); ctx.fill(); }
  if (what === 'pen') { line(ctx, [0, 0, 38, 6], 4, '#2a62d6'); }
  if (what === 'receipt') { ctx.fillStyle = '#fff'; ctx.fillRect(-2, 0, 26, 44); ctx.fillStyle = '#aaa'; for (let i = 0; i < 5; i++) ctx.fillRect(2, 6 + i * 7, 18, 2); }
}

module.exports = { person, crow, CAST, holdItem };
