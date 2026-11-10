// "The Pudding Guy": 55 s short, 2D characters in a 3D toon world, one continuous camera.
import { THREE, SC, W, H, FPS, cl, seg, lerp, EASE, pop, bump, rng, o2, scene, camera, ctex, toon, OUTM, ol, box, cyl, put, glow, card, txt, makeChar, instanced, makeCam, drawCaption, vignette, renderBlurred } from './kit.js';

const VO = await (await fetch('/pudding/vo.json')).json();
const A = i => VO.sents[i][0], B = i => VO.sents[i][1];
const CT = (s) => (VO.chunks.find(c => c[2].startsWith(s)) || [0])[0]; // start time of a caption chunk
const DUR = VO.dur;

// ---------------- sky, light, ground ----------------
const skyMat = new THREE.MeshBasicMaterial({
  side: THREE.BackSide, fog: false, map: ctex(64, 512, (c, w, h) => {
    const g = c.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#2f7df0'); g.addColorStop(0.38, '#57a8ff'); g.addColorStop(0.5, '#c9ecff'); g.addColorStop(0.56, '#9ed3ff'); g.addColorStop(1, '#6fb4f0');
    c.fillStyle = g; c.fillRect(0, 0, w, h);
  })
});
scene.add(new THREE.Mesh(new THREE.SphereGeometry(300, 32, 16), skyMat));
scene.fog = new THREE.Fog(0xc9ecff, 45, 190);
const hemi = new THREE.HemisphereLight(0xffffff, 0xaab6e0, 1.75); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0d0, 2.1); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -13, right: 13, top: 13, bottom: -13, near: 1, far: 70 }); sun.shadow.bias = -0.0012; sun.shadow.radius = 3;
scene.add(sun); scene.add(sun.target);
const grassTex = ctex(512, 512, (c) => {
  c.fillStyle = '#5fc45a'; c.fillRect(0, 0, 512, 512); const r = rng(3);
  for (let i = 0; i < 240; i++) { c.fillStyle = r() > 0.5 ? '#74d46a' : '#4fb04e'; c.beginPath(); c.ellipse(r() * 512, r() * 512, 4 + r() * 10, 2 + r() * 3, 0, 0, 7); c.fill(); }
}); grassTex.wrapS = grassTex.wrapT = THREE.RepeatWrapping; grassTex.repeat.set(40, 40);
const ground = put(new THREE.Mesh(new THREE.PlaneGeometry(260, 260), toon(0xffffff, { map: grassTex })), 0, -0.1, 0); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
const road = put(new THREE.Mesh(new THREE.PlaneGeometry(260, 5), toon(0x5b6078)), 0, -0.09, 8.5); road.rotation.x = -Math.PI / 2; road.receiveShadow = true;
for (let i = -30; i < 30; i++) { const d = put(new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.18), new THREE.MeshBasicMaterial({ color: 0xfff6c9 })), i * 3.6, -0.08, 8.5); d.rotation.x = -Math.PI / 2; }
{ const r = rng(9); for (let i = 0; i < 34; i++) { const x = -40 + r() * 90, z = r() > 0.5 ? -9 - r() * 14 : 3.2 + r() * 2.2, s = 0.5 + r() * 0.7; if (Math.abs(x) < 5 && z > 0) continue; put(ol(new THREE.IcosahedronGeometry(s, 1), toon(r() > 0.5 ? 0x3fa650 : 0x4fba5c), 0.04), x, s * 0.7, z); if (z < -9) put(cyl(0.12, 0.16, 1.2, toon(0x8a5a3a), 0.03, 7), x, -0.3, z); } }
// clouds
const clouds = [];
{ const r = rng(21); const cm = toon(0xffffff);
  for (let i = 0; i < 22; i++) { const g = new THREE.Group(); const s = 0.9 + r() * 1.2;
    for (const [x, y, k] of [[0, 0, 1], [1.0, -0.15, 0.75], [-1.05, -0.2, 0.7], [0.4, 0.45, 0.7]]) g.add(put(ol(new THREE.SphereGeometry(k, 12, 9), cm, 0.05, false), x, y, 0, g));
    g.scale.set(s, s * 0.8, s * 0.6); const bx = -60 + r() * 120; g.position.set(bx, 11.5 + r() * 9, -14 - r() * 22); g.userData.bx = bx; scene.add(g); clouds.push(g); }
}

// ---------------- pudding cup ----------------
const cupTex = ctex(1024, 256, (c, w, h) => {
  c.fillStyle = '#f7f3ea'; c.fillRect(0, 0, w, h); c.fillStyle = '#6b3a22'; c.fillRect(0, 44, w, 150);
  c.fillStyle = '#ffd98a'; c.textAlign = 'center'; c.textBaseline = 'middle';
  for (const x of [150, 874]) { c.font = '900 62px Inter'; c.fillText('CHOCO', x, 98); c.font = '800 34px Inter'; c.fillText('PUDDING', x, 150); }
  c.fillStyle = '#fff'; c.beginPath(); c.roundRect(396, 54, 232, 130, 10); c.fill(); c.fillStyle = '#111'; const r = rng(5); let x = 412;
  while (x < 610) { const bw = 3 + (r() * 3 | 0) * 2; c.fillRect(x, 64, bw, 88); x += bw + 3 + (r() * 2 | 0) * 3; }
  c.font = '700 20px Inter'; c.fillText('0 12150 31999 5', 512, 168);
});
const cupGeo = new THREE.CylinderGeometry(0.11, 0.085, 0.15, 16); cupGeo.rotateY(Math.PI);
const cupMats = [toon(0xffffff, { map: cupTex }), toon(0xd9deef), toon(0xf7f3ea)];

// ---------------- GARAGE (origin) ----------------
const wallG = toon(0xf3dfae), wallG2 = toon(0xe6cc95);
put(box(8.2, 0.1, 7.6, toon(0xc9cde0), 0.03), 0, -0.05, -2.6).receiveShadow = true;
put(box(8.2, 4.9, 0.2, wallG, 0.04), 0, 2.45, -6.2);
for (const s of [-1, 1]) put(box(0.2, 4.9, 7.2, wallG2, 0.04), s * 4.1, 2.45, -2.6);
put(box(8.2, 0.5, 0.26, toon(0x8a6a4a), 0.03), 0, 0.25, -6.05);
const calendar = put(card(1.25, 1.5, (c, w, h) => {
  c.fillStyle = '#fffdf6'; c.fillRect(0, 0, w, h); c.fillStyle = '#d9433f'; c.fillRect(0, 0, w, 0.34); txt(c, 'MAY 1999', w / 2, 0.18, 0.19, '#fff');
  const days = 31, cols = 7; for (let d = 1; d <= days; d++) { const cx = 0.12 + ((d + 5) % cols) * 0.168, cy = 0.5 + Math.floor((d + 5) / cols) * 0.19; txt(c, '' + d, cx, cy, 0.085, '#3a3550', { weight: 700 });
    if (d < 12) { c.strokeStyle = '#d9433f'; c.lineWidth = 0.02; c.beginPath(); c.moveTo(cx - 0.05, cy - 0.05); c.lineTo(cx + 0.05, cy + 0.05); c.moveTo(cx + 0.05, cy - 0.05); c.lineTo(cx - 0.05, cy + 0.05); c.stroke(); }
    if (d === 31) { c.strokeStyle = '#d9433f'; c.lineWidth = 0.028; c.beginPath(); c.ellipse(cx, cy, 0.1, 0.085, 0, 0, 7); c.stroke(); } }
  txt(c, 'DEADLINE!!', 0.78, 1.4, 0.1, '#d9433f');
  c.strokeStyle = '#16111f'; c.lineWidth = 0.03; c.strokeRect(0, 0, w, h);
}), -2.2, 3.35, -6.08);
const led = put(card(2.3, 0.62, () => { }), 0.25, 3.75, -6.08);
let ledKey = '';
function setLed(s) { if (s === ledKey) return; ledKey = s; led.redraw((c, w, h) => { c.fillStyle = '#16111f'; c.beginPath(); c.roundRect(0, 0, w, h, 0.08); c.fill(); c.fillStyle = '#2a1f1a'; c.fillRect(0.06, 0.06, w - 0.12, h - 0.12); txt(c, s, w / 2, h / 2 + 0.01, 0.3, '#ffb347', { weight: 900 }); }); }
put(card(1.3, 1.6, (c, w, h) => { c.fillStyle = '#16213f'; c.fillRect(0, 0, w, h); txt(c, 'Y2K', w / 2, 0.42, 0.44, '#ffe14d'); txt(c, 'SURVIVAL', w / 2, 0.85, 0.19, '#fff'); txt(c, 'KIT', w / 2, 1.08, 0.19, '#fff'); txt(c, '(it\'s pudding)', w / 2, 1.38, 0.1, '#9fb2ff', { weight: 700, italic: true }); c.strokeStyle = '#16111f'; c.lineWidth = 0.03; c.strokeRect(0, 0, w, h); }), 2.6, 3.3, -6.08);
for (const [x, z, s, ry] of [[-3.3, -5.3, 1, 0.1], [-3.35, -5.25, 0.8, -0.2], [3.3, -5.2, 1.05, -0.15], [3.2, -0.6, 0.9, 0.3], [-3.3, -0.4, 0.85, -0.25]]) {
  const b = put(box(0.9 * s, 0.75 * s, 0.9 * s, toon(0xc99a5b), 0.03), x, (x === -3.35 ? 0.75 + 0.3 : 0.375 * s), z); b.rotation.y = ry;
  const l = card(0.7 * s, 0.3 * s, (c, w, h) => { txt(c, 'PUDDING', w / 2, h / 2, 0.15 * s, '#5a3a1c'); }, { alpha: true }); l.position.set(0, 0, 0.455 * s); b.add(l);
}
// the mountain
const MN = 1150, MR = 2.35, MH = 2.5, MC = [0, 0, -3.0];
const mtn = instanced(cupGeo, cupMats, MN).add();
const mcore = put(new THREE.Mesh(new THREE.ConeGeometry(MR - 0.12, MH - 0.1, 28), toon(0x5a3220)), MC[0], (MH - 0.1) / 2, MC[2]);
const MCUP = []; { const r = rng(77);
  for (let i = 0; i < MN; i++) { const rr = MR * Math.sqrt(r()), a = r() * Math.PI * 2; let y = MH * (1 - rr / MR); y = Math.min(y, 2.02) + r() * 0.1;
    MCUP.push({ x: MC[0] + Math.cos(a) * (rr + 0.05), y: y + 0.04, z: MC[2] + Math.sin(a) * (rr + 0.05), rx: (r() - 0.5) * 2.4, ry: r() * 6.3, rz: (r() - 0.5) * 2.4, d: r() }); }
  MCUP.sort((p, q2) => p.y - q2.y); }
