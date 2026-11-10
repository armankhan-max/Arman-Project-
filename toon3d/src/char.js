// 2D character rig drawn on a canvas, then shown as a flat card inside the 3D world.
// Design: user's hoodie guy (round brown head, bowl hair with tuft, teal hoodie, navy pants)
// with the bold dark outline of the "2D character in 3D world" look.

export const BASE = {
  skin: '#c98a5e', skinSh: '#b3744b', hair: '#2a1612', top: '#1f9e96', topSh: '#167f7b',
  inner: '#f6f1e7', pants: '#232c4d', shoe: '#1b1620', line: '#17121c',
};
const L1 = 88, L2 = 88, CX = 256;

function armPts(side, a1, a2, bob) {
  const d = Math.PI / 180, sx = CX + side * 84, sy = 408 + bob;
  const ex = sx + side * Math.sin(a1 * d) * L1, ey = sy + Math.cos(a1 * d) * L1;
  const hx = ex + side * Math.sin((a1 + a2) * d) * L2, hy = ey + Math.cos((a1 + a2) * d) * L2;
  return [sx, sy, ex, ey, hx, hy];
}
// hand position in 512x768 rig space
export function handPos(P, side) {
  const a = side > 0 ? (P.armR || [12, 6]) : (P.armL || [12, 6]);
  const p = armPts(side, a[0], a[1], P.bob || 0);
  return [p[4], p[5]];
}