function setMountain(t) {
  const full = t < 10 || t > 30.2; const t0 = A(13) + 0.25, span = 1.75;
  mcore.scale.setScalar(full ? 1 : Math.max(0.001, EASE.out(seg(t, t0, t0 + span))));
  for (let i = 0; i < MN; i++) { const p = MCUP[i]; let dy = 0, s = 1;
    if (!full) { const ts = t0 + span * (i / MN) + p.d * 0.12, k = seg(t, ts, ts + 0.32); if (k <= 0) s = 0.0001; dy = (1 - k * k) * 6.5 + (k >= 1 ? 0 : 0); if (k >= 1) dy = Math.max(0, 0.12 * Math.exp(-(t - ts - 0.32) * 9) * Math.abs(Math.sin((t - ts - 0.32) * 18))); }
    mtn.set(i, p.x, p.y + dy, p.z, p.rx, p.ry, p.rz, s); }
  mtn.done();
}
const receipt = card(0.62, 3.0, (c, w, h) => {
  c.fillStyle = '#fffdf6'; c.fillRect(0, 0, w, h); txt(c, 'MEGA MART', w / 2, 0.14, 0.085, '#16111f');
  for (let i = 0; i < 26; i++) { txt(c, 'CHOCO PUDDING', 0.05, 0.32 + i * 0.078, 0.042, '#3a3550', { weight: 700, align: 'left' }); txt(c, '.25', w - 0.05, 0.32 + i * 0.078, 0.042, '#3a3550', { weight: 700, align: 'right' }); }
  txt(c, '× 12,150', w / 2, 2.44, 0.075, '#3a3550', { weight: 800 }); c.fillStyle = '#16111f'; c.fillRect(0.04, 2.52, w - 0.08, 0.012);
  txt(c, 'TOTAL', w / 2, 2.63, 0.08, '#16111f'); txt(c, '$3,000', w / 2, 2.8, 0.17, '#d9433f');
}, { ppu: 320 });
receipt.geometry.translate(0, -1.5, 0); receipt.rotation.x = -0.76; put(receipt, 0.5, 2.42, -2.5); receipt.material.side = THREE.DoubleSide;

// ---------------- STORE (x = 18.2 .. 34.8) ----------------
const checker = ctex(256, 256, (c) => { for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { c.fillStyle = (i + j) % 2 ? '#f6f8ff' : '#54c7c2'; c.fillRect(i * 64, j * 64, 64, 64); } }); checker.wrapS = checker.wrapT = THREE.RepeatWrapping; checker.repeat.set(5.5, 2.5);
put(box(16.6, 0.1, 7.6, toon(0xffffff, { map: checker }), 0.03), 26.5, -0.05, -1.5);
put(box(16.6, 4.7, 0.2, toon(0xfff1cf), 0.04), 26.5, 2.35, -5.2);
put(box(16.6, 0.5, 0.24, toon(0xf08a4b), 0.0), 26.5, 4.0, -5.08);
for (const x of [18.2, 34.8]) put(box(0.2, 4.7, 7.4, toon(0xffe2a8), 0.04), x, 2.35, -1.5);
// promo poster + freezer
const poster = put(card(2.5, 3.1, (c, w, h) => {
  c.fillStyle = '#fff8e4'; c.fillRect(0, 0, w, h); c.fillStyle = '#e23d3d'; c.fillRect(0, 0, w, 0.72); txt(c, 'FLY FREE!', w / 2, 0.32, 0.4, '#fff'); txt(c, "SUMMER '99 PROMO", w / 2, 0.6, 0.11, '#ffe9a8', { weight: 800 });
  // barcodes row
  const r = rng(8); for (let k = 0; k < 10; k++) { const bx = 0.2 + k * 0.215; c.fillStyle = '#fff'; c.fillRect(bx, 0.9, 0.17, 0.2); c.strokeStyle = '#16111f'; c.lineWidth = 0.012; c.strokeRect(bx, 0.9, 0.17, 0.2); c.fillStyle = '#16111f'; let x = bx + 0.02; while (x < bx + 0.15) { const bw = 0.008 + r() * 0.012; c.fillRect(x, 0.92, bw, 0.16); x += bw + 0.01; } }
  txt(c, '10 BARCODES', w / 2, 1.36, 0.3, '#16111f'); txt(c, '=', w / 2, 1.68, 0.3, '#e23d3d');
  txt(c, '500 MILES', w / 2, 2.05, 0.4, '#1f66d6');
  c.save(); c.translate(2.02, 2.42); c.rotate(-0.35); c.fillStyle = '#1f66d6'; c.beginPath(); c.moveTo(-0.22, 0.02); c.lineTo(0.2, -0.03); c.lineTo(0.26, 0); c.lineTo(0.2, 0.04); c.closePath(); c.fill(); c.beginPath(); c.moveTo(0, 0); c.lineTo(-0.1, -0.16); c.lineTo(-0.03, -0.16); c.lineTo(0.1, 0); c.lineTo(-0.03, 0.17); c.lineTo(-0.1, 0.17); c.closePath(); c.fill(); c.restore();
  txt(c, 'on every YumCo frozen dinner*', w / 2, 2.62, 0.1, '#3a3550', { weight: 700 }); txt(c, "*please don't buy 12,000 of anything", w / 2, 2.86, 0.075, '#8a86a8', { weight: 600, italic: true });
  c.strokeStyle = '#16111f'; c.lineWidth = 0.05; c.strokeRect(0, 0, w, h);
}), 21.5, 2.75, -5.08);
const hl1 = put(card(2.3, 0.5, (c, w, h) => { c.strokeStyle = '#ffd400'; c.lineWidth = 0.07; c.beginPath(); c.roundRect(0.05, 0.05, w - 0.1, h - 0.1, 0.12); c.stroke(); }, { alpha: true }), 21.5, 2.94, -5.05);
const hl2 = put(card(2.3, 0.62, (c, w, h) => { c.strokeStyle = '#ffd400'; c.lineWidth = 0.07; c.beginPath(); c.roundRect(0.05, 0.05, w - 0.1, h - 0.1, 0.12); c.stroke(); }, { alpha: true }), 21.5, 2.25, -5.05);
put(box(2.9, 0.95, 0.95, toon(0xeef2ff), 0.035), 21.5, 0.475, -4.55); put(box(2.7, 0.06, 0.8, toon(0x9fd8ff), 0.0), 21.5, 0.96, -4.55);
{ const r = rng(4); for (let i = 0; i < 8; i++) put(box(0.3, 0.07, 0.34, toon([0xe23d3d, 0x3fa650, 0xf0b23a, 0x7c6fd0][i % 4]), 0.012), 20.4 + (i % 4) * 0.72 + r() * 0.1, 1.02, -4.72 + (i > 3 ? 0.36 : 0)).rotation.y = r() * 0.4 - 0.2; }
function hangSign(text, x, y, z, w, bg, fg) { const s = put(card(w, 0.62, (c, ww, h) => { c.fillStyle = bg; c.beginPath(); c.roundRect(0, 0, ww, h, 0.1); c.fill(); c.strokeStyle = '#16111f'; c.lineWidth = 0.05; c.stroke(); txt(c, text, ww / 2, h / 2 + 0.01, 0.34, fg); }, { alpha: true }), x, y, z); for (const sx of [-1, 1]) put(cyl(0.012, 0.012, 1.2, toon(0x8a86a8), 0, 5), x + sx * w * 0.4, y + 0.9, z); return s; }
hangSign('FROZEN', 21.5, 4.55, -3.6, 2.1, '#57a8ff', '#fff');
hangSign('DISCOUNT!', 27, 3.7, -3.9, 2.7, '#ffd400', '#e23d3d');
hangSign('CHECKOUT', 31.6, 3.5, -3.2, 2.4, '#3fa650', '#fff');
// shelf
const SX = 27, shelfM = toon(0x6f7fd6), boardM = toon(0xe9ecff), BY = [0.42, 0.98, 1.54, 2.1];
put(box(3.5, 2.95, 0.1, shelfM, 0.03), SX, 1.5, -5.0); for (const s of [-1, 1]) put(box(0.1, 2.95, 0.7, shelfM, 0.03), SX + s * 1.75, 1.5, -4.68);
for (const y of BY) put(box(3.42, 0.06, 0.66, boardM, 0.02), SX, y, -4.68);
for (const [x, yi] of [[26.9, 2], [27.9, 1], [26.1, 3], [27.3, 0]]) put(card(0.46, 0.2, (c, w, h) => { c.fillStyle = '#ffd400'; c.beginPath(); c.roundRect(0, 0, w, h, 0.03); c.fill(); c.strokeStyle = '#16111f'; c.lineWidth = 0.02; c.stroke(); txt(c, '25¢', w / 2, h / 2 + 0.005, 0.15, '#e23d3d'); }, { ppu: 512, alpha: true }), x, BY[yi] - 0.1, -4.33);
const SN = 80, shelfCups = instanced(cupGeo, cupMats, SN).add(); const SCUP = [];
{ const r = rng(31); for (let row = 0; row < 4; row++) for (let k = 0; k < 10; k++) for (let dp = 0; dp < 2; dp++) SCUP.push({ x: SX - 1.44 + k * 0.32, y: BY[row] + 0.03 + 0.075, z: -4.5 - dp * 0.26, row, k, dp, j: r() }); SCUP.sort((a, b) => (b.row - a.row) || (a.k - b.k) || (a.dp - b.dp)); }
const scanLine = put(new THREE.Mesh(new THREE.PlaneGeometry(0.035, 2.9), new THREE.MeshBasicMaterial({ color: 0xff2a2a, fog: false })), 25, 1.5, -4.3); const scanGlow = glow(0xff3a3a, 1.6, 25, 1.6, -4.25);
const storeLed = put(card(2.6, 0.5, () => { }), SX, 3.05, -5.08); let slKey = '';
function setStoreLed(s) { if (s === slKey) return; slKey = s; storeLed.redraw((c, w, h) => { c.fillStyle = '#16111f'; c.beginPath(); c.roundRect(0, 0, w, h, 0.07); c.fill(); txt(c, s, w / 2, h / 2 + 0.01, 0.23, '#7dffb0'); }); }
// cart
const cart = new THREE.Group(); scene.add(cart);
{ const m = toon(0xb9bfd6); for (const [w, h, d, x, y, z] of [[1.0, 0.05, 0.62, 0, 0.5, 0], [1.0, 0.05, 0.05, 0, 0.98, 0.3], [1.0, 0.05, 0.05, 0, 0.98, -0.3], [0.05, 0.05, 0.62, 0.48, 0.98, 0], [0.05, 0.05, 0.62, -0.48, 0.98, 0], [0.05, 0.5, 0.05, 0.48, 0.74, 0.3], [0.05, 0.5, 0.05, -0.48, 0.74, 0.3], [0.05, 0.5, 0.05, 0.48, 0.74, -0.3], [0.05, 0.5, 0.05, -0.48, 0.74, -0.3], [0.05, 0.7, 0.05, -0.62, 0.95, 0.28], [0.05, 0.7, 0.05, -0.62, 0.95, -0.28], [0.06, 0.06, 0.66, -0.66, 1.3, 0]]) cart.add(put(box(w, h, d, m, 0.018), x, y, z, cart));
  for (let i = 0; i < 5; i++) cart.add(put(box(0.02, 0.44, 0.02, m, 0), -0.36 + i * 0.18, 0.74, 0.3, cart));
  for (const [x, z] of [[0.4, 0.26], [0.4, -0.26], [-0.4, 0.26], [-0.4, -0.26]]) { const wl = cyl(0.09, 0.09, 0.05, toon(0x3a3550), 0.015, 10); wl.rotation.x = Math.PI / 2; cart.add(put(wl, x, 0.09, z, cart)); cart.add(put(box(0.04, 0.34, 0.04, m, 0.012), x, 0.3, z, cart)); } }
const CPILE = []; { const r = rng(12); for (let i = 0; i < SN; i++) { const lay = Math.floor(i / 12), rad = Math.max(0.05, 0.36 - lay * 0.045); CPILE.push({ x: (r() - 0.5) * 2 * rad * 1.15, y: 0.62 + lay * 0.135 + r() * 0.04, z: (r() - 0.5) * 2 * rad * 0.7, rx: (r() - 0.5) * 1.6, ry: r() * 6, rz: (r() - 0.5) * 1.6 }); } }
// checkout
put(box(2.8, 0.95, 0.95, toon(0x4a5a9c), 0.035), 31.7, 0.475, -3.0); put(box(2.6, 0.05, 0.8, toon(0x2f3559), 0.0), 31.7, 0.96, -3.0);
put(box(0.5, 0.42, 0.5, toon(0xe9ecff), 0.03), 32.95, 1.2, -3.05); put(box(0.38, 0.2, 0.05, toon(0x7dffb0), 0.02), 32.95, 1.3, -2.78);
const ckCups = instanced(cupGeo, cupMats, 46).add(); { const r = rng(40); for (let i = 0; i < 46; i++) { const lay = Math.floor(i / 10); ckCups.set(i, 31.0 + (r() - 0.5) * (1.1 - lay * 0.22), 1.06 + lay * 0.135, -2.95 + (r() - 0.5) * (0.6 - lay * 0.1), (r() - 0.5) * (lay ? 1.5 : 0.2), r() * 6, (r() - 0.5) * (lay ? 1.5 : 0.2)); } ckCups.done(); }
const strip = card(0.36, 2.6, (c, w, h) => { c.fillStyle = '#fffdf6'; c.fillRect(0, 0, w, h); for (let i = 0; i < 40; i++) { c.fillStyle = '#8a86a8'; c.fillRect(0.04, 0.08 + i * 0.062, 0.17 + (i * 37 % 5) * 0.012, 0.018); c.fillRect(0.26, 0.08 + i * 0.062, 0.06, 0.018); } c.strokeStyle = '#16111f'; c.lineWidth = 0.02; c.strokeRect(0, 0, w, h); });
strip.geometry.translate(0, 1.3, 0); put(strip, 32.95, 1.42, -3.04); strip.material.side = THREE.DoubleSide;