export function drawChar(ctx, W, H, P) {
  const C = Object.assign({}, BASE, P.colors || {});
  const s = W / 512, LW = 9, bob = P.bob || 0;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, W, H);
  ctx.setTransform(s, 0, 0, s, 0, 0);
  ctx.lineJoin = ctx.lineCap = 'round';
  const tube = (pts, w, col) => {
    ctx.beginPath(); ctx.moveTo(pts[0], pts[1]);
    for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
    ctx.strokeStyle = C.line; ctx.lineWidth = w + LW * 1.6; ctx.stroke();
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke();
  };
  const fs = (fill, lw = LW) => { ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = lw; ctx.stroke(); };

  // legs + shoes
  if (P.legs !== 'none') {
    const sw = P.walk || 0; // -1..1 stride
    for (const side of [-1, 1]) {
      const fx = CX + side * 36 + side * sw * 26, fy = 728 - Math.max(0, side * sw) * 14;
      tube([CX + side * 30, 560 + bob, fx, fy], 24, C.pants);
      ctx.beginPath(); ctx.ellipse(fx + side * 12, fy + 8, 30, 15, 0, 0, 7); fs(C.shoe, 6);
    }
  }
  // hood behind the neck
  ctx.beginPath(); ctx.ellipse(CX, 378 + bob, 96, 40, 0, 0, 7); fs(C.topSh);
  // neck
  ctx.beginPath(); ctx.rect(CX - 27, 325 + bob, 54, 70); fs(C.skin);
  // body
  ctx.beginPath(); ctx.roundRect(CX - 92, 372 + bob, 184, 216, [60, 60, 72, 72]);
  ctx.fillStyle = C.top; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = C.topSh; ctx.fillRect(CX + 34, 360 + bob, 80, 240);
  if (P.stripes) { ctx.fillStyle = P.stripes; for (let y = 384; y < 600; y += 34) ctx.fillRect(CX - 100, y + bob, 200, 14); }
  ctx.beginPath(); ctx.roundRect(CX - 58, 500 + bob, 100, 58, 14); ctx.fillStyle = C.topSh; ctx.fill();
  ctx.restore();
  ctx.beginPath(); ctx.roundRect(CX - 92, 372 + bob, 184, 216, [60, 60, 72, 72]);
  ctx.strokeStyle = C.line; ctx.lineWidth = LW; ctx.stroke();
  // inner tee + drawstrings
  ctx.beginPath(); ctx.moveTo(CX - 36, 374 + bob); ctx.lineTo(CX + 36, 374 + bob);
  ctx.quadraticCurveTo(CX + 30, 440 + bob, CX, 452 + bob); ctx.quadraticCurveTo(CX - 30, 440 + bob, CX - 36, 374 + bob);
  fs(C.inner, 6);
  if (!P.noStrings) for (const side of [-1, 1]) tube([CX + side * 17, 404 + bob, CX + side * 19, 478 + bob], 7, C.inner);

  // arms
  for (const side of [-1, 1]) {
    const a = side > 0 ? (P.armR || [12, 6]) : (P.armL || [12, 6]);
    const p = armPts(side, a[0], a[1], bob);
    tube(p, 42, C.top);
    if (side > 0 && P.tied) { // index finger with the string bow
      const d = (a[0] + a[1]) * Math.PI / 180;
      const fx = p[4] + Math.sin(d) * 44, fy = p[5] + Math.cos(d) * 44;
      tube([p[4], p[5], fx, fy], 15, C.skin);
    }
    ctx.beginPath(); ctx.arc(p[4], p[5], 27, 0, 7); fs(C.skin);
    if (P.prop === 'lily' && side < 0) {
      tube([p[4], p[5] + 20, p[4] + 6, p[5] - 80], 6, '#3f9a4e');
      for (let k = 0; k < 5; k++) { ctx.beginPath(); ctx.ellipse(p[4] + 6 + Math.cos(k * 1.256) * 16, p[5] - 86 + Math.sin(k * 1.256) * 16, 15, 9, k * 1.256, 0, 7); fs('#fff7fb', 5); }
      ctx.beginPath(); ctx.arc(p[4] + 6, p[5] - 86, 8, 0, 7); fs('#ffd447', 4);
    }
  }

  // head
  ctx.save();
  ctx.translate(CX + (P.headX || 0), 232 + bob + (P.headY || 0)); ctx.rotate((P.tilt || 0) * Math.PI / 180);
  for (const side of [-1, 1]) { ctx.beginPath(); ctx.arc(side * 116, 14, 20, 0, 7); fs(C.skin); }
  ctx.beginPath(); ctx.arc(0, 0, 118, 0, 7); ctx.fillStyle = C.skin; ctx.fill();
  ctx.save(); ctx.clip(); ctx.beginPath(); ctx.arc(150, 30, 118, 0, 7); ctx.fillStyle = C.skinSh; ctx.fill(); ctx.restore();
  ctx.beginPath(); ctx.arc(0, 0, 118, 0, 7); ctx.strokeStyle = C.line; ctx.lineWidth = LW; ctx.stroke();
  // hair
  if (P.hair !== 'none') {
    ctx.beginPath(); ctx.moveTo(8, -118); ctx.lineTo(24, -152); ctx.lineTo(44, -112); fs(C.hair);
    ctx.beginPath(); ctx.arc(0, 0, 123, Math.PI * 1.1, -Math.PI * 0.1); ctx.closePath(); fs(C.hair);
  }
  if (P.hat === 'nightcap') {
    ctx.beginPath(); ctx.moveTo(-120, -52); ctx.quadraticCurveTo(-60, -210, 70, -190); ctx.quadraticCurveTo(170, -170, 176, -60);
    ctx.quadraticCurveTo(120, -130, 118, -52); ctx.closePath(); fs(P.hatCol || '#d9433f');
    ctx.beginPath(); ctx.roundRect(-128, -70, 256, 34, 16); fs('#f6f1e7');
    ctx.beginPath(); ctx.arc(176, -52, 22, 0, 7); fs('#f6f1e7');
  } else if (P.hat === 'cap') {
    ctx.beginPath(); ctx.arc(0, -30, 124, Math.PI, 0); ctx.closePath(); fs(P.hatCol || '#5b5f73');
    ctx.beginPath(); ctx.roundRect(-150, -44, 190, 26, 12); fs(P.hatCol || '#5b5f73');
  }
  // brows
  const br = (P.brow || 0) * Math.PI / 180, by = -62 + (P.browY || 0);
  for (const side of [-1, 1]) {
    ctx.save(); ctx.translate(side * 47, by); ctx.rotate(-side * br);
    ctx.beginPath(); ctx.moveTo(-23, 0); ctx.lineTo(23, 0); ctx.strokeStyle = C.hair === '#00000000' ? C.line : C.line; ctx.lineWidth = 13; ctx.stroke(); ctx.restore();
  }
  // eyes
  const eye = P.blink ? 'closed' : (P.eye || 'normal'), lk = P.look || [0, 0];
  for (const side of [-1, 1]) {
    const ex = side * 46, ey = -6;
    if (eye === 'happy' || eye === 'closed') {
      ctx.beginPath();
      if (eye === 'happy') ctx.arc(ex, ey + 8, 22, Math.PI * 1.1, -Math.PI * 0.1); else ctx.arc(ex, ey - 8, 22, Math.PI * 0.1, Math.PI * 0.9);
      ctx.strokeStyle = C.line; ctx.lineWidth = 8; ctx.stroke(); continue;
    }
    const r = eye === 'wide' ? 34 : 27, pr = eye === 'wide' ? 9 : 14;
    ctx.beginPath(); ctx.arc(ex, ey, r, 0, 7); fs('#ffffff', 6);
    const px = ex + lk[0] * (r - pr - 5), py = ey + lk[1] * (r - pr - 5);
    ctx.beginPath(); ctx.arc(px, py, pr, 0, 7); ctx.fillStyle = '#111'; ctx.fill();
    ctx.beginPath(); ctx.arc(px + pr * 0.35, py - pr * 0.35, pr * 0.32, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
    if (eye === 'squint') { // heavy lid
      ctx.save(); ctx.beginPath(); ctx.arc(ex, ey, r + 3, 0, 7); ctx.clip();
      ctx.fillStyle = C.skin; ctx.fillRect(ex - r - 4, ey - r - 4, 2 * r + 8, r - 2); ctx.restore();
      ctx.beginPath(); ctx.moveTo(ex - r, ey - 6); ctx.lineTo(ex + r, ey - 6); ctx.strokeStyle = C.line; ctx.lineWidth = 7; ctx.stroke();
    }
  }
  // nose
  ctx.beginPath(); ctx.arc(-2, 24, 11, -Math.PI * 0.45, Math.PI * 0.75); ctx.strokeStyle = C.skinSh; ctx.lineWidth = 6; ctx.stroke();
  // mouth
  const m = P.mouth || 'smile', my = 64; ctx.strokeStyle = C.line; ctx.lineWidth = 7;
  if (m === 'smile') { ctx.beginPath(); ctx.arc(0, my - 22, 32, Math.PI * 0.2, Math.PI * 0.8); ctx.stroke(); }
  else if (m === 'frown') { ctx.beginPath(); ctx.arc(0, my + 30, 30, Math.PI * 1.25, Math.PI * 1.75); ctx.stroke(); }
  else if (m === 'flat') { ctx.beginPath(); ctx.moveTo(-20, my); ctx.lineTo(20, my); ctx.stroke(); }
  else if (m === 'grit') {
    ctx.beginPath(); ctx.roundRect(-30, my - 14, 60, 30, 10); fs('#fff', 6);
    ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-30, my + 1); ctx.lineTo(30, my + 1);
    for (const x of [-15, 0, 15]) { ctx.moveTo(x, my - 14); ctx.lineTo(x, my + 16); } ctx.stroke();
  } else if (m === 'grin') {
    ctx.beginPath(); ctx.moveTo(-34, my - 10); ctx.quadraticCurveTo(0, my + 44, 34, my - 10); ctx.closePath(); fs('#fff', 6);
  } else { // 'o' / 'talk'
    const o = P.mouthOpen == null ? 1 : P.mouthOpen;
    ctx.beginPath(); ctx.ellipse(0, my + 2, 17, 4 + 15 * o, 0, 0, 7); fs('#5a1f2a', 6);
  }
  if (P.sweat) for (const [dx, dy, k] of [[98, -70, 1], [-104, -40, 0.7]]) {
    ctx.beginPath(); ctx.moveTo(dx, dy - 22 * k); ctx.quadraticCurveTo(dx + 16 * k, dy + 4 * k, dx, dy + 12 * k);
    ctx.quadraticCurveTo(dx - 16 * k, dy + 4 * k, dx, dy - 22 * k); fs('#8fd6ff', 5);
  }
  ctx.restore();

  if (P.tied) { // little bow on the finger, drawn on top
    const a = P.armR || [12, 6], p = armPts(1, a[0], a[1], bob), d = (a[0] + a[1]) * Math.PI / 180;
    const fx = p[4] + Math.sin(d) * 34, fy = p[5] + Math.cos(d) * 34;
    for (const k of [-1, 1]) { ctx.beginPath(); ctx.ellipse(fx + k * 11, fy, 11, 7, k * 0.5, 0, 7); fs('#f3e6c4', 4); }
  }
}