// ---------------- FOOD BANK (x = -26.7 .. -17.3) ----------------
const wood = ctex(256, 256, (c) => { c.fillStyle = '#e0b07a'; c.fillRect(0, 0, 256, 256); c.strokeStyle = '#c9965f'; c.lineWidth = 4; for (let y = 0; y < 256; y += 42) { c.beginPath(); c.moveTo(0, y); c.lineTo(256, y); c.stroke(); } }); wood.wrapS = wood.wrapT = THREE.RepeatWrapping; wood.repeat.set(3, 3);
put(box(9.6, 0.1, 7.2, toon(0xffffff, { map: wood }), 0.03), -22, -0.05, -1.7);
put(box(9.6, 4.5, 0.2, toon(0xbfe9cc), 0.04), -22, 2.25, -5.2); for (const x of [-26.7, -17.3]) put(box(0.2, 4.5, 7.0, toon(0xa6dcb8), 0.04), x, 2.25, -1.7);
put(card(4.6, 0.95, (c, w, h) => { c.fillStyle = '#ff7a59'; c.beginPath(); c.roundRect(0, 0, w, h, 0.12); c.fill(); c.strokeStyle = '#16111f'; c.lineWidth = 0.05; c.stroke(); txt(c, 'COMMUNITY FOOD BANK', w / 2, h / 2 + 0.01, 0.34, '#fff'); }, { alpha: true }), -22, 3.75, -5.08);
put(box(3.2, 0.08, 0.5, toon(0x8a6a4a), 0.025), -24.6, 2.3, -4.85); put(box(3.2, 0.08, 0.5, toon(0x8a6a4a), 0.025), -19.4, 2.3, -4.85);
{ const r = rng(15); for (let i = 0; i < 14; i++) put(cyl(0.13, 0.13, 0.32, toon([0xe23d3d, 0x3fa650, 0xf0b23a, 0x57a8ff][i % 4]), 0.018, 10), (i < 7 ? -25.9 : -20.7) + (i % 7) * 0.42 + r() * 0.05, 2.5, -4.85); }
put(box(4.6, 0.1, 1.2, toon(0xf6f8ff), 0.03), -22, 0.95, -2.5); for (const [x, z] of [[-24.1, -2.0], [-19.9, -2.0], [-24.1, -3.0], [-19.9, -3.0]]) put(box(0.1, 0.95, 0.1, toon(0x8a86a8), 0.02), x, 0.47, z);
const fbCups = instanced(cupGeo, cupMats, 44).add(); { const r = rng(60); for (let i = 0; i < 44; i++) { const g = i % 4, lay = Math.floor((i / 4) / 6); fbCups.set(i, [-24.1, -22.7, -21.3, -19.9][g] + (r() - 0.5) * (0.42 - lay * 0.1), 1.08 + lay * 0.135, -2.45 + (r() - 0.5) * 0.5, (r() - 0.5) * (lay ? 1.6 : 0.2), r() * 6, (r() - 0.5) * (lay ? 1.6 : 0.2)); } fbCups.done(); }
const lblBox = put(box(0.8, 0.5, 0.6, toon(0xc99a5b), 0.03), -22, 0.25, -1.2); { const l = card(0.7, 0.26, (c, w, h) => txt(c, 'LABELS', w / 2, h / 2, 0.17, '#5a3a1c'), { alpha: true }); l.position.set(0, 0, 0.305); lblBox.add(l); }
const lblTex = ctex(64, 40, (c) => { c.fillStyle = '#fff'; c.fillRect(0, 0, 64, 40); c.fillStyle = '#111'; for (let x = 6; x < 58; x += 7) c.fillRect(x, 6, x % 3 ? 2 : 4, 28); });
const flyLabels = Array.from({ length: 12 }, () => { const m = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.125), new THREE.MeshBasicMaterial({ map: lblTex, side: THREE.DoubleSide })); scene.add(m); return m; });
// mailbox
const mailbox = new THREE.Group(); mailbox.position.set(-16.6, 0, 1.6); scene.add(mailbox);
mailbox.add(put(box(0.14, 1.0, 0.14, toon(0x8a6a4a), 0.025), 0, 0.5, 0, mailbox));
const mbBody = new THREE.Group(); mbBody.position.y = 1.0; mailbox.add(mbBody);
mbBody.add(put(box(0.62, 0.42, 0.9, toon(0x2f6fe0), 0.03), 0, 0.21, 0, mbBody)); { const top = cyl(0.31, 0.31, 0.9, toon(0x2f6fe0), 0.03, 16); top.rotation.x = Math.PI / 2; mbBody.add(put(top, 0, 0.42, 0, mbBody)); }
mbBody.add(put(box(0.5, 0.06, 0.03, toon(0x16213f), 0), 0, 0.5, 0.46, mbBody));
{ const l = card(0.5, 0.18, (c, w, h) => txt(c, 'MAIL', w / 2, h / 2, 0.14, '#fff'), { alpha: true }); l.position.set(0, 0.2, 0.455); mbBody.add(l); }
const mbFlag = new THREE.Group(); mbFlag.position.set(0.33, 0.25, 0.1); mbBody.add(mbFlag); mbFlag.add(put(box(0.04, 0.42, 0.06, toon(0xe23d3d), 0.015), 0, 0.21, 0, mbFlag)); mbFlag.add(put(box(0.04, 0.16, 0.22, toon(0xe23d3d), 0.015), 0, 0.36, -0.1, mbFlag));
const envelope = put(box(0.5, 0.34, 0.16, toon(0xfff8e6), 0.022), 0, 0, 0);

// ---------------- PLANE ----------------
const plane = new THREE.Group(); scene.add(plane);
{ const white = toon(0xffffff), blue = toon(0x2f6fe0), red = toon(0xe23d3d), dark = new THREE.MeshBasicMaterial({ color: 0x16213f });
  const f = ol(new THREE.CapsuleGeometry(0.82, 4.2, 8, 20), white, 0.04); f.rotation.z = Math.PI / 2; plane.add(f);
  plane.add(put(box(1.5, 0.14, 6.4, blue, 0.04), 0.0, -0.3, 0, plane));
  const fin = box(1.0, 1.35, 0.14, red, 0.035); fin.rotation.z = 0.35; plane.add(put(fin, -2.55, 1.05, 0, plane)); plane.add(put(box(0.7, 0.1, 2.3, blue, 0.03), -2.6, 0.25, 0, plane));
  for (const z of [-1.7, 1.7]) { const e = cyl(0.26, 0.22, 0.9, toon(0xd9deef), 0.03, 12); e.rotation.z = Math.PI / 2; plane.add(put(e, 0.2, -0.62, z, plane)); }
  for (const x of [-1.9, -1.3, -0.7, 1.7, 2.2]) plane.add(put(new THREE.Mesh(new THREE.CircleGeometry(0.17, 16), dark), x, 0.22, 0.815, plane));
  const cw = new THREE.Mesh(new THREE.CircleGeometry(0.3, 16), dark); cw.scale.set(1, 0.6, 1); plane.add(put(cw, 2.75, 0.32, 0.6, plane)); cw.rotation.y = 0.9;
  plane.add(put(new THREE.Mesh(new THREE.CircleGeometry(0.5, 28), new THREE.MeshBasicMaterial({ color: 0x9fd8ff })), 0.55, 0.22, 0.822, plane));
  plane.add(put(ol(new THREE.TorusGeometry(0.52, 0.06, 8, 28), toon(0xb9bfd6), 0.018), 0.55, 0.22, 0.84, plane));
  const stripe = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 0.12), new THREE.MeshBasicMaterial({ color: 0x2f6fe0 })); plane.add(put(stripe, -0.1, -0.2, 0.822, plane));
}
const banner = card(4.6, 0.95, (c, w, h) => { c.fillStyle = '#ffd400'; c.fillRect(0, 0, w, h); c.strokeStyle = '#16111f'; c.lineWidth = 0.06; c.strokeRect(0, 0, w, h); txt(c, '1,250,000 MILES', w / 2, h / 2 + 0.02, 0.5, '#16111f'); });
banner.material.side = THREE.DoubleSide; put(banner, -6.3, 0.1, 0, plane); const rope = put(box(1.1, 0.03, 0.03, toon(0x3a3550), 0), -3.45, 0.1, 0, plane);
const tag = card(1.7, 0.95, (c, w, h) => { c.fillStyle = '#fff8e4'; c.beginPath(); c.moveTo(0.3, 0.03); c.lineTo(w - 0.03, 0.03); c.lineTo(w - 0.03, h - 0.03); c.lineTo(0.3, h - 0.03); c.lineTo(0.03, h / 2); c.closePath(); c.fill(); c.strokeStyle = '#16111f'; c.lineWidth = 0.05; c.stroke(); c.beginPath(); c.arc(0.3, h / 2, 0.06, 0, 7); c.stroke(); txt(c, '$150,000', 1.02, 0.36, 0.3, '#2a9d4b'); txt(c, 'of flights', 1.02, 0.7, 0.16, '#3a3550', { weight: 800 }); }, { alpha: true });
put(tag, -1.35, 0.25, 0.95, plane);
const STAMPS = [['PARIS', '#e23d3d', -0.6, 0.86], ['TOKYO', '#7c3fd6', 0.62, 0.9], ['CAIRO', '#d68a1f', -0.62, -0.72], ['RIO', '#2a9d4b', 0.62, -0.74], ['SYDNEY', '#1f66d6', 0.0, 1.32]].map(([n, col, x, y], i) => {
  const s = card(0.74, 0.74, (c, w, h) => { c.translate(w / 2, h / 2); c.rotate((i - 2) * 0.16); c.strokeStyle = col; c.lineWidth = 0.045; c.beginPath(); c.arc(0, 0, 0.32, 0, 7); c.stroke(); c.lineWidth = 0.02; c.beginPath(); c.arc(0, 0, 0.26, 0, 7); c.stroke(); txt(c, n, 0, 0, n.length > 5 ? 0.115 : 0.14, col); }, { alpha: true });
  put(s, 0.55 + x, 0.22 + y, 0.98, plane); return s; });
const taxForm = card(1.0, 1.25, (c, w, h) => { c.fillStyle = '#fffdf6'; c.fillRect(0, 0, w, h); c.strokeStyle = '#16111f'; c.lineWidth = 0.04; c.strokeRect(0, 0, w, h); c.fillStyle = '#1f66d6'; c.fillRect(0, 0, w, 0.22); txt(c, 'TAX RETURN', w / 2, 0.12, 0.11, '#fff');
  txt(c, 'Charity donation:', 0.08, 0.38, 0.075, '#3a3550', { weight: 700, align: 'left' }); txt(c, '12,150 puddings', 0.08, 0.52, 0.095, '#16111f', { align: 'left' });
  c.fillStyle = '#c9cde0'; for (let i = 0; i < 4; i++) c.fillRect(0.08, 0.68 + i * 0.1, 0.84 - (i % 2) * 0.2, 0.025); txt(c, 'Deduction:', 0.08, 1.12, 0.075, '#3a3550', { weight: 700, align: 'left' }); });
put(taxForm, 1.42, 0.2, 0.98, plane); taxForm.rotation.z = -0.06;
const stampMark = card(1.0, 0.6, (c, w, h) => { c.translate(w / 2, h / 2); c.rotate(-0.2); c.strokeStyle = '#e02626'; c.lineWidth = 0.045; c.beginPath(); c.roundRect(-0.42, -0.2, 0.84, 0.4, 0.05); c.stroke(); txt(c, '−$815', 0, -0.045, 0.2, '#e02626'); txt(c, 'WRITE-OFF', 0, 0.115, 0.085, '#e02626'); }, { alpha: true, ppu: 400 });
put(stampMark, 1.44, -0.12, 1.0, plane);
const stamper = new THREE.Group(); plane.add(stamper); stamper.add(put(box(0.5, 0.3, 0.3, toon(0xe02626), 0.025), 0, 0, 0, stamper)); { const hd = cyl(0.07, 0.07, 0.45, toon(0x8a5a3a), 0.02, 10); hd.rotation.x = Math.PI / 2; stamper.add(put(hd, 0, 0, 0.36, stamper)); }

// math cards floating by David
const MATH = [['10 barcodes = 500 mi', 13.25], ['1 barcode = 50 mi', 13.95], ['cheapest barcode = ?', 14.7]].map(([s, t0], i) => {
  const m = card(1.3, 0.3, (c, w, h) => txt(c, s, w / 2, h / 2, 0.125, '#fff', { stroke: '#16111f', sw: 0.045 }), { alpha: true, ppu: 400 }); m.userData.t0 = t0; put(m, 23.2, 1.8 + i * 0.27, -3.3); m.material.depthTest = false; m.renderOrder = 5; return m; });
const bulb = put(card(0.5, 0.6, (c, w, h) => { c.fillStyle = '#ffe14d'; c.beginPath(); c.arc(w / 2, 0.24, 0.19, 0, 7); c.fill(); c.strokeStyle = '#16111f'; c.lineWidth = 0.035; c.stroke(); c.fillStyle = '#c9cde0'; c.beginPath(); c.roundRect(w / 2 - 0.09, 0.41, 0.18, 0.13, 0.03); c.fill(); c.stroke(); }, { alpha: true, ppu: 400 }), 23.2, 2.72, -3.3); bulb.material.depthTest = false; bulb.renderOrder = 5;
const bulbGlow = glow(0xffe14d, 2.0, 23.2, 2.77, -3.25);

// ---------------- cast ----------------
const david = makeChar(1024);  scene.add(david.mesh);
const DAVID = { colors: {} };
const mk = (x, y, z, sc = 1) => { const c = makeChar(512); put(c.mesh, x, y, z); c.mesh.scale.setScalar(sc); return c; };
const shop1 = mk(0, 0, -2.5), shop2 = mk(0, 0, -1.8), cashier = mk(32.25, 0, -3.75, 1.08), vols = [mk(-23.4, 0.3, -3.25, 1.12), mk(-22, 0.3, -3.3, 1.12), mk(-20.6, 0.3, -3.25, 1.12)];
const SKIN = [{ skin: '#f1c9a5', skinSh: '#dba983', hair: '#7a4a22' }, { skin: '#8a5a3c', skinSh: '#724628', hair: '#15101a' }, { skin: '#f4d2b0', skinSh: '#e0b48e', hair: '#e07a2c' }, { skin: '#d9a070', skinSh: '#bf8456', hair: '#3a1f12' }];
const OUTFIT = [{ top: '#e9b33a', topSh: '#c48f22', pants: '#3a2d4d' }, { top: '#d9577a', topSh: '#b53f60', pants: '#232c4d' }, { top: '#7c6fd0', topSh: '#5f52b0', pants: '#2a2a3a' }, { top: '#58b368', topSh: '#3f914e', pants: '#3a2d4d' }];
const pal = (i, j) => ({ ...SKIN[i], ...OUTFIT[j], inner: OUTFIT[j].top });

// ---------------- camera ----------------
const PL2 = [-12.6, 13.6, -8]; // plane parking spot for the finale
const K = [
  [0.0, [0.5, 3.15, -0.5], [0, 2.92, -2.75], 28, 'lin'],
  [0.95, [0.45, 3.15, -0.7], [0, 2.92, -2.75], 28, 'lin'],
  [1.75, [0.9, 2.7, 6.6], [0, 1.75, -3], 40, 'io'],
  [2.35, [0.85, 2.75, 6.4], [0, 1.8, -3], 40, 'lin'],
  [3.1, [1.5, 3.2, 7.4], [1.5, 14, -6], 50, 'io'],
  [4.25, [4.5, 4.2, 7.0], [14.5, 14, -6], 50, 'lin'],
  [5.05, [21.5, 2.7, 3.4], [21.5, 2.45, -5], 44, 'io'],
  [A(3), [21.5, 2.7, 2.9], [21.5, 2.5, -5], 44, 'lin'],
  [A(3) + 0.45, [21.5, 2.7, 1.5], [21.5, 2.62, -5], 38, 'io'],
  [B(3), [21.5, 2.68, 1.2], [21.5, 2.58, -5], 38, 'lin'],
  [A(4) + 0.4, [21.0, 1.7, 2.6], [21.4, 1.55, -4], 46, 'io'],
  [B(4), [21.1, 1.7, 2.3], [21.4, 1.55, -4], 46, 'lin'],
  [A(5) + 0.3, [23.15, 1.35, 0.7], [23.2, 1.12, -3.4], 30, 'out'],
  [B(5) + 0.1, [23.16, 1.35, 0.45], [23.2, 1.12, -3.4], 30, 'lin'],
  [A(6) + 0.5, [23.7, 1.75, 1.1], [23.2, 1.55, -3.4], 36, 'io'],
  [B(6), [22.8, 1.75, 0.95], [23.2, 1.55, -3.4], 36, 'lin'],
  [A(7) + 0.6, [26.5, 1.9, 1.9], [26.7, 1.6, -5], 44, 'io'],
  [B(7), [26.55, 1.9, 1.6], [26.7, 1.6, -5], 44, 'lin'],
  [A(8) + 0.45, [26.9, 1.82, -2.7], [26.9, 1.68, -5], 28, 'io'],
  [CT('25 cents') - 0.1, [26.9, 1.8, -2.85], [26.9, 1.66, -5], 28, 'lin'],
  [CT('25 cents') + 0.3, [26.9, 1.52, -3.3], [26.9, 1.46, -5], 22, 'io'],
  [B(8), [26.9, 1.52, -3.4], [26.9, 1.46, -5], 22, 'lin'],
  [A(9) + 0.45, [26.74, 1.66, -3.92], [26.74, 1.645, -5], 30, 'io'],
  [A(9) + 1.15, [26.74, 1.66, -3.98], [26.74, 1.645, -5], 30, 'lin'],
  [A(9) + 1.6, [26.9, 1.75, -1.6], [26.9, 1.42, -5], 42, 'io'],
  [B(9) + 0.1, [26.9, 1.75, -1.45], [26.9, 1.42, -5], 42, 'lin'],
  [A(10) + 0.5, [26.2, 2.7, 1.5], [26.5, 1.15, -4.2], 46, 'io'],
  [B(10), [26.35, 2.6, 1.3], [26.6, 1.15, -4.2], 46, 'lin'],
  [A(11) + 0.4, [31.6, 1.9, 2.6], [31.75, 1.4, -3.2], 40, 'io'],
  [B(11), [31.65, 1.9, 2.3], [31.75, 1.4, -3.2], 40, 'lin'],
  [A(12) + 0.3, [30.95, 1.35, 1.5], [30.85, 1.12, -2.3], 30, 'out'],
  [B(12) + 0.1, [30.95, 1.35, 1.25], [30.85, 1.12, -2.3], 30, 'lin'],
  [A(13) + 0.55, [0.5, 3.5, 7.6], [0, 2.05, -3], 44, 'io'],
  [B(13), [0.4, 3.4, 7.0], [0, 2.05, -3], 44, 'lin'],
  [A(14) + 0.55, [0.55, 2.55, 1.15], [0.5, 0.78, -0.62], 30, 'io'],
  [B(14), [0.53, 2.4, 0.95], [0.5, 0.72, -0.62], 30, 'lin'],
  [A(15) + 0.4, [0.4, 3.1, -0.3], [0, 2.9, -2.75], 30, 'io'],
  [B(15), [0.38, 3.1, -0.5], [0, 2.9, -2.75], 30, 'lin'],
  [A(16) + 0.45, [-2.0, 3.4, -1.0], [-2.2, 3.35, -6], 30, 'io'],
  [CT('and nobody') - 0.05, [-2.02, 3.4, -1.3], [-2.2, 3.35, -6], 30, 'lin'],
  [CT('and nobody') + 0.5, [0.7, 3.2, 0.0], [0, 2.75, -2.75], 36, 'io'],
  [CT('12,000 labels') - 0.1, [0.65, 3.2, -0.15], [0, 2.75, -2.75], 36, 'lin'],
  [CT('12,000 labels') + 0.6, [0.0, 7.6, 4.2], [0, 1.6, -3], 46, 'io'],
  [B(16), [0.0, 7.9, 4.5], [0, 1.6, -3], 46, 'lin'],
  [A(17) + 0.45, [0.5, 3.12, -0.3], [0.05, 2.92, -2.75], 28, 'io'],
  [B(17), [0.48, 3.12, -0.45], [0.05, 2.92, -2.75], 28, 'lin'],
  [A(18) + 0.5, [-22, 2.3, 3.6], [-22, 1.75, -3], 42, 'io'],
  [B(18), [-21.8, 2.25, 3.0], [-22, 1.75, -3], 42, 'lin'],
  [A(19) + 0.5, [-17.2, 1.5, 6.9], [-17.2, 1.05, 1.6], 42, 'io'],
  [CT('and gets') + 0.1, [-17.2, 1.5, 6.5], [-17.2, 1.05, 1.6], 42, 'lin'],
  [CT('and gets') + 0.85, [-16.5, 2.2, 7.5], [-16.0, 13.6, -8], 52, 'io'],
  [B(19), [-16.3, 2.3, 7.3], [-15.9, 13.6, -8], 52, 'lin'],
  [A(20) + 0.6, [-13.4, 13.95, 0.2], [-13.7, 13.82, -8], 36, 'io'],
  [B(20), [-13.3, 13.95, -0.3], [-13.65, 13.82, -8], 36, 'lin'],
  [A(21) + 0.45, [-12.0, 13.95, -1.6], [-12.05, 13.9, -8], 36, 'io'],
  [B(21) + 0.1, [-12.0, 13.95, -1.95], [-12.05, 13.9, -8], 36, 'lin'],
  [A(22) + 0.45, [-11.45, 13.86, -1.9], [-11.45, 13.8, -8], 34, 'io'],
  [B(22), [-11.45, 13.86, -2.1], [-11.45, 13.8, -8], 34, 'lin'],
  [A(23) + 0.3, [-11.45, 13.84, -2.45], [-11.45, 13.78, -8], 32, 'out'],
  [DUR, [-11.45, 13.84, -2.75], [-11.45, 13.78, -8], 32, 'lin'],
];
const cam = makeCam(K);
const T_STAMP = CT('tax write-off') + 0.38;
const shake = t => Math.exp(-Math.max(0, t - T_STAMP) * 9) * (t >= T_STAMP ? 1 : 0) + bump(t, A(13) + 0.6, 1.2) * 0.25;

// ---------------- acting ----------------
const blink = t => (t % 3.1) < 0.09;
const talk = t => 0.35 + 0.65 * Math.abs(Math.sin(t * 17));
function update(t) {
  const c0 = cam.at(t); sun.target.position.set(c0.look[0], 0, c0.look[2]); sun.position.set(c0.look[0] + 7, 17, c0.look[2] + 11);
  { const vis = (lo, hi) => (c0.look[0] > lo && c0.look[0] < hi) || (c0.pos[0] > lo && c0.pos[0] < hi);
    const g = vis(-13, 13), st = vis(15, 40), fb = vis(-40, -12);
    mtn.mesh.visible = mtn.outl.visible = mcore.visible = g; shelfCups.mesh.visible = shelfCups.outl.visible = ckCups.mesh.visible = ckCups.outl.visible = st; fbCups.mesh.visible = fbCups.outl.visible = fb;
    if (g) setMountain(t); }

  // --- plane ---
  const fin = t > 30;
  if (!fin) { const k = seg(t, 2.55, 4.5); plane.position.set(lerp(-9, 18, k), 14, -6); plane.rotation.z = 0.05; }
  else { const k = EASE.out(seg(t, CT('and gets') + 0.3, CT('and gets') + 1.5)); plane.position.set(lerp(-34, PL2[0], k), PL2[1] + Math.sin(t * 1.6) * 0.06, PL2[2]); plane.rotation.z = Math.sin(t * 1.1) * 0.012; }
  banner.visible = rope.visible = fin; banner.rotation.y = Math.sin(t * 5) * 0.05;
  tag.scale.setScalar(Math.max(0.001, pop(t, CT('$150,000'), 0.3))); tag.rotation.z = Math.sin(t * 3) * 0.05 - 0.05;
  STAMPS.forEach((s, i) => { s.scale.setScalar(Math.max(0.001, pop(t, A(21) + 0.35 + i * 0.3, 0.22) * (1 - seg(t, A(22), A(22) + 0.25)))); });
  taxForm.scale.setScalar(Math.max(0.001, 0.9 * pop(t, A(22) + 0.5, 0.3)));
  const sk = seg(t, T_STAMP - 0.14, T_STAMP), sb = seg(t, T_STAMP + 0.1, T_STAMP + 0.4);
  stamper.visible = t > T_STAMP - 0.45 && t < T_STAMP + 0.45; stamper.position.set(1.44, -0.12, lerp(lerp(2.6, 1.18, sk * sk), 3.0, sb));
  stampMark.scale.setScalar(t >= T_STAMP ? 1 + 0.5 * Math.exp(-(t - T_STAMP) * 16) : 0.001);
  for (const g of clouds) g.position.x = ((g.userData.bx - Math.max(0, t - A(19) - 2) * 2.6 + 60) % 120 + 120) % 120 - 60;
  // years fly by: sky cycles day -> dusk -> night twice
  { const k = seg(t, A(21) + 0.2, B(21)), cyc = k > 0 && k < 1 ? (1 - Math.cos(k * Math.PI * 4)) / 2 : 0;
    skyMat.color.setRGB(lerp(1, 0.55, cyc) + cyc * 0.25 * Math.sin(k * 25), lerp(1, 0.4, cyc), lerp(1, 0.75, cyc)); hemi.intensity = 1.75 - cyc * 0.5; }

  // --- store dressing ---
  hl1.scale.setScalar(Math.max(0.001, pop(t, CT('10 barcodes'), 0.25))); hl1.visible = t < A(4);
  hl2.scale.setScalar(Math.max(0.001, pop(t, CT('500'), 0.25))); hl2.visible = t < A(4);
  MATH.forEach((m, i) => { const k = pop(t, m.userData.t0, 0.25) * (1 - seg(t, A(7) + 0.1, A(7) + 0.3)); m.scale.setScalar(Math.max(0.001, k)); m.position.y = 1.8 + i * 0.27 + Math.sin(t * 2.4 + i) * 0.025; m.quaternion.copy(camera.quaternion); });
  { const k = pop(t, 15.25, 0.22) * (1 - seg(t, A(7) + 0.1, A(7) + 0.3)); bulb.scale.setScalar(Math.max(0.001, k)); bulb.quaternion.copy(camera.quaternion); bulbGlow.material.opacity = cl(k) * 0.8; }
  // scanner sweep over every barcode
  const s0 = A(9) + 1.45, s1 = B(9) + 0.05, sx = lerp(25.3, 28.7, seg(t, s0, s1)), scanning = t > s0 && t < s1;
  scanLine.visible = scanning; scanLine.position.x = sx; scanGlow.position.x = sx; scanGlow.material.opacity = scanning ? 0.7 : 0;
  // cups leave the shelf for the cart
  const f0 = A(10) + 0.25, cartX = lerp(26.9, 32.5, EASE.in(seg(t, B(10) - 0.35, B(10) + 0.5)));
  cart.position.set(cartX, 0, -2.5); cart.visible = t > A(7) && t < B(10) + 0.5;
  for (let i = 0; i < SN; i++) { const p = SCUP[i], q = CPILE[i], ts = f0 + i * 0.021, k = seg(t, ts, ts + 0.34);
    if (k <= 0) { const hop = scanning ? Math.max(0, 1 - Math.abs(p.x - sx) / 0.2) * 0.06 : 0; shelfCups.set(i, p.x, p.y + hop, p.z, 0, (p.j - 0.5) * 0.5, 0); }
    else { const e = EASE.io(k); shelfCups.set(i, lerp(p.x, cartX + q.x, e), lerp(p.y, q.y, e) + Math.sin(k * Math.PI) * 0.9, lerp(p.z, -2.5 + q.z, e), q.rx * e + k * 6, q.ry * e, q.rz * e, cart.visible ? 1 : 0.0001); } }
  shelfCups.done();
  setStoreLed(t < f0 ? 'IN STOCK: LOTS' : `STORES CLEARED: ${Math.round(lerp(1, 10, seg(t, f0 + 0.2, B(10) - 0.1)))}/10`);
  strip.scale.y = Math.max(0.001, EASE.out(seg(t, A(12) + 0.1, B(12))));
  setLed(t < A(15) ? `CUPS: ${Math.round(12150 * (t < 10 ? 1 : EASE.out(seg(t, A(13) + 0.3, B(13) - 0.25)))).toLocaleString('en-US')}` : 'PEELED: 3 / 12,150');
  receipt.scale.y = Math.max(0.001, t < 10 ? 0.001 : EASE.out(seg(t, A(14) - 0.1, A(14) + 0.6))); receipt.visible = t > 20 && t < A(17) + 0.3 && t < CT('12,000 labels') + 0.3 ? true : (t > 20 && t < A(15));

  // --- shoppers who ignore the poster ---
  { const k1 = seg(t, A(4) - 0.6, A(5) + 0.2), k2 = seg(t, A(4) - 0.5, A(5) + 0.2);
    shop1.mesh.position.x = lerp(19.4, 22.3, k1); shop2.mesh.position.x = lerp(23.4, 19.6, k2); shop1.mesh.visible = shop2.mesh.visible = t > 5 && t < A(5) + 0.22;
    shop1.draw({ plain: true, colors: pal(0, 1), eye: 'squint', look: [0.8, 0.3], mouth: 'flat', walk: Math.round(Math.sin(t * 13) * 2) / 2, bob: Math.abs(Math.sin(t * 13)) * 8, armL: [10, 10], armR: [20, 100], propR: 'phone' });
    shop2.draw({ plain: true, colors: pal(2, 2), eye: 'closed', mouth: 'smile', hat: 'cap', hatCol: '#e23d3d', walk: Math.round(Math.sin(t * 12 + 1) * 2) / 2, bob: Math.abs(Math.sin(t * 12 + 1)) * 8, armL: [25, 20], armR: [-20, 15] }); }
  // --- cashier ---
  { const asking = t > CT('Sir') - 0.05 && t < B(11) + 0.05, stare = t > A(12);
    cashier.draw({ plain: true, colors: pal(1, 3), apron: '#f6f8ff', hat: 'visor', eye: 'squint', look: [-0.85, 0.15], brow: stare ? 10 : (asking ? 14 : 0), browY: asking ? -6 : 0, mouth: asking ? 'talk' : 'flat', mouthOpen: talk(t), armL: [25, asking ? 120 : 30], armR: [18, 12], tilt: asking ? -9 : -3, blink: blink(t + 1) }); }
  // --- volunteers ---
  const eatT = CT('they keep');
  vols.forEach((v, i) => { const ph = t * 9 + i * 2.1, eat = t > eatT + i * 0.12;
    v.draw(eat ? { plain: true, colors: pal([3, 0, 1][i], [0, 2, 1][i]), apron: '#ff7a59', eye: 'happy', mouth: 'grin', propR: 'spoon', spoonFull: Math.sin(ph) > 0, propL: 'cup', armL: [28, -105], armR: [22, 132 + Math.round(Math.sin(ph)) * 16], bob: Math.abs(Math.sin(ph * 0.5)) * 6, tilt: Math.round(Math.sin(ph * 0.5)) * 4, hat: i === 1 ? 'cap' : null, hatCol: '#3fa650' }
      : { plain: true, colors: pal([3, 0, 1][i], [0, 2, 1][i]), apron: '#ff7a59', eye: 'normal', look: [0, 0.8], mouth: 'smile', propL: 'cup', armL: [28, -100], armR: [26 + Math.round(Math.sin(ph)) * 14, -78 - Math.round(Math.sin(ph)) * 30], bob: Math.abs(Math.sin(ph)) * 4, hat: i === 1 ? 'cap' : null, hatCol: '#3fa650' }); });
  flyLabels.forEach((m, i) => { const v = i % 3, per = 0.45, ph = ((t - A(18)) / per + i * 0.37) % 1, on = t > A(18) - 0.4 && t < eatT + 0.2;
    m.visible = on; const x0 = -23.4 + v * 1.4 + 0.25, y0 = 1.55, z0 = -2.9; m.position.set(lerp(x0, -22, ph), lerp(y0, 0.55, ph) + Math.sin(ph * Math.PI) * 0.9, lerp(z0, -1.2, ph)); m.rotation.set(ph * 9 + i, ph * 7, i); });

  // --- David, one card that travels with the story ---
  const D = david, dm = D.mesh; let P; dm.scale.setScalar(1); dm.rotation.set(0, 0, 0); if (dm.parent !== scene) scene.add(dm); let face = true;
  if (t < 4.6) { // king of pudding mountain
    dm.position.set(0, 1.68, -2.75); const bite = Math.sin(t * 7.5), look = t > 2.5;
    P = { legs: 'none', eye: look ? 'normal' : (t > 1.2 ? 'normal' : 'happy'), look: look ? [0.5, -0.9] : [0, 0.1], mouth: look ? 'grin' : (bite > 0.3 ? 'talk' : 'smirk'), mouthOpen: 0.8, propR: 'spoon', spoonFull: bite < 0.3, propL: 'cup', armL: look ? [150, 12] : [26, -112], armR: look ? [30, 110] : [20, 128 + (bite > 0.3 ? 22 : 0)], tilt: look ? -8 : Math.round(bite) * 3, bob: Math.max(0, bite) * 5 };
  } else if (t < A(7) + 0.22) { // sees the promo, does the math
    dm.position.set(23.2, 0, -3.4); const seen = t > A(5), math = t > A(6);
    P = math ? { eye: 'squint', look: [Math.sin(t * 3) * 0.5, -0.5], brow: -10, mouth: t > 15.25 ? 'grin' : 'flat', propL: 'calc', armL: [34, -128], armR: [24, -118 + Math.round(Math.sin(t * 20)) * 10], tilt: Math.sin(t * 2) * 3, bob: t > 15.25 ? bump(t, 15.25, 0.3) * 14 : 0 }
      : { eye: seen ? 'wide' : 'normal', look: [-0.9, -0.35], mouth: seen ? 'o' : 'flat', mouthOpen: 0.7, brow: seen ? 14 : 0, browY: seen ? -8 : 0, armL: [12, 8], armR: [12, 8], bob: bump(t, A(5) + 0.05, 0.25) * 16, tilt: -4 };
    if (t > 15.25 && math) P.eye = 'wide';
  } else if (t < B(10) + 0.5) { // the discount shelf
    const k = EASE.out(seg(t, A(7) + 0.25, A(7) + 0.85)), leave = EASE.in(seg(t, B(10) - 0.35, B(10) + 0.5));
    dm.position.set(lerp(23.8, 25.95, k) + leave * 5.75, 0, -3.0); const grab = t > A(10) + 0.2, awe = t > A(8);
    P = grab ? { eye: 'happy', mouth: 'grin', armL: [150 + Math.round(Math.sin(t * 18)) * 14, 12], armR: [140 - Math.round(Math.sin(t * 18)) * 14, 14], bob: Math.abs(Math.sin(t * 9)) * 12, walk: leave > 0 ? Math.round(Math.sin(t * 16)) : 0 }
      : { eye: awe ? 'wide' : 'normal', look: [0.85, -0.2], brow: awe ? 12 : 0, browY: awe ? -8 : 0, mouth: awe ? 'o' : 'smile', mouthOpen: 0.9, armL: [14, 10], armR: awe ? [70, 30] : [14, 10], walk: k < 1 ? Math.round(Math.sin(t * 16)) : 0, bob: bump(t, A(8), 0.25) * 12, tilt: 4 };
  } else if (t < A(13) + 0.3) { // checkout, deadpan
    dm.position.set(30.85, 0, -2.3); const say = t > CT('Y2K') - 0.03 && t < B(12) - 0.25, after = t >= B(12) - 0.25;
    P = { eye: 'squint', look: [after ? 0 : 0.85, 0], mouth: say ? 'talk' : 'flat', mouthOpen: talk(t), brow: 0, armL: [14, 8], armR: [14, 8], tilt: 0, blink: blink(t), bob: bump(t, CT('Y2K'), 0.2) * 5 };
  } else if (t < A(18) + 0.3) { // back on the mountain
    const up = pop(t, B(13) - 0.75, 0.35); dm.position.set(0, lerp(0.2, 1.68, cl(up, 0, 1.08)), -2.75);
    const prob = t > A(15), peel = t > CT('and nobody') && t < A(17), call = t >= A(17);
    P = call ? { legs: 'none', eye: 'normal', look: [0.4, -0.2], mouth: 'talk', mouthOpen: talk(t), brow: 6, propR: 'phone', armR: [24, 146], armL: [20, -110], propL: 'cup', tilt: 5 }
      : peel ? { legs: 'none', eye: 'squint', look: [-0.3, 0.9], mouth: 'grit', brow: -14, sweat: true, propL: 'cup', armL: [30, -112], armR: [24 + Math.round(Math.sin(t * 16)) * 5, -96 + Math.round(Math.sin(t * 16)) * 12], headX: Math.sin(t * 40) * 1.5, tilt: -3 }
        : prob ? { legs: 'none', eye: 'wide', look: [t > A(16) ? -0.9 : 0, t > A(16) ? -0.6 : 0], mouth: 'grit', brow: 16, browY: -6, sweat: true, armL: [150, 20], armR: [150, 20], headX: Math.sin(t * 36) * 2, bob: bump(t, A(15), 0.2) * 10 }
          : { legs: 'none', eye: 'happy', mouth: 'grin', armL: [158, 8], armR: [158, 8], bob: Math.abs(Math.sin(t * 8)) * 8, propR: t > A(14) ? null : null };
  } else if (t < CT('and gets') + 0.9) { // mailbox
    dm.position.set(-17.75, 0, 1.55); const sent = t > CT('the barcodes,') + 0.35;
    P = { eye: sent ? 'happy' : 'normal', look: [0.8, 0], mouth: sent ? 'grin' : 'smile', propR: sent ? null : 'envelope', armR: sent ? [150, 10] : [78, 12], armL: sent ? [150, 10] : [14, 8], bob: sent ? Math.abs(Math.sin(t * 9)) * 10 : bump(t, A(19) + 0.5, 0.25) * 8, tilt: 3 };
  } else { // window seat, for the next twenty years
    plane.add(dm); face = false; dm.position.set(0.55, 0.22 - 1.216 * 1.22 - 0.02, 0.9); dm.scale.setScalar(1.22);
    const old = t > A(21) + 0.95, end = t > A(22), wink = t > T_STAMP + 0.25;
    P = { headOnly: true, shades: !end, eye: wink ? 'wink' : 'normal', look: end ? [0.75, 0.1] : [0, 0], mouth: wink ? 'grin' : (end ? 'smirk' : 'smile'), beard: old ? '#d9dbe8' : null, colors: old ? { hair: '#b9bccb' } : {}, tilt: wink ? 6 : Math.sin(t * 2) * 2, brow: wink ? 8 : 0 };
    if (wink) P.look = [0, 0];
  }
  D.draw(P); if (face) D.face(camera);
  for (const c of [shop1, shop2, cashier, ...vols]) c.face(camera);

  // mailbox swallows the fat envelope
  { const ts = CT('the barcodes,') + 0.35, k = seg(t, ts, ts + 0.22); const h = D.handWorld ? null : null;
    envelope.visible = k > 0 && k < 1; envelope.position.set(lerp(-17.2, -16.6, k), lerp(1.3, 1.5, k) + Math.sin(k * Math.PI) * 0.25, 1.75 + 0.35 * (1 - k)); envelope.rotation.y = 0.3;
    const g = bump(t, ts + 0.2, 0.3); mbBody.scale.set(1 + g * 0.35, 1 - g * 0.12, 1 + g * 0.2); mbFlag.rotation.x = -Math.PI / 2 * (1 - EASE.back(seg(t, ts + 0.3, ts + 0.55))); }
}

window.DUR = DUR; window.FPS = FPS;
window.renderFrame = (t) => {
  cam.set(t); update(t);
  renderBlurred(t, cam, shake);
  vignette(0.26); drawCaption(t, VO.chunks);
};
window.READY = document.fonts.load('900 40px Inter').then(() => document.fonts.load('italic 700 40px Inter')).then(() => true);
